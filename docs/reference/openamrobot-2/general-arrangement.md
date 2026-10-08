---
title: General arrangement
tags: [builder, integrator]
status: planned
description: Upper-body arrangement of OpenAMRobot 2.0, option B, lift column on a two-position base plate, arm profile and arm mount point, height stack, configuration IDs and the decisions behind the layout.
---

# General arrangement

**Canonical source:** the platform CAD in [openamr-platform-hw](https://github.com/openAMRobot/openamr-platform-hw) and the upper-body CAD in [openamr-upperbody-hw](https://github.com/openAMRobot/openamr-upperbody-hw). Drawings are derived from the platform STEP model, the supplier CAD of the lift column and the official [OpenArm 2.0 CAD](https://docs.openarm.dev/hardware/openarm-2.0/general/); when any of them changes, the drawings are regenerated.

**Applies to:** OpenAMRobot 2.0, upper-body mounting option B, decided on 9 October 2026 and recorded in P-03 revision 18.9 item 18. Dimensions in millimetres, heights from the floor (Z = 0); x forward, y left, z up.

!!! warning "Design decision, drawings pending"
    The values below are decided, but the supplier CAD for the lift column hole patterns, the OpenArm J1_A plate outline and the chassis deck pattern orientation is still pending. The drawing set of 28 September 2026 has been withdrawn from this page; it will be regenerated from the option B CAD. Battery and electronics outlines remain placeholders until the mechanical work package (M-01) fixes them.

## Upper-body layout

| Element | Value | Why |
|---|---|---|
| Lift column | DOLD Hexalift V4, 350 mm stroke, 530 mm retracted and 880 mm extended, mounted with its 240 mm side fore-aft | Moves the shoulder between 1000 and 1350 mm for low and high work heights |
| Base plate | 10 mm aluminium on the 294 mm chassis deck, top face 304 mm; two fore-aft column positions, centre (`bp000`) and +50 mm (`bp050`) | The 304 mm top face is the height reference; the second position moves the arms forward for reach |
| Arm profile | MISUMI HFS6-60120 (60 mm lateral, 120 mm fore-aft), 340 mm long, on a 10 mm adapter plate on the column top, 120 mm ahead of the column front face; 844 to 1184 mm at the retracted lift | Same 6-series T-slots as the OpenArm pillar, so the J1_A plates bolt on unchanged and the official arm kinematics stay exact |
| Arm mount point | OpenArm J1_A, frame `openarm_{side}_base_link`: 180 mm ahead of the column axis, y = ±31 mm, no rotation | The upstream OpenArm body (`openarm_body_link0`) is not used |
| Shoulder height | 1000 mm at the retracted lift, 1350 mm fully extended, measured at the OpenArm arm mount point | Lift height is joint state; calibrated stops `L1000`, `L1175` and `L1350` |
| Head camera | Stereolabs ZED Mini on the lift carriage, lens 22 mm ahead of and 223 mm above the arm mount point, centred at y = 0, pitch 15 to 35 degrees down in 5 degree steps (baseline 25 degrees) | Moves with the arms; the pitch bracket pivots on the lens line |
| Maximum height | At most 1700 mm for the complete assembled robot at full lift extension, including the head camera; the robot may be lower | Door and rack envelope of the target sites |
| Battery | Centred 25 percent of the robot length from the rear | Balances the forward mass of the arms and keeps the centre of gravity near the drive axle |
| Electronics | All inside the mobile platform; the lift carriage carries the arms, head camera and chest E-stop | Shorter harnesses, protected enclosure, no control electronics on the lift |
| Drive and castors | Hub motors on the centre axle, four swivel castors, 52 mm total castor height | Existing platform geometry, no change to track or wheelbase |

## Height stack

| Level | Retracted lift (mm) | Extended lift (mm) |
|---|---|---|
| Chassis deck top | 294 | 294 |
| Base-plate top face (height reference) | 304 | 304 |
| Column top (304 + column length) | 834 | 1184 |
| Arm profile, on the 10 mm adapter plate | 844 to 1184 | 1194 to 1534 |
| Shoulder at the arm mount point (304 + column length + 166) | 1000 | 1350 |
| Head-camera lens line (shoulder + 223) | 1223 | 1573 |

## Configuration IDs

Every configuration ID propagates to the robot description, TF, MoveIt, camera calibration, the configuration hash and the dataset metadata. The canonical list and the model live in [openamr-upperbody-sw](https://github.com/openAMRobot/openamr-upperbody-sw).

| Axis | IDs |
|---|---|
| Column | `dold_v4_350`, `tl3_400` (fallback; lengths pending supplier data) |
| Base plate | `bp000` (centre), `bp050` (+50 mm) |
| Head-camera pitch | `hp15`, `hp20`, `hp25` (baseline), `hp30`, `hp35` |
| Base-camera tilt | `bt05`, `bt10`, `bt15` |

The lift stops `L1000`, `L1175` and `L1350` are calibration IDs; the current lift height is joint state, not a configuration ID.

## Next

[Mass and stability](mass-and-stability.md) explains the stability model and the rerun that option B requires.
