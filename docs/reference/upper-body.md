# Upper body

**Maturity: Planned and under development.**

The upper-body capability is represented by separate hardware, firmware and software repositories. It is not a separate product named “OpenAMH” in the current organization.

| Layer | Owning repository |
|---|---|
| Software | [openamr-upperbody-sw](https://github.com/openAMRobot/openamr-upperbody-sw) |
| Firmware | [openamr-upperbody-fw](https://github.com/openAMRobot/openamr-upperbody-fw) |
| Hardware | [openamr-upperbody-hw](https://github.com/openAMRobot/openamr-upperbody-hw) |
| Manipulation integration | [openamrobot-manipulation](https://github.com/openAMRobot/openamrobot-manipulation) |

These repositories currently establish component boundaries and contribution destinations. Do not infer production readiness, validated payloads or safety certification from repository existence.

!!! info "OpenAMRobot 2.0 upper body"
    Development cycle 2 replaces the lift concept with a fixed mast (top 1500 mm above the floor) carrying two OpenArm 2.0 arms at four indexed shoulder heights, 1300 to 1450 mm, installed at 1350 mm. See the [general arrangement](openamrobot-2/general-arrangement.md) and the [mass and stability model](openamrobot-2/mass-and-stability.md).
