"""Valida o frontmatter de cada SKILL.md: name igual à pasta e description não vazia (até 1024 caracteres)."""

from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAX_DESCRIPTION = 1024


def parse_frontmatter(texto: str) -> dict[str, str] | None:
    """Lê só linhas `chave: valor` entre os `---`; devolve None se não houver frontmatter."""
    linhas = texto.lstrip("﻿").splitlines()
    if not linhas or linhas[0].strip() != "---":
        return None
    dados: dict[str, str] = {}
    for linha in linhas[1:]:
        if linha.strip() == "---":
            return dados
        chave, sep, valor = linha.partition(":")
        if sep and not linha[0].isspace():
            valor = valor.strip()
            if len(valor) >= 2 and valor[0] == valor[-1] and valor[0] in "\"'":
                valor = valor[1:-1]
            dados[chave.strip()] = valor
    return None  # frontmatter nunca fechado


def validate(skills_dir: Path) -> list[str]:
    erros: list[str] = []
    for pasta in sorted(p for p in skills_dir.iterdir() if p.is_dir()):
        arquivo = pasta / "SKILL.md"
        if not arquivo.is_file():
            erros.append(f"{pasta.name}: SKILL.md não existe")
            continue
        dados = parse_frontmatter(arquivo.read_text(encoding="utf-8"))
        if dados is None:
            erros.append(f"{pasta.name}: frontmatter ausente ou sem fechamento")
            continue
        if dados.get("name") != pasta.name:
            erros.append(f"{pasta.name}: name {dados.get('name')!r} diferente do nome da pasta")
        descricao = dados.get("description", "")
        if not descricao:
            erros.append(f"{pasta.name}: description vazia")
        elif len(descricao) > MAX_DESCRIPTION:
            erros.append(f"{pasta.name}: description com {len(descricao)} caracteres (máximo {MAX_DESCRIPTION})")
    return erros


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "skills_dir", nargs="*", type=Path, help="pastas de skills (padrão: .agents/skills e .claude/skills)"
    )
    parser.add_argument("--root", type=Path, default=ROOT, help=argparse.SUPPRESS)
    args = parser.parse_args()
    pastas = args.skills_dir or [args.root / ".agents" / "skills", args.root / ".claude" / "skills"]
    erros = [e for pasta in pastas if pasta.is_dir() for e in validate(pasta)]
    for erro in erros:
        print(f"ERRO {erro}")
    if not erros:
        print("skills válidas")
    return 1 if erros else 0


if __name__ == "__main__":
    raise SystemExit(main())
