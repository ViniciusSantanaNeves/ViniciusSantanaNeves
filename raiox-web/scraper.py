# -*- coding: utf-8 -*-
"""Coleta os dados públicos de um anúncio do Airbnb a partir do link."""
import re
import html as htmlmod
import httpx

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

ROOM_RE = re.compile(r"/rooms/(\d+)")
SHORT_RE = re.compile(r"airbnb\.[a-z.]+/(?:l|h)/", re.I)


class ErroColeta(Exception):
    pass


def _get(url: str) -> httpx.Response:
    return httpx.get(url, headers={"User-Agent": UA, "Accept-Language": "pt-BR,pt;q=0.9"},
                     follow_redirects=True, timeout=30)


def normalizar_url(url: str) -> str:
    url = url.strip()
    if not url.startswith("http"):
        url = "https://" + url
    if "airbnb" not in url:
        raise ErroColeta("O link precisa ser de um anúncio do Airbnb.")
    m = ROOM_RE.search(url)
    if m:
        return f"https://www.airbnb.com.br/rooms/{m.group(1)}"
    if SHORT_RE.search(url):
        r = _get(url)
        m = ROOM_RE.search(str(r.url))
        if m:
            return f"https://www.airbnb.com.br/rooms/{m.group(1)}"
    raise ErroColeta("Não foi possível identificar o anúncio nesse link. "
                     "Use o link que contém /rooms/ ou o link de compartilhar do Airbnb.")


def _meta(html: str, prop: str) -> str:
    m = re.search(r'"%s" content="([^"]*)"' % re.escape(prop), html)
    return htmlmod.unescape(m.group(1)) if m else ""


def coletar(url: str) -> dict:
    url = normalizar_url(url)
    r = _get(url)
    if r.status_code != 200 or "airbnb" not in str(r.url):
        raise ErroColeta("O Airbnb não devolveu a página do anúncio. Tente novamente em instantes.")
    html = r.text

    og_title = _meta(html, "og:title")          # "Apartamento · Riviera ... · ★4,94 · 3 quartos · 6 camas · 2 banheiros"
    titulo = _meta(html, "og:description") or ""
    if not titulo:
        m = re.search(r"<title[^>]*>([^<]*)</title>", html)
        titulo = htmlmod.unescape(m.group(1)).split(" - ")[0] if m else ""

    def _num(pat):
        m = re.search(pat, html)
        return m.group(1) if m else ""

    nota = _num(r'"starRating":([0-9.]+)').replace(".", ",")
    avaliacoes = _num(r'"reviewCount":"?(\d+)')
    superhost = '"isSuperhost":true' in html

    partes = [p.strip() for p in og_title.split("·")]
    tipo = partes[0] if partes else ""
    local = partes[1] if len(partes) > 1 else ""
    quartos = camas = banheiros = ""
    for p in partes:
        if "quarto" in p:
            quartos = p
        elif "cama" in p:
            camas = p
        elif "banheiro" in p:
            banheiros = p

    fotos = sorted(set(re.findall(
        r'https://a0\.muscache\.com/im/pictures/[^"\\ ]+?\.(?:jpg|jpeg|png)', html)))
    fotos = [f for f in fotos if "PlatformAssets" not in f and "/user" not in f
             and "search-bar" not in f]

    capa = _meta(html, "og:image").split("?")[0]

    m = re.search(r'name="description" content="([^"]*)"', html)
    descricao = htmlmod.unescape(m.group(1)) if m else ""

    return dict(url=url, titulo=titulo, tipo=tipo, local=local, nota=nota,
                avaliacoes=avaliacoes, superhost=superhost, quartos=quartos,
                camas=camas, banheiros=banheiros, fotos=fotos, capa=capa,
                descricao=descricao)


def baixar_fotos(dados: dict, pasta, maximo: int = 6) -> list:
    """Baixa a capa e algumas fotos para colocar no relatório."""
    pasta.mkdir(parents=True, exist_ok=True)
    urls = []
    if dados.get("capa"):
        urls.append(dados["capa"])
    for f in dados.get("fotos", []):
        base = f.split("?")[0]
        if base not in urls:
            urls.append(base)
        if len(urls) >= maximo:
            break
    salvas = []
    for i, u in enumerate(urls, start=1):
        try:
            r = _get(u + "?im_w=960")
            if r.status_code == 200 and len(r.content) > 5000:
                destino = pasta / f"foto-{i:02d}.jpg"
                destino.write_bytes(r.content)
                salvas.append(destino.name)
        except Exception:
            continue
    return salvas
