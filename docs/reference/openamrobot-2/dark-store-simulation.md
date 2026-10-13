---
title: Dark-store pick simulation
tags: [integrator, developer, partner]
status: planned
description: Interactive 3D simulation of OpenAMRobot 2.0 picking a grocery order in a two-aisle dark store, with reach, grasp, payload, column-moment and camera checks for every shelf location.
---

# Dark-store pick simulation

**Canonical source:** the OpenAMRobot 2.0 plan set (decision addendum P-03, revision 18.9 item 18 of 9 October 2026, upper-body mounting option B; revision 19.0 of 12 October 2026 for the column position and the base sensors) and the official OpenArm 2.0 description. The simulation is a teaching and discussion tool built from those inputs; it is not a specification and does not replace the F2S stability model, supplier evidence or physical tests.

**Applies to:** OpenAMRobot 2.0 with the DOLD Hexalift V4 350 mm lift on a two-position base plate, two OpenArm 2.0 arms with the pinch gripper mounted 180 mm ahead of the column axis, and two totes on the front deck.

!!! note "Visualization only"
    Visualization only; grocery requirements belong to OpenAMRobot 3.0. The dark store is an illustration of the OpenAMRobot 2.0 geometry, not a requirement or a release scope for 2.0. The scenario is dark-store picking, a [reference use case for OpenAMRobot 3.0](../use-cases.md#dark-store-picking).

!!! warning "Design proposal, about ±2 cm"
    Geometry comes from the current design baseline and supplier data sheets. The lift outline is drawn from the manufacturer's published 240 × 60 mm basic dimension and the adapter-plate outline is approximate until supplier CAD and the adapter-plate drawing arrive. Use the results to compare options and to plan pilots, not as a release or safety claim.

## Interactive simulation

The robot works in a small local grocery hub: two aisles of shelving with drinks, dairy, snacks and pantry goods, a packing table for order handover and a robot dock. Pick any shelf location from the list or click a product in the 3D view, then run a single pick cycle or the eight-item demo order. On a phone, open the full-screen version.

<a class="oamr-button oamr-button--primary" href="/assets/simulation/openamrobot2-dark-store-sim.html" target="_blank" rel="noopener">Open full screen</a>

<div class="oamr-frame oamr-frame--tall">
<iframe src="/assets/simulation/openamrobot2-dark-store-sim.html" title="OpenAMRobot 2.0 dark-store pick simulation" loading="lazy" allow="fullscreen"></iframe>
</div>

## What it shows

| Area | What you can do |
|---|---|
| Robot | Lift stops L1000, L1175 and L1350 (shoulder height in mm), two base-plate positions (centre `bp000` and +50 mm `bp050`), head camera pitch, base camera tilt and tote riser |
| Pick target | Every product on every shelf level of both aisles; front, second or third row |
| Checks | Reach margin with full seven-joint inverse kinematics, arm clearance to shelves, totes and column, jaw opening against the 88 mm gripper, gap to neighbouring products, payload, column moments, lift load, tote placement and visibility for the head, base and wrist cameras |
| Comparison | Reach margin of every location at all three lift stops, with the stop the robot would use |
| Order run | Picks eight items from both aisles, drives to the packing table, places them upright and returns to the dock |
| Export | Records the order run as a video and saves the run timeline as CSV |

## What the current baseline tells us

| Finding | Consequence for pilots |
|---|---|
| Shelves between about 0.5 m and 1.4 m are reachable; the 1.72 m top shelf and the floor deck are not | Plan robot-picked assortment on the middle shelves; keep heavy multipacks and crates for people |
| Most locations work at L1000; 1.32 m shelves need L1175 | Lift travel at 18 mm/s dominates the pick cycle when the stop changes |
| Cereal, biscuit boxes, coffee bags and chocolate bars facing the aisle with their wide side do not fit the 88 mm gripper | Face robot-picked cartons with the narrow side out, or plan a different end effector |
| Facings packed with 6 to 8 mm gaps leave no room for the gripper fingers (about 17 mm needed) | Space robot-picked facings wider or allow a nudge strategy |
| Without a riser the arms cannot reach the tote floor at L1000 | A tote riser of about 120 mm lets the robot place items in the totes and take them out again |
| The fixed head camera cannot see side shelves or the totes | Wrist cameras carry the close-range perception during picking and placing |

The findings were rechecked on 12 October 2026 with the column position of P-03 revision 19.0 (column axis x = +0.060 m from `base_link` at `bp000` and +0.110 m at `bp050`). Shelf reach per level and the lift stop used are the same as with the earlier column position, superseded by P-03 revision 19.0, and the eight-item demo order completes at both base-plate positions, because the robot parks relative to the shoulder. These results change when an input changes. The simulation recalculates them in the browser for the settings you choose.

## Basis and limits

- Heights follow the P-03 datum: floor at zero, steel deck 294 mm, aluminium base plate top 304 mm, column 530 mm retracted and 880 mm extended, 166 mm from the column head plate to the OpenArm mount.
- Column position (P-03 revision 19.0): the column axis is 330 mm behind the 780 mm chassis front edge, x = +0.060 m from `base_link` at `bp000` and +0.110 m at `bp050`.
- Base sensors (P-03 revision 19.0): Gemini 336L housing centre 142.5 mm above the floor, `base_camera_link` (0.376, 0, 0.0445) from `base_link`, up-tilt `bt05`, `bt10` or `bt15`; RPLIDAR S3 beam 222.0 mm above the floor; four MB7060 ultrasonic sensors in the front and rear edge holes and two TF-Luna cliff sensors in the front and rear centre holes, 91.4 mm above the floor.
- Option B layout: the OpenArm arm mount point sits 180 mm ahead of the column axis, at y ±31 mm, on a MISUMI HFS6-60120 arm profile (340 mm) standing on a 10 mm adapter plate on the column head; the ZED Mini lens is 22 mm ahead of and 223 mm above the arm mount point.
- Arm kinematics and meshes come from the official OpenArm 2.0 description; payload 4.1 kg nominal and 6.0 kg peak including the end effector.
- The collision screen uses spheres along the arm against shelves, uprights, totes, column and chassis; it ignores neighbouring products.
- Moments are static, at the column foot, compared with the Hexalift ratings of 450 / 225 N·m lateral and 1200 / 500 N·m lengthwise (static / dynamic).
- Products, brands and prices are invented. The store is a generic local grocery hub, not a specific operator.

## Related pages

- [OpenAMRobot 2.0 design](index.md)
- [Mass and stability (F2S)](mass-and-stability.md)
- [Retail and replenishment](../../solutions/retail.md)
- [Reference use cases](../use-cases.md) (dark-store picking is a reference use case for OpenAMRobot 3.0)
