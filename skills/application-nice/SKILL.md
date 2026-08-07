---
name: application-nice
description: Analyse a job opportunity and build an evidence-led, persona-specific application or interview pack for François-Pro or Sarah-Pro. Use for job search, role and company due diligence, CV targeting, cover or recruiter messages, application portfolios, interview preparation, success profiles, candidate-role fit, or 30/60/90-day hypotheses. Always confirm the active persona before reading candidate assets. Use one shared application OS but keep François and Sarah sources, templates, examples, claims, metrics, and outputs strictly segregated.
---

# Application Nice

## Confirm and lock the persona

Before any research, file read, recommendation, or drafting, ask exactly one question: **« Cette candidature concerne-t-elle François-Pro ou Sarah-Pro ? »** Do this even when the likely persona appears obvious from context.

After confirmation, set `active_persona` to `francois-pro` or `sarah-pro` for the full run. Read only the matching persona reference and asset roots. Never load the other persona to enrich, compare, or fill a gap unless the user explicitly requests a cross-persona comparison.

- François-Pro: read [references/francois-profile.md](references/francois-profile.md); use only `assets/personas/francois/` and `assets/examples/francois/`.
- Sarah-Pro: read [references/sarah-profile.md](references/sarah-profile.md); use only `assets/personas/sarah/` and `assets/examples/sarah/`.

Read [references/common-application-os.md](references/common-application-os.md) after persona confirmation. Read [references/artifact-catalog.md](references/artifact-catalog.md) only when selecting deliverables. Read [references/source-and-asset-map.md](references/source-and-asset-map.md) before using an example or claiming that a historical file is available.

This public source package deliberately excludes private CVs, contact details, transcripts, and application binaries. Check `assets/private-assets.manifest.example.json`; if a required active-persona asset is unavailable at runtime, ask the user to attach or authorize access to that asset instead of substituting memory.

## Maintain three independent truths

Do not cross the boundaries before the matching stage:

1. **Company truth** — strategy, organization, capabilities, hiring, newsflow, culture signals, constraints, and decision system.
2. **Role truth** — mandate, success outcomes, decision rights, stakeholders, operating conditions, explicit requirements, hidden tests, and likely competing archetypes.
3. **Candidate truth** — only verified CV, portfolio, interview, recommendation, and user-confirmed evidence for the active persona.

Never rewrite company or role reality to make the candidate fit. Never strengthen a candidate claim because it would improve the application.

## Execute the application OS

1. Confirm persona and opportunity stage.
2. Capture the job description, company, geography, language, deadline, channel, and requested artifacts.
3. Research only the company and role signals capable of changing the decision or narrative.
4. Build the role success profile and identify knockout criteria, hidden tests, decision makers, and competing archetypes.
5. Match candidate evidence to outcomes, not keywords. Mark `proven | adjacent | gap | unknown`.
6. Issue `PURSUE | VALIDATE | NURTURE | DECLINE` with conditions and a falsifier.
7. Choose the smallest application pack needed for the stage.
8. Draft from the active persona source of truth; preserve voice, dates, metrics, and scope.
9. Run the board-gate review appropriate to the stage.
10. Freeze functional content, then invoke `$nice-output-engine` for visual artifacts.

Use `assets/application-case.schema.json` for the case record.

## Board-gate review

Review the application through the decision sequence, not as a generic ATS exercise:

- **Recruiter or search firm** — is the shortlist argument immediate and defensible?
- **Business or founders** — is ownership, value, judgment, and motivation credible?
- **Operations and technology** — can the candidate execute across real dependencies and constraints?
- **Board or final sponsor** — does the appointment risk remain acceptable and is the first-year mandate believable?

For each gate, record likely concern, evidence, residual risk, validation question, and narrative response. Do not manufacture confidence where evidence is missing.

## Persona segregation rules

- Prefix every case and output path with `francois` or `sarah`.
- Never copy a metric, sentence, use case, reference, template, color system, or historical example across personas.
- Treat the common OS as process only; it contains no candidate facts.
- Store new candidate evidence only under the active persona root.
- Treat historical application examples as learning material, never as current truth.
- Require explicit user confirmation before promoting a new inferred fact into a persona source of truth.

## Output quality

- Lead with an honest apply/no-apply recommendation.
- Preserve candidate positioning without pretending either persona is a developer, scientist, or another profession they have not held.
- Use achievements only with verified scope, date, and ownership.
- Prefer a short role-specific narrative to exhaustive biography.
- Expose gaps and bridge them with adjacent evidence, a validation question, or a bounded learning plan.
- Keep the CV source stable; make targeted variants, never silent replacements.
- Render only after the content, evidence, and persona checks pass.
