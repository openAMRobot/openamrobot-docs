---
title: Use
---

<section class="oamr-hero oamr-hero--compact"><div><span class="oamr-status oamr-status--experimental">Experimental operation</span><h1>Operate supported workflows safely</h1><p>Move from controlled driving and maps to locations, missions, no-code programs, demonstrations and daily monitoring.</p></div><img src="https://avatars.githubusercontent.com/u/175850144?v=4" alt="OpenAMRobot logo"></section>

## Operating areas

| Area | Use it to | Continue with |
| --- | --- | --- |
| Driving | Establish manual control and safe stop behaviour | [Driving](driving/index.md) |
| Mapping | Create and maintain the robot's spatial reference | [Mapping your space](mapping/index.md) |
| Locations | Name reusable destinations and poses | [Locations and poses](locations/index.md) |
| Missions | Combine supported steps with failure policies and run history | [Missions](missions/index.md) |
| Blockly | Build bounded workflows without writing ROS 2 code | [Programming without code](blockly/index.md) |
| Demonstration | Capture, review and evaluate task demonstrations | [Teaching by demonstration](demonstration/index.md) |
| Monitoring | Read robot state, logs and events during daily operation | [Monitoring](monitoring/index.md) |

<div class="oamr-path"><span>Inspect</span><b>→</b><span>Start</span><b>→</b><span>Run</span><b>→</b><span>Monitor</span><b>→</b><span>Recover or stop</span><b>→</b><span>Record</span></div>

The browser interface lives in [`openamrobot-ui`](https://github.com/openAMRobot/openamrobot-ui). ROS 2 navigation and docking behaviour lives in [`openamr-platform-sw`](https://github.com/openAMRobot/openamr-platform-sw).

!!! warning "Know the supported boundary"
    Verify release, robot profile, environment and safety assumptions before operation. A simulation result is not evidence that a physical deployment is safe or accepted.
