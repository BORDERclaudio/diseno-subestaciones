import os, sys
from fastapi import FastAPI, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import init_db, get_db, Usuario, Memoria
from auth import hash_password, verify_password, crear_token, decodificar_token

import modulos.conductores.modelo as cond_modelo
import modulos.conductores.calculos as cond_calculos
import modulos.conductores.graficos as cond_graficos
import modulos.conductores.export_word as cond_word

import modulos.apantallamiento.modelo as apa_modelo
import modulos.apantallamiento.calculos as apa_calculos
import modulos.apantallamiento.graficos as apa_graficos
import modulos.apantallamiento.export_word as apa_word

app = FastAPI(title="DISEÑO DE SUBESTACIONES")
BASE_DIR = Path(__file__).parent

PLOTS_DIR = BASE_DIR / "static" / "plots"
PLOTS_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

MODULOS = {
    "conductores": {
        "nombre": "Conductores Flexibles",
        "param_cls": cond_modelo.ParamConductor,
        "result_cls": cond_modelo.ResultConductor,
        "calcular": cond_calculos.calcular,
        "grafico": cond_graficos.generar,
        "exportar": cond_word.exportar,
        "template_form": "conductores/formulario.html",
        "template_result": "conductores/resultados.html",
    },
    "apantallamiento": {
        "nombre": "Apantallamiento (Esfera Rodante)",
        "param_cls": apa_modelo.ParamApantallamiento,
        "result_cls": apa_modelo.ResultApantallamiento,
        "calcular": apa_calculos.calcular,
        "grafico": apa_graficos.generar,
        "exportar": apa_word.exportar,
        "template_form": "apantallamiento/formulario.html",
        "template_result": "apantallamiento/resultados.html",
    },
}

@app.on_event("startup")
def startup():
    init_db()

def get_usuario_from_cookie(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("token")
    if not token:
        return None
    try:
        uid = decodificar_token(token)
        return db.query(Usuario).filter(Usuario.id == uid).first()
    except Exception:
        return None

# ─── AUTH ─────────────────────────────────────────────
@app.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {"error": None})

