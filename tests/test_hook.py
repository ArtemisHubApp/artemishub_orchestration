"""Testes do hook PreToolUse que avisa em qual submódulo a pessoa está."""

import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import artemis_repos
import pytest

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / ".claude" / "hooks" / "submodule_context.py"

_spec = importlib.util.spec_from_file_location("submodule_context", HOOK)
hook = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(hook)
handle = hook.handle


COMANDO_HOOK = (
    'sh -c \'if python3 -c "" >/dev/null 2>&1; then exec python3 "$0"; else exec python "$0"; fi\' '
    '"$CLAUDE_PROJECT_DIR/.claude/hooks/submodule_context.py"'
)


def _payload(session: str, path: str, chave: str = "file_path") -> dict:
    return {"session_id": session, "tool_input": {chave: path}}


def test_avisa_uma_vez_por_sessao(tmp_path):
    p = _payload("s1", str(ROOT / "artemishub_rag/src/query.py"))
    out = handle(p, ROOT, tmp_path)
    saida = out["hookSpecificOutput"]
    assert saida["hookEventName"] == "PreToolUse"
    assert saida["additionalContext"] == (
        "Você está em artemishub_rag. Leia artemishub_rag/AGENTS.md (ou README.md) antes de alterar."
    )
    assert handle(p, ROOT, tmp_path) is None


def test_aviso_e_por_repo_e_por_sessao(tmp_path):
    assert handle(_payload("s1", str(ROOT / "artemishub_rag/a.py")), ROOT, tmp_path) is not None
    assert handle(_payload("s1", str(ROOT / "artemishub_docs/a.md")), ROOT, tmp_path) is not None
    assert handle(_payload("s2", str(ROOT / "artemishub_rag/a.py")), ROOT, tmp_path) is not None


def test_aceita_chave_path(tmp_path):
    assert handle(_payload("s3", str(ROOT / "artemishub_docs/x.md"), "path"), ROOT, tmp_path) is not None


def test_caminho_windows(tmp_path, monkeypatch):
    monkeypatch.setattr(os.path, "normcase", str.lower)
    p = _payload("s2", str(ROOT).upper() + "\\ARTEMISHUB_RAG\\src\\x.py")
    assert handle(p, ROOT, tmp_path) is not None


WT = ROOT.parent / "artemishub-worktrees"


def test_reconhece_worktree_irma_do_orquestrador(tmp_path):
    p = _payload("s-wt", str(WT / "artemishub_rag/feat/20-ocr/src/query.py"))
    out = handle(p, ROOT, tmp_path)
    assert out["hookSpecificOutput"]["additionalContext"] == (
        "Você está em artemishub_rag. Leia artemishub_rag/AGENTS.md (ou README.md) antes de alterar."
    )
    assert handle(p, ROOT, tmp_path) is None  # mesma sessão e mesmo repo: um aviso só


def test_worktree_caminho_windows(tmp_path, monkeypatch):
    monkeypatch.setattr(os.path, "normcase", str.lower)
    p = _payload("s-wt-win", str(WT).upper() + "\\ARTEMISHUB_DOCS\\docs\\5-x\\a.md")
    assert handle(p, ROOT, tmp_path) is not None


def test_worktree_de_repo_desconhecido_nao_conta(tmp_path):
    assert handle(_payload("s", str(WT / "artemishub_rag_old/feat/1-x/a.py")), ROOT, tmp_path) is None
    assert handle(_payload("s", str(WT / "outra_coisa.txt")), ROOT, tmp_path) is None


def test_fora_de_submodulo(tmp_path):
    assert handle(_payload("s", str(ROOT / "README.md")), ROOT, tmp_path) is None


def test_repo_irmao_com_prefixo_parecido_nao_conta(tmp_path):
    assert handle(_payload("s", str(ROOT / "artemishub_rag_old/x.py")), ROOT, tmp_path) is None
    assert handle(_payload("s", str(ROOT / "artemishub_rag")), ROOT, tmp_path) is None


def test_session_id_inseguro_vira_nome_de_arquivo_seguro(tmp_path):
    p = _payload("../../etc/x y", str(ROOT / "artemishub_rag/a.py"))
    assert handle(p, ROOT, tmp_path) is not None
    assert all(f.parent == tmp_path for f in tmp_path.iterdir())
    assert handle(p, ROOT, tmp_path) is None


def test_entradas_malformadas_devolvem_none(tmp_path):
    for p in ({}, {"tool_input": None}, {"tool_input": {}}, {"tool_input": {"file_path": 3}}, [], "x", None):
        assert handle(p, ROOT, tmp_path) is None


def _roda(entrada: str, **env) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=entrada,
        text=True,
        capture_output=True,
        check=False,
        env={**os.environ, **env},
    )


def test_json_invalido_sai_zero():
    r = _roda("{")
    assert r.returncode == 0
    assert r.stdout == ""


def test_json_nao_dict_sai_zero():
    assert _roda("[1, 2]").returncode == 0


def test_main_imprime_json_e_sai_zero(tmp_path):
    entrada = json.dumps(_payload("sessao-main-teste", str(ROOT / "artemishub_docs/a.md")))
    env = {"CLAUDE_PROJECT_DIR": str(ROOT), "TMPDIR": str(tmp_path), "TEMP": str(tmp_path), "TMP": str(tmp_path)}
    r = _roda(entrada, **env)
    assert r.returncode == 0
    assert "artemishub_docs/AGENTS.md" in json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"]
    assert _roda(entrada, **env).stdout == ""


def test_repos_iguais_aos_scripts():
    assert hook.REPOS == artemis_repos.REPOS


def test_settings_json_valido_e_com_hook():
    cfg = json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
    (grupo,) = cfg["hooks"]["PreToolUse"]
    assert grupo["matcher"] == "Read|Edit|Write"
    (h,) = grupo["hooks"]
    assert h["type"] == "command"
    assert h["command"] == COMANDO_HOOK
    assert set(cfg["permissions"]["deny"]) == {
        "Read(**/.venv/**)",
        "Read(**/node_modules/**)",
        "Read(**/data/**)",
        "Read(**/chroma*/**)",
        "Read(**/*.lock)",
    }
    assert cfg["enabledPlugins"] == {"superpowers@claude-plugins-official": True}
    assert "extraKnownMarketplaces" not in cfg


def test_comandos_existem_com_description():
    for nome in ("start", "sync", "worktree"):
        texto = (ROOT / ".claude" / "commands" / f"{nome}.md").read_text(encoding="utf-8")
        assert texto.startswith("---\ndescription: ")
    assert "python scripts/setup.py" in (ROOT / ".claude/commands/start.md").read_text(encoding="utf-8")
    assert "python scripts/sync.py" in (ROOT / ".claude/commands/sync.md").read_text(encoding="utf-8")
    assert "python scripts/worktree.py new" in (ROOT / ".claude/commands/worktree.md").read_text(encoding="utf-8")


@pytest.mark.skipif(shutil.which("sh") is None, reason="sh indisponível")
def test_comando_configurado_roda_no_sh(tmp_path):
    cfg = json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
    comando = cfg["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
    entrada = json.dumps(_payload("sessao-sh-teste", str(ROOT / "artemishub_docs/a.md")))
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(ROOT), "TMPDIR": str(tmp_path)}
    r = subprocess.run(["sh", "-c", comando], input=entrada, text=True, capture_output=True, check=False, env=env)
    assert r.returncode == 0
    assert "artemishub_docs/AGENTS.md" in json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"]
