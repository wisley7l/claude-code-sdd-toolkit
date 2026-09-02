# Créditos — skill `glossary`

> **Este arquivo não é carregado no contexto do agente.** Vive ao lado do `SKILL.md` e é
> deliberadamente **não referenciado** por ele, para que atribuição e notas de design não
> consumam contexto em runtime. É documentação pra humano e cumprimento de licença na
> distribuição — a skill é o diretório inteiro, então este arquivo acompanha qualquer cópia.

## Origem

Original. Sem derivação de terceiros — nada a atribuir.

## O problema que a fez nascer (25-08-2026)

O usuário reclamou de densidade: *"ainda usa muito termo técnico que eu não estou acostumado, gate,
nit entre vários outros isso torna leitura muito densa"* — e completou: *"e tá sendo em tudo
ultimamente"*.

A contagem confirmou. Nas 16 skills: `lente` 84 ocorrências, `red/green` 53, `gate` 48, `baseline`
20, `nit` 5, mais `must-fix`, `flaky`, `fixture`, `dedup`, `trade-off`, `overhead`. Quase tudo veio
da referência em inglês que serviu de base pro v10, entrou sem tradução e virou vocabulário da casa.

## A decisão

A saída óbvia era traduzir tudo — trocar `gate` por "comando que verifica", `nit` por "opcional", e
varrer os 16 arquivos. **Foi ele que recusou**, e o argumento é melhor que o meu: traduzir esconde o
termo. Ele continuaria sem entender PR, documentação e conversa de fora, que usam `gate` e `nit` de
qualquer jeito. Aprender o vocabulário serve pra vida inteira; renomear serve só dentro deste repo.

Três escolhas dele, na sequência:

1. **Um dicionário só, global** (`~/.claude/thoughts/glossario.md`), não um por projeto — senão o
   vocabulário fica picado em N arquivos e `gate` seria explicado três vezes.
2. **Cresce dos dois lados** — quando ele pergunta, e quando o agente usa termo novo. O segundo é o
   que faz volume sem depender de ele lembrar de perguntar.
3. **Nasce populado** com os ~22 termos que o próprio toolkit usa, cada um com a frase real da skill
   onde aparece.

O `🆕` marca o que entrou e ele ainda não leu — é o que transforma um arquivo de consulta em algo
que dá pra estudar aos poucos.

## Por que uma skill e não só memória

A memória cobre o gatilho automático em qualquer sessão ("usei termo novo, gravo"). Mas consulta,
listagem, marcar como lido e as regras de como escrever um verbete são procedimento, e procedimento
em memória é peso morto de contexto em toda conversa. As duas peças coexistem: a memória dispara, a
skill executa.
