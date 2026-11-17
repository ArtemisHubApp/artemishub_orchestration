import shutil

import branches
import pytest
import worktree
from artemis_repos import git
from conftest import git as tgit
from worktree import validate_branch

RAG = "artemishub_rag"


@pytest.mark.parametrize(
    "nome",
    ["claude/optimistic-meitner-8yac2i", "Feat/OCR", "feat/ocr", "feat/20-ocr_diretrizes", "feat/20-ação"],
)
def test_branch_fora_do_padrao_recusada(nome):
    with pytest.raises(SystemExit, match="use feat/<nº issue>-<slug>"):
        validate_branch(nome)


def test_branch_valida_aceita():
    validate_branch("feat/20-ocr-diretrizes")
    validate_branch("fix/3-x")


def commit_na_worktree(path, nome="a.txt"):
    (path / nome).write_text("x\n", encoding="utf-8")
    tgit("add", nome, cwd=path)
    tgit("commit", "-q", "-m", f"feat: {nome}", cwd=path)


def test_new_cria_fora_do_repo_a_partir_de_staging(fake_org):
    p = worktree.new("rag", "feat/20-ocr-diretrizes", fake_org.root)
    assert p == fake_org.root.parent / "artemishub-worktrees/artemishub_rag/feat/20-ocr-diretrizes"
    assert git("rev-parse", "HEAD", cwd=p) == git("rev-parse", "origin/staging", cwd=fake_org.root / RAG)


def test_new_sem_staging_usa_main(fake_org_sem_staging):
    p = worktree.new("rag", "feat/20-ocr-diretrizes", fake_org_sem_staging.root)
    assert git("rev-parse", "HEAD", cwd=p) == git("rev-parse", "origin/main", cwd=fake_org_sem_staging.root / RAG)


def test_new_recusa_caminho_existente(fake_org):
    worktree.new("rag", "feat/20-a", fake_org.root)
    with pytest.raises(SystemExit, match="já existe"):
        worktree.new("rag", "feat/20-a", fake_org.root)


def test_new_valida_nome(fake_org):
    with pytest.raises(SystemExit, match="use feat/<nº issue>-<slug>"):
        worktree.new("rag", "feat/ocr", fake_org.root)


def test_list_devolve_repo_branch_path(fake_org):
    p = worktree.new("rag", "feat/20-a", fake_org.root)
    assert worktree.list_(fake_org.root) == [{"repo": RAG, "branch": "feat/20-a", "path": p}]


def test_squash_sem_gh_e_desconhecido_e_nao_apaga(fake_org, monkeypatch):
    monkeypatch.setattr(shutil, "which", lambda _: None)
    repo_dir = fake_org.root / RAG
    p = worktree.new("rag", "feat/1-x", fake_org.root)
    commit_na_worktree(p)
    tgit("push", "-q", "origin", "feat/1-x", cwd=p)
    fake_org.push_commit(RAG, "staging", "a.txt")  # "squash": mesmo conteúdo, commit novo
    git("fetch", "origin", cwd=repo_dir)
    assert branches.merged_status(repo_dir, "feat/1-x", "staging") == "desconhecido"
    assert worktree.prune(fake_org.root, dry_run=False) == []
    assert p.exists()


def test_prune_remove_worktree_mergeada_limpa(fake_org, monkeypatch):
    monkeypatch.setattr(shutil, "which", lambda _: None)
    repo_dir = fake_org.root / RAG
    p = worktree.new("rag", "feat/1-x", fake_org.root)
    commit_na_worktree(p)
    tgit("push", "-q", "origin", "HEAD:staging", cwd=p)  # merge real (fast-forward)
    assert worktree.prune(fake_org.root, dry_run=True) == [p]
    assert p.exists()
    assert worktree.prune(fake_org.root, dry_run=False) == [p]
    assert not p.exists()
    assert git("branch", "--list", "feat/1-x", cwd=repo_dir) == ""


def test_prune_nao_remove_worktree_suja(fake_org, monkeypatch):
    monkeypatch.setattr(shutil, "which", lambda _: None)
    p = worktree.new("rag", "feat/1-x", fake_org.root)
    commit_na_worktree(p)
    tgit("push", "-q", "origin", "HEAD:staging", cwd=p)
    (p / "rascunho.txt").write_text("nao commitado\n", encoding="utf-8")
    assert worktree.prune(fake_org.root, dry_run=False) == []
    assert (p / "rascunho.txt").exists()


