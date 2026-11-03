"""Static checks on the gateway's catalog, config and compose files.

Run from the repo root: python ci/check_config.py
Exits non-zero, listing every problem, when:
- a YAML file does not parse;
- the two compose files disagree on the gateway image or the --servers list;
- an active server (--servers) is missing from mcp_catalog.yaml;
- an active server's image is not pinned by digest (@sha256:).
"""

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
COMPOSE_FILES = ("docker-compose.yaml", "docker-compose-denis.yaml")
SERVICE = "mcp_gateway"
SERVERS_FLAG = "--servers="


def load(name: str) -> object:
    with (ROOT / name).open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def gateway(compose: dict) -> tuple[str, list[str]]:
    service = compose["services"][SERVICE]
    flags = [arg for arg in service["command"] if arg.startswith(SERVERS_FLAG)]
    if len(flags) != 1:
        raise ValueError(f"expected one {SERVERS_FLAG} flag, found {len(flags)}")
    servers = [s.strip() for s in flags[0][len(SERVERS_FLAG):].split(",") if s.strip()]
    return service["image"], servers


def main() -> int:
    errors: list[str] = []

    catalog = load("mcp_catalog.yaml")
    config = load("mcp_config.yaml")
    if not isinstance(catalog, dict) or not isinstance(catalog.get("registry"), dict):
        errors.append("mcp_catalog.yaml: no top-level `registry` mapping")
        registry: dict = {}
    else:
        registry = catalog["registry"]
    if config is not None and not isinstance(config, dict):
        errors.append("mcp_config.yaml: top level must be a mapping")

    found: dict[str, tuple[str, list[str]]] = {}
    for name in COMPOSE_FILES:
        try:
            found[name] = gateway(load(name))
        except (KeyError, TypeError, ValueError) as exc:
            errors.append(f"{name}: cannot read the {SERVICE} service: {exc!r}")

    if len(found) == len(COMPOSE_FILES):
        (local_image, local_servers), (denis_image, denis_servers) = (
            found[n] for n in COMPOSE_FILES
        )
        if local_image != denis_image:
            errors.append(f"gateway image differs: {local_image} vs {denis_image}")
        if local_servers != denis_servers:
            errors.append(f"--servers differs: {local_servers} vs {denis_servers}")

    active = sorted({s for _, servers in found.values() for s in servers})
    for server in active:
        entry = registry.get(server)
        if not isinstance(entry, dict):
            errors.append(f"active server {server!r} is not in mcp_catalog.yaml")
            continue
        image = str(entry.get("image", ""))
        if "@sha256:" not in image:
            errors.append(f"active server {server!r} image is not digest-pinned: {image!r}")

    for err in errors:
        print(f"ERROR: {err}")
    if not errors:
        print(f"OK: {len(registry)} catalog entries; active servers {active} pinned by digest")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
