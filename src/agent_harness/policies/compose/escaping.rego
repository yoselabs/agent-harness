package compose.escaping

# DOLLAR ESCAPING — bare $ corrupts values silently
#
# WHAT: Detects bare $ in environment values that Docker Compose will
# interpolate as variable references.
#
# WHY: Docker Compose interpolates $VAR in values. A bcrypt hash like
# $2a$12$... gets silently corrupted — Compose interprets $2a as a variable
# reference and replaces it with empty string. Agents generate passwords
# and hashes without knowing about this interpolation.
#
# WITHOUT IT: Passwords silently corrupted, auth fails with no error.
# Hours of debugging because the value looks correct in the compose file
# but is mangled at runtime.
#
# FIX: Escape all literal $ as $$ in compose environment values
# (e.g., $$2a$$12$$... for bcrypt hashes).
#
# Input: parsed docker-compose YAML

import rego.v1

# ── Policy: bare $ in environment values ──

deny contains msg if {
	some name, svc in input.services
	env := svc.environment
	is_object(env)

	some key, val in env
	is_string(val)
	_has_bare_dollar(val)

	msg := sprintf("services.%s: environment.%s contains bare '$' — Docker Compose will interpolate this as a variable. Escape as '$$' if literal (e.g., bcrypt hashes, special chars).", [name, key])
}

# Also check environment as list format: ["KEY=value"]
deny contains msg if {
	some name, svc in input.services
	env := svc.environment
	is_array(env)

	some entry in env
	is_string(entry)
	contains(entry, "=")
	parts := split(entry, "=")
	key := parts[0]

	# Rejoin everything after first = (value may contain =)
	val := substring(entry, count(key) + 1, -1)
	_has_bare_dollar(val)

	msg := sprintf("services.%s: environment %s contains bare '$' — Docker Compose will interpolate this as a variable. Escape as '$$' if literal.", [name, key])
}

# True if string contains $ not followed by { or $ or end-of-string
_has_bare_dollar(s) if {
	# Match $ followed by a word character (variable interpolation pattern)
	regex.match(`\$[a-zA-Z0-9_]`, s)

	# But not already escaped as $$ or used as ${VAR}
	not regex.match(`^(\$\{|\$\$)`, s)
}
