#!/usr/bin/env python3
"""Servidor do Parábola Scanner: app estático + integração de vendas com o Bling (API v3)."""

import base64
import hashlib
import hmac
import json
import os
import re
import threading
import time
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PORT = int(os.environ.get("PORT", 8000))
ROOT = Path(__file__).parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)

BLING_CLIENT_ID = os.environ.get("BLING_CLIENT_ID", "")
BLING_CLIENT_SECRET = os.environ.get("BLING_CLIENT_SECRET", "")
BLING_API = "https://api.bling.com.br/Api/v3"
BLING_AUTH = "https://bling.com.br/Api/v3/oauth/authorize"
BLING_TOKEN = "https://api.bling.com.br/Api/v3/oauth/token"

TOKENS_FILE = DATA / "bling_tokens.json"
MAP_FILE = DATA / "bling_ids.json"
DONE_FILE = DATA / "vendas_processadas.json"

_lock = threading.Lock()


# ---------------- token store ----------------

def _load(f, default):
    try:
        return json.loads(f.read_text())
    except Exception:
        return default


def _save(f, obj):
    f.write_text(json.dumps(obj, ensure_ascii=False))


def bling_configured():
    return bool(BLING_CLIENT_ID and BLING_CLIENT_SECRET)


# ---------------- sessão do app (login das vendedoras via Bling) ----------------

SESSION_DAYS = 180


def _hmac(msg):
    return hmac.new(BLING_CLIENT_SECRET.encode(), msg.encode(),
                    hashlib.sha256).hexdigest()[:32]


def make_session():
    exp = str(int(time.time() + SESSION_DAYS * 86400))
    return f"{exp}.{_hmac(exp)}"


def check_session(token):
    try:
        exp, sig = (token or "").split(".")
        return hmac.compare_digest(sig, _hmac(exp)) and time.time() < int(exp)
    except Exception:
        return False


# states pendentes do OAuth com validade (sobrevive a corrida de deploy)
def _states():
    st = _load(DATA / "oauth_state.json", {})
    if not isinstance(st, dict) or "state" in st:  # formato antigo
        st = {}
    return {k: v for k, v in st.items() if time.time() - v < 1200}


def bling_connected():
    return TOKENS_FILE.exists()


