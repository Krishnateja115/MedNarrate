# MedNarrate Admin - Runbook

## Overview
This runbook covers operational troubleshooting and incident response workflows for the MedNarrate Admin portal.

## Incident Workflow
1. **Detection:** Alerts manifest in the Command Center and Health Endpoint (`/api/v1/admin/system/health`).
2. **Support Triage:** Support agents escalate user tickets to Incidents using the Ticket Detail view.
3. **Diagnostics:** 
   - Check `AI Traces` to see if the LLM provider has failed.
   - For database issues, verify the health status in the Command Center.
4. **Mitigation:** Execute predefined tasks such as Retry/Reprocess in the `Reports` queue or fallback LLM providers in the `AI Config` panel.
5. **Resolution & Audit:** Link the mitigated incident to the original support ticket, resolving both. All these actions are automatically tracked in the `Audit Logs`.

## Break-Glass Emergency Access
When emergency access to patient PHI is required to resolve a stuck pipeline:
1. Support agent requests `SensitiveAccessGrant` via the UI.
2. Superadmin approves it in the `Security Center`.
3. Support agent can temporarily access the resource.
4. Access expires automatically or is manually revoked.

## RAG Diagnostics
If report generation is hallucinating:
1. Navigate to RAG Operations.
2. Check the indexing state of recent clinical guidelines.
3. Trigger a manual Reindex if vector stores are out of sync.
