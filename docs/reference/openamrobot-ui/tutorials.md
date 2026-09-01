---
title: Tutorials
tags: [beginner, builder, developer]
description: Three worked tasks in the OpenAMRobot dashboard, starting with no robot at all.
---

# openamrobot-ui · Tutorials


**For:** anyone with the dashboard open.
**Before you start:** [Set up](setup.md), Demo Mode is enough for tutorials 1 and 2.
**When you finish:** you will have explored the interface, built a visual program, and understood the relay chain.

---

## Tutorial 1 · Learn the interface without a robot

**Time:** 20 minutes. **Needs:** Demo Mode only. **Risk:** none.

```bash
docker compose up --build
```

Open `http://127.0.0.1:5050/`, choose **Explore without a robot**, and confirm the purple banner.

Visit these five pages in order and answer the question for each:

| Page | Question to answer |
|:--|:--|
| Map `/` | Where is the robot, and what do the joystick controls do? |
| Health `/health` | Which topics does the robot need, and what does "fresh" mean? |
| Status `/info` | What is the battery doing, and where is the camera feed? |
| Programs `/blocks` | What blocks exist, and what can they command? |
| Config `/config` | Where is Demo Mode, and where are speed limits? |

**Why this order.** Map is where you will spend your time. Health is what you check before you
trust anything. Config is where you turn Demo Mode off, and you should know where it is before you
need it.

**Verify:** you can find Demo Mode, the speed limits and the connection indicator without hunting.

---

## Tutorial 2 · Build your first visual program

**Time:** 20 minutes. **Needs:** Demo Mode. **Risk:** none.

Open `/blocks`.

1. Build a short program: move to a named location, wait, return.
2. Run it and watch the execution highlight move through the blocks.
3. Break it deliberately — reference a location that does not exist — and read the failure message.

**What to look for.** The failure message. A good visual programming environment tells a
non-programmer what went wrong in language they can act on. Note whether it does. That judgement is
directly useful: it is exactly the feedback that improves the Programs page for the people it is
built for.

**Verify:** the program runs to completion in Demo Mode, and you can explain what each block did.

---

## Tutorial 3 · Follow a value from the robot to the screen

**Time:** 30 minutes. **Needs:** a running simulation or robot, and a terminal. **Risk:** none, read-only.

This is the tutorial that makes the architecture concrete.

Start the simulation, then the UI. In a sourced terminal:

```bash
# 1 · The source topic
ros2 topic hz /map
ros2 topic info /map --verbose      # note the QoS durability

# 2 · The relayed topic the browser actually reads
ros2 topic hz /ui/map
ros2 topic info /ui/map --verbose   # note the different QoS

# 3 · The relay node doing the translation
ros2 node list | grep relay
```

Now open `/health` in the dashboard and find the same topics listed with their freshness.

**What you have just proved.** The browser does not read `/map`. It reads `/ui/map`, which exists
because the QoS profile on `/map` is not one a browser negotiates reliably. The relay is not
decoration; it is the reason the map appears at all.

**Then break it.** Stop the relay node and watch the map page go blank while `/map` continues
publishing perfectly. That is the exact symptom in the troubleshooting table, and now you know why.

**Verify:** you can state which topic the browser subscribes to, and what happens when the relay
stops.

---

## Where to go next

| Interest | Next |
|:--|:--|
| Operating the robot properly | [Use](../../use/index.md) |
| The architecture | [Concepts](concepts.md) |
| Deploying it | [Configuration](configuration.md) |
| The repository's own lessons | [Lessons 00–13](https://github.com/openAMRobot/openamrobot-ui/blob/main/docs/lessons/README.md) |

---

**Build it:** [`openamrobot-ui`](https://github.com/openAMRobot/openamrobot-ui)
