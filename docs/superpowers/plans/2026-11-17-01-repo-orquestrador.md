# Plano 1: repo `artemishub_orchestration`, implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** criar o repo guarda-chuva do Artemis. Ele reúne os 5 repos como submódulos, é a fonte única de regras para agentes (`AGENTS.md` e skills de SDD), traz scripts multiplataforma para setup, sync, worktrees e faxina de branches, sobe um compose de desenvolvimento e publica workflows de CI reutilizáveis.

**Architecture:** o repo não tem código de aplicação. Tudo o que é executável fica em `scripts/` (Python 3.11+, só biblioteca padrão), em cima de um módulo comum `scripts/artemis_repos.py`. As regras são texto (`AGENTS.md` e `.agents/skills/`), lido por qualquer agente. Hook, plugin e comandos do Claude são extras em `.claude/`. Os testes usam pytest com repositórios git temporários (remotos *bare* locais), sem rede.

**Tech Stack:** git (submódulos e worktrees), Python 3.11+ stdlib, pytest, ruff, uv (só para as dev deps), GitHub Actions, Docker Compose, `gh` CLI (opcional, em `branches.py` e `worktree.py prune`).

**Spec:** `docs/superpowers/specs/2026-11-17-artemishub-orchestration-design.md` (seções 6.1 a 6.12). Índice dos planos: `docs/superpowers/plans/2026-11-17-00-indice.md`.

## Global Constraints

- Submódulos, nesta ordem: `artemishub_docs`, `artemishub_frontend`, `artemishub_backend`, `artemishub_agents`, `artemishub_rag`. URLs `https://github.com/ArtemisHubApp/<repo>.git` (todas HTTPS). `branch = staging`.
- Branch base de trabalho: `staging`. Se `origin/staging` não existir, usar `main` e imprimir `AVISO: <repo> ainda não tem staging; usando main.`
- Worktrees em `<pai do orquestrador>/artemishub-worktrees/<repo>/<branch>/`, nunca dentro de um repo.
- Nome de branch: `^(feat|fix|chore|docs|refactor|test|ci)/\d+-[a-z0-9]+(-[a-z0-9]+)*$`.
- Scripts: Python ≥ 3.11, só biblioteca padrão, sem caminho absoluto fixo (tudo a partir de `Path(__file__).resolve().parents[1]`), funcionando em Windows, macOS e Linux. Nenhum link simbólico no repo.
- Nunca descartar mudança local: nada de `reset --hard`, `checkout -- .` ou `clean`.
- Textos para humanas em português. Mensagens de commit no padrão Conventional Commits.
- `AGENTS.md` com no máximo 250 linhas. `CLAUDE.md` e `GEMINI.md` contêm exatamente `@AGENTS.md\n`.
- Skills do Superpowers copiadas do `artemishub_rag` @ `cc5459c` (`.agents/skills/`), **sem** a `orchestrator`. Os hashes vão para o `skills-lock.json` sem alteração.
- `.gitattributes`: `* text=auto eol=lf`.

## Review Focus

1. **Repo ainda sem `staging`** (antes do Plano 5): setup, sync e worktree devem usar `main` e avisar, sem falhar. Teste na Task 2.
2. **Submódulo com mudança não commitada no `sync`:** pular aquele repo com aviso e nunca descartar nada. Teste na Task 3.
3. **Branch mergeada por *squash*:** a branch não é ancestral da base, então `git branch --merged` não a vê. `branches.py` e `worktree.py prune` consultam o `gh`. Sem `gh`, classificam como `desconhecido` e **nunca** apagam. Teste na Task 4.
4. **Caminho estilo Windows no hook** (`C:\...\artemishub_rag\src\x.py`, barras invertidas, maiúsculas diferentes): o hook precisa reconhecer o submódulo. Teste na Task 7.
5. **Nome de branch automático de agente ou fora do padrão** (`claude/optimistic-meitner-8yac2i`, `Feat/OCR`, acentos): `worktree.py new` recusa e sugere `feat/<nº>-<slug>`. Teste na Task 4.
6. **Clone com `--recurse-submodules`**, que deixa os submódulos em *detached HEAD*: o `setup.py` coloca cada um na branch base. Teste na Task 3.

---

## Mapa de arquivos

