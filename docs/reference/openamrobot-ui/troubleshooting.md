---
title: Troubleshooting
tags: [builder, developer]
description: Symptom-based diagnosis for the OpenAMRobot dashboard.
---

# openamrobot-ui · Troubleshooting


**For:** someone whose dashboard is not behaving.
**Before you start:** a terminal with the workspace sourced.
**When you finish:** the cause identified, not just the symptom described.

## Diagnose in this order

The architecture is a chain. Work along it.

```
Browser  →  Flask (5050)  →  rosbridge (9090)  →  relays  →  ROS 2 topics  →  robot
```

1. Does the page open? → Flask, port `5050`
2. Is the indicator green? → rosbridge, port `9090`
3. Are topics fresh on `/health`? → the robot stack
4. Is one panel blank while others work? → that panel's relay or topic

## By symptom

### Page does not open

The UI process is not running, or port `5050` is taken.

```bash
docker compose logs -f          # Docker
ros2 node list | grep ui        # manual
```

Check nothing else is bound to `5050`. Running Docker and a manual install together will do exactly
this.

### Page opens, connection indicator is red

Rosbridge is not reachable.

- Is `rosbridge_websocket` in the logs?
- Is the configured host correct in `/config`?
- Is port `9090` reachable from the browser's machine, not just from the robot?

Remote browsers need both `5050` **and** `9090`.

### Green connection, but the map or pose is frozen

!!! danger "Do not drive"
    A frozen pose means the robot on screen is not where the robot is. Any goal you send is aimed
    at a stale position.

Open `/health` and check topic freshness. A green connection means the browser reached rosbridge.
It says nothing about whether the robot is publishing.

### Map alone is blank, everything else works

The relay chain. This is the most instructive failure in the system.

```bash
ros2 topic hz /map          # is the source publishing?
ros2 topic hz /ui/map       # is the relayed version publishing?
ros2 node list | grep relay # is map_volatile_relay running?
```

If `/map` is fine and `/ui/map` is silent, the relay is down. The browser cannot consume `/map`
directly because of its QoS durability. See [Concepts](concepts.md#why-relays-exist).

### Camera alone is blank

- Is the correct image topic selected?
- Is `web_video_server` installed? The camera node only appears when it is.
- Is port `8080` reachable?

### Route or map buttons fail

The optional helper node is not running:

```bash
ros2 launch openamr_ui_package physnode_launch.py
```

Map and route file operations depend on it. Without it the pages render but the buttons do nothing.

### UI changes do not appear after editing

The frontend is built and synced into the ROS package. Editing source is not enough:

```bash
bash scripts/build_frontend.sh
bash scripts/sync_frontend_to_ros.sh
cd ros2 && colcon build --symlink-install && source install/setup.bash
```

Then hard-refresh the browser. A cached bundle looks exactly like a build that did not happen.

### My missions and schedules disappeared

They were in `localStorage` for that browser profile. A different browser, a different machine, a
cleared cache or a private window all mean they are not there.

Not recoverable unless you backed up. See [Configuration](configuration.md#data-locations).

### Scheduled actions stopped running

Scheduler runs **in the browser tab**. Closing the tab, sleeping the laptop or navigating away
stops it. Do not use Scheduler for anything that must run unattended.

### Voice Command does not respond

The backend needs an Anthropic API key at runtime:

```bash
ANTHROPIC_API_KEY="your-key" docker compose up
```

Check it is not committed anywhere, and that it is being passed rather than baked into the image.

## Safety-related, not bugs

| Behaviour | Reality |
|:--|:--|
| Dashboard E-STOP does not always stop the robot | It is a software stop: one zero-velocity command plus a Nav2 goal cancel. Not latched, not safety-rated, depends on browser, network, rosbridge and controller. **Keep a tested physical E-stop within reach.** |
| Anyone on the network can drive the robot | Only `AUTH_MODE=open` is implemented. Keep it on a trusted network behind a firewall or authenticated proxy. |
| Missions stop when the tab closes | They are browser-side by design. |

## Still stuck

- Repository troubleshooting guide and Lesson 12 on debugging with the ROS CLI:
  [`docs/`](https://github.com/openAMRobot/openamrobot-ui/tree/main/docs)
- Organisation discussions: [github.com/orgs/openAMRobot/discussions](https://github.com/orgs/openAMRobot/discussions)
- Upstream: [rosbridge_suite](https://github.com/RobotWebTools/rosbridge_suite) ·
  [ROS 2 QoS](https://docs.ros.org/en/jazzy/Concepts/Intermediate/About-Quality-of-Service-Settings.html)

---

**Build it:** [`openamrobot-ui`](https://github.com/openAMRobot/openamrobot-ui)
