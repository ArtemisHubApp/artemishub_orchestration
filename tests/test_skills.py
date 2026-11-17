"""Skills: Superpowers copiado, artemis-sdd e as duas cópias em sincronia."""

import json
import shutil
from pathlib import Path

import sync_skills
import validate_skills

ROOT = Path(__file__).resolve().parents[1]


def test_skills_validas():
    assert validate_skills.validate(ROOT / ".agents/skills") == []


def test_sem_orchestrator():
    assert not (ROOT / ".agents/skills/orchestrator").exists()


def test_lock_bate_com_pastas():
    lock = json.loads((ROOT / "skills-lock.json").read_text(encoding="utf-8"))["skills"]
    pastas = {p.name for p in (ROOT / ".agents/skills").iterdir()} - {"artemis-sdd"}
    assert set(lock) == pastas and len(pastas) == 15


def test_claude_tem_so_artemis_sdd():
    assert [p.name for p in (ROOT / ".claude/skills").iterdir()] == ["artemis-sdd"]


def test_copias_em_sincronia():
    assert sync_skills.check(ROOT) == []


def _raiz_falsa(tmp_path: Path) -> Path:
    shutil.copytree(ROOT / ".agents/skills/artemis-sdd", tmp_path / ".agents/skills/artemis-sdd")
    sync_skills.sync(tmp_path)
    return tmp_path


def test_sync_recria_destino(tmp_path):
    raiz = _raiz_falsa(tmp_path)
    (raiz / ".claude/skills/artemis-sdd/lixo.txt").write_text("x", encoding="utf-8")
    sync_skills.sync(raiz)
    assert not (raiz / ".claude/skills/artemis-sdd/lixo.txt").exists()
    assert sync_skills.check(raiz) == []


def test_check_detecta_divergencia(tmp_path):
    raiz = _raiz_falsa(tmp_path)
    alvo = raiz / ".claude/skills/artemis-sdd/SKILL.md"
    alvo.write_bytes(alvo.read_bytes() + b"x")
    assert sync_skills.check(raiz) == ["SKILL.md"]


def test_check_detecta_arquivo_faltando_e_sobrando(tmp_path):
    raiz = _raiz_falsa(tmp_path)
    (raiz / ".claude/skills/artemis-sdd/extra.md").write_text("x", encoding="utf-8")
    (raiz / ".claude/skills/artemis-sdd/SKILL.md").unlink()
    assert sorted(sync_skills.check(raiz)) == ["SKILL.md", "extra.md"]


def _skill(raiz: Path, pasta: str, frontmatter: str) -> Path:
    d = raiz / pasta
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text(frontmatter, encoding="utf-8")
    return raiz


def test_validate_pega_name_errado(tmp_path):
    _skill(tmp_path, "minha-skill", "---\nname: outro\ndescription: ok\n---\ncorpo\n")
    erros = validate_skills.validate(tmp_path)
    assert len(erros) == 1 and "minha-skill" in erros[0]


def test_validate_aceita_aspas(tmp_path):
    _skill(tmp_path, "a", '---\nname: "a"\ndescription: \'texto: com dois pontos\'\n---\n')
    assert validate_skills.validate(tmp_path) == []


def test_validate_pega_description_vazia_longa_e_sem_frontmatter(tmp_path):
    _skill(tmp_path, "vazia", "---\nname: vazia\ndescription:\n---\n")
    _skill(tmp_path, "longa", f"---\nname: longa\ndescription: {'x' * 1025}\n---\n")
    _skill(tmp_path, "sem", "# sem frontmatter\n")
    erros = validate_skills.validate(tmp_path)
    assert len(erros) == 3
    assert any("vazia" in e for e in erros) and any("longa" in e for e in erros) and any("sem" in e for e in erros)


def test_validate_pega_pasta_sem_skill_md(tmp_path):
    (tmp_path / "oca").mkdir()
    assert any("oca" in e for e in validate_skills.validate(tmp_path))
