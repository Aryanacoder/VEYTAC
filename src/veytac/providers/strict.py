"""Strict structured-output transform (TRD 7.3).

The Meta chat API with ``strict: True`` rejects Pydantic-style schemas:
every object must list ``required`` containing EVERY key in ``properties``,
``$ref``/``$defs`` are not resolved server-side, and constraining keywords
(``exclusiveMinimum``, ``default``, ``title``...) are unsupported.

``to_strict_schema`` converts a ``model_json_schema()`` dict into that
shape: refs inlined, ``required`` completed, ``additionalProperties``
forced false, unsupported keywords stripped. Pure dict function, no I/O.
"""

from __future__ import annotations

from copy import deepcopy

_ALLOWED_KEYS = frozenset({
    "type", "properties", "required", "additionalProperties",
    "items", "enum", "anyOf", "oneOf", "description",
})

_REF_PREFIX = "#/$defs/"


def _resolve(node: object, defs: dict) -> object:
    if isinstance(node, dict):
        if set(node.keys()) == {"$ref"} and isinstance(node["$ref"], str):
            target = node["$ref"]
            if target.startswith(_REF_PREFIX):
                name = target[len(_REF_PREFIX):]
                if name not in defs:
                    raise ValueError(f"unresolvable $ref: {target}")
                return _resolve(deepcopy(defs[name]), defs)
            raise ValueError(f"external $ref unsupported in strict mode: {target}")
        return {k: _resolve(v, defs) for k, v in node.items()}
    if isinstance(node, list):
        return [_resolve(v, defs) for v in node]
    return node


def _strict(node: object) -> object:
    if isinstance(node, list):
        return [_strict(v) for v in node]
    if not isinstance(node, dict):
        return node
    # `properties` maps field names to schemas: map, never keyword-filter.
    if isinstance(node.get("properties"), dict):
        props = {k: _strict(v) for k, v in node["properties"].items()}
        out: dict = {
            k: _strict(v)
            for k, v in node.items()
            if k in _ALLOWED_KEYS and k not in ("properties", "required")
        }
        out["properties"] = props
        out["required"] = sorted(props.keys())
        out["additionalProperties"] = False
        out["type"] = "object"
        return out
    out = {k: _strict(v) for k, v in node.items() if k in _ALLOWED_KEYS}
    if out.get("type") == "array" and "items" not in out:
        out["items"] = {}
    return out


def to_strict_schema(schema: dict) -> dict:
    """Convert a Pydantic JSON schema to strict structured-output shape."""
    if not isinstance(schema, dict):
        raise ValueError("schema must be a dict")
    defs = schema.get("$defs", {})
    if not isinstance(defs, dict):
        raise ValueError("$defs must be an object")
    resolved = _resolve(deepcopy(schema), defs)
    if isinstance(resolved, dict):
        resolved.pop("$defs", None)
    return _strict(resolved)  # type: ignore[return-value]


def audit_strict(schema: object, path: str = "$") -> list[str]:
    """Return violations of the strict shape (empty = compliant)."""
    problems: list[str] = []
    if isinstance(schema, dict):
        if "$ref" in schema or "$defs" in schema:
            problems.append(f"{path}: unresolved $ref/$defs")
        for k in schema:
            if k not in _ALLOWED_KEYS and k != "required":
                problems.append(f"{path}: unsupported keyword {k!r}")
        if "properties" in schema and isinstance(schema["properties"], dict):
            req = schema.get("required")
            if not isinstance(req, list) or set(req) != set(schema["properties"].keys()):
                problems.append(f"{path}: required must list every property key")
            if schema.get("additionalProperties") is not False:
                problems.append(f"{path}: additionalProperties must be false")
        for k, v in schema.items():
            if k == "properties" and isinstance(v, dict):
                # field-name map, not a schema node: audit each field schema
                for fk, fv in v.items():
                    if isinstance(fv, (dict, list)):
                        problems.extend(audit_strict(fv, f"{path}.{k}.{fk}"))
            elif isinstance(v, (dict, list)):
                problems.extend(audit_strict(v, f"{path}.{k}"))
    elif isinstance(schema, list):
        for i, v in enumerate(schema):
            problems.extend(audit_strict(v, f"{path}[{i}]"))
    return problems
