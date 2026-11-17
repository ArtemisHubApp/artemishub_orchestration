"""AGENTS.md: seções, tamanho, links, regras explícitas e importação por Claude e Gemini."""

import re

from conftest import REPOS, ROOT

TITULOS = [
    "## O que é o Artemis",
    "## Repositórios",
    "## Regra de ouro",
    "## Regras de SDD",
    "## Branches e worktrees",
    "## Higiene do GitHub",
    "## Código limpo",
    "## Decisões (ADR)",
    "## Kanban",
    "## Segurança",
    "## Submódulos: cuidados",
]


def _agents() -> str:
    return (ROOT / "AGENTS.md").read_text(encoding="utf-8")


def test_agents_md_tem_secoes_e_tamanho():
    t = _agents()
    assert all(h in t for h in TITULOS) and len(t.splitlines()) <= 250


def test_links_locais_existem():
    """Todo link relativo aponta para arquivo existente; dentro de submódulo basta o repo existir (R3)."""
    sem_blocos = re.sub(r"```.*?```", "", _agents(), flags=re.DOTALL)
    for alvo in re.findall(r"\]\(([^)\s]+)\)", sem_blocos):
        if re.match(r"[a-z]+:", alvo) or alvo.startswith("#"):
            continue
        caminho = alvo.split("#")[0]
        if caminho.startswith("artemishub_"):
            assert caminho.split("/")[0] in REPOS, alvo
        else:
            assert (ROOT / caminho).exists(), alvo


def test_regras_de_rastreabilidade_explicitas():
    t = _agents()
    assert "Toda tarefa tem uma issue associada" in t and "Docs sempre atualizadas" in t


def test_skills_so_no_orquestrador():
    assert "skills só no orquestrador" in _agents().lower()


def test_claude_e_gemini_importam():
    assert (ROOT / "CLAUDE.md").read_text() == (ROOT / "GEMINI.md").read_text() == "@AGENTS.md\n"


def _readme() -> str:
    return (ROOT / "README.md").read_text(encoding="utf-8")


def test_como_abrir_o_agente_numa_worktree():
    for texto in (_agents(), _readme()):
        assert "Como abrir o agente numa tarefa" in texto
        for trecho in [
            "/add-dir",
            "--add-dir",
            "--include-directories",
            "confira a opção na documentação da sua versão",
        ]:
            assert trecho in texto, trecho


def test_primeiro_push_com_upstream_documentado():
    comando = (ROOT / ".claude/commands/worktree.md").read_text(encoding="utf-8")
    for texto in (_agents(), _readme(), comando):
        assert "git push -u origin <tipo>/<nº>-<slug>" in texto


def test_mudancas_no_orquestrador_e_ponteiros_de_submodulo():
    t = _agents()
    assert "Mudança no próprio orquestrador" in t and "a partir de `main`" in t
    cuidados = t.split("## Submódulos: cuidados")[1]
    assert "new commits" in cuidados and "git add -A" in cuidados


def test_readme_docker_sem_make_e_prune_yes():
    r = _readme()
    for cmd in [
        'docker compose run --rm rag uv run python -m src.query "',
        "docker compose run --rm rag uv run python -m src.demo",
        "docker compose run --rm rag uv run pytest -q",
        "make prune-yes",
    ]:
        assert cmd in r, cmd
    assert "`make prune` já usa `--yes`" not in r
