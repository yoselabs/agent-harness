package dokploy.traefik

# DOKPLOY TRAEFIK — routing labels and network requirements
#
# WHAT: Ensures services with Traefik routing labels have `traefik.enable=true`
# and are connected to `dokploy-network`.
#
# WHY (traefik.enable): Dokploy's traefik-ts runs with `exposedbydefault=false`.
# Without `traefik.enable=true`, the service silently gets no routes — 404 with
# no error, no warning. Agents add Traefik labels but forget `enable=true`.
#
# WHY (dokploy-network): Traefik can only route to services on its network.
# A service with correct labels but on the wrong network silently returns 502.
# Agents create internal networks but forget to also add `dokploy-network`.
#
# WITHOUT IT: Silent 404s (missing enable) or 502s (wrong network) that take
# hours to debug because the labels "look correct."
#
# FIX: Add `traefik.enable=true` to labels and `dokploy-network` to networks.
#
# Input: parsed docker-compose YAML

import rego.v1

# ── Policy: traefik.enable=true required when Traefik labels present ──

deny contains msg if {
	some svc_name, svc in input.services
	_has_traefik_routing_labels(svc)
	not _has_traefik_enable(svc)
	msg := sprintf("dokploy: service '%s' has Traefik routing labels but missing 'traefik.enable=true' — service will silently 404", [svc_name])
}

# ── Policy: dokploy-network required when Traefik labels present ──

deny contains msg if {
	some svc_name, svc in input.services
	_has_traefik_routing_labels(svc)
	not _on_dokploy_network(svc)
	msg := sprintf("dokploy: service '%s' has Traefik labels but is not on 'dokploy-network' — Traefik can't route to it (502)", [svc_name])
}

# ── Helpers ──

_has_traefik_routing_labels(svc) if {
	some label in svc.labels
	contains(label, "traefik.http.")
}

_has_traefik_enable(svc) if {
	some label in svc.labels
	label == "traefik.enable=true"
}

_on_dokploy_network(svc) if {
	some net in svc.networks
	net == "dokploy-network"
}

# Also handle networks as object (map) form
_on_dokploy_network(svc) if {
	is_object(svc.networks)
	svc.networks["dokploy-network"]
}
