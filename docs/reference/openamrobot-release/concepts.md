---
title: Release concepts
description: How OpenAMRobot product releases are built from several repositories, what is frozen, and how to read the version table.
---

<section class="oamr-hero oamr-hero--compact"><div><span class="oamr-status oamr-status--experimental">Experimental</span><h1>How releases work</h1><p>One frozen, checksummed archive for a platform that lives in many repositories.</p></div><img src="https://avatars.githubusercontent.com/u/175850144?v=4" alt="OpenAMRobot logo"></section>

## For

Anyone who needs to reproduce, study or cite a specific state of the OpenAMRobot platform, rather than the moving `main` branches.

**When you finish:** you will know what a product release contains, why component tags are only a convenience, and which versions exist and which are still planned.

**Applies to:** the process described in the [`openamrobot-release`](https://github.com/openAMRobot/openamrobot-release) repository README.

## The idea

OpenAMRobot is developed across several repositories. A GitHub source archive covers only one repository, and the archive of the release repository contains only the release builder. So the official product-level release is a custom archive, built by `openamrobot-release`, that combines the participating repositories.

According to the repository README:

- Each release is a GitHub release in `openamrobot-release`. It carries an immutable source archive of every component repository.
- A `MANIFEST.json` records the exact commit and archive checksum of each component. `checksums.sha256` covers every file.
- A published release is never edited. A correction is a new release.
- `main` in a component repository is never a release.

## Component tags are for navigation

Component repositories carry a tag with the release version, on the commit that `MANIFEST.json` records. The tags let you open a component at its release state. If a component tag and the release archive ever disagree, the archive is authoritative.

The README notes that the `v0.0.1` component tags were added on 6 October 2026, after the release, and that they point to the commits recorded in the `v0.0.1` manifest.

## Versions

| Version | Status | What it is |
| --- | --- | --- |
| `v0.0.1` | **Released** (11 July 2026) | The first public platform release: the existing robot. |
| `v2.0.0-rc.1` | **Not published** | A pre-release candidate for OpenAMRobot 2.0. The README lists it as planned for 20 November 2026. Pre-releases are published as GitHub pre-releases. |
| `v2.0.0` | **Not published** | The planned 2.0 final release, after physical integration, testing and acceptance. The README lists 18 December 2026. |

Checked on 22 November 2026: the GitHub releases list of `openamrobot-release` shows only `v0.0.1`. Planned dates can move, so the repository README and its releases page are the record, not this table.

The `v2.0.0-rc.1` candidate builder exists in the repository and builds from exact commit SHAs. Its own documentation says the candidate is dated 2026-10-19 and that final component acceptance is pending. A candidate build is evidence that sources can be reproduced. It is not evidence that the robot works or is safe.

## What a release does not prove

- A checksum detects corruption. It is not a signature and it is not approval of the release.
- Bundling source does not validate package builds, firmware, robot operation or physical safety.
- Build-time downloads of upstream dependencies are not locked by the source bundle.

## Next step

[Set up and verify a release build](setup.md), or look up the [files and outputs](reference.md).
