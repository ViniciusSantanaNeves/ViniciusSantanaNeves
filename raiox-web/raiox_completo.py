# -*- coding: utf-8 -*-
"""
Raio-X do Anúncio COMPLETO (18 blocos · 6 fases) rodando no servidor, para a
equipe 33hosts, sem depender de uma sessão do Claude Code.

Pipeline: coleta da página pública -> extração detalhada -> fotos -> radar de
algoritmo (busca na web, com cache) -> análise pela API da Anthropic (visão +
saída estruturada) -> PDF no design system (relatorio_completo).

Requer a variável de ambiente ANTHROPIC_API_KEY.
"""
import base64
import codecs
import json
import os
import re
import time
from pathlib import Path

import metodologia
import relatorio_completo
import scraper

MODELO = os.environ.get("MODELO_RAIOX", "claude-opus-5-5")
MODELO_RADAR = os.environ.get("MODELO_RADAR", MODELO)
MAX_FOTOS = 12
RADAR_VALIDADE_DIAS = 7

MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
         "agosto", "setembro", "outubro", "novembro", "dezembro"]


class ErroRaioX(Exception):
    pass


def _cliente():
    chave = os.environ.get("ANTHROPIC_API_KEY", "")
    if not chave:
        raise ErroRaioX("ANTHROPIC_API_KEY não está configurada no servidor.")
    import anthropic
    return anthropic.Anthropic(api_key=chave)


def data_rotulo() -> str:
    t = time.localtime()
    return f"{MESES[t.tm_mon - 1].capitalize()} de {t.tm_year}"


# ---------------------------------------------------------------- extração --

def _desescapar(t: str) -> str:
    try:
        return codecs.decode(t, "unicode_escape").encode("latin-1").decode("utf-8", "ignore")
    except Exception:
        return t


def extrair_detalhes(html: str) -> dict:
    """Extrai do HTML público os campos que o motor de análise precisa."""
    def um(pat, flags=0):
        m = re.search(pat, html, flags)
        return m.group(1) if m else ""

    detalhes = {
        "nota_geral": um(r'"starRating":([0-9.]+)'),
        "avaliacoes": um(r'"reviewCount":"?(\d+)'),
        "superhost": '"isSuperhost":true' in html,
        "guest_favorite": ('"isGuestFavorite":true' in html) or ("Preferido dos hóspedes" in html),
        "capacidade": um(r'"personCapacity":(\d+)'),
        "reserva_imediata": '"instantBookable":true' in html,
        "tempo_anfitriao": _desescapar(um(r'"(\d+\s+anos?\s+hospedando)"')),
    }

    notas = {}
    for chave, rotulo in [("accuracyRating", "exatidão"), ("checkinRating", "check-in"),
                          ("cleanlinessRating", "limpeza"), ("communicationRating", "comunicação"),
                          ("locationRating", "localização"), ("valueRating", "custo-benefício")]:
        v = um(r'"%s":([0-9.]+)' % chave)
        if v:
            notas[rotulo] = v
    detalhes["notas_categoria"] = notas

    disponiveis, indisponiveis = [], []
    for disp, titulo in re.findall(r'"available":(true|false),"title":"((?:[^"\\]|\\.){2,80})"', html):
        titulo = _desescapar(titulo)
        alvo = disponiveis if disp == "true" else indisponiveis
        if titulo not in alvo:
            alvo.append(titulo)
    detalhes["comodidades"] = disponiveis[:80]
    detalhes["nao_incluso"] = indisponiveis[:30]

    trechos, vistos = [], set()
    for bruto in re.findall(r'"htmlText":"((?:[^"\\]|\\.)+)"', html):
        texto = _desescapar(bruto).replace("<br />", "\n").replace("<br/>", "\n").replace("<br>", "\n")
        texto = re.sub(r"<[^>]+>", "", texto).strip()
        if len(texto) > 40 and texto[:80] not in vistos:
            vistos.add(texto[:80])
            trechos.append(texto)
    detalhes["descricao_completa"] = "\n\n".join(trechos)[:7000]

    ruido = {"Compartilhar", "Salvar", "Salvo", "Traduzido automaticamente.", "Adultos",
             "Crianças", "Bebês", "Animais de estimação", "O que esse lugar oferece",
             "Onde você vai dormir", "Avaliações", "Localização", "Fotos", "Comodidades"}
    regras = []
    for bruto in re.findall(r'"title":"((?:[^"\\]|\\.){3,70})","subtitle"', html):
        t = _desescapar(bruto)
        if t not in regras and t not in ruido:
            regras.append(t)
    for frase in re.findall(r'(?:Proibido|Não é permitido|É permitido|Permitido)[^"<\\]{3,60}', html):
        if frase not in regras:
            regras.append(frase)
    detalhes["regras_e_itens"] = regras[:40]

    return detalhes


def coletar_tudo(url: str) -> dict:
    dados = scraper.coletar(url)        # título, nota, local, fotos, capa...
    import httpx
    r = httpx.get(dados["url"], headers={"User-Agent": scraper.UA,
                                         "Accept-Language": "pt-BR,pt;q=0.9"},
                  follow_redirects=True, timeout=30)
    dados.update(extrair_detalhes(r.text))
    dados["total_fotos"] = len(dados.get("fotos", []))
    return dados


# ------------------------------------------------------------------- radar --

