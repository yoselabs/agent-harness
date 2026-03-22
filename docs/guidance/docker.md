# Docker Guidance

Non-deterministic guidance for Docker stack — reasoning behind config choices that can't be expressed as Rego policies.

Deterministic controls (hadolint, conftest Rego policies, .dockerignore template) live in `src/agent_harness/stacks/docker/`. Use `agent-harness audit` and `agent-harness lint` for enforcement.

---

## Guidance (Non-Deterministic)

Best practices that require judgment — can't be reliably linted.

### .dockerignore

Every project with a Dockerfile should have one. Without it, build context includes `.git`, `node_modules`, secrets. Template in `stacks/docker/templates.py`.

### Base image selection

- Prefer `-slim` variants (smaller, fewer vulnerabilities)
- Pin versions: `node:22-bookworm-slim`, not `node:latest`
- Multi-stage: full image for build, slim for runtime
- Alpine uses musl libc — breaks native extensions in Python, Node.js, Ruby. Go and Rust are fine.

### Named volumes

Named volumes for persistent data (databases, uploads). Bind mounts for development only.

### Dependency chains

Use `service_healthy` and `service_completed_successfully` conditions in `depends_on`.

---

## Common Mistakes (Docker)

- `COPY . .` before dep install — every build downloads all dependencies from scratch
- Missing `$$` escaping — silently corrupts passwords in compose
- No healthchecks — deployments succeed while app crashes in a loop
