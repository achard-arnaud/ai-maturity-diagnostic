"""Epic 14 S01: SearchRequest / EvidenceCandidate acquisition contract.

Pure, dependency-free shapes and functions -- no storage, no network
(mirrors app/research_policy.py's and app/signal_policy.py's established
convention). Encodes ADR-011 (docs/ADR-011-evidence-acquisition-search.md):
a harvested `search-social-networks` Result becomes an EvidenceCandidate
only through here, with provenance validated before the candidate can
exist at all, and it can never carry a Demand/Fit/TargetPlan-readiness
field -- acquisition never directly creates Demand, Fit or authority
(Epic 14 purpose statement).

This module does not call any source adapter; app/harvest_runner.py (S02+)
is the caller that turns a real search-social-networks Result into the
inputs build_evidence_candidate() expects.
"""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping

from app.signal_policy import DEMAND_ONLY_FIELDS, compute_dedup_key

SPACES = frozenset({"discover", "research", "targets"})

# The nine search-social-networks sources this Epic wraps (ADR-011 §1).
SOURCES = frozenset(
    {"web", "linkedin", "youtube", "hackernews", "arxiv", "github", "reddit", "x", "perplexity"}
)

# Only this lane, post-Fit, may originate a Targets-space request
# (ADR-011 §6): every other source stays Discover/Research until a Fit
# decision exists.
TARGETS_SPACE_SOURCES = frozenset({"linkedin"})

# Fields unique to CanonicalFitAssessmentV1 / CanonicalTargetPlanV1
# (contracts/fit_assessment_v1.schema.yaml, contracts/target_plan_v1.schema.yaml)
# that must never appear on an EvidenceCandidate/harvested payload --
# the second half of "acquisition never directly creates Demand, Fit or
# authority" (DEMAND_ONLY_FIELDS, imported above, covers the Demand half).
FIT_OR_TARGET_ONLY_FIELDS = frozenset(
    {
        "input_lock",
        "gates",
        "coverage",
        "gaps",
        "alternatives",
        "counter_evidence",
        "score",
        "verdict",
        "fit_assessment_id",
        "target_plan_id",
    }
)

# Per ADR-011 §4: a freshly harvested, uncorroborated candidate is never
# graded/typed above these -- promotion above U1/hypothesis is a claim-
# lineage decision (app.research_policy.validate_claim_lineage), never an
# acquisition-time default.
DEFAULT_EVIDENCE_GRADE = "U1"
DEFAULT_EPISTEMIC_STATUS = "hypothesis"
_UNCORROBORATED_MAX_GRADES = frozenset({"U1", "N0"})
_UNCORROBORATED_MAX_STATUSES = frozenset({"hypothesis", "inference", "unknown"})

EXCERPT_MAX_LENGTH = 1000  # contracts/evidence_v1.schema.yaml's excerpt.maxLength


class AcquisitionPolicyError(RuntimeError):
    pass


def assert_no_demand_or_fit_fields(payload: Mapping[str, Any]) -> None:
    """Raise if a harvested/candidate payload carries any Demand-only or
    Fit/TargetPlan-only field -- acquisition never directly creates Demand,
    Fit or authority (Epic 14 purpose statement; ADR-011 §2)."""

    found = (DEMAND_ONLY_FIELDS | FIT_OR_TARGET_ONLY_FIELDS) & payload.keys()
    if found:
        raise AcquisitionPolicyError(
            f"acquisition payload carries Demand/Fit/TargetPlan-only field(s) {sorted(found)} -- "
            "search results cannot create Demand, Fit or Target readiness (Epic 14 purpose; ADR-011 S2)"
        )


@dataclass(frozen=True)
class SearchRequest:
    """A bounded request to acquire evidence for one workspace.

    `sources` must be given explicitly and non-empty: Program invariant
    "do not fan out to all sources by default" (ADR-011 S1/S3) is enforced
    here, not left to a caller's convention.
    """

    workspace_id: str
    query: str
    sources: tuple[str, ...]
    space: str
    requested_by: str
    days: int = 30
    limit: int = 10
    enrich: bool = True
    allow_commercial: bool = False
    research_case_id: str | None = None

    def __post_init__(self) -> None:
        if not self.workspace_id.strip():
            raise AcquisitionPolicyError("workspace_id is required")
        if not self.query.strip():
            raise AcquisitionPolicyError("query is required")
        if not self.requested_by.strip():
            raise AcquisitionPolicyError("requested_by is required")
        if self.space not in SPACES:
            raise AcquisitionPolicyError(f"unknown space: {self.space!r} (expected one of {sorted(SPACES)})")
        if not self.sources:
            raise AcquisitionPolicyError(
                "sources must be given explicitly and non-empty -- "
                "do not fan out to every source by default (ADR-011 S3)"
            )
        unknown = set(self.sources) - SOURCES
        if unknown:
            raise AcquisitionPolicyError(f"unknown source(s): {sorted(unknown)}")
        # ADR-011 S6: LinkedIn may only be requested from the Targets space
        # (post-Fit); every other space keeps it out entirely.
        if "linkedin" in self.sources and self.space != "targets":
            raise AcquisitionPolicyError(
                "linkedin may only be requested from space='targets' (post-Fit) -- "
                "see ADR-011 S6 Discover/Research/Targets placement"
            )
        if self.space == "targets":
            non_targets_sources = set(self.sources) - TARGETS_SPACE_SOURCES
            if non_targets_sources:
                raise AcquisitionPolicyError(
                    f"space='targets' only accepts {sorted(TARGETS_SPACE_SOURCES)}, got {sorted(non_targets_sources)}"
                )
        if self.days < 1:
            raise AcquisitionPolicyError("days must be >= 1")
        if self.limit < 1:
            raise AcquisitionPolicyError("limit must be >= 1")


