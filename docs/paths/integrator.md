# Integrator path

For people adapting a supported platform to a customer site, workflow or external system.

<div class="oamr-path"><span>Qualify</span><b>→</b><span>Configure</span><b>→</b><span>Validate</span><b>→</b><span>Deploy</span><b>→</b><span>Support</span></div>

1. Define the workflow, environment, safety assumptions and acceptance criteria.
2. Configure [sensors](../configure/sensors/index.md), [navigation](../configure/navigation-tuning/index.md), [docking](../configure/docking-config/index.md) and [networking](../configure/network/index.md).
3. Connect external systems through the contracts owned by `openamrobot-interfaces` and `openamrobot-comm`.
4. Run acceptance tests, record the configuration and prepare rollback and support procedures.

**Finish when:** the deployment is reproducible, versioned and accepted against explicit site criteria.