```
.gitmodules  .gitignore  .gitattributes  pyproject.toml  .env.example  Makefile  docker-compose.yml
AGENTS.md  CLAUDE.md  GEMINI.md  README.md  skills-lock.json
scripts/artemis_repos.py      # comum: lista de repos, git(), base_branch(), worktrees_root()
scripts/setup.py  sync.py  status.py  worktree.py  branches.py
scripts/sync_skills.py  validate_skills.py
.agents/skills/<15 skills do Superpowers>/  .agents/skills/artemis-sdd/{SKILL.md,references/codigo-limpo.md}
.claude/skills/artemis-sdd/   # cópia gerada por sync_skills.py
.claude/settings.json  .claude/hooks/submodule_context.py  .claude/commands/{start,sync,worktree}.md
.github/workflows/ci.yml  gitleaks.yml  python-ci.yml
tests/conftest.py  tests/test_*.py
```

Decisões minhas que desviam do texto do spec, sem mudar a intenção:
- `validate-skills` e `skills-in-sync` viram dois jobs de um único `.github/workflows/ci.yml`, junto com os testes dos scripts.
- A fonte editável da `artemis-sdd` é `.agents/skills/artemis-sdd/`, e o `.claude/` recebe a cópia. Assim, todas as skills de `.agents/` ficam no mesmo lugar.
- O índice do Chroma fica no *bind mount* do repo, onde o `rag` já grava. O volume nomeado de modelos é só o cache do Hugging Face.

---

### Task 1: esqueleto do repo e fixture de testes

**Files:**
- Create: `.gitmodules` (via `git submodule add`), `.gitignore`, `.gitattributes`, `pyproject.toml`, `tests/conftest.py`, `tests/test_repo_layout.py`

**Interfaces:**
- Produces: a fixture `fake_org(tmp_path) -> FakeOrg`, com `FakeOrg.root: Path` (orquestrador falso com os 5 submódulos), `FakeOrg.remotes: dict[str, Path]` (remotos *bare*), `FakeOrg.push_commit(repo: str, branch: str, filename: str) -> str` (commit novo no remoto, devolve o SHA) mais a fixture irmã `fake_org_sem_staging`, igual à `fake_org` mas com remotos só com `main` (Review Focus 1). Os submódulos usam `file://` com `-c protocol.file.allow=always`.

- [ ] **Step 1:** `git submodule add -b staging https://github.com/ArtemisHubApp/<repo>.git <repo>` para os 5 repos, na ordem dos Global Constraints. Enquanto não houver `staging` no remoto, use `-b main` e depois edite o `.gitmodules` para `branch = staging`.
- [ ] **Step 2:** crie o `.gitignore` (`.env*`, `!.env.example`, `.venv/`, `__pycache__/`, `.pytest_cache/`, `.DS_Store`, `artemishub-worktrees/`), o `.gitattributes` (`* text=auto eol=lf`) e o `pyproject.toml` (`name = "artemishub-orchestration"`, `requires-python = ">=3.11"`, sem dependências, `[dependency-groups] dev = ["pytest>=8", "ruff>=0.6"]`, `[tool.ruff] line-length = 120`, `[tool.pytest.ini_options] testpaths = ["tests"]`).
- [ ] **Step 3: escreva o teste**

```python
def test_gitmodules_lista_os_5_repos_https_staging():
    cfg = parse_gitmodules(ROOT / ".gitmodules")  # configparser simples no próprio teste
    assert [s["path"] for s in cfg] == ["artemishub_docs", "artemishub_frontend", "artemishub_backend",
                                        "artemishub_agents", "artemishub_rag"]
    assert all(s["url"] == f"https://github.com/ArtemisHubApp/{s['path']}.git" for s in cfg)
    assert all(s["branch"] == "staging" for s in cfg)

def test_sem_symlinks_no_repo():
    tracked = subprocess.run(["git", "ls-files", "-s"], capture_output=True, text=True, cwd=ROOT).stdout
    assert not [l for l in tracked.splitlines() if l.startswith("120000")]

def test_fake_org_fixture(fake_org):
    assert (fake_org.root / "artemishub_rag" / ".git").exists()
```

- [ ] **Step 4:** implemente o `conftest.py`, rode `uv run pytest tests/test_repo_layout.py -v` e espere PASS.
- [ ] **Step 5:** commit `chore: esqueleto do orquestrador com os 5 submódulos`.

### Task 2: módulo comum `scripts/artemis_repos.py`

**Files:** Create `scripts/artemis_repos.py` e `tests/test_artemis_repos.py`.

