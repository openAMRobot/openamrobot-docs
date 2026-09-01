---
title: Mechanical assembly
tags: [builder]
status: experimental
description: Assemble and inspect the OpenAMRobot wheel modules using the maintained hardware procedure.
---

# Mechanical assembly

**Canonical source:** [`openamr-platform-hw/manufacturing/assembly/README.md`](https://github.com/openAMRobot/openamr-platform-hw/blob/main/manufacturing/assembly/README.md)
**Applies to:** the documented OpenAMRobot reference mobile base; verify repository revision before changing hardware or firmware.

!!! warning "Experimental project documentation"
    These instructions describe the current reference build and its measured behavior. Use physical safeguards, test with wheels clear of the floor, and revalidate after changing parts, wiring, firmware, battery chemistry, or geometry.

## 🔩 Wheel Assembly Tutorial

[![Wheel Assembly](https://img.youtube.com/vi/FlsYwoiEAsk/maxresdefault.jpg)](https://youtu.be/FlsYwoiEAsk?list=PLlQYRQ1Q-yzqA89n-1vjrnNSw8hSucCKi)

▶️ Step-by-step assembly of the OpenAMRobot drive wheel module.

The drive-wheel assembly (motor + gearbox + drive shaft + brackets, `MMP.03.*` in
[../../mechanical/](https://github.com/openAMRobot/openamr-platform-hw/blob/main/mechanical)) is assembled in the sequence shown below. Follow the same
order left and right.

**Step 1**
![Wheel assembly step 1](https://raw.githubusercontent.com/openAMRobot/openamr-platform-hw/main/manufacturing/assembly/AMR_wheel_assembly_1.png)

**Step 2**
![Wheel assembly step 2](https://raw.githubusercontent.com/openAMRobot/openamr-platform-hw/main/manufacturing/assembly/AMR_wheel_assembly_2.png)

**Step 3**
![Wheel assembly step 3](https://raw.githubusercontent.com/openAMRobot/openamr-platform-hw/main/manufacturing/assembly/AMR_wheel_assembly_3.png)

**Step 4**
![Wheel assembly step 4](https://raw.githubusercontent.com/openAMRobot/openamr-platform-hw/main/manufacturing/assembly/AMR_wheel_assembly_4.png)

**Step 5**
![Wheel assembly step 5](https://raw.githubusercontent.com/openAMRobot/openamr-platform-hw/main/manufacturing/assembly/AMR_wheel_assembly_5.png)

See the per-part production drawings (PDF/DXF) in
[../../mechanical/cad/production_files/](https://github.com/openAMRobot/openamr-platform-hw/blob/main/mechanical/cad/production_files).

## Engineering handoff

- Record the repository commit, hardware revision, supply voltage, and test configuration with every result.
- Stop if observed wiring, component labels, geometry, or topic behavior differs from this page; resolve the discrepancy in the owning repository first.
- Report documentation or implementation defects through [the repository issue tracker](https://github.com/openAMRobot/openamr-platform-hw/issues).
