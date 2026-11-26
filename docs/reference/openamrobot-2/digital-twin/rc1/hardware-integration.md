---
title: From the Digital Twin to hardware (proposed)
tags: [developer, integrator]
status: experimental
description: A proposal for how the tests of the OpenAMRobot 2.0 rc.1 Digital Twin could be reused when hardware integration starts, and what only hardware can show.
---

# From the Digital Twin to hardware (proposed)

This page is a proposal for the next work stream. It is not an approved commissioning procedure and it is not a safety
procedure. It needs review by the platform lead and the firmware owner before anyone acts on it. Nothing on this page
has been run on hardware.

The rc.1 Digital Twin is simulation only. No firmware runs by default: the base controller is a Python stand-in, and
the motor driver (ZLAC8015D), the lift controller (CTL-017), the battery management system and the arm motors are
protocol emulators on five virtual CAN buses. The safety chain is not modelled. See
[Where the logic runs](execution-map.md) and [Limitations](limitations.md).

The page gives no wiring values, currents, component choices or safety logic. Those belong to the hardware and
firmware work packages.

## What the twin already helps with

- **Reachability checks.** `scn03_arms_reach` brings both arms to a shelf target at two lift heights.
- **Frame and joint verification.** `scn09_single_writer` checks the TF tree and one writer per topic. The combined
  model has its own model tests.
- **Navigation and manipulation software development.** Nav2 and MoveIt 2 run as native software against the
  simulated robot.
- **Bus protocol development.** The host side speaks the device protocols on `vcan_drive`, `vcan_aux`, `vcan_bms`,
  `vcan_arm_l` and `vcan_arm_r`. The arm driver is the unmodified upstream driver.
- **Regression tests.** The 17 scene tests `scn01` to `scn17` and the whole-robot mission run headless in CI.
- **Preparing acceptance scenarios.** Each scenario already has a sequence, measured quantities and limits. See the
  [Scenario catalog](scenarios.md).

## What the twin cannot establish

Only hardware can show the following:

- motor behaviour, torque and current
- traction, wheel slip and castor rolling on a real floor
- encoder accuracy
- electrical safety
- braking
- thermal behaviour
- durability
- payload
- grasp reliability
- sensor noise. The simulated IMU has no noise model
- real bus timing. A virtual CAN bus has no bit timing, arbitration, error frames or bus-off
- safety of the complete robot

The emulators are not verified against the delivered devices. The lift controller emulator implements a proposed
object dictionary. The battery protocol is unconfirmed for the delivered unit.

## Existing tests and a possible hardware counterpart

The table is a starting point for discussion. "Reuse" names what exists today. The other two columns are proposals.

| Stage | Scenario or test to reuse | What must change | New measurement needed |
|---|---|---|---|
| Controller bench | The Renode tests of the read-only telemetry image in the platform SIL workflow: banner, reset behaviour, heartbeat loss reported as unknown and never as zero | The controller board replaces the emulated processor. The image in the twin only reads. Command firmware is not part of the twin | Real timing. The timing checks in Renode are plausibility checks, not measurements |
| CAN communication | Bus part of `scn09_single_writer` (at least one frame per bus in 2 s, CAN FD only on the arm buses, classic CAN only on the base buses), `test_canfd_vcan`, the `candump -L` trace format | Physical interfaces replace the virtual ones. The replay tool refuses any interface whose name does not start with `vcan`, so only recording carries over as it is | Bit timing, error frames, bus load and bus-off behaviour |
| Motor driver and encoders | The emulator tests `test_zlac8015d.py`, the SIL protocol tests, the wheel ratio checks of `scn17_base_yaw_fast` | The delivered driver replaces the emulator. Object mapping, axis order and sign are not represented in the twin and need confirmation | Reported wheel speed and position against an independent reference, with the wheels off the floor |
| Compute module deployment | `scn10_profiles` (update rates), `scn09_single_writer` | The native stack is built and run on the 2.0 compute module. The twin does not exercise that module | Update rates, processor load and memory on the module |
| Mobile base | `scn01_drive`, `scn17_base_yaw_fast` | An external position reference replaces simulation ground truth. The 0.411 m track is replaced by a calibrated value | Distance, heading and turn angle on a measured floor |
| LiDAR and IMU | `scn06_stale_sensors` | Real drivers replace the Gazebo sensors and the bridge | Scan rate, noise, frame orientation, time stamps |
| Lift | `scn02_lift_permit`, `scn16_lift_fast` | The lift has no real hardware interface yet. Permit timing values in the twin are simulation test values | Position at each stop against an external measure. The permit check is a software check and stays outside safety evidence |
| One arm | `scn03_arms_reach` for one side, `scn04_grasp` | Real CAN FD adapters, the `real` hardware profile. The gripper unit difference between model and driver must be resolved first (upperbody issue 79) | End point position against an external measure, holding under load |
| Two arms | `scn03_arms_reach`, `scn09_single_writer` | Both arm buses live at once | Clearance between the arms and the body, traffic on both arm buses |
| Complete robot | The Baseline 1 mission with its eight phases | Planning from the map estimate and not from ground truth. Item poses from a detector, which does not exist yet. Gazebo contact sensors have no direct counterpart | Station position error against an external reference, success counts over repeated runs |

