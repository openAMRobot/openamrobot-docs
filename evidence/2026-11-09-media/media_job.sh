#!/bin/bash
# Resumable media job (9 Nov 2026): each stage runs only if its output is missing, so it can be re-run after the
# container stops it. Method of evidence/2026-11-04-media/media_job.sh without the store pictures and the store video
# (unchanged on 9 Nov). The 1080p tour is rendered once with its PNG frames kept and encoded at CRF 27 (15 MB limit);
# determinism: frames 0 to 59 are rendered a second time and their hashes compared (tour_frames_0-59.sha256).
S=${S:-/tmp/media9}
R=/home/claude/openamrobot-docs
E=$R/evidence/2026-11-09-media
mkdir -p $S
bash $E/serve.sh
cd $R
B=http://localhost:8802/
log() { echo "$(date -u +%FT%TZ) $*" >> $S/media_job.log; }
# 1. high-resolution stills 01 to 08 (robot only; the store stills 09 and 10 are not re-rendered)
for n in 01 02 03 04 05 06 07 08; do
  ls $S/stills/${n}_*.png >/dev/null 2>&1 || { log "still $n"; node $E/stills.js $B $S/stills $n >> $S/media_job.log 2>&1; }
done
# 2. tour posters and the no-WebGL image
[ -f $S/posters/exploded-static.png ] || { mkdir -p $S/posters; log "posters"; node $R/evidence/2026-10-27-store-media/exploded_stills.js $B $S/posters >> $S/media_job.log 2>&1; }
# 3. tour videos (frames kept, resumable)
tour() { local v=$1 W=$2 H=$3; shift 3; [ -f $S/$v.mp4 ] || { log "$v start"; (time node scripts/render_tour.js $W $H $S/$v.tmp.mp4 $B "$@") >> $S/media_job.log 2>&1 && mv $S/$v.tmp.mp4 $S/$v.mp4; log "$v done"; }; }
tour tour1080p 1920 1080 --frames-dir $S/tourframes1080 --resume 1 --crf 27
tour tour1080x1350 1080 1350 --frames-dir $S/tourframes1350 --resume 1 --crf 27
log ALL_DONE
