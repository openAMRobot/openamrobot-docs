---
title: Navigation
---
<section class="oamr-hero oamr-hero--compact"><div><span class="oamr-status oamr-status--experimental">Experimental</span><h1>Navigation</h1><p>Understand how OpenAMRobot localizes, plans, controls and moves through its environment.</p></div><img src="https://avatars.githubusercontent.com/u/175850144?v=4" alt="OpenAMRobot logo"></section>

## For

**Primary path:** Integrator

This page explains how navigation fits into the OpenAMRobot software stack. It provides the system-level architecture and links to the owning implementation repository.

**Applies to:** OpenAMRobot mobile-platform navigation in the current experimental software stack. This page covers localization, planning, control, navigation behaviors, velocity processing, collision monitoring, and their interfaces at the system level. Exact package configuration and implementation details remain in `openamr-platform-sw`.

**When you finish:** you can identify the five main stages of the navigation flow—localization, Nav2 planning/control, velocity processing, collision monitoring, and the robot base—and locate the owning repository for their implementation details.

!!! warning "Current capability and safety status"
    The current mobile-platform navigation stack is **experimental**. The software repository documents an end-to-end simulation using ROS 2 Jazzy, Gazebo Harmonic and Nav2. Real-robot integration and physical validation remain in progress.

    Navigation behavior depends on correct sensor data, TF, odometry, localization and controller configuration. This page describes the system architecture; it does not establish physical safety limits, acceptance criteria or production readiness.

## Before you start

You should have a basic understanding of:

* ROS 2 nodes and topics
* TF coordinate frames
* odometry
* laser scan data
* maps and localization
* Nav2 navigation concepts

For exact installation commands, package versions, parameters and launch procedures, use the canonical [`openamr-platform-sw`](https://github.com/openAMRobot/openamr-platform-sw) repository.

## Navigation architecture

At the system level, OpenAMRobot navigation follows this flow:

```text
Sensors and robot state
        │
        ├── Laser scan
        ├── Odometry
        └── TF
        │
        ▼
Localization
        │
        ├── Map
        └── Robot pose
        │
        ▼
Nav2
 ┌───────────────┬────────────────┐
 │               │                │
 ▼               ▼                ▼
Planner       Controller       Behaviors
 │               │                │
 └───────┬───────┴────────────────┘
         ▼
Velocity processing
         ▼
Collision monitoring
         ▼
Robot base
         │
         ▼
Odometry / TF feedback
```

The current platform navigation implementation separates localization and navigation responsibilities while using Nav2 for planning, control and behavior management.

## Localization

Localization estimates the robot pose relative to the map.

The current mobile-platform navigation stack uses map data, laser observations, odometry and TF relationships to maintain the robot's estimated pose.

See [Localization](localization.md) for the navigation-specific explanation.

## Planning and control

Navigation planning determines a path toward a goal while considering the environment represented by the navigation costmaps.

The controller converts the planned path into velocity commands for the mobile base.

The exact planner, controller, parameters and tuning values are maintained in the owning software repository.

See:

* [Path planning](path-planning.md)
* [Obstacle avoidance](obstacle-avoidance.md)

## Costmaps

OpenAMRobot navigation uses navigation costmaps to represent obstacles and traversability for planning and control.

At a system level:

* the **global costmap** supports planning through the larger environment;
* the **local costmap** represents the nearby environment used during motion control.

The exact costmap layers, footprint, sensor configuration and tuning parameters belong to the current platform implementation.

## Velocity and robot feedback

The navigation command path can be understood as:

```text
Navigation controller
        ↓
Velocity processing
        ↓
Collision monitoring
        ↓
Robot base
        ↓
Odometry
        ↓
TF / navigation feedback
```

This feedback loop allows navigation to continuously relate commanded motion to the robot's estimated state and environment.

The exact topic names, remappings and QoS settings are maintained by the owning repositories.

## TF

Navigation depends on consistent coordinate-frame relationships.

The mobile platform uses TF to relate the map, odometry, robot base and sensor frames.

A typical navigation relationship is:

```text
map
 └── odom
      └── base_link
           ├── base_footprint
           └── sensor frames
```

The exact frame names and sensor transforms are configuration-dependent and must be verified against the current platform implementation.

See [Coordinate frames](coordinate-frames.md).

## Mapping and localization

Navigation can use a previously created map for localization, while SLAM provides a mapping workflow when a map is not yet available.

These are different operating modes:

```text
SLAM
  Mapping + localization
        ↓
      Map
        ↓
Localization
  Localization on existing map
        ↓
      Nav2
```

See [SLAM and mapping](slam-and-mapping.md) and [Localization](localization.md).

## Docking

Docking builds on the navigation stack to move the robot toward a docking target and complete the docking sequence.

The current platform software documents an AprilTag-based docking simulation integrated with Nav2.

See [Docking](docking.md) for the system-level docking workflow.

## Simulation and physical validation

The current software stack provides an end-to-end simulation path using ROS 2 Jazzy, Gazebo Harmonic and Nav2.

Simulation can be used to verify software integration and navigation behaviour, but simulation results do not establish physical robot acceptance or safety.

Physical validation requires the appropriate hardware, sensors, calibration, safety controls and approved test procedures.

## Verification

Navigation documentation is considered verified only when the described behaviour can be traced to an approved implementation or evidence source.

The current implementation source is:

* [`openamr-platform-sw`](https://github.com/openAMRobot/openamr-platform-sw)
* [`openamr-platform-sw navigation documentation`](https://github.com/openAMRobot/openamr-platform-sw/tree/main/docs/navigation)

Exact implementation details should be checked against that repository before publishing release-specific instructions.

## Next steps

* [Coordinate frames](coordinate-frames.md)
* [Odometry](odometry.md)
* [SLAM and mapping](slam-and-mapping.md)
* [Localization](localization.md)
* [Path planning](path-planning.md)
* [Obstacle avoidance](obstacle-avoidance.md)
* [Docking](docking.md)

## Owning source

[`openamr-platform-sw`](https://github.com/openAMRobot/openamr-platform-sw) is the canonical source for the current mobile-platform navigation implementation, including implementation details, configuration, parameters, launch files and tests.

This page provides the cross-project explanation and should not duplicate implementation-specific configuration.
