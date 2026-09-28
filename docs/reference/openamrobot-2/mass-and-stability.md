---
title: Mass and stability (F2S)
tags: [builder, integrator]
status: planned
description: The F2S stability and stopping model for OpenAMRobot 2.0, mass budget, centre of gravity envelope, tipping margins, stopping distance and the drive-pair check.
---

# Mass and stability (F2S)

**Canonical source:** the F2S deliverable of the OpenAMRobot 2.0 execution plan, owned by the platform lead and published with the mechanical release in [openamr-platform-hw](https://github.com/openAMRobot/openamr-platform-hw). This page explains the model and its current results; the workbook with the formulas is filed with the deliverable.

**Applies to:** OpenAMRobot 2.0, model of 28 September 2026, pending measured inputs. For guidance on extending mass and stability in your own build, see [Mass and stability in the customization section](../../customize/hardware/mass-and-stability.md).

!!! warning "Fabrication gate, not a certificate"
    F2S is the gate that must pass before any structural part is fabricated. It is a static and quasi-static model on flat floors. It does not replace the physical tipping and braking tests of the commissioning window, and it makes no safety certification claim.

## What the model answers

| Question | Method |
|---|---|
| How heavy is the robot and where is its centre of gravity? | Mass budget of every subsystem with its position, from CAD volumes, supplier data and the official OpenArm 2.0 description |
| Can it tip while working? | Centre of gravity projected onto the tipping boundary (castor swivel axes minus the 15 mm castor offset) in four poses: travel, both arms forward with payload, one arm sideways, and a 150 N drawer pull at 1090 mm |
| Can it tip while braking or turning? | Forward and lateral acceleration at which the centre of gravity crosses the boundary, compared with the configured deceleration and the traction limit |
| How far does it travel before stopping? | Reaction latency plus braking at the configured deceleration, up to the speed limit |
| Is the drive pair within its rating? | Gross mass against the ZLTECH 120 kg drivable-mass rating, plus the vertical load per motor in a rocking case with a dynamic factor |

## Results (model of 28 September 2026)

| Output | Result | Basis |
|---|---|---|
| Gross mass | About 93 kg | Cap 120 kg; chassis 21 kg from CAD volumes, battery 23 kg, arms with grippers 12 kg, mast about 10 kg, payload 3 kg |
| Centre of gravity | 366 to 448 mm high across the four poses, within 35 mm of the drive axle | Lowest in travel pose, highest with both arms forward |
| Lowest static margin | 86 mm, drawer pull of 150 N at 1090 mm | Minimum 50 mm; the robot would tip at about 220 N |
| Braking | Tipping needs more than 5.4 m/s² in the worst pose; traction limit about 3.5 m/s²; configured deceleration 2.5 m/s² | Both limits above the configured value |
| Stopping distance at the 1.5 m/s ceiling | 0.82 m, including 0.25 s reaction latency | Minimum look-ahead for obstacle and floor sensing at the ceiling speed |
| Wheel speed at 1.5 m/s | 143 rpm | Motor rated 200 rpm |
| Drive pair | Within the 120 kg drivable-mass rating; about 650 N vertical load per motor in the rocking case | Allowable radial load requested from ZLTECH |
| Geometry change | None | Battery to the rear, mast on the drive axle, flat-floor envelope |

## Inputs and their status

| Input | Source | Status |
|---|---|---|
| Platform geometry, castor and wheel positions, mast mounting face | Platform STEP model | From CAD |
| Chassis mass | CAD volumes at steel density, top cover included | To be weighed |
| Arm, gripper and body masses | Official OpenArm 2.0 description and CAD | Official |
| Battery mass and position | Selected pack and the 25 percent placement decision | Decided, pack not yet built |
| Castor offset and height | Supplier data, Blickle LPA-VSTH 35K | Official |
| Wheel friction coefficient | Supplier data, ZLTECH | Official |
| Radial load limit per motor | ZLTECH | Requested |
| Dynamic factor for uneven floors | Assumed 1.5 | Replaced by the physical rocking test |

## Operating envelope that follows

- Flat indoor floors. Thresholds and cable covers are crossed at crawl speed until the physical test replaces the assumed dynamic factor; the 35 mm castor wheels stop on small steps.
- Drawer and door pulls up to 150 N at working height with the hands kept close to the body.
- Command ceiling 1.5 m/s in software, treated as an analytical limit until the stopping tests set the accepted operating speed; obstacle detection must reach at least 0.9 m ahead at that speed.

## Next

[Hardware architecture](hardware-architecture.md) shows the electrical side of the same robot; [General arrangement](general-arrangement.md) shows the geometry the model uses.
