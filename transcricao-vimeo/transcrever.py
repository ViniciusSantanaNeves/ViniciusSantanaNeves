#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Transcritor de videos do Vimeo (curso / area de membros).

O que ele faz, para cada video da lista videos.json:
  1) Baixa SOMENTE o audio usando yt-dlp, autenticando com o SEU acesso
     (cookies do navegador onde voce assiste, e/ou o dominio do curso).
  2) Transcreve o audio em portugues.
  3) Salva um .txt (texto corrido) e um .srt (com tempos) na pasta 'transcricoes/'.

Ele pula videos ja transcritos, entao voce pode parar e rodar de novo quando quiser.

--------------------------------------------------------------------------------
COMO USAR (resumo -- detalhes no README.md):

  1. Instale as dependencias:
        pip install -r requirements.txt
     E instale o ffmpeg (necessario para extrair audio):
        - Windows:  winget install Gyan.FFmpeg    (ou baixe em ffmpeg.org)
        - Mac:      brew install ffmpeg
        - Linux:    sudo apt install ffmpeg

  2. Configure o acesso (escolha UMA das formas abaixo), via variavel de ambiente:

     a) Cookies do navegador onde voce assiste ao curso (mais simples p/ aluno):
            COOKIES_FROM_BROWSER=chrome     (ou firefox, edge, brave, safari...)

     b) Dominio do curso (se o video for "restrito por dominio"):
            COURSE_REFERER=https://site-do-curso.com.br

     c) Senha do video (se for video protegido por senha):
            VIMEO_PASSWORD=a-senha

     Voce pode combinar (ex.: cookies + referer). O ideal e comecar so com cookies.

  3. Rode:
        python transcrever.py

--------------------------------------------------------------------------------
MOTOR DE TRANSCRICAO (padrao: faster-whisper, roda no seu PC, de graca):

     WHISPER_MODEL=small        tamanho do modelo local: tiny|base|small|medium|large-v3
                                (maior = mais preciso, porem mais lento)

     Para usar a API da OpenAI (paga, porem rapida e sem pesar no PC):
        MOTOR=openai
        OPENAI_API_KEY=sk-...

Exemplo completo (Linux/Mac):
     COOKIES_FROM_BROWSER=chrome WHISPER_MODEL=medium python transcrever.py
