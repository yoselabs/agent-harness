"""Preset registry — single source of truth for all available presets."""

from agent_harness.presets.docker import DockerPreset
from agent_harness.presets.dokploy import DokployPreset
from agent_harness.presets.javascript import JavaScriptPreset
from agent_harness.presets.python import PythonPreset
from agent_harness.presets.universal import UniversalPreset

PRESETS = [PythonPreset(), JavaScriptPreset(), DockerPreset(), DokployPreset()]
UNIVERSAL = UniversalPreset()
