---
name: imp-review
description: Revisa a implementação com lentes independentes — conformidade, bugs, segurança, nomenclatura, queries e testes — e mostra os achados pra você decidir. Depois que o time comenta, valida se cada pedido foi de fato atendido. Corrige o pequeno e devolve ao implement o que mexe em comportamento.
disable-model-invocation: true
argument-hint: [número do PR | branch | vazio = o que está em curso]
allowed-tools: Read Edit Write Grep Glob Agent Skill AskUserQuestion Bash(git status*) Bash(git diff*) Bash(git log*) Bash(git show*) Bash(git branch*) Bash(git add*) Bash(git worktree list*) Bash(gh *) Bash(npm *) Bash(npx *) Bash(pnpm *) Bash(bun *) Bash(bunx *) Bash(node *) Bash(go *) Bash(lizard *) Bash(ls *) Bash(structure-cache *) Bash(structure-cache)
---

# imp-review

Olha o código com olhos que quem implementou não tem — inclusive quando quem implementou foi você,
minutos atrás. Roda em dois momentos, e detecta qual pelo estado do PR:

- **Sem review humano ainda** → revisa a implementação inteira e traz o que achou.
- **O time já comentou** → valida se cada ponto levantado foi de fato atendido.

Os achados vão **pra tela, pra você decidir**. Nenhuma nota, nenhum "aprovado", nenhum relatório
que substitua sua leitura.

## Antes de gastar análise

Resolva o root (`git worktree list | head -1`) e delimite o escopo:

- **PR** informado ou detectado pela branch (`gh pr list --head <branch> --state open`) → `gh pr diff`.
  Detecte sempre: revisar o diff local quando existe PR aberto ignora o que já foi discutido lá.
- **Branch** → `git diff <base>...HEAD`, com a base lida do `CLAUDE.md`/`ARCHITECTURE.md`.
- **Nada commitado ainda** (chamado pelo `implement`) → `git diff HEAD`, staged e não-staged.

**Diff vazio, nada a revisar** — diga e pare.

**Build ou lint quebrado é parada.** Se o `CLAUDE.md` declara os comandos, rode antes: review sobre
build quebrado gera ruído que enterra o achado real. Se o projeto não declara comando nenhum, siga e
registre que não houve verificação prévia — não invente o comando.

Leia `CLAUDE.md`, `ARCHITECTURE.md` e os **arquivos completos** que o diff toca. Diff sozinho não
mostra o contexto que decide se algo é bug.

## O que o time já disse

Havendo PR aberto, colete antes de analisar:

```bash
gh pr view <N> --json reviews,reviewDecision,comments,body
gh api repos/{owner}/{repo}/pulls/<N>/comments
```

Agrupe as threads (`in_reply_to_id`), ignore autores `[bot]`, e trate isso como **contexto, não
verdade absoluta**: você pode discordar de um revisor humano se tiver evidência concreta — apresente
as duas leituras e deixe a decisão com o usuário.

**Não duplique o que um humano já apontou.** Repetir o achado dele infla o resultado e afoga o que
só você viu. Registre como já apontado, e diga se confirma, refuta ou complementa.

## As lentes

Lance **numa única resposta** (turnos separados serializam) — `subagent_type: general-purpose`,
`model: opus` para as que exigem julgamento (bugs, segurança, queries, testes) e `sonnet` para as de
padrão (conformidade, nomenclatura):

> Leia `${CLAUDE_SKILL_DIR}/lenses.md` e assuma a lente **<nome>**. Diff e arquivos completos:
> `<conteúdo>`. Constitution: `<CLAUDE.md e ARCHITECTURE.md>`. Você é read-only e não aprova nada.

**Pule a lente cujo escopo não aparece no diff** — sem query, sem lente de queries; sem arquivo de
teste, sem lente de testes. Lente sem matéria-prima inventa achado.

**Complexidade é medida, não julgada** — roda direto aqui, sem subagente: a regra do linter do
projeto, ou `lizard -C <limite>`, sobre os arquivos do diff, considerando só funções que o diff
tocou. Sem ferramenta disponível, diga que não mediu. Complexidade nunca é bloqueante: é risco de
manutenção, não defeito.

