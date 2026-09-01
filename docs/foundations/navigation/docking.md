---
title: Docking and charging
tags: [beginner, builder]
description: How a robot finds its dock and gets onto it reliably, and why the last metre is the hard part.
---

# Docking and charging


**For:** anyone who wants to understand automatic docking.
**Before you start:** [Localization](localization.md).
**When you finish:** you will know why the last metre needs different techniques from the first
twenty, and what makes docking reliable or not.

## Why docking is its own problem

Navigation gets the robot to within a few centimetres of a goal. That is excellent for a delivery
point and useless for a charging contact, which needs millimetres and a specific heading.

Two reasons ordinary navigation cannot close that gap:

**Precision.** Map-frame localization has error on the order of centimetres. Charging contacts have
tolerances on the order of millimetres.

**Reference.** Navigation positions the robot relative to the *map*. Docking must position it
relative to the *dock*, which is a physical object that may have been nudged since the map was made.

So docking switches reference frames for the final approach. It stops asking "where am I on the
map" and starts asking "where am I relative to that dock, right now, as seen by my sensor."

## Ways to find a dock

| Method | How | Strengths | Weaknesses |
|:--|:--|:--|:--|
| **Fiducial marker** | Camera detects a printed tag of known size | Cheap, precise, gives full 6-DoF pose | Needs light, needs line of sight |
| **Retroreflective markers** | Lidar sees abnormally bright returns from reflective tape | Works in darkness, uses the existing lidar | Needs a lidar that reports intensity |
| **Geometric shape** | Lidar detects a distinctive profile such as a V-notch | No added materials | Confusable with similar shapes |
| **Magnetic or IR beacon** | Dock emits a signal the robot homes on | Simple, robust | Coarse; usually combined with something else |

This platform uses the first: [AprilTag](https://april.eecs.umich.edu/software/apriltag), a
fiducial family designed for exactly this. It is detected reliably at an angle, at distance, and
under uneven lighting, and it yields a full pose rather than just a bearing.

## The general sequence

Nearly every docking implementation has the same four phases, whatever the sensing method:

1. **Approach.** Navigate to a staging pose near the dock using normal navigation. Map-frame
   accuracy is enough here.
2. **Acquire.** Find the marker. Usually rotate until it is detected and its pose reading is stable
   over several frames.
3. **Align.** Move so the robot is perpendicular to the dock face and on its centreline. This
   matters because a straight-in final approach is far more repeatable than a curved one.
4. **Engage.** Drive straight in, slowly, until contact or until the target standoff is reached.

The OpenAMRobot implementation follows exactly this, ending about 90 cm from the tag and square to
it. Undocking is the reverse and deliberately simpler: reverse 1.5 m, spin 180°.

## Why the alignment phase exists

It is tempting to drive from wherever you are straight at the dock. This works badly.

Approaching at an angle means the robot must curve as it closes, and any error in the curve
compounds near the end where there is no room left to correct. Squaring up first converts a
two-dimensional problem into a one-dimensional one: once you are on the centreline and
perpendicular, the only remaining variable is distance.

## What makes docking unreliable

| Cause | Effect |
|:--|:--|
| Poor camera calibration | Pose estimate is systematically wrong; the robot aligns confidently to the wrong place |
| Tag too small for the distance | Detection is noisy at range |
| Uneven or changing lighting | Intermittent detection, jitter |
| Dock physically moved | Map staging pose is wrong; the robot searches |
| Floor slip during final approach | Odometry-based final motion overshoots |
| Single tag | One bad reading has nothing to be checked against |

The usual improvements, in order of effect: better calibration, larger or multiple tags, a
visual-servo final stage that continuously corrects rather than driving a precomputed distance,
and mechanical funnelling on the dock so the last centimetres are guided by shape rather than by
software.

## Safety

!!! warning "Docking is a blind manoeuvre in many implementations, including this one"
    In this stack, phases 2 to 4 publish velocity commands directly, bypassing the navigation
    stack. The costmaps and collision monitor are not in the loop, so the robot **will not stop**
    for something that enters its path during the approach.

    Keep the dock approach clear. Do not stand in it. Closing this gap — routing the manoeuvre
    through the navigation stack or adding lidar collision checking — is a stated roadmap item.

This is a good example of a general principle: a robot behaviour that bypasses the safety pipeline
for precision reasons must be documented as such, so that whoever deploys it knows where the
boundary is.

## Charging

Docking gets the robot to the contacts. Charging is then an electrical problem: contact
resistance, inrush current, a charger that must not energise until contact is confirmed, and a
battery management system that decides when to stop.

The dock should not be live until the robot reports engagement. Exposed live contacts in a space
where people walk are a hazard, and a shorting risk from dropped metal objects.

## Further reading

- [AprilTag](https://april.eecs.umich.edu/software/apriltag)
- [apriltag_ros](https://github.com/christianrauch/apriltag_ros)
- [Nav2 docking server](https://docs.nav2.org/configuration/packages/configuring-docking-server.html)
- [Camera calibration in ROS](https://docs.nav2.org/tutorials/docs/camera_calibration.html)

## Related

[Localization](localization.md) ·
[openamr-platform-sw Concepts](../../reference/openamr-platform-sw/concepts.md#docking-apriltag-and-a-four-phase-approach) ·
[Docking configuration](../../configure/docking-config/index.md)

## Next

[How manipulation works](../manipulation/index.md)
