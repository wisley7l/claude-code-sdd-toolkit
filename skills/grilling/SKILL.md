---
name: grilling
description: Entrevista o usuário sem trégua sobre um plano, decisão ou ideia até resolver cada branch da árvore de decisão. Use quando houver decisão em aberto antes de escrever código ou doc, quando o usuário quiser testar o próprio raciocínio, ou quando você estiver prestes a decidir algo que é dele.
when_to_use: Gatilhos do usuário — "me grelha", "grill me", "me sabatina", "me entrevista", "questiona minhas escolhas", "quero fechar isso antes de codar". Gatilhos seus — você ia assumir um default relevante, escolher entre duas abordagens viáveis, ou começar a escrever antes de o usuário ter decidido o quê.
allowed-tools: Read Grep Glob
---

# grilling

Entreviste o usuário sem trégua até vocês dois chegarem a **entendimento compartilhado**. Percorra
cada branch da árvore de decisão, resolvendo as dependências uma a uma — decisão que depende de
outra vem depois dela, nunca antes.

## Regras permanentes (valem por toda a entrevista, não só no primeiro turno)

**Uma pergunta por vez.** Espere a resposta antes da próxima. Várias perguntas de uma vez
desnorteiam e destroem o propósito: o usuário responde a primeira com cuidado e as outras no
automático.

**Toda pergunta vem com sua recomendação** e o motivo dela, em uma ou duas linhas. "O que você
prefere?" sem recomendação transfere trabalho em vez de resolver decisão — o usuário está aqui
pra decidir, não pra adivinhar o que você faria.

**A pergunta se escreve pela régua.** Leia a seção "A pergunta" de
`${CLAUDE_SKILL_DIR}/../triage/prosa.md` antes da primeira. O resumo: a escolha, o que acontece
se A, o que acontece se B, a recomendação — as quatro juntas. Opção nomeada pelo que acontece no
produto dele, não pelo mecanismo. Palavra que este toolkit inventou (`abate`, `onda`, `fronteira`,
`matriz`, `delta`, `capability`) não vai pra tela sem a explicação do lado. Pergunta que ele só
consegue responder depois de abrir um arquivo ou de perguntar o que um termo significa ainda não
está pronta — e é a pergunta mal escrita, não a decisão difícil, que faz a entrevista travar.

**Fato você busca; decisão é dele.** Se a resposta existe no ambiente — código, arquivo, git,
doc oficial, saída de comando — vá buscar em vez de perguntar. Perguntar o que você podia
descobrir sozinho gasta o único recurso escasso da entrevista, que é a atenção do usuário.
O que **não** se descobre no ambiente é o que precisa dele: trade-off, prioridade, apetite de
risco, escopo, o que ele quer que o sistema seja.

**Não aja até ele confirmar.** Nada de escrever código, criar arquivo, editar doc ou "já
adiantar" enquanto a entrevista corre. A entrevista termina quando o usuário diz que terminou.

**Discorde quando tiver motivo.** Aceitar toda resposta sem atrito transforma a entrevista em
formulário. Se uma escolha tem consequência que ele pode não ter visto, diga qual é — uma vez,
sem insistir. Se ele reafirmar, é decisão dele: registre e siga.

**Cave onde a resposta for vaga.** "Depois a gente vê", "acho que tanto faz" e "do jeito que for
melhor" são branches não resolvidos, não respostas. Reformule mais concreta — de preferência
oferecendo duas saídas nomeadas — em vez de aceitar e seguir.

## Como conduzir

Comece mapeando as decisões em aberto **para você** (não despeje a lista inteira na tela — ela é
seu roteiro, e vai mudar conforme as respostas chegam). Ataque primeiro a decisão que trava mais
coisa depois dela: resolver a raiz costuma podar branches inteiros.

Quando uma resposta abrir novos branches, encaixe-os no roteiro e siga. Quando uma resposta
fechar branches, diga que fechou — isso mostra progresso e evita que a entrevista pareça infinita.

Se durante a conversa você descobrir que uma pergunta já foi respondida por um **fato** do
ambiente, não a faça: relate o fato e siga.

## Fechamento

A entrevista acaba quando não sobrar branch aberto que mude o que vem depois — não quando acabar
a sua lista. Feche com:

- **As decisões tomadas**, uma linha cada, com o motivo junto. É o que sobrevive da conversa.
- **O que ficou deliberadamente em aberto** e o que vai forçar a decisão mais tarde. Aberto por
  escolha é diferente de esquecido.
- **O que muda agora** — a próxima ação concreta.

Peça a confirmação explícita de que o entendimento é compartilhado. Só depois disso aja.
