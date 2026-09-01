---
title: When something goes wrong
tags: [domain-expert, beginner]
description: What to do first when the robot stops, drifts or behaves oddly.
---

# When something goes wrong


**For:** a Domain Expert, at the moment something is not right.
**Before you start:** nothing. Read this before you need it.
**When you finish:** you will know what to do first, in order, without guessing.

## Stop first, diagnose second

!!! danger "The dashboard E-STOP is not a safety device"
    The red button on screen sends one stop command over the network. It is not latched, not
    safety-rated, and it depends on the browser, the network and the robot all still working.

    **Use the validated physical emergency stop.** It must act independently of the browser and
    network to stop hazardous motion according to the system's safety design. That independence is
    why it must be accessible whenever the robot is powered.

Order of actions:

1. **Physical emergency stop**, if anyone or anything is at risk
2. **Move people away** from the robot
3. Only then start looking at screens

Nothing on this page is more important than those three lines.

## The first three checks

Once the situation is safe, almost every problem is answered by three things on screen.

### 1 · Is the connection green?

Top of the dashboard. Red means the browser has lost contact with the robot. What you see on screen
is history, not the present.

### 2 · Are the topics fresh?

Open **Health**. It lists the information streams the robot needs and how recently each arrived.

"Fresh" means arriving now. "Stale" means the robot stopped sending it. A stale scan means the robot
is navigating blind. A stale pose means the robot on screen is not the robot in the room.

!!! warning "Do not drive on stale data"
    A green connection only means the browser reached the robot's bridge. It does not mean the
    robot is publishing. Green with a frozen pose is the dangerous combination, because everything
    looks fine.

### 3 · What do the events say?

Open **Events**. It is a filterable history of what happened. Work backwards from the moment things
went wrong. The cause is usually a few entries before the symptom.

## Common situations

### The robot stopped and will not move

- Is it in an error state? Check **Status**.
- Is the goal still active, or did it fail? Check **Events**.
- Is something in front of it that it will not drive through? Look at the robot, not the screen.
- Is the battery low enough that motion is inhibited?

### The robot is somewhere it should not be

Stop it. The likely cause is a wrong pose estimate: the robot believed it was elsewhere and drove
accordingly.

Do not simply re-send the goal. Re-establish where the robot actually is first, then confirm the
map on screen matches the room.

### The map is blank

The map is not reaching the browser. The robot may still be navigating perfectly.

This is a display problem, not necessarily a robot problem — but do not drive while you cannot see
where the robot is. Report it and check
[the relay chain](../../reference/openamrobot-ui/troubleshooting.md#map-alone-is-blank-everything-else-works).

### The camera is black

Camera only. Navigation does not depend on it. Check that the right camera is selected in the
interface.

### It drove somewhere strange, then recovered

Usually localization: the robot was briefly unsure where it was, corrected, and continued. Occasional
correction is normal. Repeated correction in the same place means that part of the environment is
hard for the robot, and is worth reporting.

### A scheduled job did not run

Scheduler runs in the browser tab. If the tab was closed, the laptop slept, or the browser was
restarted, it did not run. This is by design, not a fault.

## What to record before you ask for help

Whoever helps you will ask these. Having them ready saves an hour.

- What was the robot doing when it happened?
- What did the connection indicator show?
- What did **Health** show — which topics were stale?
- What do the last entries in **Events** say?
- Has it happened before, and in the same place?
- What is the robot's software version?

A screenshot of Health and Events at the moment of failure is worth more than a paragraph of
description.

## When to stop using the robot entirely

Stop, and do not restart until someone has looked at it:

- Any contact with a person
- Any motion you did not command
- The physical emergency stop did not stop it
- Repeated unexplained behaviour in the same place
- Any visible damage, smoke, burning smell, or unusual noise
- Battery swelling, heat or damage

None of these are wait-and-see. See [Safety in daily use](safety.md).

## Related

[Daily operation](daily-operation.md) · [Reading the dashboard](reading-the-dashboard.md) ·
[Safety in daily use](safety.md) ·
[Diagnosis](../../maintain/diagnosis/index.md)

## Next

[Safety in daily use](safety.md)
