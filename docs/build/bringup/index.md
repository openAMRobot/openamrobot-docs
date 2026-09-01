---
title: Bring-up
---

<section class="oamr-hero oamr-hero--compact"><div><span class="oamr-status oamr-status--planned">Hardware validation in progress</span><h1>Bring up one subsystem at a time</h1><p>Verify power, communication, motors and sensors before permitting normal robot motion.</p></div><img src="https://avatars.githubusercontent.com/u/175850144?v=4" alt="OpenAMRobot logo"></section>

## Controlled sequence

<div class="oamr-path"><span>Pre-power</span><b>→</b><span>First power</span><b>→</b><span>Motor check</span><b>→</b><span>Sensor check</span><b>→</b><span>First motion</span></div>

| Checkpoint | Continue only when |
| --- | --- |
| [Pre-power](pre-power-checklist.md) | Polarity, protection, grounding, connectors and mechanical clearances are verified |
| [First power-on](first-power-on.md) | Rails are stable, no component overheats and the system can be stopped immediately |
| [Motor and drive check](motor-check.md) | Direction, encoder feedback and commanded speed agree with the configuration |
| [Sensor check](sensor-check.md) | Expected ROS 2 topics update with plausible frames, rates and values |
| [First motion](first-motion.md) | The robot moves at reduced limits in a controlled area and stops as expected |

Record hardware revision, firmware commit, software release, robot profile and every measured result. Stop at the first unexpected state and use [common bring-up failures](common-bringup-failures.md) to collect evidence before changing multiple variables.

!!! warning "Not yet a released real-robot procedure"
    The owning software repository marks real-robot drivers and control as in progress. Treat these pages as the acceptance structure for tested contributions, not proof that every physical configuration is supported today.
