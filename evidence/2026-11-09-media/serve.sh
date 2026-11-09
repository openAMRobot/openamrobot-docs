#!/bin/bash
# start the server on 8802 from this clone if not already serving it
R=/home/claude/openamrobot-docs/docs/assets/roadmap
if ! curl -sf -o /dev/null http://localhost:8802/robot.html; then
  (cd $R && nohup python3 -m http.server 8802 >/dev/null 2>&1 &)
  sleep 2
fi
