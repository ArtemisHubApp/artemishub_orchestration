"""Hook PreToolUse do Claude Code: avisa, uma vez por sessão, em qual submódulo a pessoa está mexendo.

Usa só a biblioteca padrão e sempre sai com código 0: um erro aqui nunca pode travar o Claude.
"""

from __future__ import annotations

import json
import os
import re
import sys
import tempfile
from pathlib import Path

# Repetida de scripts/artemis_repos.py de propósito (o hook não importa scripts/);
# tests/test_hook.py garante que as duas listas continuam iguais.
REPOS: tuple[str, ...] = (
    "artemishub_docs",
    "artemishub_frontend",
    "artemishub_backend",
    "artemishub_agents",
    "artemishub_rag",
)


def _normalizar(caminho: str) -> str:
    """Aceita caminhos do Windows em qualquer sistema e compara sem diferenciar o que o SO ignora."""
    return os.path.normcase(os.path.abspath(caminho.replace("\\", "/")))


def _repo_do_arquivo(caminho: str, root: Path) -> str | None:
    arquivo = _normalizar(caminho)
    base = _normalizar(str(root))
    for repo in REPOS:
        if arquivo.startswith(os.path.join(base, repo) + os.sep):
            return repo
    return None


def handle(payload: dict, root: Path, state_dir: Path) -> dict | None:
    """Devolve o aviso para o primeiro acesso da sessão a um submódulo; senão, None."""
    if not isinstance(payload, dict):
        return None
    entrada = payload.get("tool_input")
    if not isinstance(entrada, dict):
        return None
    caminho = entrada.get("file_path") or entrada.get("path")
    if not isinstance(caminho, str) or not caminho:
        return None
    repo = _repo_do_arquivo(caminho, root)
    if repo is None:
        return None
    sessao = re.sub(r"[^A-Za-z0-9_-]", "", str(payload.get("session_id", ""))) or "sem-sessao"
    marcador = state_dir / f"{sessao}-{repo}"
    if marcador.exists():
        return None
    state_dir.mkdir(parents=True, exist_ok=True)
    marcador.touch()
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "additionalContext": f"Você está em {repo}. Leia {repo}/AGENTS.md (ou README.md) antes de alterar.",
        }
    }


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[2])
        saida = handle(payload, root, Path(tempfile.gettempdir()) / "artemis-hook")
        if saida:
            print(json.dumps(saida, ensure_ascii=False))
    except Exception:  # noqa: BLE001 - o hook nunca pode quebrar a sessão
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
