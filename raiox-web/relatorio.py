# -*- coding: utf-8 -*-
"""Gera o relatório em HTML (design system 33hosts) e o PDF com capa inteira."""
import html as H
import os
import subprocess
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
CHROME = os.environ.get("CHROME_PATH", "chromium")

ST = {"ok": ("&#10003;", "#5B8A6B"), "par": ("&#9651;", "#C99A3C"),
      "crit": ("&#10007;", "#B4534B"), "pend": ("&#9676;", "#78766C")}
BADGE = {"OK": ("#5B8A6B", "Está bem"), "AJUSTE": ("#C99A3C", "Pode melhorar"),
         "CRITICO": ("#B4534B", "Precisa de correção"),
         "PENDENTE": ("#78766C", "Conferir na conta")}

CSS = """
@page { size:A4; margin:16mm 15mm; }
*{box-sizing:border-box}
:root{
  --gold:#D7C075; --gold-600:#C6AC5B; --ink:#1C1C1C; --ink-700:#333333;
  --n100:#F3F2EE; --n200:#E7E5DE; --n300:#D4D2C8; --n500:#78766C; --n600:#57564E;
  --r-md:8px; --r-card:14px; --r-xl:20px; --r-pill:999px;
}
body{margin:0;font-family:"Linear Grotesk",Arial,sans-serif;color:var(--ink);
  line-height:1.5;font-size:10.4pt;font-weight:300}
strong{font-weight:600;color:var(--ink)}
.cover{width:210mm;height:297.5mm;background:linear-gradient(180deg,#2C2C2C 0%,#1C1C1C 100%);
  color:#fff;margin:0;padding:22mm 20mm;display:flex;flex-direction:column;page-break-after:always}
.cover .eyebrow{color:var(--gold);font-size:8.5pt;letter-spacing:.18em;font-weight:500;text-transform:uppercase}
.cover .stack{margin:auto 0;padding-top:18mm}
.cover .stack .l{display:block;font-weight:900;font-size:44pt;line-height:1.02;letter-spacing:-0.02em}
.cover .stack .gold{color:var(--gold)}
.cover .sub{font-weight:300;font-size:12pt;color:#D4D2C8;margin-top:9mm;max-width:155mm}
.cover .sub b{font-weight:500;color:#fff}
.cover .foot{margin-top:auto;border-top:1px solid var(--ink-700);padding-top:5mm;display:flex;
  justify-content:space-between;font-size:8pt;letter-spacing:.18em;text-transform:uppercase;color:var(--n500)}
.slash{color:var(--gold);font-weight:600}
.eyebrow{font-size:8pt;letter-spacing:.18em;text-transform:uppercase;color:var(--gold-600);
  font-weight:600;margin-bottom:2mm}
h2{font-weight:900;font-size:18pt;letter-spacing:-0.02em;line-height:1.05;margin:0 0 5mm;color:var(--ink)}
h3{font-weight:700;font-size:11pt;margin:6mm 0 2mm;color:var(--ink);page-break-after:avoid}
p{margin:0 0 3mm;orphans:3;widows:3}
.sec{page-break-before:always}
.placar{display:flex;gap:4mm;margin:5mm 0}
.placar div{flex:1;background:#fff;border:1px solid var(--n200);border-radius:var(--r-xl);
  padding:4mm 2mm;text-align:center;box-shadow:0 1px 3px rgba(28,28,28,.06)}
.placar b{display:block;font-weight:900;font-size:16pt}
.placar span{font-size:7.2pt;letter-spacing:.12em;text-transform:uppercase;color:var(--n500);font-weight:500}
.legenda{background:#fff;border:1px solid var(--n200);border-left:4px solid var(--gold);
  border-radius:var(--r-card);padding:4mm 6mm;margin:5mm 0;page-break-inside:avoid}
.legenda b{font-weight:700}
.legenda .li{margin:1mm 0;font-size:9.6pt}
.legenda .s{display:inline-block;width:6mm;font-weight:700;font-family:Arial}
.bloco{background:#fff;border:1px solid var(--n200);border-radius:var(--r-xl);
  padding:4mm 5mm;margin:3mm 0;box-shadow:0 1px 3px rgba(28,28,28,.05);page-break-inside:avoid}
.bloco-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:2mm}
.bloco-nome{font-weight:700;font-size:11.5pt}
.cod{color:var(--gold-600);font-weight:900;margin-right:2.5mm}
.badge{font-size:8pt;font-weight:600;letter-spacing:.04em;border:1.5px solid;
  border-radius:var(--r-pill);padding:1mm 4mm;white-space:nowrap}
table.itens{border-collapse:collapse;width:100%;margin:2mm 0;font-size:9.4pt}
table.itens td{border:0;border-bottom:1px solid var(--n100);padding:1.5mm 2mm;
  vertical-align:top;font-weight:300}
table.itens .s{width:6mm;font-weight:700;font-family:Arial}
.leitura{color:var(--n600);margin:2.5mm 0 1mm;text-align:justify}
.capafoto{margin:4mm 0;text-align:center;page-break-inside:avoid}
.capafoto img{max-width:70%;max-height:80mm;border-radius:var(--r-md);border:1px solid var(--n200)}
.capafoto div{font-size:8pt;color:var(--n500);margin-top:1.5mm}
.fotostrip{display:grid;grid-template-columns:repeat(5,1fr);gap:2.5mm;margin:3mm 0}
.fotostrip img{width:100%;height:22mm;object-fit:cover;border-radius:var(--r-md);
  border:1px solid var(--n200)}
ol.rec{padding-left:6mm}
ol.rec li{margin-bottom:2mm}
.copybox{background:#fff;border:1px solid var(--n200);border-left:4px solid var(--gold);
  border-radius:var(--r-card);padding:4mm 5mm;margin:2mm 0 4mm;page-break-inside:avoid}
.oferta{background:linear-gradient(180deg,#2C2C2C 0%,#1C1C1C 100%);color:#F3F2EE;
  margin:8mm 0 0;padding:9mm 11mm;border-radius:var(--r-xl);page-break-inside:avoid}
.oferta .eyebrow{color:var(--gold)}
.oferta h2{color:#fff;font-size:16pt}
.oferta h2 .gold{color:var(--gold)}
.oferta p{color:#D4D2C8}
.oferta strong{color:#fff}
.oferta .foot{border-top:1px solid var(--ink-700);margin-top:6mm;padding-top:4mm;display:flex;
  justify-content:space-between;font-size:7.6pt;letter-spacing:.16em;text-transform:uppercase;color:var(--n500)}
"""


