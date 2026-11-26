---
title: Architecture diagrams
tags: [developer, integrator]
status: experimental
description: Engineering diagrams of the OpenAMRobot 2.0 rc.1 Digital Twin, drawn from the source at the release commits. System, base command path, virtual CAN, firmware boundary and mission sequence.
---

# Architecture diagrams

**For:** engineers who want the structure before the text.

Every name in these diagrams is a name in the source at platform commit `2ac4070` and upperbody commit `6687f65`. The diagrams describe the default device profile `firmware_sil` unless stated. They are written in Mermaid, so the source is this page.

**Legend, used in all diagrams**

| Style | Meaning |
|---|---|
| Solid box | Runs in rc.1 |
| Dashed box | Optional in rc.1, off by default |
| Dotted box, grey | Not in rc.1 |

## 1. System overview

```mermaid
flowchart TB
  user["User: launch, scenario runner, RViz"]
  subgraph app["Mission and scenarios"]
    scen["openamrobot_build1_scene<br/>scenarios and Baseline 1 mission"]
  end
  subgraph nav["Navigation (native ROS 2)"]
    nav2["Nav2 servers, amcl"]
    arb["twist_mux, safety_stop_gate_node,<br/>velocity_smoother, collision_monitor"]
  end
  subgraph man["Manipulation (native ROS 2)"]
    moveit["MoveIt 2 move_group"]
    cm["controller_manager<br/>OpenArmHW driver (upstream, unmodified)"]
  end
  subgraph dev["Device layer on virtual CAN"]
    host["sil_stm32_host_client<br/>stand-in for the base controller"]
    zlac["sil_zlac8015d<br/>motor driver emulator"]
    ctl["ctl017_emulator<br/>lift controller emulator"]
    bms["daly_bms_emulator"]
    arme["OpenArmCanEmulator<br/>arm and gripper motors"]
  end
  subgraph gz["Gazebo Harmonic"]
    phys["Physics: wheels, lift, arms, contact"]
    sens["Sensors: LiDAR, IMU, cameras, ToF, ultrasonic"]
    gt["Ground truth"]
  end
  renode["Renode: read-only telemetry image"]
  out["Operator UI, perception, AI policies,<br/>Isaac Sim, MuJoCo, physical robot"]

  user --> scen
  scen --> nav2
  scen --> moveit
  nav2 --> arb --> host
  host <-->|vcan_drive| zlac
  host <-->|vcan_aux| ctl
  host <-->|vcan_bms| bms
  moveit --> cm
  cm <-->|vcan_arm_l, vcan_arm_r| arme
  zlac --> phys
  ctl --> phys
  arme --> phys
  phys --> sens
  sens --> nav2
  phys --> gt
  gt -.->|mission planning pose,<br/>item pose, test checks| scen
  renode -.->|reads vcan_drive| zlac

  classDef optional stroke-dasharray: 6 4;
  classDef absent stroke-dasharray: 2 3,fill:#eeeeee,color:#555555;
  class renode optional;
  class out absent;
```

The dashed arrow from ground truth matters: the whole-robot mission plans from the simulator's pose and knows the item pose from the simulator. See [Known issues and limitations](limitations.md).

## 2. Mobile base: command and feedback sequence

```mermaid
sequenceDiagram
  participant N as Nav2 controller_server
  participant A as twist_mux, stop gate,<br/>smoother, collision_monitor
  participant H as sil_stm32_host_client<br/>(stand-in)
  participant Z as sil_zlac8015d<br/>(driver emulator)
  participant W as wheel_command_adapter
  participant G as Gazebo wheel joints
  participant O as base_state_adapter
  N->>A: cmd_vel_nav
  A->>H: /cmd_vel (collision_monitor is the only writer)
  H->>Z: CANopen 60FFh target velocity, on vcan_drive
  Z->>W: /sil/drive/gz_cmd_vel
  W->>G: left and right wheel joint speed
  G-->>Z: /sil/gz/joint_states, 100 Hz
  Z-->>H: CANopen 606Ch measured velocity, 0.1 r/min
  H-->>O: /sil/base/odom
  O-->>N: /odom and TF odom to base_footprint
  Note over H,Z: twist to wheel speed and back use radius 0.098 m<br/>and effective track 0.411 m (simulation calibration)
  Note over O: raw wheel odometry, no sensor fusion
```

## 3. Virtual CAN buses and device emulators

