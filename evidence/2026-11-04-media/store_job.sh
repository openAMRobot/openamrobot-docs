#!/bin/bash
# resumable store job: determinism (frames 0-59, 1 and 2 workers), then the full run with 2 workers
S=/tmp/claude-0/-home-user-openamrobot-docs/2c25618e-29bc-55ce-9083-99e144bd4f18/scratchpad
R=/home/user/openamrobot-docs
$S/serve.sh
cd $R
B=http://localhost:8802/
log() { echo "$(date -u +%FT%TZ) $*" >> $S/store_job.log; }
for k in 1 2; do
  [ -f $S/det$k.sha ] || { mkdir -p $S/det$k; log "det$k start"; (time node scripts/render_store.js 1920 1080 --frames 0:60 --frames-dir $S/det$k --resume 1 --workers $k --fps 24 --speed 7.5 --hashes $S/det$k.sha.tmp --base $B) >> $S/store_job.log 2>&1 && mv $S/det$k.sha.tmp $S/det$k.sha; log "det$k done"; }
done
# reuse the determinism frames 0-59 as the start of the full run
mkdir -p $S/storeframes; [ -f $S/storeframes/00000.png ] || cp $S/det1/*.png $S/storeframes/
[ -f $S/store-1080p.mp4 ] || { log "store start"; (time node scripts/render_store.js 1920 1080 $S/store-1080p.tmp.mp4 --fps 24 --speed 7.5 --workers 2 --frames-dir $S/storeframes --resume 1 --hashes $S/store.sha --base $B) >> $S/store_job.log 2>&1 && mv $S/store-1080p.tmp.mp4 $S/store-1080p.mp4; log "store done"; }
log STORE_ALL_DONE
