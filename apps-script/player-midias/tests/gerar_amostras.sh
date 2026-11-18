#!/bin/sh
# Gera um vídeo de 90 s, o mp3 correspondente e uma transcrição no formato do painel.
set -e
DIR="${1:-/tmp/p45teste}"; mkdir -p "$DIR"; cd "$DIR"
STEM=00542934320248172001_2026_02_26_0001
ffmpeg -hide_banner -loglevel error -y -f lavfi -i "testsrc2=size=640x360:rate=25:duration=90" -f lavfi -i "sine=frequency=440:duration=90" \
  -c:v libx264 -pix_fmt yuv420p -preset veryfast -c:a aac -movflags +faststart "$STEM.mp4"
ffmpeg -hide_banner -loglevel error -y -i "$STEM.mp4" -vn -ac 1 -ar 32000 -b:a 32k "$STEM.mp3"
cp "$STEM.mp3" 00542934320248172001_2026_02_26_0002.mp3
python3 "$(dirname "$0")/transcricao_exemplo.py" "$DIR"
