# Retail and replenishment

**For:** retailers and pilot partners exploring stock movement, aisle assistance and replenishment workflows.

OpenAMRobot’s direction combines mobile navigation with a lift and arm-agnostic manipulation layer. Near-term pilots should isolate what the mobile platform can do reliably from experimental manipulation work.

<div class="oamr-grid"><article class="oamr-card"><h3>Mobile-first</h3><p>Transport, mapping, aisle navigation, named locations and task monitoring.</p></article><article class="oamr-card oamr-card--accent"><h3>Manipulation pilot</h3><p>Constrained objects, known poses, explicit workspace and human-supervised evaluation.</p></article></div>

**Try it:** the [dark-store pick simulation](../reference/openamrobot-2/dark-store-simulation.md) shows OpenAMRobot 2.0 picking a grocery order from two aisles and handing it over at a packing table, with reach and grasp checks for every shelf location. It is a visualization only; grocery requirements belong to OpenAMRobot 3.0.

**Measure:** task completion, intervention rate, cycle time, item-handling success, aisle disruption and recovery behavior.

!!! info "Pilot principle"
    Begin with one repeatable workflow and a narrow object/environment envelope. Expand only after the acceptance metric is met.
