# Routing table

| User intent | Owner skill | Must not route to |
|---|---|---|
| Prepare a one/two-page brief on a named external company + person + material offerings | `executive-entity-briefing` | Product ICP / opportunity matching |
| Research a target company | `enterprise-demand-intelligence` | Product matching |
| Map public decision makers or the buying committee | `enterprise-demand-intelligence` | Pilot design |
| Infer gaps from strategy, hiring, organization, and news | `enterprise-demand-intelligence` | Product ICP |
| Define or update an offer ICP | `product-icp-intelligence` | Enterprise research |
| Formalize one of the four offers | `product-icp-intelligence` | Matching |
| Compare a qualified company with one or more offers | `opportunity-fit-matching` | Fresh research |
| Score fit or apply hard gates | `opportunity-fit-matching` | Pilot design |
| Build a proof from a match | `engagement-pilot-design` | Enterprise research |
| Write cold outreach without a match artifact | Stop and route backward | Engagement design |
| Import a contact or network file | `network-contact-intake` | Enterprise research |
| Assign an ICB branch | `enterprise-icb-mapping` | Product matching |
| Prioritize companies in the network | `network-account-screening` | Product matching |
| Create or refresh studies from network changes | `network-study-orchestration` | Enterprise research content |
| Select people after a product fit | `person-opportunity-targeting` | Product ICP |
| Consolidate at least three accounts by ICB sector | `sector-intelligence-consolidation` | Contact screening |

## Collision rules

When a prompt contains a company name and a product name:

- Start with enterprise demand when the account is not qualified.
- Start with matching when the enterprise profile and product snapshot both exist.
- Start with engagement design when a match exists.

Treat a product name in a company-research prompt only as destination context. Do not use it as a hypothesis to confirm.

## ICP collisions

- “Quel est l’ICP d’Astraforge ?” -> `product-icp-intelligence`.
- “Ce compte correspond-il à l’ICP Astraforge ?” -> `opportunity-fit-matching` only when both profiles exist.
- “Trouve des comptes correspondant à l’ICP Astraforge” -> preserve the product profile, then run product-agnostic account screening; do not let enterprise research rewrite product truth.

## Stop conditions

Stop and name the missing artifact when:

- the requested owner skill lacks its required input;
- the enterprise profile contains product recommendations;
- a product snapshot contains account-specific claims;
- a selected match has a failed blocking gate.
