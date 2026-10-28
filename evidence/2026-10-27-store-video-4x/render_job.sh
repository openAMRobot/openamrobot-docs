#!/bin/bash
# store video at 4x: resumable (re-run after a container restart); stages skip finished work
S=${S:?set S to a scratch directory}
X=$S/x4
$S/serve.sh
cd /home/user/openamrobot-docs
log() { echo "$(date -u +%FT%TZ) $*" >> $X/job.log; }
A="--fps 24 --speed 4 --base http://localhost:8802/"
[ -f $X/det1.sha ] || { log det1; (time node scripts/render_store.js 1920 1080 --frames 0:60 --frames-dir $X/frames --resume 1 --hashes $X/det1.tmp $A) >> $X/job.log 2>&1 && mv $X/det1.tmp $X/det1.sha; }
[ -f $X/det2.sha ] || { log det2; (time node scripts/render_store.js 1920 1080 --frames 0:60 --frames-dir $X/det2 --resume 1 --workers 2 --hashes $X/det2.tmp $A) >> $X/job.log 2>&1 && mv $X/det2.tmp $X/det2.sha; }
[ -f $X/full.sha ] || { log full; (time node scripts/render_store.js 1920 1080 --frames 0:100000 --frames-dir $X/frames --resume 1 --hashes $X/full.tmp $A) >> $X/job.log 2>&1 && mv $X/full.tmp $X/full.sha; }
log ALL_DONE
