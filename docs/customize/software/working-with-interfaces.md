---
title: Working With Interfaces
---

<section class="oamr-hero oamr-hero--compact"><div><span class="oamr-status oamr-status--stable">Developer guide</span><h1>Working With Interfaces</h1><p>Consume reviewed ROS 2 interfaces without creating a second source of truth.</p></div><img src="https://avatars.githubusercontent.com/u/175850144?v=4" alt="OpenAMRobot logo"></section>

## For

Software developers integrating ROS 2 packages that exchange OpenAMRobot messages.

**When you finish:** you will know where interface definitions are maintained, how to update a consumer to a reviewed snapshot, and what to rebuild and validate after an interface change.

**Applies to:** OpenAMRobot software repositories that consume packages from `openAMRobot/openamrobot-interfaces`. Check the selected release and package metadata before applying commands; package names and versions can change.

## Canonical ownership

The [openAMRobot/openamrobot-interfaces repository](https://github.com/openAMRobot/openamrobot-interfaces) is the canonical source for interface definitions, reviewed snapshots, versions, validation fixtures and implementation history.

This documentation repository explains consumer workflows. Do not copy message definitions here or maintain an independently edited interface contract. If documentation and the canonical repository disagree, use the reviewed interface source and raise an issue to correct the documentation.

## Updating a consumer

1. Identify the interface package and release/snapshot currently used by your consumer.
2. Review the intended snapshot and its change notes in the interfaces repository. Do not update a consumer directly from an unreviewed working branch.
3. Update the consumer's dependency or vendored snapshot using the repository's documented procedure. Keep the selected version or commit traceable.
4. Rebuild affected ROS 2 packages so generated message code matches the selected definitions.
5. Run the interface repository's applicable verification and schema-validation guidance, then run the affected consumer's tests.
6. Record the interface snapshot/version and validation evidence in the consumer change.

Use the owning repository's current setup instructions rather than assuming a package manager command or directory layout.

## What requires a rebuild?

Treat changes to message fields, constants that affect generated interfaces, package metadata, or contract/package versions according to the compatibility policy in the canonical repository. In particular, a message-field change requires consumers that compile against the changed definition to update the reviewed snapshot and rebuild affected packages.

Do not infer compatibility solely from a successful documentation build. A consumer build and its relevant tests are separate evidence.

## Validation and schemas

Follow the canonical [verification guidance](https://github.com/openAMRobot/openamrobot-interfaces/blob/main/docs/verification.md) and [schema-validation guidance](https://github.com/openAMRobot/openamrobot-interfaces/blob/main/docs/schema-validation.md).

Future domain contracts must register their schemas and positive and negative fixtures in `schemas/validation.json`. Where a domain has no schema, report coverage as `NOT_APPLICABLE`; do not count missing schema coverage as a passing validation.

Repository-local checks do not by themselves complete the wider H-CI rollout. The downstream-consumer matrix, reusable workflow rollout and pinned validation environment remain separate work and must be reported independently.

## Safety and limitations

Interface documentation describes data contracts; it does not establish that a producer is deployed, that a consumer behaves correctly, or that a robot is safe to operate. Verify runtime behavior in the owning implementation and use the applicable supervised test procedure before connecting software to physical hardware.

## Contribution note

Keep this page focused on consumer guidance. Submit changes to interface definitions, versions, schemas and fixtures in [openAMRobot/openamrobot-interfaces](https://github.com/openAMRobot/openamrobot-interfaces). Use the [documentation contribution workflow](https://github.com/openAMRobot/openamrobot-docs/blob/main/CONTRIBUTING.md) for changes to this page.
