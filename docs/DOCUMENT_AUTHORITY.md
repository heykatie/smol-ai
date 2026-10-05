# Document authority

This index says which file owns a topic. It does not change account settings, connector scopes, spending, or execution authority.

`AGENTS.md` still holds the engineering rules. On 2026-10-05 that file had an unrelated uncommitted privacy edit, so this cleanup did not modify it. The hierarchy below is the maintenance map those rules already imply, plus the roadmap and archive added the same day.

| Topic | Owner |
| --- | --- |
| Release requirements and acceptance criteria | [prd.md](../prd.md) |
| MVP boundary and priority summary | [mvp_scope.md](../mvp_scope.md) |
| Reorder fixture values and screen copy | [demo_spec.md](../demo_spec.md) |
| Engineering instructions | [AGENTS.md](../AGENTS.md) |
| Security, privacy, credentials, and pending decisions | [SECURITY_AND_DECISIONS.md](SECURITY_AND_DECISIONS.md) |
| Technical gates, adapters, lifecycle, and recovery | [IMPLEMENTATION_CONTRACT.md](IMPLEMENTATION_CONTRACT.md) |
| Observed implementation status | [README.md](../README.md) and [STATUS.md](STATUS.md), then the code and tests |
| Hosting and storage direction | [ARCHITECTURE.md](ARCHITECTURE.md) |
| Visual design | [DESIGN.md](DESIGN.md) |
| Integration contracts and recorded status | [INTEGRATIONS.md](INTEGRATIONS.md) |
| Local setup and deploy checks | [DEVELOPMENT.md](DEVELOPMENT.md) |
| Product philosophy and engineering rules | [project_context.md](../project_context.md) |
| Future and post-MVP work | [ROADMAP.md](ROADMAP.md) |
| Hackathon history, sponsor presentation context, and the historical demo script | [archive/HACKATHON_CONTEXT.md](archive/HACKATHON_CONTEXT.md) |
| Historical inspection | [REVIEW.md](REVIEW.md), commit `2dc9093`, reviewed October 4, 2026 |

If a reorder number disagrees, `demo_spec.md` wins. If documents disagree about what is required, `prd.md` wins. If they disagree about what is built, the code, the tests, and the README win. `project_context.md` is vision, not evidence that a feature exists. `REVIEW.md` and the hackathon archive do not override later status. A roadmap item is not a release gate and does not grant permission.

Do not resolve a conflict by deleting a requirement. Say which owner applies and what evidence is missing.
