from pathlib import Path

from agent_harness.preset import Preset, PresetInfo, ToolInfo
from agent_harness.runner import CheckResult


class DockerPreset(Preset):
    name = "docker"

    def detect(self, project_dir: Path) -> bool:
        from .detect import detect_docker

        return detect_docker(project_dir)

    def run_checks(
        self, project_dir: Path, config: dict, exclude: list[str]
    ) -> list[CheckResult]:
        from .conftest_compose_check import run_conftest_compose
        from .conftest_dockerfile_check import run_conftest_dockerfile
        from .hadolint_check import run_hadolint

        results = []
        results.append(run_conftest_dockerfile(project_dir))
        results.append(
            run_conftest_compose(
                project_dir, config.get("docker", {}).get("own_image_prefix", "")
            )
        )
        results.append(run_hadolint(project_dir))
        return results

    def run_diagnostic(self, project_dir: Path, config: dict):
        from agent_harness.conftest import run_conftest_diagnostic

        results = []
        results.append(
            run_conftest_diagnostic(
                "docker-dockerfile", project_dir, "Dockerfile", "dockerfile"
            )
        )
        compose_data = None
        own_prefix = config.get("docker", {}).get("own_image_prefix", "")
        if own_prefix:
            compose_data = {"own_image_prefix": own_prefix}
        results.append(
            run_conftest_diagnostic(
                "docker-compose",
                project_dir,
                "docker-compose.prod.yml",
                "compose",
                data=compose_data,
            )
        )
        return results

    def run_fix(self, project_dir: Path, config: dict) -> list[str]:
        return []

    def get_info(self) -> PresetInfo:
        return PresetInfo(
            name="docker",
            tools=[
                ToolInfo(
                    "hadolint",
                    "Dockerfile best practices",
                    "hadolint",
                    "brew install hadolint",
                ),
                ToolInfo(
                    "conftest",
                    "compose healthchecks, image pinning, ports",
                    "conftest",
                    "brew install conftest",
                ),
            ],
        )