@app.post("/login")
def login_post(request: Request, email: str = Form(), password: str = Form(), db: Session = Depends(get_db)):
    user = db.query(Usuario).filter(Usuario.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(request, "login.html", {"error": "Email o password incorrectos"})
    token = crear_token(user.id)
    resp = RedirectResponse("/", status_code=302)
    resp.set_cookie(key="token", value=token, httponly=True, max_age=172800)
    return resp

@app.get("/registro")
def registro_page(request: Request):
    return templates.TemplateResponse(request, "registro.html", {"error": None})

@app.post("/registro")
def registro_post(request: Request, nombre: str = Form(), email: str = Form(), password: str = Form(), db: Session = Depends(get_db)):
    if db.query(Usuario).filter(Usuario.email == email).first():
        return templates.TemplateResponse(request, "registro.html", {"error": "Email ya registrado"})
    user = Usuario(nombre=nombre, email=email, password_hash=hash_password(password))
    db.add(user); db.commit()
    token = crear_token(user.id)
    resp = RedirectResponse("/", status_code=302)
    resp.set_cookie(key="token", value=token, httponly=True, max_age=172800)
    return resp

@app.get("/logout")
def logout():
    resp = RedirectResponse("/login", status_code=302)
    resp.delete_cookie("token")
    return resp

# ─── DASHBOARD ───────────────────────────────────────
@app.get("/")
def dashboard(request: Request, tipo: str = "conductores", db: Session = Depends(get_db)):
    usuario = get_usuario_from_cookie(request, db)
    if not usuario:
        return RedirectResponse("/login", status_code=302)
    if tipo not in MODULOS:
        tipo = "conductores"
    memorias = db.query(Memoria).filter(
        Memoria.usuario_id == usuario.id, Memoria.tipo == tipo
    ).order_by(Memoria.updated_at.desc()).all()
    return templates.TemplateResponse(request, "dashboard.html", {
        "usuario": usuario,
        "modulos": {k: {"nombre": v["nombre"]} for k, v in MODULOS.items()},
        "tipo_activo": tipo, "memorias": memorias,
    })

# ─── NUEVA MEMORIA ───────────────────────────────────
@app.get("/nueva/{tipo}")
def nueva_get(request: Request, tipo: str, db: Session = Depends(get_db)):
    usuario = get_usuario_from_cookie(request, db)
    if not usuario:
        return RedirectResponse("/login", status_code=302)
    if tipo not in MODULOS:
        return RedirectResponse("/", status_code=302)
    return templates.TemplateResponse(request, MODULOS[tipo]["template_form"], {
        "usuario": usuario, "p": {}, "editar": False,
    })

def _parse_params(form, param_cls):
    fields = [c.name for c in param_cls.__table__.columns if c.name != "memoria_id"]
    params = {}
    for f in fields:
        val = form.get(f)
        if val is not None and val != "":
            try:
                params[f] = float(val) if ("." in val or "e" in val.lower()) else int(val)
            except ValueError:
                params[f] = None
        else:
            params[f] = None
    return params

@app.post("/nueva/{tipo}")
async def nueva_post(request: Request, tipo: str, db: Session = Depends(get_db)):
    usuario = get_usuario_from_cookie(request, db)
    if not usuario:
        return RedirectResponse("/login", status_code=302)
    if tipo not in MODULOS:
        return RedirectResponse("/", status_code=302)
    config = MODULOS[tipo]
    form = dict(await request.form())
    nombre = form.pop("nombre", "Sin nombre")
    params = _parse_params(form, config["param_cls"])
    resultados = config["calcular"](params)

    memoria = Memoria(usuario_id=usuario.id, tipo=tipo, nombre=nombre)
    db.add(memoria); db.flush()
    db.add(config["param_cls"](memoria_id=memoria.id, **params))
    db.add(config["result_cls"](memoria_id=memoria.id, **resultados))
    db.commit()

    try:
        plot_path = PLOTS_DIR / f"{memoria.id}.png"
        if tipo == "conductores":
            config["grafico"](
                params["l"], params["fes"], params["h"], params["li"],
                resultados["bh_ieee"], resultados["dm_ieee"],
                str(plot_path)
            )
        elif tipo == "apantallamiento":
            config["grafico"](
                params["h"], params["n"],
                params.get("d_mm", 25.4) / 2000.0,
                params.get("s_cm", 45.7) / 100.0,
                resultados.get("S_esfera", 5.0),
                str(plot_path)
            )
    except Exception:
        pass
    return RedirectResponse(f"/memoria/{memoria.id}", status_code=302)

# ─── VER MEMORIA ─────────────────────────────────────
@app.get("/memoria/{memoria_id}")
def ver_memoria(request: Request, memoria_id: int, db: Session = Depends(get_db)):
    usuario = get_usuario_from_cookie(request, db)
    if not usuario:
        return RedirectResponse("/login", status_code=302)
    memoria = db.query(Memoria).filter(Memoria.id == memoria_id, Memoria.usuario_id == usuario.id).first()
    if not memoria:
        raise HTTPException(404)
    config = MODULOS[memoria.tipo]
    p_obj = db.query(config["param_cls"]).filter(config["param_cls"].memoria_id == memoria_id).first()
    r_obj = db.query(config["result_cls"]).filter(config["result_cls"].memoria_id == memoria_id).first()
    p = {c.name: getattr(p_obj, c.name) for c in p_obj.__table__.columns} if p_obj else {}
    r = {c.name: getattr(r_obj, c.name) for c in r_obj.__table__.columns} if r_obj else {}
    grafico = f"{memoria.id}.png" if (PLOTS_DIR / f"{memoria.id}.png").exists() else None
    return templates.TemplateResponse(request, config["template_result"], {
        "usuario": usuario,
        "memoria": memoria, "p": p, "r": r, "grafico": grafico,
    })

# ─── EXPORTAR WORD ───────────────────────────────────
@app.get("/memoria/{memoria_id}/exportar")
def exportar_memoria(request: Request, memoria_id: int, db: Session = Depends(get_db)):
    usuario = get_usuario_from_cookie(request, db)
    if not usuario:
        return RedirectResponse("/login", status_code=302)
    memoria = db.query(Memoria).filter(Memoria.id == memoria_id, Memoria.usuario_id == usuario.id).first()
    if not memoria:
        raise HTTPException(404)
    config = MODULOS[memoria.tipo]
    p = db.query(config["param_cls"]).filter(config["param_cls"].memoria_id == memoria_id).first()
    r = db.query(config["result_cls"]).filter(config["result_cls"].memoria_id == memoria_id).first()
    if not p or not r:
        raise HTTPException(404)
    p_dict = {c.name: getattr(p, c.name) for c in p.__table__.columns if c.name != "memoria_id"}
    r_dict = {c.name: getattr(r, c.name) for c in r.__table__.columns if c.name != "memoria_id"}
    gp = str(PLOTS_DIR / f"{memoria.id}.png") if (PLOTS_DIR / f"{memoria.id}.png").exists() else None
    buf = config["exportar"](p_dict, r_dict, gp)
    return Response(
        content=buf.read(),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename=memoria_{memoria.id}.docx"},
    )

# ─── ELIMINAR MEMORIA ────────────────────────────────
@app.get("/memoria/{memoria_id}/eliminar")
def eliminar_memoria(request: Request, memoria_id: int, db: Session = Depends(get_db)):
    usuario = get_usuario_from_cookie(request, db)
    if not usuario:
        return RedirectResponse("/login", status_code=302)
    memoria = db.query(Memoria).filter(Memoria.id == memoria_id, Memoria.usuario_id == usuario.id).first()
    if not memoria:
        raise HTTPException(404)
    config = MODULOS[memoria.tipo]
    db.query(config["param_cls"]).filter(config["param_cls"].memoria_id == memoria_id).delete()
    db.query(config["result_cls"]).filter(config["result_cls"].memoria_id == memoria_id).delete()
    db.delete(memoria); db.commit()
    plot_file = PLOTS_DIR / f"{memoria.id}.png"
    if plot_file.exists():
        plot_file.unlink()
    return RedirectResponse("/", status_code=302)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
