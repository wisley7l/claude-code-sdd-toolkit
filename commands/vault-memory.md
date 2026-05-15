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

↑ [[<NomeDoHub>]]
```

**Regras**:
- Frontmatter `tipo` deve bater com a subpasta (`tipo: decisao` em `decisoes/`)
- `data` no frontmatter = data da decisao/observacao, nao do registro
- Use wikilinks `[[outra-nota]]` para conectar a outras memorias (Obsidian renderiza)
- O rodape **sempre aponta para o hub do projeto**, nunca direto para `Comecar-aqui`. Apenas o hub aponta para `Comecar-aqui`. Isso mantem o grafo do Obsidian hierarquico (Comecar-aqui → hubs → notas).

## 4.1 Hub do projeto

Cada projeto no vault tem um arquivo de **hub** na raiz da pasta do projeto. Ele e o indice das memorias daquele projeto.

**Localizacao**: `$CLAUDE_VAULT_PATH/<org>/<projeto>/<NomeDoHub>.md`

**Como descobrir o nome do hub**:
```bash
ls "$CLAUDE_VAULT_PATH/<org>/<projeto>/"*.md 2>/dev/null
```
Pega o primeiro `*.md` na raiz (nao em subpastas) — esse e o hub. Cada projeto tem **um unico hub**.

**Se nao existir** (projeto novo no vault): voce vai criar — ver secao 7.

**Convencao de nome**: capitalize-first cada segmento separado por hyphen do slug do projeto. Ex: `gopay` → `Gopay.md`, `claude-code-sdd-toolkit` → `Claude-Code-Sdd-Toolkit.md`. Se ja existir um hub com nome diferente (apelido), use o existente (nao renomeie).

## 5. Algoritmo de leitura (inicio do command)

```
1. Se vault detectado E `<org>/<projeto>` resolvido:
   a. PRIMEIRO leia o **hub** do projeto (secao 4.1) — ele lista todas as memorias
      organizadas por categoria com hooks curtos. E o jeito eficiente de descobrir
      o que existe sem abrir cada arquivo.
   b. Identifique pelo hub quais notas individuais valem a pena abrir para a tarefa
      atual (filtre pelo hook, nao abra tudo).
   c. Abra apenas as notas individuais marcadas como relevantes.
   d. Se o hub nao existe ainda, caia para varredura direta:
      `state/decisoes/*.md`, `state/blockers/*.md`, `state/licoes/*.md` — carregue
      notas cuja `titulo`/`tags` no frontmatter pareca relevante.
2. Senao:
   - Leia `thoughts/STATE.md` se existir (comportamento legado)
```

Voce NUNCA carrega todas as notas indiscriminadamente — o hub e o filtro primario.

## 6. Algoritmo de escrita (fim do command)

Identificou algo nao-obvio durante a tarefa (decisao, blocker, licao, ideia)? Proponha registrar:

```
Identifiquei algo util para registrar:

[Conteudo + tipo: decisao/blocker/licao/ideia]

Salvar? (s/n)
```

Se aprovado:

- **Modo vault** — 3 passos sempre:
  1. Crie `state/<tipo>s/<data>-<slug>.md` com o frontmatter e o formato da secao 4, terminando com `↑ [[<NomeDoHub>]]`. Crie a subpasta se nao existir.
  2. **Atualize o hub** (`<NomeDoHub>.md`): adicione uma linha na secao correspondente (Decisões arquiteturais / Lições aprendidas / Blockers / Ideias / Preferências) no formato:
     ```
     - [[<slug-do-arquivo-sem-md>]] — hook curto da decisao (1 linha)
     ```
     Se a secao ainda nao existe no hub, crie-a (ver template do hub em [[##7-criacao-da-estrutura]]).
  3. Sem isso a nota fica orfa no indice — so descobrivel via graph view.

- **Modo legacy**: adicione entrada ao `thoughts/STATE.md` na secao correspondente (formato linha-unica conforme template original).

## 7. Criacao da estrutura (primeira vez)

Crie apenas quando voce de fato tiver uma entrada para salvar (lazy) — nao crie estrutura vazia em todo `/gerador-prd`.

### 7.1 Pasta do projeto e subpasta da categoria

```bash
mkdir -p "$CLAUDE_VAULT_PATH/<org>/<projeto>/state/<categoria>"
# <categoria> = decisoes | blockers | licoes | ideias | preferencias
```

So crie a subpasta da categoria que voce vai usar agora. As outras nascem na proxima vez que aparecer entrada do tipo (tambem lazy).

### 7.2 Hub do projeto (se ainda nao existe)

Se `ls $CLAUDE_VAULT_PATH/<org>/<projeto>/*.md` retorna vazio, crie o hub:

**Path**: `$CLAUDE_VAULT_PATH/<org>/<projeto>/<NomeDoHub>.md` (convencao de nome na secao 4.1)

**Template minimo** (preencha as secoes conforme for adicionando notas):

```markdown
# <Nome do Projeto>

[1-2 linhas descrevendo o projeto.]

Fonte autoritativa do projeto: `<path-do-repo>/` (`CLAUDE.md`, `ARCHITECTURE.md`, `.claude/skills/` se aplicavel). As memorias aqui sao complementares.

## Memórias do projeto

### Decisões arquiteturais

- [[<slug-da-primeira-nota>]] — hook curto

↑ [[Comecar-aqui]]
```

### 7.3 Registrar projeto no indice raiz

Apos criar o hub pela primeira vez, **atualize** `$CLAUDE_VAULT_PATH/Comecar-aqui.md` adicionando uma linha na secao da org correspondente:

```markdown
### <Org capitalizada>

- [[<NomeDoHub>]] — descricao curta do projeto
```

Se a secao da org ainda nao existe, crie-a. Sem isso o projeto fica invisivel no indice raiz.

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
