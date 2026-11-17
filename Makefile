# Atalhos opcionais (macOS/Linux/WSL). Tudo também funciona direto com `python scripts/...`.
PYTHON ?= $(shell command -v python3 2>/dev/null || command -v python)

.DEFAULT_GOAL := help
.PHONY: help setup sync status worktree prune prune-yes branches rag-query rag-demo

help: ## Lista os alvos disponíveis
	@grep -hE '^[a-zA-Z_%-]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "} {printf "  %-14s %s\n", $$1, $$2}'

setup: ## Baixa os submódulos e deixa cada um na branch base
	$(PYTHON) scripts/setup.py

sync: ## Atualiza os submódulos sem descartar mudanças locais
	$(PYTHON) scripts/sync.py

status: ## Mostra branch, mudanças e worktrees de cada repo
	$(PYTHON) scripts/status.py

worktree: ## Cria worktree: make worktree REPO=rag BRANCH=feat/20-ocr
	@test -n "$(REPO)" -a -n "$(BRANCH)" || { echo "Uso: make worktree REPO=rag BRANCH=feat/20-ocr" >&2; exit 2; }
	$(PYTHON) scripts/worktree.py new $(REPO) $(BRANCH)

prune: ## Mostra as worktrees que seriam removidas (ensaio, não apaga)
	$(PYTHON) scripts/worktree.py prune

prune-yes: ## Remove worktrees limpas de branches já mergeadas
	$(PYTHON) scripts/worktree.py prune --yes

branches: ## Lista branches já mergeadas nos repos
	$(PYTHON) scripts/branches.py

rag-query: ## Consulta o RAG no Docker: make rag-query Q="sua pergunta"
	@test -n "$(Q)" || { echo "Uso: make rag-query Q=\"sua pergunta\"" >&2; exit 2; }
	docker compose run --rm rag uv run python -m src.query "$(Q)"

rag-demo: ## Roda a demo do RAG no Docker
	docker compose run --rm rag uv run python -m src.demo

test-%: ## test-<servico> (ex.: make test-rag): roda os testes no Docker
	docker compose run --rm $* uv run pytest -q

shell-%: ## shell-<servico> (ex.: make shell-agents): abre um shell no Docker
	docker compose run --rm $* sh
