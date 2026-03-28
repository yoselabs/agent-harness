package compose.services

# SERVICE POLICY — healthcheck, restart, port safety
#
# WHAT: Enforces healthchecks, restart policies, and safe port bindings
# on all long-running compose services.
#
# WHY (healthcheck): dokctl and Traefik depend on healthchecks to route
# traffic and detect failed deployments. Without them, load balancers
# route to dead containers and deployments report success while crashing.
# WHY (restart): Without a restart policy, crashed services stay down
# permanently. A single OOM or uncaught exception takes the service offline.
# WHY (port binding): Docker bypasses the host firewall when binding to
# 0.0.0.0. Services meant for localhost become internet-accessible.
#
# WITHOUT IT: Silent outages, permanent crashes, and accidentally exposed
# internal services.
#
# FIX: Add healthcheck: with a probe command. Add restart: unless-stopped.
# Bind ports to 127.0.0.1 instead of 0.0.0.0.
#
# Input: parsed docker-compose YAML

import rego.v1

default _exceptions := []

_exceptions := data.exceptions if {
	data.exceptions
}

# ── Policy: every long-running service must have a healthcheck ──

deny contains msg if {
	not "compose.services_healthcheck" in _exceptions
	some name, svc in input.services
	not svc.healthcheck

	# Skip one-shot services (depended on with service_completed_successfully)
	not _is_one_shot(name)

	# Only flag if it has a restart policy (indicating long-running intent)
	# or an image (indicating it's a real service, not just a config block)
	_is_long_running(svc)

	msg := sprintf("services.%s: missing 'healthcheck:' — every long-running service must have one", [name])
}

# ── Policy: every long-running service must have a restart policy ──

deny contains msg if {
	not "compose.services_restart" in _exceptions
	some name, svc in input.services
	not svc.restart

	not _is_one_shot(name)

	# Must have an image to be a real service
	svc.image

	msg := sprintf("services.%s: missing 'restart:' policy — use 'unless-stopped' for long-running services", [name])
}

# ── Policy: no 0.0.0.0 port bindings ──

deny contains msg if {
	not "compose.services_ports" in _exceptions
	some name, svc in input.services
	some port in svc.ports

	port_str := sprintf("%v", [port])
	startswith(port_str, "0.0.0.0:")

	msg := sprintf("services.%s: binds to 0.0.0.0 (%s) — Docker bypasses firewall. Bind to 127.0.0.1 or a specific interface IP", [name, port_str])
}

# ── Helpers ──

# A service is one-shot if another service depends on it with service_completed_successfully
_is_one_shot(name) if {
	some _, other_svc in input.services
	deps := other_svc.depends_on
	is_object(deps)
	dep := deps[name]
	dep.condition == "service_completed_successfully"
}

# A service is long-running if it has a restart policy or image
_is_long_running(svc) if {
	svc.restart
}

_is_long_running(svc) if {
	svc.image
}
