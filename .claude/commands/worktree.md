---
description: Cria uma worktree isolada para trabalhar em uma issue de um dos repositórios
---

Vou criar uma pasta de trabalho isolada (worktree) a partir da `staging`. Pergunte à pessoa, uma coisa de cada vez, se ainda não foi informado:

1. Qual repositório: docs, frontend, backend, agents ou rag.
2. Qual o número da issue. Se não houver issue, avise que toda tarefa precisa de uma issue e ajude a criá-la antes de seguir.
3. Uma descrição curta da tarefa (2 a 4 palavras).

Monte o nome da branch como `<tipo>/<nº>-<slug>`:
- `tipo` é um de `feat`, `fix`, `chore`, `docs`, `refactor`, `test` ou `ci`;
- `slug` é a descrição em minúsculas, sem acentos, com letras e números separados por hífen (exemplo: `feat/42-busca-semantica`).

Confirme o nome com a pessoa e então rode `python scripts/worktree.py new <repo> <tipo>/<nº>-<slug>` (use `python3` se `python` não existir). Mostre o caminho da worktree criada.

Por fim, lembre as regras:
- o commit ou a descrição do PR deve conter `Closes #<nº>` para fechar a issue;
- o PR deve ser aberto para a branch `staging`, nunca direto para a `main`.
