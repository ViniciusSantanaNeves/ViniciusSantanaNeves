#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Transcritor dos videos do Vimeo - ARQUIVO UNICO (nao precisa de mais nada).

COMO USAR (Windows):
  1) Salve este arquivo (transcrever.py) em qualquer lugar (ex.: Downloads).
  2) Abra o Prompt de Comando (tecla Windows, digite  cmd , Enter).
  3) Cole a linha abaixo e aperte Enter:

        python "%USERPROFILE%\\Downloads\\transcrever.py"

  Pronto. Ele instala sozinho o que falta, baixa o audio de cada video
  (usando o seu acesso) e transcreve em portugues. Os resultados ficam em:
        C:\\Users\\SEU-USUARIO\\transcricoes-vimeo

  Dica: mantenha o navegador do curso ABERTO e LOGADO enquanto roda.
        Pode fechar e rodar de novo quando quiser - ele pula os ja feitos.
"""

import importlib
import subprocess
import sys
import re
import unicodedata
from pathlib import Path

# =====================================================================
# CONFIGURACAO  (mexa aqui so se precisar)
# =====================================================================
REFERER        = "https://membros.clubedosanfitrioes.com.br"
WHISPER_MODEL  = "small"     # tiny | base | small | medium | large-v3  (maior = melhor e mais lento)
IDIOMA         = "pt"
VIMEO_PASSWORD = ""          # preencha entre as aspas SO se o video pedir senha
PASTA_SAIDA    = Path.home() / "transcricoes-vimeo"

# Quantas vezes tentar baixar cada video antes de desistir (o erro de
# "part-Frag" do Windows costuma passar numa nova tentativa).
TENTATIVAS = 4

# Se algum video exigir login (raro), coloque aqui o navegador onde voce
# assiste: "chrome", "edge", "firefox" ou "brave". Deixe "" para usar so o
# referer (que e o que funciona na maioria dos casos).
COOKIES_NAVEGADOR = ""

# =====================================================================
# LISTA DOS VIDEOS
# =====================================================================
VIDEOS = [
    (1,  "Secao 1 - Raio-X",   "Quando iniciar um processo de otimizacao",                 "806942000"),
    (2,  "Secao 1 - Raio-X",   "Por que alguns anuncios nao performam",                    "802849600"),
    (3,  "Secao 1 - Raio-X",   "Checklist do Raio-X",                                      "809736931"),
    (4,  "Secao 2 - Pilares",  "Visual - o pilar da atencao",                              "802814991"),
    (5,  "Secao 2 - Pilares",  "Avaliacoes - o pilar da confianca",                        "802822004"),
    (6,  "Secao 2 - Pilares",  "Parametrizacao - o pilar do algoritmo",                    "802305708"),
    (7,  "Secao 2 - Pilares",  "Textual - o pilar da narrativa",                           "802306073"),
    (8,  "Secao 2 - Pilares",  "Textual - o pilar da narrativa com ajuda de IA",           "802307243"),
    (9,  "Secao 3 - Bonus",    "Guia da casa",                                             "554916682"),
    (10, "Secao 3 - Bonus",    "Analise de anuncios (encontro do Clube)",                  "799854841"),
    (12, "Secao 3 - Bonus",    "10 erros no Instagram",                                    "693740184"),
    (13, "Secao 4 - Acelerador","Introducao",                                              "678839301"),
    (14, "Secao 4 - Acelerador","Estrategia de partida",                                   "678849732"),
    (15, "Secao 4 - Acelerador","Fotografia - parte 1",                                    "678853379"),
    (16, "Secao 4 - Acelerador","Fotografia - parte 2",                                    "680146034"),
    (17, "Secao 4 - Acelerador","Legenda",                                                 "678854158"),
    (18, "Secao 4 - Acelerador","Titulo",                                                  "678854796"),
    (19, "Secao 4 - Acelerador","Resumo",                                                  "678859388"),
    (20, "Secao 4 - Acelerador","Descricao de espaco e preenchimento de secoes",           "678860179"),
    (21, "Secao 4 - Acelerador","Reservas instantaneas",                                   "678869249"),
    (22, "Secao 4 - Acelerador","Avaliacoes",                                              "678871739"),
    (23, "Secao 4 - Acelerador","Politica de Cancelamento",                                "678872663"),
    (24, "Secao 4 - Acelerador","Deposito de seguranca",                                   "680399656"),
    (25, "Secao 4 - Acelerador","Regras da casa",                                          "680398866"),
    (26, "Secao 4 - Acelerador","Idioma",                                                  "678876075"),
    (27, "Secao 4 - Acelerador","Numero minimo de diarias e faturamento",                  "678878190"),
    (28, "Secao 4 - Acelerador","Perfil do anfitriao",                                     "678878592"),
    (29, "Secao 4 - Acelerador","Tempo de resposta",                                       "678878775"),
    (30, "Secao 4 - Acelerador","Recusa de reserva",                                       "678879199"),
    (31, "Secao 4 - Acelerador","Atualizacao de calendario, preco e preco competitivo",    "678880506"),
    (32, "Secao 4 - Acelerador","Favoritos",                                               "678882281"),
    (33, "Secao 4 - Acelerador","Taxa de conversao",                                       "678883375"),
    (34, "Secao 4 - Acelerador","Cancelamento",                                            "678883774"),
    (35, "Secao 4 - Acelerador","Superhost, palavras-chave e localizacao",                 "680137376"),
    (36, "Secao 4 - Acelerador","Pets e hospedes de primeira viagem",                      "680137898"),
    (37, "Secao 4 - Acelerador","Janela disponivel",                                       "680139396"),
    (38, "Secao 4 - Acelerador","Fumantes",                                                "680139798"),
    (39, "Secao 4 - Acelerador","Lugar para mais hospedes e descontos",                    "680141787"),
    (40, "Secao 4 - Acelerador","Mudanca de estacao, anuncio travado e itens procurados",  "680144181"),
]


# =====================================================================
# INSTALACAO AUTOMATICA DAS DEPENDENCIAS
# =====================================================================
def garantir(pacote, modulo=None):
    modulo = modulo or pacote
    try:
        return importlib.import_module(modulo)
    except ImportError:
        print(f"  instalando {pacote} (so na primeira vez, pode demorar)...", flush=True)
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--quiet", "--user", "--upgrade", pacote]
        )
        return importlib.import_module(modulo)


# =====================================================================
# UTILIDADES
# =====================================================================
def slug(texto):
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    texto = re.sub(r"[^\w\s-]", "", texto).strip().lower()
    return re.sub(r"[\s_-]+", "-", texto) or "video"


def tempo_srt(seg):
    ms = int(round((seg - int(seg)) * 1000))
    s = int(seg); h, s = divmod(s, 3600); m, s = divmod(s, 60)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


# =====================================================================
# DOWNLOAD DO AUDIO (tenta varias estrategias ate uma funcionar)
# =====================================================================
def baixar_audio(yt_dlp, video_id, destino_base):
    url = f"https://player.vimeo.com/video/{video_id}"

    for tentativa in range(1, TENTATIVAS + 1):
        # limpa restos de download anterior (evita o erro de "part-Frag")
        for p in destino_base.parent.glob(destino_base.name + ".*"):
            try:
                p.unlink()
            except OSError:
                pass

        opts = {
            "format": "bestaudio/best",
            "outtmpl": str(destino_base) + ".%(ext)s",
            "http_headers": {"Referer": REFERER},
            "referer": REFERER,
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "ignoreerrors": False,
            # robustez contra falhas de rede e de arquivo no Windows:
            "retries": 10,
            "fragment_retries": 30,
            "file_access_retries": 30,
            "concurrent_fragment_downloads": 1,
            "continuedl": True,
        }
        if COOKIES_NAVEGADOR:
            opts["cookiesfrombrowser"] = (COOKIES_NAVEGADOR,)
        if VIMEO_PASSWORD:
            opts["videopassword"] = VIMEO_PASSWORD

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.extract_info(url, download=True)
        except Exception as e:  # noqa: BLE001
            msg = str(e).splitlines()[0][:110]
            print(f"      x tentativa {tentativa}/{TENTATIVAS} falhou: {msg}", flush=True)
            continue

        for p in destino_base.parent.glob(destino_base.name + ".*"):
            if not p.name.endswith(".part") and ".part-" not in p.name:
                print(f"      ok (tentativa {tentativa})", flush=True)
                return p
    return None


# =====================================================================
# PRINCIPAL
# =====================================================================
def main():
    print("=" * 68)
    print("  Transcritor dos videos do Vimeo - Clube dos Anfitrioes")
    print("=" * 68)
    print("  Preparando o ambiente...")

    yt_dlp = garantir("yt-dlp", "yt_dlp")
    fw     = garantir("faster-whisper", "faster_whisper")
    from faster_whisper import WhisperModel

    PASTA_SAIDA.mkdir(exist_ok=True)
    tmp = PASTA_SAIDA / "_audio_temp"
    tmp.mkdir(exist_ok=True)

    print(f"  Carregando o modelo de transcricao '{WHISPER_MODEL}' (primeira vez demora)...")
    modelo = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")

    total = len(VIDEOS)
    ok = pulados = 0
    falhas = []

    for i, (n, secao, titulo, vid) in enumerate(VIDEOS, start=1):
        nome = f"{n:02d}-{slug(titulo)}"
        out_txt = PASTA_SAIDA / f"{nome}.txt"
        out_srt = PASTA_SAIDA / f"{nome}.srt"

        print("-" * 68)
        print(f"[{i}/{total}] #{n:02d} {titulo}")

        if out_txt.exists():
            print("      ja transcrito -> pulando")
            pulados += 1
            continue

        audio = baixar_audio(yt_dlp, vid, tmp / nome)
        if audio is None:
            print("      >> NAO consegui baixar este video (verifique login/navegador)")
            falhas.append((n, titulo))
            continue

        try:
            print("      transcrevendo...")
            segs, _ = modelo.transcribe(str(audio), language=IDIOMA, vad_filter=True, beam_size=5)
            partes_txt, partes_srt = [], []
            for j, s in enumerate(segs, start=1):
                t = s.text.strip()
                partes_txt.append(t)
                partes_srt.append(f"{j}\n{tempo_srt(s.start)} --> {tempo_srt(s.end)}\n{t}\n")
            texto = " ".join(partes_txt).strip()
        except Exception as e:  # noqa: BLE001
            print(f"      >> falha ao transcrever: {e}")
            falhas.append((n, titulo))
            continue

        if not texto:
            falhas.append((n, titulo))
            continue

        out_txt.write_text(f"# {titulo}\n# {secao} | Vimeo {vid}\n\n{texto}\n", encoding="utf-8")
        out_srt.write_text("\n".join(partes_srt).strip() + "\n", encoding="utf-8")
        print(f"      OK -> {out_txt.name}")
        ok += 1

        try:
            audio.unlink()
        except OSError:
            pass

    print("=" * 68)
    print(f"  Concluido!  Transcritos: {ok} | Pulados: {pulados} | Falhas: {len(falhas)}")
    if falhas:
        print("  Nao consegui estes (rode de novo com o navegador do curso logado):")
        for n, titulo in falhas:
            print(f"     #{n:02d} {titulo}")
    print(f"\n  >> Seus textos estao na pasta:  {PASTA_SAIDA}")
    print("=" * 68)
    input("\n  Aperte Enter para fechar...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n  Interrompido. Rode de novo quando quiser - ele continua de onde parou.")
    except Exception as e:  # noqa: BLE001
        print(f"\n  ERRO inesperado: {e}")
        input("  Aperte Enter para fechar...")
