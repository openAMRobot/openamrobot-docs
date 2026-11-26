---
title: rc.1 troubleshooting
tags: [developer, integrator]
status: experimental
description: Symptoms, likely causes, diagnostic commands and fixes for installing and running the OpenAMRobot 2.0 rc.1 Digital Twin.
---

# rc.1 troubleshooting

**For:** developers whose installation or launch of the rc.1 Digital Twin did not behave as the other pages describe.

**Canonical source:** the bootstrap script of
[openamrobot-manifest](https://github.com/openAMRobot/openamrobot-manifest), the launch file, the scripts and the CI
workflows of [openamr-upperbody-sw](https://github.com/openAMRobot/openamr-upperbody-sw). Every command below is
taken from those sources.

Each entry has the same five parts: symptom, likely cause, check, fix, and when to report. Report through the issue
tracker of the repository named in the entry; [Release information](release.md#contribute-and-report-issues) lists
what a report needs.

Unless an entry says otherwise, run the commands in a terminal with the four environment lines of the
[installation](installation.md#6-environment-of-every-new-terminal).

## Installation

### Wrong ROS distribution

- **Symptom:** the bootstrap script fails in step 1, or `source /opt/ros/jazzy/setup.bash` reports that the file does
  not exist, or packages named `ros-jazzy-...` cannot be found.
- **Likely cause:** the machine is not Ubuntu 24.04 (noble), or another ROS 2 distribution is installed and sourced.
  Only ROS 2 Jazzy on Ubuntu 24.04 is supported.
- **Check:** list the installed ROS and simulator packages, as the acceptance workflow does:

    ```bash
    dpkg-query -W -f='${Package} ${Version}\n' \
      | grep -E '^(ros-jazzy-(ros-base|rclcpp|ros-gz|gz-|ros2-control|controller-manager|hardware-interface|joint-trajectory-controller|xacro|moveit|navigation2|nav2-bringup|rmw-cyclonedds|cyclonedds)|python3-can)' \
      | sort
    ```

    An empty list means ROS 2 Jazzy is not installed.
- **Fix:** use an Ubuntu 24.04 x86_64 machine and run the bootstrap script. Do not source a second ROS distribution
  in the same terminal.
- **Report when:** the script fails in step 1 on a clean Ubuntu 24.04 x86_64 machine. Repository: openamrobot-manifest.

### Wrong Gazebo version

- **Symptom:** the launch starts but the simulator behaves differently from this documentation, or Gazebo packages
  changed after a system upgrade.
- **Likely cause:** the three pinned Gazebo vendor packages were replaced or were never pinned.
- **Check:**

    ```bash
    gz sim --versions
    ```

    The acceptance workflow expects `8.15.0`. `gz sdf --versions` must print `14.9.0`.
- **Fix:** run the bootstrap script again. Its step 2 reinstalls the pinned builds with `--allow-downgrades` and holds
  them with `apt-mark hold`.
- **Report when:** the pinned builds are no longer available from the package server. Repository: openamrobot-manifest.

### Missing dependencies

- **Symptom:** `colcon build` stops on a package that cannot be found, or the launch stops with a missing package or
  Python module.
- **Likely cause:** step 4 of the installation did not finish, for example after a network error.
- **Check:** from the workspace root, the dependency step of the script prints what it cannot resolve:

    ```bash
    paths=$(colcon list --base-paths src --packages-up-to openamrobot_build1_scene openamrobot_station_alignment --paths-only)
    rosdep install --rosdistro jazzy --from-paths $paths --ignore-src -y -r
    ```

- **Fix:** run the bootstrap script again; it is idempotent. Then rebuild (step 5).
- **Report when:** a dependency is still unresolved after a complete second run. Repository: openamrobot-manifest.

## Workspace

### Duplicate packages

- **Symptom:** `colcon` reports two packages with the same name, typically `openamr_ui_msgs`.
- **Likely cause:** the workspace also contains the operator UI repository, or it was made from the full source
  inventory `releases/v2.0.0-rc.1.repos`. `openamr_ui_msgs` is provided by both openamrobot-interfaces and
  openamrobot-ui. The full inventory is not a buildable workspace.
- **Check:** from the root of the openamrobot-manifest checkout:

    ```bash
    python3 tools/check_profile.py releases/v2.0.0-rc.1-digital-twin.repos --release releases/v2.0.0-rc.1.repos --workspace "$HOME/oamr_dt_ws"
    ```

    It fails and names the package when two `package.xml` files provide the same ROS package name.
- **Fix:** use a new, empty workspace and import only `releases/v2.0.0-rc.1-digital-twin.repos`. The operator UI is
  not part of the rc.1 Digital Twin.
- **Report when:** the check fails on a workspace that holds only the six repositories of the profile. Repository:
  openamrobot-manifest.

### Workspace not sourced

- **Symptom:** `ros2 launch` or `ros2 run` reports that the package `openamrobot_build1_scene` is not found.
- **Likely cause:** the terminal is new and the workspace is not sourced, or the build did not finish.
- **Check:** confirm that `$HOME/oamr_dt_ws/install/setup.bash` exists. If it does not, the build did not finish.
- **Fix:**

    ```bash
    source /opt/ros/jazzy/setup.bash
    source $HOME/oamr_dt_ws/install/setup.bash
    ```

    Set the two `export` lines of the installation as well.
- **Report when:** not a defect; no report needed.

## Launch

### Virtual CAN: the launch prints BLOCKED

- **Symptom:** the launch prints a line starting with `BLOCKED:` that names missing virtual CAN interfaces or a
  wrong MTU, and stops. It ends with `Create them with: ros2 run openamrobot_build1_scene setup_vcan_all.sh`.
- **Likely cause:** the default profile `firmware_sil` needs five virtual CAN interfaces and they could not be
  created: the `vcan` kernel module is missing, or there is no root or passwordless sudo.
- **Check:**

    ```bash
    ros2 run openamrobot_build1_scene setup_vcan_all.sh
    ```

    It prints the reason after `BLOCKED:`, or one line per interface with its MTU. To see the existing interfaces:

    ```bash
    ip -details link show type vcan
    ```

    The arm buses `vcan_arm_l` and `vcan_arm_r` must show MTU 72 (CAN FD), the three base buses MTU 16.
- **Fix:** install the kernel module package named by the script (on Ubuntu `linux-modules-extra-$(uname -r)`) and
  run `sudo -v` in the same terminal before the script (it calls `sudo` without asking for a password; do not use
  `sudo ros2 run`). On a machine where virtual CAN cannot be had, use `profile:=fast` or
  `profile:=fine`.
- **Report when:** the script ends with exit code 0 and the launch still prints `BLOCKED`. Repository:
  openamr-upperbody-sw.

### No /clock

- **Symptom:** the launch prints `BLOCKED (sim infrastructure): no /clock within 60 s of the launch start; the real
  arm driver was not started` and stops; or a scenario fails with "Gazebo did not start: no /clock or no ground truth".
- **Likely cause:** either Gazebo did not come up, or it started and then stopped stepping. The second case is a
  known intermittent start-up defect ([openamr-upperbody-sw issue 135](https://github.com/openAMRobot/openamr-upperbody-sw/issues/135)):
  the simulator publishes a few milliseconds of `/clock` and freezes, so a check that starts later sees no message.
  Its cause is not known. It happened in 2 of 14 mission start-ups during qualification. A leftover process of an
  earlier launch can also cause a missing clock.
- **Check:**

    ```bash
    ros2 topic info /clock -v
    ```

    A publisher count of 0 means Gazebo or the bridge is not up. A publisher with no new messages
    (`ros2 topic echo /clock --once` does not return) means the simulation froze. Then look for a simulator left from an earlier launch:

    ```bash
    pgrep -af "gz sim"
    ```

- **Fix:** stop the launch with Ctrl+C, make sure no earlier simulator is running (see [Shutdown](#shutdown)), and
  start again. A BLOCKED start is not a result; repeat it.
- **Report when:** three starts in a row end with `no /clock`, or it happens in the `fast` profile. Add the launch
  log to issue 135 of openamr-upperbody-sw.

### Missing TF

- **Symptom:** RViz reports that the fixed frame `map` does not exist, or a transform lookup fails.
- **Likely cause:** `map` is published only when Nav2 runs. Other frames are missing only when the state publishers
  or the odometry source did not start.
- **Check:** in **Terminal 2**:

    ```bash
    ros2 run tf2_ros tf2_echo base_footprint lift_carriage_link
    ```

    This must print a transform in every profile. Then check the odometry source:

    ```bash
    ros2 topic echo --once /odom
    ```

- **Fix:** if only `map` is missing, start the launch with `nav2:=true` (the default) and `sensors:=true`. If the
  model frames are missing, read the first error in Terminal 1; the launch stops as a whole when a required process
  fails.
- **Report when:** `map` is missing with Nav2 running for more than a few minutes of simulation time. Repository:
  openamr-upperbody-sw.

### Empty RViz displays

- **Symptom:** RViz opens but some displays show nothing or an error.
- **Likely cause:** the display needs a component that the launch arguments switched off, or it is off in the saved
  file. The "Ground truth" display is off on purpose.
- **Check:** compare the display with the "Needs" column of the [RViz guide](rviz.md#displays). To see which nodes
  run:

    ```bash
    ros2 node list
    ```

- **Fix:** start the launch with `nav2:=true` and `moveit:=true` (the defaults) for the full picture, and
  `extra_sensors:=true` for the camera displays. Tick the display's checkbox if it is off in the file.
- **Report when:** a display stays empty with the full stack running and it is not one of the three defects of
  [issue 143](https://github.com/openAMRobot/openamr-upperbody-sw/issues/143). Repository: openamr-upperbody-sw.

### Controllers not active

- **Symptom:** a scenario fails with "not ready after ... of Gazebo time" and names arm joint states or a controller.
- **Likely cause:** the controller manager did not load or activate a controller, often on a slow start.
- **Check:**

    ```bash
    ros2 service call /controller_manager/list_controllers controller_manager_msgs/srv/ListControllers
    ```

    In `fast` and `fine` the joint state broadcaster, both arm controllers, both gripper controllers and the lift
    controller must be `active`.
- **Fix:** restart the launch. Close other heavy programs if the real-time factor is very low.
- **Report when:** the same controller stays inactive on repeated starts. Repository: openamr-upperbody-sw.

## Middleware

### DDS configuration

- **Symptom:** nodes in the same launch do not see each other: a scenario waits for a topic that another terminal
  can see, or late-started nodes never connect.
- **Likely cause:** the terminal does not use CycloneDDS, or `CYCLONEDDS_URI` is not set. The Build 1 launch has
  many participants; at the default CycloneDDS limit late participants did not match in the project's benchmark, so
  CI raises `MaxAutoParticipantIndex` to 120. Terminal 1 and Terminal 2 must use the same settings. Fast DDS is not
  the acceptance middleware ([openamr-platform-sw issue 197](https://github.com/openAMRobot/openamr-platform-sw/issues/197)).
- **Check:** print the middleware that ROS loads in this terminal, as the acceptance workflow does:

    ```bash
    python3 -c "from rclpy.utilities import get_rmw_implementation_identifier as g; print(g())"
    ```

    It must print `rmw_cyclonedds_cpp`.
- **Fix:** in every terminal:

    ```bash
    export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
    export CYCLONEDDS_URI='<CycloneDDS><Domain Id="any"><Discovery><MaxAutoParticipantIndex>120</MaxAutoParticipantIndex></Discovery></Domain></CycloneDDS>'
    ```

    Then restart the launch. If the ROS daemon was started with other settings, stop it with `ros2 daemon stop`.
- **Report when:** discovery fails with both variables set in all terminals. Repository: openamr-upperbody-sw.

## Demonstrations

### Navigation goal failure

- **Symptom:** `scn01_drive` ends with exit code 1 and the log says that `navigate_to_pose` or the spin ended with a
  status other than success; or a goal you sent yourself is aborted.
- **Likely cause:** Nav2 was not ready or lost its inputs; or you hit a known limitation: a cancelled and resumed
  goal can end ABORTED ([openamr-platform-sw issue 207](https://github.com/openAMRobot/openamr-platform-sw/issues/207)),
  an operator cancel can report ABORTED instead of CANCELED
  ([issue 189](https://github.com/openAMRobot/openamr-platform-sw/issues/189)), and the station approach can stop
  short ([issue 201](https://github.com/openAMRobot/openamr-platform-sw/issues/201)). With the Bullet Featherstone
  engine the base does not turn.
- **Check:** open `build1_logs/scn01_drive.json` and read the `failures` entry and the recorded run profile and
  engine. Confirm that the robot was at its spawn station and that odometry arrives:

    ```bash
    ros2 topic echo --once /odom
    ```

- **Fix:** start a fresh launch with the default DART engine and run the scenario once, before anything else moved
  the robot. Do not rely on cancel and resume in rc.1.
- **Report when:** the plain drive scenario fails on a fresh `fast` launch. Attach the JSON log and the launch
  output. Repository: openamr-upperbody-sw.

### A scenario ends BLOCKED

- **Symptom:** `run_scenario.py` ends with exit code 3.
- **Likely cause:** only `scn05_bus_loss` ends with exit code 3: the emulated lift controller faulted because the
  machine ran below a real-time factor of 0.55 while the lift moved. A missing prerequisite (a device scenario on a
  launch without devices, a stack that is not ready) ends with exit code 1, FAIL.
- **Check:** the `reason` entry of the scenario's JSON log names the cause and the measured real-time factor.
- **Fix:** start the launch with the profile the scenario needs ([Demonstrations](demonstrations.md)). For the lift
  on a slow machine use `scn16_lift_stops` in the `fast` profile.
- **Report when:** BLOCKED is not a defect of the twin by itself. Report it when the stated prerequisite was in fact
  present. Repository: openamr-upperbody-sw.

## Shutdown

- **Symptom:** after Ctrl+C in Terminal 1, `rviz2` reports a non-zero exit, or the Gazebo server or a bridge prints
  a crash, or a process stays alive and the next launch behaves oddly.
- **Likely cause:** known teardown defects: the `rviz2` exit is defect 2 of
  [issue 143](https://github.com/openAMRobot/openamr-upperbody-sw/issues/143); the simulator and bridge teardown
  notes are in [`docs/issues/`](https://github.com/openAMRobot/openamr-upperbody-sw/tree/1ab45a62957d238fc293eee08a8fd9158acebb01/docs/issues)
  of openamr-upperbody-sw. Processes seen to outlive a launch in CI include the simulator, the Nav2 controller server
  and a bridge.
- **Check:**

    ```bash
    pgrep -af "gz sim"
    ```

    It lists each remaining simulator process with its process ID and command line.
- **Fix:** press Ctrl+C once and wait; the launch stops the simulator through its own helper. If a process from your
  launch is still listed, end that one process by the ID that the check printed. Do not end processes by a name
  pattern: on a shared machine, or on a machine connected to a robot, a pattern can match processes that are not
  yours. CI uses name patterns only because a hosted runner is a single-use machine.

    To remove the virtual CAN interfaces after the last run:

    ```bash
    ros2 run openamrobot_build1_scene setup_vcan_all.sh --delete
    ```

- **Report when:** a process cannot be stopped with Ctrl+C on repeated runs and is not covered by the notes above.
  Repository: openamr-upperbody-sw.
