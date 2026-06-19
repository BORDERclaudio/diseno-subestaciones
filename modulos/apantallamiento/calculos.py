import math

E0_DEFAULT = 21.1
TOL = 1e-6
MAX_ITER = 100
TOL_Z = 1e-4

def radio_equivalente_haz(n, r, s):
    if n == 1:
        return r
    elif n == 2:
        return math.sqrt(r * s)
    else:
        g = 1.0 if n <= 3 else 1.12
        return (n * g * r * s ** (n - 1)) ** (1.0 / n)

def newton_raphson_rc(V_objetivo, h, E0):
    Rc = 0.5 * h
    for i in range(MAX_ITER):
        ln_arg = 2.0 * h / Rc
        if ln_arg <= 1.0:
            Rc = h * 0.99
            ln_arg = 2.0 * h / Rc
        f = E0 * Rc * math.log(ln_arg) - V_objetivo
        df = E0 * (math.log(ln_arg) - 1.0)
        if abs(df) < 1e-12:
            break
        Rc_nuevo = Rc - f / df
        if Rc_nuevo <= 0:
            Rc_nuevo = 0.5 * Rc
        if abs(Rc_nuevo - Rc) < TOL:
            return Rc_nuevo, i + 1
        Rc = Rc_nuevo
    return Rc, MAX_ITER

def brown_impedance(h, Rc, r_e):
    arg1 = 2.0 * h / Rc
    arg2 = 2.0 * h / r_e
    if arg1 <= 1.0 or arg2 <= 1.0:
        return None
    return 60.0 * math.sqrt(math.log(arg1) * math.log(arg2))

def calcular(p):
    Vnom = p["Vnom"]
    BIL = p["BIL"]
    h = p["h"]
    n = p["n"]
    d_mm = p["d_mm"]
    r = d_mm / 2000.0
    s_cm = p["s_cm"]
    s = s_cm / 100.0
    E0 = p["E0"]
    tipo_op = p["tipo_elemento"]
    modo_iter = p["modo_iter"]

    k_factor = 1.0 if tipo_op == 1 else 1.2
    E0_kVm = E0 * 100.0
    r_e = radio_equivalente_haz(n, r, s)

    if modo_iter == 1:
        V_obj = BIL
        Zs = 60.0 * math.log(2.0 * h / r_e)
        for it in range(50):
            Rc, n_iter_nr = newton_raphson_rc(V_obj, h, E0_kVm)
            if n == 1:
                Rc_prime = Rc
            elif n == 2:
                R0 = r_e
                Rc_prime = R0 + Rc
            else:
                Rc_prime = r_e + Rc
            Zs_nuevo = brown_impedance(h, Rc_prime, r_e)
            if Zs_nuevo is None:
                raise ValueError("Geometria no valida para formula de Brown")
            if abs(Zs_nuevo - Zs) < TOL_Z:
                Zs = Zs_nuevo
                break
            Zs = Zs_nuevo
        else:
            pass
    else:
        Zs = 60.0 * math.log(2.0 * h / r_e)
        Rc, n_iter_nr = newton_raphson_rc(BIL, h, E0_kVm)
        if n == 1:
            Rc_prime = Rc
        elif n == 2:
            R0 = r_e
            Rc_prime = R0 + Rc
        else:
            Rc_prime = r_e + Rc
        Zs = brown_impedance(h, Rc_prime, r_e)
        if Zs is None:
            raise ValueError("Geometria no valida para formula de Brown")

    I_min = 2.0 * BIL / Zs
    S_esfera = 8.0 * k_factor * (I_min ** 0.65)

    return dict(
        r_e=round(r_e*100, 2),
        Rc=round(Rc*100, 2),
        n_iter_nr=n_iter_nr,
        Rc_prime=round(Rc_prime*100, 2) if n > 1 else None,
        Zs=round(Zs, 1),
        I_min=round(I_min, 2),
        S_esfera=round(S_esfera, 2),
    )
