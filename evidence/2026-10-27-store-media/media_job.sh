#!/bin/bash
# resumable media job: each stage runs only if its output is missing (re-run after a container restart)
S=/tmp/claude-0/-home-user-openamrobot-docs/03ec3bc6-39ad-5310-9115-eabb461b907e/scratchpad
R=/home/user/openamrobot-docs
$S/serve.sh
cd $R
B=http://localhost:8802/
log() { echo "$(date -u +%FT%TZ) $*" >> $S/media_job.log; }
# 1. determinism: frames 0 to 59 twice (1 worker, 2 workers)
for k in 1 2; do
  [ -f $S/det$k.sha ] || { mkdir -p $S/det$k; log "det$k start"; (time node scripts/render_store.js 1920 1080 --frames 0:60 --frames-dir $S/det$k --resume 1 --workers $k --fps 24 --speed 7.5 --hashes $S/det$k.sha.tmp --base $B) >> $S/media_job.log 2>&1 && mv $S/det$k.sha.tmp $S/det$k.sha; log "det$k done"; }
done
# 2. pictures (PNG, converted to JPEG later)
mkdir -p $S/pics
while read name w h t cam; do
  [ -f $S/pics/$name.png ] || { log "pic $name"; node scripts/render_store.js $w $h --still $t --cam $cam --out $S/pics/$name.png --fps 24 --speed 7.5 --base $B >> $S/media_job.log 2>&1; }
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
# 3. tour videos: 1080p twice (byte identity), then the vertical cut
for v in tour1080a tour1080b tour1080x1350; do
  case $v in tour1080x1350) W=1080; H=1350;; *) W=1920; H=1080;; esac
  [ -f $S/$v.mp4 ] || { log "$v start"; (time node scripts/render_tour.js $W $H $S/$v.tmp.mp4 $B) >> $S/media_job.log 2>&1 && mv $S/$v.tmp.mp4 $S/$v.mp4; log "$v done"; }
done
log ALL_DONE
