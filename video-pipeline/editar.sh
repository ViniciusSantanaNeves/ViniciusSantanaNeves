#!/usr/bin/env bash
# Pipeline completo: vídeo bruto → vídeo editado.
#
#   ./editar.sh <video.mp4> <nome-do-trabalho> [pauta.json]
#
# Sem pauta: para depois da transcrição e mostra o texto, para o Claude Code
# (skill /editar-video) ou você escrever trabalhos/<nome>/pauta.json.
# Com pauta: monta, confere e renderiza trabalhos/<nome>/editado.mp4.
#
# Variáveis opcionais:
#   CORTAR_SILENCIOS=0   não faz jump cut (padrão 1)
#   SILENCIO_MIN=0.45    silêncio mínimo para cortar, em segundos
#   MODELO=small         modelo do Whisper (tiny|base|small|medium|large-v3)
#   SO_PREVIEW=1         abre o preview no navegador em vez de renderizar
set -euo pipefail

AQUI="$(cd "$(dirname "$0")" && pwd)"
HF="$AQUI/node_modules/.bin/hyperframes"
VIDEO="${1:?Informe o vídeo}"
NOME="${2:?Informe o nome do trabalho}"
PAUTA="${3:-}"
DIR="$AQUI/trabalhos/$NOME"
mkdir -p "$DIR"

echo "▸ 0/4 Preparando o vídeo"
if [ "${CORTAR_SILENCIOS:-1}" = "1" ]; then
  python3 "$AQUI/scripts/cortar_silencios.py" "$VIDEO" "$DIR/bruto.mp4" --min "${SILENCIO_MIN:-0.45}"
else
  cp "$VIDEO" "$DIR/bruto.mp4"
fi

if [ ! -f "$DIR/transcricao.json" ]; then
  echo "▸ 1/4 Transcrevendo (Whisper, português)"
  python3 "$AQUI/scripts/transcrever.py" "$DIR/bruto.mp4" "$DIR/transcricao.json" --modelo "${MODELO:-small}"
else
  echo "▸ 1/4 Transcrição já existe — reaproveitando"
fi

if [ -z "$PAUTA" ]; then
  if [ -f "$DIR/pauta.json" ]; then PAUTA="$DIR/pauta.json"; else
    echo
    echo "Transcrição pronta em $DIR/transcricao.json"
    echo "Próximo passo: escreva $DIR/pauta.json (peça ao Claude Code: /editar-video $NOME)"
    echo "e rode de novo: ./editar.sh \"$VIDEO\" $NOME"
    exit 0
  fi
fi

echo "▸ 2/4 Montando o projeto HyperFrames"
rm -rf "$DIR/projeto"
node "$AQUI/scripts/montar.mjs" --video "$DIR/bruto.mp4" --transcricao "$DIR/transcricao.json" \
  --pauta "$PAUTA" --saida "$DIR/projeto"

cd "$DIR/projeto"
echo "▸ 3/4 Conferindo (erros de layout, área segura do Reels, leitura)"
"$HF" check --safe-zone reels || true

if [ "${SO_PREVIEW:-0}" = "1" ]; then
  "$HF" preview
  exit 0
fi

echo "▸ 4/4 Renderizando"
"$HF" render -o "$DIR/editado.mp4"
echo "✔ Pronto: $DIR/editado.mp4"
