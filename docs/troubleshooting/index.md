---
title: Troubleshooting
---

# Troubleshooting

Start with the owning repository’s README and issue tracker because commands, dependencies and known defects are version-specific.

For cross-component failures:

1. record the exact release or commit of every component;
2. confirm power, emergency stop and physical safety before repeating a test;
3. identify the first boundary where expected data or behavior is lost;
4. capture logs without credentials, personal data or confidential material;
5. reproduce with the smallest safe configuration; and
6. report the issue in the repository that owns the failing boundary.

Use [private security reporting](https://github.com/openAMRobot/.github/blob/main/SECURITY.md) for vulnerabilities. Do not publish credentials or exploit details.
