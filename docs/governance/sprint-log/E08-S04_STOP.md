# STOP — Epic 08 / Sprint S04

## Objective

Graph/read model buying committee. Stop condition: "projection sans new
truth" (a projection introduces no new truth) -- graph determinism.

## Outputs

- `app/buying_committee_view.py`: `build_committee_graph(stakeholders,
  influences_by_stakeholder_id)`. Pure, read-only projection over
  already-recorded StakeholderRole/Influence data -- no writes, no
  inference beyond what's in the inputs. Nodes carry only fields sourced
  directly from a stakeholder record; edges exist only where an
  Influence record's `warm_path` is set. Both nodes and edges are stably
  sorted by id, so the graph is deterministic regardless of input order.
- `tests/test_buying_committee_view.py`: 7 tests -- every stakeholder
  becomes a node, a node's fields are exactly the input's own fields (no
  fabricated field), no edge without a warm_path, an edge created and
  correctly attributed when one exists; and the Sprint's own determinism
  property across three angles (node order independent of input order,
  edge order independent of input order, repeated calls over the same
  data are byte-identical).

## Evidence

`python -m unittest tests.test_buying_committee_view -v`: 7/7 pass.
Full `python scripts/check_release.py`: 0 errors.
