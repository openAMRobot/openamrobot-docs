---
title: rc.1 architecture
tags: [developer, integrator]
status: experimental
description: Diagrams of the OpenAMRobot 2.0 rc.1 Digital Twin as it is implemented, the repositories and packages, and the simulation runtime with Gazebo, ros2_control, Nav2, MoveIt 2, RViz, software in the loop and virtual CAN.
---

# rc.1 architecture

**For:** developers who need to know which process does what in the running twin, and where its source lives.

**Canonical source:** `launch/build1.launch.py` and `config/command_map.yaml` of `openamrobot_build1_scene` in
[openamr-upperbody-sw](https://github.com/openAMRobot/openamr-upperbody-sw), and the package `openamrobot_sil` of
[openamr-platform-sw](https://github.com/openAMRobot/openamr-platform-sw), at the candidate commits. The diagrams are
drawn from those files. They show what rc.1 starts, not the target architecture; the target is on the
[Digital twin architecture](../architecture.md) page.

!!! warning "Simulation only"
    The hardwired safety chain (E-stops, contactors, brakes, charge inhibit) is not modelled. No box in these
    diagrams is a safety function.

## Status marks

Every element carries one of four marks.

| Mark | Meaning in rc.1 |
|---|---|
| supported | part of the supported profile and exercised by the qualification runs |
| experimental | present in the candidate, switched on by an argument, not part of the qualified default or still Proposed |
| planned | not in the candidate |
| hardware-dependent | exists only with physical hardware, which rc.1 does not cover |

## System overview

Which repository provides which part, and what the twin stands in for.

```mermaid
flowchart TB
  subgraph manifest["openamrobot-manifest"]
    boot["bootstrap_digital_twin.sh and the pinned profile<br/>(supported)"]
  end
  subgraph upper["openamr-upperbody-sw"]
    scene["openamrobot_build1_scene<br/>launch, world, scenarios, RViz file<br/>(supported)"]
    model["combined model: base, lift, two arms<br/>description, control, gazebo, moveit packages<br/>(supported)"]
    armemu["openamrobot_openarm_emulator<br/>arm motor emulators on CAN FD<br/>(supported)"]
  end
  subgraph platform["openamr-platform-sw"]
    basedesc["openamrobot_description<br/>mobile base model<br/>(supported)"]
    nav["openamrobot_nav2 and openamrobot_perception<br/>Nav2 launch files, scan body filter<br/>(supported)"]
    sil["openamrobot_sil<br/>drive, battery and lift emulators, host test client<br/>(supported)"]
    align["openamrobot_station_alignment<br/>(experimental)"]
    dock["openamrobot_docking<br/>dock model only, no docking node runs<br/>(planned)"]
  end
  subgraph ifc["openamrobot-interfaces"]
    msgs["shared messages<br/>(supported)"]
  end
  subgraph upstream["Enactic OpenArm, Apache-2.0"]
    oadesc["openarm_description<br/>(supported)"]
    oaros["openarm_ros2: openarm_hardware driver<br/>(supported)"]
    oacan["openarm_can<br/>(supported)"]
  end
  subgraph outside["Outside the supported profile"]
    ui["operator UI<br/>(planned)"]
    fw["firmware on the 2.0 controller<br/>(hardware-dependent)"]
    robot["physical robot, Jetson<br/>(hardware-dependent)"]
  end
  boot --> scene
  scene --> model
  scene --> armemu
  scene --> nav
  scene --> sil
  scene -.-> align
  model --> basedesc
  model --> oadesc
  armemu --> oaros
  oaros --> oacan
  nav --> msgs
  align --> msgs
  dock -.-> scene
```

Solid arrows mean "uses". Dotted arrows mean an optional or partial use: the station alignment is started only with
`station_alignment:=true`, and the docking package contributes its dock model to the world while no docking node
runs.

## Simulation runtime, profile `firmware_sil`

The default profile and the one the Baseline 1 mission runs in. Commands leave the robot software as they would on
the robot, cross a virtual CAN bus to an emulated device, and the emulator acts on the joint in Gazebo.

```mermaid
flowchart LR
  subgraph ui_layer["Viewer"]
    rviz["RViz with build1.rviz<br/>(supported, defects in issue 143)"]
  end
  subgraph apps["Robot software, root namespace"]
    nav2["Nav2: localization, planner, controller,<br/>behaviours, collision monitor<br/>(supported)"]
    scanf["scan_body_filter<br/>(supported)"]
    foot["footprint_publisher<br/>(supported)"]
    moveit["MoveIt 2: move_group,<br/>planning_scene_loader, joint_state_clamp<br/>(supported)"]
    salign["station alignment<br/>(experimental)"]
    cm["ros2_control controller manager<br/>arm, gripper and gravity controllers<br/>(supported)"]
    drv["upstream driver openarm_hardware<br/>(supported)"]
    gff["gravity_feedforward<br/>(experimental)"]
    jsp["joint_state_publisher and<br/>robot_state_publisher<br/>(supported)"]
    bsa["base_state_adapter<br/>(supported)"]
  end
  subgraph silbox["Software in the loop, openamrobot_sil"]
    host["host test client in the<br/>base controller slot<br/>(supported)"]
    renode["firmware image in Renode<br/>stm32:=renode_readonly<br/>(experimental)"]
    zlac["drive emulator<br/>(supported)"]
    bms["battery management emulator<br/>(supported)"]
    ctl["lift controller emulator<br/>(supported)"]
  end
  subgraph vcan["Virtual CAN"]
    vdrive(["vcan_drive, classic CAN"])
    vbms(["vcan_bms, classic CAN"])
    vaux(["vcan_aux, classic CAN"])
    varm(["vcan_arm_l and vcan_arm_r, CAN FD"])
  end
  subgraph plant["Plant, namespace sim"]
    simcm["controller manager in Gazebo<br/>arm motor emulators, joint state broadcaster<br/>(supported)"]
    wca["wheel_command_adapter<br/>(supported)"]
    gz["Gazebo Harmonic, DART<br/>world from scene.yaml<br/>(supported)"]
    bridge["ros_gz bridges: control and sensors<br/>(supported)"]
    rtf["rtf_monitor<br/>(supported)"]
  end
  nav2 -- "/cmd_vel" --> host
  host --> vdrive --> zlac
  renode -.-> vdrive
  zlac -- "/sil/drive/gz_cmd_vel" --> wca --> gz
  host --> vbms --> bms
  host --> vaux --> ctl --> gz
  moveit --> cm --> drv --> varm --> simcm --> gz
  gff --> cm
  salign -.-> nav2
  gz --> bridge
  bridge -- "/clock" --> nav2
  bridge -- "scan" --> scanf -- "/scan_filtered" --> nav2
  bridge --> rtf
  host -- "wheel speeds, lift state" --> bsa
  bsa -- "/odom and odom to base_footprint" --> nav2
  foot --> nav2
  jsp -- "/tf" --> moveit
  nav2 --> rviz
  moveit --> rviz
  jsp --> rviz
```

Reading notes, each taken from the launch file or the single-writer map of the scene:

- `/cmd_vel` has one writer, the Nav2 collision monitor. The docking nodes are not started because they would be a
  second writer.
- The lift has one command path in this profile: `/sil/lift/command` and `/sil/lift/permit` to the host test client,
  over `vcan_aux` to the lift controller emulator. MoveIt 2 does not move the lift here.
- The arm emulators emulate the CAN motor devices only. Gazebo owns the rigid-body dynamics of every joint.
- `/odom` and the transform from `odom` to `base_footprint` come from `base_state_adapter`, from wheel speeds read
  over CAN. The transform from `map` to `odom` comes from the Nav2 localization node.
- With `driver_clock:=sim` the real arm driver starts only after the first `/clock` message.
- A virtual CAN bus has no bit rate, no arbitration, no error frames and no bus-off.

## Simulation runtime, profiles `fast` and `fine`

No devices and no virtual CAN. The controllers act on Gazebo directly.

```mermaid
flowchart LR
  nav2f["Nav2<br/>(supported)"]
  moveitf["MoveIt 2<br/>(supported)"]
  cmf["gz_ros2_control controller manager<br/>arm, gripper and lift controllers<br/>(supported)"]
  dd["DiffDrive plugin of the base<br/>(supported)"]
  gzf["Gazebo Harmonic, DART<br/>(supported)"]
  bridgef["ros_gz control bridge<br/>(supported)"]
  fmf["finger_mimic_follower<br/>(supported)"]
  rvizf["RViz<br/>(supported, defects in issue 143)"]
  nav2f -- "/cmd_vel" --> bridgef --> dd --> gzf
  moveitf --> cmf --> gzf
  fmf --> gzf
  gzf --> bridgef
  bridgef -- "/clock, /odom, odom to base_footprint" --> nav2f
  nav2f --> rvizf
  moveitf --> rvizf
```

In these profiles the grippers do not move with the default DART engine; see
[Launch profiles and arguments](launch.md#physics-engines).

## What is not in the diagrams

- The hardwired safety chain, hub motor holding brakes, battery behaviour, motor current and heat, sensor noise and
  the CAN physical layer are not modelled.
- Isaac Sim, MuJoCo, LeRobot and AI policies are not part of rc.1.
- The host link between the base controller and the computer is not modelled: the host test client talks ROS
  directly.

The complete list is in
[`docs/build1_scene.md`](https://github.com/openAMRobot/openamr-upperbody-sw/blob/1ab45a62957d238fc293eee08a8fd9158acebb01/docs/build1_scene.md)
of openamr-upperbody-sw.
