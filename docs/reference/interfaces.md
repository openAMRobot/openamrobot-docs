# Interfaces

[openamrobot-interfaces](https://github.com/openAMRobot/openamrobot-interfaces) is the canonical repository for shared ROS 2 messages, services and actions.

Interface definitions, package versions, compatibility rules and dependency instructions must remain in that repository because they change with code. This page explains only the ecosystem boundary:

- producers and consumers depend on the shared contract rather than duplicating definitions;
- breaking interface changes require coordinated versioning and migration;
- component-specific internal messages remain with their component unless multiple repositories consume them.

See [Communication](communication.md) for the transport and integration boundary.
