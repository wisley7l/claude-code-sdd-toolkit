# Créditos — skill `baseline`

> Não carregado no contexto do agente: fica ao lado do `SKILL.md` e não é referenciado por ele.
> Ver `NOTICE.md` na raiz para o protocolo.

## Origem

**Peça nova, sem equivalente em nenhuma das fontes.** O formato de saída, porém, é contrato
herdado do v9 e precisa ser preservado — ver `REFACTOR-v10.md`, Parte E.2.

### Contrato preservado do v9

Fonte: `deprecated/commands-v9/references.v9/capability-template.md` (126 linhas).

`thoughts/capabilities/<domínio>.md` sem timestamp · `C<N>` sequencial nunca reusado · todo `C<N>`
com `[Origem]` obrigatório · comportamento observável nunca implementação · cenários
`Quando → então` · seções `Comportamento atual` / `Fora do escopo` / `Dívida conhecida` /
`Removido`, com as vazias omitidas · frontmatter `dominio` + `atualizado` + `specs` · domínio como
área de comportamento (não módulo) · preferir encaixar em capability existente · nunca criar
domínio novo sem confirmação · nunca commitar (`thoughts/` é gitignored).

### Divergência consciente com o OpenSpec

O OpenSpec **recusa** povoamento retroativo por princípio:

> "You do not document your whole codebase to start. You write specs only for what you're about
> to change." — `docs/existing-projects.md`

Adotamos assim mesmo, por dois motivos que o modelo deles não cobre:

1. **O delta precisa saber contra o que está calculando.** Sem `C<N>` pro comportamento alterado,
   a spec marca `ADDED` o que é `MODIFIED`, e o fechamento mescla errado — em silêncio.
2. **Partimos de zero capability** em todos os projetos. O modelo delta-first puro só converge
   depois de muitos ciclos; até lá, todo domínio tocado pela primeira vez fica sem base.

O risco que eles evitam (spec derivada que ninguém validou, bug promovido a contrato) é tratado
aqui por três mecanismos, não ignorado:

- **`[Origem: derivado do código em <data>]`** distinto de `[Origem: spec-X · PR #N]` — a
  procedência é explícita no documento, não implícita.
- **A tabela promessa × acidente** — teste dedicado é promessa; só-no-código é comportamento de
  origem desconhecida, marcado com confiança baixa; detalhe interno fica de fora; discordância
  entre teste e código não é resolvida pelo agente, é sinalizada.
- **Na dúvida, deixa de fora e diz que deixou.** Ausência o próximo ciclo corrige; requisito
  falso, não.

E a postura "não ferva o oceano" **é adotada**: um domínio por vez, de preferência o que se vai
mexer, com "parar no meio" declarado como resultado legítimo.

## Adaptações e decisões nossas

- **Testes como fonte primária** — contam o que alguém *decidiu*; implementação conta o que o
  código faz, bugs inclusive. A ordem de evidência (testes → docs → código → `git log` →
  `structure-cache --importers`) segue a mesma lógica da skill `spec`.
- **Consumidor externo como sinal de contrato**: se algo é importado de fora do domínio, é mais
  provável que seja promessa que detalhe.
- **Lotes de 3 a 5 requisitos**, escritos ao fim de cada lote. Vem do pedido do usuário ("povoar
  por etapas") e resolve dois problemas: ninguém revisa trinta requisitos de uma vez (aprovação em
  bloco é a anestesia que o v10 combate), e a sessão pode ser interrompida sem perder trabalho.
- **Complementa, nunca reescreve.** Requisito com origem de spec não é tocado por derivação de
  código — se o código o contradiz, isso é *achado* pro usuário (possível regressão ou sync
  perdido), não correção automática.
- **`disable-model-invocation: true`** — escreve arquivos. E a skill `spec` **oferece** o baseline
  ao usuário em vez de invocá-lo: quem decide gastar esse trabalho é ele.

## Por que não tem adversário (ao contrário da `spec`)

A `spec` precisa de adversário porque o autor não enxerga o que faltou, e o gate dela é um único
momento de leitura no fim. O `baseline` já é adversarial por construção: cada lote de 3–5
requisitos passa pelo usuário com a evidência (`arquivo:linha`) do lado, antes do próximo. A
revisão é contínua e granular, não um passe único no final.
