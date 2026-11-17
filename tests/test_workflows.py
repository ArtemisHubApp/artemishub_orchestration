"""Valida a estrutura dos workflows do GitHub Actions (sem rodar o Actions)."""

import pytest

yaml = pytest.importorskip("yaml")

from conftest import ROOT  # noqa: E402

WF = ROOT / ".github" / "workflows"


def load(nome: str) -> dict:
    return yaml.safe_load((WF / nome).read_text(encoding="utf-8"))


def gatilhos(wf: dict) -> dict:
    # PyYAML (YAML 1.1) le a chave `on` como booleano True.
    return wf[True] if True in wf else wf["on"]


def runs(job: dict) -> str:
    return "\n".join(s.get("run", "") for s in job["steps"])


def usos(job: dict) -> list[str]:
    return [s["uses"] for s in job["steps"] if "uses" in s]


def test_python_ci_reutilizavel():
    wf = load("python-ci.yml")
    assert "workflow_call" in gatilhos(wf)
    assert set(wf["jobs"]) == {"no-local-skills", "lint", "test", "pr-title", "gitleaks"}
    inputs = gatilhos(wf)["workflow_call"]["inputs"]
    assert inputs["python-versions"]["default"] == '["3.12"]'
    assert inputs["run-pyright"]["type"] == "boolean" and inputs["run-pyright"]["default"] is True


def test_lint_checa_lock_e_locked():
    steps = runs(load("python-ci.yml")["jobs"]["lint"])
    assert "uv lock --check" in steps and "uv sync --locked" in steps and "lint-imports" in steps
    assert "ruff check ." in steps and "ruff format --check ." in steps


def test_lint_import_linter_condicional_e_pyright_advisory():
    steps = load("python-ci.yml")["jobs"]["lint"]["steps"]
    imp = next(s for s in steps if "lint-imports" in s.get("run", ""))
    assert "grep -q" in imp["run"] and "[tool.importlinter]" in imp["run"]
    pyr = next(s for s in steps if "pyright" in s.get("run", ""))
    assert pyr["continue-on-error"] is True and "run-pyright" in pyr["if"]


def test_no_local_skills_cobre_as_4_formas():
    run = load("python-ci.yml")["jobs"]["no-local-skills"]["steps"][-1]["run"]
    assert all(p in run for p in [".claude/skills", ".agents/skills", "agent/skills", "skills-lock.json"])
    assert "::error::skills ficam no artemishub_orchestration" in run


def test_test_usa_matriz_de_inputs():
    job = load("python-ci.yml")["jobs"]["test"]
    assert job["strategy"]["matrix"]["python-version"] == "${{ fromJSON(inputs.python-versions) }}"
    assert "uv sync --locked --dev" in runs(job) and "uv run pytest -q" in runs(job)


def test_pr_title_so_em_pull_request():
    job = load("python-ci.yml")["jobs"]["pr-title"]
    assert job["if"] == "github.event_name == 'pull_request'"
    assert job["permissions"] == {"contents": "read", "pull-requests": "read"}
    step = next(s for s in job["steps"] if s["uses"].startswith("amannn/action-semantic-pull-request@v5"))
    tipos = step["with"]["types"].split()
    assert set(tipos) == {"feat", "fix", "chore", "docs", "refactor", "test", "ci", "release"}


def test_gitleaks_historico_completo():
    for nome, job in [("python-ci.yml", load("python-ci.yml")["jobs"]["gitleaks"])]:
        assert "ghcr.io/gitleaks/gitleaks" in runs(job), nome
        assert not any("gitleaks-action" in u for u in usos(job)), nome
        checkout = next(s for s in job["steps"] if s["uses"].startswith("actions/checkout"))
        assert checkout["with"]["fetch-depth"] == 0


def test_todos_os_jobs_com_permissao_minima():
    for nome in ["python-ci.yml", "ci.yml", "gitleaks.yml"]:
        wf = load(nome)
        for job_id, job in wf["jobs"].items():
            perms = job.get("permissions", wf.get("permissions"))
            assert perms and perms.get("contents") == "read", f"{nome}:{job_id}"


def test_ci_do_orquestrador():
    wf = load("ci.yml")
    g = gatilhos(wf)
    assert "edited" in g["pull_request"]["types"] and g["push"]["branches"] == ["staging", "main"]
    assert "pull_request" in wf["concurrency"]["cancel-in-progress"]
    assert set(wf["jobs"]) == {"tests", "skills"}
    tests = wf["jobs"]["tests"]
    checkout = next(s for s in tests["steps"] if s["uses"].startswith("actions/checkout"))
    assert checkout["with"]["submodules"] is False
    r = runs(tests)
    for cmd in ["uv sync --locked --dev", "ruff check", "ruff format --check", "pytest"]:
        assert cmd in r
    r = runs(wf["jobs"]["skills"])
    assert "scripts/validate_skills.py" in r and "scripts/sync_skills.py --check" in r


def test_gitleaks_do_orquestrador():
    wf = load("gitleaks.yml")
    g = gatilhos(wf)
    assert "pull_request" in g and "push" in g
    job = wf["jobs"]["gitleaks"]
    assert "ghcr.io/gitleaks/gitleaks" in runs(job) and " git /repo" in runs(job)
    assert not any("gitleaks-action" in u for u in usos(job))
    assert "edited" in g["pull_request"]["types"]


def test_snippet_do_chamador_tem_permissions_e_edited():
    cab = (WF / "python-ci.yml").read_text(encoding="utf-8").split("name: Python CI")[0]
    assert "permissions: { contents: read, pull-requests: read }" in cab
    assert "edited" in cab
