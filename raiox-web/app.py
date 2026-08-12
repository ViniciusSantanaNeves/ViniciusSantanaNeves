# -*- coding: utf-8 -*-
"""
Raio-X Express 33hosts.
Site em que o proprietário cola o link do anúncio do Airbnb e baixa um PDF
com a análise automática, no design da marca.

Rodar localmente:  uvicorn app:app --host 0.0.0.0 --port 8000
"""
import re
import time
import uuid
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

import analise as motor
import relatorio
import scraper

APP_DIR = Path(__file__).resolve().parent
TRABALHOS = APP_DIR / "trabalhos"
TRABALHOS.mkdir(exist_ok=True)

app = FastAPI(title="Raio-X Express 33hosts")
app.mount("/static", StaticFiles(directory=APP_DIR / "static"), name="static")

_ultimos_pedidos: dict = {}   # controle simples de frequência por IP


PAGINA = """<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Raio-X Express · 33hosts</title>
<style>
@font-face{font-family:"Linear Grotesk";src:url("/static/fonts/LinearGrotesk-Light.ttf");font-weight:300}
@font-face{font-family:"Linear Grotesk";src:url("/static/fonts/LinearGrotesk-Regular.ttf");font-weight:400}
@font-face{font-family:"Linear Grotesk";src:url("/static/fonts/LinearGrotesk-SemiBold.ttf");font-weight:600}
@font-face{font-family:"Linear Grotesk";src:url("/static/fonts/LinearGrotesk-Black.ttf");font-weight:900}
*{box-sizing:border-box}
body{margin:0;background:linear-gradient(180deg,#2C2C2C 0%,#1C1C1C 100%);min-height:100vh;
 font-family:"Linear Grotesk",Arial,sans-serif;color:#fff;display:flex;flex-direction:column}
.wrap{max-width:680px;margin:0 auto;padding:48px 24px;flex:1;display:flex;flex-direction:column;justify-content:center}
.eyebrow{color:#D7C075;font-size:12px;letter-spacing:.18em;font-weight:600;text-transform:uppercase}
h1{font-weight:900;font-size:56px;line-height:1.0;letter-spacing:-0.02em;margin:18px 0 8px}
h1 .gold{color:#D7C075}
.sub{color:#D4D2C8;font-weight:300;font-size:17px;max-width:520px}
form{margin-top:32px;display:flex;gap:10px;flex-wrap:wrap}
input[type=url]{flex:1;min-width:260px;padding:16px 18px;border-radius:999px;border:1.5px solid #333;
 background:#262626;color:#fff;font:inherit;font-size:15px;outline:none}
input[type=url]:focus{border-color:#D7C075}
button{padding:16px 28px;border-radius:999px;border:0;background:#D7C075;color:#1C1C1C;
 font:inherit;font-weight:600;font-size:15px;cursor:pointer}
button:hover{background:#C6AC5B}
button:disabled{opacity:.6;cursor:wait}
.nota{color:#78766C;font-size:13px;margin-top:14px;font-weight:300}
.erro{margin-top:18px;background:#3a2523;border:1px solid #B4534B;color:#f0d9d6;
 border-radius:14px;padding:12px 16px;font-size:14px}
.espera{margin-top:18px;color:#D7C075;font-size:14px;display:none}
footer{border-top:1px solid #333;color:#78766C;font-size:11px;letter-spacing:.16em;
 text-transform:uppercase;padding:18px 24px;display:flex;justify-content:space-between}
footer .slash{color:#D7C075;font-weight:600}
</style></head><body>
<div class="wrap">
  <div class="eyebrow">33hosts <span style="color:#D7C075">/</span> Short Stay Solutions</div>
  <h1>RAIO-X<br><span class="gold">EXPRESS</span></h1>
  <p class="sub">Cole o link do seu anúncio no Airbnb e receba, em um minuto,
  uma análise gratuita em PDF com os primeiros passos para vender mais.</p>
  <form method="post" action="/analisar" onsubmit="enviar(this)">
    <input type="url" name="url" required placeholder="https://www.airbnb.com.br/rooms/..." >
    <button type="submit">Analisar meu anúncio</button>
  </form>
  <p class="espera" id="espera">Analisando o seu anúncio. Isso leva menos de um minuto...</p>
  __ERRO__
  <p class="nota">Funciona com links de anúncios públicos do Airbnb. Nenhuma senha é pedida.</p>
</div>
<footer><span>Anfitriões profissionais.</span>
<span>Raio-X Express <span class="slash">/</span> 33hosts</span></footer>
<script>
function enviar(f){f.querySelector('button').disabled=true;
document.getElementById('espera').style.display='block';}
</script>
</body></html>"""