## O que vira achado

Reporte com **confiança ≥ 80** — abaixo disso é palpite, e palpite enterra o achado bom.

| Grau | O que é |
|---|---|
| **Bloqueia** | bug real, falha de segurança, quebra de contrato |
| **Atenção** | risco concreto que merece decisão antes do merge |
| **Menor** | nomenclatura, style, complexidade, melhoria que não bloqueia nada |

**Fora de escopo, sempre:** problema pré-existente que a mudança não introduziu; o que o linter já
pega sozinho; preocupação hipotética sem evidência no código. Nomenclatura e style **nunca** sobem
de grau — "talvez ficasse melhor" não é evidência.

Toda sugestão cita a base: `arquivo:linha` do padrão que o projeto já usa, o trecho do `CLAUDE.md`
que a exige, ou a documentação oficial da linguagem. Sugestão que só se apoia em "boa prática" não
entra.

## Mostrar

Achados por gravidade, na tela, cada um em duas linhas: o quê, onde, e a pergunta ou o ajuste que
resolve. **Inclusive os que você discorda** — com sua discordância anotada do lado, não filtrados.

Junto, o que importa tanto quanto: **onde você olhou e o que ficou de fora** — quais lentes rodaram,
quais foram puladas e por quê, se a complexidade foi medida. Sem isso o usuário não sabe o tamanho
do silêncio.

Não existe veredito aqui. "Aprovado" é palavra do `pr-ready`, e mesmo lá quem aprova é o usuário.

## Corrigir

Para cada achado que o usuário decidir endereçar, o caminho depende do que ele mexe:

- **Não muda comportamento** (nome, typo, extração local, guarda faltando num caminho já testado) →
  corrija direto: edite, rode o gate, `git add`. **Contagem de testes caiu, pare** — a régua vale
  aqui igual.
- **Muda comportamento** → vira **tarefa no `tasks.md`**, num bloco `## Correções do review`, com o
  requisito que ela toca e a verificação esperada. Quem executa é o `implement`, no ciclo normal:
  teste primeiro, red verificado, green.

Essa fronteira é o ponto todo. Correção que altera o que o sistema faz e entra por fora do ciclo é
comportamento sem teste — exatamente o que o resto do workflow existe pra impedir.

**Se a correção crescer** (decisão arquitetural, biblioteca nova, redesenho), pare: isso é mudança
de plano, não conserto. Leve ao usuário.

## Quando o time já comentou

Aqui o trabalho é outro: **o comentário humano é o contrato**. Mudar algo por perto não conta.

Para cada thread, em ordem de não atendidos primeiro:

```
@fulano em src/foo.ts:42
  Pediu:     <o ponto, 1 a 2 linhas>
  No código: <arquivo:linha — o que a correção fez>
  Leitura:   atendido | parcial — <o que falta> | não endereçado | divergente — <mudou outra coisa>
```

Em caso de dúvida sobre se a correção atende, delegue **aquele ponto** a um subagente Opus escopado
no comentário e nos arquivos dele — não o diff inteiro.

**Parcial, não endereçado e divergente são pendências**, e seguem o mesmo caminho da seção acima:
pequeno se corrige aqui, comportamento vai pro `tasks.md`.

Ao fim, ofereça **rascunhos de resposta para cada thread** — o que foi feito, `arquivo:linha`, hash
se já houver commit — prontos para você colar. **Você nunca posta no PR.** Ler via `gh` é livre;
escrever é do usuário.

## Registrar

No `notes.md` da pasta da mudança, não num relatório à parte: os achados que viraram correção, os
que o usuário decidiu deixar como dívida (com o motivo), e o que ficou fora do alcance das lentes.

## Sempre

- **Nunca comente no PR.**
- **Nunca infle.** Zero achado é resultado legítimo — diga isso e diga onde olhou.
- **Nunca aprove.** Não é sua palavra.
