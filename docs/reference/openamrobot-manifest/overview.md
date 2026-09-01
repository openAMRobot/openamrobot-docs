---
title: openamrobot-manifest overview
---

<section class="oamr-hero oamr-hero--compact"><div><span class="oamr-status oamr-status--stable">Active</span><h1>Assemble the source workspace</h1><p>A version-aware repository manifest for checking out the OpenAMRobot ecosystem together.</p></div><img src="https://avatars.githubusercontent.com/u/175850144?v=4" alt="OpenAMRobot logo"></section>

[`openamrobot-manifest`](https://github.com/openAMRobot/openamrobot-manifest) owns the `.repos` manifest used by `vcs import`.

```bash
mkdir -p ~/oamr_ws && cd ~/oamr_ws
vcs import . < /path/to/openamrobot.repos
colcon build
```

ROS 2 packages land under `src/` and participate in the colcon build. Hardware, firmware, UI and documentation are checked out beside them and retain their own toolchains. Pin the manifest revision when reproducing a release or test result.
