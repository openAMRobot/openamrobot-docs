# Store video at 4x speed (robot page)

Simulation visualization only, rendered offline from `docs/assets/roadmap/robot.html` in render mode. Not footage
of the real robot. The store video `media/openamrobot-2-store-1080p.mp4` is re-rendered at 4x simulation speed
(it was 7.5x in #59). It uses the same "Run order (8 items)" run (255.9 s of simulated time), the same cameras and
cuts (Follow, with 1.3 s Side cuts around each grasp) and the same full look. The corner caption
"OpenAMRobot 2.0, simulation visualization, 4x speed" is drawn by the page controller (no overlay pass). The
pictures, tour videos, tour posters, page layout, materials and geometry are not changed.

- Base: `8c9116085d9f1a2f0c8bad20596f7a5330063251` (main after #59)
- Head: the last commit of this branch (see the PR)

## Changed files

| File | Change |
| --- | --- |
| `docs/assets/roadmap/media/openamrobot-2-store-1080p.mp4` | re-rendered at 4x, 1536 frames, 64.0 s |
| `docs/assets/roadmap/media/openamrobot-2-store-1080p-poster.png` | new poster from frame 788 of the new render |
| `docs/assets/roadmap/media/store/thumbs/store_video_poster.jpg` | 640 x 360 thumbnail of the same frame |
| `docs/assets/roadmap/robot.html` | the sentence under the video: duration, size, speed |
| `scripts/render_store.js` | `--target-bytes N` / `--bitrate K`: two-pass x264 encode instead of a fixed CRF |

## Media

| File | Size (bytes) | sha256 |
| --- | --- | --- |
| `media/openamrobot-2-store-1080p.mp4` | 14,506,295 | `3b30d890b4770a7b6b8bfe86e4c509032ec3cf6822a73c3f4917c96c3a52a5c6` |
| `media/openamrobot-2-store-1080p-poster.png` (1920 x 1080, 192 colours) | 681,164 | `db24d776b58ecce523a9ae42b835b2060f7b6890e5c4a2a1f3f3575646f1a0f4` |
| `media/store/thumbs/store_video_poster.jpg` (640 x 360, quality 82) | 59,223 | `97b37b20d64d398bf48bc26d018c19171fe9708c8dacbe76882b3448f8b8ad6f` |

Video (ffprobe): H.264, yuv420p, 1920 x 1080, 24/1 fps, 1536 frames, duration 64.000 s, no audio stream,
average bit rate 1,813,286 bit/s (container), encoded with two-pass x264 `medium` at 1828 kbit/s.

Encode: the first two-pass run used `--target-bytes 14500000` (computed 1776 kbit/s) and came out at 14,093,249
bytes (x264 undershoots the requested average); the second run used `--bitrate 1828` (1776 x 14.5 / 14.09) and
gives 14,506,295 bytes, at 15 MB or less (`MEDIA_MAX_BYTES` in `check_roadmap.py` is unchanged). Each encode took
about 1.5 min.

Poster: frame 788 (sim 131.3 s, Follow view), the same moment of the run as the #59 poster (frame 420 at 7.5x).
It is taken from the rendered PNG frame of this video, with the 4x caption: palette of 192 colours
(`palettegen` / `paletteuse`), and a 640 px JPEG thumbnail for the `poster` attribute.

Sample frames from the encoded MP4 (JPEG quality 88), in `frames/`:

| Position | Frame | Video time | Sim time | Size (bytes) | sha256 |
| --- | --- | --- | --- | --- | --- |
| 10 % | 153 | 6.4 s | 25.5 s | 287,087 | `d60dfc984196e242061ba6c1ff1b5b7908756875f13907f279fb67a1a3d34987` |
| 30 % | 460 | 19.2 s | 76.7 s | 314,602 | `bc62d56f1b3c74934bccca2e5867fcf215daea42076ec777945249c9d6e4102e` |
| 50 % | 768 | 32.0 s | 128.0 s | 389,819 | `da2f774ccb0f02022aaddaa85d2e552b043d24fa894b0e454d15b93d3f2c67ff` |
| 70 % | 1075 | 44.8 s | 179.2 s | 231,905 | `2cf99e23d52a3f11126fe8739a5004a0d963b0171ee35f1842a93a53cf69ef2b` |
| 90 % | 1382 | 57.6 s | 230.3 s | 241,790 | `e39de725bc8584ae8100beb7edbb94d2c6177cc9fe4aee9f4489c749460ca099` |

## Render

Headless Chromium (Playwright) with SwiftShader (no GPU), 4 vCPU, one worker. `render_job.sh` is the resumable
job (frames are written as `.part` files and renamed; a re-run skips finished frames and stages);
`render_job.log` is its log. `$S` is a scratch directory; `$S/serve.sh` serves a copy of
`docs/assets/roadmap` of this branch on port 8802.

- Frame-time estimate: the first 60 frames (det1) took 1068 s, 17.8 s per frame, so 1536 frames were estimated
  at about 27,300 s (7.6 h).
- Actual: the container restarted three times; the job resumed each time from the frames on disk.

| Segment | Start (UTC) | End (UTC) | Frames | Time |
| --- | --- | --- | --- | --- |
| 1 | 27 Oct 17:23:24 | about 20:53 (last log line: frame 570 at 20:47) | 0 to 589 | about 3 h 30 min |
| 2 | 27 Oct 22:52:39 | 22:58:45 | 590 to 601 | 6 min 6 s |
| 3 | 28 Oct 00:56:08 | 03:30:52 | 602 to 1530 | 2 h 34 min 44 s |
| 4 | 28 Oct 03:31:45 | 03:38:31 | 1531 to 1535, then hashes of all frames | 6 min 46 s |

  Total rendering time about 6 h 18 min (10 h 15 min wall clock including the restarts). Segment 3 ran at
  10.0 s per frame, faster than segment 1 (about 21 s per frame), on the restarted container.

## Determinism

Frames 0 to 59 rendered twice: once with one worker (`det1.sha256`), once with two workers into a separate
directory (`det2.sha256`). The two hash lists are identical (`cmp`), and the first 60 lines of the full run's
hashes (`full.sha256`, 1536 PNG frames) are the same as `det1.sha256`.

## Checks

Commands (run from the repository root; `$S/venv` has the packages of `requirements.txt`):

```
S=<scratch dir>; S=$S bash evidence/2026-10-27-store-video-4x/render_job.sh
node scripts/render_store.js 1920 1080 docs/assets/roadmap/media/openamrobot-2-store-1080p.mp4 --fps 24 --speed 4 \
  --frames-dir $S/x4/frames --resume 1 --target-bytes 14500000 --base http://localhost:8802/
node scripts/render_store.js 1920 1080 docs/assets/roadmap/media/openamrobot-2-store-1080p.mp4 --fps 24 --speed 4 \
  --frames-dir $S/x4/frames --resume 1 --bitrate 1828 --base http://localhost:8802/
ffprobe -v error -show_entries format=duration,bit_rate,size:stream=codec_name,width,height,r_frame_rate,nb_frames,pix_fmt \
  -of default=nw=1 docs/assets/roadmap/media/openamrobot-2-store-1080p.mp4
python3 evidence/2026-10-27-store-video-4x/add_media_section.py docs/assets/roadmap/robot.html 64.0 14506295 24 4 255.9
python3 scripts/check_roadmap.py
$S/venv/bin/mkdocs build --strict -d $S/site
bash scripts/check_docs.sh
node evidence/2026-10-27-store-media/first_load.js http://localhost:8802/ http://localhost:8807/
node evidence/2026-10-27-store-media/page_checks.js http://localhost:8802/ http://localhost:8807/ $S/x4/pc
```

Port 8807 serves `docs/assets/roadmap` of main `8c91160` (`git archive`).

| Check | Result |
| --- | --- |
| `check_roadmap.py` | passed (exit 0): "Roadmap check passed: 6 pages, snapshot 24 Oct 2026." |
| `mkdocs build --strict` | passed (exit 0) |
| `check_docs.sh` | passed with 0 warnings (exit 0) |
| Console, 375 and 1280 px (`page_checks.json`) | robot.html and exploded.html: no console errors or warnings, no failed requests |
| Horizontal scroll (`page_checks.json`) | none: scrollWidth equals innerWidth (375 and 1280) on both pages |
| First load (`first_load.json`) | 4,164,300 bytes after, 4,164,335 bytes on main (-35); budget 4,195,678 (`ROBOT_FIRST_LOAD_MAX_BYTES`, #59) |
| Sentence under the video | "Store run: 1920 x 1080, 24 fps, H.264, no audio, 64.0 s, 14.5 MB; played at 4x speed, 255.9 s of simulated time in 64.0 s of video." |

`robot_375_media_section.jpg` and `robot_1280_media_section.jpg` show the media section with the new sentence.

## Not verified

- Playback on a real GPU and in browsers other than headless Chromium; all frames were rendered with SwiftShader.
- Appearance of the physical robot: this is a simulation visualization, not footage.
- Thumbnail loading after scrolling: in this headless SwiftShader run the eight thumbnails got their `src` after
  scrolling to the section but had not finished loading within 120 s (the 3D view keeps the main thread busy);
  each thumbnail URL returns HTTP 200 from the local server. The thumbnails and their loading code are unchanged
  from main.
- Segment 1's end time is estimated from the last log line before the container restart.
