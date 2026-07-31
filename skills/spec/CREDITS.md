# Créditos — skill `spec`

> Não carregado no contexto do agente: fica ao lado do `SKILL.md` e não é referenciado por ele.
> Ver `NOTICE.md` na raiz para o protocolo.

## Origens

**Gist "Formação da especificação"** por @parruda —
https://gist.github.com/parruda/85bf3d6ee2e8adee5c0dd9429afd76b3
**Sem licença declarada** → conceito sim, texto não. Nada foi copiado.

Conceito herdado: a especificação de comportamento como fase própria, anterior ao plano técnico;
pesquisa no codebase antes de escrever; proibição explícita de descrever o COMO; critérios
verificáveis sem linguagem vaga.

**Conceito recusado:** as 8 seções obrigatórias (histórias/stakeholders, critérios de sucesso, RF,
RNF, restrições, contexto técnico, testes de aceitação, mapa RF→AT) e o método "leia todos os
arquivos relevantes". Motivos:

- Formulário fixo orienta a **completude de seções**, não a qualidade do requisito. O gate do v9
  verificava se as seções existiam — um documento passava inteiro sendo intestável.
- A seção "Contexto Técnico & Pontos de Integração" **contradiz a própria proibição do COMO**.
  Herdamos essa contradição no v9 sem notar.
- "Ler todos os arquivos relevantes" não tem critério de parada; pesquisa sem limite produz
  documento sem limite. Trocado pela capability como critério de parada.

**OpenSpec** (Fission-AI) — MIT © 2024 OpenSpec Contributors.
Texto da licença: `../../LICENSES/` · Conceitos, sem cópia de texto.

- Um comportamento por requisito; "and also" significa que são dois.
- Observável e testável por quem não leu o código (o exemplo do upload de 10 MB é adaptação do
  contraste que eles usam).
- Cenário precisa **exercitar**, não reafirmar o requisito; bugs moram nas bordas.
- Nome descritivo de cenário em vez de "Cenário 2".
- Palavras-chave RFC 2119 (`DEVE`/`DEVERIA`/`PODE`), com `DEVE` como padrão.
- **Right-sizing**: uma intenção por mudança, articulável numa frase.
- **Delta-first** `ADDED`/`MODIFIED`/`REMOVED` — convergência independente com o v9, que já
  usava exatamente essas três marcações.
- A pergunta de fechamento vem do "two-minute pass" deles: *"I'd be comfortable if the AI built
  exactly this and nothing more."*
- Postura brownfield ("you don't document all of it") no tratamento de capability ausente.

**tlc-spec-driven** (tech-leads-club/agent-skills) por Felipe Rodrigues — **CC-BY-4.0**.
⚠️ Atribuição obrigatória e permanente, inclusive em adaptações.

Conceito presente aqui: consulta a fonte antes de assumir (Knowledge Verification Chain), que no
v9 virou o princípio "Zero Inferência" e aqui aparece como a ordem de fontes do legwork.

## Adaptações nossas

- **Ordem de fontes por pergunta**, do barato pro caro, com a **capability como critério de
  parada** — resolve o problema de pesquisa sem limite herdado da gist.
- **Testes valem mais que implementação** pra descobrir o comportamento prometido. O v9 só fazia
  esse inventário no `/sdd-plan` (Etapa 1 do pair de testes) — tarde demais, porque a spec já
  tinha declarado como novo um comportamento que já tinha teste.
- **`structure-cache` para dimensionar, não para descobrir** — a skill responde estrutura, não
  comportamento, e só cobre TS/JS.
- **Régua do `grilling` por custo de reverter** (escopo, delta `MODIFIED`/`REMOVED`, conflito com
  a capability), em vez de entrevista ritual em toda spec.
- **Chamada explícita do `grilling`**, não auto-invocação: descriptions são truncadas quando o
  listing de skills estoura o budget, começando pelas menos invocadas — uma skill pouco usada
  some da auto-invocação sem avisar.
- **RNF vira requisito normal** com número e cenário, em vez de seção separada.
- **Suposições explícitas** quando a decisão não sobe pro usuário — contestar suposição escrita é
  barato; descobrir suposição implícita depois do código, não.
- **Change folder única** (`thoughts/changes/NNN-slug/`) em vez de `thoughts/specs/`.

## O adversário (`adversary.md`)

Não vem de nenhuma das fontes — **nenhuma das três valida a spec com agente separado**:

- **parruda**: auto-verificação. "Leia o arquivo da especificação / Verifique se todas as seções
  estão presentes e são substanciais" — o mesmo agente que escreveu revisa.
- **v9**: idem (Passo 8, "após escrever, releia e verifique"). Os subagentes do `/sdd-spec` v9
  apareciam só na **pesquisa** (Passos 3 e 4, `Explore`), nunca na validação. O painel de
  subagentes ficava no `/sdd-plan`, não na spec.
- **OpenSpec**: põe a verificação no **humano** (o "two-minute pass"), sem agente.

**Por que adicionamos:** auto-verificação pega erro de forma (seção vazia, `C<N>` inexistente),
mas não pega **ausência** — se o autor soubesse que faltava um requisito, teria escrito. E
"o cenário exercita ou só repete?" é justamente o critério que quem escreveu não consegue aplicar
em si mesmo.

**Por que adversário e não juiz** (decisão explícita do usuário): um validador que aprova vira
anestesia — "o agente validou, deve estar bom" — e isso adiciona mais uma camada entre o usuário
e o artefato, que é o problema que o refactor v10 existe pra resolver. Trocaríamos ler 300 linhas
por ler um ✅. Por isso ele é proibido de emitir veredito e obrigado a fechar dizendo **onde
olhou**, para o usuário saber o que não foi coberto.

O "two-minute pass" do OpenSpec segue sendo o gate real, e é humano: *"eu ficaria confortável se
isto fosse construído exatamente assim, e nada além?"*

## Decisões de design

- **`disable-model-invocation: true`** — a skill escreve arquivos. A doc do Claude Code recomenda
  invocação manual para workflows com side effect ou onde o timing importa. Também zera o context
  load da description.
- **Template inline, não em arquivo irmão** — é usado em toda execução; arquivo de apoio faria
  sentido para referência ocasional, não para o formato principal.
- **Escrita como standing instructions**, não como passos numerados: o `SKILL.md` entra no
  contexto uma vez e permanece pela sessão, então receita sequencial se perde depois do primeiro
  turno.
