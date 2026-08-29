# Architecture

OpenAMRobot separates implementation, contracts, releases, durable documentation and governance so each concern has one owner.

## Layers

| Layer | Owner |
|---|---|
| Mobile-base ROS 2 software | [openamr-platform-sw](https://github.com/openAMRobot/openamr-platform-sw) |
| Mobile-base firmware | [openamr-platform-fw](https://github.com/openAMRobot/openamr-platform-fw) |
| Mobile-base hardware | [openamr-platform-hw](https://github.com/openAMRobot/openamr-platform-hw) |
| Operator interface | [openamrobot-ui](https://github.com/openAMRobot/openamrobot-ui) |
| Shared ROS 2 contracts | [openamrobot-interfaces](https://github.com/openAMRobot/openamrobot-interfaces) |
| Communication boundary | [openamrobot-comm](https://github.com/openAMRobot/openamrobot-comm) |
| Upper-body components | [Upper-body overview](../upper_body/) |
| Release coordination | [openamrobot-release](https://github.com/openAMRobot/openamrobot-release) and [openamrobot-manifest](https://github.com/openAMRobot/openamrobot-manifest) |
| Governance and contribution | [openAMRobot/.github](https://github.com/openAMRobot/.github) |
| Durable conceptual documentation | [openamrobot-docs](https://github.com/openAMRobot/openamrobot-docs) |

## Ownership rule

Implementation-sensitive details stay with the component that owns them. Shared contracts stay in interface or communication repositories. Cross-repository compatibility is captured by the manifest and release repository. This site explains the relationships without duplicating commands or parameters.

See the [Documentation Standard](../DOCUMENTATION_STANDARD.md) and complete [repository index](../repositories/).

## Safety boundary

No single repository proves that an assembled robot is safe. Integrators must validate the complete configured system, including mechanical, electrical, firmware, software, communication and operator-control behavior. See [Safety](../safety/).