@dataclass(frozen=True)
class EvidenceCandidate:
    """The mapped, not-yet-promoted shape a source adapter's raw Result
    becomes before it is written as CanonicalEvidenceV1/CanonicalSignalV1
    (ADR-011 S2). Promotion to a canonical record is a separate, explicit
    step this module does not perform.

    `source_kind` is always "public" -- every search-social-networks
    source is public-web acquisition (contracts/{evidence,signal}_v1
    .schema.yaml's `source.kind` enum), matching the same constant
    app.signal_ingestion.ingest_public already uses. `acquisition_source`
    is the specific channel (e.g. "hackernews", "linkedin") -- this is
    the field a caller filters/explains "why matched" by, not source_kind.
    """

    candidate_id: str
    workspace_id: str
    space: str
    acquisition_source: str
    source_kind: str
    locator: str
    excerpt: str
    observed_at: str
    dated_at: str | None
    evidence_grade: str
    epistemic_status: str
    entity_refs: tuple[str, ...]
    dedup_key: str
    metadata: Mapping[str, Any] = field(default_factory=dict)


def build_evidence_candidate(
    *,
    candidate_id: str,
    workspace_id: str,
    space: str,
    source_name: str,
    locator: str,
    title: str,
    snippet: str = "",
    dated_at: str | None = None,
    observed_at: str | None = None,
    entity_refs: tuple[str, ...] = (),
    evidence_grade: str = DEFAULT_EVIDENCE_GRADE,
    epistemic_status: str = DEFAULT_EPISTEMIC_STATUS,
    metadata: Mapping[str, Any] | None = None,
) -> EvidenceCandidate:
    """Map one harvested Result into an EvidenceCandidate, rejecting it if
    provenance is missing rather than silently defaulting (Epic 14 S01
    test: "missing provenance rejected").
    """

    if not workspace_id.strip():
        raise AcquisitionPolicyError("workspace_id is required")
    if space not in SPACES:
        raise AcquisitionPolicyError(f"unknown space: {space!r}")
    if source_name not in SOURCES:
        raise AcquisitionPolicyError(f"unknown source: {source_name!r}")
    if not locator.strip():
        raise AcquisitionPolicyError("a candidate requires a non-empty locator (provenance)")
    if not title.strip() and not snippet.strip():
        raise AcquisitionPolicyError("a candidate requires a non-empty title or snippet")
    if evidence_grade not in _UNCORROBORATED_MAX_GRADES:
        raise AcquisitionPolicyError(
            f"a freshly harvested candidate cannot be graded {evidence_grade!r} without prior "
            f"corroboration -- expected one of {sorted(_UNCORROBORATED_MAX_GRADES)} (ADR-011 S4)"
        )
    if epistemic_status not in _UNCORROBORATED_MAX_STATUSES:
        raise AcquisitionPolicyError(
            f"a freshly harvested candidate cannot carry epistemic_status={epistemic_status!r} -- "
            f"expected one of {sorted(_UNCORROBORATED_MAX_STATUSES)} (ADR-011 S4)"
        )

    resolved_metadata = dict(metadata or {})
    assert_no_demand_or_fit_fields(resolved_metadata)

    excerpt = " ".join(f"{title} {snippet}".split()).strip()[:EXCERPT_MAX_LENGTH]
    resolved_observed_at = observed_at or datetime.now(timezone.utc).isoformat()
    dedup_key = compute_dedup_key(source_name, locator, excerpt)

    return EvidenceCandidate(
        candidate_id=candidate_id,
        workspace_id=workspace_id,
        space=space,
        acquisition_source=source_name,
        source_kind="public",
        locator=locator,
        excerpt=excerpt,
        observed_at=resolved_observed_at,
        dated_at=dated_at,
        evidence_grade=evidence_grade,
        epistemic_status=epistemic_status,
        entity_refs=entity_refs,
        dedup_key=dedup_key,
        metadata=resolved_metadata,
    )


