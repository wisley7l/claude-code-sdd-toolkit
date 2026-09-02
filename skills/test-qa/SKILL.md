---
name: test-qa
description: QA de verdade sobre a aplicação rodando — sobe o ambiente, executa a verificação que ficou pendente e explora o que foi tocado atrás de bug, inconsistência, erro de escrita e comportamento inesperado. Achados com reprodução na tela; nunca conserta, nunca aponta pra produção.
disable-model-invocation: true
argument-hint: <rota, tela ou fluxo a testar — ou nada pra usar a mudança mais recente>
allowed-tools: Read Edit Write Grep Glob Agent AskUserQuestion Bash(git status*) Bash(git diff*) Bash(git log*) Bash(git worktree list*) Bash(npm *) Bash(npx *) Bash(pnpm *) Bash(bun *) Bash(bunx *) Bash(node *) Bash(go *) Bash(make *) Bash(docker *) Bash(curl *) Bash(lsof *) Bash(ps *) Bash(kill *) Bash(ls *) Bash(cat *) Bash(mkdir *) Bash(gh pr view*)
---

# test-qa

Testes verdes provam que o código faz o que os testes pedem. Não provam que a **feature funciona**.
Você sobe a aplicação, exercita o que a mudança tocou e **procura defeito** — não confirma que está
bom. Achado sem reprodução não é achado; ausência de achado é resultado legítimo e você diz onde
olhou.

Você **não conserta nada** e **não commita nada**. Ao final o usuário decide o que fazer com o que
apareceu.

## Dois momentos, detectados pelo estado

**Existe mudança em `thoughts/changes/<NNN>-<slug>/`** (a mais recente, ou a que o argumento indicar):
leia `spec.md`, `plan.md` e `tasks.md`. Duas coisas saem daí, nesta ordem:

1. **A verificação que ficou pendente.** Todo requisito sai do planejamento com uma forma de
   verificação, e o piso é verificação manual com evidência registrada — que é **dívida, não pronto**.
   Os requisitos marcados assim são sua primeira lista, e executá-los aqui é o que fecha essa dívida.
2. **A exploração**, sobre as rotas, telas e fluxos que o diff tocou (`git diff --stat` contra a base).

**Não existe mudança, ou o argumento aponta um alvo direto** (`/tk7:test-qa POST /checkout`): você
só explora, e o alvo é o que ele disse. Sem spec como contrato, tudo que você achar estranho e que
ninguém especificou vira **pergunta**, não bug — ver graus, abaixo.

`root` é o repositório principal (`git worktree list | head -1`), sempre. Você quase certamente roda
dentro de uma worktree, onde `thoughts/` local está vazio porque é gitignored — vale para toda
leitura e escrita.

## Como se sobe isto, sem chutar

Na ordem, parando no primeiro que responder: `CLAUDE.md` do projeto (seção de comandos) → skill do
projeto que já cubra rodar o app (`.claude/skills/` com nome tipo `run`, `dev`, `local`) → memória do
projeto → `package.json` / `Makefile` / `docker-compose.yml` / `Procfile` / `.env.example`.

Você precisa sair daí com: **comando de boot, porta, env necessária e serviços de apoio** (banco,
fila, front *e* back quando o alvo é tela). Se qualquer um desses ficar em aberto, **pergunte** — uma
pergunta objetiva, não um questionário. Comando de boot chutado quebra o ambiente do usuário ou, pior,
sobe apontando pro lugar errado.

**Quando ele responder, ofereça gravar.** Uma nota de memória do tipo `project`, com o gancho *"quando
precisar subir o app deste projeto"*, contendo comando, porta, env e serviços. Sem isso você pergunta
a mesma coisa toda vez, e é exatamente o tipo de conhecimento que não está em lugar nenhum do repo.

## O ambiente é seu enquanto durar

Quem sobe é você, aqui — não um subagente. Subagente termina quando devolve o resultado, e o processo
que ele deixou de pé fica sem dono pra derrubar.

