import configparser
import subprocess
from pathlib import Path

from conftest import ROOT

REPOS = ["artemishub_docs", "artemishub_frontend", "artemishub_backend", "artemishub_agents", "artemishub_rag"]


def parse_gitmodules(path: Path) -> list[dict[str, str]]:
    cfg = configparser.ConfigParser()
    cfg.read(path)
    return [{**cfg[s], "name": s} for s in cfg.sections()]


def test_gitmodules_lista_os_5_repos_https_staging():
    cfg = parse_gitmodules(ROOT / ".gitmodules")
    assert [s["path"] for s in cfg] == REPOS
    assert all(s["url"] == f"https://github.com/ArtemisHubApp/{s['path']}.git" for s in cfg)
    assert all(s["branch"] == "staging" for s in cfg)


def test_sem_symlinks_no_repo():
    tracked = subprocess.run(["git", "ls-files", "-s"], capture_output=True, text=True, cwd=ROOT).stdout
    assert not [line for line in tracked.splitlines() if line.startswith("120000")]


def test_fake_org_fixture(fake_org):
    assert (fake_org.root / "artemishub_rag" / ".git").exists()


def test_fake_org_tem_main_e_staging(fake_org):
    for repo, remote in fake_org.remotes.items():
        refs = subprocess.run(["git", "branch", "--list"], capture_output=True, text=True, cwd=remote).stdout
        assert "main" in refs and "staging" in refs, repo


def test_fake_org_sem_staging_so_tem_main(fake_org_sem_staging):
    for remote in fake_org_sem_staging.remotes.values():
        refs = subprocess.run(["git", "branch", "--list"], capture_output=True, text=True, cwd=remote).stdout
        assert "main" in refs and "staging" not in refs


def test_push_commit_devolve_sha_da_branch(fake_org):
    sha = fake_org.push_commit("artemishub_rag", "staging", "novo.txt")
    remote = fake_org.remotes["artemishub_rag"]
    head = subprocess.run(["git", "rev-parse", "staging"], capture_output=True, text=True, cwd=remote).stdout.strip()
    assert sha == head
