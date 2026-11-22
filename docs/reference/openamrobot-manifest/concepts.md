---
title: Manifest concepts
description: How the OpenAMRobot manifest repository separates a development workspace from a pinned release snapshot.
---

<section class="oamr-hero oamr-hero--compact"><div><span class="oamr-status oamr-status--stable">Active</span><h1>Development manifest and pinned snapshot</h1><p>Two ways to check out the same ecosystem: following branches, or pinned to exact commits.</p></div><img src="https://avatars.githubusercontent.com/u/175850144?v=4" alt="OpenAMRobot logo"></section>

## For

Developers and reviewers who need to know which manifest to use, and why a pinned checkout is different from a development one.

**When you finish:** you will know the difference between `openamrobot.repos` and a release snapshot, and what a successful import does and does not show.

**Applies to:** [`openamrobot-manifest`](https://github.com/openAMRobot/openamrobot-manifest), checked against its `main` at `5b782ac` on 22 November 2026. The repository README is the record.

## Two kinds of manifest

| Manifest | Tracks | Use it for |
| --- | --- | --- |
| `openamrobot.repos` | Branches, so it can move. | Everyday development. |
| `releases/v2.0.0-rc.1.repos` | Full 40-character commit SHAs. | Reproducing a specific state of the platform. |

The development manifest "may track branches", so two checkouts made on different days can differ. The release snapshot retains the development manifest's repository URLs and checkout paths but pins every entry to an exact commit. Its checker rejects branches, tags and abbreviated hashes.

Future release versions get their own `.repos` file. A release snapshot is only updated through a reviewed pull request with explicit replacement SHAs and fresh evidence of the exact checkout.

## The rc.1 snapshot is a candidate

The `v2.0.0-rc.1` snapshot is dated 2026-10-19 and has 13 entries. The README states that it demonstrates a pinned checkout and is **not final rc.1 acceptance**. The repository's open pull requests refresh those pins, so check the repository for the current state before you rely on a date or a commit.

It agrees with the component pins in the release repository candidate, which also includes a separately pinned governance export. See [release concepts](../openamrobot-release/concepts.md).

## What an import does not prove

- `vcs import` and `colcon list` do not show that a full workspace build passes.
- Package discovery currently finds the same `openamr_ui_msgs` package under both `src/` and `ui/` (tracked as OA-08). The manifest does not hide or fix this.
- Source pins for the driver packages do not claim a reproducible binary build. The micro-ROS superbuild downloads further dependencies while it compiles.

## Next step

[Check out and validate a workspace](setup.md), or look up the [files, checks and drivers](reference.md).
