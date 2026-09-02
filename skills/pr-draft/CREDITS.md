# Créditos — skill `pr-draft`

> Não carregado no contexto do agente: fica ao lado do `SKILL.md` e não é referenciado por ele.
> Ver `NOTICE.md` na raiz para o protocolo.

## Origem

Construção própria, do `pr-draft.v9.md` (310 linhas, **sem atribuição de terceiros**). Cobre os dois
modos do original: kickoff e `sync`.

## Kickoff e sync na mesma peça — como no v9

Cheguei a separar o `sync` numa skill própria e **voltei atrás a pedido do usuário** (31-07-2026):
*"não dava pro pr-draft ter um sync para ficar tudo em um só ou é ruim?"*

Ele estava certo, e o argumento que eu tinha usado era fraco. Eu aleguei custo de contexto — mas as
duas são `disable-model-invocation: true`, então **só entram no contexto quando invocadas**; a
diferença real era ~80 linhas numa invocação. O custo que user-invoked paga de verdade é
**cognitive load**: lembrar que a peça existe. `pr-draft sync` já está na memória muscular dele; uma
nona peça seria mais uma pra esquecer.

E era inconsistente: eu tinha acabado de unificar `worktree` (criar + remover) argumentando "mesmo
recurso, conhecimento compartilhado" — e o corpo do PR é exatamente isso, com a regra "não vaze
artefato interno" valendo idêntica nos dois modos.

## O modo sync

Preservado do v9 (linhas 194–256 do `pr-draft.v9.md`):

- **⭐ Funciona de sessão limpa** — re-hidrata dos artefatos e do diff, nada depende do histórico.
  No v9 já era o uso recomendado (pós-`/clear`). Aqui o motivo está escrito: sessão longa carrega a
  narrativa da implementação, e narrativa mente por omissão.
- **⭐ Desvio do plano nunca é omitido** — o que quem revisa mais precisa saber, e o que mais some
  por parecer feio.
- **"Comece o review por"** com arquivo real do diff e o motivo.
- **Lê o diff completo**, não só os nomes; abre o código quando o diff não se explica. Subagente
  `Explore` para diff grande.
- **`gh pr edit` só com confirmação**; título só muda se pedido; nunca sai do draft.

**Ganho de graça no v10:** o v9 garimpava o `IMP-DD-MM-YYYY-slug.md` em `thoughts/history/` pra
achar desvios e contagem. A I.12 pôs tudo na pasta da mudança, e o `notes.md` do `implement` já traz
em tabela a evidência de red por tarefa, a contagem, os desvios e a dívida.

A seção **Verificação** ficou mais honesta que o "Test plan" do v9: o `## Testes` do `plan.md`
registra o que foi cortado e o que ficou como **verificação manual aprovada pelo usuário** (E.5,
endurecido em 31-07-2026). Isso entra no corpo em vez de sumir — no v9 um requisito com
`Tests: none` justificado desaparecia, e quem revisava não tinha como saber que aquele
comportamento não tinha rede.

## Preservado do v9

- **Draft sempre** — sair do draft é clique humano.
- **Commit vazio como andaime** — o PR precisa de um ponto de partida; código só na worktree.
- **Working tree sujo é parada dura** — mudanças não commitadas viajariam no checkout.
- **Root volta pra branch default** — o repositório principal nunca fica preso na feature.
- **⭐ Corpo é público** — nada de caminhos de `thoughts/`, link ou id de sessão do Claude, número de
  roadmap. Foi guardrail duramente aprendido no v9 e está repetido lá e aqui de propósito.
- **Fallback manual** quando `push` ou `gh pr create` são negados: comandos exatos com valores
  reais, um por vez, esperando confirmação. Nunca contornar permissão negada.
- **Sem force-push, sem reescrever histórico, sem deletar branch.**

## O que saiu

- **Promoção do item de roadmap** (`backlog/` → `em-progresso/`, ~15 linhas do Passo 5.5) — toca
  dado vivo, é Onda 2 (`REFACTOR-v10.md`, Parte E.1). Volta quando o `roadmap` for reconstruído.
- **Detecção de artefatos por glob em três diretórios** (`thoughts/specs/`, `thoughts/plans/`) —
  desnecessária: a I.12 pôs tudo numa pasta só por mudança.

## Ganho de graça no v10

O `tasks.md` agrupa tarefas **por bloco de PR** (I.13). Quando o plano prevê mais de um PR, esta
peça sabe qual bloco este PR fecha — no v9 isso dependia de casar o slug da branch com o item de
roadmap certo, com desempate por pergunta. Agora é leitura direta do artefato.

## Os modos `stack` e `restack` (19-08-2026)

Construção própria. A única dependência externa é a extensão oficial **`gh stack`**
(`github/gh-stack`, stacked PRs do GitHub em public preview desde 30-07-2026), **chamada como CLI —
nada de código dela foi copiado ou adaptado**, então não há obrigação de atribuição a cumprir aqui.
Registrado só porque é dependência opcional: sem a extensão, o modo `stack` degrada pro kickoff
um-a-um em vez de improvisar a cadeia com `--base`.

O desenho dos dois modos saiu de fatos medidos contra a extensão instalada, não da documentação —
ver **I.40** no `REFACTOR-v10.md`, que registra os quatro achados e o que cada um forçou.
