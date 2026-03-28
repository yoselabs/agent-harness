package compose.hostname

# HOSTNAME — DNS identity on shared network
#
# WHAT: Enforces that services on dokploy-network set an explicit hostname.
#
# WHY: dokploy-network is shared across all compose projects. Without hostname,
# the service has no DNS name for cross-project discovery. Other services
# can't find it reliably. If it doesn't need cross-project access, it
# shouldn't be on dokploy-network at all.
#
# WITHOUT IT: Services on the shared network are invisible to other projects.
# Cross-project HTTP calls fail because there's no stable DNS name to target.
#
# FIX: Add `hostname: <service-name>` to the service definition. If the
# service doesn't need cross-project access, move it to an internal network
# (internal: true) instead of dokploy-network.
#
# Input: parsed docker-compose YAML

import rego.v1

default _exceptions := []

_exceptions := data.exceptions if {
	data.exceptions
}

# ── Policy: services on dokploy-network must have hostname ──

deny contains msg if {
	not "compose.hostname" in _exceptions
	some name, svc in input.services
	not svc.hostname

	# Only applies to services on dokploy-network
	_on_dokploy_network(svc)

	# Skip one-shot services
	not _is_one_shot(name)

	msg := sprintf("services.%s: missing 'hostname:' — dokploy-network means exposed; set hostname (DNS contract) or move to an internal network", [name])
}

# ── Helpers ──

_on_dokploy_network(svc) if {
	some net in svc.networks
	net == "dokploy-network"
}

_on_dokploy_network(svc) if {
	is_object(svc.networks)
	svc.networks["dokploy-network"]
}

_is_one_shot(name) if {
	some _, other_svc in input.services
	deps := other_svc.depends_on
	is_object(deps)
	dep := deps[name]
	dep.condition == "service_completed_successfully"
}
