#!/usr/bin/env python3
"""Servidor local do gerenciador: HTTP + persistência em SQLite."""
import json, sqlite3, http.server, os

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gerenciador.db")
ROOT = os.path.dirname(os.path.abspath(__file__))

# tabela -> (colunas simples, colunas que chegam como lista)
TABLES = {
    "cidades":   (["cidade", "uf", "status"], ["bairros"]),
    "nichos":    (["nome", "obs"], []),
    "leads":     (["nome", "telefone", "email", "cidade", "nicho", "site", "status", "obs"], []),
    "campanhas": (["nome", "nicho", "status", "obs"], ["cidades"]),
}

def db():
    c = sqlite3.connect(DB)
    for t, (cols, _) in TABLES.items():
        c.execute("CREATE TABLE IF NOT EXISTS %s (id INTEGER PRIMARY KEY AUTOINCREMENT, %s)" %
                  (t, ", ".join("%s TEXT" % c2 for c2 in cols)))
    return c

def load(c):
    out = {}
    for t, (cols, lists) in TABLES.items():
        allc = cols + lists
        rows = []
        for r in c.execute("SELECT id,%s FROM %s ORDER BY id" % (",".join(allc), t)):
            d = {"id": r[0]}
            for i, k in enumerate(allc):
                d[k] = json.loads(r[i + 1]) if k in lists else r[i + 1]
            rows.append(d)
        out[t] = rows
    return out

def sync(c, data):
    for t, (cols, _) in TABLES.items():
        items = data.get(t, [])
        if not isinstance(items, list):
            continue
        ids_recebidos = set()
        for it in items:
            vals, parts = [], []
            for col in cols:
                vals.append(it.get(col)); parts.append("?")
            for col in TABLES[t][1]:
                vals.append(json.dumps(it.get(col, []), ensure_ascii=False)); parts.append("?")
            if isinstance(it.get("id"), int):
                row = c.execute("SELECT id FROM %s WHERE id=?" % t, (it["id"],)).fetchone()
                if row:
                    c.execute("UPDATE %s SET %s WHERE id=?" % (t, ",".join("%s=?" % x for x in cols + TABLES[t][1])),
                              vals + [it["id"]])
                    ids_recebidos.add(it["id"])
                    continue
            cur = c.execute("INSERT INTO %s(%s) VALUES(%s)" % (t, ",".join(cols + TABLES[t][1]), ",".join(parts)), vals)
            it["id"] = cur.lastrowid
            ids_recebidos.add(it["id"])
        presentes = {r[0] for r in c.execute("SELECT id FROM %s" % t)}
        a_remover = presentes - ids_recebidos
        if a_remover:
            c.execute("DELETE FROM %s WHERE id IN (%s)" % (t, ",".join("?" * len(a_remover))), tuple(a_remover))
    c.commit()

def _norm(s):
    import unicodedata
    s = unicodedata.normalize("NFD", str(s or "")).encode("ascii", "ignore").decode().lower()
    return " ".join(s.split())

def _digits(s):
    return "".join(ch for ch in str(s or "") if ch.isdigit())

def _chave(it):
    tel = _digits(it.get("telefone"))
    if len(tel) >= 10:
        return "tel:" + tel[-10:]
    return "nome:" + _norm(it.get("nome")) + "|" + _norm(it.get("cidade"))

def importar_leads(c, leads, max_novos=None):
    """Insere leads evitando duplicados. Não apaga nada existentes."""
    existentes = set()
    for r in c.execute("SELECT nome, telefone, cidade FROM leads"):
        existentes.add(_chave({"nome": r[0], "telefone": r[1], "cidade": r[2]}))
    novos, duplicados, invalidos = [], 0, 0
    for it in leads or []:
        if not _norm(it.get("nome")):
            invalidos += 1
            continue
        k = _chave(it)
        if k in existentes:
            duplicados += 1
            continue
        if max_novos is not None and len(novos) >= max_novos:
            break
        vals = [
            (it.get("nome") or "").strip(),
            (it.get("telefone") or "").strip(),
            (it.get("email") or "").strip(),
            (it.get("cidade") or "").strip(),
            (it.get("nicho") or "").strip(),
            it.get("site") or "sem site",
            it.get("status") or "novo",
            (it.get("obs") or "").strip(),
        ]
        cur = c.execute(
            "INSERT INTO leads(nome,telefone,email,cidade,nicho,site,status,obs) VALUES(?,?,?,?,?,?,?,?)", vals)
        existentes.add(k)
        novos.append({"id": cur.lastrowid, "nome": vals[0], "cidade": vals[3]})
    # cidades que receberam lead passam de "nao iniciada" para "em andamento"
    cidades_ativas = []
    visitadas = {n["cidade"] for n in novos if n["cidade"]}
    for cidade in visitadas:
        row = c.execute("SELECT id,status FROM cidades WHERE lower(trim(cidade))=lower(trim(?))", (cidade,)).fetchone()
        if row and (row[1] or "") == "nao iniciada":
            c.execute("UPDATE cidades SET status='em andamento' WHERE id=?", (row[0],))
            cidades_ativas.append(cidade)
    c.commit()
    return {"novos": len(novos), "duplicados": duplicados, "invalidos": invalidos,
            "cidades_atualizadas": cidades_ativas, "leads": novos}

class H(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def _json(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self._json({}, 204)

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/api/state":
            c = db()
            try:
                self._json(load(c))
            finally:
                c.close()
            return
        if path == "/api/campanhas":
            c = db()
            try:
                d = load(c)
            finally:
                c.close()
            ativas = [x for x in d["campanhas"] if _norm(x.get("status")) == "ativa"]
            self._json({"total": len(ativas), "campanhas": ativas})
            return
        if path == "/api/ping":
            self._json({"ok": True, "db": os.path.exists(DB)})
            return
        super().do_GET()

    def do_POST(self):
        path = self.path.split("?")[0]
        if path == "/api/state":
            n = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(n) or b"{}")
            c = db()
            try:
                sync(c, data)
                self._json(load(c))
            finally:
                c.close()
            return
        if path == "/api/leads/import":
            n = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(n) or b"{}")
            c = db()
            try:
                res = importar_leads(c, data.get("leads"), data.get("max_novos"))
                self._json(res)
            finally:
                c.close()
            return
        self._json({"erro": "rota desconhecida"}, 404)

if __name__ == "__main__":
    http.server.ThreadingHTTPServer(("127.0.0.1", 8642), H).serve_forever()