def _token_request(payload):
    basic = base64.b64encode(f"{BLING_CLIENT_ID}:{BLING_CLIENT_SECRET}".encode()).decode()
    req = urllib.request.Request(
        BLING_TOKEN,
        data=urllib.parse.urlencode(payload).encode(),
        headers={
            "Authorization": f"Basic {basic}",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        tok = json.loads(r.read())
    tok["expires_at"] = time.time() + tok.get("expires_in", 21600) - 120
    _save(TOKENS_FILE, tok)
    return tok


def access_token():
    with _lock:
        tok = _load(TOKENS_FILE, None)
        if not tok:
            raise RuntimeError("Bling não conectado. Abra /api/bling/conectar")
        if time.time() >= tok.get("expires_at", 0):
            tok = _token_request({"grant_type": "refresh_token",
                                  "refresh_token": tok["refresh_token"]})
        return tok["access_token"]


def bling(method, path, body=None, params=None):
    url = BLING_API + path
    if params:
        url += "?" + urllib.parse.urlencode(params, doseq=True)
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": f"Bearer {access_token()}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Bling {e.code} em {path}: {e.read().decode()[:400]}")


# ---------------- catálogo: mapa ISBN -> produto Bling ----------------

def _norm_titulo(s):
    import unicodedata
    s = unicodedata.normalize("NFD", (s or "").lower()).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    s = re.sub(r"^(a|o|as|os|um|uma) ", "", s.strip())
    return re.sub(r"\s+", " ", s)


def build_product_map():
    """Casa os ISBNs do catálogo com os produtos do Bling por SKU e por nome.
    (A listagem do Bling não expõe GTIN, mas expõe codigo/nome.)"""
    try:
        extra = _load(ROOT / "isbn_extra.json", {})
        # 1) baixa o catálogo inteiro do Bling (codigo, nome, preco)
        produtos, page = [], 1
        while True:
            res = bling("GET", "/produtos", params={
                "pagina": page, "limite": 100, "criterio": 2, "tipo": "P"})
            rows = res.get("data", [])
            if not rows:
                break
            produtos.extend(rows)
            page += 1
            time.sleep(0.35)
        por_sku = {str(p.get("codigo") or "").strip(): p
                   for p in produtos if str(p.get("codigo") or "").strip()}
        por_nome = {_norm_titulo(p.get("nome")): p for p in produtos}

        # 2) casa cada ISBN: SKU exato -> nome exato -> nome contém
        mapa, sku_hits, nome_hits, sem = {}, 0, 0, []
        for isbn, info in extra.items():
            p = por_sku.get(str(info.get("sku") or "").strip())
            if p:
                sku_hits += 1
            else:
                nt = _norm_titulo(info.get("t"))
                p = por_nome.get(nt)
                if not p and len(nt) >= 15:
                    p = next((v for k, v in por_nome.items()
                              if len(k) >= 15 and (k.startswith(nt[:25]) or nt.startswith(k[:25]))), None)
                if p:
                    nome_hits += 1
            if p:
                mapa[isbn] = {"id": p["id"], "nome": p.get("nome", ""),
                              "preco": p.get("preco", 0)}
            else:
                sem.append(info.get("t", isbn)[:40])
        _save(MAP_FILE, mapa)
        _save(DATA / "map_status.json",
              {"ok": True, "produtosBling": len(produtos), "casadosPorSku": sku_hits,
               "casadosPorNome": nome_hits, "semMatch": sem[:40],
               "quando": datetime.now().isoformat()})
        return mapa
    except Exception as e:
        _save(DATA / "map_status.json",
              {"ok": False, "erro": str(e)[:500], "quando": datetime.now().isoformat()})
        raise


def product_map():
    return _load(MAP_FILE, {})


# ---------------- venda ----------------

def _consumidor_final():
    try:
        res = bling("GET", "/contatos/consumidor-final")
        return res["data"]
    except RuntimeError as e:
        if "insufficient_scope" not in str(e):
            raise
        # sem escopo de Contatos: acha o Consumidor Final nos pedidos recentes
        # (as vendas manuais da frente de caixa usam ele)
        res = bling("GET", "/pedidos/vendas", params={"pagina": 1, "limite": 100})
        for p in res.get("data", []):
            c = p.get("contato") or {}
            if c.get("id") and "consumidor" in (c.get("nome") or "").lower():
                return {"id": c["id"], "nome": c["nome"]}
        raise


def _formas_pagamento():
    res = bling("GET", "/formas-pagamentos", params={"pagina": 1, "limite": 100})
    return [f for f in res.get("data", []) if f.get("situacao", 1) == 1]


def _norm(s):
    import unicodedata
    return unicodedata.normalize("NFD", (s or "").lower()) \
        .encode("ascii", "ignore").decode()


def forma_pagamento_id(tipo):
    """tipo: pix | dinheiro | cartao. Resolve pro ID cadastrado no Bling."""
    formas = cached("formas_pagamento", _formas_pagamento)
    busca = {
        "pix": ["pix"],
        "dinheiro": ["dinheiro"],
        "cartao": ["cartao de credito", "credito", "cartao"],
    }.get(_norm(tipo) or "dinheiro", ["dinheiro"])
    for termo in busca:
        for f in formas:
            if termo in _norm(f.get("descricao")):
                return f["id"]
    for f in formas:  # fallback: dinheiro, senão a primeira ativa
        if "dinheiro" in _norm(f.get("descricao")):
            return f["id"]
    return formas[0]["id"] if formas else None


_cache = {}


def cached(key, fn, ttl=3600):
    v = _cache.get(key)
    if v and time.time() - v[0] < ttl:
        return v[1]
    r = fn()
    _cache[key] = (time.time(), r)
    return r


def criar_contato(cust):
    nome = (cust.get("nome") or "").strip()
    cel = re.sub(r"\D", "", cust.get("whatsapp") or "")
    cpf = re.sub(r"\D", "", cust.get("cpf") or "")
    email = (cust.get("email") or "").strip()
    if not (nome or cel or cpf or email):
        return None
    if not nome:
        nome = f"Cliente {cel[-4:] if cel else cpf[-4:] if cpf else 'Feira'} " + \
               datetime.now().strftime("%d/%m")
    body = {"nome": nome, "tipo": "F", "situacao": "A"}
    if cel:
        body["celular"] = cel
    if cpf:
        body["numeroDocumento"] = cpf
    if email:
        body["email"] = email
    res = bling("POST", "/contatos", body=body)
    return {"id": res["data"]["id"], "nome": nome}


def _resolver_produto(isbn):
    mapa = product_map()
    prod = mapa.get(isbn)
    if not prod:
        res = bling("GET", "/produtos", params={"gtins[]": isbn, "limite": 5})
        rows = res.get("data", [])
        if not rows:
            raise RuntimeError(f"ISBN {isbn} não encontrado no Bling")
        p = rows[0]
        prod = {"id": p["id"], "nome": p.get("nome", ""), "preco": p.get("preco", 0)}
        mapa[isbn] = prod
        _save(MAP_FILE, mapa)
    return prod


def processar_venda(venda):
    """venda: {id, itens:[{isbn,quantidade,titulo,preco}], pagamento, cliente}
    (ou formato antigo com isbn/quantidade no topo)"""
    done = _load(DONE_FILE, {})
    vid = venda["id"]
    if vid in done:
        return done[vid]  # idempotente: retry não duplica

    itens_in = venda.get("itens") or [{"isbn": venda.get("isbn"),
                                       "quantidade": venda.get("quantidade") or 1,
                                       "preco": venda.get("preco")}]
    itens, total = [], 0.0
    for it in itens_in:
        isbn = re.sub(r"\D", "", str(it.get("isbn") or ""))
        if len(isbn) != 13:
            raise RuntimeError(f"ISBN inválido: {it.get('isbn')}")
        prod = _resolver_produto(isbn)
        qtd = max(1, int(it.get("quantidade") or 1))
        preco = float(prod.get("preco") or it.get("preco") or 0)
        total += preco * qtd * 0.80
        itens.append({
            "produto": {"id": prod["id"]},
            "descricao": prod["nome"] or it.get("titulo", ""),
            "quantidade": qtd,
            "valor": preco,
            "desconto": 20,
        })
    total = round(total, 2)

    contato = None
    if venda.get("cliente"):
        try:
            contato = criar_contato(venda["cliente"])
        except Exception:
            contato = None  # cadastro é opcional: nunca trava a venda
    if not contato:
        cf = cached("consumidor_final", _consumidor_final)
        contato = {"id": cf["id"], "nome": cf.get("nome", "Consumidor Final")}

    hoje = date.today().isoformat()
    pedido = {
        "data": hoje,
        "contato": {"id": contato["id"], "nome": contato["nome"]},
        "itens": itens,
        "parcelas": [{
            "dataVencimento": hoje,
            "valor": total,
            "formaPagamento": {"id": forma_pagamento_id(venda.get("pagamento"))},
        }],
        "observacoesInternas": f"Parabola Scanner · venda {vid}",
    }
    res = bling("POST", "/pedidos/vendas", body=pedido)
    pedido_id = res["data"]["id"]
    try:
        bling("POST", f"/pedidos/vendas/{pedido_id}/lancar-estoque")
    except Exception:
        pass  # estoque pode já baixar por configuração da conta

    result = {"pedidoId": pedido_id, "numero": res["data"].get("numero"),
              "total": total, "contato": contato["nome"]}
    done[vid] = result
    _save(DONE_FILE, done)
    return result


# ---------------- HTTP ----------------

ALLOWED = {"/index.html", "/books.js", "/embeddings.bin", "/embeddings.json",
           "/sw.js", "/manifest.webmanifest", "/icon-192.png", "/icon-512.png",
           "/favicon.ico"}
ALLOWED_PREFIX = ("/thumbs/", "/model/", "/vendor/")


class AppHandler(SimpleHTTPRequestHandler):
    extensions_map = {
        **SimpleHTTPRequestHandler.extensions_map,
        ".webmanifest": "application/manifest+json",
        ".bin": "application/octet-stream",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def _json(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _redirect(self, url):
        self.send_response(302)
        self.send_header("Location", url)
        self.end_headers()

    # ---- GET ----
    def do_GET(self):
        path, _, query = self.path.partition("?")
        qs = urllib.parse.parse_qs(query)

        if path == "/api/bling/status":
            return self._json({
                "versao": 11,
                "configurado": bling_configured(),
                "conectado": bling_connected(),
                "produtosMapeados": len(product_map()),
            })

        if path == "/api/auth/check":
            return self._json({"ok": check_session(qs.get("token", [""])[0])})

        if path == "/api/bling/conectar":
            if not bling_configured():
                return self._json({"erro": "Defina BLING_CLIENT_ID e BLING_CLIENT_SECRET"}, 500)
            state = base64.urlsafe_b64encode(os.urandom(18)).decode()
            states = _states()
            states[state] = time.time()
            _save(DATA / "oauth_state.json", states)
            return self._redirect(BLING_AUTH + "?" + urllib.parse.urlencode({
                "response_type": "code", "client_id": BLING_CLIENT_ID, "state": state}))

        if path == "/api/bling/callback":
            states = _states()
            got = qs.get("state", [""])[0]
            if not qs.get("code") or got not in states:
                return self._redirect("/?login=expirado")
            states.pop(got, None)
            _save(DATA / "oauth_state.json", states)
            try:
                _token_request({"grant_type": "authorization_code", "code": qs["code"][0]})
            except Exception as e:
                return self._json({"erro": f"troca de token falhou: {e}"}, 500)
            if len(product_map()) < 50:
                threading.Thread(target=build_product_map, daemon=True).start()
            return self._redirect("/?sessao=" + make_session())

        if path == "/api/bling/debug":
            if qs.get("chave", [""])[0] != BLING_CLIENT_SECRET[:10]:
                return self._json({"erro": "chave inválida"}, 403)
            out = {"mapStatus": _load(DATA / "map_status.json", "nunca rodou")}
            try:
                res = bling("GET", "/produtos", params={"pagina": 1, "limite": 3, "criterio": 2, "tipo": "P"})
                rows = res.get("data", [])
                out["amostraProdutos"] = [
                    {"id": p.get("id"), "nome": (p.get("nome") or "")[:40],
                     "gtin": p.get("gtin"), "codigo": p.get("codigo"),
                     "preco": p.get("preco")} for p in rows]
                out["chaves1oProduto"] = sorted(rows[0].keys()) if rows else []
            except Exception as e:
                out["erroProdutos"] = str(e)[:400]
            try:
                out["formasPagamento"] = [
                    {"id": f["id"], "descricao": f.get("descricao")}
                    for f in cached("formas_pagamento", _formas_pagamento)]
            except Exception as e:
                out["erroFormas"] = str(e)[:200]
            try:
                res = bling("GET", "/pedidos/vendas", params={"pagina": 1, "limite": 3})
                rows = res.get("data", [])
                out["pedidosAmostra"] = [{"id": p.get("id"), "numero": p.get("numero"),
                                          "contato": p.get("contato")} for p in rows]
                out["chaves1oPedido"] = sorted(rows[0].keys()) if rows else []
            except Exception as e:
                out["erroPedidos"] = str(e)[:300]
            return self._json(out)

        if path == "/api/bling/testar-venda":
            # guarda simples: exige os 10 primeiros chars do client_secret
            if qs.get("chave", [""])[0] != BLING_CLIENT_SECRET[:10]:
                return self._json({"erro": "chave inválida"}, 403)
            if not bling_connected():
                return self._json({"erro": "não conectado"}, 400)
            rel = {"passos": []}
            try:
                mapa = product_map()
                if not mapa:
                    return self._json({"erro": "mapa de produtos vazio — rode /api/bling/mapear"}, 400)
                isbn = min(mapa, key=lambda k: mapa[k].get("preco") or 9e9)
                venda = {"id": f"TESTE-{int(time.time())}", "isbn": isbn,
                         "titulo": mapa[isbn]["nome"], "quantidade": 1}
                r = processar_venda(venda)
                rel["passos"].append({"criar": r})
                pid = r["pedidoId"]
                ped = bling("GET", f"/pedidos/vendas/{pid}")["data"]
                rel["passos"].append({"conferir": {
                    "numero": ped.get("numero"), "total": ped.get("total"),
                    "item": ped.get("itens", [{}])[0].get("descricao", "")}})
                for acao in ("estornar-estoque", "estornar-contas"):
                    try:
                        bling("POST", f"/pedidos/vendas/{pid}/{acao}")
                        rel["passos"].append({acao: "ok"})
                    except Exception as e:
                        rel["passos"].append({acao: f"ignorado: {str(e)[:120]}"})
                bling("DELETE", f"/pedidos/vendas/{pid}")
                rel["passos"].append({"excluir": "ok"})
                done = _load(DONE_FILE, {})
                done.pop(venda["id"], None)
                _save(DONE_FILE, done)
                rel["resultado"] = "SUCESSO: venda criada e cancelada, conta limpa"
                return self._json(rel)
            except Exception as e:
                rel["erro"] = str(e)[:400]
                return self._json(rel, 502)

        if path == "/api/bling/mapear":
            if not bling_connected():
                return self._json({"erro": "não conectado"}, 400)
            threading.Thread(target=build_product_map, daemon=True).start()
            return self._json({"ok": "mapeamento iniciado em background"})

        if path == "/" or path == "/book-scanner.html":
            self.path = "/index.html"
        elif path not in ALLOWED and not path.startswith(ALLOWED_PREFIX):
            self.send_error(404)
            return
        super().do_GET()

    # ---- POST ----
    def do_POST(self):
        path = self.path.partition("?")[0]
        if path != "/api/vender":
            self.send_error(404)
            return
        try:
            n = int(self.headers.get("Content-Length", 0))
            venda = json.loads(self.rfile.read(n))
        except Exception:
            return self._json({"erro": "JSON inválido"}, 400)
        if not check_session(self.headers.get("X-Sessao", "")):
            return self._json({"erro": "sessão inválida — faça login", "login": True}, 401)
        tem_itens = isinstance(venda.get("itens"), list) and len(venda["itens"]) > 0
        tem_isbn = re.fullmatch(r"\d{13}", str(venda.get("isbn", "")))
        if not venda.get("id") or not (tem_itens or tem_isbn):
            return self._json({"erro": "id e itens/isbn são obrigatórios"}, 400)
        if tem_itens and len(venda["itens"]) > 50:
            return self._json({"erro": "máximo 50 itens por venda"}, 400)
        if not bling_connected():
            return self._json({"erro": "Bling não conectado", "retry": True}, 503)
        try:
            return self._json({"ok": True, **processar_venda(venda)})
        except Exception as e:
            retry = "não encontrado" not in str(e)
            return self._json({"erro": str(e)[:300], "retry": retry}, 502 if retry else 422)

    def end_headers(self):
        if self.path.startswith(ALLOWED_PREFIX):
            self.send_header("Cache-Control", "public, max-age=31536000, immutable")
        elif not self.path.startswith("/api/"):
            self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def list_directory(self, path):
        self.send_error(404)
        return None

    def log_message(self, fmt, *args):
        if "/api/" in str(args[0] if args else ""):
            super().log_message(fmt, *args)


if __name__ == "__main__":
    print(f"Parábola Scanner na porta {PORT} | Bling: "
          f"{'configurado' if bling_configured() else 'SEM credenciais'} / "
          f"{'conectado' if bling_connected() else 'não conectado'}")
    ThreadingHTTPServer.allow_reuse_address = True
    ThreadingHTTPServer(("", PORT), AppHandler).serve_forever()
