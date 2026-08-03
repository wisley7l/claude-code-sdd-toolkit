# CLAUDE.md — claude-code-sdd-toolkit

## Estado atual: refactor v10 em curso

Este repo está **em reconstrução**. Todo o toolkit v9 (24 commands, 4 skills, 17 references,
READMEs) foi **deprecado em 30-07-2026**. O ciclo central e as peças que tocam dados vivos já
nasceram (Ondas 0 a 2, mais `pr-review` da Onda 3); falta a periferia — pesquisa, diagnóstico de
bug, verificação e o `setup`.

👉 **Leia [`REFACTOR-v10.md`](./REFACTOR-v10.md) antes de qualquer coisa.** É o mapa do refactor:
inventário do v9, mapa da referência adotada, regras do v10, fila de reconstrução e —
o mais importante — os **contratos de dados** (Parte E) que não podem quebrar.

## O que é este repo

Coleção de slash commands e skills para [Claude Code](https://docs.anthropic.com/en/docs/claude-code).
Não é uma aplicação — é um **toolkit** de artefatos markdown instalados em `~/.claude/commands/`
e `~/.claude/skills/`.

```
.claude-plugin/plugin.json   # manifesto — o repo É o plugin `tk7`
skills/                      # AS PEÇAS VIVAS. o scanner varre aqui — nada morto dentro
  grilling/  spec/  baseline/  plan/  test-plan/  implement/
  worktree/  pr-draft/  code-review/  pr-review/  pr-ready/
  pr-close/  pr-audit/  roadmap/  memory/
REFACTOR-v10.md              # o mapa. começa aqui.
NOTICE.md + LICENSES/        # atribuições de terceiros + protocolo
deprecated/                  # TODO o v9: commands-v9/ skills-v9/ READMEs, CLAUDE.v9
scripts/                     # executáveis (structure-cache, ouvir) — INTOCADO pelo refactor
```

**O repo é um plugin.** `.claude-plugin/plugin.json` com `name: tk7` faz todas as peças
carregarem namespaced: `skills/spec/SKILL.md` → **`/tk7:spec`**. Plugin skills **não colidem
com skills personal, project ou bundled** — e o nome curto (`/spec`) continua funcionando como
atalho enquanto estiver livre. Instala como *skills-directory plugin* (`~/.claude/skills/tk7/`),
sem marketplace e sem install step — clone ou symlink, os dois carregam.

⚠️ **Nada de arquivo morto dentro de `skills/`** — o scanner varre esse diretório. Foi por isso
que `skills/deprecated/` e `commands/deprecated/` foram consolidados em `deprecated/` na raiz.

**Estrutura das peças:** `skills/<nome>/SKILL.md` + `CREDITS.md` irmão. Commands e skills foram
fundidos no Claude Code, e skill é superset (arquivos de apoio no diretório, controle de
invocação, `context: fork`). Nomes em inglês (leading word é conceito pré-treinado), corpo em pt-BR.

## Regras enquanto o refactor durar

1. **Nada nasce sem passar pela Parte C** do `REFACTOR-v10.md` (leading word, invocação
   explícita model vs user, granularidade, failure modes). Peça que não passa, não entra.
2. **Um por vez.** Revisar → decidir → escrever → usar de verdade → só então a próxima.
   Nada de port em lote do v9.
3. **⚠️ Parte E é bloqueante.** `roadmap`, `sdd-close`, memória e auditoria tocam dados que
   existem em projetos reais fora deste repo. Recriar sem preservar formato (ou sem escrever
   migração) quebra dado vivo.
4. **Não deletar `deprecated/`** — é fallback, é a fonte canônica dos contratos da Parte E,
   **e carrega as atribuições de licença** (ver `NOTICE.md`).
5. **Atribuição nunca entra no `SKILL.md`** — vai em `skills/<nome>/CREDITS.md`, arquivo irmão
   não referenciado pela skill, portanto fora do contexto em runtime. Texto integral da licença
   em `LICENSES/`. Protocolo completo no [`NOTICE.md`](./NOTICE.md). ⚠️ Conceitos do v9 vindos
   de fonte **CC-BY-4.0** (test count protection, gates, doc auto-sized, Knowledge Verification
   Chain) mantêm a obrigação de atribuir mesmo reescritos com outras palavras.
6. **Não commitar/pushar sem o usuário pedir explicitamente.**
7. **Idioma:** ✅ decidido — **nome da skill em inglês, corpo e docs em pt-BR.** O nome é
   *leading word*, conceito pré-treinado que ancora a invocação; o corpo é pra você ler.

## Princípios que sobrevivem ao v10

Não são negociáveis e estão detalhados na Parte E.5 do `REFACTOR-v10.md`:

- **Red verificável** — o teste falha pelo motivo certo antes de implementar; falso-verde = parada dura.
- **Test count protection** — contagem de testes não cai em silêncio.
- **Commit sob aprovação humana** — `git add` livre; `commit`/`push` só com OK explícito.
- **Gate de verde** — CI passou, ou suíte local completa, antes de entregar.
- **Zero inferência** — comportamento de API se verifica (Context7 ou código existente).
- **Spec viva só sob merge** — comportamento não entregue nunca entra na capability.
- **Usuário no volante** — o agente busca **fato**; a **decisão** é do usuário. Foi a ausência
  disso que motivou o refactor.