def test_gh_diz_mergeada_squash(fake_org, monkeypatch):
    monkeypatch.setattr(branches, "_gh_pr_mergeado", lambda repo_dir, branch, sha: True)
    p = worktree.new("rag", "feat/1-x", fake_org.root)
    commit_na_worktree(p)  # não é ancestral de staging; só o gh diz que foi mergeada
    repo_dir = fake_org.root / RAG
    assert branches.merged_status(repo_dir, "feat/1-x", "staging") == "mergeada"
    assert worktree.prune(fake_org.root, dry_run=False) == [p]
    assert not p.exists()
    # git branch -d (nunca -D) recusa apagar a branch não ancestral: nada é perdido
    assert git("branch", "--list", "feat/1-x", cwd=repo_dir) != ""


def test_gh_diz_nao_mergeada_e_aberta(fake_org, monkeypatch):
    monkeypatch.setattr(branches, "_gh_pr_mergeado", lambda repo_dir, branch, sha: False)
    p = worktree.new("rag", "feat/1-x", fake_org.root)
    commit_na_worktree(p)
    assert branches.merged_status(fake_org.root / RAG, "feat/1-x", "staging") == "aberta"


def _empurra_branches(fake_org):
    p = worktree.new("rag", "feat/1-mergeada", fake_org.root)
    commit_na_worktree(p)
    tgit("push", "-q", "origin", "HEAD:staging", cwd=p)
    tgit("push", "-q", "origin", "HEAD:feat/1-mergeada", cwd=p)
    q = worktree.new("rag", "feat/2-aberta", fake_org.root)
    commit_na_worktree(q, "b.txt")
    tgit("push", "-q", "origin", "feat/2-aberta", cwd=q)
    return fake_org.remotes[RAG]


def _remotas(remote):
    return set(git("for-each-ref", "--format=%(refname:short)", "refs/heads", cwd=remote).split())


def test_branches_lista_sem_apagar(fake_org, monkeypatch, capsys):
    monkeypatch.setattr(shutil, "which", lambda _: None)
    remote = _empurra_branches(fake_org)
    assert branches.main(fake_org.root, delete=False) == 0
    out = capsys.readouterr().out
    assert "mergeada     feat/1-mergeada" in out
    assert "desconhecido feat/2-aberta" in out
    assert _remotas(remote) == {"main", "staging", "feat/1-mergeada", "feat/2-aberta"}


def test_branches_delete_so_apaga_mergeada_apos_confirmar(fake_org, monkeypatch):
    monkeypatch.setattr(shutil, "which", lambda _: None)
    remote = _empurra_branches(fake_org)
    monkeypatch.setattr("builtins.input", lambda _="": "s")
    branches.main(fake_org.root, delete=True)
    assert _remotas(remote) == {"main", "staging", "feat/2-aberta"}


def test_branches_delete_sem_confirmacao_nao_apaga(fake_org, monkeypatch):
    monkeypatch.setattr(shutil, "which", lambda _: None)
    remote = _empurra_branches(fake_org)
    monkeypatch.setattr("builtins.input", lambda _="": "")
    branches.main(fake_org.root, delete=True)
    assert "feat/1-mergeada" in _remotas(remote)


def test_delete_julga_o_remoto_nao_a_branch_local_velha(fake_org, monkeypatch):
    monkeypatch.setattr(shutil, "which", lambda _: None)
    p = worktree.new("rag", "feat/3-velha", fake_org.root)
    topo_staging = git("rev-parse", "HEAD", cwd=p)  # a local fica aqui: ancestral da staging
    commit_na_worktree(p)
    tgit("push", "-q", "origin", "HEAD:feat/3-velha", cwd=p)  # o remoto tem um commit extra, não mergeado
    tgit("update-ref", "refs/heads/feat/3-velha", topo_staging, cwd=p)
    monkeypatch.setattr("builtins.input", lambda _="": "s")
    branches.main(fake_org.root, delete=True)
    assert "feat/3-velha" in _remotas(fake_org.remotes[RAG])


def test_gh_mergeada_com_outra_ponta_nao_apaga(fake_org, monkeypatch):
    p = worktree.new("rag", "feat/4-reuso", fake_org.root)
    commit_na_worktree(p)
    tgit("push", "-q", "origin", "feat/4-reuso", cwd=p)
    monkeypatch.setattr(shutil, "which", lambda _: "/usr/bin/gh")

    class R:
        returncode = 0
        stdout = '[{"number": 1, "headRefOid": "0000000000000000000000000000000000000000"}]'

    real_run = branches.subprocess.run
    monkeypatch.setattr(branches.subprocess, "run", lambda *a, **k: R() if a[0][0] == "gh" else real_run(*a, **k))
    repo_dir = fake_org.root / RAG
    assert branches.merged_status(repo_dir, "feat/4-reuso", "staging", remoto=True) == "aberta"
    assert worktree.prune(fake_org.root, dry_run=False) == []
    monkeypatch.setattr("builtins.input", lambda _="": "s")
    branches.main(fake_org.root, delete=True)
    assert "feat/4-reuso" in _remotas(fake_org.remotes[RAG])
