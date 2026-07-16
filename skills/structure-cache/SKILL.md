---
name: structure-cache
description: Consulta a estrutura do código (quem importa X, o que Y define, impacto de mexer num arquivo, god-nodes/acoplamento) a partir de um cache regenerável invalidado por hash — SEM reler código a cada consulta. Use quando precisar entender dependências/impacto estrutural de um codebase (fase de pesquisa de /sdd-plan e /sdd-spec, análise de blast radius antes de mudar um arquivo), ou quando o usuário pedir "quem usa/importa isso", "o que quebra se eu mexer aqui", "quais os módulos mais acoplados". Escopo atual: TS/JS. Cache em `<worktree>/thoughts/cache/structure/`, worktree-safe. NÃO é memória — o grafo é derivável e apodrece; só a conclusão não-óbvia vai pra auto-memory via /sdd-learning.
---

# structure-cache — Estrutura do código sob demanda, sem reler tudo

Um índice *shallow* da estrutura do código (imports + definições por arquivo, hotspots por acoplamento) que responde perguntas de dependência/impacto **sem reler os arquivos fonte**. É um **cache regenerável**, não conhecimento durável: invalidado por hash, jogado fora e reconstruído. O grafo **nunca** vai pra auto-memory — só a conclusão não-óbvia (via `/sdd-learning`).

## Comando

O motor é `scripts/structure-cache/build.py`, exposto no PATH como `structure-cache` (atalho `sc`):

```
structure-cache <build|check|query> [opções]
```

Instale o comando com `scripts/install-structure-cache.sh` (cria wrappers em `~/.local/bin` apontando pro motor no repo; sem sudo, idempotente). Os commands SDD que usam o cache (`/sdd-plan`, `/sdd-spec`, `/pair-review`, `/sdd-learning`) já trazem `Bash(structure-cache *)` no allowlist — **não prompta**. Se o comando não estiver instalado, o fallback é `python3 <toolkit>/scripts/structure-cache/build.py <...>`. O `--root` é **auto-detectado** via `git rev-parse --show-toplevel` — rode de qualquer subdir do repo/worktree.

> **Subagentes precisam ser instruídos explicitamente.** Um subagente `Explore`/`general-purpose` não herda o corpo do command que o lançou — se o prompt dele não mandar consultar o `structure-cache` antes de grepar, ele vai direto ao Grep e ignora o cache. Ao delegar pesquisa de estrutura/dependência, repita a diretiva no prompt do subagente (os commands `/sdd-plan` e `/sdd-spec` já fazem isso).

## Protocolo de consulta (consulta → fallback)

É o mesmo molde do Step 0 do Knowledge Verification Chain: **consulta o cache; se não serve, cai na fonte** (reler código). Nunca falha por ausência de cache.

1. **Query direto** — para uma pergunta estrutural, chame:
   - `structure-cache query --importers <file>` → quem importa o arquivo (blast radius)
   - `structure-cache query --imports <file>` → o que o arquivo importa
   - `structure-cache query --defs <file>` → definições no arquivo
   - `structure-cache query --hotspots [--top N]` → god-nodes por acoplamento
   - Acrescente `--json` para consumo programático.
2. **Interprete o exit code**:
   - `0` → respondeu. Use o resultado. Se veio aviso de STALE no stderr, considere `structure-cache build --incremental` antes de confiar em detalhes finos.
   - `3` → **sem cache**. Duas opções: (a) `structure-cache build` para criar (barato, sem LLM) e re-consultar; ou (b) **fallback**: reler o código como já se faz hoje (Grep/Glob/Read ou subagente Explore). Escolha (a) quando fizer várias consultas; (b) para uma pergunta pontual.
3. **Nunca bloqueie** o trabalho por causa do cache — ele é aceleração, não dependência.

## Manter o cache fresco

- `structure-cache build` — constrói/atualiza. **Incremental automático**: se já há cache, reaproveita os arquivos sem hash divergente (não precisa de flag). `--full` força rebuild completo.
- `structure-cache check` — exit `0`=fresco, `1`=stale. É o **backstop de correção** que pega `rebase`/`checkout`/`stash` (mudanças de arquivo que não passam por commit).
- `structure-cache export [--html PATH] [--open]` — gera um `graph.html` **local e self-contained** (força-dirigido, sem CDN) pra visualizar dependências/acoplamento. Abre via `file://`; nada sobe pra fora. Use quando o usuário quiser *ver* o grafo, não só consultar.
- `structure-cache open` — gera (se preciso) e **abre o grafo no navegador padrão**. É o atalho pra "quero ver o grafo".
- `structure-cache help` (ou sem subcomando) — lista todos os subcomandos.
- Hooks `post-commit`/`post-checkout` (opt-in) mantêm o cache morno automaticamente. Mesmo com hooks, `check`/query revalidam por hash — a correção não depende do hook.

## Worktree

O cache vive **dentro** do worktree corrente (`<worktree>/thoughts/cache/structure/`) e o `--root` resolve o topo *daquele* worktree. Cada worktree tem cache isolado — sem contaminação entre branches. Nada é escrito fora dessa pasta.

## Limites (escopo atual)

- **TS/JS apenas** (multi-linguagem é evolução futura).
- **Imports + definições**, sem call-graph / resolução de símbolo cross-arquivo (edges são `imports`, confiança `EXTRACTED`).
- Extração via tree-sitter quando instalado; senão, fallback regex (mesmo schema, menos preciso em casos complexos).
- Não substitui leitura de código para entender *lógica* — responde **estrutura/dependência**, não comportamento interno de uma função.

## Elo com a memória

O `HOTSPOTS.md` derivado (god-nodes, acoplamento) é insumo do `/sdd-learning`: ele lê esse arquivo e **propõe** `lesson`/`blocker` durável (ex.: "módulo X é hub de acoplamento — mexer impacta N subsistemas"), sob confirmação, via `memory-keeper`. O índice/grafo em si **não** é persistido na auto-memory.