def _fonts_css(base_url: str = "") -> str:
    pesos = [("Light", 300), ("Regular", 400), ("Medium", 500),
             ("SemiBold", 600), ("Bold", 700), ("Black", 900)]
    regras = []
    for nome, peso in pesos:
        regras.append(
            '@font-face{font-family:"Linear Grotesk";'
            f'src:url("{base_url}static/fonts/LinearGrotesk-{nome}.ttf");'
            f"font-weight:{peso};}}")
    return "\n".join(regras)


def _limpa(texto: str) -> str:
    """Aplica a regra da casa: nada de travessões no texto do relatório."""
    return (texto or "").replace(" — ", ". ").replace("—", ",").replace(" – ", ". ")


def render_html(analise: dict, fotos_dir: str = "", fotos: list = None) -> str:
    d = analise["dados"]
    placar = analise["placar"]

    blocos_html = ""
    for b in analise["blocos"]:
        cor, rotulo = BADGE.get(b["status"], BADGE["PENDENTE"])
        linhas = ""
        for texto, st in b["itens"]:
            ic, c = ST[st]
            linhas += (f'<tr><td class="s" style="color:{c}">{ic}</td>'
                       f"<td>{H.escape(_limpa(texto))}</td></tr>")
        blocos_html += f"""
        <div class="bloco">
          <div class="bloco-head">
            <div class="bloco-nome"><span class="cod">{b['cod']}</span>{H.escape(b['nome'])}</div>
            <div class="badge" style="color:{cor};border-color:{cor}">{rotulo}</div>
          </div>
          <table class="itens">{linhas}</table>
          <p class="leitura">{H.escape(_limpa(b['leitura']))}</p>
        </div>"""

    resumo_html = "".join(f"<p>{H.escape(_limpa(p))}</p>"
                          for p in analise["resumo"].split("\n\n"))

    recs = "".join(f"<li>{H.escape(_limpa(r))}</li>" for r in analise["recomendacoes"])

    titulos_ia = ""
    if analise.get("titulos_ia"):
        ops = "".join(f"<li><strong>{H.escape(t)}</strong></li>" for t in analise["titulos_ia"])
        titulos_ia = (f'<h3>Sugestões de título para o seu anúncio</h3>'
                      f'<div class="copybox"><ol>{ops}</ol></div>')

    fotos_html = ""
    if fotos:
        capa = fotos[0]
        resto = "".join(f'<img src="{fotos_dir}{f}">' for f in fotos[1:6])
        fotos_html = f"""
        <div class="capafoto"><img src="{fotos_dir}{capa}">
          <div>Foto de capa atual do anúncio</div></div>
        {f'<div class="fotostrip">{resto}</div>' if resto else ''}"""

    contexto = " · ".join(x for x in [d.get("tipo"), d.get("local"), d.get("quartos"),
                                      d.get("camas"), d.get("banheiros")] if x)
    nota_linha = ""
    if d.get("nota"):
        sup = " · Superhost" if d.get("superhost") else ""
        nota_linha = f"Nota {d['nota']} com {d.get('avaliacoes', '?')} avaliações{sup}"

    legenda = """
    <div class="legenda">
      <b>Como ler os símbolos desta análise</b>
      <div class="li"><span class="s" style="color:#5B8A6B">&#10003;</span> Este item está bem feito.</div>
      <div class="li"><span class="s" style="color:#C99A3C">&#9651;</span> Este item pode melhorar.</div>
      <div class="li"><span class="s" style="color:#B4534B">&#10007;</span> Este item precisa de correção. Comece por aqui.</div>
      <div class="li"><span class="s" style="color:#78766C">&#9676;</span> Este item só pode ser conferido com acesso à conta do anúncio.</div>
    </div>"""

    return f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<title>Raio-X Express</title>
