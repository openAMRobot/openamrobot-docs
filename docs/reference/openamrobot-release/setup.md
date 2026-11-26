---
title: Build and verify a release
description: The steps to build and verify an OpenAMRobot release archive from the release repository, and the separate rc.1 candidate build.
---

<section class="oamr-hero oamr-hero--compact"><div><span class="oamr-status oamr-status--experimental">Experimental</span><h1>Build and verify a release</h1><p>Rebuild an archive from the release repository and check it against its checksum.</p></div><img src="https://avatars.githubusercontent.com/u/175850144?v=4" alt="OpenAMRobot logo"></section>

## For

Maintainers and reviewers who need to rebuild or independently check a release archive. If you only want to use a release, download the published archive and verify its checksum.

**When you finish:** you will have built an archive, run the validator on it, and checked its external checksum.

**Applies to:** the procedures in `RELEASE_PROCESS.md` and `RC1_RELEASE.md` of [`openamrobot-release`](https://github.com/openAMRobot/openamrobot-release). These documents change with the repository, so read the current copy before you run anything. The commands below are summarised from them and have not been run by the documentation team.

## Before you start

- Python 3.10 or newer, Git, and network access to the pinned repositories (for the rc.1 candidate).
- A clone of `openamrobot-release`.
- Nothing here touches a robot.

## Verify a downloaded release

For a published release, check the archive against its external checksum file:

```sh
sha256sum -c OpenAMRobot-v0.0.1-source.zip.sha256
```

Replace the file name with the version you downloaded. The archive also holds `MANIFEST.json` and `checksums.sha256`, which list the component commits and the checksums of the files inside.

## Build the v0.0.1 archive

`RELEASE_PROCESS.md` describes the steps:

1. Put the component ZIP archives in `input/`. The names must match `release-config.json`.
2. Review the metadata in `release-metadata/` and the version in `release-config.json`.
3. Build from the repository root:

   ```sh
   python3 scripts/build_release.py --config release-config.json --input-dir input --output-dir dist
   ```

4. Validate the result, replacing the file name with the current version:

   ```sh
   python3 scripts/validate_release.py dist/OpenAMRobot-v0.0.1-source.zip
   ```

5. Check the external checksum from inside `dist/`, then read `dist/build-report.md`.

Publishing, which means creating the tag and the GitHub release and uploading the assets, is done by the release owners and is not covered here.

## Build the rc.1 candidate

`RC1_RELEASE.md` describes a separate path with its own configuration, `release-config.rc1.json`. Every repository in its snapshot is pinned to a full commit SHA, and the source archives are locked with SHA-256. Install the requirements, run the tests, build twice into separate directories with `--fetch`, validate both outputs, and compare them byte for byte:

```sh
python -m pip install -r requirements-release.txt
python -m unittest discover -s tests -v
python scripts/build_release.py --config release-config.rc1.json --input-dir input/first --output-dir dist/first --fetch
python scripts/build_release.py --config release-config.rc1.json --input-dir input/second --output-dir dist/second --fetch
python scripts/validate_release.py dist/first/OpenAMRobot-v2.0.0-rc.1-source.zip
python scripts/validate_release.py dist/second/OpenAMRobot-v2.0.0-rc.1-source.zip
cmp dist/first/OpenAMRobot-v2.0.0-rc.1-source.zip dist/second/OpenAMRobot-v2.0.0-rc.1-source.zip
```

If a build fails on a checksum, do not update the checksum to make it pass. A changed checksum is a deliberate source-selection change that goes through review.

This path produces a **candidate**. It is not a release, and the repository says final component acceptance is pending.

## If it did not work

Read the error and the repository documents first. Missing cache entries and any checksum mismatch fail the build by design. Report problems in the [release repository issues](https://github.com/openAMRobot/openamrobot-release/issues).

## Next step

[Files, outputs and limits](reference.md).
