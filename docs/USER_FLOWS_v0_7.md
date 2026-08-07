# User flows v0.7

## 1. Demand → use case → value chain

```text
Demand
-> ICB sector
-> company
-> study
-> use case
   -> Add / update use flow
   -> Analyse chaîne de valeur
   -> Explore UC graph
   -> Open organization
   -> Qualification
   -> Nudging
```

### Analyse chaîne de valeur

1. Select a canonical company UC.
2. Prepare `enterprise-value-chain-causal-analysis` with the study/inventory context.
3. Produce/refresh `05c_value_chain_causal_map.yaml`.
4. Display Porter activity chain + Ishikawa causes.
5. Display adjacent-workflow hypotheses and validation questions.
6. CTA `Valider comme use case` routes back to `enterprise-use-case-intelligence`; it never promotes automatically.

## 2. Company → organization → reach

```text
company study
-> enterprise demand
-> valid product matching
-> person targeting
-> organization/current-role validation
-> iterative reach matchmaking
-> first wave / second wave / validation only
-> engagement pilot
```

Stakeholder lanes:

- promoter / economic sponsor;
- prescriber / influencer;
- terrain owner / user;
- technical sponsor;
- veto / control.

The reach view must expose the evidence basis and missing validation for each person. Newsflow may create a `why_now` trigger but cannot upgrade fit or authority.

## 3. Offer → opportunities

```text
Offers
-> canonical shelf/profile
-> audit/update product truth
-> view studies using current or historical snapshots
-> open qualification cockpit for one study
```

No account fact is written to the canonical offer profile.

## 4. Contact → company → opportunity

```text
network contact
-> company relationship
-> current-role validation
-> company demand state
-> valid match (if any)
-> stakeholder/reach lane
```

A contact without positive fit is not an outreach target. A stale role creates a resolver CTA, not a hidden dead end.

## 5. UC graph / heritage

### Company view

- canonical company UCs;
- explicit dependencies;
- shared assets/outcomes;
- Porter adjacency;
- shared causal constraints;
- backlinks.

### Sector view

- represented companies;
- observed UC families;
- repeated assets/outcomes;
- cross-company similarity hypotheses;
- evidence scope and publication grade.

Sector similarity never writes into a company inventory.

## 6. Nudging

```text
company UC inventory
-> graph context inside the same company only
-> productivization / dependency upsell / feedback-backed cross-sell
-> human review
-> feedback recorded back in company UC inventory
```

Nudging still does not read ICB or product fit.

## 7. Blocker resolver pattern

Every blocked state renders:

```text
[Blocker]
Why: ...
Needs: ...
Resolve with: <CTA>
Expected after: ...
```

Examples:

| Blocker | CTA | Owner | Postcondition |
|---|---|---|---|
| Missing company demand evidence | Refresh demand | `enterprise-demand-intelligence` | demand profile ready |
| Missing product snapshot | Refresh product truth/snapshot | `product-icp-intelligence` | immutable snapshot exists |
| Critical fit gate OPEN | Resolve gate evidence | `opportunity-fit-matching` / human evidence | gate PASS/FAIL |
| Role stale | Validate current role | `person-opportunity-targeting` | dated role observation |
| No suitable first-wave stakeholder | Expand second round | `iterative-reach-matchmaking` | additional role hypotheses/validation queue |
| UC lacks value-chain analysis | Analyse chaîne de valeur | `enterprise-value-chain-causal-analysis` | 05c analysis exists |
| Adjacent workflow unverified | Validate as use case | `enterprise-use-case-intelligence` | evidence-backed UC or rejected hypothesis |
| Benchmark below 3 studies | Add/complete company | network/demand workflow | >=3 current complete studies |

## 8. Follow-up dashboard

The dashboard aggregates resolvers, not just statuses:

1. Qualification blockers.
2. Reach/current-role blockers.
3. Demand/UC/value-chain completeness.
4. Sector benchmark edge.
5. Nudging feedback/review.
6. Product/release TODO.

Clicking a follow-up item opens the corresponding menu and prepares the owner skill/human action with its context paths.