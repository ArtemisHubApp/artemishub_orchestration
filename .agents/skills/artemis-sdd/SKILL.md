---
name: artemis-sdd
description: Use antes de qualquer mudança de código ou doc nos repos do Artemis (rag, agents, backend, frontend, docs). Classifica o tamanho da tarefa (S0 a S3), exige issue, worktree e docs atualizadas, diz onde salvar spec, plano e ADR, e traz o checklist de PR.
---

# artemis-sdd: fluxo de SDD do Artemis

Complementa o Superpowers com o que é só do Artemis. O trabalho acontece nos repos filhos
(`artemishub_rag`, `artemishub_agents`, `artemishub_backend`, `artemishub_frontend`,
`artemishub_docs`); o orquestrador só guarda regras e scripts. Antes de mexer num repo, leia o
`AGENTS.md` dele (ou o README, se ainda não existir).

## 1. Classifique a tarefa (S0 a S3)

Diga a classificação e o porquê numa linha antes de começar.

| Tamanho | Quando | O que fazer |
|---|---|---|
| **S0** | Edição trivial: typo, link, comentário, ajuste de uma linha sem efeito no comportamento | Editar direto (ainda com issue, worktree e PR). |
| **S1** | Mudança pequena e clara, sem decisão de design | Plano curto com critérios de aceite; teste antes do código se o comportamento mudar. |
| **S2/S3** | Funcionalidade nova, mudança que cruza módulos, risco alto ou decisão de arquitetura | Fluxo completo do Superpowers: `brainstorming` → spec → `writing-plans` → `test-driven-development` → `subagent-driven-development` ou `executing-plans` → `requesting-code-review` → `finishing-a-development-branch`. |

Na dúvida entre dois tamanhos, escolha o maior. Complexidade e risco (dados pessoais, segurança,
produção) sobem o tamanho.

## 2. Toda tarefa tem issue

Nada de código, doc ou configuração sem issue no kanban (rastreabilidade).

- Sem issue, crie com `gh issue create` (no repo certo) ou peça o número antes de começar.
- Inclua a issue no quadro (`gh project item-add 1 --owner ArtemisHubApp --url <URL da issue>`) e marque a Semana no card.
- Branch e PR carregam o número: `feat/<nº>-<slug>` e `Closes #<nº>` no PR.

## 3. Worktree, nunca direto na `staging` ou `main`

```
python scripts/worktree.py new <repo> <tipo>/<nº>-<slug>
```

Exemplo: `python scripts/worktree.py new rag feat/20-ocr-diretrizes`. Tipos: `feat`, `fix`,
`chore`, `docs`, `refactor`, `test`, `ci`. A worktree nasce de `origin/staging`, fica em
`../artemishub-worktrees/<repo>/<branch>/` e o PR vai para `staging`. Nunca commite direto em
`staging` nem em `main`. O checkout local do submódulo pode estar atrasado: use `git fetch` e
`git show origin/staging:<arquivo>` para ver o estado real.

## 4. Onde salvar cada coisa

- **Spec e plano:** no **repo do submódulo** afetado, em `docs/superpowers/specs/` e
  `docs/superpowers/plans/`, versionados no mesmo PR. Nunca no orquestrador.
- **ADR:** em `artemishub_docs/docs/adr/` (`NNN-titulo.md`, próximo número livre com 3 dígitos,
  no formato do ADR-002: contexto, decisão, alternativas, consequências, status; nav do `mkdocs.yml`
  e tabela de `docs/adr/index.md`), quando a mudança altera arquitetura,
  stack ou processo. Na etapa de spec, lembre disso: proponha o rascunho e a equipe aprova no PR.
- **Código limpo e arquitetura:** siga `references/codigo-limpo.md`.

## 5. Docs sempre atualizadas

Quando algo relevante muda (comportamento, comando, configuração, arquitetura, dependência),
atualize **no mesmo PR**: README e `AGENTS.md` do repo, `artemishub_docs` e ADR quando couber.
Inclui o **site no GitHub Pages** (gerado do `artemishub_docs`): se a mudança altera algo que
o site descreve, abra também um PR no `artemishub_docs` atualizando a página e cite os dois PRs
um no outro. Se o PR não mexeu em doc, a descrição diz por quê.

## 6. Checklist de PR

- [ ] `Closes #<nº>` na descrição e a branch com o número da issue
- [ ] Título no padrão Conventional Commits (`feat: ...`, `fix: ...`)
- [ ] Alvo é `staging`; revisão de outra integrante
- [ ] Testes escritos antes do código e passando (quando o comportamento mudou)
- [ ] Docs atualizadas, ou a descrição explica por que não
- [ ] ADR criado ou proposto, se mudou arquitetura, stack ou processo
- [ ] Revisado contra `references/codigo-limpo.md`
- [ ] Sem `.env`, segredos nem dados pessoais reais em fixtures (LGPD)

## Agentes sem o Superpowers nativo

Codex, Gemini e GPT não carregam as skills sozinhos. Antes da tarefa, abra
`.agents/skills/<skill>/SKILL.md` (por exemplo `brainstorming`, `writing-plans`,
`test-driven-development`) e siga o que está lá. O Claude recebe o Superpowers pelo plugin e esta
skill pela pasta `.claude/skills/`.

## Editando esta skill

A fonte editável é `.agents/skills/artemis-sdd/`. Depois de editar, rode
`python scripts/sync_skills.py` para atualizar `.claude/skills/artemis-sdd/`; o CI falha se as
duas cópias divergirem.
