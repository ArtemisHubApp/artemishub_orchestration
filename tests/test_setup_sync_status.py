import setup
import status
import sync
from artemis_repos import git
from conftest import REPOS


def detach_all(org):
    for r in REPOS:
        git("checkout", "--detach", cwd=org.root / r)


def test_setup_tira_submodulos_do_detached_head(fake_org, capsys):
    detach_all(fake_org)
    assert setup.main(fake_org.root) == 0
    assert all(git("branch", "--show-current", cwd=fake_org.root / r) == "staging" for r in REPOS)
    assert "Pronto: 5 repos em staging" in capsys.readouterr().out


def test_setup_sem_staging_usa_main(fake_org_sem_staging, capsys):
    detach_all(fake_org_sem_staging)
    assert setup.main(fake_org_sem_staging.root) == 0
    assert all(git("branch", "--show-current", cwd=fake_org_sem_staging.root / r) == "main" for r in REPOS)
    captured = capsys.readouterr()
    assert "Pronto: 5 repos em main" in captured.out
    assert "AVISO: artemishub_rag ainda não tem staging; usando main." in captured.err


def test_setup_cria_branch_local_rastreando_origin(fake_org):
    repo = fake_org.root / "artemishub_rag"
    git("checkout", "--detach", cwd=repo)
    git("branch", "-D", "staging", cwd=repo)
    assert setup.main(fake_org.root) == 0
    assert git("branch", "--show-current", cwd=repo) == "staging"
    assert git("rev-parse", "--abbrev-ref", "staging@{u}", cwd=repo) == "origin/staging"


def test_sync_traz_commit_novo(fake_org, capsys):
    sha = fake_org.push_commit("artemishub_rag", "staging", "novo.txt")
    assert sync.main(fake_org.root) == 0
    assert git("rev-parse", "HEAD", cwd=fake_org.root / "artemishub_rag") == sha
    out = capsys.readouterr().out
    assert "feat: novo.txt" in out
    assert "sem novidades" in out  # os outros repos


def test_sync_pula_repo_sujo_sem_descartar(fake_org, capsys):
    f = fake_org.root / "artemishub_rag" / "rascunho.py"
    f.write_text("x=1")
    fake_org.push_commit("artemishub_rag", "staging", "novo.txt")
    sync.main(fake_org.root)
    assert "PULADO artemishub_rag: há mudanças locais não commitadas" in capsys.readouterr().out
    assert f.read_text() == "x=1"


def test_status_conta_sujo_e_atraso(fake_org):
    (fake_org.root / "artemishub_docs" / "a.md").write_text("a")
    fake_org.push_commit("artemishub_rag", "staging", "b.txt")
    git("fetch", cwd=fake_org.root / "artemishub_rag")
    rows = {r["repo"]: r for r in status.collect(fake_org.root)}
    assert list(rows) == REPOS
    assert rows["artemishub_docs"]["dirty"] and rows["artemishub_rag"]["behind"] == 1
    assert rows["artemishub_rag"]["ahead"] == 0
    assert rows["artemishub_rag"]["branch"] == "staging"
    assert rows["artemishub_rag"]["worktrees"] == 0


def test_status_conta_worktrees_e_imprime_tabela(fake_org, tmp_path, capsys):
    repo = fake_org.root / "artemishub_rag"
    git("worktree", "add", "-b", "feat/1-x", str(tmp_path / "wt"), cwd=repo)
    rows = {r["repo"]: r for r in status.collect(fake_org.root)}
    assert rows["artemishub_rag"]["worktrees"] == 1
    assert status.main(fake_org.root) == 0
    out = capsys.readouterr().out
    assert "artemishub_rag" in out and "staging" in out


def _commit_local(repo, nome="local.txt"):
    (repo / nome).write_text("so aqui\n", encoding="utf-8")
    git("add", nome, cwd=repo)
    git("-c", "user.name=T", "-c", "user.email=t@example.com", "commit", "-q", "-m", f"feat: {nome}", cwd=repo)
    return git("rev-parse", "HEAD", cwd=repo)


def test_sync_pula_repo_em_outra_branch(fake_org, capsys):
    repo = fake_org.root / "artemishub_rag"
    git("checkout", "-q", "-b", "feat/7-minha", cwd=repo)
    fake_org.push_commit("artemishub_rag", "staging", "novo.txt")
    assert sync.main(fake_org.root) == 0
    assert "PULADO artemishub_rag: está em feat/7-minha, não em staging" in capsys.readouterr().out
    assert git("branch", "--show-current", cwd=repo) == "feat/7-minha"


def test_sync_pula_head_destacado_com_commit_so_local(fake_org, capsys):
    repo = fake_org.root / "artemishub_rag"
    git("checkout", "-q", "--detach", cwd=repo)
    sha = _commit_local(repo)
    assert sync.main(fake_org.root) == 0
    assert "PULADO artemishub_rag: HEAD destacado com commits que só existem localmente" in capsys.readouterr().out
    assert git("rev-parse", "HEAD", cwd=repo) == sha
    assert git("branch", "--show-current", cwd=repo) == ""


def test_setup_pula_head_destacado_com_commit_so_local(fake_org, capsys):
    detach_all(fake_org)
    repo = fake_org.root / "artemishub_rag"
    sha = _commit_local(repo)
    assert setup.main(fake_org.root) == 0
    out = capsys.readouterr().out
    assert "PULADO artemishub_rag: HEAD destacado com commits que só existem localmente" in out
    assert git("rev-parse", "HEAD", cwd=repo) == sha
    assert git("branch", "--show-current", cwd=fake_org.root / "artemishub_docs") == "staging"
