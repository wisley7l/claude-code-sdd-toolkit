# Reference: review interno do executor (/executor-plan)

> Carregado sob demanda pelo `/executor-plan` na Verificação Final (Etapa 3.5).
> Auto-revisão de **segurança + testes + bugs** sobre o diff staged, antes do
> handoff — pega o problema cedo (contexto fresco) pra que o review do time seja mínimo.
> Independente de quem implementou: subagentes Opus **frescos**, sem o histórico da
> sessão (mesma lógica de independência do `/sdd-review`). Achados estruturados,
> cada must-fix verificado antes de aplicar, loop com guarda de convergência.

## Quando roda

- **Sempre** — modo autônomo e `--step`. Flag `--sem-review` pula esta etapa.
- Roda **uma vez** no fim (Verificação Final), depois do gate de complexidade/simplifier e antes do validador Haiku. Fixes aplicadas aqui entram no staging e são limpas pela passada final do simplifier.

## Escopo do diff

```bash
DIFF_FILES=$(git diff --cached --name-only)
# se vazio (modo --step já commitou por tarefa), use a branch:
#   BASE lida do CLAUDE.md/ARCHITECTURE.md (main/dev/...); git diff <BASE>...HEAD
```

As 3 lentes recebem **os arquivos completos** tocados pelo diff (não só o hunk — contexto insuficiente gera falso-positivo) + `CLAUDE.md`/`ARCHITECTURE.md`.

## Painel — 3 lentes (Opus, em paralelo no mesmo turno)

Emita as 3 chamadas `Agent` numa **única mensagem** (`subagent_type: general-purpose`, `model: opus`) — turnos separados serializam. **Pule a lente cujo escopo não aparece no diff** (ex.: sem arquivo de teste no diff → pule Testes).

**Lente Segurança** (a prioridade):
- Secrets hardcoded; SQL injection, XSS, command injection; path traversal; desserialização insegura
- Autenticação/autorização ausente; vazamento de dado sensível em log/resposta
- **Domínio pagamentos/e-commerce**: verificação de assinatura HMAC de webhook, idempotência de operação que muta pagamento, money handling (nunca float), PCI (não logar cartão/CVV), validação runtime de input não-confiável, race conditions/ordering de webhook

**Lente Bugs & Lógica**:
- Lógica/condições incorretas; acesso a null/undefined sem checagem; off-by-one; race conditions
- Resource leaks (conexão não fechada, cleanup faltando); tratamento de erro ausente; edge cases não tratados; type mismatch
- Dead code introduzido (export/import/função sem referência)
- **Concorrência desperdiçada**: `await` sequencial de operações de I/O independentes que deveriam rodar em paralelo (hoist da promise ou `Promise.all`)
- **Fan-out de query (round-robin/N+1)**: `Promise.all(items.map(i => db.query(i)))` ou loop com query por iteração — deveria ser batch (`WHERE id IN (...)`, join, dataloader). Também: `Promise.all` ilimitado sobre I/O que pode estourar connection pool/rate limit — deveria limitar concorrência

**Lente Testes**:
- Código novo sem teste correspondente; cenários ausentes (input vazio/null/erro/limites)
- Testes que não testam nada (assertion genérica), acoplados a internals, ou com descrição que mente
- Testes frágeis (ordem, estado compartilhado, valor sensível a ambiente); cobertura falsa

## Prompt (base comum — troque só a lente e a lista de checagens)

```
Você é um reviewer independente. Não implementou este código — avalie do zero,
sem assumir que decisões foram tomadas "por boa razão".
Sua lente: [Segurança | Bugs & Lógica | Testes].

Revise SÓ os arquivos abaixo (diff da implementação), contra CLAUDE.md/ARCHITECTURE.md.
Arquivos: <lista + conteúdo completo>

Checagens da sua lente: <bullets da lente acima>

Se sua lente não se aplica ao diff, retorne {"findings":[]} — não force achado.
Retorne SOMENTE JSON, sem narrativa:

{
  "findings": [
    {
      "severidade": "CRITICAL" | "MAJOR" | "MINOR",
      "confidence": 0-100,
      "arquivo": "path:linha",
      "problema": "<1-2 frases>",
      "correcao": "<ajuste concreto>"
    }
  ]
}

Reporte só confidence >= 80. CRITICAL = bug real/falha de segurança/quebra de
contrato; MAJOR = risco concreto; MINOR = melhoria não-bloqueante.
```

## Loop de correção (na main do executor)

1. Junte os findings das 3 lentes. **must-fix = CRITICAL + MAJOR** (confidence ≥ 80). MINOR vai só pro relatório (IMP), sem ação.
2. **Verifique cada must-fix você mesmo** contra o código antes de aplicar — reviewer erra. Descarte os inválidos com motivo (1 linha) pro IMP.
3. Aplique as fixes válidas direto (o executor edita), `git add` das mudanças.
4. **Test count protection + gate**: reexecute o gate após as fixes. Se teste que passava quebrar, ou a contagem cair → **PARADA DURA** (mesma régua do resto do executor). Não "conserte sozinho".
5. Se aplicou fix → **nova rodada de review com subagentes frescos** (só as lentes que tinham must-fix). **Guarda de convergência**: máximo **2 rodadas**, ou pare se uma rodada não reduzir os must-fix válidos.
6. **must-fix aberto ao fim** (não resolvido em 2 rodadas, ou você discorda da fix): **parada dura** — dispare `PushNotification` e leve ao usuário:

```
Review interno: [X] must-fix não resolvidos após [N] rodada(s):
  1. 🔴 CRITICAL — [problema] — arquivo:linha
  2. 🟡 MAJOR — [problema] — arquivo:linha

Opções:
  (a) Corrigir manualmente com sua orientação
  (b) Aceitar como está — anoto no IMP como dívida consciente
  (c) Parar e discutir o design

[a/b/c]
```

## Saída

- **Todas as lentes limpas** (0 must-fix) → siga pro validador Haiku / simplifier final.
- Anote no IMP (seção "Review Interno"): must-fix aplicados, descartados (com motivo), MINOR observados, rodadas.
- Alimente o resumo final: `Review interno: N must-fix aplicados, 0 aberto (S/T/B)`.