**Interfaces:**
- Produces:
  - `ROOT: Path`
  - `REPOS: tuple[str, ...]`, com os 5 repos na ordem
  - `resolve_repo(name: str) -> str`, que aceita `rag` ou `artemishub_rag` e levanta `SystemExit` com a lista válida
  - `git(*args: str, cwd: Path, check: bool = True) -> str`, que devolve o stdout sem espaços nas pontas
  - `base_branch(repo_dir: Path) -> str`, que devolve `"staging"` ou `"main"` com o aviso dos Global Constraints em stderr
  - `is_dirty(repo_dir: Path) -> bool`
  - `worktrees_root(root: Path = ROOT) -> Path`, que é `root.parent / "artemishub-worktrees"`
  - Todas as funções aceitam `root` ou `repo_dir` explícitos, para os testes.

- [ ] **Step 1: escreva os testes**

```python
def test_resolve_repo_aceita_curto_e_longo():
    assert resolve_repo("rag") == resolve_repo("artemishub_rag") == "artemishub_rag"
def test_resolve_repo_invalido(): 
    with pytest.raises(SystemExit): resolve_repo("xyz")
def test_base_branch_staging(fake_org):
    assert base_branch(fake_org.root / "artemishub_rag") == "staging"
def test_base_branch_sem_staging_usa_main_e_avisa(fake_org_sem_staging, capsys):
    assert base_branch(fake_org_sem_staging.root / "artemishub_rag") == "main"
    assert "ainda não tem staging; usando main" in capsys.readouterr().err
def test_worktrees_root_fica_fora_do_repo(tmp_path):
    assert worktrees_root(tmp_path / "orq") == tmp_path / "artemishub-worktrees"
```

- [ ] **Step 2:** rode e veja FAIL (*module not found*).
- [ ] **Step 3:** implemente. Em `base_branch`, use `git ls-remote --heads origin staging` (sem depender de fetch prévio).
- [ ] **Step 4:** rode `uv run pytest tests/test_artemis_repos.py -v` e espere PASS.
- [ ] **Step 5:** commit `feat: módulo comum dos scripts`.

### Task 3: `setup.py`, `sync.py` e `status.py`

**Files:** Create `scripts/setup.py`, `scripts/sync.py`, `scripts/status.py` e `tests/test_setup_sync_status.py`.

**Interfaces:**
- Consumes: Task 2.
- Produces:
  - `setup.main(root: Path = ROOT) -> int`: confere `git` no PATH e Python ≥ 3.11; roda `git submodule update --init --recursive`; para cada repo faz `fetch`, `checkout <base>` e `pull --ff-only`, ou cria a branch local rastreando `origin/<base>`; ao final imprime `Pronto: 5 repos em <base>`. Devolve 0 em caso de sucesso.
  - `sync.main(root) -> int`: roda `pull --ff-only` no orquestrador; para cada repo, se `is_dirty`, imprime `PULADO <repo>: há mudanças locais não commitadas` e segue para o próximo; senão faz checkout da base e `pull --ff-only` e imprime `git log --oneline <antes>..<depois>` (ou `sem novidades`).
  - `status.collect(root) -> list[dict]`, com as chaves `repo`, `branch`, `dirty: bool`, `ahead: int`, `behind: int` e `worktrees: int`. `status.main` imprime uma tabela.

- [ ] **Step 1: escreva os testes**

```python
def test_setup_tira_submodulos_do_detached_head(fake_org):
    detach_all(fake_org)                          # helper: git checkout --detach em cada submódulo
    assert setup.main(fake_org.root) == 0
    assert all(git("branch", "--show-current", cwd=fake_org.root / r) == "staging" for r in REPOS)

def test_sync_traz_commit_novo(fake_org, capsys):
    sha = fake_org.push_commit("artemishub_rag", "staging", "novo.txt")
    sync.main(fake_org.root)
    assert git("rev-parse", "HEAD", cwd=fake_org.root / "artemishub_rag") == sha

def test_sync_pula_repo_sujo_sem_descartar(fake_org, capsys):
    f = fake_org.root / "artemishub_rag" / "rascunho.py"; f.write_text("x=1")
    fake_org.push_commit("artemishub_rag", "staging", "novo.txt")
    sync.main(fake_org.root)
    assert "PULADO artemishub_rag" in capsys.readouterr().out and f.read_text() == "x=1"

def test_status_conta_sujo_e_atraso(fake_org):
    (fake_org.root / "artemishub_docs" / "a.md").write_text("a")
    fake_org.push_commit("artemishub_rag", "staging", "b.txt"); git("fetch", cwd=fake_org.root / "artemishub_rag")
    rows = {r["repo"]: r for r in status.collect(fake_org.root)}
    assert rows["artemishub_docs"]["dirty"] and rows["artemishub_rag"]["behind"] == 1
```

