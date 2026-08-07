---
name: network-study-orchestration
description: Build and apply the company research and refresh queue from canonical network records. Use when a new contact batch should create company studies, when added people must propagate to their companies, when diagnostics are stale, or when high-priority screened accounts need initialization. Only orchestrate study lifecycle; do not perform company research, matching, contact targeting, or sector synthesis.
---

# Network Study Orchestration

## Responsibility

Connect network changes to versioned company studies without mixing research content into the orchestration layer.

Read [refresh-policy.md](references/refresh-policy.md) before applying the queue.

## Procedure

1. Load companies and product-agnostic screening tiers.
2. Find the newest linked study by `company_id`.
3. Queue `create` when tier A or B lacks a study.
4. Queue `refresh` when a newer contact batch affects the company or the study is stale.
5. Keep current studies `ready` and lower-priority accounts `hold`.
6. Apply only an explicitly bounded number of queue entries.

Preview:

```bash
python scripts/sync_study_queue.py
```

Apply a bounded batch:

```bash
python scripts/sync_study_queue.py --apply --limit 5
```

Write `data/private/network/study_queue.yaml` and initialize studies through `scripts/init_study.py`.
