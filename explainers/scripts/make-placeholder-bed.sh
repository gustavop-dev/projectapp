#!/usr/bin/env bash
# Genera una cama musical de reemplazo (pad sintético suave, libre de derechos,
# 84 s) con ffmpeg puro. Sirve para que el pipeline tenga música desde el primer
# render; reemplazala por una pista con licencia en shared/music/bed.mp3 cuando
# el operador la provea (dejá la licencia en shared/music/LICENSE.txt).
#
#   bash scripts/make-placeholder-bed.sh
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT_DIR="$HERE/../shared/music"
mkdir -p "$OUT_DIR"

# Progresión de 4 acordes (D · Bm · G · A) de 8 s cada uno, con envolvente Hann
# por acorde para que cada uno "respire"; cuatro voces por acorde.
CHORD='mod(floor(t/8),4)'
ENV='(0.5-0.5*cos(2*PI*mod(t,8)/8))'
V1="if(lt($CHORD,1),146.83,if(lt($CHORD,2),123.47,if(lt($CHORD,3),98,110)))"
V2="if(lt($CHORD,1),185,if(lt($CHORD,2),146.83,if(lt($CHORD,3),123.47,138.59)))"
V3="if(lt($CHORD,1),220,if(lt($CHORD,2),185,if(lt($CHORD,3),146.83,164.81)))"
V4="if(lt($CHORD,1),293.66,if(lt($CHORD,2),246.94,if(lt($CHORD,3),196,220)))"
EXPR="$ENV*(0.30*sin(2*PI*t*$V1)+0.22*sin(2*PI*t*$V2)+0.18*sin(2*PI*t*$V3)+0.12*sin(2*PI*t*$V4)+0.06*sin(2*PI*t*($V4*1.003)))"

ffmpeg -y -hide_banner -loglevel error \
  -f lavfi -i "aevalsrc='${EXPR}|${EXPR}':s=48000:d=84" \
  -af "lowpass=f=1400,tremolo=f=0.35:d=0.15,aecho=0.8:0.6:180|340:0.28|0.16,afade=t=in:d=3,afade=t=out:st=80:d=4,loudnorm=I=-20:TP=-2:LRA=9" \
  -c:a libmp3lame -q:a 2 "$OUT_DIR/bed.mp3"

cat > "$OUT_DIR/LICENSE.txt" <<'EOF'
bed.mp3 — pad sintético generado con ffmpeg (scripts/make-placeholder-bed.sh).
Sin autoría de terceros ni licencia externa: puede usarse libremente.
Reemplazar por la pista definitiva y documentar acá su licencia.
EOF

ffprobe -v error -show_entries format=duration,size -of default=nw=1 "$OUT_DIR/bed.mp3"