- [ ] **Step 2:** rode e veja FAIL.
- [ ] **Step 3:** implemente os três scripts. Cada um tem um `if __name__ == "__main__": raise SystemExit(main())` e um `--root` oculto no `argparse`.
- [ ] **Step 4:** rode `uv run pytest tests/test_setup_sync_status.py -v` e espere PASS.
- [ ] **Step 5:** commit `feat: setup, sync e status multiplataforma`.

### Task 4: `worktree.py` e `branches.py`

**Files:** Create `scripts/worktree.py`, `scripts/branches.py` e `tests/test_worktree_branches.py`.

**Interfaces:**
- Consumes: Task 2.
- Produces:
  - `BRANCH_RE` (a regex dos Global Constraints).
  - `worktree.validate_branch(name: str) -> None`: levanta `SystemExit` com uma mensagem que contém `use feat/<nº issue>-<slug>`.
  - `worktree.new(repo: str, branch: str, root: Path = ROOT) -> Path`: faz `fetch`, depois `git worktree add -b <branch> <worktrees_root>/<repo>/<branch> origin/<base>` e devolve o caminho. Se o caminho já existir, levanta `SystemExit`.
  - `worktree.list_(root) -> list[dict]`, com as chaves `repo`, `branch` e `path`.
  - `worktree.prune(root, dry_run: bool = True) -> list[Path]`: remove só as worktrees que `merged_status` dá como `mergeada` e que não estão sujas.
  - `branches.merged_status(repo_dir: Path, branch: str, base: str) -> Literal["mergeada", "aberta", "desconhecido"]`: primeiro tenta `gh pr list --head <branch> --state merged --json number`. Sem `gh` ou se ele falhar, recorre a `git merge-base --is-ancestor` (devolve `mergeada` se for ancestral, senão `desconhecido`).
  - `branches.main(root, delete: bool)`: lista as branches remotas (menos `main` e `staging`) com o status. Com `--delete`, pede confirmação `s/N` por repo e apaga **só** as `mergeada`, com `git push origin --delete`.

- [ ] **Step 1: escreva os testes**

```python
@pytest.mark.parametrize("nome", ["claude/optimistic-meitner-8yac2i", "Feat/OCR", "feat/ocr", "feat/20-ocr_diretrizes", "feat/20-ação"])
def test_branch_fora_do_padrao_recusada(nome):
    with pytest.raises(SystemExit, match="use feat/<nº issue>-<slug>"): validate_branch(nome)

def test_new_cria_fora_do_repo_a_partir_de_staging(fake_org):
    p = worktree.new("rag", "feat/20-ocr-diretrizes", fake_org.root)
    assert p == fake_org.root.parent / "artemishub-worktrees/artemishub_rag/feat/20-ocr-diretrizes"
    assert git("rev-parse", "HEAD", cwd=p) == git("rev-parse", "origin/staging", cwd=fake_org.root / "artemishub_rag")

def test_new_sem_staging_usa_main(fake_org_sem_staging): ...   # HEAD == origin/main

def test_squash_sem_gh_e_desconhecido_e_nao_apaga(fake_org, monkeypatch):
    monkeypatch.setattr(shutil, "which", lambda _: None)
    # branch empurrada e "squash-mergeada" (conteúdo copiado para staging num commit novo, sem ancestralidade)
    assert branches.merged_status(repo_dir, "feat/1-x", "staging") == "desconhecido"
    assert worktree.prune(fake_org.root, dry_run=False) == []

def test_prune_remove_worktree_mergeada_limpa(fake_org): ...   # merge real (ancestral) → removida
```

- [ ] **Step 2:** rode e veja FAIL.
- [ ] **Step 3:** implemente. `worktree.py` tem os subcomandos `new <repo> <branch>`, `list` e `prune [--yes]`; sem `--yes`, o `prune` só mostra o que faria.
- [ ] **Step 4:** rode `uv run pytest tests/test_worktree_branches.py -v` e espere PASS.
- [ ] **Step 5:** commit `feat: worktrees a partir da staging e faxina segura de branches`.

### Task 5: skills, com o Superpowers copiado e a `artemis-sdd`

**Files:**
- Create: `.agents/skills/<15 skills>` (copiadas de `artemishub_rag/.agents/skills` @ `cc5459c`, menos a `orchestrator`), `skills-lock.json` (entradas do lock do rag, menos `orchestrator`), `.agents/skills/artemis-sdd/SKILL.md`, `.agents/skills/artemis-sdd/references/codigo-limpo.md`, `scripts/sync_skills.py`, `scripts/validate_skills.py` e `tests/test_skills.py`
- Generate: `.claude/skills/artemis-sdd/`

