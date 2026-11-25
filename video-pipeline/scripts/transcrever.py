#!/usr/bin/env python3
"""Etapa 1 — Transcrição com tempo por palavra (português).

Uso:
  python3 scripts/transcrever.py <video.mp4> <saida.json> [--modelo small]

Saída: lista de palavras no formato que o HyperFrames espera
  [{"id": "w0", "text": "Olha", "start": 0.12, "end": 0.40}, ...]

Também remove palavras "fantasmas" que o Whisper inventa no silêncio final.
"""
import argparse
import json
import re
import subprocess
import sys


def duracao(arquivo: str) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", arquivo],
        capture_output=True, text=True, check=True,
    )
    return float(out.stdout.strip())


def inicio_do_silencio_final(arquivo: str, total: float) -> float:
    """Retorna onde começa o silêncio que vai até o fim do arquivo (ou o total)."""
    proc = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", arquivo, "-af",
         "silencedetect=noise=-35dB:d=0.6", "-f", "null", "-"],
        capture_output=True, text=True,
    )
    inicios = [float(m) for m in re.findall(r"silence_start: ([\d.]+)", proc.stderr)]
    fins = [float(m) for m in re.findall(r"silence_end: ([\d.]+)", proc.stderr)]
    if inicios and len(fins) < len(inicios):  # último silêncio vai até o fim
        return inicios[-1]
    return total


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("video")
    p.add_argument("saida")
    p.add_argument("--modelo", default="small",
                   help="tiny | base | small | medium | large-v3 (maior = mais preciso e lento)")
    p.add_argument("--idioma", default="pt")
    a = p.parse_args()

    from faster_whisper import WhisperModel

    total = duracao(a.video)
    corte = inicio_do_silencio_final(a.video, total)

    # Decodifica o áudio com o ffmpeg (16 kHz mono) em vez do PyAV, que
    # quebra entre versões; o Whisper recebe o áudio já pronto.
    import numpy as np
    pcm = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", a.video, "-ac", "1", "-ar", "16000",
         "-f", "s16le", "-"],
        capture_output=True, check=True,
    ).stdout
    audio = np.frombuffer(pcm, np.int16).astype(np.float32) / 32768.0

    modelo = WhisperModel(a.modelo, device="auto", compute_type="int8")
    segmentos, info = modelo.transcribe(
        audio, language=a.idioma, word_timestamps=True, vad_filter=True,
    )

    palavras = []
    for seg in segmentos:
        for w in seg.words or []:
            texto = w.word.strip()
            if not texto or w.start >= corte:
                continue
            palavras.append({
                "id": f"w{len(palavras)}",
                "text": texto,
                "start": round(max(0.0, w.start), 3),
                "end": round(min(w.end, total), 3),
            })

    with open(a.saida, "w", encoding="utf-8") as f:
        json.dump(palavras, f, ensure_ascii=False, indent=1)

    texto = " ".join(w["text"] for w in palavras)
    print(json.dumps({
        "ok": True, "palavras": len(palavras), "duracao": total,
        "idioma": info.language, "saida": a.saida, "texto": texto,
    }, ensure_ascii=False))


if __name__ == "__main__":
    sys.exit(main())
