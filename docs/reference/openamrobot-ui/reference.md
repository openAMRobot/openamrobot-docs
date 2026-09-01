---
title: Reference
tags: [developer]
description: Pages, ports, services, packages and commands for openamrobot-ui.
---

# openamrobot-ui · Reference

<span class="track track-developer">Developer</span>
{: .track-row }

**For:** a developer looking something up.
**Before you start:** nothing.
**When you finish:** you have the name you came for.

!!! note "Canonical source"
    Exact versions, routes and message definitions are canonical in the repository. When this page
    and the repository disagree, the repository is right.

## Pages

| Page | URL | Purpose |
|:--|:--|:--|
| Map | `/` | Map, goals, pose, joystick, docking, waypoints |
| Routes | `/route` | Reusable waypoint sequences |
| Maps | `/maps` | Create, save, switch, rename, organise maps |
| Programs | `/blocks` | Blockly visual programs, Voice Command |
| Scheduler | `/scheduler` | Time-triggered browser-side actions |
| Missions | `/missions` | Multi-step browser-side missions |
| Status | `/info` | Camera, telemetry, battery, system health |
| Robot | `/robot` | URDF/Xacro model, live joint information |
| Devices | `/devices` | External-device registry, serial detection |
| Health | `/health` | Readiness, topic freshness, lifecycle, diagnostics |
| Metrics | `/metrics` | Distance, uptime, success statistics |
| Recordings | `/recordings` | Rosbag recording and replay |
| Events | `/events` | Filterable event history |
| Console | `/console` | `/rosout` and topic echo |
| Parameters | `/params` | Read or change Nav2 parameters |
| Fleet | `/fleet` | Robot profiles, active-robot selection |
| Config | `/config` | Connections, Demo Mode, limits, preferences |
| Notes | `/notes` | Example plugin page |

## Services and ports

| Service | Default | Purpose |
|:--|:--|:--|
| Flask UI | `http://127.0.0.1:5050` | React dashboard and REST API |
| Rosbridge | `ws://127.0.0.1:9090` | Browser-to-ROS communication |
| Web video | `http://127.0.0.1:8080` | Optional camera streams |

## Processes in the logs

A healthy start shows:

```
flask_app
rosbridge_websocket
map_volatile_relay
nav_relays
```

The camera node appears only when `web_video_server` is installed.

## ROS 2 packages

| Package | Contents |
|:--|:--|
| `openamr_ui_bringup` | Launch files, including `ui.launch.py` |
| `openamr_ui_msgs` | UI-specific message definitions |
| `openamr_ui_package` | Backend node, maps, paths, `physnode_launch.py` |

Verify:

```bash
ros2 pkg list | grep openamr_ui
```

## Launch files

| File | Package | Starts |
|:--|:--|:--|
| `ui.launch.py` | `openamr_ui_bringup` | Dashboard, rosbridge, relays |
| `physnode_launch.py` | `openamr_ui_package` | Map and route file operations, route-following helpers |

## Commands

```bash
# Docker
docker compose up --build
docker compose up -d
docker compose logs -f
docker compose down

# Manual build
bash scripts/build_frontend.sh
bash scripts/sync_frontend_to_ros.sh
cd ros2 && colcon build --symlink-install && source install/setup.bash

# Launch
ros2 launch openamr_ui_bringup ui.launch.py
ros2 launch openamr_ui_package physnode_launch.py

# Frontend development
cd web && npm ci && npm run dev

# Tests
cd web && CI=true npm test -- --watchAll=false && npm run build
cd ../ros2 && colcon test --packages-select openamr_ui_package openamr_ui_msgs
colcon test-result --verbose
```

## Repository layout

```
openamrobot-ui/
├── web/                  React frontend
├── ros2/src/             ROS 2 packages
├── api/                  backend API
├── docs/
│   ├── lessons/          numbered lessons 00–13, plus a glossary
│   ├── extending/        panel, device and Blockly extension guides
│   ├── installation.md
│   ├── development.md
│   └── troubleshooting.md
├── scripts/              build and sync helpers
├── Dockerfile
├── docker-compose.yml
└── LICENSE               MIT
```

## Data locations

| Data | Location |
|:--|:--|
| Programs, locations, history, recordings, certificates | `~/.openamr_ui/` |
| Docker backend data | Volume `openamr_ui_data` |
| Schedules, missions, devices, profiles, metrics, preferences | Browser `localStorage` |
| Maps and routes | `ros2/src/openamr_ui_package/maps/` and `paths/` |

## Facts

| | |
|:--|:--|
| Frontend | React |
| Backend | Flask |
| Browser-to-ROS | rosbridge |
| ROS distribution | Jazzy |
| Host OS | Ubuntu 24.04 LTS |
| Node.js | 18 to 20, `>=18 <21` |
| Authentication | `open` only. `local` and `external` reserved. |
| Licence | MIT |

## Repository documentation

Lessons 00 to 13 cover the operator and architecture learning paths, with a glossary. Extension
guides cover adding a panel, a device or a Blockly block. Installation, development and
troubleshooting guides sit alongside.

Start at
[`docs/lessons/00-your-first-10-minutes.md`](https://github.com/openAMRobot/openamrobot-ui/blob/main/docs/lessons/00-your-first-10-minutes.md).

---

**Build it:** [`openamrobot-ui`](https://github.com/openAMRobot/openamrobot-ui)