**Interfaces:**
- Produces:
  - `sync_skills.sync(root) -> None`: copia `.agents/skills/artemis-sdd` para `.claude/skills/artemis-sdd`, apagando e recriando o destino.
  - `sync_skills.check(root) -> list[str]`: devolve os arquivos que diferem (vazio quando está em dia). O CLI aceita `--check` e sai com código 1 quando há diferença.
  - `validate_skills.validate(skills_dir: Path) -> list[str]`: devolve os erros. Cada `SKILL.md` precisa de frontmatter YAML com `name` igual ao nome da pasta e `description` não vazia, com no máximo 1024 caracteres. O parse é feito à mão: só linhas `chave: valor` entre `---`.

**Conteúdo da `artemis-sdd/SKILL.md`:** `name: artemis-sdd`. A `description` começa com "Use antes de qualquer mudança de código ou doc nos repos do Artemis". O corpo tem:
1. classificar a tarefa de S0 a S3 (S0 = edição trivial direta; S1 = plano curto com critérios de aceite e teste se o comportamento mudar; S2/S3 = brainstorming → spec → plano → TDD → execução → review do Superpowers);
2. issue no kanban antes de codar, com a semana marcada;
3. worktree com `python scripts/worktree.py new <repo> <tipo>/<nº>-<slug>`, nunca commit direto em `staging` ou `main`;
4. spec e plano salvos no **repo do submódulo**, em `docs/superpowers/{specs,plans}/`;
5. ADR no `artemishub_docs` (`docs/arquitetura/decisoes/`) quando a mudança muda arquitetura, stack ou processo;
6. checklist de PR (`Closes #`, título no padrão Conventional Commits, testes, docs, ADR, `codigo-limpo.md`);
7. para agentes sem o Superpowers nativo: "abra `.agents/skills/<skill>/SKILL.md` e siga".

**Conteúdo do `codigo-limpo.md`:** as seções 1 a 4 do `artemishub_rag/.agents/skills/orchestrator/references/coding-principles.md`, mantendo a nota de atribuição (andrej-karpathy-skills, MIT) e tirando as menções a etapas que não existem (`grill`, `build`, tiers T0–T3). Depois vêm a lista de código limpo e o diagrama e as regras de clean architecture, copiados do spec 6.12 item 1, mais a regra de migração gradual.

- [ ] **Step 1: escreva os testes**

```python
def test_skills_validas(): assert validate_skills.validate(ROOT / ".agents/skills") == []
def test_sem_orchestrator(): assert not (ROOT / ".agents/skills/orchestrator").exists()
def test_lock_bate_com_pastas():
    lock = json.loads((ROOT / "skills-lock.json").read_text())["skills"]
    pastas = {p.name for p in (ROOT / ".agents/skills").iterdir()} - {"artemis-sdd"}
    assert set(lock) == pastas and len(pastas) == 15
def test_claude_tem_so_artemis_sdd():
    assert [p.name for p in (ROOT / ".claude/skills").iterdir()] == ["artemis-sdd"]
def test_copias_em_sincronia(): assert sync_skills.check(ROOT) == []
def test_check_detecta_divergencia(tmp_path): ...   # copia árvore, altera 1 byte no .claude → lista não vazia
def test_validate_pega_name_errado(tmp_path): ...   # name: outro → erro citando a pasta
```

- [ ] **Step 2:** rode e veja FAIL.
- [ ] **Step 3:** copie as skills e o lock, escreva os dois textos, implemente os scripts e rode `python scripts/sync_skills.py`.
- [ ] **Step 4:** rode `uv run pytest tests/test_skills.py -v` e espere PASS.
- [ ] **Step 5:** commit `feat: skills centralizadas (Superpowers + artemis-sdd)`.

### Task 6: `AGENTS.md`, `CLAUDE.md`, `GEMINI.md` e `README.md`

**Files:** Create os quatro arquivos e `tests/test_agents_md.py`.

**Conteúdo do `AGENTS.md`:** as seções do spec 6.2 (itens 1 a 7), com os títulos exatos do teste. Inclui:
- a regra de worktree e staging (6.10);
- as 6 regras de higiene (6.11);
- a regra de ADR (6.9);
- a regra "skills só no orquestrador";
- a tabela de repos com stack e comando de execução **conferidos em cada README**: `rag` → `python -m src.demo` e `python -m src.query "<pergunta>"`; `agents` → `uv run pytest`; `backend`/`frontend` → "sem scaffold".

