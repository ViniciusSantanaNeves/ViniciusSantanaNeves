# -*- coding: utf-8 -*-
"""
Relatório completo do Raio-X do Anúncio no design system 33hosts
(Linear Grotesk · #1C1C1C · #D7C075). Recebe o dicionário produzido por
raiox_completo.gerar_analise e devolve o HTML; gerar_pdf imprime capa
full-bleed e miolo separados no Chromium e junta com pypdf.
"""
import html
import os
import subprocess
from pathlib import Path

try:
    import markdown as mdlib

    def md(t):
        return mdlib.markdown(t, extensions=["tables", "sane_lists"])
except ImportError:  # fallback mínimo: parágrafos simples
    def md(t):
        pares = "".join(f"<p>{html.escape(p)}</p>" for p in t.split("\n\n") if p.strip())
        return pares

APP_DIR = Path(__file__).resolve().parent
FONTS = (APP_DIR / "static" / "fonts").as_posix()
CHROME = os.environ.get("CHROME_PATH", "chromium")

ST = {"ok": ("✓", "#5B8A6B"), "par": ("△", "#C99A3C"),
      "crit": ("✗", "#B4534B"), "pend": ("◌", "#78766C")}
BL = {"OK": ("#5B8A6B", "OK"), "AJUSTE": ("#C99A3C", "Ajuste"),
      "CRITICO": ("#B4534B", "Crítico"), "PENDENTE": ("#78766C", "Requer painel"),
      "PARCIAL": ("#78766C", "Parcial")}
TILE = {"ok": "#5B8A6B", "alerta": "#C99A3C", "ruim": "#B4534B"}


def _foto(fotos_dir: str, n: int) -> str:
    return f"{fotos_dir}/foto-{n:02d}.jpg"


def render_html(d: dict, data_rotulo: str, fotos_dir: str, fotos_disponiveis: int) -> str:
    cont = {"OK": 0, "AJUSTE": 0, "CRITICO": 0, "PEND": 0}
    fases_html = ""
    for f in d["fases"]:
        blocos_html = ""
        for b in f["blocos"]:
            cor, rotulo = BL.get(b["status"], BL["PARCIAL"])
            cont["PEND" if b["status"] in ("PENDENTE", "PARCIAL") else b["status"]] += 1
            itens = "".join(
                f'<tr><td class="st" style="color:{ST[i["st"]][1]}">{ST[i["st"]][0]}</td>'
                f'<td>{html.escape(i["texto"])}</td></tr>' for i in b["itens"])
            extra = ""
            n_ev = int(b.get("foto_evidencia") or 0)
            if 1 <= n_ev <= fotos_disponiveis:
                extra += (f'<figure class="ev"><img src="{_foto(fotos_dir, n_ev)}">'
                          f'<figcaption>{html.escape(b.get("legenda_evidencia", ""))}</figcaption></figure>')
            if b.get("cod") == "B4" and d.get("galeria"):
                tiles = "".join(
                    f'<div class="tile" style="border-top-color:{TILE[g["selo"]]}">'
                    f'<img src="{_foto(fotos_dir, g["foto"])}">'
                    f'<div class="tile-cap">{html.escape(g["legenda"])}</div></div>'
                    for g in d["galeria"] if 1 <= g["foto"] <= fotos_disponiveis)
                extra += ('<p class="micro">Evidência: amostra da galeria atual (verde funciona, '
                          'amarelo pode melhorar, vermelho remover).</p>'
                          f'<div class="galeria">{tiles}</div>')
            blocos_html += f"""
            <div class="bloco">
              <div class="bloco-head">
                <div class="bloco-nome"><span class="cod">{html.escape(b['cod'])}</span>{html.escape(b['nome'])}</div>
                <div class="badge" style="color:{cor};border-color:{cor}">{rotulo}</div>
              </div>
              <table class="itens">{itens}</table>
              <p class="leitura">{html.escape(b['leitura'])}</p>
              {extra}
            </div>"""
        fases_html += f"""
        <section class="fase">
          <div class="eyebrow">{html.escape(f['fase'])}</div>
          <h2>{html.escape(f['tema'])}.</h2>
          {blocos_html}
        </section>"""

    comp_rows = ""
    placar = {"ok": 0, "par": 0, "crit": 0, "pend": 0}
    for c in d["completude"]:
        ic, cor = ST[c["st"]]
        placar[c["st"]] += 1
        comp_rows += (f'<tr><td class="st" style="color:{cor}">{ic}</td>'
                      f'<td><strong>{html.escape(c["campo"])}</strong></td>'
                      f'<td>{html.escape(c["situacao"])}</td></tr>')
    aval = placar["ok"] + placar["par"] + placar["crit"]
    pct = round(100 * (placar["ok"] + placar["par"] * 0.5) / aval) if aval else 0

    ap_html = ""
    for bl_ in d["aplicacoes"]["blocos"]:
        nota = f'<p class="micro">{html.escape(bl_["nota"])}</p>' if bl_.get("nota") else ""
        ap_html += f'<h3>{html.escape(bl_["titulo"])}</h3>{nota}<div class="copybox">{md(bl_["corpo"])}</div>'

    plano_html = ""
    for p in d["plano"]:
        lis = "".join(f"<li>{html.escape(a)}</li>" for a in p["acoes"])
        plano_html += f'<h3>{html.escape(p["etapa"])}</h3><ol class="plano">{lis}</ol>'

    ctx = "".join(f"<tr><th>{html.escape(c['campo'])}</th><td>{html.escape(c['valor'])}</td></tr>"
                  for c in d["contexto"])

    imovel = d["imovel"]
    oferta = d["oferta"]

    return f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><style>
