import threading, time, urllib.request, sys, os
import uvicorn

# Importar modulos para que PyInstaller los empaquete
import main
import database, auth
import modulos.conductores.modelo
import modulos.conductores.calculos
import modulos.conductores.graficos
import modulos.conductores.export_word
import modulos.apantallamiento.modelo
import modulos.apantallamiento.calculos
import modulos.apantallamiento.graficos
import modulos.apantallamiento.export_word

HOST = "127.0.0.1"
PORT = 8000

def start_server():
    base = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base)
    sys.path.insert(0, base)
    uvicorn.run(main.app, host=HOST, port=PORT, log_level="warning")

def wait_for_server(timeout=60):
    url = f"http://{HOST}:{PORT}/login"
    deadline = time.time() + timeout
    dots = 0
    sys.stdout.write("Iniciando servidor")
    sys.stdout.flush()
    while time.time() < deadline:
        try:
            urllib.request.urlopen(url, timeout=2)
            print(" OK")
            return True
        except Exception:
            dots += 1
            if dots % 5 == 0:
                sys.stdout.write(".")
                sys.stdout.flush()
            time.sleep(0.5)
    print(" TIMEOUT")
    return False

if __name__ == "__main__":
    t = threading.Thread(target=start_server, daemon=True)
    t.start()

    if not wait_for_server():
        input("\nERROR: No se pudo iniciar el servidor.\nPresiona Enter para salir...")
        sys.exit(1)

    try:
        import webview
        webview.create_window(
            "DISENO DE SUBESTACIONES",
            f"http://{HOST}:{PORT}",
            width=1280, height=800,
            resizable=True, text_select=True,
        )
    except Exception as e:
        import webbrowser
        print(f"\nVentana nativa no disponible ({e})")
        print("Abriendo en el navegador...")
        webbrowser.open(f"http://{HOST}:{PORT}")
        input("\nPresiona Enter para cerrar el servidor...")