O `README.md` é para humanas:
- o primeiro uso (`git clone --recurse-submodules` + `python scripts/setup.py`);
- uma seção "Usa ChatGPT no navegador? Anexe o AGENTS.md";
- uma tabela de comandos com o equivalente `make` para cada script.

- [ ] **Step 1: escreva os testes**

```python
TITULOS = ["## O que é o Artemis", "## Repositórios", "## Regra de ouro", "## Regras de SDD",
           "## Branches e worktrees", "## Higiene do GitHub", "## Código limpo", "## Decisões (ADR)",
           "## Kanban", "## Segurança", "## Submódulos: cuidados"]
def test_agents_md_tem_secoes_e_tamanho():
    t = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert all(h in t for h in TITULOS) and len(t.splitlines()) <= 250
def test_links_locais_existem():   # todo link relativo [x](caminho) do AGENTS.md aponta para arquivo existente
    ...
def test_claude_e_gemini_importam():
    assert (ROOT / "CLAUDE.md").read_text() == (ROOT / "GEMINI.md").read_text() == "@AGENTS.md\n"
```

- [ ] **Step 2:** rode e veja FAIL.
- [ ] **Step 3:** escreva os textos.
- [ ] **Step 4:** rode `uv run pytest tests/test_agents_md.py -v` e espere PASS. Depois, verificação manual: num Gemini CLI, `/memory show` precisa listar o conteúdo do `AGENTS.md`. Se não listar, crie `.gemini/settings.json` com `{"context": {"fileName": ["AGENTS.md"]}}`, troque o `GEMINI.md` por esse arquivo e ajuste o teste.
- [ ] **Step 5:** commit `docs: AGENTS.md como fonte única para todos os agentes`.

### Task 7: camada Claude (hook, settings e comandos)

**Files:** Create `.claude/hooks/submodule_context.py`, `.claude/settings.json`, `.claude/commands/start.md`, `.claude/commands/sync.md`, `.claude/commands/worktree.md` e `tests/test_hook.py`.

**Interfaces:**
- Produces:
  - `submodule_context.handle(payload: dict, root: Path, state_dir: Path) -> dict | None`: lê `payload["tool_input"]["file_path"]` (ou `"path"`) e `payload["session_id"]`. Se o arquivo estiver dentro de `root/<repo>` para algum `repo` em `REPOS`, e não existir o marcador `state_dir/<session_id>-<repo>`, cria o marcador e devolve `{"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": "Você está em <repo>. Leia <repo>/AGENTS.md (ou README.md) antes de alterar."}}`. Nos demais casos devolve `None`.
  - O `main()` lê o JSON do stdin, usa `root` de `CLAUDE_PROJECT_DIR` ou do caminho do script e `state_dir = tempfile.gettempdir()/artemis-hook`, imprime o JSON se houver e **sempre** sai com código 0, inclusive com JSON inválido.
  - Os caminhos são comparados com `os.path.normcase(os.path.abspath(...))` (Review Focus 4). O hook não importa `scripts/`: a lista `REPOS` fica repetida nele, e um teste garante que as duas listas batem.
- **`settings.json`:**
  - `hooks.PreToolUse` com `matcher: "Read|Edit|Write"` e `command: "python \"$CLAUDE_PROJECT_DIR/.claude/hooks/submodule_context.py\""`;
  - `permissions.deny` com `Read(**/.venv/**)`, `Read(**/node_modules/**)`, `Read(**/data/**)`, `Read(**/chroma*/**)` e `Read(**/*.lock)`;
  - `extraKnownMarketplaces` + `enabledPlugins` para o Superpowers. Antes de escrever, confira o nome exato do marketplace no README de `obra/superpowers`; o esperado é `superpowers@superpowers-marketplace`.
- **Comandos:**
  - `start.md`: confere git, Python e Docker, roda `python scripts/setup.py` e explica cada passo em português simples, para quem não é dev.
  - `sync.md`: roda `python scripts/sync.py` e resume o que mudou por repo.
  - `worktree.md`: pergunta o repo e o nº da issue e roda `python scripts/worktree.py new`.

- [ ] **Step 1: escreva os testes**

