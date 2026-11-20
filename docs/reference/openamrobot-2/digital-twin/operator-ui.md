---
title: Operator UI and Control Room
tags: [developer, integrator, operator]
status: experimental
description: How to watch the OpenAMRobot 2.0 digital twin in the read-only Control Room, and when the browser operator UI may be connected to it.
---

# Operator UI and Control Room

**For:** engineers and operators who want to watch the twin, and anyone about to connect the browser UI to it.

**Canonical source:** [`docs/demo/control_room.md`](https://github.com/openAMRobot/openamr-upperbody-sw/blob/d39a648/docs/demo/control_room.md)
in openamr-upperbody-sw (pull request [#84](https://github.com/openAMRobot/openamr-upperbody-sw/pull/84), open) and
[openamrobot-ui](https://github.com/openAMRobot/openamrobot-ui).

!!! warning "Simulation, not hardware validation"
    The Control Room and the UI show simulation data. A Stop button in the UI is a functional software stop, never a
    safety function.

## Control Room

The Control Room is a read-only engineering monitor. It publishes nothing outside `/control_room/`, sends no action
goal, calls no service and writes no parameter. It shows the same run three ways: live next to the running mission,
as a replay of the run's recording on its own simulation time, and as an offline HTML report.

What it shows: the scene in RViz and Lichtblick, mission phases, which component is an emulator, a host stand-in, the
real driver or Gazebo physics, the writers of the command topics (with a warning when `/cmd_vel` has a writer other
than `collision_monitor`), localization and station error against ground truth, MoveIt trajectories, lift position,
contacts, real-time factor, and every virtual CAN bus with frame rates and decoded signals.

**Desktop.** Build and start it next to a running scene (from the twin workspace of
[Install and run](install-and-run.md), with the #84 branch checked out in place of the pinned upperbody commit,
because the Control Room package is not on the integration branch yet):

```bash
colcon build --symlink-install --packages-up-to openamrobot_control_room openamrobot_build1_scene
source install/setup.bash
ros2 launch openamrobot_control_room control_room.launch.py
```

Replay and the offline report: `replay.launch.py` and `mission_report.py`, described in `control_room.md`. Status:
not checked on a desktop for the release candidate (step 5 of the
[desktop acceptance checklist](install-and-run.md#desktop-acceptance-checklist)).

## Operator UI

openamrobot-ui is the browser interface of the robot. It shows robot state, the map and mission status, and has
driving and Stop controls.

**Do not connect `main` of openamrobot-ui to the twin for driving.** On `main` the UI publishes `geometry_msgs/Twist`
directly on `/cmd_vel`. That goes around `velocity_smoother`, `collision_monitor` and, once it exists, the stop gate,
so it is the one path in the twin with no limits.

The authorised path needs two changes together:

| Change | What it does | State |
|---|---|---|
| openamrobot-ui [#50](https://github.com/openAMRobot/openamrobot-ui/pull/50) | the UI publishes `TwistStamped` on `/ui/cmd_vel` and binds the Stop button to `/safety/stop_lock` | open, draft |
| openamr-platform-sw [#90](https://github.com/openAMRobot/openamr-platform-sw/pull/90) | relays `/ui/cmd_vel` into the manual input of `twist_mux`, then stop gate, smoother and collision monitor | open, two-person review |

They ship together or not at all. Until both are adopted into the twin, the UI may be used only for monitoring views,
with manual driving unused, and the release candidate reports the UI command path as BLOCKED.

### Twin operator profile (simulation evidence, not yet merged)

openamrobot-ui [#62](https://github.com/openAMRobot/openamrobot-ui/pull/62) (open, draft, stacked on #50) adds a twin
launch profile (`twin.launch.py`) and a read-only status panel. The browser reaches the twin through a restricted
rosbridge bound to 127.0.0.1: it may read an explicit list of topics, write only `/goal_pose`, call the stop lock
services and the cancel services, and send no action goal. `/ui/cmd_vel` is writable only with `manual_drive:=true`
(default false). Full interface inventory and the desktop acceptance script: `docs/digital_twin.md` on #62.

Headless run on the twin with the #90 stack ([44806541459](https://github.com/openAMRobot/openamrobot-ui/actions/runs/44806541459), success):

- graph: `/cmd_vel` has `collision_monitor` as its only publisher; `/ui/cmd_vel` has none;
- bridge probe 11 of 11 as expected: publishing on `/cmd_vel`, `/ui/cmd_vel` and `/initialpose`, parameter and
  lifecycle changes, action goals and non-loopback connections are refused;
- browser 8 of 8: bundle check, live status, map and pose, Resume through the gate, a UI goal then Cancel ending
  CANCELED, Stop (software) during a goal locks and cancels it, mission status labelled Proposed, STALE and
  DISCONNECTED states.

This shows the authorised chain working on the twin with unmerged code (#90, #50, #62). It is not rc.1 content and
not safety evidence.

Acceptance check for the command path on a desktop: `ros2 topic info /cmd_vel --verbose` shows only
`collision_monitor` as publisher, and the UI's Stop locks the base within 0.5 s.

## Next step

[Scenarios](scenarios.md).
