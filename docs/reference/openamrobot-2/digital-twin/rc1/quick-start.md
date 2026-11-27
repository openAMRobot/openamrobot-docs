---
title: Quick start
tags: [developer, integrator]
status: experimental
description: Install the OpenAMRobot 2.0 rc.1 Digital Twin, launch it, check that it is ready, run the drive demonstration and stop it.
---

# Quick start

**For:** developers who want the first verified result from the rc.1 Digital Twin.

**Canonical source:** the bootstrap script of
[openamrobot-manifest](https://github.com/openAMRobot/openamrobot-manifest) and the README of the package
`openamrobot_build1_scene` in [openamr-upperbody-sw](https://github.com/openAMRobot/openamr-upperbody-sw).

!!! warning "Simulation only"
    A passing demonstration shows that the software and the model agree with each other. It is not hardware,
    physical acceptance or safety evidence.

## 1. What you will achieve

The whole OpenAMRobot 2.0 model (mobile base, lift, two arms) stands in a Gazebo world with shelves. Nav2 and
MoveIt 2 run on top. You start it, confirm that it is ready, and let a scripted scenario drive the base 2 m forward
and turn it 90 degrees. The scenario ends with PASS, FAIL or BLOCKED and a JSON log.

This page uses the run profile `fast`: physics and controllers only, no emulated devices and no virtual CAN. It is
the profile the clean-install check in CI starts.

## 2. What you need

- A machine that matches the [tested environment](requirements.md): Ubuntu 24.04 on x86_64.
- `sudo` rights and network access for the installation.
- Two terminals. They are called Terminal 1 and Terminal 2 on all pages of this section.

## 3. Install

```bash
sudo apt-get update && sudo apt-get install -y git
git clone https://github.com/openAMRobot/openamrobot-manifest.git
git -C openamrobot-manifest checkout c567f178a56c9e7c739617e2350e17ba125a5283
bash openamrobot-manifest/tools/bootstrap_digital_twin.sh "$HOME/oamr_dt_ws"
```

The release is not published yet. The `git checkout` line selects the version of the installer that installs exactly
the software this page describes; at publication it is replaced by the release tag. The [Installation](installation.md#install-with-the-bootstrap-script) page explains it and every step.

## 4. Launch

**Terminal 1.** Set the environment, then start the twin with RViz:

```bash
source /opt/ros/jazzy/setup.bash
source $HOME/oamr_dt_ws/install/setup.bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI='<CycloneDDS><Domain Id="any"><Discovery><MaxAutoParticipantIndex>120</MaxAutoParticipantIndex></Discovery></Domain></CycloneDDS>'
```

```bash
ros2 launch openamrobot_build1_scene build1.launch.py profile:=fast rviz:=true
```

Leave Terminal 1 running.

!!! warning "This launch is for driving only"
    With `profile:=fast` and the default engine, run `scn01_drive` and nothing with the arms. `scn03_arms_reach`
    fails in this launch with `left_park_joints_not_moved`, and the grippers do not move. That is a known limit of the
    physics engine in this profile, not a fault of your installation. For arms and grippers, stop this launch and
    start the one in [Grasp](demonstrations.md#4-grasp), which selects the engine the left-arm grasp is qualified with. No other arm motion is qualified in `fast`.

### What you should see

- A Gazebo window with the robot at the origin of a floor with shelf units, a tote, an item and a dock model.
- An RViz window with the robot model, the map, the laser scan and the planning scene. Details:
  [RViz guide](rviz.md).
- In Terminal 1, a line that starts with `Build 1 scene:` (the project's internal name of this simulated scene) followed by the run identity as JSON (profile, physics
  step, physics engine), and one line that starts with `KNOWN LIMIT:`. With the default DART engine it says that the
  grippers do not move in the `fast` and `fine` profiles. That is expected and does not affect the drive.

Without a display, add `headless:=true` and leave out `rviz:=true`. That is the form CI uses.

### Check that it is ready { #4-check-that-it-is-ready }

The clean-install check in CI treats the twin as ready when three things hold within 300 s of the launch: `/clock`
advances (more than 20 messages spanning more than 5 s of simulation time), `/robot_description` is published, and
the TF tree contains `base_link`. In an automated test on a fresh machine it saw a robot description of about 100000 characters
and 69 TF frames.

**Terminal 2.** Set the same environment as in Terminal 1:

```bash
source /opt/ros/jazzy/setup.bash
source $HOME/oamr_dt_ws/install/setup.bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI='<CycloneDDS><Domain Id="any"><Discovery><MaxAutoParticipantIndex>120</MaxAutoParticipantIndex></Discovery></Domain></CycloneDDS>'
```

Then check by hand:

```bash
ros2 topic info /clock -v
```

One publisher must be listed. If the publisher count is 0, the simulator or its bridge did not start.

```bash
ros2 topic echo --once /odom
```

One odometry message must print.

```bash
ros2 run tf2_ros tf2_echo base_footprint lift_carriage_link
```

A transform must print repeatedly; stop it with Ctrl+C. In RViz the robot model is drawn only when
`/robot_description` and TF are present, so a complete robot in RViz is the visual form of the same check.

You do not have to wait by hand before the next step: the scenario runner waits for the stack itself and names what
is missing if it gives up.

## 5. First demonstration: drive

**Terminal 2:**

```bash
ros2 run openamrobot_build1_scene run_scenario.py scn01_drive
```

The scenario sends a Nav2 goal 2 m ahead, waits until the base has stopped, then asks Nav2 to spin 90 degrees. It
compares odometry with the simulator's ground truth. In RViz and Gazebo the robot drives forward and turns on the
spot.

| Exit code | Meaning |
|---|---|
| 0 | PASS: the drive ended between 1.85 m and 2.15 m of ground truth distance and the turn between 78 and 102 degrees, with odometry inside its guard values |
| 1 | FAIL: a check failed. The log names it |
| 2 | the scenario name is unknown |
| 3 | BLOCKED: not used by this scenario. Only `scn05_bus_loss` can end BLOCKED. BLOCKED is not PASS |

The log is `build1_logs/scn01_drive.json` in the directory where you ran the command. Print the exit code with
`echo $?` straight after the command.

In the automated installation test this scenario ended with exit code 0 on both fresh machines, with the software
this page installs. No duration is quoted here: the CI step
that contains it also contains the start-up wait, and took between 3 and 4 minutes in total on a hosted runner.

## 6. Second demonstration: lift

The same launch stays open. **Terminal 2:**

```bash
ros2 run openamrobot_build1_scene run_scenario.py scn16_lift_stops
```

The lift carriage travels to its stops (0.350 m, 0.0 m, 0.175 m, 0.350 m, 0.0 m). Exit code 0 means that every stop
was reached within 0.003 m and the controller never reported success before arrival. The clean-install check in CI
runs this scenario in the same launch, after the drive.

For arms and grippers, stop this launch first and follow [Grasp](demonstrations.md#4-grasp).

## 7. Stop

**Terminal 1:** press Ctrl+C once and wait until the prompt returns. The launch stops the Gazebo server through its
own helper.

Two things can look like errors and are known:

- `rviz2` can report a non-zero exit when the launch is closed
  ([openamr-upperbody-sw issue 143](https://github.com/openAMRobot/openamr-upperbody-sw/issues/143)).
- The Gazebo server and the ROS bridge can crash or hang during teardown. The two notes in
  [`docs/issues/`](https://github.com/openAMRobot/openamr-upperbody-sw/tree/6687f65b8bd03f83ef6c38a7ddaf47eb3bfd18ac/docs/issues)
  of openamr-upperbody-sw describe them.

If a process is left over, see [Troubleshooting, shutdown](troubleshooting.md#shutdown). Do not end processes by a
broad name pattern on a machine that runs anything else.

## 8. Where next

- [Demonstrations](demonstrations.md): lift, arms, grasp and the full Baseline 1 mission.
- [Launch profiles and arguments](launch.md): the device profile `firmware_sil` with virtual CAN.
- [Capability and maturity](capabilities.md): what each part of the twin is qualified for.