```python
def test_avisa_uma_vez_por_sessao(tmp_path):
    p = {"session_id": "s1", "tool_input": {"file_path": str(ROOT / "artemishub_rag/src/query.py")}}
    out = handle(p, ROOT, tmp_path)
    assert "artemishub_rag/AGENTS.md" in out["hookSpecificOutput"]["additionalContext"]
    assert handle(p, ROOT, tmp_path) is None
def test_caminho_windows(tmp_path, monkeypatch):   # Review Focus 4
    monkeypatch.setattr(os.path, "normcase", str.lower)
    p = {"session_id": "s2", "tool_input": {"file_path": str(ROOT).upper() + "\\ARTEMISHUB_RAG\\src\\x.py"}}
    assert handle(p, ROOT, tmp_path) is not None   # normalize "\\" → os.sep antes de comparar
def test_fora_de_submodulo(tmp_path): assert handle({"session_id": "s", "tool_input": {"file_path": str(ROOT / "README.md")}}, ROOT, tmp_path) is None
def test_json_invalido_sai_zero(): assert subprocess.run([sys.executable, HOOK], input="{", text=True).returncode == 0
def test_repos_iguais_aos_scripts(): assert hook.REPOS == artemis_repos.REPOS
def test_settings_json_valido_e_com_hook(): ...   # json.loads + matcher == "Read|Edit|Write"
```

- [ ] **Step 2:** rode e veja FAIL.
- [ ] **Step 3:** implemente e escreva os arquivos.
- [ ] **Step 4:** rode `uv run pytest tests/test_hook.py -v` e espere PASS. Depois, verificação manual no Claude Code aberto na raiz: ler `artemishub_rag/README.md` precisa mostrar o aviso uma vez, e `/plugin` precisa listar o Superpowers habilitado.
- [ ] **Step 5:** commit `feat: camada Claude com hook de contexto, plugin Superpowers e comandos`.

### Task 8: `docker-compose.yml`, `.env.example` e `Makefile`

**Files:** Create `docker-compose.yml`, `.env.example`, `Makefile` e `tests/test_compose_make.py`.

**Conteúdo do compose:**
- Âncora comum `x-uv-service`:
  - `image: ghcr.io/astral-sh/uv:python3.12-bookworm-slim`;
  - `working_dir: /app`;
  - `environment: {UV_LOCKED: "1", UV_LINK_MODE: copy, HF_HOME: /cache/hf}`;
  - volume `hf-cache:/cache/hf`.
- Serviço `rag`: `./artemishub_rag:/app`, `rag-venv:/app/.venv`, `env_file: [{path: ./artemishub_rag/.env, required: false}]` e `command: ["uv", "run", "python", "-m", "src.query", "--help"]`.
- Serviço `agents`: o mesmo molde, com `agents-venv` e `command: ["uv", "run", "pytest", "-q"]`.
- Serviços `backend` e `frontend`: `profiles: ["app"]`, `image: busybox` e `command: ["echo", "<repo> ainda sem scaffold; veja o plano da semana 6"]`.

**`.env.example`:** só comentários explicando que cada submódulo tem o próprio `.env`. Por enquanto não há variáveis do orquestrador.

**`Makefile`:**
- alvos `setup`, `sync`, `status`, `worktree` (`REPO=` `BRANCH=`), `prune`, `branches`, `rag-query` (`Q=`), `rag-demo`, `test-%`, `shell-%` e `help`;
- cada alvo chama um script ou `docker compose run --rm`;
- `help` lista os comentários `##`.

- [ ] **Step 1: escreva os testes**

```python
def test_compose_valido():   # skip se docker ausente
    r = subprocess.run(["docker", "compose", "config", "-q"], cwd=ROOT); assert r.returncode == 0
def test_compose_servicos_e_profiles():
    cfg = json.loads(subprocess.run(["docker", "compose", "--profile", "app", "config", "--format", "json"],
                                    cwd=ROOT, capture_output=True, text=True).stdout)
    assert set(cfg["services"]) == {"rag", "agents", "backend", "frontend"}
    assert cfg["services"]["rag"]["environment"]["UV_LOCKED"] == "1"
def test_make_help_lista_alvos():   # skip se make ausente
    out = subprocess.run(["make", "help"], cwd=ROOT, capture_output=True, text=True).stdout
    assert all(a in out for a in ["setup", "sync", "worktree", "rag-query"])
```

- [ ] **Step 2:** rode e veja FAIL.
- [ ] **Step 3:** escreva os arquivos.
- [ ] **Step 4:** rode `uv run pytest tests/test_compose_make.py -v` e espere PASS. Depois, verificação manual: `docker compose run --rm rag uv run python -m src.query "O que diz a Lei 14.611?"` precisa imprimir trechos com fonte (sem LLM configurado, só evidências). Se o `uv.lock` do `rag` estiver desatualizado, o `UV_LOCKED=1` falha de propósito. Nesse caso, registre uma issue para o Plano 4 em vez de afrouxar a regra.
- [ ] **Step 5:** commit `feat: compose de desenvolvimento para rag e agents`.