The observation scenarios `scn05_bus_loss` and `scn08_arm_power_cut` record reactions in simulation. Repeating a bus
loss or a power cut on hardware can drop a load or move the robot. That needs its own procedure, approved by the
platform lead, and is outside this proposal.

## Proposed layered test architecture

The proposal: one set of scenario definitions and acceptance values, three back ends.

| Layer | Back end | Devices | Reference for motion | Status |
|---|---|---|---|---|
| 1 | Emulators | Protocol emulators on virtual CAN, Gazebo physics | Simulation ground truth | Exists in rc.1 |
| 2 | Hardware in the loop | Real controller or real device on a bench, the rest simulated | Depends on the device under test | Proposed. Does not exist in rc.1 |
| 3 | Physical robot | All devices real | External measurement | Proposed |

Proposed properties:

- The scenario code in `scenarios.py` stays the single definition of sequence and limits. A back end supplies the
  robot interface and the reference measurement.
- Every run declares its back end in its log, as runs declare `planning_pose_source` and `object_pose_source` today.
- The result line keeps its form: `BUILD1 <scenario> RESULT <result> <reason> log <path>`. PASS, FAIL and BLOCKED keep
  their meaning. BLOCKED is never a pass.
- Recorded runs from layers 2 and 3 are compared with the twin run of the same scenario. A difference is a finding
  about the twin or about the hardware. It is recorded, not tuned away.
- Limits are reviewed per layer. Several limits in the source are marked as estimated guard values for this
  simulation. They are not physical specifications.
- A scenario that depends on ground truth is marked as not portable until a reference measurement exists for it.
- A pass on layer 1 or 2 is never reported as a result of layer 3.

Open question for the review: whether the bench layer belongs in the scene package or in the firmware repositories.

## What can be built before hardware arrives

1. **Bus diagnostic scripts.** Listen on each bus, count frames per identifier, check frame kind per bus, and write
   `candump -L` traces. `scn09_single_writer` already listens on all five buses.
2. **Interface conformance checks.** A check list per device protocol, run against the emulators first. The same
   checks later show where a delivered device differs from its emulator.
3. **Recording and replay.** The launch has a replay hook, `replay_<bus>:=<file>`, that plays a trace into a virtual
   bus in place of that bus's emulator. Traces recorded from real devices can feed the unchanged host software.
4. **A calibration procedure for track, wheel radius and odometry.** The SIL path uses a wheel radius of 0.098 m and
   an effective track of 0.411 m. The 0.411 m value is a calibration of the simulation, not a chassis dimension. The
   procedure should define the drives, the external reference, the computation and the acceptance band, and be
   rehearsed in the twin with `scn01_drive`.
5. **A commissioning checklist skeleton.** Section headings and evidence fields per integration step, with the
   content left to the owners named in the next section.

All five are software work and follow the rules in [Contribute to the Digital Twin](contributing.md).

## Proposed integration order

Each step starts only when the step before it has a recorded result. The order is a proposal.

1. **Power protection and the hardwired safety provisions.** These are designed and verified by qualified people on
   the hardware, outside this software. The twin contributes nothing to this step. Telemetry, watchdogs, status
   displays and fixtures are never safety evidence.
2. **Compute and controller communication.** The compute module and the base controller exchange frames on the bench.
   Reuse: bus diagnostic scripts, conformance checks.
3. **Motor drivers and encoders.** Wheels off the floor. Confirm object mapping, axis order and sign against the
   delivered driver.
4. **Mobile base.** First drives on a measured floor. Run the calibration procedure, then the counterpart of
   `scn01_drive`.
5. **LiDAR and IMU.** Real drivers, frame orientation, rates. Then localization against a map.
6. **Further sensors.** Cameras, time-of-flight and ultrasonic sensors, one at a time.
7. **Lift.** Counterparts of `scn02_lift_permit` and `scn16_lift_fast`, once the lift has a hardware interface.
8. **First arm.** Counterpart of `scn03_arms_reach` for one side, then `scn04_grasp`.
9. **Second arm.** Both arms together.
10. **Complete robot.** The mission sequence, with planning from the map estimate.
11. **Perception and AI.** Item poses from a detector in place of ground truth, then learned policies.

## Hardware generations

The platform repository also contains the bring-up of the earlier robot generation, which has its own controller board
and IMU. That generation and the 2.0 controller hardware are separate gates and stay separate in tests, logs and
results. The twin exercises neither of them, and no 2.0 real-robot bring-up exists yet in these repositories.

## What this page does not claim

- No step above has been carried out.
- No acceptance value above is a physical specification.
- No test above is safety evidence, on any layer.
- The table does not say that a twin scenario will pass on hardware.

## Review needed

| Reviewer | Question |
|---|---|
| Platform lead | Is the integration order right, and which steps need a separate approved procedure? |
| Firmware owner | Which conformance checks match the device contracts, and where does the bench layer live? |
| Navigation maintainer | Which reference measurement replaces ground truth for the base scenarios? |
| Manipulation maintainer | Which arm scenarios are safe to repeat on hardware, and in which order? |

Propose changes through an issue in the owning repository. See [Contribute to the Digital Twin](contributing.md),
[Capabilities](capabilities.md) and [Release and evidence](release.md).