```mermaid
flowchart LR
  subgraph ros["ROS 2 side (host processes)"]
    host["sil_stm32_host_client"]
    drv["OpenArmHW in controller_manager"]
  end
  subgraph bus["Linux SocketCAN, virtual"]
    b1(["vcan_drive<br/>classic CAN, CANopen"])
    b2(["vcan_aux<br/>classic CAN"])
    b3(["vcan_bms<br/>classic CAN"])
    b4(["vcan_arm_l<br/>CAN FD"])
    b5(["vcan_arm_r<br/>CAN FD"])
  end
  subgraph emu["Device emulators (host processes)"]
    z["ZLAC8015D emulator, node 1<br/>link-loss reaction 250 ms"]
    c["CTL-017 emulator, node 0x10<br/>permit freshness 200 ms"]
    m["Daly BMS emulator, static values"]
    al["Left arm and gripper motors"]
    ar["Right arm and gripper motors"]
  end
  gz["Gazebo joints"]
  host --- b1 --- z
  host --- b2 --- c
  host --- b3 --- m
  drv --- b4 --- al
  drv --- b5 --- ar
  z --> gz
  c --> gz
  al --> gz
  ar --> gz
```

A virtual bus carries frames only. Bit timing, arbitration, error frames and bus-off do not exist on it and are not tested.

## 4. Firmware and Renode boundary

```mermaid
flowchart TB
  subgraph d["Default in rc.1"]
    s["Base controller slot:<br/>Python stand-in, no firmware logic"]
  end
  subgraph o["Optional in rc.1: stm32:=renode_readonly"]
    r["Renode, STM32H743 platform with additions"]
    t["Telemetry image built from the firmware repository<br/>reads 606Ch, 6041h, 603Fh. Commands nothing"]
    r --- t
  end
  subgraph n["Not in rc.1"]
    f["Base controller firmware commanding the drive"]
    l["Lift controller firmware"]
    h["Hardware in the loop"]
    p["Physical controller board"]
  end
  s -->|commands and reads| bus(["vcan_drive"])
  t -.->|reads only| bus
  classDef optional stroke-dasharray: 6 4;
  classDef absent stroke-dasharray: 2 3,fill:#eeeeee,color:#555555;
  class r,t optional;
  class f,l,h,p absent;
```

The Renode path is tested in the platform SIL workflow. The scene tests and the mission run with the stand-in.

## 5. Whole-robot mission sequence

One leg of the Baseline 1 mission. A strict dispatch runs two legs. Phase names are those of the mission definition.

```mermaid
flowchart LR
  p1["spawn<br/>settle at origin"] --> p2["nav_to_station<br/>Nav2 drive, station alignment<br/>odometry within 0.10 m"]
  p2 --> p3["stop_authorize<br/>base stopped,<br/>lift refused without permit"]
  p3 --> p4["lift_to_target<br/>within 0.006 m"]
  p4 --> p5["arm_approach"]
  p5 --> p6["grasp<br/>contact evidence"]
  p6 --> p7["lift_object<br/>lift 0.08 m, hold"]
  p7 --> p8["retreat<br/>park arms, turn, leave,<br/>cancelled goal stops"]
```

Base, lift and arm act one after the other in this mission. Nothing in rc.1 qualifies coordinated motion of base and arms.

