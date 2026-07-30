# Reference: 🧬 Capability viva (spec do sistema)

Contrato do arquivo de **capability** — a especificação **viva** de um domínio de comportamento do produto.
Consumido por `/sdd-spec` (lê na largada + marca o delta) e `/sdd-close` (mescla o delta após merge).

## Capability ≠ SPEC

| | SPEC de mudança | Capability viva |
|---|---|---|
| Path | `thoughts/specs/spec-<TS>-<slug>.md` | `thoughts/capabilities/<dominio>.md` |
| Nome | **tem timestamp** | **sem timestamp** |
| Escopo | uma feature | um domínio de comportamento |
| Ciclo | nasce, entrega, vai pra `closed/` | **nunca move** — só cresce |
| Responde | "o que vamos mudar" | "o que o sistema faz hoje" |

Regra mnemônica: **tem timestamp = morre; não tem = vive.**

N SPECs convergem numa capability. `checkout.md` acumula o cupom (spec-1730), o parcelamento (spec-1745) e o frete grátis (spec-1802) — é o documento que responde *"como o checkout se comporta hoje"* sem reler código.

`thoughts/capabilities/` é **local** (cai sob o `thoughts/` já gitignored). Não commite — não há conflito de merge a tratar.

## Granularidade do domínio

Um domínio = uma área de **comportamento observável** (`checkout`, `auth-sessao`, `notificacoes`), não um módulo de código nem uma feature. Slug em kebab-case, sem timestamp.

- **Preferir encaixar numa capability existente** a criar nova (princípio *atualizar > criar*). Antes de propor domínio novo, liste os existentes.
- **Nunca crie capability nova sem confirmação do usuário** — proliferação de domínios de 1 requisito destrói o valor do documento.
- Se uma SPEC toca 2+ domínios, o delta se divide entre as capabilities correspondentes.

## Formato do arquivo

```markdown
---
dominio: checkout
atualizado: DD-MM-YYYY
specs:
  - spec-1730123456-cupom-frete
  - spec-1745987654-parcelamento
---

# Capability: Checkout

> O que o sistema faz hoje neste domínio. Derivado das SPECs entregues (PR merged).
> Não edite à mão o que o `/sdd-close` mescla — corrija na SPEC e deixe o sync aplicar.

## Comportamento atual

### C1 — Aplicação de cupom
O sistema DEVE aceitar no máximo um cupom por pedido.
- **Quando** o cliente aplica um cupom válido → desconto aplicado sobre o subtotal
- **Quando** o cupom está expirado → erro "cupom expirado", pedido inalterado
- **Quando** já existe cupom no pedido → substitui o anterior
[Origem: spec-1730123456-cupom-frete · PR #142]

### C2 — Cálculo de frete
...
[Origem: spec-1730123456-cupom-frete · PR #142]

## Fora do escopo desta capacidade

- Cupom cumulativo — decidido em spec-1730123456, adiado [PR #142]

## Dívida conhecida

- Sem teste e2e do fluxo de expiração de cupom [spec-1730123456 · roadmap [[014-e2e-cupom-expirado]]]

## Removido

- ~~C3 — Cupom por CPF~~ — removido em spec-1802... [PR #171, DD-MM-YYYY]
```

### Regras do formato

- **`C<N>` sequencial por capability, nunca reusado** (mesma disciplina do `NNN` do roadmap). `C3` removido não volta como `C3`.
- **Todo `C<N>` tem `[Origem: <spec> · PR #N]`** — rastro obrigatório (Zero Inferência). Sem origem identificável, não mescle: pergunte.
- **Comportamento observável, nunca implementação.** Sem nome de função, arquivo ou lib — isso é o mesmo contrato da SPEC. Capability que virou descrição de código perdeu a função.
- **`Quando → então`** nos cenários, herdado do Given/When/Then dos testes de aceitação da SPEC.
- **Seções vazias são omitidas** — capability nova costuma ter só `## Comportamento atual`.
- `specs:` no frontmatter é o rastro cumulativo de quais SPECs contribuíram (para auditoria).

## Delta: como a SPEC declara a mudança

O `/sdd-spec` marca o delta **só quando a SPEC toca capability existente**. Feature em domínio novo é `ADDED` implícito — não precisa de marcação.

Na SPEC, na seção de Requisitos Funcionais, o RF ganha um sufixo de delta:

```markdown
- **RF3** [MODIFIED → checkout C1]: passa a aceitar até 3 cupons cumulativos por pedido
- **RF4** [REMOVED → checkout C3]: cupom por CPF deixa de existir
- **RF5**: (sem marcação) — comportamento novo, será ADDED
```

- `[MODIFIED → <dominio> C<N>]` — altera comportamento já especificado
- `[REMOVED → <dominio> C<N>]` — comportamento deixa de existir
- sem marcação — `ADDED` implícito

## Merge: como o `/sdd-close` aplica

Roda **só sob PR MERGED** — é o único momento em que o comportamento passou a ser verdade.

1. **Resolva a capability** de cada RF marcado. Não existe arquivo do domínio → crie do template (sob confirmação).
2. **Aplique por tipo de delta:**
   - `ADDED` → novo `C<N>` = `max(N existente) + 1`, com `[Origem]` da SPEC + PR
   - `MODIFIED` → **edite** o `C<N>` existente e **acrescente** a nova SPEC ao `[Origem]` (vira `[Origem: spec-A · PR #142 · spec-B · PR #171]`). Não substitua o rastro antigo.
   - `REMOVED` → tire de `## Comportamento atual`, registre em `## Removido` com PR e data. Nunca apague o rastro.
3. **Atualize** `atualizado:` e acrescente a SPEC em `specs:`.
4. **Edição cirúrgica, nunca reescrita do arquivo.** Use `Edit` no `C<N>` alvo — reescrever a capability inteira perde histórico de outros domínios/requisitos.

### Guardrails do merge

- **`C<N>` alvo não existe** (MODIFIED/REMOVED apontando pra requisito inexistente) → **PARE nesse delta** e avise. Provavelmente a SPEC referenciou errado ou outro close já aplicou. Não invente o requisito.
- **Delta já aplicado** (o `[Origem]` já cita esta SPEC + PR) → pule, idempotente. Rodar `/sdd-close` duas vezes não duplica requisito.
- **SPEC sem marcação de delta em domínio existente** → não trate como ADDED silenciosamente. Mostre os `C<N>` do domínio e pergunte se é novo comportamento ou modificação de um existente.
- **Nunca commite** — `thoughts/` é local.
- **Em dúvida, não mescle.** Capability errada é pior que capability incompleta: ela vira fonte de verdade pro `/sdd-spec` do próximo ciclo e propaga o erro.

## Leitura: como o `/sdd-spec` consome

Na largada da pesquisa (antes de ler código), o `/sdd-spec`:

1. Lista `thoughts/capabilities/*.md` — se a pasta não existe, segue sem ela (não é dependência).
2. Abre a(s) do domínio da demanda: é o que o sistema **promete** hoje.
3. Cruza com o `structure-cache`: a capability diz *o que é prometido*, o `sc` diz *o que quebra se mudar*.
4. Detecta sobreposição → marca o delta nos RFs.

Capability é **aceleração, nunca dependência**: ausente ou incompleta, a pesquisa segue pelo código como hoje. Mas quando existe, ela evita redescobrir do zero o comportamento que já foi especificado.
