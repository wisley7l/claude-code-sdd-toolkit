---
description: Verificação comportamental pós-implementação — roda a aplicação e exercita os fluxos tocados, captura evidência real e anexa ao IMP. Nunca aponta pra produção.
model: claude-sonnet-4-6
allowed-tools: Read, Write, Edit, Glob, Grep, Agent, Skill, AskUserQuestion, Bash(npm *), Bash(npx *), Bash(bun *), Bash(bunx *), Bash(pnpm *), Bash(node *), Bash(go *), Bash(docker *), Bash(docker compose *), Bash(curl *), Bash(lsof *), Bash(ps *), Bash(kill *), Bash(git status*), Bash(git diff*), Bash(git log*), Bash(git worktree list*), Bash(gh *), Bash(ls *), Bash(mkdir *)
---

# Verifica — a feature funciona de verdade?

Testes verdes provam que o código faz o que os testes pedem — não que a **feature funciona no app real**. Você sobe a aplicação, exercita os fluxos que a mudança tocou, observa o comportamento e registra **evidência**. É o QA de 5 minutos entre o `/executor-plan` e o review/PR ready.

**O que você NÃO é**: substituto de testes (eles continuam obrigatórios) nem teste de carga/e2e formal. Você é a checagem "liga e vê funcionando" que humano faria antes de pedir review.

## Princípios

- **Evidência > suposição**: "verificado" exige output real capturado (resposta HTTP, log, registro criado, tela). Sem evidência = não verificado
- **Nunca produção**: só ambiente local/dev/sandbox. Gateways de pagamento SEMPRE em test mode (chaves de teste, eventos de teste)
- **Side effects sob confirmação**: qualquer ação que escapa da máquina (e-mail real, webhook pra terceiro, cobrança, mensagem) só roda com OK explícito — prefira mocks/sandbox
- **Zero Inferência no boot**: como rodar o app vem do `CLAUDE.md`, skills do projeto, scripts declarados (`package.json`, `Makefile`, `docker-compose.yml`) — nunca chute comando
- **Sempre derrube o que subiu**: processo iniciado pra verificação é encerrado ao final, sucesso ou falha

## Fluxo

### 1. Escopo — o que verificar

Derive os fluxos comportamentais tocados:
- Do **IMP** mais recente (`thoughts/history/`) e/ou do **SPEC**: o que foi implementado, quais endpoints/fluxos/telas mudaram
- Sem IMP/SPEC: pergunte ao usuário o que verificar (1 frase por fluxo)

Liste 2-6 checagens concretas, cada uma com: ação → comportamento esperado. Ex: `POST /checkout com cupom válido → 200 + desconto aplicado no total`.

### 2. Descobrir como rodar

Na ordem: `CLAUDE.md` (seção de comandos/run) → skills do projeto (`.claude/skills/` com nome tipo `run`, `dev`, `local`) → `package.json` scripts / `Makefile` / `docker-compose.yml` / `Procfile`. Identifique também: porta, env necessária (`.env.example`), dependências de serviço (DB, fila).

Se não encontrar forma declarada de rodar: **pergunte** ("Como rodo o app localmente?"). Não invente.

### 3. Plano de verificação (confirmação)

```
Plano de verificação:

Boot: [comando] (porta [N], env: [ok | faltam: X])
Checagens:
  1. [ação] → espero [comportamento]
  2. ...
Side effects externos: [nenhum | lista — CONFIRMAR antes]

Executo? [s/n/ajustar]
```

Se houver side effect externo na lista, destaque e só siga com OK explícito por item.

### 4. Executar

1. Suba o app **em background** (capture o log de boot). Boot falhou → reporte o erro e pare; consertar boot pode ser `/quick-task`.
2. Execute cada checagem: `curl`/CLI/script/evento de teste do gateway. Capture o output real (status + corpo relevante, linhas de log, registro consultado).
3. Compare com o esperado. Divergência = checagem FALHOU (sem "quase passou").
4. **Encerre o processo** que você subiu (e containers que você criou).

Pra fluxo com UI, se não houver como automatizar: descreva o passo manual pro usuário executar e aguarde o relato — registre como `verificado manualmente pelo usuário`.

### 5. Registrar evidência

Anexe ao IMP da feature (ou crie `thoughts/history/VER-DD-MM-YYYY-[slug].md` se não houver IMP):

```markdown
## Verificação Comportamental

Data: DD-MM-YYYY · App: [comando de boot] · Ambiente: [local/dev/sandbox]

| Checagem | Esperado | Observado | Evidência | Status |
|---|---|---|---|---|
| POST /checkout c/ cupom | 200 + desconto | 200, total 90.00 | [trecho do response] | ✅ |
| [...] | | | | ❌ |
```

### 6. Resultado

- **Tudo ✅**: informe e sugira o próximo passo (`/sdd-review` ou marcar PR ready).
- **Alguma ❌**: mostre a evidência da falha e ofereça: (a) `/quick-task` pro fix, (b) investigar com `/investiga` se a causa não for óbvia, (c) parar aqui. A checagem que falhou re-roda após o fix.

## Guardrails

- **Produção é proibida**: URL/env de produção detectada no alvo = pare e avise. Sem exceção
- **Pagamentos sempre em test mode**: chave live detectada no env usado = pare e avise antes de qualquer chamada
- **Side effect externo só com OK por item**: e-mail, webhook real, cobrança, mensagem
- **Evidência obrigatória**: checagem sem output capturado não vira ✅
- **Derrube o que subiu**: nunca deixe processo/container órfão
- **Não conserta aqui**: falha vira handoff (`/quick-task` / `/investiga`) — este command só verifica
- **Nunca commita/pusha**
