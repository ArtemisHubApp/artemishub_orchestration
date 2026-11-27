"""Release em SemVer: calcula a próxima versão e monta o nome e as notas a partir dos títulos dos PRs.

Os títulos seguem Conventional Commits (`tipo(escopo)!: descrição`):

- `!` depois do tipo, ou `BREAKING CHANGE` no título: major (antes da 1.0.0, minor);
- algum `feat`: minor;
- o resto: patch. A primeira release é `v0.1.0`.

Uso (no workflow de release): `python scripts/release.py --anterior v0.1.0 --titulo-release "release: tema"
--repo ArtemisHubApp/<repo> --prs prs.json` imprime `{"versao", "nome", "notas"}` em JSON. O `prs.json` é a saída
de `gh pr list --json number,title,author`. Só biblioteca padrão.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

_SEMVER = re.compile(r"v(\d+)\.(\d+)\.(\d+)")
_CONVENCIONAL = re.compile(r"^(?P<tipo>[a-z]+)(\([^)]*\))?(?P<quebra>!)?:\s")
_RELEASE = re.compile(r"^release:\s*(?P<tema>.*)$")

# Seções das notas, na ordem em que aparecem; tipos fora desta lista vão para "Outros".
_SECOES = [
    ("Novidades", {"feat"}),
    ("Correções", {"fix"}),
    ("Documentação", {"docs"}),
    ("CI e manutenção", {"ci", "chore", "refactor", "test", "build", "perf", "style"}),
]
_OUTROS = "Outros"


def _tipo(titulo: str) -> str | None:
    achado = _CONVENCIONAL.match(titulo)
    return achado["tipo"] if achado else None


def _quebra(titulo: str) -> bool:
    achado = _CONVENCIONAL.match(titulo)
    return bool(achado and achado["quebra"]) or "BREAKING CHANGE" in titulo


def proxima_versao(anterior: str | None, titulos: list[str]) -> str:
    """Versão seguinte a `anterior` (ex.: `v0.1.0`) conforme os títulos; sem anterior, `v0.1.0`."""
    if anterior is None:
        return "v0.1.0"
    achado = _SEMVER.fullmatch(anterior)
    if not achado:
        raise ValueError(f"versão anterior fora do SemVer vX.Y.Z: {anterior}")
    major, minor, patch = (int(parte) for parte in achado.groups())
    if any(_quebra(t) for t in titulos):
        return f"v{major}.{minor + 1}.0" if major == 0 else f"v{major + 1}.0.0"
    if any(_tipo(t) == "feat" for t in titulos):
        return f"v{major}.{minor + 1}.0"
    return f"v{major}.{minor}.{patch + 1}"


def tema_do_release(titulo: str) -> str:
    """O que vem depois de `release:` no título do PR de release; vazio se não for um."""
    achado = _RELEASE.match(titulo.strip())
    return achado["tema"].strip() if achado else ""


def nome_da_release(versao: str, tema: str) -> str:
    return f"{versao} · {tema}" if tema else versao


def _secao(titulo: str) -> str:
    tipo = _tipo(titulo)
    for nome, tipos in _SECOES:
        if tipo in tipos:
            return nome
    return _OUTROS


def notas(prs: list[dict], anterior: str | None, nova: str, repo: str) -> str:
    """Notas em Markdown, uma seção por tipo de PR; o próprio PR de release não entra."""
    por_secao: dict[str, list[str]] = {}
    for item in sorted(prs, key=lambda p: p["number"]):
        titulo = item["title"].strip()
        if tema_do_release(titulo) or titulo.startswith("release:"):
            continue
        autora = (item.get("author") or {}).get("login", "")
        linha = f"- {titulo} (#{item['number']})" + (f" por @{autora}" if autora else "")
        por_secao.setdefault(_secao(titulo), []).append(linha)

    partes: list[str] = []
    for nome in [s for s, _ in _SECOES] + [_OUTROS]:
        if nome in por_secao:
            partes.append(f"## {nome}\n\n" + "\n".join(por_secao[nome]))
    if not partes:
        partes.append("Sem PRs novos desde a versão anterior.")
    if anterior:
        partes.append(f"**Comparação completa:** https://github.com/{repo}/compare/{anterior}...{nova}")
    else:
        partes.append("Primeira release do repositório.")
    return "\n\n".join(partes) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--anterior", default="", help="Tag SemVer anterior (vazio se não há)")
    parser.add_argument("--titulo-release", default="", help="Título do PR de release (release: <tema>)")
    parser.add_argument("--repo", required=True, help="owner/nome do repositório")
    parser.add_argument("--prs", required=True, type=Path, help="JSON de `gh pr list --json number,title,author`")
    parser.add_argument("--versao", default="", help="Força a versão (ex.: ao recriar releases antigas)")
    args = parser.parse_args()

    prs = json.loads(args.prs.read_text(encoding="utf-8"))
    anterior = args.anterior or None
    titulos = [p["title"] for p in prs if not p["title"].startswith("release:")]
    versao = args.versao or proxima_versao(anterior, titulos)
    if not _SEMVER.fullmatch(versao):
        raise SystemExit(f"versão fora do SemVer vX.Y.Z: {versao}")
    saida = {
        "versao": versao,
        "nome": nome_da_release(versao, tema_do_release(args.titulo_release)),
        "notas": notas(prs, anterior, versao, args.repo),
    }
    print(json.dumps(saida, ensure_ascii=False))


if __name__ == "__main__":
    main()
