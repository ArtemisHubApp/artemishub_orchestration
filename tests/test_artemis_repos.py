import pytest
from artemis_repos import base_branch, resolve_repo, worktrees_root


def test_resolve_repo_aceita_curto_e_longo():
    assert resolve_repo("rag") == resolve_repo("artemishub_rag") == "artemishub_rag"


def test_resolve_repo_invalido():
    with pytest.raises(SystemExit):
        resolve_repo("xyz")


def test_base_branch_staging(fake_org):
    assert base_branch(fake_org.root / "artemishub_rag") == "staging"


def test_base_branch_sem_staging_usa_main_e_avisa(fake_org_sem_staging, capsys):
    assert base_branch(fake_org_sem_staging.root / "artemishub_rag") == "main"
    assert "AVISO: artemishub_rag ainda não tem staging; usando main." in capsys.readouterr().err


def test_worktrees_root_fica_fora_do_repo(tmp_path):
    assert worktrees_root(tmp_path / "orq") == tmp_path / "artemishub-worktrees"


def test_base_branch_nao_casa_por_sufixo(fake_org_sem_staging):
    from artemis_repos import git

    repo_dir = fake_org_sem_staging.root / "artemishub_rag"
    git("push", "-q", "origin", "HEAD:refs/heads/old/staging", cwd=repo_dir)
    assert base_branch(repo_dir) == "main"
