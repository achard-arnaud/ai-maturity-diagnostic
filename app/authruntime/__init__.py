"""Auth/runtime adapter layer for ADR-007.

This package is the ONLY part of the codebase allowed to depend on
FastAPI/Starlette/Authlib. Existing plain-Python business modules under
``app/`` must never import from here, and this package must never
reimplement scoring/qualification/business logic — it only resolves
identity, workspace membership and audit trail around calls into the
existing business modules.
"""
