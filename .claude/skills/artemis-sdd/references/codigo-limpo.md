# Código limpo e clean architecture

Fonte única das regras de código do Artemis, para quem escreve código nos repos: pessoas e agentes.
Os quatro primeiros princípios foram adaptados de
[andrej-karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills) (MIT), que resume
as observações de Andrej Karpathy sobre os erros típicos de LLMs ao programar.

Os princípios pendem para a cautela, não para a velocidade. Ajuste o rigor ao tamanho da tarefa
(S0 a S3, veja o `SKILL.md`): um typo não pede cerimônia, só os hábitos.

## 1. Pense antes de codar

Não presuma. Não esconda a confusão. Exponha os tradeoffs.

- Declare as suposições. Se o pedido tem mais de uma leitura, nomeie as leituras em vez de
  escolher uma em silêncio.
- Se existe um caminho mais simples, diga e discorde.
- Se algo não está claro, pare e diga o que confunde.

As perguntas vêm ANTES de implementar: no brainstorming e na spec. No meio da tarefa, não escolha
em silêncio: pergunte. Em S0/S1, que pulam a spec, declare as suposições numa linha.

## 2. Simplicidade primeiro

O mínimo de código que resolve o problema. Nada especulativo.

- Nenhuma funcionalidade além do pedido.
- Nenhuma abstração para código de uso único.
- Nenhuma flexibilidade ou configuração que ninguém pediu.
- Nenhum tratamento de erro para cenário que não pode acontecer (isso não dispensa validar entrada
  que vem de fora do processo: usuário, arquivos, rede, ambiente, outro serviço).
- Se 200 linhas podem ser 50, reescreva. Pergunte: uma pessoa sênior acharia isto complicado demais?

## 3. Mudanças cirúrgicas

Toque só no que precisa. Limpe só a sua própria bagunça.

- Não "melhore" código, comentário ou formatação vizinhos.
- Não refatore o que não está quebrado. A refatoração do TDD vale só para o código que a tarefa
  escreveu ou alterou.
- Siga o estilo existente, mesmo que você faria diferente.
- Código morto que não é seu: mencione no PR, não apague.
- Sobras que a SUA mudança criou (imports, variáveis, funções que ficaram sem uso): remova.

**O teste:** toda linha alterada se explica pela tarefa.

## 4. Execução guiada por objetivo

Defina critérios de sucesso. Repita até verificar.

- "Adicionar validação" → "escrever testes para entradas inválidas e fazê-los passar".
- "Corrigir o bug" → "escrever um teste que o reproduz e fazê-lo passar".
- "Refatorar X" → "testes passam antes e depois".

Cada passo do plano tem uma checagem que dá para rodar ou observar (um teste, um comando e a saída
esperada), nunca "funciona". Relatório de review não é prova: rode as checagens você mesma.

## 5. Código limpo

- Nomes que dizem a intenção.
- Funções curtas, com uma responsabilidade.
- Sem números ou strings mágicos: valores de configuração vão para `config/`.
- Type hints em toda função pública.
- Erros explícitos: nada de `except: pass`.
- Sem código morto nem código comentado.
- Comentário explica o porquê, não o quê.
- Testes legíveis, no formato arrange, act, assert.

## 6. Clean architecture (hexagonal)

Padrão para `rag`, `agents` e `backend`:

```
adapters (inbound: CLI/HTTP · outbound: Chroma, LLM, arquivos)
     └──► application (use_cases + ports = interfaces)
               └──► domain (entidades e regras puras, sem libs externas)
```

- As dependências só apontam para dentro.
- O domínio não importa nada de I/O.
- Os use cases só conhecem as *ports* (interfaces), nunca um adapter concreto.
- A montagem (injeção de dependência) acontece num único ponto de entrada (`main`/`cli`).

## 7. Migração gradual

Módulo antigo só migra para as camadas quando uma tarefa já precisa mexer nele (mudança
cirúrgica). Nada de refatoração geral.

## Como isto é cobrado

- No CI: ruff com regras ampliadas e import-linter com o contrato de camadas bloqueiam o PR.
- Na revisão: o checklist do PR e a etapa de review do Superpowers usam este documento como critério.
