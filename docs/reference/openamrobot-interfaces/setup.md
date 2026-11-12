---
title: Setup
---

<section class="oamr-hero oamr-hero--compact"><div><span class="oamr-status oamr-status--stable">Reference guide</span><h1>Interface setup and validation</h1><p>Use the canonical interfaces repository for package setup, verification and schema validation.</p></div><img src="https://avatars.githubusercontent.com/u/175850144?v=4" alt="OpenAMRobot logo"></section>

## For

Developers setting up or validating ROS 2 interface packages used by OpenAMRobot.

**When you finish:** you will have located the canonical setup instructions and know where to find the authoritative validation requirements.

## Canonical source

The [openAMRobot/openamrobot-interfaces repository](https://github.com/openAMRobot/openamrobot-interfaces) owns interface definitions, package versions, reviewed snapshots, schemas, fixtures and implementation history.

Follow the setup instructions in that repository for the ROS 2 distribution and package version you are using. Do not rely on copied commands or definitions in this page when the canonical instructions have changed.

## Verification

Use the canonical [interface verification guide](https://github.com/openAMRobot/openamrobot-interfaces/blob/main/docs/verification.md) for the required checks and evidence.

## Schema validation

Use the canonical [schema validation guide](https://github.com/openAMRobot/openamrobot-interfaces/blob/main/docs/schema-validation.md).

Future domain contracts must register their schemas and positive and negative fixtures in `schemas/validation.json`. If a domain does not have a schema, record its schema coverage as `NOT_APPLICABLE`; absence of a schema is not a passing validation result.

## CI status and limitations

Repository-local checks are not equivalent to full H-CI adoption. The downstream-consumer matrix, reusable workflow rollout and pinned validation environment remain separate rollout work. Do not describe this repository as fully H-CI compliant until those steps have been independently completed and evidenced.

## Contribution note

Submit changes to interface definitions, schemas, fixtures and their validation rules in [openAMRobot/openamrobot-interfaces](https://github.com/openAMRobot/openamrobot-interfaces). This page should remain a short learning-layer entry point linking to that canonical source.
