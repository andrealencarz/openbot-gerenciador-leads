#!/usr/bin/env python3
"""Servidor local do gerenciador: HTTP + persistência em SQLite."""
import json, sqlite3, http.server, os

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gerenciador.db")
ROOT = os.path.dirname(os.path.abspath(__file__))

def db():
    c = sqlite3.connect(DB)
    c.execute("CREATE TABLE IF NOT EXISTS cidades (id INTEGER PRIMARY KEY AUTOINCREMENT, cidade TEXT, uf TEXT, bairros TEXT, status TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS nichos (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, obs TEXT)")
    return c

def load(c):
    cidades = [{"id": r[0], "cidade": r[1], "uf": r[2], "bairros": json.loads(r[3]), "status": r[4]}
               for r in c.execute("SELECT id,cidade,uf,bairros,status FROM cidades ORDER BY id")]
    nichos = [{"id": r[0], "nome": r[1], "obs": r[2]}
              for r in c.execute("SELECT id,nome,obs FROM nichos ORDER BY id")]
    return {"cidades": cidades, "nichos": nichos}

class H(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def _json(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/api/state":
            c = db()
            try:
                self._json(load(c))
            finally:
                c.close()
            return
        super().do_GET()

    def do_POST(self):
        if self.path == "/api/state":
            n = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(n) or b"{}")
            c = db()
            try:
                ids_c = {r[0] for r in c.execute("SELECT id FROM cidades")}
                for it in data.get("cidades", []):
                    b = json.dumps(it.get("bairros", []), ensure_ascii=False)
                    if it.get("id") in ids_c:
                        c.execute("UPDATE cidades SET cidade=?,uf=?,bairros=?,status=? WHERE id=?",
                                  (it.get("cidade"), it.get("uf"), b, it.get("status"), it["id"]))
                        ids_c.discard(it["id"])
                    else:
                        cur = c.execute("INSERT INTO cidades(cidade,uf,bairros,status) VALUES(?,?,?,?)",
                                        (it.get("cidade"), it.get("uf"), b, it.get("status")))
                        it["id"] = cur.lastrowid
                if ids_c:
                    c.execute("DELETE FROM cidades WHERE id IN (%s)" % ",".join("?" * len(ids_c)), tuple(ids_c))
                ids_n = {r[0] for r in c.execute("SELECT id FROM nichos")}
                for it in data.get("nichos", []):
                    if it.get("id") in ids_n:
                        c.execute("UPDATE nichos SET nome=?,obs=? WHERE id=?", (it.get("nome"), it.get("obs"), it["id"]))
                        ids_n.discard(it["id"])
                    else:
                        cur = c.execute("INSERT INTO nichos(nome,obs) VALUES(?,?)", (it.get("nome"), it.get("obs")))
                        it["id"] = cur.lastrowid
                if ids_n:
                    c.execute("DELETE FROM nichos WHERE id IN (%s)" % ",".join("?" * len(ids_n)), tuple(ids_n))
                c.commit()
                self._json(load(c))
            finally:
                c.close()
            return
        self._json({"erro": "rota desconhecida"}, 404)

if __name__ == "__main__":
    c = db()
    if c.execute("SELECT COUNT(*) FROM cidades").fetchone()[0] == 0 and \
       c.execute("SELECT COUNT(*) FROM nichos").fetchone()[0] == 0:
        print("banco vazio — dados serão importados do navegador na primeira gravação")
    c.close()
    http.server.ThreadingHTTPServer(("127.0.0.1", 8642), H).serve_forever()
