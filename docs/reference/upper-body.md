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
    Development cycle 2 mounts two OpenArm 2.0 arms on a DOLD Hexalift V4 lift column (option B, P-03 revision 18.9 item 18). The column stands on a base plate with two positions, centre and +50 mm; the OpenArm arm mount point is 180 mm ahead of the column axis, and the shoulder moves from 1000 mm to 1350 mm above the floor. Configuration IDs: column `dold_v4_350` or `tl3_400`, base plate `bp000` or `bp050`, head pitch `hp15` to `hp35`, base tilt `bt05` to `bt15`. See the [general arrangement](openamrobot-2/general-arrangement.md) and the [mass and stability model](openamrobot-2/mass-and-stability.md).
