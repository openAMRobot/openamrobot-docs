---
title: General arrangement
tags: [builder, integrator]
status: planned
description: Side, front and top views of OpenAMRobot 2.0 to scale, with the mast and shoulder mounting detail, the parts list and the decisions behind the layout.
---

# General arrangement

**Canonical source:** the platform CAD in [openamr-platform-hw](https://github.com/openAMRobot/openamr-platform-hw) and the upper-body CAD in [openamr-upperbody-hw](https://github.com/openAMRobot/openamr-upperbody-hw). The drawings below are derived from the platform STEP model and the official [OpenArm 2.0 CAD](https://docs.openarm.dev/hardware/openarm-2.0/general/); when either changes, the drawings are regenerated.

**Applies to:** OpenAMRobot 2.0, design proposal of 28 September 2026. Dimensions in millimetres. The installation height, the four positions and the own mast are recorded in P-03 revision 18.2.

!!! warning "Design proposal"
    The arrangement is drawn to scale from CAD, but four inputs are still open: the weighed chassis mass, the ZLTECH radial load limit, the hub-motor bracket and the arm supply without the OpenArm body. Battery and electronics outlines are placeholders until the mechanical work package (M-01) fixes them.

## Drawing sheet

The interactive sheet contains the three views, a numbered parts list, the mast detail with section A-A, the comparison of the four mast positions and the stability summary. Balloon numbers on the drawings refer to the parts list on the sheet.

<a class="oamr-button oamr-button--primary" href="/assets/hardware/openamrobot2-general-arrangement.html" target="_blank" rel="noopener">Open the drawing sheet full screen</a>

<div class="oamr-frame oamr-frame--tall">
<iframe src="/assets/hardware/openamrobot2-general-arrangement.html" title="OpenAMRobot 2.0 general arrangement, interactive drawing sheet" loading="lazy"></iframe>
</div>

## Views

<figure class="oamr-figure">
<img src="/assets/hardware/openamrobot2-ga-elevations.jpg" alt="Side and front elevations of OpenAMRobot 2.0 at the same scale, arms stowed, installed shoulder axis at 1350 mm, mast top at 1500 mm, assembled height no more than 1700 mm, numbered balloons for the parts list" loading="lazy">
<figcaption>Side and front views at the same scale. Front is to the right in the side view. The arms are drawn stowed at the 1350 mm installation height; ghost outlines mark the other three shoulder positions (1300, 1400 and 1450 mm).</figcaption>
</figure>

<figure class="oamr-figure">
<img src="/assets/hardware/openamrobot2-ga-top-view.jpg" alt="Top view of OpenAMRobot 2.0 with the tipping boundary, centre of gravity envelope, drawer-pull margin and LiDAR field" loading="lazy">
<figcaption>Top view. The dashed rectangle is the tipping boundary, the castor swivel axes moved inwards by their 15 mm offset. The centre of gravity stays inside it in every pose; the drawer-pull case (P4) is the closest at 86 mm.</figcaption>
</figure>

<figure class="oamr-figure">
<img src="/assets/hardware/openamrobot2-ga-mast-detail.jpg" alt="Detail A: elevation of the shoulder zone on the MISUMI HFS6-60120 profile with the four mounting positions and section A-A through the profile with the OpenArm J1_A plates" loading="lazy">
<figcaption>Detail A. The OpenArm J1_A plates bolt to the side T-slots of the profile with M5 bolts; one M6 bolt through the index cross hole locates both plates at the selected height.</figcaption>
</figure>

<figure class="oamr-figure">
<img src="/assets/hardware/openamrobot2-ga-parts-list.jpg" alt="Parts list 1 to 20 for the general arrangement with key data and sources" loading="lazy">
<figcaption>Parts list for the balloon numbers on the views.</figcaption>
</figure>

## Layout decisions shown

| Element | Value | Why |
|---|---|---|
| Mast | One MISUMI HFS6-60120 aluminium profile, 1196 mm long with its top 1500 mm above the floor, on the platform centre bracket (8 M8 rivet nuts) | Same 6-series T-slots as the OpenArm pillar, so the arm plates bolt on unchanged and the official arm kinematics stay exact |
| Shoulder positions | Four indexed positions, 1300, 1350, 1400 and 1450 mm above the floor; installation height 1350 mm | 1350 mm keeps about 350 mm of reach at the 820 mm test height; stability changes little between positions |
| Maximum height | At most 1700 mm for the complete assembled robot including the head camera; the robot may be lower | Door and rack envelope of the target sites |
| Battery | Centred 25 percent of the robot length from the rear | Balances the forward mass of the arms and keeps the centre of gravity near the drive axle |
| Electronics | All inside the mobile platform | Shorter harnesses, protected enclosure, no electronics on the mast |
| Drive and castors | Hub motors on the centre axle, four swivel castors, 52 mm total castor height | Existing platform geometry, no change to track or wheelbase |

## Mast positions compared

Theoretical horizontal reach of the gripper at the A4 test heights, using the official 633 mm arm reach. Stability figures come from the [mass and stability model](mass-and-stability.md).

| Shoulder axis | 1300 | 1350 (installed) | 1400 | 1450 |
|---|---|---|---|---|
| Arm plate top (mm) | 1361 | 1411 | 1461 | 1511 |
| Reach at 820 mm height (mm) | 413 | 346 | 254 | 62 |
| Reach at 1090 mm height (mm) | 597 | 577 | 552 | 521 |
| Reach at 1355 mm height (mm) | 631 | 633 | 631 | 626 |
| Centre of gravity height in travel (mm) | 366 | 375 | 384 | 392 |
| Braking deceleration that tips the robot, travel pose (m/s²) | 7.8 | 7.6 | 7.4 | 7.2 |

## Next

[Mass and stability](mass-and-stability.md) explains the numbers behind the tipping boundary and the stopping distance.
