# Template de Hub

Hub é o **índice de memórias** de um escopo. **Hub do projeto centraliza tudo** sobre o projeto — sabor geral (`feedback`/`project`/`reference`) + sabor SDD (`decisoes`/`licoes`/`preferencias`/`blockers`/`ideias` em `state/`). Discovery único: 1 read no hub → agente sabe o que existe.

## Localização

- **Global**: `$CLAUDE_VAULT_PATH/global/Global.md`
- **Org** (opcional): `$CLAUDE_VAULT_PATH/<org>/<NomeDaOrg>.md`
- **Projeto**: `$CLAUDE_VAULT_PATH/<org>/<projeto>/<NomeDoHub>.md`

## Nome do hub

Capitalize cada segmento kebab:
- `web-app` → `Web-App.md`
- `finance-app` → `Finance-App.md`
- `claude-code-sdd-toolkit` → `Claude-Code-Sdd-Toolkit.md`

**Apelidos**: se já existir hub com nome diferente (ex: pasta `acme/web-storefront/` com hub `legacy-shop.md` em minúsculo, herdado de um repo antigo que foi renomeado), **mantenha o existente**. Descobrir com:

```bash
ls "$CLAUDE_VAULT_PATH/<path>/"*.md 2>/dev/null
```

## Template — hub de projeto (unificado: sabor geral + SDD)

```markdown
# <Nome>

[1-2 linhas descrevendo o projeto. Stack + propósito.]

Fonte autoritativa do código: `<path-do-repo>/` (`CLAUDE.md`, `ARCHITECTURE.md`, `.claude/skills/`). Memórias aqui são complementares — capturam "porquê" e regras de colaboração que não cabem no código.

## Memórias do projeto

### Decisões arquiteturais

- [[slug]] — hook curto de 1 linha

### Lições aprendidas

- [[slug]] — hook curto

### Preferências

- [[slug]] — hook curto

### Blockers conhecidos

- [[slug]] — hook curto

### Ideias adiadas

- [[slug]] — hook curto

### Feedback (regras de colaboração)

- [[slug]] — hook curto

### Project (contexto/decisões)

- [[slug]] — hook curto

### Reference (links externos)

- [[slug]] — hook curto

↑ [[Comecar-aqui]]
```

**Origem das seções**:
- `Decisões` / `Lições` / `Preferências` / `Blockers` / `Ideias` → notas em `<org>/<projeto>/state/<categoria>/` — escritas pelos commands do toolkit SDD (`/sdd-plan`, `/executor-plan`, `/quick-task`, `/sdd-learning`).
- `Feedback` / `Project` / `Reference` → notas em `<org>/<projeto>/<tipo>/` — escritas por este skill `vault-memory` sob pedido explícito.

Apesar das origens diferentes, **todas as entradas vivem no mesmo hub** — é o ponto único de discovery do projeto.

## Template — hub global (só sabor geral)

```markdown
# Global

Memórias que valem em **qualquer projeto** — perfil do usuário, regras transversais, referências.

## Memórias globais

### User (perfil)

- [[slug]] — hook curto

### Feedback (regras de colaboração)

- [[slug]] — hook curto

### Reference (links externos)

- [[slug]] — hook curto

↑ [[Comecar-aqui]]
```

Hub global **não tem** seções de sabor SDD — `state/` só existe em projetos.

## Template — hub de org (opcional, só sabor geral)

Só crie se houver notas no escopo da org (que não cabem em projeto específico nem em global).

```markdown
# <NomeDaOrg>

Memórias que valem na org `<org>` (cross-projeto dentro da org).

## Memórias

### Feedback

- [[slug]] — hook curto

### Project

- [[slug]] — hook curto

### Reference

- [[slug]] — hook curto

↑ [[Comecar-aqui]]
```

## Regras

- **Seção vazia → omita** (não deixe header sem conteúdo).
- **Tipo `user` só aparece em `Global.md`** (escopo global only).
- **Sabor SDD só aparece em hubs de projeto** (não em global, não em org).
- **Hub aponta pra `Comecar-aqui`** no rodapé — único lugar que aponta pra raiz.
- **Notas individuais apontam pro hub** — nunca direto pra `Comecar-aqui`.
- **Atualizar hub é obrigatório** ao criar nota nova (seja qual for o sabor). Sem isso, nota fica órfã.
- **Ordem de seções no hub de projeto**: sabor SDD primeiro (decisões → lições → preferências → blockers → ideias), depois sabor geral (feedback → project → reference). Decisões arquiteturais geralmente são a info mais procurada — ficam no topo.
- **Ordem de seções no hub global**: user → feedback → reference.
