---
title: Localization
tags: [beginner, builder]
description: How a robot works out where it is on a map it already has.
---

# Localization


**For:** anyone who wants to understand how the robot knows its place.
**Before you start:** [Coordinate frames](coordinate-frames.md) and [SLAM and mapping](slam-and-mapping.md).
**When you finish:** you will understand particle filters well enough to debug them.

## The job

You have a map. The robot is somewhere on it. Odometry says roughly where, but odometry drifts.
The laser sees walls. Localization reconciles the two into a single best estimate, continuously.

## Particle filters, in plain terms

AMCL — Adaptive Monte Carlo Localization — uses a **particle filter**. The idea is easier than the
name.

Imagine a thousand guesses about where the robot is. Each guess is a particle: a position and a
heading.

1. **Move.** The robot drives forward half a metre. Every particle moves half a metre in its own
   heading, plus a little random noise to represent the fact that odometry is imperfect.
2. **Sense.** The laser returns a scan. For each particle, ask: *if the robot were here, what would
   the laser see?* Compare against the real scan.
3. **Weight.** Particles that predicted well get high weight. Particles that predicted badly get
   low weight.
4. **Resample.** Draw a new set of particles, favouring the heavy ones. Bad guesses die out; good
   ones multiply.
5. **Repeat**, several times a second.

Within a few metres of driving, the cloud collapses onto the true position and follows it.

**The "adaptive" part:** when the robot is confident, AMCL uses fewer particles and saves
computation. When it becomes uncertain, it uses more. You can watch this happen in RViz — the cloud
visibly tightens and spreads.

## What you see in RViz

The particle cloud is the best diagnostic in the stack, and it is free:

| Cloud looks like | Meaning |
|:--|:--|
| Tight blob, follows the robot | Healthy. Confident and correct. |
| Wide scatter | Uncertain. Just started, or the environment is featureless. |
| Stretched along a corridor | Position along the corridor is ambiguous. Normal. Resolves at a junction. |
| Two separate clumps | The environment is genuinely ambiguous — identical aisles, symmetric rooms. |
| Tight but in the wrong place | Confidently wrong. The worst state. Re-seed it. |

## The initial pose

AMCL is not usually given a global search. It needs a starting guess.

In RViz, *2D Pose Estimate* lets you click the robot's approximate position and drag its heading.
Get within a metre or so and it converges quickly.

Without a guess, one of three things happens: it converges slowly, it converges to the wrong place
in a repetitive environment, or it never converges.

Production systems solve this with a known start position — usually the charging dock, which is
exactly where a docked robot is.

## The kidnapped robot problem

Pick a running robot up and put it somewhere else. Its particles are all clustered where it used to
be, all now predicting badly.

A particle filter can recover if it is configured to inject random particles when overall
confidence collapses. That is a tuning decision, and it trades recovery ability against stability:
too much injection makes a healthy filter jittery.

Practically: if you move a robot by hand, re-seed the pose.

## Parameters worth knowing

| Parameter | What it controls | Symptom of too low | Symptom of too high |
|:--|:--|:--|:--|
| `min_particles` / `max_particles` | Cloud size | Fails to converge, or loses track | CPU load |
| `laser_max_range` | How far scans are trusted | Ignores useful distant features | Noisy far returns pollute matching |
| `odom_alpha1..4` | How much odometry is trusted | Filter ignores real motion | Cloud spreads too fast |
| `update_min_d` / `update_min_a` | How far or how much rotation before an update | Wasted computation | Sluggish correction |

Reference: [Nav2 AMCL configuration](https://docs.nav2.org/configuration/packages/configuring-amcl.html)

!!! tip "Tune the environment first"
    Before tuning the filter, ask whether the map is good and whether the space has features. A
    localization problem in a long empty corridor is a space problem, not a parameter problem.

## Localization and the transform tree

Worth restating because it is the connection between two ideas: AMCL does not publish the robot's
pose directly. It publishes the **`map` → `odom`** transform. Odometry publishes `odom` →
`base_link`. Chain them and you have the robot on the map.

This is why localization corrections appear as small jumps in `map` while `odom` stays perfectly
smooth. See [Coordinate frames](coordinate-frames.md#why-both).

## Further reading

- [Nav2 AMCL](https://docs.nav2.org/configuration/packages/configuring-amcl.html)
- [Monte Carlo localization](https://en.wikipedia.org/wiki/Monte_Carlo_localization)
- [Particle filters](https://en.wikipedia.org/wiki/Particle_filter)
- [Probabilistic Robotics](http://www.probabilistic-robotics.org/) — the standard text

## Related

[SLAM and mapping](slam-and-mapping.md) · [Path planning](path-planning.md) ·
[openamr-platform-sw Concepts](../../reference/openamr-platform-sw/concepts.md)

## Next

[Path planning](path-planning.md)
