#!/bin/sh
# Captura uma live do YouTube em 1080p60 sem recodificar (vídeo 312 + áudio 234 do HLS, -c copy), em blocos .ts.
# uso: sh scripts/captura_youtube.sh URL PASTA [MINUTOS]
# - reconecta sozinho (URL HLS expirada, ffmpeg morto);
# - vigia o ATRASO da mídia gravada em relação ao relógio: se passar de 150 s, reinicia o ffmpeg
#   e puxa a lacuna da janela HLS (~15 min) para PASTA-recup/<inicio>-0000.ts (vira job igual aos blocos).
URL="$1"; DIR="$2"; MIN="${3:-15}"; RECUP="$DIR-recup"
export PATH="$HOME/.local/bin:$PATH"
mkdir -p "$DIR" "$RECUP"; n=0; gap_from="${GAP_FROM:-}"  # GAP_FROM=epoch: já começa recuperando a lacuna desde esse instante
FFOPT="-nostdin -loglevel error -http_persistent 0 -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 4 -seg_max_retry 8 -rw_timeout 15000000"
log() { echo "$(date -u +%FT%TZ) $*" >> "$DIR/captura.log"; }
media_end() {  # segundos de mídia já gravados na sessão $t
  ls "$DIR"/$t-*.ts >/dev/null 2>&1 || { echo 0; return; }
  last=$(ls "$DIR"/$t-*.ts | tail -1); k=$(basename "$last" .ts); k=$((10#${k#*-} + 1))  # índice no nome: blocos fechados já viraram job
  p=$(tail -c 4000000 "$last" | ffprobe -v error -select_streams a -show_entries packet=pts_time -of csv=p=0 - 2>/dev/null | tail -1)
  echo $(( (k-1)*MIN*60 + ${p%.*} + 0 ))
}
while :; do
  urls=$(yt-dlp -g -f "312+234/311+234" --no-warnings "$URL" 2>>"$DIR/yt-dlp.err")
  v=$(echo "$urls" | sed -n 1p); a=$(echo "$urls" | sed -n 2p)
  if [ -z "$v" ] || [ -z "$a" ]; then
    log "sem URL (live acabou?)"; sleep 20; n=$((n+1)); [ "$n" -ge 9 ] && { log "encerrando: sem URL por 3 min"; exit 0; }; continue
  fi
  n=0; t=$(date +%s)
  log "ffmpeg inicia sessão $t"
  ffmpeg $FFOPT -i "$v" -i "$a" -map 0:v -map 1:a -c copy -f segment -segment_time $((MIN*60)) -reset_timestamps 1 \
    "$DIR/$t-%04d.ts" 2>>"$DIR/ffmpeg.err" &
  pid=$!
  if [ -n "$gap_from" ]; then  # lacuna da sessão anterior: de $gap_from (epoch) até agora, da janela HLS
    lost=$((t - gap_from)); N=$(curl -s -m 20 "$v" | grep -c EXTINF)
    if [ "$lost" -ge 20 ] && [ "$lost" -le 800 ] && [ "$N" -gt 0 ]; then
      idx=$(( N - lost/2 - 15 )); [ "$idx" -lt 0 ] && idx=0
      st=$((gap_from - 20)); log "backfill de ${lost}s a partir de $gap_from (índice HLS $idx de $N)"
      ffmpeg $FFOPT -live_start_index $idx -i "$v" -live_start_index $idx -i "$a" -map 0:v -map 1:a -c copy -t $((lost+40)) \
        "$RECUP/$st-0000.ts" 2>>"$RECUP/ffmpeg.err" &
    else
      log "lacuna de ${lost}s fora do que dá para recuperar (VOD depois)"
    fi
    gap_from=""
  fi
  while kill -0 $pid 2>/dev/null; do
    sleep 30
    el=$(( $(date +%s) - t )); me=$(media_end); lag=$((el - me))
    if [ "$el" -gt 150 ] && [ "$lag" -gt 150 ]; then
      log "atrasado ${lag}s (mídia $me s em $el s), reiniciando"; gap_from=$((t + me)); kill -9 $pid; break
    fi
  done
  wait $pid 2>/dev/null; rc=$?
  if [ -z "$gap_from" ]; then  # ffmpeg terminou sozinho: o que faltou até agora
    me=$(media_end); gap_from=$((t + me))
  fi
  log "ffmpeg terminou (rc=$rc)"; sleep 2
done
