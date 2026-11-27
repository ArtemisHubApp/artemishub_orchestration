"""Release em SemVer: próxima versão, nome e notas a partir dos títulos dos PRs (Conventional Commits)."""

import json
import subprocess
import sys

import pytest
from conftest import ROOT
from release import nome_da_release, notas, proxima_versao, tema_do_release

REPO = "ArtemisHubApp/artemishub_orchestration"


def pr(numero: int, titulo: str, autora: str = "AmandaElisa") -> dict:
    return {"number": numero, "title": titulo, "author": {"login": autora}}


@pytest.mark.parametrize(
    ("anterior", "titulos", "esperada"),
    [
        (None, ["docs: qualquer coisa"], "v0.1.0"),
        (None, ["feat!: muda tudo"], "v0.1.0"),
        ("v0.1.0", ["docs: a", "fix: b"], "v0.1.1"),
        ("v0.1.1", ["fix: a", "feat: b"], "v0.2.0"),
        ("v0.2.0", ["feat(api)!: quebra o contrato"], "v0.3.0"),  # antes da 1.0.0, quebra sobe o minor
        ("v1.4.2", ["chore: a"], "v1.4.3"),
        ("v1.4.2", ["feat(rag): b"], "v1.5.0"),
        ("v1.4.2", ["refactor!: c"], "v2.0.0"),
        ("v1.4.2", ["fix: d BREAKING CHANGE no contrato"], "v2.0.0"),
        ("v0.3.0", [], "v0.3.1"),
    ],
)
def test_proxima_versao(anterior, titulos, esperada):
    assert proxima_versao(anterior, titulos) == esperada


def test_versao_anterior_invalida_e_recusada():
    with pytest.raises(ValueError, match="SemVer"):
        proxima_versao("v2026.11.27b", ["fix: a"])


@pytest.mark.parametrize(
    ("titulo", "tema"),
    [
        ("release: staging em todos os repos", "staging em todos os repos"),
        ("release: 2026-11-27b", "2026-11-27b"),
        ("Merge pull request #27 from ArtemisHubApp/staging", ""),
        ("", ""),
    ],
)
def test_tema_do_release(titulo, tema):
    assert tema_do_release(titulo) == tema


def test_nome_com_e_sem_tema():
    assert nome_da_release("v0.2.0", "quadro automático") == "v0.2.0 · quadro automático"
    assert nome_da_release("v0.2.0", "") == "v0.2.0"


def test_notas_agrupam_por_tipo_e_ignoram_releases():
    prs = [
        pr(22, "ci: workflow Quadro inclui as issues da org no Project"),
        pr(18, "chore: staging em todos os repos nas regras de SDD"),
        pr(20, "docs: padrão de issues do kanban e status dos ADRs", "anajbsouza"),
        pr(31, "feat(api): rota de currículo"),
        pr(33, "fix: corrige o cookie"),
        pr(27, "release: 2026-11-27b"),
        pr(40, "Título fora do padrão"),
    ]
    texto = notas(prs, "v0.1.0", "v0.2.0", REPO)
    secoes = [linha for linha in texto.splitlines() if linha.startswith("## ")]
    assert secoes == ["## Novidades", "## Correções", "## Documentação", "## CI e manutenção", "## Outros"]
    assert "- feat(api): rota de currículo (#31) por @AmandaElisa" in texto
    assert "- docs: padrão de issues do kanban e status dos ADRs (#20) por @anajbsouza" in texto
    assert "#27" not in texto  # o próprio PR de release não entra
    # Ordem dentro da seção: número do PR crescente.
    assert texto.index("(#18)") < texto.index("(#22)")
    assert texto.rstrip().endswith(f"**Comparação completa:** https://github.com/{REPO}/compare/v0.1.0...v0.2.0")


def test_notas_da_primeira_release_sem_comparacao_e_sem_secao_vazia():
    texto = notas([pr(2, "docs: plano 2")], None, "v0.1.0", REPO)
    assert "## Documentação" in texto and "## Novidades" not in texto
    assert "compare" not in texto and "Primeira release" in texto


def test_notas_sem_prs():
    assert "Sem PRs novos" in notas([], "v0.1.0", "v0.1.1", REPO)


def test_cli_devolve_json(tmp_path):
    arquivo = tmp_path / "prs.json"
    arquivo.write_text(json.dumps([pr(31, "feat: rota")]), encoding="utf-8")
    saida = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "release.py"),
            "--anterior",
            "v0.1.0",
            "--titulo-release",
            "release: currículo",
            "--repo",
            REPO,
            "--prs",
            str(arquivo),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    dados = json.loads(saida.stdout)
    assert dados["versao"] == "v0.2.0"
    assert dados["nome"] == "v0.2.0 · currículo"
    assert "## Novidades" in dados["notas"]
