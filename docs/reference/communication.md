# Communication

[openamrobot-comm](https://github.com/openAMRobot/openamrobot-comm) owns shared communication contracts and integration boundaries. [openamrobot-interfaces](https://github.com/openAMRobot/openamrobot-interfaces) owns ROS 2 interface definitions.

Protocol versions, topic names, QoS, message schemas, ports and configuration belong in the owning repository. This site provides orientation and links rather than copying those values.

When adding a communication mechanism, document:

1. the owning repository;
2. producers and consumers;
3. trust and network boundary;
4. failure behavior and safety impact; and
5. the versioned contract used by both ends.
