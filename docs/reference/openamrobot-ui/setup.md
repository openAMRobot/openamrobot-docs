---
title: Set up
tags: [builder, developer]
description: Run the OpenAMRobot dashboard in Demo Mode or against a real robot.
---

# openamrobot-ui · Set up

<span class="track track-builder">Builder</span> <span class="track track-developer">Developer</span>
{: .track-row }

**For:** anyone who wants the dashboard running.
**Before you start:** Docker, or Ubuntu 24.04 with ROS 2 Jazzy.
**When you finish:** the dashboard open in your browser, in Demo Mode or connected to a robot.

## Start in Demo Mode

Five minutes, no robot, no ROS. Do this first even if you have hardware.

```bash
git clone https://github.com/openAMRobot/openamrobot-ui.git
cd openamrobot-ui
docker compose up --build
```

Then:

1. Open `http://127.0.0.1:5050/`
2. Choose **Explore without a robot** in the first-run guide
3. If the guide does not appear, open `/config` and enable **Demo Mode**
4. Confirm the **purple Demo Mode banner** and the **green connection indicator**

Demo Mode uses browser-side sample data. Nothing you press commands a real robot.

## Requirements

| Use case | Required |
|:--|:--|
| Docker demo or deployment | Docker Engine and Docker Compose. Linux or WSL recommended for host networking. |
| Manual installation | Ubuntu 24.04, ROS 2 Jazzy, Python 3, `colcon`, Node.js and npm |
| Live operation | A separately running robot or simulation stack |
| Remote browser | Access to TCP ports `5050`, `9090`, and optionally `8080` |
| Voice Command | An Anthropic API key supplied to the backend at runtime |

### Version compatibility

| Component | Target | Note |
|:--|:--|:--|
| Ubuntu | 24.04 LTS | Manual-install target |
| ROS 2 | Jazzy | Required by the documented packages and commands |
| Node.js | 18 to 20 | Enforced by `engines` (`>=18 <21`). CI validates on Node 20. |
| `openamr-platform-sw` | Jazzy branch, pinned commit | **TO CONFIRM** — record the known-good SHA per deployment |
| Robot hardware | Topic-compatible platform | Revision not yet pinned. Validate drivers, limits, docking and E-stop per robot. |

!!! note "Pin your platform commit"
    Until platform and hardware releases are pinned, treat a known-working platform commit and
    robot revision as part of each deployment's configuration. Write it down. A UI that worked last
    month against an unpinned platform is not evidence that it works today.

=== "Docker"

    ```bash
    docker compose up --build
    ```

    Useful:

    ```bash
    docker compose up -d       # background
    docker compose logs -f     # follow logs
    docker compose down        # stop, keep saved backend data
    ```

    With Voice Command:

    ```bash
    ANTHROPIC_API_KEY="your-key" docker compose up
    ```

    Real `.env` files are excluded from images. Pass secrets at runtime; never bake them in.

    **Success check.** The dashboard opens on port `5050`, and the logs show `flask_app`,
    `rosbridge_websocket`, `map_volatile_relay` and `nav_relays`. The camera node appears only when
    `web_video_server` is installed.

=== "Manual install"

    Install ROS 2 Jazzy, Node.js, npm and the declared ROS dependencies, then:

    ```bash
    cd ~/openamrobot-ui
    bash scripts/build_frontend.sh
    bash scripts/sync_frontend_to_ros.sh

    cd ros2
    source /opt/ros/jazzy/setup.bash
    colcon build --symlink-install
    source install/setup.bash
    ros2 launch openamr_ui_bringup ui.launch.py
    ```

    The backend needs Xacro for the Robot Description page.

    **Success check:**

    ```bash
    ros2 pkg list | grep openamr_ui
    ```

    Should list `openamr_ui_bringup`, `openamr_ui_msgs` and `openamr_ui_package`.

!!! warning "Do not run both"
    Docker and a manual install will fight over the same ports. Pick one.

## Connect to a real robot or simulation

The robot stack and the UI are **separate workspaces**. Start the robot or simulation first, then
the UI:

```bash
cd ~/openamrobot-ui/ros2
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 launch openamr_ui_bringup ui.launch.py
```

For map and route file operations, and route-following helpers:

```bash
ros2 launch openamr_ui_package physnode_launch.py
```

## Before enabling motion

!!! danger "Work through this every time, on real hardware"
    1. Turn **Demo Mode off**
    2. Confirm the correct **robot connection profile**
    3. Check the connection indicator is **green**
    4. Open **Health** and confirm the required topics are **fresh**
    5. Confirm the displayed **map and robot pose match the physical robot**
    6. Set **conservative speed limits** and clear the operating area
    7. **Test the physical emergency stop**

    Step 5 is the one people skip. A stale pose means the robot on screen is not the robot in the
    room, and every command you send is aimed somewhere else.

    Step 7 matters because the dashboard's E-STOP is software only. See
    [Overview](overview.md#the-e-stop-is-software-only).

## Verify it worked

- Dashboard opens on `5050`
- Connection indicator green
- Health page shows fresh topics
- Map renders and the robot pose moves when the robot moves

## If it did not work

| Symptom | First check |
|:--|:--|
| Page does not open | UI process and port `5050` |
| Page opens, connection red | Rosbridge process, configured host, port `9090` |
| Green, but map or pose frozen | Health page topic freshness. **Do not drive.** |
| Map alone blank | `/map`, `/ui/map`, and `map_volatile_relay` |
| Camera alone blank | Selected image topic, and port `8080` if used |
| Route or map buttons fail | Optional `physnode_launch.py` helpers not running |
| UI changes do not appear | Rebuild, sync, rebuild the ROS package, hard-refresh |

More in [Troubleshooting](troubleshooting.md).

## Next

[Tutorials](tutorials.md), or [Concepts](concepts.md) to understand what you just started.

---

**Build it:** [`openamrobot-ui`](https://github.com/openAMRobot/openamrobot-ui)
