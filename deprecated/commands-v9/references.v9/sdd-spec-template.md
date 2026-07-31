# Reference: template da SPEC de comportamento (/sdd-spec)

> Carregado sob demanda pelo `/sdd-spec` no momento de escrever o doc (Passo 7).
> Caminho do output: `thoughts/specs/spec-<unix_timestamp>-<slug>.md`
> A SPEC descreve **COMPORTAMENTO** (o QUÊ). Nada de código, plano ou tarefas — isso é do `/sdd-plan`.

```markdown
---
date: DD-MM-YYYY (UTC-3)
request: [a solicitação original, 1 frase]
status: draft | aprovada
related: [issue/PR/links se aplicável]
---

# SPEC: [Título — o comportamento, não a implementação]

## Resumo

> 2-3 linhas: que comportamento o sistema passa a ter e para quem. Escreva por último.

---

## 1. Histórico do Usuário & Partes Interessadas

- **Quem usa**: [papéis/atores que interagem com o recurso]
- **Quem mantém**: [quem dá suporte/opera]
- **Quem é impactado**: [afetados indiretos]

**Histórias de usuário**:
- Como [papel], eu quero [objetivo], para que [benefício].
- [uma ou mais — cubra os atores relevantes]

---

## 2. Critérios de Sucesso

> Mensuráveis e observáveis. Sem "melhorado", "melhor", "mais rápido" sem número.

- [ ] **Funcional**: [o recurso faz X — verificável]
- [ ] **Operacional**: [funciona bem — ex.: responde em <Nms p95; sem erro sob carga Y]

---

## 3. Requisitos Funcionais

> O que o sistema **DEVE** fazer. Entradas → saídas → transformações. Específico o bastante pra implementar sem perguntar.

- **RF1**: [comportamento — caminho feliz]
  - Entrada: [...] · Saída: [...] · Regra: [...]
- **RF2**: [caso de borda]
- **RF3**: [condição de erro — o que o sistema faz quando algo falha]

[Numere os RFs — os Testes de Aceitação e as tarefas do /sdd-plan vão referenciá-los.]

---

## 4. Requisitos Não Funcionais

> Inclua **apenas** o que for genuinamente relevante. Não preencha com boilerplate.

- **Desempenho**: [latência/throughput/uso de recurso, se importa]
- **Confiabilidade & erros**: [como degrada, retries, idempotência]
- **Segurança**: [authz, dados sensíveis, superfície de ataque]
- **Escala & concorrência**: [limites, corridas, volume esperado]

---

## 5. Restrições & Fora de Escopo

> **Regra dura**: o que NÃO está listado aqui está NO escopo e DEVE ser coberto pelos RFs e Testes de Aceitação.

- **Fora de escopo**: [explicitamente não incluído nesta spec]
- **Limites que não devem ser ultrapassados**: [...]
- **Decisões adiadas (intencional)**: [cada uma, explícita]
- **Parece relacionado, mas está excluído**: [...]

---

## 6. Contexto Técnico & Pontos de Integração

> Onde o recurso encosta no sistema atual. Toda afirmação técnica com `[Fonte: path:line]` ou `[Fonte: url]`. Sem fonte = `[NEEDS VERIFICATION]`.

- **Módulos/arquivos que interage**: [`path:line` — papel]
- **APIs / estruturas de dados / protocolos**: [...]
- **Dependências externas (serviços/libs)**: [com `[Fonte: url]`]

---

## 7. Testes de Aceitação

> Cenários concretos e executáveis (Given/When/Then). Descrevem **o que verificar**, NÃO como implementar. Cada um mapeia a ≥1 RF.

### AT1 — [nome do cenário] (cobre RF1)
- **Given** [estado inicial]
- **When** [ação]
- **Then** [resultado observável]

### AT2 — [caso de borda] (cobre RF2)
- **Given** ... **When** ... **Then** ...

### AT3 — [caminho de erro] (cobre RF3)
- **Given** ... **When** ... **Then** ...

[Cubra: caminho feliz, casos de borda, caminhos de erro, condições de limite.]

---

## 8. Mapa RF → Teste de Aceitação

| RF | Coberto por | Critério de sucesso relacionado |
|---|---|---|
| RF1 | AT1 | [...] |
| RF2 | AT2 | [...] |
| RF3 | AT3 | [...] |

[Todo RF tem ≥1 AT. Lacuna aqui = spec incompleta.]
```