def radar_algoritmo(pasta_cache: Path) -> str:
    """Radar de mudanças do Airbnb: busca na web com cache de alguns dias.
    Em qualquer falha, usa o radar-base registrado na metodologia."""
    cache = pasta_cache / "radar_algoritmo.json"
    try:
        info = json.loads(cache.read_text(encoding="utf-8"))
        if time.time() - info["quando"] < RADAR_VALIDADE_DIAS * 86400 and info.get("texto"):
            return info["texto"]
    except Exception:
        pass

    try:
        cliente = _cliente()
        resposta = cliente.messages.create(
            model=MODELO_RADAR,
            max_tokens=2000,
            tools=[{"type": "web_search_20260209", "name": "web_search", "max_uses": 6}],
            messages=[{"role": "user", "content": metodologia.PROMPT_RADAR}],
        )
        texto = "\n".join(b.text for b in resposta.content if b.type == "text").strip()
        if len(texto) > 100:
            cache.write_text(json.dumps({"quando": time.time(), "texto": texto},
                                        ensure_ascii=False), encoding="utf-8")
            return texto
    except Exception:
        pass
    return metodologia.RADAR_BASE


# ----------------------------------------------------------------- análise --

def _sem_travessoes(obj):
    """Remove travessões e meia-riscas de toda a estrutura (regra da casa)."""
    if isinstance(obj, str):
        obj = re.sub(r"\s*—\s*", ": ", obj)          # em dash
        obj = re.sub(r"(?<=\d)\s*–\s*(?=\d)", " a ", obj)  # en dash entre números
        return obj.replace("–", ": ").replace("—", ": ")
    if isinstance(obj, list):
        return [_sem_travessoes(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _sem_travessoes(v) for k, v in obj.items()}
    return obj


def _conteudo_com_fotos(dados: dict, fotos_paths: list, radar: str) -> list:
    resumo_dados = {k: v for k, v in dados.items() if k != "fotos"}
    conteudo = [{
        "type": "text",
        "text": ("Analise este anúncio do Airbnb e produza o Raio-X completo conforme a metodologia.\n\n"
                 f"DADOS COLETADOS DA PÁGINA PÚBLICA (JSON):\n{json.dumps(resumo_dados, ensure_ascii=False, indent=1)}\n\n"
                 f"RADAR DE MUDANÇAS DO ALGORITMO (use nos blocos B5, B8, B9, B10 e B13 e na seção Aplicações):\n{radar}\n\n"
                 f"A seguir, as primeiras {len(fotos_paths)} fotos da galeria, numeradas na ordem em que "
                 "aparecem no anúncio (a FOTO 1 é a capa). Avalie cada uma visualmente."),
    }]
    for i, caminho in enumerate(fotos_paths, start=1):
        conteudo.append({"type": "text", "text": f"FOTO {i}:"})
        with open(caminho, "rb") as f:
            dado = base64.standard_b64encode(f.read()).decode("utf-8")
        conteudo.append({"type": "image",
                         "source": {"type": "base64", "media_type": "image/jpeg", "data": dado}})
    return conteudo


def gerar_analise(dados: dict, fotos_paths: list, radar: str) -> dict:
    cliente = _cliente()
    with cliente.messages.stream(
        model=MODELO,
        max_tokens=50000,
        system=metodologia.PROMPT_SISTEMA,
        output_config={"format": {"type": "json_schema", "schema": metodologia.ESQUEMA_RAIOX}},
        messages=[{"role": "user", "content": _conteudo_com_fotos(dados, fotos_paths, radar)}],
    ) as stream:
        resposta = stream.get_final_message()

    if resposta.stop_reason == "refusal":
        raise ErroRaioX("O modelo recusou a análise deste anúncio. Tente novamente ou fale com o suporte.")
    if resposta.stop_reason == "max_tokens":
        raise ErroRaioX("A análise ficou longa demais e foi cortada. Tente novamente.")

    texto = next((b.text for b in resposta.content if b.type == "text"), "")
    analise = json.loads(texto)
    return _sem_travessoes(analise)


# -------------------------------------------------------------- orquestrar --

def executar(url: str, pasta: Path, progresso=None) -> dict:
    """Roda o Raio-X completo e devolve {'pdf': Path, 'placar': dict, 'imovel': str}."""
    def _p(msg):
        if progresso:
            progresso(msg)

    _p("Lendo o anúncio público...")
    dados = coletar_tudo(url)

    _p("Baixando as fotos da galeria...")
    fotos_dir = pasta / "fotos"
    nomes = scraper.baixar_fotos(dados, fotos_dir, maximo=MAX_FOTOS)
    fotos_paths = [fotos_dir / n for n in nomes]
    if not fotos_paths:
        raise ErroRaioX("Não foi possível baixar as fotos do anúncio.")

    _p("Atualizando o radar do algoritmo...")
    radar = radar_algoritmo(pasta.parent)

    _p("Analisando com a metodologia 33hosts (isso leva alguns minutos)...")
    analise = gerar_analise(dados, fotos_paths, radar)
    (pasta / "analise.json").write_text(json.dumps(analise, ensure_ascii=False, indent=1),
                                        encoding="utf-8")

    _p("Montando o PDF no design 33hosts...")
    rotulo = data_rotulo()
    html = relatorio_completo.render_html(analise, rotulo, fotos_dir.as_posix(), len(fotos_paths))
    (pasta / "raiox.html").write_text(html, encoding="utf-8")
    pdf = relatorio_completo.gerar_pdf(html, pasta, pasta / "raiox-completo.pdf")

    placar = {"OK": 0, "AJUSTE": 0, "CRITICO": 0, "PEND": 0}
    for f in analise["fases"]:
        for b in f["blocos"]:
            placar["PEND" if b["status"] in ("PENDENTE", "PARCIAL") else b["status"]] += 1

    return {"pdf": pdf, "placar": placar, "imovel": analise.get("imovel", ""),
            "tese": analise.get("tese", "")}
