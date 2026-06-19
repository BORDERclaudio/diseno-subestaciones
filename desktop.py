import threading, time, urllib.request, sys, os
import uvicorn
import webview

HOST = "127.0.0.1"
PORT = 8000

def start_server():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    uvicorn.run("main:app", host=HOST, port=PORT, log_level="warning")

def wait_for_server():
    url = f"http://{HOST}:{PORT}/login"
    for _ in range(40):
        try:
            urllib.request.urlopen(url, timeout=1)
            return True
        except Exception:
            time.sleep(0.5)
    return False

if __name__ == "__main__":
    t = threading.Thread(target=start_server, daemon=True)
    t.start()
    if not wait_for_server():
        print("Error: No se pudo iniciar el servidor")
        sys.exit(1)
    webview.create_window(
        "DISEÑO DE SUBESTACIONES",
        f"http://{HOST}:{PORT}",
        width=1280, height=800,
        resizable=True,
        text_select=True,
    )
