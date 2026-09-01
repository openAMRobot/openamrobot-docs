---
title: Configuration
tags: [builder, developer]
description: Connections, limits, security, data locations and secrets for the OpenAMRobot dashboard.
---

# openamrobot-ui · Configuration

<span class="track track-builder">Builder</span> <span class="track track-developer">Developer</span>
{: .track-row }

**For:** whoever is deploying the dashboard rather than just using it.
**Before you start:** the dashboard running, per [Set up](setup.md).
**When you finish:** connections, limits and access configured deliberately rather than by default.

## The Config page

`/config` holds connections, Demo Mode, speed limits and preferences. Most day-to-day settings live
here rather than in files.

| Setting | Effect |
|:--|:--|
| Connection profile | Which robot the dashboard talks to |
| Demo Mode | Browser-side sample data, no robot commands |
| Speed limits | Caps applied to manual driving |
| Preferences | Display and interface behaviour |

Preferences and profiles live in the browser's `localStorage`. They do not travel to another
browser or machine.

## Ports

| Port | Service | Required |
|:--|:--|:--|
| `5050` | Flask UI and REST API | Yes |
| `9090` | Rosbridge WebSocket | Yes |
| `8080` | Web video server | Only for camera streams |

A remote browser needs reachability to `5050` and `9090`.

## Security and access

!!! danger "There is no authentication"
    Only unauthenticated `AUTH_MODE=open` is implemented. **Anyone who can reach the UI and
    rosbridge ports can view data and command the robot.**

    `local` and `external` are reserved future modes. Requesting either currently falls back to
    `open` and shows a warning.

Deployment rules that follow from that:

- Keep the dashboard on a **trusted local network**
- **Do not expose** ports `5050`, `9090` or `8080` to the internet
- Use firewall rules or an authenticated reverse proxy where network isolation is not sufficient
- Do not commit `.env` files or API keys

Read the repository's `SECURITY.md` before deploying outside a private lab network.

This is a real constraint, not a formality. An open rosbridge on a routable address is a robot
anyone can drive.

## Secrets

Voice Command needs an Anthropic API key, supplied at runtime:

```bash
ANTHROPIC_API_KEY="your-key" docker compose up
```

Real `.env` files are excluded from Docker images by design. Pass secrets at runtime. Never bake a
key into an image, and never commit one.

## Nav2 parameters

The `/params` page reads and changes Nav2 parameters live. Convenient, and worth two cautions:

- A live parameter change takes effect **immediately**, on a robot that may be moving.
- Changes made here are **not persisted** to the platform's configuration files. After a restart
  the robot returns to its configured values.

Use `/params` to find a good value quickly. Then write it into the platform configuration so it
survives. See [openamr-platform-sw Configuration](../openamr-platform-sw/configuration.md).

## Data locations

| Data | Location |
|:--|:--|
| Programs, locations, history, recordings, certificates | `~/.openamr_ui/` |
| Docker backend data | Named volume `openamr_ui_data` |
| Schedules, missions, devices, profiles, metrics, preferences | Browser `localStorage` |
| Maps and routes | `ros2/src/openamr_ui_package/maps/` and `paths/` |

### Back up before you

- reinstall
- clear browser storage
- remove Docker volumes
- switch browser or machine

Browser-local data does not move by itself. This catches people who assume the dashboard is
stateless because it runs in a browser. Half of it is not.

## Fleet profiles

`/fleet` holds robot profiles and selects the active robot. Each profile carries its own connection
settings, so switching robots is a selection rather than a reconfiguration.

Profiles are browser-local. A second operator on a second laptop configures their own.

## Related

[Set up](setup.md) · [Concepts](concepts.md#where-state-lives) ·
[Security basics](../../learn/configure/network/security-basics.md)

---

**Build it:** [`openamrobot-ui`](https://github.com/openAMRobot/openamrobot-ui)
