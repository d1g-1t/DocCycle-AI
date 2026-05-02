"""Template variable ORM model (stub — variables stored in JSONB on template_versions)."""

# Variables are stored inline in template_versions.variables JSONB column for simplicity
# and performance (no N+1, single row fetch gives all variables).
# This module exists for forward compatibility.