@font-face {{ font-family:"Linear Grotesk"; src:url("{FONTS}/LinearGrotesk-Light.ttf"); font-weight:300; }}
@font-face {{ font-family:"Linear Grotesk"; src:url("{FONTS}/LinearGrotesk-Regular.ttf"); font-weight:400; }}
@font-face {{ font-family:"Linear Grotesk"; src:url("{FONTS}/LinearGrotesk-Medium.ttf"); font-weight:500; }}
@font-face {{ font-family:"Linear Grotesk"; src:url("{FONTS}/LinearGrotesk-SemiBold.ttf"); font-weight:600; }}
@font-face {{ font-family:"Linear Grotesk"; src:url("{FONTS}/LinearGrotesk-Bold.ttf"); font-weight:700; }}
@font-face {{ font-family:"Linear Grotesk"; src:url("{FONTS}/LinearGrotesk-Black.ttf"); font-weight:900; }}

@page {{ size:A4; margin:16mm 15mm; }}
@page :first {{ margin:0; }}
*{{box-sizing:border-box}}
:root {{
  --gold:#D7C075; --gold-600:#C6AC5B; --gold-100:#F7F1DE;
  --ink:#1C1C1C; --ink-800:#262626; --ink-700:#333333;
  --n50:#FAFAF8; --n100:#F3F2EE; --n200:#E7E5DE; --n300:#D4D2C8; --n500:#78766C; --n600:#57564E;
  --success:#5B8A6B; --warning:#C99A3C; --danger:#B4534B;
  --radius-sm:4px; --radius-md:8px; --radius-card:14px; --radius-xl:20px; --radius-pill:999px;
}}
body{{margin:0;font-family:"Linear Grotesk",Arial,sans-serif;color:var(--ink);line-height:1.45;font-size:10pt;font-weight:300}}
strong{{font-weight:600;color:var(--ink)}}
.cover{{width:210mm;height:297.5mm;background:linear-gradient(180deg,#2C2C2C 0%,#1C1C1C 100%);color:#fff;
  margin:0;padding:22mm 20mm;display:flex;flex-direction:column;page-break-after:always}}
.cover .eyebrow{{color:var(--gold);font-size:8.5pt;letter-spacing:.18em;font-weight:500;text-transform:uppercase}}
.cover .stack{{margin:auto 0;padding-top:20mm}}
.cover .stack .l{{display:block;font-weight:900;font-size:52pt;line-height:1.0;letter-spacing:-0.02em}}
.cover .stack .gold{{color:var(--gold)}}
.cover .sub{{font-weight:300;font-size:12.5pt;color:#D4D2C8;margin-top:10mm;max-width:150mm}}
.cover .sub b{{font-weight:500;color:#fff}}
.cover .foot{{margin-top:auto;border-top:1px solid var(--ink-700);padding-top:5mm;display:flex;justify-content:space-between;
  font-size:8pt;letter-spacing:.18em;text-transform:uppercase;color:var(--n500)}}
.slash{{color:var(--gold);font-weight:600}}
.sec{{page-break-before:always}}
.fase{{page-break-before:always}}
.eyebrow{{font-size:8pt;letter-spacing:.18em;text-transform:uppercase;color:var(--gold-600);font-weight:600;margin-bottom:2mm}}
h2{{font-weight:900;font-size:19pt;letter-spacing:-0.02em;line-height:1.05;margin:0 0 6mm;color:var(--ink)}}
h3{{font-weight:700;font-size:11pt;letter-spacing:-0.01em;margin:6mm 0 2mm;color:var(--ink);page-break-after:avoid}}
p{{margin:0 0 3mm;orphans:3;widows:3}}
.micro{{font-size:8pt;color:var(--n500);letter-spacing:.02em;margin:0 0 2mm}}
.placar{{display:flex;gap:4mm;margin:5mm 0}}
.placar div{{flex:1;background:#fff;border:1px solid var(--n200);border-radius:var(--radius-xl);padding:4mm 2mm;text-align:center;
  box-shadow:0 1px 3px rgba(28,28,28,.06)}}
.placar b{{display:block;font-weight:900;font-size:17pt;letter-spacing:-0.02em}}
.placar span{{font-size:7.2pt;letter-spacing:.14em;text-transform:uppercase;color:var(--n500);font-weight:500}}
.bar-phrase{{border-left:4px solid var(--gold);padding:2mm 0 2mm 5mm;margin:5mm 0;font-weight:400}}
.legenda{{background:var(--n50,#F7F6F2);border:1px solid var(--n200);border-radius:var(--radius-card,14px);
  padding:3.5mm 5mm;margin:4mm 0;page-break-inside:avoid}}
.leg-grid{{display:grid;grid-template-columns:1fr 1fr;gap:1mm 6mm;font-size:9pt;color:var(--n600)}}
.leg-grid b{{display:inline-block;width:5mm}}
table{{border-collapse:separate;border-spacing:0;width:100%;margin:3mm 0;font-size:8.7pt;
  border:1px solid var(--n200);border-radius:var(--radius-card);overflow:hidden}}
th,td{{border:0;border-bottom:1px solid var(--n200);border-right:1px solid var(--n200);
  padding:1.8mm 2.6mm;text-align:left;vertical-align:top;font-weight:300}}
tr td:last-child,tr th:last-child{{border-right:0}}
tr:last-child td{{border-bottom:0}}
th{{background:var(--n100);font-weight:600;font-size:8.3pt}}
.ctx th{{width:30%}}
.bloco{{background:#fff;border:1px solid var(--n200);border-radius:var(--radius-xl);padding:3.4mm 5mm;margin:2.4mm 0;
  box-shadow:0 1px 3px rgba(28,28,28,.05);page-break-inside:avoid}}
.bloco-head{{display:flex;justify-content:space-between;align-items:center;margin-bottom:2.5mm}}
.bloco-nome{{font-weight:700;font-size:11.5pt;letter-spacing:-0.01em}}
.cod{{color:var(--gold-600);font-weight:900;margin-right:2.5mm}}
.badge{{font-size:8pt;font-weight:600;letter-spacing:.06em;border:1.5px solid;border-radius:var(--radius-pill);padding:1mm 4mm;white-space:nowrap}}
.itens{{margin:2mm 0;border:0;border-radius:0}}
.itens td{{border:none;border-bottom:1px solid var(--n100);padding:1.3mm 2mm}}
.itens .st{{width:6mm;font-weight:700}}
.leitura{{color:var(--n600);font-weight:300;margin:2.5mm 0 1mm}}
.ev{{margin:3mm 0 1mm;text-align:center;page-break-inside:avoid}}
.ev img{{max-width:60%;max-height:78mm;border-radius:var(--radius-md);border:1px solid var(--n200)}}
.ev figcaption{{font-size:8pt;color:var(--n500);margin-top:1.5mm}}
.galeria{{display:grid;grid-template-columns:repeat(5,1fr);gap:2.5mm;margin:2mm 0;page-break-inside:avoid}}
.tile{{border-radius:var(--radius-md);overflow:hidden;border:1px solid var(--n200);border-top:3px solid var(--n300);background:#fff}}
.tile img{{width:100%;height:22mm;object-fit:cover;display:block}}
.tile-cap{{font-size:6.6pt;color:var(--n600);padding:1.4mm 2mm;line-height:1.25;font-weight:400}}
.copybox{{background:#fff;border:1px solid var(--n200);border-left:4px solid var(--gold);border-radius:var(--radius-card);
  padding:4mm 5mm;margin:2mm 0 5mm;page-break-inside:avoid}}
.copybox p,.copybox li{{font-weight:300}}
.copybox strong{{font-weight:600}}
ol.plano li,ul li{{margin-bottom:1.6mm;font-weight:300}}
ol.plano{{padding-left:6mm}}
.oferta{{background:linear-gradient(180deg,#2C2C2C 0%,#1C1C1C 100%);color:#F3F2EE;margin:10mm 0 0;
  padding:10mm 12mm;border-radius:var(--radius-xl);page-break-inside:avoid}}
.oferta .eyebrow{{color:var(--gold)}}
.oferta h2{{color:#fff}}
.oferta h2 .gold{{color:var(--gold)}}
.oferta p{{color:#D4D2C8;font-weight:300}}
.oferta strong{{color:#fff;font-weight:600}}
.oferta .foot{{border-top:1px solid var(--ink-700);margin-top:7mm;padding-top:4mm;display:flex;justify-content:space-between;
  font-size:7.6pt;letter-spacing:.16em;text-transform:uppercase;color:var(--n500)}}
</style></head><body>

<div class="cover">
  <div class="eyebrow">33hosts <span class="slash">/</span> Short Stay Solutions</div>
  <div class="stack">
    <span class="l">RAIO-X</span>
    <span class="l">DO <span class="gold">ANÚNCIO</span></span>
    <div class="sub"><b>{html.escape(imovel)}</b><br>Avaliação completa em 18 blocos e 6 fases, com evidências e plano de ação.</div>
  </div>
  <div class="foot"><span>Anfitriões profissionais.</span><span>Raio-X <span class="slash">/</span> {html.escape(data_rotulo)}</span></div>
</div>

<div>
  <div class="eyebrow">Sumário executivo</div>
  <h2>O diagnóstico em uma página.</h2>
  <div class="placar">
    <div><b style="color:var(--success)">{cont['OK']}</b><span>Blocos OK</span></div>
    <div><b style="color:var(--warning)">{cont['AJUSTE']}</b><span>Em ajuste</span></div>
    <div><b style="color:var(--danger)">{cont['CRITICO']}</b><span>Críticos</span></div>
    <div><b style="color:var(--n500)">{cont['PEND']}</b><span>Requerem painel</span></div>
  </div>
  <div class="legenda">
    <p class="micro" style="margin-bottom:1.5mm"><strong>Como ler este relatório</strong></p>
    <div class="leg-grid">
      <span><b style="color:var(--success)">✓</b> Item está bem</span>
      <span><b style="color:var(--warning)">△</b> Item pode melhorar</span>
      <span><b style="color:var(--danger)">✗</b> Item precisa de correção</span>
      <span><b style="color:var(--n500)">◌</b> Item a conferir no painel do anúncio</span>
    </div>
    <p class="micro" style="margin:2mm 0 0">Cada bloco recebe um selo geral: <b style="color:var(--success)">OK</b> (está bem) ·
    <b style="color:var(--warning)">Ajuste</b> (pode melhorar) · <b style="color:var(--danger)">Crítico</b> (corrigir primeiro) ·
    <b style="color:var(--n500)">Parcial ou Requer painel</b> (depende de conferência interna).</p>
  </div>
  {md(d['resumo'])}
</div>

<div class="sec">
  <div class="eyebrow">Ponto de partida</div>
  <h2>Contexto do imóvel.</h2>
  <p>Diagnóstico externo realizado a partir do anúncio público no Airbnb em {html.escape(data_rotulo.lower())}. Blocos marcados
  “Requer painel” dependem de acesso ao painel do anúncio e são cobertos na implementação.</p>
  <table class="ctx">{ctx}</table>
</div>

{fases_html}

<div class="sec">
  <div class="eyebrow">Anexo <span class="slash">/</span> completude</div>
  <h2>Auditoria campo a campo do editor.</h2>
  <p>Conferência de preenchimento de cada seção do editor do Airbnb, excluído o Guia de Chegada.
  Campo vazio é bônus algorítmico desperdiçado.</p>
  <div class="placar">
    <div><b style="color:var(--success)">{placar['ok']}</b><span>Preenchidos</span></div>
    <div><b style="color:var(--warning)">{placar['par']}</b><span>Parciais</span></div>
    <div><b style="color:var(--danger)">{placar['crit']}</b><span>Vazios ou errados</span></div>
    <div><b style="color:var(--n500)">{placar['pend']}</b><span>Confirmar no painel</span></div>
  </div>
  <p class="bar-phrase"><strong>Completude estimada: {pct}%</strong> nos {aval} campos auditáveis externamente.</p>
  <table><tr><th style="width:7mm"></th><th>Campo</th><th>Situação</th></tr>{comp_rows}</table>
</div>

<div class="sec">
  <div class="eyebrow">Aplicações prontas <span class="slash">/</span> saída do B5</div>
  <h2>Título, descrição e radar prontos para aplicar.</h2>
  {md(d['aplicacoes']['intro'])}
  {ap_html}
</div>

<div class="sec">
  <div class="eyebrow">Prioridades</div>
  <h2>Plano de ação 30 <span style="color:var(--gold-600)">/</span> 60 <span style="color:var(--gold-600)">/</span> 90 dias.</h2>
  {plano_html}

  <div class="oferta">
    <div class="eyebrow">Próximos passos</div>
    <h2>Sua <span class="gold">receita</span> tem plano e nome.</h2>
    <p>{html.escape(oferta)}</p>
    <p><strong>Falar com a 33hosts.</strong> Nosso especialista conduz a implementação e acompanha os
    resultados com você.</p>
    <div class="foot"><span>Anfitriões profissionais.</span><span>33hosts <span class="slash">/</span> Raio-X do Anúncio</span></div>
  </div>
</div>

</body></html>"""


def gerar_pdf(html_completo: str, pasta_trabalho: Path, pdf_final: Path) -> Path:
    """Imprime capa (margem zero, full-bleed) e miolo separados e junta no PDF final."""
    marcador = '<div class="eyebrow">Sumário executivo</div>'
    i = html_completo.index(marcador)
    i = html_completo.rindex("<div>", 0, i)
    head = html_completo[:i]
    resto = html_completo[i:]

    j = head.index('<div class="cover">')
    estilo, capa = head[:j], head[j:]

    doc_capa = (estilo + "<style>@page{margin:0 !important}.cover{width:210mm;height:297mm;margin:0}</style>"
                + capa + "</body></html>")
    doc_miolo = (estilo + "<style>@page :first{margin:16mm 15mm}</style>" + resto)

    p_capa = pasta_trabalho / "_capa.html"
    p_miolo = pasta_trabalho / "_miolo.html"
    p_capa.write_text(doc_capa, encoding="utf-8")
    p_miolo.write_text(doc_miolo, encoding="utf-8")

    pdf_capa = pasta_trabalho / "_capa.pdf"
    pdf_miolo = pasta_trabalho / "_miolo.pdf"
    for origem, destino in [(p_capa, pdf_capa), (p_miolo, pdf_miolo)]:
        subprocess.run([CHROME, "--headless", "--no-sandbox", "--disable-gpu",
                        "--no-pdf-header-footer", f"--print-to-pdf={destino}",
                        f"file://{origem}"], check=True, capture_output=True, timeout=180)

    from pypdf import PdfWriter
    w = PdfWriter()
    w.append(str(pdf_capa), pages=(0, 1))
    w.append(str(pdf_miolo))
    with open(pdf_final, "wb") as f:
        w.write(f)
    return pdf_final
