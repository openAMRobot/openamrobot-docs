---
title: Release reference
description: The files, build outputs and known limits of the OpenAMRobot release repository.
---

<section class="oamr-hero oamr-hero--compact"><div><span class="oamr-status oamr-status--experimental">Experimental</span><h1>Release reference</h1><p>What is in the release repository, what a build produces, and what it does not claim.</p></div><img src="https://avatars.githubusercontent.com/u/175850144?v=4" alt="OpenAMRobot logo"></section>

## For

Readers who need to know where a release fact is recorded.

**Applies to:** [`openamrobot-release`](https://github.com/openAMRobot/openamrobot-release), checked against its `main` at `a8f60f6` on 22 November 2026. The repository, not this page, is authoritative.

## Repository files

| File or directory | Purpose |
| --- | --- |
| `README.md` | How releases work, the version table and the included repositories. |
| `RELEASE_PROCESS.md` | The steps to build, validate and publish a release. |
| `RC1_RELEASE.md` | The SHA-pinned rc.1 candidate build procedure. |
| `release-config.json` | The v0.0.1 build configuration. |
| `release-config.rc1.json` | The rc.1 candidate configuration, with pinned SHAs and source checksums. |
| `manifests/` | Release-local snapshots of the component repositories. |
| `release-metadata/` | The release notes, known limitations and scope documents that go into a release. |
| `scripts/build_release.py`, `scripts/validate_release.py` | The builder and the validator. |
| `docs/navigation-install.md` | The navigation install gate. Its test configuration is a navigation-only fixture, not a product release configuration. |
| `STATE.md` | The working state of the builder, for maintainers. |

## Build outputs

A v0.0.1 build is described as producing:

| Output | Meaning |
| --- | --- |
| `OpenAMRobot-vX.Y.Z-source.zip` | The product archive. |
| `OpenAMRobot-vX.Y.Z-source.zip.sha256` | The external checksum of the archive. |
| `OpenAMRobot-vX.Y.Z-inventory.csv` | The inventory of what the archive contains. |
| `build-report.md` | The report of the build. |

Inside an rc.1 archive, the repository documents the component checkout paths, `release.repos`, `MANIFEST.json` (repository URLs, SHAs and source hashes) and `checksums.sha256` for every other file.

## Files to read in a release

`RELEASE_NOTES.md` for scope, and `KNOWN_LIMITATIONS.md` for unsupported or incomplete behaviour. Read both before relying on a release.

## Limits

- Checksums detect corruption. They are not a cryptographic signature or proof of approval.
- Source bundling does not validate builds, firmware, robot operation, physical safety or release readiness.
- Upstream build-time downloads are not locked by the source bundle.
- Submodules fail explicitly until they are represented by separate pinned entries.
- A published release is never edited. A correction is a new release.

## See also

[Concepts](concepts.md), [Build and verify](setup.md), and the [repository index](../repositories.md).
