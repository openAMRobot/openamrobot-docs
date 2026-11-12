# Navigation Health and Faults

## For

Developers integrating navigation status into monitoring, mission orchestration or operator-facing software.

**When you finish:** you will know where the navigation-health contract is defined, how to interpret its scope, and which implementation details still require runtime confirmation.

**Applies to:** the navigation-health interface described by the current reviewed snapshot in [openAMRobot/openamrobot-interfaces](https://github.com/openAMRobot/openamrobot-interfaces). Confirm the selected snapshot before implementation.

## Scope and safety boundary

Navigation status describes the navigation subsystem only. It is not a whole-robot readiness signal and is not a safety function. It does not implement manipulation, physical E-stop recovery, bimanual capture or the operator panel.

The canonical message definitions, reason-code vocabulary, versions and compatibility rules are maintained in the interfaces repository under `ros2/openamr_nav_msgs/`. This page is a consumer-facing explanation, not a second contract registry.

## Proposed runtime integration

The interface contract describes a navigation status message intended for publication on `/navigation/status`. The producer is tracked in [openamr-platform-sw issue #34](https://github.com/openAMRobot/openamr-platform-sw/issues/34).

Treat the topic and publication behavior as contract/proposal information until the producer implementation and deployed launch configuration confirm them. Do not infer deployed behavior from the existence of a message definition.

For exact message fields, QoS, heartbeat, validity semantics, reason-code constants and compatibility/version rules, consult the reviewed `NavigationStatus.msg` and `CONTRACT.md` in the canonical interfaces repository. Avoid copying numeric constants or version values into this page; those can change and must have one authoritative home.

## Reading status safely

- Interpret navigation health and navigation readiness as navigation-subsystem information only.
- Distinguish an explicit active E-stop report from missing or stale base telemetry. A loss of telemetry is not proof that the E-stop is active or inactive.
- Treat zero-valued fields according to their validity/known-state indicators and the canonical message contract; zero is not automatically a valid measurement.
- Use reason-code meanings and operator actions from the canonical registry. Do not renumber, reuse or independently redefine reason codes.

## Verification

1. Select and record the reviewed interface snapshot used by your consumer.
2. Inspect the exact message and contract definitions in that snapshot.
3. Build the affected consumer against the selected interface package.
4. Run the canonical positive and negative fixtures and the applicable consumer tests.
5. Confirm runtime topic, message type, QoS and producer behavior against the actual launch configuration before documenting them as deployed.

See the interfaces repository's [verification guide](https://github.com/openAMRobot/openamrobot-interfaces/blob/main/docs/verification.md) and [schema-validation guide](https://github.com/openAMRobot/openamrobot-interfaces/blob/main/docs/schema-validation.md).

## Traceability still required

The exact source wording for `Use_Case_1` requirements 3.1–3.7 and the authoritative P-02 mission-state definitions have not been established in this documentation work. Do not invent requirement mappings or mission-state transitions. Keep those acceptance items open until the owning specifications are available and reviewed.

## Safety warning

Navigation status does not actuate, reset or validate the physical E-stop, disable motor power, re-enable actuators or guarantee that the robot is safe. The hardware safety chain and base-controller safety behavior remain independently owned. Follow the approved hardware operating procedure and supervised test process.

## Ownership

- Interface definitions, schemas, versions and reason-code vocabulary: [openAMRobot/openamrobot-interfaces](https://github.com/openAMRobot/openamrobot-interfaces).
- Navigation producer implementation: [openAMRobot/openamr-platform-sw](https://github.com/openAMRobot/openamr-platform-sw).
- Product/developer explanation: this documentation repository.

Keep implementation facts synchronized with their owning repositories. Report unverified behavior as unverified.
