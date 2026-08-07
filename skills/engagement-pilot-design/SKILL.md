---
name: engagement-pilot-design
description: Turn a validated product-fit result into a bounded commercial engagement hypothesis. Use when a matching artifact already exists and the user wants a pilot, proof of value, discovery agenda, sponsor or terrain engagement, measurable success criteria, baseline, guardrails, stop or scale criteria, economic hypothesis, or evidence-based contact angle. Do not research the company, define the product ICP, or decide product fit from scratch.
---

# Engagement Pilot Design

## Responsibility

Convert an existing fit decision into the smallest credible engagement that can prove or falsify the commercial hypothesis.

## Required input

Require `06_product_fit_matrix.yaml` whose top-level decision equals the selected match, whose weighted score is coherent, and with no failed blocker/critical gate. For `VALIDATE`, an `OPEN` gate is allowed and the output must be a discovery or validation engagement rather than a delivery pilot.

Read [pilot-policy.md](references/pilot-policy.md) for proof design. Read [contact-angle.md](references/contact-angle.md) only when outreach or a meeting angle is requested.

## Procedure

1. Restate the matched problem and evidence chain without changing the fit decision.
2. Identify sponsor, terrain owner, and veto players from existing artifacts.
3. Choose the smallest representative workflow capable of testing the hypothesis.
4. Define the baseline or reconstruction method and primary KPI.
5. Define quality, supervision, security, and full-cost guardrails.
6. Define required access, responsibilities, cadence, and escalation.
7. Define explicit `SCALE | ITERATE | STOP` criteria.
8. State the conditions that invalidate the offer.
9. Produce `07_engagement_hypothesis.md`.
10. When contact targets exist, create `07b_reach_hypotheses.yaml` from verified priorities, gaps, product evidence, and current-role validation.

## Rules

Reject a pilot that measures only activity or token use, lacks a baseline plan, excludes the terrain team, relies on cherry-picked tasks, or cannot lead to a go/no-go decision.

Use the `Roadmap Acceleration Proof` only when Astraforge was selected by the matcher. Measure flow and quality together: cycle time, throughput, rework or accepted quality, supervision effort, incidents, and full AI cost.

Use `python scripts/build_reach_hypotheses.py <study_dir>` to scaffold bounded reach records. Keep them blocked while priority claims, gap claims, product proof, or current-role validation are missing.
