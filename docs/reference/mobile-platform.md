# Mobile base

The OpenAMRobot mobile base is split into independently versioned software, firmware and hardware repositories.

| Layer | Owning repository | Content |
|---|---|---|
| ROS 2 software | [openamr-platform-sw](https://github.com/openAMRobot/openamr-platform-sw) | Bringup, control, navigation, docking, simulation, drivers and perception |
| Embedded firmware | [openamr-platform-fw](https://github.com/openAMRobot/openamr-platform-fw) | Microcontroller firmware and low-level hardware communication |
| Hardware source | [openamr-platform-hw](https://github.com/openAMRobot/openamr-platform-hw) | CAD, chassis, electrical design, BOM and manufacturing source |
| Operator interface | [openamrobot-ui](https://github.com/openAMRobot/openamrobot-ui) | Browser-based operation and monitoring |
| Shared contracts | [openamrobot-interfaces](https://github.com/openAMRobot/openamrobot-interfaces) | ROS 2 messages, services and actions |
| Communication boundary | [openamrobot-comm](https://github.com/openAMRobot/openamrobot-comm) | Cross-component communication contracts |

## Start with a release

Use [openamrobot-release](https://github.com/openAMRobot/openamrobot-release) when reproducing a coordinated release. Use the individual repositories when developing a component.

The owning repositories remain canonical for exact source, versions and machine-readable contracts. This knowledge hub explains how the layers work together and provides complete learning, build, operation, configuration and maintenance paths.
