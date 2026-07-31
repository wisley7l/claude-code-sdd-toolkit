# Créditos — skill `memory`

> Não carregado no contexto do agente: fica ao lado do `SKILL.md` e não é referenciado por ele.
> Ver `NOTICE.md` na raiz para o protocolo.

## Origem

**Construção própria**, sobre o auto-memory nativo do Claude Code. Substitui `memory-keeper.v9`
(285L) e `memory-organize.v9` (488L) — 773 linhas viram 150 + um script de auditoria.

O `/executor-plan` v9 declarava "memória persistente via memory-keeper" entre os conceitos adaptados
do **tlc-spec-driven** (CC-BY-4.0), mas o que veio de lá era a *ideia* de persistir aprendizado, não
o formato: o auto-memory é da plataforma, e os tipos, o índice e a régua do gancho são nossos.

## ⚠️ Contrato de dados preservado (Parte E.4)

| Invariante | Status |
|---|---|
| `MEMORY.md` é **apenas índice** | mantido — as três camadas são todas de ponteiro |
| Flat, sem subpastas | **mantido, e agora com razão medida** (ver abaixo) |
| Nome `<tipo>_<slug>.md`, `name:` interno em kebab | mantido |
| `metadata.node_type` e `originSessionId` são do harness | mantidos — a skill não os toca |
| Conteúdo = princípio + gatilho (`Why:` / `How to apply:`) | mantido e endurecido: virou critério de existência |
| Sub-sumário quando um tipo passa de ~10 notas | mantido, com exigência nova de ser mapa de gatilhos |
| Memória centralizada no root, symlink nas worktrees | mantido (é o que a doc chama de "shared across worktrees") |

**Nada foi apagado.** Decisão explícita do usuário: *"não precisa apagar agora não"*. Os tipos
aposentados saem da oferta, não do disco.

## O que mudou, e por quê

### Os tipos: 9 → 8, medindo o uso real

Levantamento no gopay (236 notas): `feedback` 97 · `lesson` 85 · `decision` 25 · `project` 21 ·
`blocker` 4 · `reference` 2 · `preference` 1 · `idea` **0**.

- **`idea` aposentado** — zero notas em meses de uso. Não pagava a própria existência.
- **`preference` aposentado** — 1 nota, e ela é `decision` disfarçada: descreve padrão técnico do
  projeto com trade-off documentado (fire-early promises), não regra de colaboração.
- **`blocker` → `bug`** — as 4 notas existentes são exatamente sintoma + workaround. Mesma coisa
  com nome pior: "blocker" descreve o efeito em você; "bug" descreve o que se procura.
- **`win` criado** — pedido do usuário: *"coisa que acertamos e podemos reforçar"*. Não existia
  equivalente no v9, e é o único tipo cujo conteúdo ninguém escreve espontaneamente.

### O gancho virou critério de existência

O achado que motivou tudo. Medição da alcançabilidade no gopay:

```
volume escrito:       460 KB        notas linkadas no índice:    42  (17%)
volume que carrega:    10 KB        só via sub-sumário:         192  (81%)
                                    órfãs:                        2
```

81% das notas dependem de duas leituras encadeadas que só acontecem se algo der o motivo. Não é
problema de organização — é de **como a nota foi escrita**: registro do passado em vez de gatilho
pro futuro. Daí a régua: sem gancho que diga *quando* importa, não vira nota.

### Pastas: recusadas com dado, não com preferência

O usuário levantou (*"vamos precisar separar por pastas talvez"*). A resposta é não, e a razão é
medida: **só o `MEMORY.md` carrega** (200 linhas / 25KB, por doc). Mover 236 arquivos não muda os
10KB que entram na sessão. Pasta melhora navegação humana e não melhora recuperação — que era o
problema real (*"pra quando houver algo parecido ele consiga buscar na memória"*).

O investimento foi pro índice, que é o único nível que age. Some-se: subpasta não é documentada pela
plataforma, e complicaria o symlink entre worktrees do E.4.

### O que a plataforma passou a fazer sozinha

Boa parte das 488 linhas do `memory-organize` v9 existia pra manter o índice saudável. Hoje
(v2.1.210+) o harness mede o `MEMORY.md` depois de cada escrita, avisa quando está perto do limite e
**dá erro** quando passou. E desde v2.1.211 frontmatter e comentários HTML são removidos antes de
medir — o script replica exatamente isso pra não reportar limite diferente do real.

Também saiu: o modo `relink` (symlink de worktree é da skill `worktree`) e o `rename` (mover nota
entre tipos é decisão caso a caso, não operação em lote).

## ⭐ O achado que não estava no plano

Rodar a auditoria no dado real do usuário revelou **fragmentação entre configs** — o mesmo projeto
com memória em quatro diretórios:

```
.claude        236 notas    (última escrita 30-07)
.claude-m2      19 notas    (06-04)
.claude-code7    1 nota     (12-02)  ← config ATIVA, e sem MEMORY.md
.claude-old      0 notas
```

Com `CLAUDE_CONFIG_DIR=~/.claude-code7`, o gopay carrega **zero** memória — não há índice nesse
diretório. Isso responde à desconfiança que abriu o assunto (*"acho q o trabalho de memoria que
fizemos pode não ter ajudado tanto quanto eu achei"*): em parte das sessões, a memória construída
simplesmente não estava sendo lida.

Por isso a fragmentação é a **primeira** coisa que a auditoria reporta, antes de qualquer métrica de
qualidade: nada mais importa se a sessão lê o diretório errado. E por isso a skill **não consolida
sozinha** — mover dado entre configs do usuário exige o de-para na tela e o OK dele.

## Decisões do usuário (31-07-2026)

- **⭐ Flat + índice em três camadas**, depois de ver os números. *"pode seguir com esse desenho"*.
- **`idea` e `preference` aposentados** — *"acho até que pode apagar pq tem preferencia so é muito
  pouco"* — e logo em seguida, sobre o dado existente: *"não precisa apagar agora não"*. O tipo sai
  da oferta; a nota fica.
- **Pendência declarada:** consolidar as configs fragmentadas do gopay. A auditoria mostra; a
  operação espera decisão.
