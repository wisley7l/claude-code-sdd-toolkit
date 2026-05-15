---
description: Integracao opcional com vault central de memoria (segundo cerebro Obsidian) — detec, le e escreve em notas atomicas por projeto
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(test*), Bash(ls *), Bash(mkdir *), Bash(realpath*), Bash(pwd)
---

# Vault Memory — Integracao Opcional

Voce esta lendo o comportamento de **memoria persistente externa** do toolkit SDD. Esta integracao e **opt-in**: se o usuario configurou um vault central, voce le e escreve nele em notas atomicas; se nao, voce cai no fallback monolitico `thoughts/STATE.md`.

Este documento e referenciado pelos commands `gerador-prd`, `gerador-spec`, `executor-plan` e `quick-task`. Cada um chama o algoritmo de leitura no inicio e o de escrita ao final.

## 1. Deteccao do vault

```bash
test -n "$CLAUDE_VAULT_PATH" && test -d "$CLAUDE_VAULT_PATH"
```

- **`CLAUDE_VAULT_PATH` definida e aponta para diretorio existente** → modo vault ativo
- **Caso contrario** → modo legacy (`thoughts/STATE.md` monolitico, comportamento original)

Nunca infira o vault por outros caminhos. O usuario configura explicitamente via shell (ex: `export CLAUDE_VAULT_PATH=~/codigos/memory-obsidian/memory-obsidian`).

## 2. Resolucao de `<org>/<projeto>` (modo vault)

A memoria do projeto mora em `$CLAUDE_VAULT_PATH/<org>/<projeto>/state/`. Voce precisa derivar `<org>` e `<projeto>` corretamente.

**Heuristica padrao** (funciona se o usuario segue convenção `~/codigos/<org>/<projeto>/`):
1. Resolva o diretorio root do projeto (ja calculado pelos commands; e o repo principal, nao o worktree)
2. Se o path bate `*/codigos/<seg1>/<seg2>/...` → `<org>=<seg1>`, `<projeto>=<seg2>`
3. Verifique se `$CLAUDE_VAULT_PATH/<org>/<projeto>/` existe

**Quando a heuristica falha** (path fora do padrao, ou pasta nao existe no vault):
- Liste `ls $CLAUDE_VAULT_PATH/` (orgs disponiveis) e `ls $CLAUDE_VAULT_PATH/<org>/` (projetos)
- Pergunte ao usuario: "Detectei vault em `$CLAUDE_VAULT_PATH` mas nao identifiquei o projeto. Qual `<org>/<projeto>` usar? (ou `n` para pular vault desta sessao)"
- Se o projeto ainda nao existe no vault e o usuario confirma o slug: crie a estrutura (passo 4 abaixo)

## 3. Estrutura no vault

```
$CLAUDE_VAULT_PATH/<org>/<projeto>/state/
├── decisoes/        # Decisoes arquiteturais (era "Decisoes Arquiteturais" no STATE.md)
├── blockers/        # Blockers conhecidos
├── licoes/          # Licoes aprendidas
├── ideias/          # Ideias adiadas
└── preferencias/    # Preferencias do usuario (geralmente promovido para escopo global do vault)
```

**Nome de arquivo**: `<YYYY-MM-DD>-<slug-kebab>.md` (data ISO + slug curto do titulo).

## 4. Formato da nota atomica

```markdown
---
data: YYYY-MM-DD
tipo: decisao | blocker | licao | ideia | preferencia
titulo: Titulo legivel curto
tags: [opcional, palavras-chave]
---

# Titulo legivel

[Corpo: o fato/decisao/blocker em si — 1-3 paragrafos]

## Por que

[Motivo / Sintoma (se blocker) / Contexto que justifica registrar]

## Aplicar quando

[Quando essa informacao se torna relevante em uma sessao futura]

## Referencias

- `path/para/arquivo.ts:linha`
- POC: `thoughts/pocs/poc-X.md`
- PR: #NNN (se aplicavel)

↑ [[Comecar-aqui]]
```

**Regras**:
- Frontmatter `tipo` deve bater com a subpasta (`tipo: decisao` em `decisoes/`)
- `data` no frontmatter = data da decisao/observacao, nao do registro
- Use wikilinks `[[outra-nota]]` para conectar a outras memorias (Obsidian renderiza)

## 5. Algoritmo de leitura (inicio do command)

```
1. Se vault detectado E `<org>/<projeto>` resolvido:
   - Liste `state/decisoes/*.md`, `state/blockers/*.md`, `state/licoes/*.md`
   - Carregue notas cuja frontmatter `titulo` ou `tags` pareca relevante a tarefa atual
   - Use isso como contexto recuperado (mesma funcao que "Ler STATE.md" tinha)
2. Senao:
   - Leia `thoughts/STATE.md` se existir (comportamento legado)
```

Voce NUNCA carrega todas as notas indiscriminadamente — filtre por relevancia ao analisar o titulo de cada arquivo. Se uma das categorias estiver vazia, ignore.

## 6. Algoritmo de escrita (fim do command)

Identificou algo nao-obvio durante a tarefa (decisao, blocker, licao, ideia)? Proponha registrar:

```
Identifiquei algo util para registrar:

[Conteudo + tipo: decisao/blocker/licao/ideia]

Salvar? (s/n)
```

Se aprovado:

- **Modo vault**: crie `state/<tipo>s/<data>-<slug>.md` com o frontmatter e o formato da secao 4. Crie a subpasta se nao existir.
- **Modo legacy**: adicione entrada ao `thoughts/STATE.md` na secao correspondente (formato linha-unica conforme template original).

## 7. Criacao da estrutura (primeira vez)

Se o vault esta detectado mas `<vault>/<org>/<projeto>/state/` ainda nao existe:

```bash
mkdir -p "$CLAUDE_VAULT_PATH/<org>/<projeto>/state/decisoes"
mkdir -p "$CLAUDE_VAULT_PATH/<org>/<projeto>/state/blockers"
mkdir -p "$CLAUDE_VAULT_PATH/<org>/<projeto>/state/licoes"
mkdir -p "$CLAUDE_VAULT_PATH/<org>/<projeto>/state/ideias"
mkdir -p "$CLAUDE_VAULT_PATH/<org>/<projeto>/state/preferencias"
```

Crie apenas quando voce de fato tiver uma entrada para salvar (lazy) — nao crie estrutura vazia em todo `/gerador-prd`.

## 8. Fallback gracioso

Se em qualquer momento a integracao vault falhar (variavel nao definida, path quebrado, permissao negada, escrita falhou):
- **Caia no modo legacy** sem alarme — o command continua funcionando com `thoughts/STATE.md`
- Mencione brevemente ao usuario: "Vault nao acessivel; usando `thoughts/STATE.md`"
- Nao tente "consertar" o vault automaticamente

## 9. Quando invocado diretamente (`/vault-memory`)

O usuario tambem pode chamar este command sozinho. Nesse caso, reporte:
- Se vault esta detectado (com path)
- Qual `<org>/<projeto>` resolvido para o cwd atual
- Contagem de notas por categoria
- Sugestoes de cleanup (notas muito antigas, sem tags, etc) — opcional

---

**Regra de ouro**: a integracao vault e um valor agregado opcional. O toolkit deve funcionar identicamente para quem nao tem vault. Toda operacao de vault tem fallback.
