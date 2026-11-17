---
description: Prepara tudo para você começar no ArtemisHub (guia passo a passo, sem precisar ser dev)
---

Você vai guiar uma pessoa que pode NÃO ser desenvolvedora a preparar o ambiente do ArtemisHub. Use português simples, frases curtas, sem jargão. Antes de cada passo, explique em uma frase o que vai fazer e por quê. Depois de cada passo, diga se deu certo.

1. Confira as ferramentas, uma por vez, rodando `git --version`, `python --version` (ou `python3 --version` no macOS/Linux) e `docker --version`.
   - Git e Python (versão 3.11 ou mais nova) são obrigatórios. Docker é necessário só para rodar os serviços; se faltar, avise que dá para continuar e instalar depois.
   - Se algo faltar, explique como instalar, sem instalar nada sozinho:
     - Windows: Git em https://git-scm.com/download/win, Python em https://www.python.org/downloads/ (marque "Add python.exe to PATH") e Docker Desktop em https://www.docker.com/products/docker-desktop/. Alternativa pelo terminal: `winget install Git.Git`, `winget install Python.Python.3.12` e `winget install Docker.DockerDesktop`.
     - macOS: instale o Homebrew (https://brew.sh) e rode `brew install git python` e `brew install --cask docker`.
   - Peça para a pessoa me avisar quando terminar de instalar e rode a conferência de novo.
2. Com tudo pronto, explique que vai baixar os 5 repositórios do projeto (docs, frontend, backend, agents e rag) e rode `python scripts/setup.py` (use `python3` se `python` não existir).
3. Se o comando falhar, leia a mensagem de erro, explique o que ela significa em português simples e diga qual é o próximo passo. Nunca apague nem descarte arquivos da pessoa para resolver.
4. Ao terminar, resuma em poucas linhas o que ficou pronto (quais repositórios foram baixados) e sugira os próximos passos: `/sync` para atualizar os repositórios e `/worktree` para começar uma tarefa nova.
