<section class="oamr-hero oamr-hero--compact"><div><span class="oamr-status">Stage 2 · Build</span><h1>Build the platform</h1><p>Move from parts and source files to an inspected, wired and documented robot.</p></div><img src="https://avatars.githubusercontent.com/u/175850144?v=4" alt="OpenAMRobot logo"></section>

<div class="oamr-path"><span>Prepare</span><b>→</b><span>Inventory</span><b>→</b><span>Assemble</span><b>→</b><span>Wire</span><b>→</b><span>Install</span><b>→</b><span>Inspect</span></div>

## Numbered build path

| Step | Work package | Verification |
| ---: | --- | --- |
| 00 | Tools, workspace and safety | Workspace and PPE ready |
| 01 | Kit contents and BOM | Every required item identified |
| 02 | Chassis | Frame square, fasteners torqued |
| 03 | Drive units | Free rotation and correct mounting |
| 04 | Power and battery | Polarity and protection verified |
| 05 | Compute and wiring | Harness inspected and labelled |
| 06 | Sensors | Mounting, orientation and connections verified |
| 07 | Lift | Travel and limits mechanically checked |
| 08 | Arm mounting | Interface and stability accepted |
| 09 | First power-on | No fault, heat or unexpected motion |
| 10 | Acceptance | Baseline recorded and build documented |

!!! warning "Hardware documentation gate"
    Build only against the BOM, drawings and release that match each other. Never infer power wiring from a photograph.

**Sources:** [hardware repository](https://github.com/openAMRobot/openamr-platform-hw) · [release repository](https://github.com/openAMRobot/openamrobot-release)
