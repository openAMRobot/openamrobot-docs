---
title: SLAM and mapping
tags: [beginner, builder]
description: How a robot builds a map while working out where it is inside it.
---

# SLAM and mapping

<span class="track track-beginner">Beginner</span> <span class="track track-builder">Builder</span>
{: .track-row }

**For:** anyone who wants to understand where the robot's map comes from.
**Before you start:** [Coordinate frames](coordinate-frames.md).
**When you finish:** you will know what SLAM does, why it is circular, and how to drive a mapping
run that produces a usable result.

## The chicken and egg

To know where you are, you need a map. To build a map, you need to know where you are.

**SLAM** — Simultaneous Localization And Mapping — solves both at once. The robot moves, guesses
where it went from odometry, and matches what it now sees against what it has already built. Where
the match is good, it grows the map. Where the match disagrees with odometry, it trusts the sensor
and corrects the estimate.

That is the whole idea. The engineering is in doing it fast, and in not letting small errors
compound.

## Occupancy grids

The output is usually an **occupancy grid**: the world chopped into cells, each holding a
probability of being occupied.

- **Free** — laser passed through it
- **Occupied** — laser stopped in it
- **Unknown** — never observed

That third category is doing real work. A planner treats unknown space differently from free
space, and the frontier between known and unknown is what exploration algorithms drive toward.

A typical indoor grid uses 5 cm cells. Smaller cells mean a sharper map and more memory and
computation; larger cells blur thin obstacles like chair legs into nothing.

## Loop closure

The single most important idea in SLAM.

Drive a large loop and come back to where you started. Odometry has drifted, so the robot thinks
it is somewhere slightly different, and it starts drawing a second copy of a corridor it already
mapped, offset by the drift. Maps that look "doubled" or smeared are showing you exactly this.

**Loop closure** is recognising *I have been here before*, and then redistributing the accumulated
error backwards across the whole trajectory so the two observations agree. A good loop closure
visibly snaps the map into shape.

This is why mapping advice always says to close loops: drive around obstacles and return to earlier
positions, rather than covering the space in one long unrepeated path.

## SLAM versus localization

Two different jobs, easily confused:

| | SLAM | Localization |
|:--|:--|:--|
| Map | Being built | Already exists |
| Question | Where am I *and* what does the world look like? | Where am I on this known map? |
| Cost | Higher | Lower |
| When | Mapping run, or changing environments | Normal operation |
| In this stack | `slam_toolbox` | AMCL |

Normal operation localizes against a saved map. You run SLAM when you first map a space, or when
the space has changed enough that the old map is wrong.

## Driving a good mapping run

The map you get is a direct product of how you drove. Practical rules:

1. **Go slowly.** Scan matching needs overlap between consecutive scans. Fast motion, especially
   fast rotation, is the most common cause of a bad map.
2. **Rotate gently.** Rotation is where odometry error is largest.
3. **Close loops deliberately.** Return to places you have already been.
4. **Cover the whole space**, including the parts you think the robot will not use. It will.
5. **Map when it is quiet.** People walking through get drawn into the map as walls. So do parked
   trolleys that will later move.
6. **Watch it build.** In RViz, in real time. A map going wrong is obvious immediately and painful
   to discover afterwards.

## What makes a space hard

| Condition | Why it is hard |
|:--|:--|
| Long featureless corridors | Every position along it looks identical to the laser |
| Large open halls | Few returns within lidar range to match against |
| Glass and mirrors | Laser passes through or reflects; the map gets holes and ghosts |
| Highly dynamic areas | Moving objects become permanent map features |
| Repetitive layouts | Identical aisles cause confident wrong matches |

None of these make mapping impossible. They mean you drive more carefully, close more loops, and
inspect the result before trusting it.

## After mapping

A raw map usually needs cleaning: remove the person who walked through, close a doorway the robot
should not use, mark a keep-out area. Editing an occupancy grid is editing an image, and any image
editor will do it — black for occupied, white for free, grey for unknown.

## In this stack

`slam_toolbox` is installed as a dependency for mapping. Normal operation uses AMCL on a saved map,
which is what the simulation launches. See
[openamr-platform-sw Concepts](../../reference/openamr-platform-sw/concepts.md#localization-amcl-on-a-saved-map).

## Further reading

- [slam_toolbox](https://github.com/SteveMacenski/slam_toolbox)
- [Nav2 first-time robot setup](https://docs.nav2.org/setup_guides/index.html)
- [SLAM overview](https://en.wikipedia.org/wiki/Simultaneous_localization_and_mapping)
- [Occupancy grid mapping](https://en.wikipedia.org/wiki/Occupancy_grid_mapping)

## Related

[Localization](localization.md) · [Coordinate frames](coordinate-frames.md) ·
[Creating a map](../../use/mapping/creating-a-map.md)

## Next

[Localization](localization.md)
