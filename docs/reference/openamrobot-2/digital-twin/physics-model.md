---
title: Mechanical and physics model
tags: [developer, integrator]
status: experimental
description: What the OpenAMRobot 2.0 digital twin's physics models (engine, step, contact, wheels, masses), the known turn slip and base pitch, and where the parameters are registered.
---

# Mechanical and physics model

**For:** engineers who need to judge a motion result: how the robot body, wheels and joints are simulated.

**Canonical source:** the SIL fidelity record
([openamr-platform-sw pull request #168](https://github.com/openAMRobot/openamr-platform-sw/pull/168),
[`docs/architecture/sil_fidelity.md`](https://github.com/openAMRobot/openamr-platform-sw/blob/52c64da/docs/architecture/sil_fidelity.md),
draft) and the simulation parameter register
([openamr-upperbody-sw pull request #97](https://github.com/openAMRobot/openamr-upperbody-sw/pull/97),
[`simulation/parameter_register.yaml`](https://github.com/openAMRobot/openamr-upperbody-sw/blob/d3be136/simulation/parameter_register.yaml),
Proposed; deviations in [issue #96](https://github.com/openAMRobot/openamr-upperbody-sw/issues/96)). The values below
are quoted from those records for orientation; the records are the reference.

!!! warning "Simulation, not hardware validation"
    No mass, friction or dimension in the twin has been weighed or measured on OpenAMRobot 2.0 hardware.

## The model

One xacro file, `combined_robot.xacro` in openamr-upperbody-sw, describes the whole robot: the mobile base from
openamr-platform-sw, the DOLD lift as a prismatic joint (stops L1000, L1175, L1350), and two OpenArm 2.0 arms from the
upstream `openarm_description` at a pinned commit. Gazebo, RViz, MoveIt, MuJoCo and the Isaac importer all read
expansions of it. The expansion is locked by hash (`simulation/expansion_lock.yaml`, pull request #97); a change to the
model is a reviewed change of that lock.

## Engine and step

| Item | Value | Note |
|---|---|---|
| Simulator | Gazebo Harmonic (gz-sim 8.15.0, pinned vendor packages) | the reference physics |
| Engine | DART (`gz-physics-dartsim-plugin`), the default `physics_engine` | use DART for every run that drives |
| Step | 1 ms (`firmware_sil`, `fast`); 1/1500 s (`fine`) | the controller manager of the simulator publishes at about 616 Hz at the 1 ms step on a hosted runner |
| Alternative engine | Bullet Featherstone | grippers work there, but the base under-drives (0.866 m for 1.200 m commanded) and does not turn; for gripper work at a station only |
| Seed | none for Gazebo; Python and hash seeds fixed in the acceptance runs | a repeated run is not guaranteed identical |

## Contact model

Contact is DART's rigid contact with Gazebo friction tags. The wheel friction tags are `mu1` 1.5, `mu2` 0.5 with
`fdir1` along the wheel axis; contact stiffness and slip tags are not applied. Floor friction in the scene is 0.8,
estimated. Self collision of the arms is off. Contact sensors on the arm links, the item, the tote and fixtures observe
and change no force; the acceptance runs record every contact and fail on any pair not in the allowed list.

## Wheels and the known turn slip

| Item | Model | Real part |
|---|---|---|
| Drive wheel collision | flat cylinder r 0.100 m, 0.046 m wide | tyre 200 +/- 2 mm, 49.4 mm wide, Shore A 65 |
| Rolling radius | 0.100 m nominal, 0.098 m effective (the emulator path uses 0.098 m; pull request #146 moves the collision and DiffDrive to 0.098 m) | loaded radius not measured |
| Track | 0.400 m | placeholder; the 2.0 wheel assembly sets it |
| Castors | four fixed frictionless spheres r 0.026 m | swivel castors, rolling resistance unknown |
| Brake | none: an unpowered base rolls freely | 6 N m holding brake per motor |

**Turn slip (finding F1 of the fidelity record).** The flat wheel touches the floor along a line across the tread, so an
in-place turn scrubs the whole width while the commanded wheel speed holds. The base under-rotates: a pi/2 turn after
a straight move under-rotates by about 10 %, and the yaw error then turns into position error on the next straight
(grocery run 44299879412, finding F2). Odometry from the wheels does not see it, so odometry and ground truth drift
apart after turns. Proposed fix: a sphere r 0.098 m or a 4 mm cylinder as the wheel collision (pull request
[#171](https://github.com/openAMRobot/openamr-platform-sw/pull/171), awaiting the robot-description owner).

## Base attitude at rest

At spawn the Gazebo base rests 0.534 degrees nose down and 2 mm high, while the MoveIt planning scene assumes a level
base. The difference comes from the contact heights of the wheel and castor collisions. It is recorded as a known
deviation (criterion A6 of the release candidate) and needs a tracked issue against the model.

## Masses

Masses follow the project mass ledger, exported to the description (`config/roadmap_mass_export.yaml` in
openamr-platform-sw, generated from the roadmap model of this site). At the pin read by the fidelity record:
`base_link` 49.948 kg, complete base 58.163 kg, whole robot 87.11 kg. Inertias come from component boxes. Every mass is
a design value under ledger review, not a weighed value. See [Mass and stability](../mass-and-stability.md) for the
ledger itself.

## Parameter register and fidelity record

| Record | What it holds | State |
|---|---|---|
| Parameter register (#97) | every physical parameter the simulators carry, its authority, verification level (placeholder, datasheet, design decision, measured) and the check per simulator | Proposed, its parity job is red on a removed `xacro` package build |
| SIL fidelity record (#168) | the level of modelling per subsystem, the class (implemented model, approximation, placeholder, not modelled), the real value and its source, and a ranked fidelity roadmap | draft, review requested |
| Reality gap register (audits repository) | 188 known differences between twin and robot, each with the measurement that would close it | none measured yet |

## Limits that matter most

- Floor and tyre friction, castor drag and swivel, and wheel torque limits are not measured or not modelled.
- Drive limits differ per layer: Gazebo DiffDrive allows 1.0 m/s while the project speed ceiling is 0.5 m/s
  (pull request [#173](https://github.com/openAMRobot/openamr-platform-sw/pull/173) proposes one set).
- Camera fields of view are not the datasheet values; wrist camera frames are placeholders.
- No brake, battery or power model.