"""

import json
import os
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

# ------------------------------------------------------------------ configuracao
BASE_DIR   = Path(__file__).resolve().parent
VIDEOS     = BASE_DIR / "videos.json"
AUDIO_DIR  = BASE_DIR / "audios"          # audios baixados (temporarios)
OUT_DIR    = BASE_DIR / "transcricoes"    # resultados (.txt e .srt)

COOKIES_FROM_BROWSER = os.environ.get("COOKIES_FROM_BROWSER", "").strip()
COURSE_REFERER       = os.environ.get("COURSE_REFERER", "").strip()
VIMEO_PASSWORD       = os.environ.get("VIMEO_PASSWORD", "").strip()

MOTOR          = os.environ.get("MOTOR", "faster-whisper").strip().lower()
WHISPER_MODEL  = os.environ.get("WHISPER_MODEL", "small").strip()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "").strip()
IDIOMA         = os.environ.get("IDIOMA", "pt").strip()
MANTER_AUDIO   = os.environ.get("MANTER_AUDIO", "").strip() not in ("", "0", "false", "no")


# ------------------------------------------------------------------ utilidades
def log(msg):
    print(msg, flush=True)


def slug(texto):
    """Transforma um titulo em nome de arquivo seguro."""
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    texto = re.sub(r"[^\w\s-]", "", texto).strip().lower()
    texto = re.sub(r"[\s_-]+", "-", texto)
    return texto or "video"


def checar_ferramenta(nome, dica):
    from shutil import which
    if which(nome) is None:
        log(f"[ERRO] '{nome}' nao encontrado. {dica}")
        return False
    return True


def formatar_tempo_srt(segundos):
    ms = int(round((segundos - int(segundos)) * 1000))
    s = int(segundos)
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


# ------------------------------------------------------------------ download
def baixar_audio(video_id, destino_base):
    """
    Baixa o audio de um video do Vimeo. Retorna o caminho do arquivo de audio
    ou None em caso de falha. 'destino_base' e o caminho SEM extensao.
    """
    url = f"https://player.vimeo.com/video/{video_id}"

    cmd = [
        "yt-dlp",
        "-f", "bestaudio/best",
        "-x", "--audio-format", "mp3",     # extrai audio em mp3 (usa ffmpeg)
        "--audio-quality", "5",
        "--no-playlist",
        "--retries", "5",
        "--fragment-retries", "5",
        "-o", str(destino_base) + ".%(ext)s",
    ]

    # Vimeo costuma exigir um Referer valido para videos embutidos.
    referer = COURSE_REFERER or "https://vimeo.com"
    cmd += ["--referer", referer]

    if COOKIES_FROM_BROWSER:
        cmd += ["--cookies-from-browser", COOKIES_FROM_BROWSER]
    if VIMEO_PASSWORD:
        cmd += ["--video-password", VIMEO_PASSWORD]

    cmd.append(url)

    log(f"    baixando audio (id {video_id})...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        log("    [FALHA no download]")
        # mostra so as ultimas linhas do erro para nao poluir
        erro = (res.stderr or res.stdout or "").strip().splitlines()
        for linha in erro[-6:]:
            log(f"      > {linha}")
        return None

    esperado = Path(str(destino_base) + ".mp3")
    if esperado.exists():
        return esperado

    # fallback: procura qualquer arquivo com esse prefixo
    for p in AUDIO_DIR.glob(destino_base.name + ".*"):
        return p
    return None


# ------------------------------------------------------------------ transcricao
_modelo_fw = None  # cache do modelo faster-whisper


def transcrever_faster_whisper(audio_path):
    global _modelo_fw
    from faster_whisper import WhisperModel

    if _modelo_fw is None:
        log(f"    carregando modelo faster-whisper '{WHISPER_MODEL}' (primeira vez demora)...")
        _modelo_fw = WhisperModel(WHISPER_MODEL, device="auto", compute_type="auto")

    segmentos, _info = _modelo_fw.transcribe(
        str(audio_path),
        language=IDIOMA,
        vad_filter=True,       # ignora silencios longos
        beam_size=5,
    )

    texto_partes, srt_partes = [], []
    for i, seg in enumerate(segmentos, start=1):
        t = seg.text.strip()
        texto_partes.append(t)
        srt_partes.append(
            f"{i}\n{formatar_tempo_srt(seg.start)} --> {formatar_tempo_srt(seg.end)}\n{t}\n"
        )
    return " ".join(texto_partes).strip(), "\n".join(srt_partes).strip()


def transcrever_openai(audio_path):
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)

    with open(audio_path, "rb") as f:
        resp = client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            language=IDIOMA,
            response_format="verbose_json",
        )

    texto = (resp.text or "").strip()
    srt_partes = []
    for i, seg in enumerate(getattr(resp, "segments", []) or [], start=1):
        # a resposta pode vir como objeto ou dict, dependendo da versao do SDK
        start = seg["start"] if isinstance(seg, dict) else seg.start
        end   = seg["end"]   if isinstance(seg, dict) else seg.end
        t     = (seg["text"] if isinstance(seg, dict) else seg.text).strip()
        srt_partes.append(
            f"{i}\n{formatar_tempo_srt(start)} --> {formatar_tempo_srt(end)}\n{t}\n"
        )
    return texto, "\n".join(srt_partes).strip()


def transcrever(audio_path):
    if MOTOR == "openai":
        if not OPENAI_API_KEY:
            log("    [ERRO] MOTOR=openai mas OPENAI_API_KEY nao foi definida.")
            return None, None
        return transcrever_openai(audio_path)
    return transcrever_faster_whisper(audio_path)


# ------------------------------------------------------------------ principal
def main():
    log("=" * 70)
    log("  Transcritor de videos do Vimeo")
    log("=" * 70)

    # checagens basicas
    if not checar_ferramenta("yt-dlp", "Instale com: pip install -r requirements.txt"):
        sys.exit(1)
    if not checar_ferramenta("ffmpeg", "Instale o ffmpeg (veja o README.md)."):
        sys.exit(1)

    if not (COOKIES_FROM_BROWSER or COURSE_REFERER or VIMEO_PASSWORD):
        log("")
        log("  [AVISO] Nenhum acesso configurado (COOKIES_FROM_BROWSER / COURSE_REFERER /")
        log("          VIMEO_PASSWORD). Videos privados provavelmente falharao com erro 403.")
        log("          Veja o README.md. Continuando mesmo assim...")
        log("")

    videos = json.loads(VIDEOS.read_text(encoding="utf-8"))
    AUDIO_DIR.mkdir(exist_ok=True)
    OUT_DIR.mkdir(exist_ok=True)

    total = len(videos)
    ok, pulados, falhas = 0, 0, []

    for idx, v in enumerate(videos, start=1):
        n, titulo, vid, secao = v["n"], v["titulo"], v["id"], v.get("secao", "")
        nome = f"{n:02d}-{slug(titulo)}"
        out_txt = OUT_DIR / f"{nome}.txt"
        out_srt = OUT_DIR / f"{nome}.srt"

        log("-" * 70)
        log(f"[{idx}/{total}] #{n:02d} {titulo}")

        if out_txt.exists():
            log("    ja transcrito -> pulando")
            pulados += 1
            continue

        audio_base = AUDIO_DIR / nome
        audio = baixar_audio(vid, audio_base)
        if audio is None:
            falhas.append((n, titulo, "download"))
            continue

        try:
            log("    transcrevendo...")
            texto, srt = transcrever(audio)
        except Exception as e:  # noqa: BLE001
            log(f"    [FALHA na transcricao] {e}")
            falhas.append((n, titulo, "transcricao"))
            continue

        if not texto:
            falhas.append((n, titulo, "vazio"))
            continue

        cabecalho = f"# {titulo}\n# {secao}\n# Vimeo ID: {vid}\n\n"
        out_txt.write_text(cabecalho + texto + "\n", encoding="utf-8")
        if srt:
            out_srt.write_text(srt + "\n", encoding="utf-8")
        log(f"    OK -> {out_txt.name}")
        ok += 1

        if not MANTER_AUDIO:
            try:
                audio.unlink()
            except OSError:
                pass

    # resumo final
    log("=" * 70)
    log(f"  Concluido. Transcritos: {ok} | Pulados: {pulados} | Falhas: {len(falhas)}")
    if falhas:
        log("  Falhas:")
        for n, titulo, etapa in falhas:
            log(f"    #{n:02d} {titulo}  ({etapa})")
        log("  Dica: confira o acesso (cookies/referer/senha) e rode de novo -")
        log("        os que ja deram certo serao pulados automaticamente.")
    log(f"  Resultados em: {OUT_DIR}")
    log("=" * 70)


if __name__ == "__main__":
    main()