def candidate_to_signal(candidate: EvidenceCandidate, *, stale_after_days: int = 14) -> dict[str, Any]:
    """Map an EvidenceCandidate onto a CanonicalSignalV1-shaped dict
    (ADR-011 S6: Discover-space candidates become signals, not evidence --
    a signal has no entity_refs requirement, unlike evidence_v1's
    minItems: 1, which fits a broad, pre-Fit, not-yet-linked-to-a-company
    discovery result exactly).

    Reuses the exact source.kind/source.ref convention
    app.signal_ingestion.ingest_public already established: source.ref is
    the locator (URL), matching every other signal in this codebase,
    regardless of which acquisition_source produced it -- the specific
    channel is preserved in metadata for "why matched" purposes instead.
    """

    signal: dict[str, Any] = {
        "signal_id": f"signal_{uuid.uuid4().hex}",
        "workspace_id": candidate.workspace_id,
        "source": {"kind": candidate.source_kind, "ref": candidate.locator},
        "observed_at": candidate.observed_at,
        "status": "new",
        "company_entity_id": None,
        "dedup_key": candidate.dedup_key,
        "freshness": {"stale_after_days": stale_after_days},
        "provenance": {
            "source_refs": [candidate.locator],
            "epistemic_status": candidate.epistemic_status,
            "evidence_grade": candidate.evidence_grade,
        },
    }
    assert_no_demand_or_fit_fields(signal)
    return signal


# contracts/evidence_v1.schema.yaml's usage/license note for public-web
# acquisition -- see scripts/social_search/NOTICE.md for the underlying
# vendored source's own terms.
PUBLIC_WEB_INDEX_LICENSE = "public web index (see scripts/social_search/NOTICE.md); no purchase, no authenticated access"


def candidate_to_evidence(candidate: EvidenceCandidate, *, license: str = PUBLIC_WEB_INDEX_LICENSE) -> dict[str, Any]:
    """Map an EvidenceCandidate onto a CanonicalEvidenceV1-shaped dict
    (ADR-011 S6: Research-space candidates become evidence tied to an
    already-identified company, never Discover-space candidates -- see
    candidate_to_signal for those).

    Raises if entity_refs is empty: evidence_v1.schema.yaml requires
    entity_refs with minItems: 1 -- a candidate with no known company/
    person yet is a Discover-space signal, not evidence (ADR-011 S6);
    this function refuses to silently paper over that distinction.
    """

    if not candidate.entity_refs:
        raise AcquisitionPolicyError(
            "a candidate needs at least one entity_ref to become evidence -- "
            "an entity-less candidate is a Discover-space signal, not Research-space "
            "evidence (see candidate_to_signal, ADR-011 S6)"
        )

    if candidate.dated_at:
        evidence_type = "fact_publication"
        dated_at = candidate.dated_at
    else:
        evidence_type = "observation"
        dated_at = candidate.observed_at

    return {
        "evidence_id": f"evidence_{uuid.uuid4().hex}",
        "workspace_id": candidate.workspace_id,
        "source": {"kind": candidate.source_kind, "ref": candidate.locator},
        "locator": candidate.locator,
        "evidence_type": evidence_type,
        "dated_at": dated_at,
        "excerpt": candidate.excerpt,
        "hash": hashlib.sha256(candidate.excerpt.encode("utf-8")).hexdigest(),
        "license": license,
        "entity_refs": list(candidate.entity_refs),
        "evidence_grade": candidate.evidence_grade,
    }


_EXTERNAL_IDENTITY_ENTITY_TYPES = frozenset({"person", "company", "relationship"})


def candidate_to_external_identity_mapping(
    candidate: EvidenceCandidate,
    *,
    provider: str,
    internal_entity_type: str,
    internal_entity_id: str,
    source_evidence_id: str,
    confidence: float | None = None,
) -> dict[str, Any]:
    """Map a Targets-space candidate onto an ExternalIdentityMapping-shaped
    dict (contracts/external_identity_mapping.schema.yaml), ADR-011 S4/S6.

    `status` is not a parameter: it is always "candidate" here, by
    construction -- this function has no way to produce "validated". Per
    LI-POL-008 and the schema's own x-rule ("External identifiers are
    aliases and never replace internal IDs"), only a separate, existing
    human/primary role-validation workflow may ever move a mapping past
    "candidate"; a harvested LinkedIn hit alone never does.

    `internal_entity_id` must already exist (role_validation_request
    .schema.yaml's own x-rule: "Internal IDs are canonical and must exist
    before a connector call") -- this function does not create people,
    companies or relationships, only proposes an external alias for one
    that's already known.
    """

    if internal_entity_type not in _EXTERNAL_IDENTITY_ENTITY_TYPES:
        raise AcquisitionPolicyError(f"unknown internal_entity_type: {internal_entity_type!r}")
    if not internal_entity_id.strip():
        raise AcquisitionPolicyError("internal_entity_id is required")
    if not source_evidence_id.strip():
        raise AcquisitionPolicyError("source_evidence_id is required")
    if confidence is not None and not (0 <= confidence <= 1):
        raise AcquisitionPolicyError("confidence must be between 0 and 1")

    mapping: dict[str, Any] = {
        "mapping_id": f"idmap_{uuid.uuid4().hex}",
        "provider": provider,
        "internal_entity_type": internal_entity_type,
        "internal_entity_id": internal_entity_id,
        "external_subject_ref": candidate.locator,
        "status": "candidate",
        "observed_at": candidate.observed_at,
        "source_evidence_id": source_evidence_id,
    }
    if confidence is not None:
        mapping["confidence"] = confidence
    return mapping
