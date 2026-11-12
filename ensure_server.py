#!/usr/bin/env python3
"""Garante que o backend do gerenciador esteja rodando em 127.0.0.1:8642.

Uso: python3 ensure_server.py
Saída: uma linha JSON {"status":"online|iniciado|erro", ...}
Código de saída: 0 se o servidor respondeu, 1 se não foi possível.
"""
import json, os, socket, subprocess, sys, time, urllib.request

HOST, PORT = "127.0.0.1", 8642
ROOT = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(ROOT, "server.log")
URL = "http://%s:%d/api/ping" % (HOST, PORT)


def ping(timeout=2.0):
    try:
        with urllib.request.urlopen(URL, timeout=timeout) as r:
            data = json.loads(r.read().decode() or "{}")
            return bool(data.get("ok"))
    except Exception:
        return False


def porta_ocupada():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.5)
    try:
        return s.connect_ex((HOST, PORT)) == 0
    finally:
        s.close()


def subir():
    """Sobe o servidor numa sessão nova, para sobreviver ao fim do shell da rotina."""
    log = open(LOG, "ab")
    subprocess.Popen(
        [sys.executable, "server.py"],
        cwd=ROOT,
        stdin=subprocess.DEVNULL,
        stdout=log,
        stderr=log,
        start_new_session=True,  # destaca do grupo de processos do chamador
        close_fds=True,
    )


def main():
    if ping():
        print(json.dumps({"status": "online", "url": URL, "ja_estava": True}))
        return 0

    if porta_ocupada() and not ping():
        # processo travado na porta: derruba pelo lsof e tenta subir de novo
        try:
            pids = subprocess.run(["lsof", "-ti", "tcp:%d" % PORT], capture_output=True, text=True).stdout.split()
            for pid in pids:
                subprocess.run(["kill", "-9", pid], capture_output=True)
            time.sleep(1)
        except Exception:
            pass

    subir()
    for _ in range(40):  # até 20 s
        if ping():
            print(json.dumps({"status": "iniciado", "url": URL, "ja_estava": False, "log": LOG}))
            return 0
        time.sleep(0.5)

    print(json.dumps({"status": "erro", "url": URL, "log": LOG,
                      "detalhe": "servidor nao respondeu apos iniciar; veja o server.log"}))
    return 1


if __name__ == "__main__":
    sys.exit(main())