Acceptance values per phase: [Scenario catalog](scenarios.md#baseline-1-whole-robot-mission).

## 6. Manipulation and lift control

```mermaid
flowchart TB
  subgraph plan["Planning (native)"]
    mg["MoveIt 2 move_group<br/>groups: left_arm, right_arm, both_arms,<br/>left_gripper, right_gripper, lift"]
    ps["Planning scene with collision objects"]
    mg --- ps
  end
  subgraph ctrl["Controllers in controller_manager"]
    la["left_arm_controller"]
    ra["right_arm_controller"]
    lg["left_gripper_controller"]
    rg["right_gripper_controller"]
  end
  subgraph a["firmware_sil: device path"]
    hw["OpenArmHW driver (upstream)"]
    em["OpenArmCanEmulator on vcan_arm_l, vcan_arm_r"]
    hc["sil_stm32_host_client"]
    ce["ctl017_emulator on vcan_aux<br/>moves only with a fresh permit"]
    lc["/sil/lift/command and /sil/lift/permit<br/>published by the scenario or mission"]
    lc --> hc
    hw <--> em
    hc <--> ce
  end
  subgraph b["fast and fine: direct path"]
    gzc["gz_ros2_control<br/>incl. lift_controller"]
  end
  gz["Gazebo joints: arms, grippers, lift_joint"]
  js["/joint_states (one writer)"]
  mg --> la & ra & lg & rg
  la & ra & lg & rg --> hw
  la & ra & lg & rg -.-> gzc
  em --> gz
  ce --> gz
  gzc -.-> gz
  gz --> js --> mg
```

Solid arrows are the device profile, dashed arrows the profiles without devices. In the device profile the lift is not driven by a ros2_control controller: it is commanded over the bus through the base controller stand-in. In `fast` the arms and grippers are qualified with the Bullet Featherstone engine only.

## 7. Physics, sensors and state feedback

```mermaid
flowchart LR
  act["Actuation<br/>wheel joint speeds, lift, arm torques"] --> phys["Gazebo Harmonic physics<br/>DART by default, 1 ms step"]
  phys --> motion["Motion and contact"]
  motion --> sens["Simulated sensors<br/>LiDAR, IMU, cameras, ToF, ultrasonic"]
  motion --> jstate["Joint states"]
  motion --> gt["Ground truth pose<br/>and contact sensors"]
  phys --> clock["/clock"]
  sens --> est["amcl, costmaps, collision_monitor"]
  jstate --> odom["Wheel odometry via the bus"]
  odom --> est
  est --> cmd["Nav2 and MoveIt 2 commands"]
  cmd --> act
  clock -.-> est
  clock -.-> cmd
  gt -.->|checks, and mission planning pose| test["Tests and mission"]
```

Ground truth exists only in simulation. Where a test or the mission uses it, the page for that test says so.

## 8. Repositories in the release

```mermaid
flowchart TB
  man["openamrobot-manifest<br/>pins every repository to a commit"]
  rel["openamrobot-release<br/>source lock, archive, checksums, notes"]
  docs["openamrobot-docs<br/>this site"]
  subgraph ws["Supported Digital Twin workspace (6 repositories)"]
    up["openamr-upperbody-sw<br/>model, MoveIt 2, emulators, scenes, mission"]
    pl["openamr-platform-sw<br/>base description, Nav2, SIL devices"]
    itf["openamrobot-interfaces<br/>messages and contracts"]
    oa1["enactic/openarm_description"]
    oa2["enactic/openarm_ros2"]
    oa3["enactic/openarm_can"]
  end
  inv["Further repositories in the full source inventory<br/>(hardware, firmware, UI and others):<br/>pinned and archived, not built in this workspace"]
  man --> ws
  man --> inv
  rel --> man
  docs --> rel
  up --> pl
  up --> itf
  up --> oa1 & oa2 & oa3
  pl --> itf
  classDef absent stroke-dasharray: 2 3,fill:#eeeeee,color:#555555;
  class inv absent;
```

The source archive holds the full inventory. The installation builds the six repositories of the supported workspace.

## 9. From simulation to hardware (proposed)

Only the first column exists in rc.1. The rest is a proposal for the next work stream and has not been approved as a commissioning procedure.

```mermaid
flowchart LR
  s1["Now: device emulators<br/>on virtual CAN, Gazebo"]
  s2["Optional now: read-only<br/>firmware image in Renode"]
  s3["Proposed: firmware<br/>commanding in emulation"]
  s4["Proposed: hardware in the loop<br/>real controller, simulated plant"]
  s5["Proposed: component bench tests"]
  s6["Proposed: physical mobile base"]
  s7["Proposed: complete physical robot"]
  c["Shared: ROS 2 interfaces, scenarios,<br/>acceptance values, recorded runs"]
  cal["Calibration back into the twin<br/>(track, friction, sensor noise)"]
  s1 --> s2 --> s3 --> s4 --> s5 --> s6 --> s7
  c -.- s1 & s4 & s6 & s7
  s6 -.-> cal -.-> s1
  classDef optional stroke-dasharray: 6 4;
  classDef absent stroke-dasharray: 2 3,fill:#eeeeee,color:#555555;
  class s2 optional;
  class s3,s4,s5,s6,s7,cal absent;
```

## 10. Digital Twin today and later

```mermaid
flowchart TB
  subgraph now["In rc.1"]
    gz["Gazebo Harmonic twin"]
    rv["RViz visualization"]
    rn["Renode, read-only image (optional)"]
  end
  subgraph later["Not in rc.1"]
    is["Isaac Sim"]
    mj["MuJoCo"]
    pr["Physical robot"]
    pe["Perception"]
    te["Teleoperation and data capture"]
    le["LeRobot and policy training"]
    ev["Policy evaluation"]
  end
  model["Combined robot model and interfaces"]
  model --> gz
  model --> rv
  model -.-> is & mj
  gz -.-> pe
  pr -.-> te -.-> le -.-> ev
  gz -.-> ev
  classDef optional stroke-dasharray: 6 4;
  classDef absent stroke-dasharray: 2 3,fill:#eeeeee,color:#555555;
  class rn optional;
  class is,mj,pr,pe,te,le,ev absent;
```

Dashed arrows are intended relations, not working integrations.
