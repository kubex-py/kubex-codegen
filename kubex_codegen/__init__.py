"""Kubernetes OpenAPI -> Pydantic v2 code generator for kubex.

Emits the `kubex-k8s-1-NN` distribution package for one Kubernetes version,
with Pydantic models that plug into the `kubex_core.models.*` base types.
The CLI entry point is `kubex_codegen.__main__` (the `kubex-codegen` command).
"""
