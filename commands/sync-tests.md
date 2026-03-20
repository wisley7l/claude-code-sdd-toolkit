---
description: Sincroniza testes TDD (thoughts/tests/) entre worktree e root, mostrando diffs antes de agir.
argument-hint: <caminho-da-worktree>
allowed-tools: Bash, Read, Glob, AskUserQuestion
---

# Sync Tests — Sincronizador de Testes TDD

Compara e sincroniza `thoughts/tests/` entre um worktree e o repo root, garantindo que testes nao se percam ao mover entre ambientes.

**Premissa**: o worktree e a fonte da verdade — os testes foram escritos/evoluidos la.

## Argumentos

- `$ARGUMENTS` — Caminho da worktree (obrigatorio). Se vazio, listar worktrees disponiveis e perguntar qual usar via AskUserQuestion.

## Fluxo de Execucao

### Passo 1 — Resolver Caminhos

```bash
MAIN_ROOT=$(git worktree list | head -1 | awk '{print $1}')
WORKTREE_DIR="$ARGUMENTS"
```

Validar que ambos os diretorios existem. Se `$WORKTREE_DIR/thoughts/tests/` nao existir ou estiver vazio:

```
Nenhum teste TDD encontrado em <worktree>/thoughts/tests/. Nada a sincronizar.
```

Encerrar.

### Passo 2 — Inventariar Arquivos

Listar todos os arquivos de teste em ambos os lados:

- `WORKTREE_DIR/thoughts/tests/**/*` (apenas arquivos, nao diretorios)
- `MAIN_ROOT/thoughts/tests/**/*` (apenas arquivos, nao diretorios)

Usar caminhos relativos a `thoughts/tests/` para comparacao.

Categorizar cada arquivo:

| Categoria | Condicao |
|-----------|----------|
| **NOVO** | Existe no worktree, nao existe no root |
| **ORFAO** | Existe no root, nao existe no worktree |
| **IGUAL** | Existe em ambos, conteudo identico |
| **MODIFICADO** | Existe em ambos, conteudo diferente |

Para verificar se sao identicos, comparar via `diff -q`:

```bash
diff -q "$WORKTREE_DIR/thoughts/tests/$FILE" "$MAIN_ROOT/thoughts/tests/$FILE"
```

### Passo 3 — Mostrar Resumo

Exibir relatorio antes de qualquer acao:

```
Sync Tests: <worktree> → <root>

NOVOS (worktree → root):
  + path/to/new-test.test.ts

MODIFICADOS (worktree sobrescreve root):
  ~ path/to/changed-test.test.ts

IGUAIS (nenhuma acao):
  = path/to/same-test.test.ts

ORFAOS (so no root, mantidos):
  ? path/to/orphan-test.test.ts
```

Se nao houver NOVOS nem MODIFICADOS:

```
Testes ja estao sincronizados. Nada a fazer.
```

Encerrar.

### Passo 4 — Mostrar Diffs dos Modificados

Para cada arquivo MODIFICADO, mostrar o diff:

```bash
diff -u "$MAIN_ROOT/thoughts/tests/$FILE" "$WORKTREE_DIR/thoughts/tests/$FILE"
```

Rotular claramente:

```
--- root: thoughts/tests/<file>
+++ worktree: thoughts/tests/<file>
```

### Passo 5 — Pedir Confirmacao

```
Aplicar sincronizacao?
- [N] arquivos novos serao copiados para o root
- [M] arquivos modificados serao sobrescritos no root
- [O] arquivos orfaos serao mantidos no root (nenhuma acao)

Confirma? (s/n)
```

Se o usuario negar, encerrar sem fazer nada.

### Passo 6 — Executar Sincronizacao

Para cada arquivo NOVO:

```bash
mkdir -p "$MAIN_ROOT/thoughts/tests/$(dirname $FILE)"
cp "$WORKTREE_DIR/thoughts/tests/$FILE" "$MAIN_ROOT/thoughts/tests/$FILE"
```

Para cada arquivo MODIFICADO:

```bash
cp "$WORKTREE_DIR/thoughts/tests/$FILE" "$MAIN_ROOT/thoughts/tests/$FILE"
```

Arquivos ORFAOS e IGUAIS: nenhuma acao.

### Passo 7 — Confirmar Resultado

```
Sync concluido:
  [N] novos copiados
  [M] modificados atualizados
  [O] orfaos mantidos
  [I] iguais (sem acao)
```

## Tratamento de Erros

- Worktree nao existe → listar disponiveis e perguntar
- `thoughts/tests/` vazio no worktree → encerrar com mensagem clara
- Falha ao copiar → reportar arquivo especifico e parar

## Importante

- **Nunca apagar** arquivos orfaos do root — podem ser de outro worktree
- **Nunca agir** sem mostrar o resumo e pedir confirmacao
- **Sempre mostrar diffs** dos arquivos modificados antes de confirmar
- O worktree e sempre a fonte da verdade para arquivos que existem em ambos os lados
