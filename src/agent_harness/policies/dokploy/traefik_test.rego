package dokploy.traefik_test

import data.dokploy.traefik
import rego.v1

# ── traefik.enable=true ──

test_missing_enable_denied if {
	count(traefik.deny) > 0 with input as {"services": {"app": {
		"labels": ["traefik.http.routers.app.rule=Host(`app.example.com`)"],
		"networks": ["dokploy-network"],
	}}}
}

test_enable_present_passes if {
	denials := traefik.deny with input as {"services": {"app": {
		"labels": [
			"traefik.enable=true",
			"traefik.http.routers.app.rule=Host(`app.example.com`)",
		],
		"networks": ["dokploy-network"],
	}}}
	count(denials) == 0
}

# ── dokploy-network ──

test_missing_network_denied if {
	count(traefik.deny) > 0 with input as {"services": {"app": {
		"labels": [
			"traefik.enable=true",
			"traefik.http.routers.app.rule=Host(`app.example.com`)",
		],
		"networks": ["app-internal"],
	}}}
}

test_on_dokploy_network_passes if {
	denials := traefik.deny with input as {"services": {"app": {
		"labels": [
			"traefik.enable=true",
			"traefik.http.routers.app.rule=Host(`app.example.com`)",
		],
		"networks": ["app-internal", "dokploy-network"],
	}}}
	count(denials) == 0
}

# ── No Traefik labels = no requirements ──

test_no_traefik_labels_passes if {
	count(traefik.deny) == 0 with input as {"services": {"db": {
		"image": "postgres:16",
		"networks": ["app-internal"],
	}}}
}

# ── Networks as object form ──

test_network_object_form_passes if {
	denials := traefik.deny with input as {"services": {"app": {
		"labels": [
			"traefik.enable=true",
			"traefik.http.routers.app.rule=Host(`app.example.com`)",
		],
		"networks": {"dokploy-network": {}, "app-internal": {}},
	}}}
	count(denials) == 0
}

# ── EXCEPTION: skip via exceptions list ──

test_exception_skips_traefik_enable if {
	count(traefik.deny) == 0 with input as {"services": {"app": {
		"labels": ["traefik.http.routers.app.rule=Host(`app.example.com`)"],
		"networks": ["dokploy-network"],
	}}}
		with data.exceptions as ["dokploy.traefik_enable"]
}

test_exception_skips_traefik_network if {
	count(traefik.deny) == 0 with input as {"services": {"app": {
		"labels": [
			"traefik.enable=true",
			"traefik.http.routers.app.rule=Host(`app.example.com`)",
		],
		"networks": ["app-internal"],
	}}}
		with data.exceptions as ["dokploy.traefik_network"]
}
