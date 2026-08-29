# OpenAMRobot Documentation

Central documentation, architecture, safety, compatibility, and onboarding repository for the OpenAMRobot ecosystem.

## Purpose

This repository acts as the single source of truth for:

- system architecture
- onboarding
- hardware/software integration
- safety documentation
- interface documentation
- communication standards
- compatibility matrices
- tutorials
- troubleshooting
- contributor documentation

## Ecosystem Repositories

### Platform Software

```text
openamr-platform-sw
```

ROS 2 software, simulation, navigation, docking, drivers, perception, and bringup.

### Platform Firmware

```text
openamr-platform-fw
```

Embedded firmware, microcontroller code, low-level interfaces, and hardware communication.

### Platform Hardware

```text
openamr-platform-hw
```

CAD, chassis, electrical systems, manufacturing files, BOM lists, and mechatronics.

### Shared Interfaces

```text
openamrobot-interfaces
```

ROS 2 messages, services, actions, schemas, and interface contracts.

### User Interfaces

```text
openamrobot-ui
```

Operator UI and user-facing applications.

## Repository Structure

```text
openamrobot-docs/
├── docs/
├── assets/
├── mkdocs.yml
└── README.md
```

## Documentation Areas

### Core

- getting started
- architecture
- safety
- communication
- interfaces
- UI

### OpenAMR Platform

- software
- hardware
- firmware
- navigation
- docking

### OpenAMH Humanoid

- software
- hardware
- firmware

## Documentation Principles

Documentation should be:

- contributor-friendly
- beginner-accessible
- technically precise
- architecture-oriented
- version-aware
- maintainable
- reusable

## Future Scope

Planned future additions:

- compatibility matrices
- deployment guides
- manufacturing workflows
- calibration procedures
- CI/CD documentation
- fleet management
- API references
- educational materials

## License

Documentation license to be finalized.

Expected future direction:

- documentation: CC-BY-SA-4.0
- technical assets: MIT where applicable

## Ownership, licensing, and contributions

OpenAMRobot is a project initiated, operated, and controlled by **Botshare LTD** (Cyprus Company ID HE479056). Botshare LTD owns the transferable economic rights in original OpenAMRobot material created by or validly assigned to it. Third-party material remains subject to its respective ownership, licences, and notices.

Original OpenAMRobot software and firmware are licensed under MIT, documentation under CC BY 4.0, and hardware design source under CERN-OHL-P-2.0, as mapped in [`LICENSING.md`](LICENSING.md). Public distribution grants the permissions stated in the applicable licence; it does not transfer ownership of underlying copyright, trademarks, patents, or other intellectual property.

Accepted external contributions require DCO sign-off and an applicable Individual or Corporate Contributor Agreement. See the organization [IP Policy](https://github.com/openAMRobot/.github/blob/main/IP_POLICY.md), [Contribution Guide](https://github.com/openAMRobot/.github/blob/main/CONTRIBUTING.md), and [Contributor Agreement Process](https://github.com/openAMRobot/.github/blob/main/CLA.md).
