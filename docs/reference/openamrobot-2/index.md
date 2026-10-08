---
title: OpenAMRobot 2.0 design
tags: [builder, integrator, developer]
status: planned
description: The OpenAMRobot 2.0 development cycle in one place, hardware architecture, general arrangement, stability model, decisions taken and inputs still open.
---

<section class="oamr-hero oamr-hero--compact"><div><span class="oamr-status oamr-status--planned">Design in progress · development cycle 2</span><h1>OpenAMRobot 2.0 design</h1><p>Hardware architecture, general arrangement and stability model of the dual-arm mobile manipulator being designed between 21 September and 20 November 2026.</p><div class="oamr-actions"><a class="oamr-button oamr-button--primary" href="hardware-architecture/">Hardware architecture</a><a class="oamr-button" href="general-arrangement/">General arrangement</a><a class="oamr-button" href="mass-and-stability/">Mass and stability</a></div></div><img src="https://avatars.githubusercontent.com/u/175850144?v=4" alt="OpenAMRobot logo"></section>

**For:** builders, integrators and developers who need to know what the next robot looks like before the hardware exists.

**Canonical source:** the owning repositories listed below and the OpenAMRobot 2.0 plan set kept by the project leads. This section explains the design and records its status; it does not replace repository files, supplier evidence or the manufacturing release.

!!! warning "Design proposal, not a released robot"
    Every drawing and number in this section is a design proposal awaiting measured inputs. Nothing here is a build instruction, and no safety claim follows from a diagram being published.

## What OpenAMRobot 2.0 is

OpenAMRobot 2.0 keeps the existing differential-drive mobile platform and adds a lift column carrying two [OpenArm 2.0](https://docs.openarm.dev/) arms, an NVIDIA Jetson Orin NX compute module and an STM32-based base controller. The lift column stands on a two-position base plate and moves the shoulder between 1000 and 1350 mm above the floor.

| Area | What this section documents | Owning repository |
|---|---|---|
| Hardware architecture | Connection model of compute, base controller, drives, power, sensors and arms (public extract of BOM Issue 7) | [openamr-platform-hw](https://github.com/openAMRobot/openamr-platform-hw) (BOM to be published with the electrical release) |
| General arrangement | Upper-body layout, height stack and configuration IDs; drawings regenerated from the option B CAD | [openamr-platform-hw](https://github.com/openAMRobot/openamr-platform-hw) and [openamr-upperbody-hw](https://github.com/openAMRobot/openamr-upperbody-hw) |
| Mass and stability | The F2S stability and stopping model: mass budget, centre of gravity, tipping margins, stopping distance | [openamr-platform-hw](https://github.com/openAMRobot/openamr-platform-hw) |
| Arms and manipulation | OpenArm 2.0 integration, device packages, fake-hardware baseline | [openamrobot-manipulation](https://github.com/openAMRobot/openamrobot-manipulation) |

## Decisions recorded so far

Recorded means written in the decision addendum of the plan set (P-03); the revision is given with each decision.

| Decision | Value | Date |
|---|---|---|
| Drivetrain | Two ZLTECH ZLLG80ASM250-L-B hub motors with brakes, one ZLAC8015D V4.2 driver, 200 mm wheels | 21 September 2026 |
| Battery | One 8S1P EVE LF105 LiFePO4 pack, 25.6 V, 105 Ah, Daly 150 A BMS, 20 A charger; battery centred at 25 percent of the robot length from the rear | 28 September 2026, recorded in P-03 revision 18.2 |
| Base camera | Orbbec Gemini 336L, front mounted, tilted 10 degrees up (tilt configuration IDs `bt05`, `bt10`, `bt15`); two wrist cameras | 23 September 2026 |
| Upper-body mounting (option B) | DOLD Hexalift V4 lift column, 350 mm stroke (530 mm retracted, 880 mm extended), 240 mm side fore-aft, on a 10 mm aluminium base plate on the 294 mm deck (top face 304 mm) with two column positions, centre (`bp000`) and +50 mm (`bp050`); MISUMI HFS6-60120 arm profile, 340 mm, on a 10 mm adapter plate on the column top; OpenArm arm mount point 180 mm ahead of the column axis, y = ±31 mm | 9 October 2026, recorded in P-03 revision 18.9 item 18 |
| Shoulder height | 1000 mm at the retracted lift (304 + 530 + 166) to 1350 mm fully extended (304 + 880 + 166), at the OpenArm arm mount point; lift height is joint state, calibrated stops `L1000`, `L1175`, `L1350`; maximum assembled height 1700 mm (the robot may be lower, never higher; this is not shoulder height) | 9 October 2026, recorded in P-03 revision 18.9 item 18 |
| Head camera | Stereolabs ZED Mini on the lift carriage, lens 22 mm ahead of and 223 mm above the arm mount point, pitch 15 to 35 degrees down in 5 degree steps, baseline 25 degrees | 9 October 2026, recorded in P-03 revision 18.9 item 18 |
| Configuration IDs | Column `dold_v4_350`, `tl3_400`; base plate `bp000`, `bp050`; head pitch `hp15` to `hp35`; base tilt `bt05`, `bt10`, `bt15` | 9 October 2026, recorded in P-03 revision 18.9 item 18 |
| Speed | Command ceiling 1.5 m/s, treated as an analytical limit; the accepted operating speed follows from the stability model and the stopping tests | 28 September 2026, recorded in P-03 revision 18.2 |

## Inputs still open

- Weighed mass of the existing chassis (the model uses steel volume from CAD).
- ZLTECH data: allowable radial load per motor and the dynamic rating of the brake.
- Hub-motor bracket design and the final track.
- Supplier CAD: lift-column hole patterns, OpenArm J1_A plate outline and the orientation of the chassis deck pattern.
- The stability (F2S) rerun for option B at full lift on both base-plate positions.
- Confirmation that the arms can be supplied without the OpenArm body.

When an input closes, the page that depends on it is updated and its verification date changes.

## How to comment

Open a thread in [GitHub Discussions](https://github.com/openAMRobot/.github/discussions) or use the feedback link at the bottom of any page. Design decisions are taken by the project leads and recorded in the plan set; a merged documentation page is not itself a decision.
