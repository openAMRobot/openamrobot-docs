# Stills, posters and tour videos re-rendered for the 9 Nov 2026 refresh: evidence

Base: `5d7bc1a` (docs #83 head). Every picture and video here is a simulation visualization rendered offline from the
roadmap pages; none is footage of the real robot. The dark-store video and the store stills 09 and 10 are not
re-rendered on 9 Nov (unchanged scene).

Method: the method of `evidence/2026-11-04-media` (resumable job script, SwiftShader render modes of exploded.html,
JPEG under 1 MB, palette-reduced posters). Scripts here: `media_job.sh` (stills, posters, tour videos), `serve.sh`
(server on port 8802 from this clone), `stills.js` and `stills_caption.py` (stills), `pictures.py` (JPEG, thumbnails,
contact sheets, posters), `tour_preview.js` (preview gate: one low-resolution frame 0.5 s after each tour keyframe).

## 1. Preview gate

Before the final renders, `tour_preview.js` rendered one 640 x 360 frame per tour stop (36 frames, `contact_preview.jpg`).
Checked by eye against the 8 Nov decisions: stop 54 shows the receiver in its plastic frame ("Receiver plastic frame
(20 mm)", "Receiver (bought later)"); stop 79.5 shows the flag rod guide on the static column and the second E-stop on
top of the moving adapter plate, button up. No stop showed a superseded position.

## 2. Tour captions changed (model/exploded.json)

| Time (s) | Change |
|---|---|
| 43.5 | Lift foot fixed through its tabs (D-20) |
| 54 | Receiver plastic frame 20 mm, 15 mm clear above, charger bought later; `tz_receiver_frame` framed and labelled |
| 71.5 | Upper-body cables through the two 50 x 25 mm openings |
| 79.5 | Flag rod guide and the second E-stop on the adapter plate; `second_estop` framed and labelled at 79.5 and 84 |

Tour length and keyframe timing are unchanged.

## 3. Outputs

See `log_summary.txt` for sizes, durations, frame counts and the determinism hashes.
