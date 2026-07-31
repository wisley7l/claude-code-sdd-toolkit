# Créditos — skill `pr-audit`

> Não carregado no contexto do agente: fica ao lado do `SKILL.md` e não é referenciado por ele.
> Ver `NOTICE.md` na raiz para o protocolo.

## Origem

**Construção própria.** O `/pr-followup-audit` v9 (341L) não tem equivalente em nenhuma fonte
mapeada — nem no tlc-spec-driven, nem no OpenSpec, nem no mattpocock/skills. Saiu de uso real.

Sem obrigação de atribuição.

## ⚠️ Contrato de dados preservado (Parte E.3)

A issue perene **já existe em repositórios reais** — este é o contrato mais frágil da Parte E,
porque o dado mora no GitHub e não em disco local.

| Invariante | Como sobreviveu |
|---|---|
| **Uma issue por repositório**, título canônico `chore: Auditoria contínua de follow-ups de review` | mantido, com instrução explícita de **procurar antes de criar** |
| Body = **só o que está aberto** (é de onde sai o contador) | mantido, com o porquê: body que só cresce trava o contador e para de significar |
| Bloco que fecha inteiro **sai do body** e sobrevive no comentário | mantido |
| Comentário = a rodada, **append-only**, nunca reeditado | mantido |
| Formato do item, parseável e ordenável | mantido verbatim |
| Taxonomia `SEGURANCA > DADO > CONTRATO > DISPONIBILIDADE > ROBUSTEZ > COBERTURA > HIGIENE` | mantida, com a justificativa de cada posição |
| Desempate: `ativo` antes de `armado`; irreversível antes de reversível | mantido |
| Item aberto rodada após rodada = má descrição, mau dimensionamento ou falta de dono | mantido |
| **Fechar como risco aceito é resultado legítimo** | mantido |

## O que sobreviveu porque é raro, não porque é antigo

Boa parte das 341 linhas era julgamento acumulado que nenhuma reescrita produziria do zero. Foi
preservado quase intacto:

- **`APPROVED` com body é a assinatura do follow-up.** *"Aprovado com texto não quer dizer resolvido
  — quer dizer o oposto."* É o achado mais útil da peça inteira e o menos intuitivo.
- **As três que parecem dívida e não são** — review esperando resposta (compare `submitted_at` com o
  último commit), follow-up que já tem PR aberto, decisão deliberada de adiar.
- **O anti-loop do opcional não feito:** *"item nasce baixo porque foi adiado, nunca é pego porque
  está baixo"*. Adiar uma vez é critério de **entrada** na dívida, não de posição na fila — o
  revisor ofereceu a janela mais barata que existia e ela foi recusada por decisão explícita.
- **As duas que não parecem dívida e são** — fix aceito que nunca executa (o `if (campo > 0)` num
  caminho onde ninguém popula o campo) e regressão de escopo entre PRs.
- **As armadilhas** — bot que "revisou" sem revisar, tracker invisível (`git check-ignore`),
  urgência inflada, ordenar pelo histórico, confiar no corpo do PR.

## A janela, por pedido do usuário

*"pr-audit ainda peço para fazer igual era no v9 por data, tipo a 4 semanas atrás ou do dia x ao
dia y"*. O v9 cobria "N semanas" e "desde marco"; **intervalo fechado não estava lá**, e a montagem
filtrava no cliente (`--limit 60` e corta).

Isso escondia um defeito: `--limit` corta pelos **mais recentes**, então uma janela antiga volta
vazia sem erro nenhum — e vazio silencioso lê como "nenhuma dívida", a conclusão errada mais cara
desta peça.

Passou a resolver tudo em datas absolutas e filtrar **no servidor**, via `--search`:

```
merged:2026-07-01..2026-07-15
```

Verificado contra a API real do GitHub antes de escrever, junto com `date -d '4 weeks ago'` para as
formas relativas. A janela resolvida é confirmada na tela antes de gastar subagente.

## Sem script aqui, e isso é decisão, não omissão

A I.28 mandou o determinístico virar script, e o `roadmap` e o `memory-audit` seguiram. **Aqui não**,
pelo motivo que o próprio v9 já registrava: *"a montagem da lista de PRs muda de `jq` conforme o
filtro; um script fixo seria contornado na primeira variação."*

A diferença é a natureza do trabalho. O roadmap tem formato fixo e cálculo sempre igual — script.
A auditoria tem consulta variável e triagem que é julgamento puro — prosa, com o subagente fazendo
a coleta. Determinístico não é sinônimo de scriptável: o que varia por pergunta não vira comando.

## Divisão de trabalho: coleta versus triagem

O v9 já tinha isso certo e foi mantido: **os subagentes coletam e verificam; a triagem é
centralizada** em quem delegou. Auditores diferentes olham PRs diferentes e triariam com critérios
divergentes — e critério divergente num checklist compartilhado é o que faz o time parar de confiar
nele.

Daí a obrigação de campos no retorno (`Fonte`, `Classe`, `Opcional?`, datas): sem eles, quem tria
adivinha. A instrução é reprocessar o grupo, não completar de cabeça.

## Relação com o `pr-close`

Não se sobrepõem, e vale dizer por quê: o `pr-close` colhe follow-up de **um** PR no momento do merge —
é profilaxia, e previne acumulação futura. O `pr-audit` varre **N PRs já mergeados** — é resgate do
passivo que existe antes de haver fluxo, ou do que escapou dele.

Mesma fonte (comentários de review), saídas diferentes: o `pr-close` extrai também *regra de
comportamento* pra memória; o `pr-audit` extrai só *trabalho pendente*.
