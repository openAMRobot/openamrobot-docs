---
title: Mass and stability (F2S)
tags: [builder, integrator]
status: planned
description: The F2S stability and stopping model for OpenAMRobot 2.0, mass budget, centre of gravity envelope, tipping margins, stopping distance and the drive-pair check.
---

# Mass and stability (F2S)

**Canonical source:** the F2S deliverable of the OpenAMRobot 2.0 execution plan, owned by the platform lead and published with the mechanical release in [openamr-platform-hw](https://github.com/openAMRobot/openamr-platform-hw). This page explains the model and the status of its results; the workbook with the formulas is filed with the deliverable.

**Applies to:** OpenAMRobot 2.0 with upper-body mounting option B (P-03 revision 18.9 item 18, 9 October 2026): lift column on a two-position base plate, shoulder 1000 to 1350 mm. For guidance on extending mass and stability in your own build, see [Mass and stability in the customization section](../../customize/hardware/mass-and-stability.md).

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

## Results

!!! note "Rerun pending for option B"
    The model of 28 September 2026 was built for an upper body without a lift and is no longer current. Its results are withdrawn from this page. The model is being rerun for option B; results will be published here when the rerun is complete.

The rerun covers:

| Case | Option B values |
|---|---|
| Lift position | Fully extended, shoulder 1350 mm at the OpenArm arm mount point; retracted, shoulder 1000 mm |
| Base-plate position | Both column positions, centre (`bp000`) and +50 mm (`bp050`) |
| Upper-body geometry | Lift column 530 to 880 mm on the 304 mm base-plate top face, arm mount point 180 mm ahead of the column axis, head camera 22 mm ahead of and 223 mm above the arm mount point |
| Height envelope | Complete robot at most 1700 mm at full lift extension |
| Poses and loads | Travel, both arms forward with payload, one arm sideways, 150 N drawer pull at 1090 mm, braking and turning |

## Inputs and their status

| Input | Source | Status |
|---|---|---|
| Platform geometry, castor and wheel positions, base-plate mounting face | Platform STEP model | From CAD |
| Lift column, base plate and arm profile geometry and masses | Supplier CAD and data for the DOLD Hexalift V4, option B layout | Supplier CAD pending |
| Chassis mass | CAD volumes at steel density, top cover included | To be weighed |
| Arm and gripper masses | Official OpenArm 2.0 description and CAD | Official |
| Battery mass and position | Selected pack and the 25 percent placement decision | Decided, pack not yet built |
| Castor offset and height | Supplier data, Blickle LPA-VSTH 35K | Official |
| Wheel friction coefficient | Supplier data, ZLTECH | Official |
| Radial load limit per motor | ZLTECH | Requested |
| Dynamic factor for uneven floors | Assumed 1.5 | Replaced by the physical rocking test |

## Operating envelope

These limits come from the earlier model and are confirmed or replaced by the option B rerun.


- Flat indoor floors. Thresholds and cable covers are crossed at crawl speed until the physical test replaces the assumed dynamic factor; the 35 mm castor wheels stop on small steps.
- Drawer and door pulls up to 150 N at working height with the hands kept close to the body.
- Command ceiling 1.5 m/s in software, treated as an analytical limit until the stopping tests set the accepted operating speed; obstacle detection must reach at least 0.9 m ahead at that speed.

## Next

[Hardware architecture](hardware-architecture.md) shows the electrical side of the same robot; [General arrangement](general-arrangement.md) shows the geometry the model uses.
