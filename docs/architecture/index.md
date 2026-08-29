# Architecture

This section describes the architecture of the OpenAMRobot ecosystem and how the different hardware, software, firmware, communication, and interface components work together.

## System Overview

OpenAMRobot is designed as a modular robotics ecosystem. Individual components can be developed and maintained independently while communicating through defined interfaces.

The architecture is organized around the following areas:

- Robot platforms
- Hardware
- Firmware
- Software
- Communication
- Interfaces
- Navigation and perception
- User interfaces
- Safety systems

## Robot Platforms

### OpenAMR

OpenAMR is the autonomous mobile robot platform.

It provides the foundation for mobile robotics applications including navigation, sensing, control, communication, and autonomous operation.

[Explore the OpenAMR Platform](../openamr_platform/)

### OpenAMH

OpenAMH is the humanoid robotics platform within the OpenAMRobot ecosystem.

It combines humanoid hardware, embedded firmware, software, communication interfaces, and higher-level robot control.

[Explore OpenAMH Humanoid](../openamh_humanoid/)

## Communication

OpenAMRobot components communicate through defined protocols and interfaces so that software, firmware, and hardware modules can interact reliably.

[View Communication Documentation](../communication/)

## Interfaces

Interfaces define how OpenAMRobot components exchange commands, telemetry, sensor information, and system state.

[View Interfaces](../interfaces/)

## Safety

Safety considerations are part of the platform architecture and should be considered when designing, integrating, and operating OpenAMRobot systems.

[View Safety Documentation](../safety/)

## Next Steps

- [Getting Started](../getting_started/)
- [OpenAMR Platform](../openamr_platform/)
- [OpenAMH Humanoid](../openamh_humanoid/)
- [Communication](../communication/)
- [Interfaces](../interfaces/)
