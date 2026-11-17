"""Copia a artemis-sdd de .agents/skills/ (fonte editável) para .claude/skills/ (sem links simbólicos)."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = "artemis-sdd"


def _fonte(root: Path) -> Path:
    return root / ".agents" / "skills" / SKILL


def _destino(root: Path) -> Path:
    return root / ".claude" / "skills" / SKILL


def sync(root: Path = ROOT) -> None:
    destino = _destino(root)
    if destino.exists():
        shutil.rmtree(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(_fonte(root), destino)


def _arquivos(base: Path) -> dict[str, bytes]:
    if not base.is_dir():
        return {}
    return {p.relative_to(base).as_posix(): p.read_bytes() for p in sorted(base.rglob("*")) if p.is_file()}


def check(root: Path = ROOT) -> list[str]:
    """Arquivos que diferem entre a fonte e a cópia (vazio quando está em dia)."""
    fonte, copia = _arquivos(_fonte(root)), _arquivos(_destino(root))
    return sorted(nome for nome in fonte.keys() | copia.keys() if fonte.get(nome) != copia.get(nome))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="só verifica; sai com 1 se houver diferença")
    parser.add_argument("--root", type=Path, default=ROOT, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.check:
        diferencas = check(args.root)
        for nome in diferencas:
            print(f"DIVERGE: {nome}")
        if diferencas:
            print("Rode: python scripts/sync_skills.py")
            return 1
        print("skills em sincronia")
        return 0
    sync(args.root)
    print(f"copiado: .agents/skills/{SKILL} -> .claude/skills/{SKILL}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