Antes de subir, cheque o marcador do ambiente compartilhado, que vive no repositório principal porque
é o único lugar visível entre worktrees:

```
<root>/thoughts/.env-em-uso     # branch · tarefa · hora em que foi adquirido
```

- **Livre** — registre o uso, suba o ambiente em background capturando o log de boot, e **apague o
  marcador ao terminar**, com sucesso ou sem.
- **Ocupado** — pergunte, dizendo **quem** usa e **desde quando**. Pode ser um `implement` rodando
  em outra worktree. Não derrube o que não é seu.

**Boot falhou é parada**, com o log na tela: consertar boot não é QA.

**Derrube o que subiu.** Todo processo e todo container que você criou morre no fim, inclusive quando
a exploração parou no meio. O que já estava de pé antes de você continua de pé.

## O que não se faz aqui

- **Produção nunca.** URL, env ou credencial de produção no alvo: pare e avise. Sem exceção, sem
  "só uma leitura".
- **Pagamento sempre em test mode.** Chave live no ambiente que você vai usar: pare antes de qualquer
  chamada.
- **Side effect que escapa da máquina** — e-mail real, webhook pra terceiro, cobrança, mensagem —
  só com OK **item a item**, e prefira sandbox ou mock.
- **Dado que você cria é lixo que fica.** Marque tudo que criar com um prefixo reconhecível
  (`qa-<data>-…`), liste o que ficou no fim, e ofereça limpar. Exploração de rota é fuzzing: em banco
  compartilhado ela suja o ambiente de todo mundo.
- **Nada de reparo.** Encontrou, registrou, seguiu. Consertar no meio contamina o resto da rodada.

## O plano de ataque, sob confirmação

Antes de tocar em qualquer coisa, uma tela só:

```
Alvo: <rotas / telas / fluxos>
Boot: <comando> (porta N · env: ok | faltam X) · derrubo ao final
Verificação pendente do plano: <N itens, ou nenhum>
Lentes: <as que se aplicam>  ·  Paralelo: <quais>  ·  Sequencial: <quais e por quê>
Dado que vou criar: <o que, com que prefixo>
Side effects externos: <nenhum | lista — OK por item>

Sigo?
```

## Delegar a exploração

Você orquestra; as lentes são subagentes. Cada uma cobre uma perspectiva e ignora o resto — é o que
faz a varredura ser sistemática em vez de sorte.

O recurso decide o que paralelize:

| Lentes | Como rodam |
|---|---|
| API, cada uma com **seus próprios dados** (prefixo por lente) | Paralelo — todas as chamadas `Agent` numa resposta só |
| API sobre o **mesmo recurso** (mesma entidade, mesmo estado) | Sequencial — uma corrompe a leitura da outra |
| Tela | **Sequencial** — o navegador é um só; duas lentes dirigindo a mesma janela se atropelam |

Lançar um `Agent`, esperar, lançar o próximo serializa o grupo e o paralelismo evapora.

Cada subagente vai com `subagent_type: general-purpose` e **`model: sonnet`** — o alvo chega decidido,
o protocolo está no arquivo, e o julgamento sobre o que volta fica desta ponta. Ele recebe:

> Leia `${CLAUDE_SKILL_DIR}/lenses.md` e siga exatamente. Sua lente é **\<nome\>**, e apenas ela.
> Alvo: `<rota + contrato conhecido, ou tela + fluxo>`. Ambiente já de pé em `<url:porta>`.
> Credenciais de teste: `<as que valem>`. Prefixo dos dados que você criar: `qa-<data>-<lente>`.
> Fora de escopo: `<o que outra lente cobre, e o que o usuário pediu pra não tocar>`.

Subagente não herda nada desta sessão: o que não estiver no prompt dele não existe.

**Tela sem driver de navegador** (`claude-in-chrome` ou Playwright indisponível): não simule. Descreva
o passo exato pro usuário executar, aguarde o relato dele e registre como *verificado manualmente pelo
usuário* — é evidência de grau diferente, e a diferença precisa aparecer.

