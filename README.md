# OpenAMRobot Documentation

Central documentation, architecture, safety, compatibility, and onboarding repository for the OpenAMRobot ecosystem.

## Purpose

This repository is the canonical documentation hub for durable, cross-project guidance. Implementation-sensitive commands, interfaces, configuration, and safety requirements remain versioned in their owning repositories. See the [Documentation Standard](docs/DOCUMENTATION_STANDARD.md).

The hub covers:

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

**Status:** Active documentation hub; individual subsystem maturity is stated on its page and in its owning repository.

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

## Repository boundaries

- Exact versions, parameters, source code and interface contracts remain canonical in their owning repositories.
- This repository owns cross-project architecture, learning paths, durable explanations and the published documentation site.
- Tested commands should be linked to their owning repository instead of copied into multiple locations.

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

## Licence

Original documentation, diagrams, tutorials, and media in this repository are licensed under CC BY 4.0. Software examples and scripts are MIT; hardware source is CERN-OHL-P-2.0. See [LICENSING.md](LICENSING.md) for the controlling asset map and third-party exclusions.

## Ownership, licensing, and contributions

OpenAMRobot is a project initiated, operated, and controlled by **Botshare LTD** (Cyprus Company ID HE479056). Botshare LTD owns the transferable economic rights in original OpenAMRobot material created by or validly assigned to it. Third-party material remains subject to its respective ownership, licences, and notices.

Original OpenAMRobot software and firmware are licensed under MIT, documentation under CC BY 4.0, and hardware design source under CERN-OHL-P-2.0, as mapped in [`LICENSING.md`](LICENSING.md). Public distribution grants the permissions stated in the applicable licence; it does not transfer ownership of underlying copyright, trademarks, patents, or other intellectual property.

Accepted external contributions require DCO sign-off and an applicable Individual or Corporate Contributor Agreement. See the organization [IP Policy](https://github.com/openAMRobot/.github/blob/main/IP_POLICY.md), [Contribution Guide](https://github.com/openAMRobot/.github/blob/main/CONTRIBUTING.md), and [Contributor Agreement Process](https://github.com/openAMRobot/.github/blob/main/CLA.md).
