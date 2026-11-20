---
title: Evidence, limits and releases of the digital twin
tags: [developer, integrator]
status: experimental
description: The test evidence behind the OpenAMRobot 2.0 digital twin, how to reproduce a run, the fidelity assumptions and known limitations, and how the source pre-release and the Digital Twin release candidate differ.
---

# Evidence and limits

**For:** anyone who wants to check a twin claim, reproduce a run or decide whether a result is good enough.

**Canonical source:** the runs and records named below. This page is a guide to them, dated 20 November 2026; the
runs, the integration records and the release metadata of
[openamrobot-release](https://github.com/openAMRobot/openamrobot-release) are the record.

!!! warning "Simulation, not hardware validation"
    Every item here is development evidence at L1 to L4. No result has been checked on a bench (L5) or on the robot
    (L6).

## How to read a result

A twin result counts only with:

1. the six commits of the workspace (upperbody-sw, platform-sw, interfaces, openarm_description, openarm_ros2,
   openarm_can);
2. the run profile (`firmware_sil`, `faults`, `fast`, `fine`) and the acceptance profile (sim-oracle);
3. the engine and step;
4. the settings declared by the run (middleware, retreat option, cancellation check, seed, alignment);
5. a run ID or a file at a commit.

A result without these is a description, not evidence.

## Test evidence

| What | Run | Result | What it shows |
|---|---|---|---|
| Baseline 1, three parallel single legs, station alignment on | [44309791416](https://github.com/openAMRobot/openamr-upperbody-sw/actions/runs/44309791416), [44309804809](https://github.com/openAMRobot/openamr-upperbody-sw/actions/runs/44309804809), [44309817813](https://github.com/openAMRobot/openamr-upperbody-sw/actions/runs/44309817813) | 8/8 each; station error 2.8, 21.7, 2.6 mm | the mission completes; not strict, not consecutive |
| Two legs one after the other, scratch branch | [44470870769](https://github.com/openAMRobot/openamr-upperbody-sw/actions/runs/44470870769) | 8/8 and 8/8 | the fixes work together; before the strict gates, not acceptance |
| Diagnostic: cancellation at mission start, no-reverse configuration, forward retreat | [44735544898](https://github.com/openAMRobot/openamr-upperbody-sw/actions/runs/44735544898), [44736351073](https://github.com/openAMRobot/openamr-upperbody-sw/actions/runs/44736351073) | 7/8, 6/8 | 13 of 13 cancel checks pass; forward retreat works; odometry guard fails after the following turn |
| Diagnostic: #94, #95, #98, #99 on the integration branch, platform no-reverse candidate #178, forward retreat, cancellation at the end | [44808492353](https://github.com/openAMRobot/openamr-upperbody-sw/actions/runs/44808492353) | 8/8 phases, mission PASS; verdict failed on contact events outside the allowed list | odometry guard 0.067 m, station error 6 mm, cancel 13 of 13 at the end; a single diagnostic leg, not acceptance |
| Operator UI on the twin (#90, #50, #62 unmerged) | [44806541459](https://github.com/openAMRobot/openamrobot-ui/actions/runs/44806541459) | browser 8/8, bridge probe 11/11 | the authorised command chain from the browser; see [Operator UI](operator-ui.md) |
| MuJoCo structural and parameter parity (#97 on #104) | job 136548142270 | 2922 checks, 0 failures; 281 tests, 0 failed | the generated model matches the expansion; 21 declared deviations (issue #96) |
| Gazebo versus MuJoCo benchmark (#106) | comparison job 136550014672 | 12 of 21 metrics within tolerance | causes listed on [Simulators](simulators.md#gazebo-versus-mujoco-benchmark); the Gazebo lift row is under investigation |
| Isaac Sim CPU checks (#107) | job 136548160155 | 108 tests, 0 failed | the kit and import job; no GPU run |
| Grocery demonstration | [44299879412](https://github.com/openAMRobot/openamr-upperbody-sw/actions/runs/44299879412) | 10 of 12 checks | demonstration on older pins; odometry drift after turns |
| AI capture and conversion | [44448676604](https://github.com/openAMRobot/openamr-upperbody-sw/actions/runs/44448676604) | converted | one episode, 543 frames, four cameras; development evidence |
| Headless quick start of this handbook | `digital-twin-quickstart` workflow of openamrobot-docs | see the pull request that adds it | the documented install, build, tests, device launch and scenario 14 |

The strict two-leg acceptance on the reviewed integration heads is the release candidate's mission criterion. It has
not been run yet (20 Nov 2026). Its run ID and verdict will be recorded in the release candidate report and in `docs/integration/baseline1.md` of
openamr-upperbody-sw when it exists. Preserved artifacts of earlier runs are pre-releases of openamr-upperbody-sw
(`sim-baseline1-2026-11-18`, `sim-grocery-demo-2026-11-18`, `sim-videos-2026-11-19`,
`dev-evidence-baseline1-c9-2026-11-19`): development artifacts, not acceptance.

## Reproduce a run

On your computer: follow [Install and run](install-and-run.md) to step 5, then run the Baseline 1 command of that page.
Compare your phase table and checks with the run's job summary, not the exact numbers: Gazebo has no seed and parking
varies from run to run.

In CI, for maintainers with write access to openamr-upperbody-sw, one validation leg on the integration branch:

```bash
gh workflow run baseline1-acceptance.yml --repo openAMRobot/openamr-upperbody-sw --ref integration/baseline1 -f sequence=single
```

Not run for this page: the inputs are those of the workflow's `workflow_dispatch` section at the pinned commit, and the
runs above were started this way. `-f sequence=strict` (the default) runs the two-leg strict sequence, about 3.7 hours. Each leg uploads its bag, CAN
dumps, video, phase JSON and `declaration.json`; the verdict job prints the commits of both legs.

## Fidelity assumptions

- Signal level only: CAN frames and register values from state machines and rigid-body physics. No circuit, motor
  phase current, CAN physical layer or battery electrochemistry anywhere.
- Every emulator is a protocol and behaviour stand-in built from filed documents or proposals, not compared with a
  delivered device.
- Masses are ledger design values; friction, wheel contact, castors, camera parameters and the track are estimates or
  placeholders. The parameter register names the verification level of each.
- Object and planning poses come from ground truth (sim-oracle).

## Known limitations

| Limitation | Effect | Where tracked |
|---|---|---|
| Flat wheel collision, turn slip | heading error after in-place turns; odometry drift | fidelity record F1, F2; platform-sw #171 |
| Base pitch 0.534 deg nose down at rest, 2 mm high | planning scene and Gazebo disagree slightly | upperbody-sw [#105](https://github.com/openAMRobot/openamr-upperbody-sw/issues/105) |
| Speed limits differ per layer (Gazebo 1.0 m/s, ceiling 0.5 m/s) | stopping and acceleration differ by layer | platform-sw #173 |
| No brake, battery or power model | no hold on slopes, no voltage sag, no inrush | fidelity record F6 |
| BMS returns constants | no battery effect on the run | fidelity record F5 |
| Camera fields of view not from datasheets; wrist frames placeholders | camera data differ from the real sensors | fidelity record F3, F4 |
| STM32 is a host stand-in | no firmware evidence from the twin | [Firmware and message flow](firmware.md) |
| Real-time factor 0.13 to 0.5 on hosted runners | lift checks can be BLOCKED | scene README, Known limits |
| Docking off | no docking path in any acceptance run | `use_docking` false |
| UI command path not authorised | no manual driving from the UI | [Operator UI](operator-ui.md#operator-ui) |
| MuJoCo and Gazebo differ beyond tolerance in 9 of 21 benchmark metrics (arm sag without gravity compensation in MuJoCo, wheel servo in turns); Gazebo lift benchmark row unexplained | cross-simulator results are comparisons, not confirmations | [Simulators](simulators.md#gazebo-versus-mujoco-benchmark), issue #96 |
| No Isaac run | no Isaac evidence | [Simulators](simulators.md#isaac-sim) |

## Release and versioning

| | Source pre-release v2.0.0-rc.1 | Digital Twin release candidate |
|---|---|---|
| What | the reviewed `main` of every repository, pinned by full commit in a manifest, as a source archive | the twin as it runs: integration branches of upperbody-sw and platform-sw plus their pinned inputs |
| Contains the Build 1 scene and Baseline 1 | no (`main` of openamr-upperbody-sw has no `openamrobot_build1_scene`) | yes |
| Pins | `manifests/v2.0.0-rc.1.repos` in openamrobot-release | the six commits of the strict run, recorded in the release candidate report and in the integration snapshot of the release metadata |
| Evidence | build and test status per repository | the gates of the release candidate (model, devices and faults, mission, simulators, AI and UI, documentation) |
| Physical, electrical, safety acceptance | none | none |

The release metadata of v2.0.0-rc.1 (openamrobot-release pull request
[#18](https://github.com/openAMRobot/openamrobot-release/pull/18), open) lists the integration branches in a separate
integration snapshot, "not release content". When a reviewed integration change merges to `main`, a later source
release carries it.
