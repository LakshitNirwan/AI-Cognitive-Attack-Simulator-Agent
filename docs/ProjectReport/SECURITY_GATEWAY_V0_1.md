# AICAS in-process security gateway prototype

## Flow

`content surfaces → injected task-specific detector → deterministic policy → allowlisted action gate → JSONL audit`

Supported content surfaces remain distinct: `user_input`, `retrieved_content`, `tool_output`, and `assistant_output`. The detector returns `Finding` records carrying the original surface and task identifier. A finding is routed to `REVIEW`; the prototype does not claim calibrated confidence thresholds. Detector/input errors also route to review.

An action runs only when the decision is `ALLOW`, its name is explicitly allowlisted, an executor is present, and any required approval record passes an injected verifier. Unknown actions are blocked. The authorization record is written before the executor is invoked; execution outcome is written as a second event. If the first audit write fails, the action is not invoked.

The JSONL log includes request/event IDs, policy version, decision, reasons, hashes of supplied content/evidence, task/surface/confidence metadata, action name, and approval record ID. It does not include raw content, action parameters, or executor result.

## Security boundary and limitations

This is an in-process reference implementation, not an HTTP server. Its caller must authenticate/authorize users, supply trustworthy detector results, and provide a verifier that checks approvals against an authoritative source. The local JSONL append is not a database transaction and does not promise concurrent-writer safety, tamper evidence, retention controls, or secret scanning of action names/approval IDs. Production deployment requires those controls plus API contract, persistence, and end-to-end tests.

No ML detector is connected. Confidence values are recorded for audit only and do not drive policy. A human review workflow is not implemented; `REVIEW` prevents the action from running.