## O que volta, e o que você aceita

Achado sem **passos de reprodução** e **evidência literal** (comando e resposta, ou os cliques e o que
apareceu na tela e no console) não entra na lista. Re-execute na hora o que parecer decisivo: relato
de subagente é relato, e um falso positivo custa mais caro que um achado a menos.

Grau, que não é severidade:

| Grau | O que é |
|---|---|
| **bug** | Viola a spec, o contrato da API ou quebra o fluxo. Tem reprodução. |
| **inconsistência** | Funciona, mas diverge de como o resto do sistema se comporta. |
| **escrita** | Typo, acentuação, texto truncado, label que mente, termo inconsistente, inglês vazando. |
| **dúvida** | Comportamento que ninguém especificou e que parece errado. **Vira pergunta, não bug** — inventar requisito aqui é o mesmo vício da spec, um passo mais tarde. |

Severidade é separada e vale só pros dois primeiros: quebra o fluxo · degrada · cosmético.

## Onde isso fica

**Na tela, como veio** — os achados inteiros, agrupados por grau, cada um com reprodução. Você não
resume em placar: "12 checagens, 3 falhas" é a informação que menos importa.

O que sobrevive vai pro `notes.md` da mudança, seção `## QA`. Sem mudança associada, fica na tela e
pronto — arquivo novo pra cada rodada de QA é convite a não ler.

```markdown
## QA — DD-MM-YYYY

Ambiente: <boot · porta> · Alvo: <o que foi exercitado> · Lentes: <quais>

### Verificação pendente do plano
| Requisito | Esperado | Observado | Evidência | Status |
|---|---|---|---|---|
| R3 | 200 + desconto aplicado | 200, total 90.00 | `<trecho da resposta>` | ✅ |

### Achados
| # | Grau | Severidade | O que acontece | Reprodução |
|---|---|---|---|---|

### Onde não olhei
- <o que ficou fora do alcance das lentes, e por quê>

### Dado criado
- <o que ficou no ambiente · limpo | pendente>
```

`thoughts/` é local e gitignored — não commite.

## Depois: corrigir agora?

Peça pra ele **ler os achados** antes de decidir, e trate a decisão como dele. A fronteira é a mesma
do review, e ela não é negociável por pressa de fim de ciclo:

| O achado | Caminho |
|---|---|
| Não muda comportamento — typo, texto, label, formatação | corrige na hora, com o gate rodando depois |
| **Muda comportamento** | vira tarefa em `tasks.md`, bloco `## Achados de QA` → `implement` |
| Cresce — decisão de design, requisito que ninguém tinha visto | para: é mudança de spec ou de plano, não conserto |
| `dúvida` | volta pra ele como pergunta, e a resposta pode virar requisito novo |

Correção que muda comportamento **não** se faz aqui e não se faz à mão: ela passa por teste que falha
antes, como qualquer outra. Foi por escapar disso no fim do ciclo que o v9 acumulou dívida.

Nenhuma peça deste toolkit invoca outra. Termine com o comando pronto, como última linha, escolhendo
pelo que apareceu:

> Escrevi as 3 correções de comportamento em `tasks.md`, bloco `## Achados de QA`.
> Rode **`/tk7:implement`** pra executá-las com TDD.

ou

> Nada que mude comportamento. Rode **`/tk7:imp-review`** sobre o que está staged.

ou, quando o que apareceu for grande demais pra tarefa:

> O achado #2 contradiz o R4 da spec. Rode **`/tk7:spec`** — isto é decisão de comportamento, não bug.

## Ao terminar

Em tela: o que foi exercitado e com que lentes, a verificação pendente que fechou (com evidência), os
achados por grau, **onde você não olhou**, o dado que ficou no ambiente, e a confirmação de que tudo
que você subiu foi derrubado. Depois a pergunta de correção.