### Task 9: workflows (CI do orquestrador, gitleaks e `python-ci` reutilizável)

**Files:** Create `.github/workflows/ci.yml`, `.github/workflows/gitleaks.yml`, `.github/workflows/python-ci.yml` e `tests/test_workflows.py`.

**Conteúdo dos workflows:**
- **`ci.yml`:** roda em `pull_request` e em `push` para `staging` e `main`. Jobs:
  - `tests`: `uv sync --locked --dev`, `ruff check`, `ruff format --check` e `pytest`; checkout com `submodules: false`, já que os testes usam a `fake_org`;
  - `skills`: `python scripts/validate_skills.py` e `python scripts/sync_skills.py --check`.
- **`gitleaks.yml`:** `gitleaks/gitleaks-action@v2` em PRs e pushes.
- **`python-ci.yml`:** `on: workflow_call`. Inputs: `python-versions` (string JSON, default `'["3.12"]'`) e `run-pyright` (boolean, default `true`). Jobs:
  1. `no-local-skills`: falha com `::error::skills ficam no artemishub_orchestration` se existir `.claude/skills`, `.agents/skills`, `agent/skills` ou `skills-lock.json`.
  2. `lint`: `astral-sh/setup-uv@v6`, `uv lock --check`, `uv sync --locked --dev`, `uv run ruff check .` e `uv run ruff format --check .`. Se o `pyproject.toml` tiver `[tool.importlinter]`, roda também `uv run lint-imports`. Por fim, `uvx pyright` com `continue-on-error: true` (só avisa).
  3. `test`: matriz `fromJSON(inputs.python-versions)` com `uv sync --locked --dev` e `uv run pytest -q`.
  4. `pr-title`: só em `pull_request`, com `amannn/action-semantic-pull-request@v5` e os tipos `feat, fix, chore, docs, refactor, test, ci`.
  5. `gitleaks`.
- Use `permissions: contents: read` em todos, mais `pull-requests: read` no `pr-title`.

- [ ] **Step 1: escreva os testes** (parse de YAML com `yaml` só se estiver instalado; senão, `pytest.importorskip("yaml")` e PyYAML no grupo dev)

```python
def test_python_ci_reutilizavel():
    wf = load("python-ci.yml"); assert "workflow_call" in wf[True] or "workflow_call" in wf["on"]
    assert set(wf["jobs"]) == {"no-local-skills", "lint", "test", "pr-title", "gitleaks"}
def test_lint_checa_lock_e_locked():
    steps = " ".join(s.get("run", "") for s in load("python-ci.yml")["jobs"]["lint"]["steps"])
    assert "uv lock --check" in steps and "uv sync --locked" in steps and "lint-imports" in steps
def test_no_local_skills_cobre_as_4_formas():
    run = load("python-ci.yml")["jobs"]["no-local-skills"]["steps"][-1]["run"]
    assert all(p in run for p in [".claude/skills", ".agents/skills", "agent/skills", "skills-lock.json"])
```

- [ ] **Step 2:** rode e veja FAIL.
- [ ] **Step 3:** escreva os workflows. Se `actionlint` existir, rode `actionlint` e espere nenhum erro.
- [ ] **Step 4:** rode `uv run pytest tests/test_workflows.py -v` e espere PASS.
- [ ] **Step 5:** commit `ci: CI do orquestrador, gitleaks e python-ci reutilizável`.

### Task 10: verificação final e publicação

- [ ] **Step 1:** rode `uv run pytest -q && uv run ruff check . && python scripts/validate_skills.py && python scripts/sync_skills.py --check`. Tudo precisa passar.
- [ ] **Step 2:** faça o clone limpo noutra pasta: `git clone --recurse-submodules <repo local> /tmp/orq && python /tmp/orq/scripts/setup.py`, que precisa terminar com `Pronto: 5 repos em <base>`. Depois, `python scripts/worktree.py new rag feat/1-teste` cria `../artemishub-worktrees/artemishub_rag/feat/1-teste`. Remova a worktree e a branch de teste em seguida.
- [ ] **Step 3:** confira os critérios de sucesso 1 a 4 da seção 8 do spec que dependem só deste repo, numa sessão nova do Claude Code, do Codex e do Gemini CLI aberta na raiz. Os critérios de CI nos filhos, ADRs e `.github` ficam para os planos 2 a 5.
- [ ] **Step 4 (pessoa com acesso à org):** criar `ArtemisHubApp/artemishub_orchestration` (público), fazer push da `main`, criar `staging` a partir dela e torná-la branch padrão. Atualizar o índice dos planos: Plano 1 concluído.
