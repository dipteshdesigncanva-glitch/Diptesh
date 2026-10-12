#!/usr/bin/env bash
# Rebuild clips/ and frames/ from the brand's product-page screen recording, then remove the mouse cursor.
# usage: ./extract_clips.sh path/to/recording.mp4
set -euo pipefail
SRC="$1"; cd "$(dirname "$0")"
mkdir -p frames clips
for t in 1.0 3.9 6.0 8.6 13.4 14.2 22.8 27.9; do ffmpeg -v error -y -ss "$t" -i "$SRC" -frames:v 1 "frames/t$t.png"; done
while read -r name start dur crop; do
  mkdir -p "clips/$name"
  ffmpeg -v error -y -ss "$start" -t "$dur" -i "$SRC" -vf "crop=$crop,fps=30" -q:v 2 "clips/$name/%03d.jpg"
done <<'CLIPS'
rgb 5.0 2.3 1235:435:335:370
rotate 12.9 1.2 1300:815:300:93
venom 16.95 1.45 640:818:860:90
layers 15.25 1.65 1000:818:0:90
hotswap 19.85 1.6 950:695:880:210
game 23.35 2.0 1430:610:0:295
CLIPS
cp frames/t6.0.png cursor_ref.png
python3 clean_cursor.py cursor_ref.png "frames/t*.png" "clips/*/[0-9]*.jpg"
