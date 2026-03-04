---
description: Remove branches locais cujas remotas já foram deletadas (merged/closed).
allowed-tools: Bash, AskUserQuestion
---

# Git Prune Local Branches

Remove branches locais que não possuem mais correspondente remota (já foram merged e deletadas no GitHub).

## Fluxo de Execução

### Passo 1 — Atualizar Referências Remotas

```bash
git fetch --prune origin
```

### Passo 2 — Listar Branches Órfãs

Identificar branches locais cujo tracking remoto foi removido:

```bash
git branch -vv | grep ': gone]' | awk '{print $1}'
```

Se não houver nenhuma, informar ao usuário e encerrar.

### Passo 3 — Mostrar ao Usuário

Listar as branches que serão removidas e pedir confirmação antes de prosseguir.

### Passo 4 — Remover Branches

Para cada branch listada:

```bash
git branch -d <branch>
```

Se `-d` falhar (branch não fully merged), avisar o usuário sobre qual branch falhou e perguntar se quer forçar com `-D`.

### Passo 5 — Reportar

Informar:
- Quantas branches foram removidas
- Se alguma falhou e por quê
- Branches locais restantes: `git branch`

## Importante

- **Nunca** deletar `main`, `master`, `staging`, `prod` ou `dev`
- **Nunca** deletar a branch atual (checked out)
- **Nunca** usar `-D` sem consentimento explícito
- Sempre mostrar a lista e pedir confirmação antes de deletar
