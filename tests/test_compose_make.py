import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
precisa_docker = pytest.mark.skipif(shutil.which("docker") is None, reason="docker ausente")
precisa_make = pytest.mark.skipif(shutil.which("make") is None, reason="make ausente")


def compose(*args):
    return subprocess.run(["docker", "compose", *args], cwd=ROOT, capture_output=True, check=False, text=True)


@precisa_docker
def test_compose_valido():
    r = compose("config", "-q")
    assert r.returncode == 0, r.stderr


@precisa_docker
def test_compose_servicos_e_profiles():
    cfg = json.loads(compose("--profile", "app", "config", "--format", "json").stdout)
    assert set(cfg["services"]) == {"rag", "agents", "backend", "frontend"}
    assert cfg["services"]["rag"]["environment"]["UV_LOCKED"] == "1"
    assert cfg["services"]["agents"]["environment"]["UV_LOCKED"] == "1"


@precisa_docker
def test_compose_sem_profile_so_sobe_rag_e_agents():
    cfg = json.loads(compose("config", "--format", "json").stdout)
    assert set(cfg["services"]) == {"rag", "agents"}


def test_anchor_do_compose_sem_volumes_mortos():
    yaml = pytest.importorskip("yaml")
    cfg = yaml.safe_load((ROOT / "docker-compose.yml").read_text(encoding="utf-8"))
    assert "volumes" not in cfg["x-uv-service"]  # cada serviço declara os seus (o merge `<<` não soma listas)
    for servico in ("rag", "agents"):
        assert "hf-cache:/cache/hf" in cfg["services"][servico]["volumes"]


@precisa_make
def test_make_help_lista_alvos():
    out = subprocess.run(["make", "help"], cwd=ROOT, capture_output=True, check=False, text=True).stdout
    assert all(a in out for a in ["setup", "sync", "worktree", "rag-query"])


@precisa_make
def test_make_alvos_documentados_no_help():
    out = subprocess.run(["make", "help"], cwd=ROOT, capture_output=True, check=False, text=True).stdout
    for alvo in ["status", "prune", "branches", "rag-demo", "test-", "shell-"]:
        assert alvo in out


@precisa_make
def test_make_worktree_exige_repo_e_branch():
    r = subprocess.run(["make", "worktree"], cwd=ROOT, capture_output=True, check=False, text=True)
    assert r.returncode != 0
    assert "REPO=" in r.stderr + r.stdout


@precisa_make
def test_make_prune_e_ensaio_e_prune_yes_remove():
    def plano(alvo):
        return subprocess.run(["make", "-n", alvo], cwd=ROOT, capture_output=True, check=False, text=True).stdout

    assert "worktree.py prune" in plano("prune") and "--yes" not in plano("prune")
    assert "worktree.py prune --yes" in plano("prune-yes")
