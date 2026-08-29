# OpenAMRobot Documentation

Ecosystem overview, architecture, safety, compatibility, and onboarding for OpenAMRobot.

> **Status:** Active

![OpenAMRobot ecosystem](assets/openamrobot-ecosystem.svg)

## Start here

| I want to | Go to |
| --- | --- |
| See what OpenAMRobot is | [Overview](docs/overview.md) |
| Get a working system | [openamrobot-release](https://github.com/openAMRobot/openamrobot-release) |
| Build or modify one part | The repository index below |

## Repository index

Every repository in the organization. If it is not listed here, it does not exist.

### Platform, the mobile base

| Repository | Type | Status | What it is |
| --- | --- | --- | --- |
| [openamr-platform-sw](https://github.com/openAMRobot/openamr-platform-sw) | Component | Active | ROS 2 stack: description, simulation, Nav2, docking |
| [openamr-platform-fw](https://github.com/openAMRobot/openamr-platform-fw) | Component | Active | micro-ROS motor control firmware |
| [openamr-platform-hw](https://github.com/openAMRobot/openamr-platform-hw) | Component | Active | CAD, electrical, BOM, manufacturing files |

### Upper body, the manipulator

| Repository | Type | Status | What it is |
| --- | --- | --- | --- |
| [openamr-upperbody-sw](https://github.com/openAMRobot/openamr-upperbody-sw) | Component | Planned | Arm and lift software |
| [openamr-upperbody-fw](https://github.com/openAMRobot/openamr-upperbody-fw) | Component | Planned | Lift and end-effector firmware |
| [openamr-upperbody-hw](https://github.com/openAMRobot/openamr-upperbody-hw) | Component | Planned | Lift and arm mount mechanics |
| [openamrobot-manipulation](https://github.com/openAMRobot/openamrobot-manipulation) | Component | Planned | Shared arm-integration framework |

### Shared contracts

| Repository | Type | Status | What it is |
| --- | --- | --- | --- |
| [openamrobot-interfaces](https://github.com/openAMRobot/openamrobot-interfaces) | Contract | Active | ROS 2 messages, services, actions |
| [openamrobot-comm](https://github.com/openAMRobot/openamrobot-comm) | Contract | <status> | Protocols, bridges, transports |
| [openamrobot-manifest](https://github.com/openAMRobot/openamrobot-manifest) | Contract | Active | Workspace manifest for a full checkout |

### Interfaces and releases

| Repository | Type | Status | What it is |
| --- | --- | --- | --- |
| [openamrobot-ui](https://github.com/openAMRobot/openamrobot-ui) | Component | Active | Browser dashboard |
| [openamrobot-release](https://github.com/openAMRobot/openamrobot-release) | Hub | Active | Assembled downloadable releases |
| [openamrobot-docs](https://github.com/openAMRobot/openamrobot-docs) | Hub | Active | This repository |

### Showcase and legacy

| Repository | Type | Status | What it is |
| --- | --- | --- | --- |
| [EOD-robot](https://github.com/openAMRobot/EOD-robot) | Showcase | Active | EOD proof of concept, CAD only |
| [openamr](https://github.com/openAMRobot/openamr) | Legacy | Archived | Superseded by the platform repos |
| [OpenAMR_UI_package](https://github.com/openAMRobot/OpenAMR_UI_package) | Legacy | Archived | Superseded by openamrobot-ui |
| [OpenAMR_UI_dev](https://github.com/openAMRobot/OpenAMR_UI_dev) | Legacy | Archived | Superseded by openamrobot-ui |

## Architecture

The ecosystem diagram above is the canonical copy. Other repositories embed it by
raw URL and must not keep their own copy.

| Document | Covers |
| --- | --- |
| [System architecture](docs/architecture.md) | How the repos compose into a robot |
| [Safety](docs/safety.md) | What is and is not safety rated |
| [Compatibility](docs/compatibility.md) | Versions that are known to work together |
| [Onboarding](docs/onboarding.md) | First day as a contributor |

## Documentation rules

All repositories follow [the documentation standard](docs/documentation-standard.md).
Templates: [docs/templates/](docs/templates/).

## Support

<The single canonical support and sponsorship section. Every other repository
links here instead of repeating the tables.>

## Project

MIT licensed. Maintained by Botshare Ltd.