PAGINA_OK = """<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Análise pronta · Raio-X Express</title>
<style>
body{margin:0;background:linear-gradient(180deg,#2C2C2C 0%,#1C1C1C 100%);min-height:100vh;
 font-family:Arial,sans-serif;color:#fff;display:flex;align-items:center;justify-content:center}
.card{max-width:520px;margin:24px;background:#262626;border:1px solid #333;border-radius:20px;
 padding:36px;text-align:center}
h1{font-size:26px;margin:0 0 10px}
h1 span{color:#D7C075}
p{color:#D4D2C8;font-weight:300;line-height:1.5}
a.botao{display:inline-block;margin-top:18px;padding:16px 30px;border-radius:999px;
 background:#D7C075;color:#1C1C1C;font-weight:700;text-decoration:none}
a.volta{display:block;margin-top:16px;color:#78766C;font-size:13px}
</style></head><body>
<div class="card">
  <h1>Sua análise está <span>pronta</span>.</h1>
  <p>__TITULO__</p>
  <a class="botao" href="/baixar/__ID__">Baixar o PDF da análise</a>
  <a class="volta" href="/">Analisar outro anúncio</a>
</div>
</body></html>"""


@app.get("/", response_class=HTMLResponse)
def inicio():
    return PAGINA.replace("__ERRO__", "")


@app.post("/analisar", response_class=HTMLResponse)
def analisar(url: str = Form(...)):
    agora = time.time()
    # limpeza simples de trabalhos antigos (mais de 2 horas)
    for pasta in TRABALHOS.iterdir():
        try:
            if pasta.is_dir() and agora - pasta.stat().st_mtime > 7200:
                for f in pasta.iterdir():
                    f.unlink()
                pasta.rmdir()
        except OSError:
            pass

    try:
        dados = scraper.coletar(url)
    except scraper.ErroColeta as e:
        return PAGINA.replace("__ERRO__", f'<div class="erro">{e}</div>')
    except Exception:
        return PAGINA.replace("__ERRO__",
                              '<div class="erro">Não conseguimos ler esse anúncio agora. '
                              'Tente novamente em instantes.</div>')

    trabalho = uuid.uuid4().hex[:12]
    pasta = TRABALHOS / trabalho
    pasta.mkdir()

    fotos = scraper.baixar_fotos(dados, pasta / "fotos")

    resultado = motor.montar_analise(dados)
    resultado = motor.enriquecer_com_ia(resultado)

    html_rel = relatorio.render_html(resultado, fotos_dir="fotos/", fotos=fotos)
    # o Chromium precisa achar as fontes: aponta para a pasta static do app
    html_rel = html_rel.replace('url("static/fonts/', f'url("{APP_DIR}/static/fonts/')
    (pasta / "relatorio.html").write_text(html_rel, encoding="utf-8")

    try:
        relatorio.gerar_pdf(html_rel, pasta, pasta / "raiox-express.pdf")
    except Exception:
        raise HTTPException(500, "Falha ao gerar o PDF. Tente novamente.")

    titulo = dados.get("titulo") or "Seu anúncio"
    return PAGINA_OK.replace("__ID__", trabalho).replace("__TITULO__", titulo)


@app.get("/baixar/{trabalho}")
def baixar(trabalho: str):
    if not re.fullmatch(r"[0-9a-f]{12}", trabalho):
        raise HTTPException(404)
    pdf = TRABALHOS / trabalho / "raiox-express.pdf"
    if not pdf.exists():
        raise HTTPException(404, "Análise não encontrada ou expirada.")
    return FileResponse(pdf, filename="Raio-X-Express-33hosts.pdf",
                        media_type="application/pdf")
