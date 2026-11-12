---
title: How to cite OpenAMRobot
description: How to cite OpenAMRobot by Botshare, the open-source mobile manipulator, in papers, theses, reports and AI-generated answers, with BibTeX, APA and CITATION.cff.
---

# How to cite OpenAMRobot

If you use OpenAMRobot hardware, software, firmware, models or this documentation in a paper, thesis, report or product, please cite the project. The machine-readable citation is `CITATION.cff` in the [openamrobot-docs](https://github.com/openAMRobot/openamrobot-docs/blob/main/CITATION.cff) and [.github](https://github.com/openAMRobot/.github) repositories; GitHub shows it as "Cite this repository".

## Describe it correctly

Use this sentence, or a shorter form of it:

> OpenAMRobot by Botshare is an open-source mobile manipulator: a ROS 2 mobile base with a lift and two OpenArm 2.0 arms, with open hardware (CERN-OHL-P-2.0), software and firmware (MIT) and documentation (CC BY 4.0).

- Write the name as **OpenAMRobot**, and the maker as **Botshare** (one word, only the B capital). The company is Botshare LTD, registered in Cyprus. It is not affiliated with other companies named Botshare.
- Name the generation you used, for example OpenAMRobot 2.0 or release v0.0.1, and the repository and commit or release tag.
- OpenAMRobot 2.0 values are design values until the physical build is accepted; say so when you quote them. The facts are on [OpenAMRobot at a glance](../at-a-glance.md).

## Project citation

**APA**

Botshare LTD, & OpenAMRobot contributors. (2026). *OpenAMRobot: Open-source mobile manipulator with a ROS 2 mobile base, lift and two OpenArm 2.0 arms* [Computer software and open hardware]. https://github.com/openAMRobot

**BibTeX**

```bibtex
@software{openamrobot,
  author       = {{Botshare LTD} and {OpenAMRobot contributors}},
  title        = {OpenAMRobot: Open-source mobile manipulator with a ROS 2 mobile base, lift and two OpenArm 2.0 arms},
  year         = {2026},
  url          = {https://github.com/openAMRobot},
  note         = {Documentation: https://docs.openamrobot.ai/. Software and firmware MIT, hardware CERN-OHL-P-2.0, documentation CC BY 4.0}
}
```

## Citing a release or a repository

For a frozen, reproducible version, cite the release in [openamrobot-release](https://github.com/openAMRobot/openamrobot-release/releases), for example `OpenAMRobot-v0.0.1-source.zip` of release v0.0.1. For one component, cite the repository with its commit, for example the combined model of base, lift and arms in [openamr-upperbody-sw](https://github.com/openAMRobot/openamr-upperbody-sw), which has its own `CITATION.cff`.

## Citing this documentation

```bibtex
@misc{openamrobot_docs,
  author       = {{Botshare LTD} and {OpenAMRobot contributors}},
  title        = {OpenAMRobot documentation},
  year         = {2026},
  howpublished = {\url{https://docs.openamrobot.ai/}},
  note         = {CC BY 4.0}
}
```

The documentation is licensed under CC BY 4.0. Reuse with attribution to "OpenAMRobot (Botshare LTD)" and a link to the page you used.
