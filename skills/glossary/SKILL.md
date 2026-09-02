---
name: glossary
description: Explica um termo técnico em português claro e guarda a explicação no dicionário pessoal do usuário, em ~/.claude/thoughts/glossario.md. Use quando ele perguntar o que uma palavra quer dizer ("o que é gate?", "não conheço esse termo", "isso aí é o quê?"), quando pedir a lista do que já aprendeu, e também por conta própria — sempre que você usar um termo técnico que ainda não está no dicionário, registre lá.
argument-hint: <termo, ou nada pra ver a lista>
allowed-tools: Read Edit Write Grep Glob Bash(ls *)
---

# glossary

O dicionário pessoal do usuário vive em `~/.claude/thoughts/glossario.md`. É um arquivo só, global,
usado em qualquer projeto.

Ele está aprendendo o vocabulário técnico. Não presuma que uma palavra é conhecida só porque é
comum no mercado.

## O que fazer, em cada situação

**Ele perguntou um termo que já está lá.** Responda em duas ou três linhas, com suas palavras, sem
mandar ele abrir arquivo. Se der pra mostrar o termo em uso no projeto onde vocês estão agora,
mostre a linha real — é o que faz fixar. Tire o `🆕` daquela linha do índice.

**Ele perguntou um termo que não está lá.** Explique primeiro, na conversa. Depois escreva o
verbete e diga em uma linha que guardou. Já entra sem `🆕`, porque ele acabou de ler.

**Ele chamou sem termo nenhum.** Mostre o índice com os `🆕` em cima. Ofereça ler dois ou três
deles ali mesmo. Não despeje o arquivo inteiro na tela.

**Você usou um termo que não está lá.** Isso vale em qualquer conversa, sem ele pedir nada. Escreva
o verbete com `🆕` e avise numa linha só:

> (guardei *idempotente* no glossário)

Nada de parar o assunto pra dar aula. Se ele quiser, pergunta.

**Ele disse que já sabe.** Tire o `🆕` e siga. Não insista.

## O que conta como termo pra registrar

Registre palavra que carrega um conceito: `gate`, `flaky`, `idempotente`, `blast radius`, `mock`.

Não registre nome próprio de ferramenta (`npm`, `git`, `Playwright`), nome de arquivo, nem palavra
comum de programação que ele usa todo dia (`função`, `array`, `commit`, `merge`). Na dúvida entre
registrar e não registrar, registre — sobra é barato, falta é o problema que ele levantou.

## Como escrever um verbete

O que faz um verbete bom:

- **Primeira frase entrega o significado.** Sem rodeio, sem história antes.
- **Português comum.** Se a explicação precisa de outro termo técnico, ou você explica ele ali
  mesmo em cinco palavras, ou aponta pro verbete dele com `[termo](#termo)`.
- **A origem, quando ajuda a lembrar.** `nit` vem de catar lêndea, `stale` é pão dormido. Imagem
  gruda melhor que definição.
- **Uma comparação com o vizinho**, quando existe par que confunde: fixture e factory, mock e stub,
  nit e must-fix.
- **Por que alguém se importa.** O que dá errado no mundo real quando a coisa que o termo nomeia
  aparece.
- **Uma linha real de onde ele viu**, em citação, quando você souber de onde veio.

Três a seis linhas. Verbete que vira artigo ninguém relê.

Modelo:

```markdown
## <termo>

<O que é, na primeira frase.> <De onde vem a palavra, se ajudar.>

<Por que importa — o problema real que ele nomeia.>

<Comparação com o termo vizinho, se houver.>

> `<arquivo>` — "<a frase onde ele apareceu>"
```

E a linha no índice, em ordem alfabética:

```markdown
| [<termo>](#<âncora>) | <o significado em oito palavras> | 🆕 |
```

## Cuidados com o arquivo

Ele é do usuário, e é único. Sempre leia antes de escrever, e **acrescente** — nunca reescreva o
arquivo inteiro por causa de um verbete novo. Verbete que já existe você melhora no lugar, sem
duplicar entrada no índice.

Ordem alfabética no índice e nos verbetes. Se o arquivo não existir, crie com o cabeçalho, o índice
e o primeiro verbete.
