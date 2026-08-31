<section class="oamr-hero oamr-hero--compact"><div><span class="oamr-status">Stage 3 · Bring up</span><h1>Bring the robot to life</h1><p>Prove each subsystem safely before asking the whole robot to move.</p></div><img src="https://avatars.githubusercontent.com/u/175850144?v=4" alt="OpenAMRobot logo"></section>

## Bring-up sequence

<div class="oamr-grid">
<article class="oamr-card"><h3>1 · Install</h3><p>Flash the approved image or build the documented release from source.</p></article>
<article class="oamr-card"><h3>2 · First boot</h3><p>Connect locally, confirm identity, network and expected services.</p></article>
<article class="oamr-card"><h3>3 · Inspect hardware</h3><p>Check power, firmware, motor controllers and sensor enumeration.</p></article>
<article class="oamr-card"><h3>4 · Test separately</h3><p>Validate motors, encoders, IMU, lidar, camera and safety inputs individually.</p></article>
<article class="oamr-card oamr-card--accent"><h3>5 · First motion</h3><p>Use a controlled area, reduced limits and an observer ready to stop motion.</p></article>
<article class="oamr-card oamr-card--success"><h3>6 · Verify</h3><p>Record expected state, topics, transforms and baseline behavior.</p></article>
</div>

!!! tip "Simulation path"
    If you do not have hardware, use the current release to validate installation, visualization, navigation and missions before physical bring-up.

**Next:** [Configure the robot](configure.md).