<style>{_fonts_css()}{CSS}</style></head><body>

<div class="cover">
  <div class="eyebrow">33hosts <span class="slash">/</span> Short Stay Solutions</div>
  <div class="stack">
    <span class="l">RAIO-X</span>
    <span class="l"><span class="gold">EXPRESS</span></span>
    <div class="sub"><b>{H.escape(_limpa(d.get('titulo') or 'Anúncio do Airbnb'))}</b><br>
    Análise automática dos itens públicos do seu anúncio, com os primeiros passos para vender mais.</div>
  </div>
  <div class="foot"><span>Anfitriões profissionais.</span>
  <span>Raio-X Express <span class="slash">/</span> 33hosts</span></div>
</div>

<div>
  <div class="eyebrow">Resumo</div>
  <h2>Como está o seu anúncio.</h2>
  <div class="placar">
    <div><b style="color:#5B8A6B">{placar['OK']}</b><span>Está bem</span></div>
    <div><b style="color:#C99A3C">{placar['AJUSTE']}</b><span>Pode melhorar</span></div>
    <div><b style="color:#B4534B">{placar['CRITICO']}</b><span>Corrigir</span></div>
    <div><b style="color:#78766C">{placar['PEND']}</b><span>Conferir na conta</span></div>
  </div>
  {legenda}
  <p><strong>{H.escape(contexto)}</strong>{('<br>' + H.escape(nota_linha)) if nota_linha else ''}</p>
  {resumo_html}
</div>

<div class="sec">
  <div class="eyebrow">Análise</div>
  <h2>Bloco por bloco.</h2>
  {blocos_html}
</div>

<div class="sec">
  <div class="eyebrow">Seu anúncio hoje</div>
  <h2>As fotos que o hóspede vê primeiro.</h2>
  {fotos_html or '<p>Não foi possível baixar as fotos do anúncio.</p>'}

  <div class="eyebrow" style="margin-top:8mm">Primeiros passos</div>
  <h2>O que fazer agora.</h2>
  {titulos_ia}
  <ol class="rec">{recs}</ol>

  <div class="oferta">
    <div class="eyebrow">Próximo passo</div>
    <h2>Seu anúncio pode <span class="gold">render mais</span>.</h2>
    <p>Este relatório mostra o que dá para ver por fora. O <strong>Raio-X completo da 33hosts</strong>
    analisa o anúncio inteiro em 18 blocos: fotos uma a uma, textos, preço em relação aos concorrentes
    e configurações da conta. E entrega as correções já escritas, prontas para colar no anúncio.</p>
    <p><strong>Fale com a 33hosts.</strong> Anfitriões profissionais no Litoral Norte de São Paulo.</p>
    <div class="foot"><span>Anfitriões profissionais.</span>
    <span>33hosts <span class="slash">/</span> Raio-X Express</span></div>
  </div>
</div>

</body></html>"""


def gerar_pdf(html_completo: str, pasta_trabalho: Path, pdf_final: Path) -> Path:
    """Imprime capa (margem zero) e miolo separados e junta no PDF final."""
    marcador = '<div class="eyebrow">Resumo</div>'
    i = html_completo.index(marcador)
    i = html_completo.rindex("<div>", 0, i)
    head = html_completo[:i]
    resto = html_completo[i:]

    j = head.index('<div class="cover">')
    estilo, capa = head[:j], head[j:]

    doc_capa = (estilo + "<style>@page{margin:0 !important}.cover{width:210mm;height:297mm;margin:0}</style>"
                + capa + "</body></html>")
    doc_miolo = estilo + resto

    p_capa = pasta_trabalho / "_capa.html"
    p_miolo = pasta_trabalho / "_miolo.html"
    p_capa.write_text(doc_capa, encoding="utf-8")
    p_miolo.write_text(doc_miolo, encoding="utf-8")

    pdf_capa = pasta_trabalho / "_capa.pdf"
    pdf_miolo = pasta_trabalho / "_miolo.pdf"
    for origem, destino in [(p_capa, pdf_capa), (p_miolo, pdf_miolo)]:
        subprocess.run([CHROME, "--headless", "--no-sandbox", "--disable-gpu",
                        "--no-pdf-header-footer", f"--print-to-pdf={destino}",
                        f"file://{origem}"], check=True, capture_output=True, timeout=120)

    from pypdf import PdfWriter
    w = PdfWriter()
    w.append(str(pdf_capa), pages=(0, 1))
    w.append(str(pdf_miolo))
    with open(pdf_final, "wb") as f:
        w.write(f)
    return pdf_final
