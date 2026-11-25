#!/usr/bin/env python3
"""Etapa 0 — Corte automático de silêncios (jump cut) para vídeos falados.

Uso:
  python3 scripts/cortar_silencios.py <entrada.mp4> <saida.mp4> [--min 0.45] [--limiar -35] [--folga 0.10]

  --min      silêncio mínimo (s) para cortar. 0.35 = ritmo de Reels; 0.6 = mais natural
  --limiar   volume (dB) abaixo do qual é silêncio. Ambiente ruidoso: suba para -30
  --folga    quanto de silêncio manter antes/depois de cada fala (s)
"""
import argparse
import json
import re
import subprocess


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("entrada")
    p.add_argument("saida")
    p.add_argument("--min", type=float, default=0.45)
    p.add_argument("--limiar", type=float, default=-35)
    p.add_argument("--folga", type=float, default=0.10)
    a = p.parse_args()

    total = float(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", a.entrada],
        capture_output=True, text=True, check=True).stdout)

    log = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", a.entrada, "-af",
         f"silencedetect=noise={a.limiar}dB:d={a.min}", "-f", "null", "-"],
        capture_output=True, text=True).stderr
    ini = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", log)]
    fim = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", log)]
    fim += [total] * (len(ini) - len(fim))

    # Trechos de fala = o complemento dos silêncios, com folga nas bordas.
    manter, cursor = [], 0.0
    for s, e in zip(ini, fim):
        a0, a1 = cursor, min(total, max(0.0, s) + a.folga)
        if a1 - a0 > 0.05:
            manter.append((a0, a1))
        cursor = max(0.0, e - a.folga)
    if total - cursor > 0.05:
        manter.append((cursor, total))

    if not manter:
        raise SystemExit("Nenhuma fala encontrada — confira --limiar.")

    expr = "+".join(f"between(t,{s:.3f},{e:.3f})" for s, e in manter)
    subprocess.run([
        "ffmpeg", "-v", "error", "-y", "-i", a.entrada,
        "-vf", f"select='{expr}',setpts=N/FRAME_RATE/TB",
        "-af", f"aselect='{expr}',asetpts=N/SR/TB",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p",
        "-g", "30", "-c:a", "aac", "-b:a", "192k", a.saida,
    ], check=True)

    novo = sum(e - s for s, e in manter)
    print(json.dumps({
        "ok": True, "original": round(total, 2), "final": round(novo, 2),
        "removido": round(total - novo, 2), "cortes": max(0, len(manter) - 1), "saida": a.saida,
    }))


if __name__ == "__main__":
    main()
