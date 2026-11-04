#!/bin/bash
# resumable media job (4 Nov 2026): each stage runs only if its output is missing (re-run after a container restart).
# The store video runs in store_job.sh (determinism frames 0 to 59 with 1 and 2 workers, then the full run, 2 workers).
S=/tmp/claude-0/-home-user-openamrobot-docs/2c25618e-29bc-55ce-9083-99e144bd4f18/scratchpad
R=/home/user/openamrobot-docs
E=$R/evidence/2026-11-04-media
$S/serve.sh
cd $R
B=http://localhost:8802/
log() { echo "$(date -u +%FT%TZ) $*" >> $S/media_job.log; }
# 1. store pictures (PNG, converted to JPEG later): sim time and camera as in October
mkdir -p $S/pics
while read name w h t cam; do
  [ -f $S/pics/$name.png ] || { log "pic $name"; node scripts/render_store.js $w $h --still $t --cam $cam --out $S/pics/$name.tmp.png --fps 24 --speed 7.5 --base $B >> $S/media_job.log 2>&1 && mv $S/pics/$name.tmp.png $S/pics/$name.png; }
done <<'L'
01_aisle_follow 1920 1080 128 follow
02_pick_side 1920 1080 15.6 pick
03_place_tote 1920 1080 21.6 tote
04_front_low 1920 1080 40 front
05_store_overview 1920 1080 100 store
06_dock 1920 1080 255.9 over
02_pick_side_1080x1350 1080 1350 15.6 pick
04_front_low_1080x1350 1080 1350 40 front
L
# 2. high-resolution stills (PNG), caption burned in later
[ -f $S/stills/10_store_at_dock.png ] || { log "stills start"; node $E/stills.js $B $S/stills >> $S/media_job.log 2>&1; log "stills done"; }
# 3. tour posters and the no-WebGL image (October script: frame 780, opened base; frame 0 raw canvas)
[ -f $S/posters/exploded-static.png ] || { mkdir -p $S/posters; log "posters"; node $R/evidence/2026-10-27-store-media/exploded_stills.js $B $S/posters >> $S/media_job.log 2>&1; }
# 4. tour videos: 1080p twice (byte identity), then the vertical cut
for v in tour1080a tour1080b tour1080x1350; do
  case $v in tour1080x1350) W=1080; H=1350;; *) W=1920; H=1080;; esac
  [ -f $S/$v.mp4 ] || { log "$v start"; (time node scripts/render_tour.js $W $H $S/$v.tmp.mp4 $B) >> $S/media_job.log 2>&1 && mv $S/$v.tmp.mp4 $S/$v.mp4; log "$v done"; }
done
log ALL_DONE
