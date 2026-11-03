# mcp_gateway

The MCP tool gateway for [mAgenticX](../magenticx): the upstream `docker/mcp-gateway` image (dind variant) serving a curated Model Context Protocol catalog over SSE at `http://mcp_gateway:8005/sse` for magenticx's `agents` service. Active servers: `tavily`, `arxiv-mcp-server`.

| File | Purpose |
| --- | --- |
| `mcp_catalog.yaml` | Docker MCP catalog; only the ids in `--servers` run |
| `mcp_config.yaml` | Per-server config |
| `mcp_secret.example.env` | Template for the gitignored `mcp_secret.env` |
| `docker-compose.yaml` | Local — joins magenticx's `mcp_net` |
| `docker-compose-denis.yaml` | Dennis — plain Compose (Swarm can't run dind), `mcp_gateway` overlay |

## Run locally

```sh
cp mcp_secret.example.env mcp_secret.env   # fill in tavily.api_token
# start magenticx first (it creates the mcp_net network), then:
docker compose up -d
```

Gateway stuck on `Waiting for dockerd...`? `docker compose up -d --force-recreate --no-deps mcp_gateway` — a plain `docker restart` won't fix it.

Deployment on Dennis is automated by the CI/CD pipeline ([`.github/workflows/pipeline.yml`](.github/workflows/pipeline.yml)) over a locked-down SSH key; the operational runbook is kept privately.
