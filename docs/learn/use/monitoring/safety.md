---
title: Safety in daily use
tags: [beginner]
description: The safety rules for working with the robot every day, and why the on-screen stop is not enough.
---

# Safety in daily use

<span class="track track-beginner">Beginner</span>
{: .track-row }

**For:** anyone who works near the robot, whether or not they operate it.
**Before you start:** nothing. This page comes before you touch anything.
**When you finish:** you will know the rules, and the reasoning behind each one.

!!! danger "Framework document"
    This page states network-wide practice. It is not a substitute for a risk assessment of your
    own site, and it is not legal or regulatory advice. Requirements differ by country and by
    workplace. Anything jurisdiction-specific must be confirmed locally.

## The one thing to remember

**The red E-STOP on the screen is not an emergency stop.**

It sends one zero-velocity command and asks the navigation system to cancel its goal. That is a
software request travelling over a network, through a browser, a bridge and a controller. If any
part of that chain has failed — which is exactly the situation in which you reach for an emergency
stop — pressing it may do nothing at all.

The **physical emergency stop** is a mechanical device that removes power. It works when software
does not. It is the one you use.

Every session, before the robot moves: **locate the physical stop and test it.**

## Before the robot moves

Every time. On real hardware.

1. Demo Mode **off**, and you have confirmed it
2. Correct robot selected
3. Connection indicator **green**
4. **Health** page shows fresh topics
5. Map and robot pose on screen **match the physical robot**
6. Conservative speed limits set
7. Operating area clear of people and obstructions
8. Physical emergency stop located and **tested**

Step 5 is the one people skip, and it is the one that causes the worst outcomes. If the robot on
screen is not the robot in the room, every command is aimed somewhere else.

## While it is moving

- **Someone watches the robot**, not the screen. The screen shows what the robot believes; only a
  person sees what is actually happening.
- **Stay out of its path.** Do not test whether it will stop for you.
- **Do not walk behind it while it is reversing.** Rear sensing is limited on most platforms.
- **Do not ride on it, lean on it, or use it to carry a person.** It is not designed for it.
- **Keep the area clear** of trailing cables, spills and loose objects.
- **Watch the load**, if it is carrying something. A shifting load changes how the robot handles.

## Docking is a blind manoeuvre

!!! warning
    During the docking approach the robot may be driving without obstacle checking. On this
    platform, the scanning, alignment and final approach phases publish motion commands directly
    and bypass the safety pipeline. **The robot will not stop for something that enters its path.**

    Keep the dock approach clear. Do not stand in it. Do not reach into it.

## Around the arm and lift

Where fitted:

- The arm's reach is larger than it looks. Stay outside it while it is powered.
- Never place a hand inside the arm's workspace while a program is running.
- The lift can move without the base moving. A stationary robot is not necessarily a still robot.
- Elevated mass changes stability. A robot with a raised lift tips more easily than one without.

## Batteries

- Do not charge a damaged, swollen or wet battery.
- Do not leave a charging robot unattended in an unoccupied building unless the installation was
  designed for it.
- Report any heat, smell, swelling or deformation immediately and stop using the robot.
- Follow local rules for storage and disposal. These differ by country.

## Stop and escalate immediately if

- The robot contacts a person
- The robot moves without a command
- The physical emergency stop does not stop it
- You see smoke, smell burning, or hear an unusual noise
- A battery is hot, swollen or damaged
- Any part of the structure is visibly damaged or loose

Do not restart to see whether it repeats. Report it, and record what happened.

## Reporting

Report every incident, and every near miss.

A near miss is information about a failure that has not hurt anyone yet. A site that only reports
injuries learns the same lesson at a much higher price.

Record: what happened, when, who was present, what the robot was doing, what the dashboard showed,
and what you did.

## Who is responsible

The operator is responsible for the safety of the immediate area during operation.

The deployment owner is responsible for the risk assessment, for training, for the physical
emergency stop being present and tested, and for regulatory compliance in their jurisdiction.

The platform is provided for research, education and development. Validating safety for a specific
deployment — emergency stop behaviour, watchdogs, fault handling, suitability, compliance — is the
responsibility of whoever deploys it.

## Related

[When something goes wrong](when-something-goes-wrong.md) ·
[Working safely](../../../foundations/safety/index.md) ·
[Safety limits](../../configure/safety-limits/index.md) ·
[Docking and charging](../../../foundations/navigation/docking.md)

## Next

[Maintain](../../maintain/index.md)
