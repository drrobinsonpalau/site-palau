#!/bin/bash
# Converte um vídeo para o formato aceito pelo Instagram (Reels/Stories):
# H.264 High 4.1, 1080x1920, 30 fps constantes, ~6 Mbps, AAC estéreo 48 kHz,
# índice (moov) no início do arquivo e cores BT.709.
# Uso: ./para-instagram.sh entrada.mp4 [saida.mp4]
set -e
entrada="$1"
saida="${2:-${entrada%.mp4}-instagram.mp4}"
ffmpeg -v error -y -i "$entrada" \
  -vf "scale=1080:1920:flags=lanczos,fps=30,format=yuv420p" \
  -c:v libx264 -profile:v high -level:v 4.1 -preset slow -b:v 6M -maxrate 8M -bufsize 12M \
  -g 60 -keyint_min 30 -sc_threshold 0 \
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 \
  -c:a aac -b:a 128k -ar 48000 -ac 2 \
  -movflags +faststart \
  "$saida"
echo "$saida"
