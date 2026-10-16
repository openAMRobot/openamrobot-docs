# Navigation Health and Faults

## Scope

Navigation status describes the navigation subsystem only. It is not a
whole-robot readiness signal or a safety function.

The canonical definitions are maintained in
[openamrobot-interfaces](https://github.com/openAMRobot/openamrobot-interfaces),
under `ros2/openamr_nav_msgs/`.

## Runtime status contract

The proposed status topic is `/navigation/status`, using `NavigationStatus`.

The producer is tracked in
[openamr-platform-sw issue #34](https://github.com/openAMRobot/openamr-platform-sw/issues/34).
The topic name and runtime behavior must be confirmed with the producer
implementation before being treated as deployed behavior.

The interface contract specifies:

- Reliable, transient-local QoS with depth 1.
- Publication on field changes and a default 2 Hz heartbeat.
- `CONTRACT_VERSION` is currently `1`.
- Message field changes require a contract version bump and consumer rebuild.
- Reason codes are append-only and must never be renumbered or reused.
- Adding a reason-code constant alone does not require a version bump.

These are contract requirements, not proof that a live producer implements them.

## Reading status safely

- `health` distinguishes unknown, OK, degraded, and fault states.
- `navigation_readiness` describes navigation only.
- `not_ready_reasons` lists reasons navigation is not ready.
- `active_reasons` lists currently active reason codes.
- `thresholds_id` is `UNSET` when no threshold profile is applied.
- A zero value is not automatically evidence of healthy operation.
- Fields documented as valid only in particular states must not be interpreted
  as meaningful outside those states.

Consult `NavigationStatus.msg` and `CONTRACT.md` for the authoritative field
definitions and validity rules.

## Reason-code registry

Reason-code constants are defined in `NavigationStatus.msg`. Do not create
a second independent registry.

| Group | Codes |
|---|---|
| General | `NONE` (0) |
| Navigation stack | `NAV_STACK_NOT_STARTED` (1001), `NAV_STACK_STARTING` (1002), `NAV_STACK_RESETTING` (1003), `NAV_NODE_INACTIVE` (1004), `NAV_CONFIG_FAULT` (1005) |
| Sensors | `SENSOR_DATA_STALE` (2001), `SENSOR_NOT_CONFIGURED` (2002), `SENSOR_NO_DATA_YET` (2003), `SENSOR_DATA_INVALID` (2004), `SENSOR_RATE_LOW` (2005) |
| Localization | `LOCALIZATION_NOT_INITIALIZED` (3001), `LOCALIZATION_UNCERTAIN` (3002), `LOCALIZATION_STALE_WHILE_MOVING` (3003), `LOCALIZATION_PAUSED_FOR_DOCKING` (3004), `TF_UNAVAILABLE` (3005) |
| Navigation task | `GOAL_OUTSIDE_MAP` (4001), `GOAL_BLOCKED` (4002), `START_BLOCKED` (4003), `NO_VALID_PATH` (4004), `PLANNER_TIMEOUT` (4005), `CONTROLLER_TIMEOUT` (4006), `STUCK` (4007), `LOCAL_BLOCKED` (4008), `NAV_UNKNOWN_FAULT` (4009) |
| Recovery | `RECOVERY_IN_PROGRESS` (5001), `RECOVERY_LIMIT_REACHED` (5002) |
| Protection | `COLLISION_LAYER_INACTIVE` (6001), `MOTION_SOURCE_UNPROTECTED` (6002), `REAR_COVERAGE_UNAVAILABLE` (6003), `PROTECTION_STATE_UNKNOWN` (6004), `SPEED_LIMIT_ACTIVE` (6005), `REVERSE_SPEED_LIMITED` (6006), `MOTION_SOURCE_PARTIALLY_PROTECTED` (6007), `COLLISION_APPROACH_ACTIVE` (6008) |
| Docking | `DOCK_ENGAGEMENT_UNKNOWN` (7001), `DOCK_TAGS_NOT_VISIBLE` (7002), `DOCK_ALIGNMENT_FAILED` (7003), `DOCK_TIMEOUT` (7004), `DOCK_STAGING_FAILED` (7005), `UNDOCK_FAILED` (7006), `UNDOCKING_BEFORE_GOAL` (7007), `DOCK_REASON_UNSPECIFIED` (7008) |
| Parking | `PARK_TARGET_UNREACHABLE` (8001), `PARK_POSE_MISSED` (8002), `PARKING_NOT_IMPLEMENTED` (8003) |
| Base/I8 | `BASE_LINK_LOST` (9001), `BASE_NOT_READY` (9002), `ESTOP_ACTIVE` (9003), `BATTERY_LOW` (9004) |

Reason-code constants identify conditions; operator-facing text and recommended
actions should be maintained consistently with the canonical registry.

## E-stop and base-controller limitations

`ESTOP_ACTIVE` is reported only when fresh base telemetry explicitly reports
an active E-stop. Missing or stale telemetry must instead be represented by
`BASE_LINK_LOST` or `BASE_NOT_READY`, with navigation readiness set to
`NAVIGATION_READINESS_NOT_READY`.

Navigation status does not actuate, reset, or validate the physical E-stop,
disable motor power, re-enable actuators, or guarantee that the robot is safe.
Those responsibilities remain with the base/I8 safety implementation.

## Traceability and known gaps

The documentation search did not locate the source text for `Use_Case_1`
requirements 3.1–3.7 or the authoritative P-02 mission-state definitions.
Their exact requirement wording and state mappings therefore remain to be
verified against the owning specification.

Do not infer that a reason code maps to a particular P-02 state without that
evidence. Add the requirement-to-interface, requirement-to-test, and
requirement-to-mission-state mappings when the authoritative source is
available.

The `/navigation/status` producer is tracked in platform issue #34.
Goal identity for checkpointing and resume is tracked in
[platform issue #38](https://github.com/openAMRobot/openamr-platform-sw/issues/38).
