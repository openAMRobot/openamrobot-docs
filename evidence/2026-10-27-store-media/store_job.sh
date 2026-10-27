#!/bin/bash
# resumable full store render (re-run after a container restart)
S=/tmp/claude-0/-home-user-openamrobot-docs/03ec3bc6-39ad-5310-9115-eabb461b907e/scratchpad
$S/serve.sh
cd /home/user/openamrobot-docs && (time node scripts/render_store.js 1920 1080 $S/store-1080p.mp4 --fps 24 --speed 7.5 --frames-dir $S/storeframes --resume 1 --recaption 1 --hashes $S/store.sha --base http://localhost:8802/) >> $S/store_render.log 2>&1
echo STORE_DONE >> $S/store_render.log
