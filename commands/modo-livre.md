---
description: MODO LIVRE — toggle do modo autônomo. `on` instala settings (allow + ask pra commit/push + deny dos perigosos), `off` restaura backup, `update` reescreve com o JSON canônico. NUNCA commita/pusha/rm por iniciativa própria.
model: claude-sonnet-4-6
argument-hint: [on|off|update|status]
---

# /modo-livre

Antes de qualquer outra coisa:

1. Este command roda na **base Sonnet** (frontmatter) — toggle simples (parse de args + escrita de settings + filesystem ops), Sonnet dá conta. **Não rode `/model`**: trocar de modelo invalida o cache de prompt e gasta token à toa.
2. Rode `/compact` — se a sessão veio depois de `/sdd-plan` (único command que roda em Opus na thread principal e infla contexto), compactar agora libera tokens. Sessão nova sem comandos prévios: pule, não há o que compactar.

Você está implementando o toggle do MODO LIVRE para o projeto **na pasta atual**.

Parseie `$ARGUMENTS` (case-insensitive, trim espaços):

- `on`, `ativar`, `ativa`, `enable`, ou vazio → **ATIVAR**
- `off`, `desativar`, `desativa`, `disable` → **DESATIVAR**
- `update`, `atualizar`, `refresh`, `sync` → **ATUALIZAR**
- `status`, `estado`, `state` → **STATUS**
- qualquer outra coisa → mostre status + lista de subcomandos

## Pré-cheques (toda invocação)

1. Confirme `pwd` — você está na raiz do projeto onde o modo será aplicado
2. Se o subcomando é `on` e os diretórios não existem, crie:
   - `mkdir -p .claude` (settings ficam aqui — o harness procura aqui)
   - `mkdir -p thoughts/modo-livre` (marker e backup ficam aqui — `thoughts/` é convencionalmente gitignored em projetos SDD, evita poluir o repo)
3. Marker file: `thoughts/modo-livre/active`
4. Backup file: `thoughts/modo-livre/settings.local.json.bak`
5. Settings file: `.claude/settings.local.json`

> **Por que esses paths?** A gambiarra é deixar tudo que não é o `settings.local.json` em si dentro de `thoughts/`, que já é gitignored em projetos SDD. Assim o command NÃO precisa mexer no `.gitignore` do projeto. O `.claude/settings.local.json` em si vai aparecer em `git status` se não estiver gitignored — você decide se adiciona manualmente ou ignora.

## ATIVAR (`on`)

**1.** Se `thoughts/modo-livre/active` JÁ existe → mostre:
```
Modo livre já está ATIVO desde <timestamp do marker>.
Use `/modo-livre off` para desativar.
```
e pare.

**2.** Se `.claude/settings.local.json` existe → faça backup:
```bash
cp .claude/settings.local.json thoughts/modo-livre/settings.local.json.bak
```
Se NÃO existe → não faça backup (não havia config anterior).

**3.** Escreva `.claude/settings.local.json` com o conteúdo do reference `modo-livre-settings.json` (ver seção [JSON canônico](#json-canônico)).

**4.** Crie o marker com timestamp ISO 8601:
```bash
date -Iseconds > thoughts/modo-livre/active
```

**5.** Avise ao usuário:
```
✅ MODO LIVRE ATIVADO
Marker: thoughts/modo-livre/active (<timestamp>)
Backup: <"presente em thoughts/modo-livre/settings.local.json.bak" OU "nenhum (sem config anterior)">

⚠️ RECARREGUE A SESSÃO pro harness aplicar:
   1. Ctrl+C
   2. claude (novamente, na mesma pasta)

As regras NUNCA (commit/push por iniciativa própria, rm, etc) continuam valendo —
guardrail comportamental + harness: commit/push promptam SEMPRE (ask),
force push e destrutivos ficam bloqueados (deny) em qualquer permission mode.

💡 Compatível com permission mode AUTO (Shift+Tab após opt-in, ou
   `claude --permission-mode auto`) — deny/ask continuam valendo nele.
```

## DESATIVAR (`off`)

**1.** Se `thoughts/modo-livre/active` NÃO existe → mostre:
```
Modo livre não está ativo. Nada a desativar.
```
e pare.

**2.** Restaurar settings:
- Se `thoughts/modo-livre/settings.local.json.bak` existe → `mv` ele de volta:
  ```bash
  mv thoughts/modo-livre/settings.local.json.bak .claude/settings.local.json
  ```
- Se NÃO existe (não havia config antes) → `rm .claude/settings.local.json`

**3.** Remova o marker:
```bash
rm thoughts/modo-livre/active
```

**4.** Limpeza opcional (tentativa, ignore erro se não vazio):
- `rmdir thoughts/modo-livre` (se vazio)
- `rmdir .claude` (se vazio)

**5.** Avise:
```
✅ MODO LIVRE DESATIVADO
Settings restaurado: <"backup aplicado" OU "removido (não havia anterior)">

⚠️ RECARREGUE A SESSÃO pro harness aplicar:
   1. Ctrl+C
   2. claude (novamente)
```

## ATUALIZAR (`update`)

Use quando o **JSON canônico** mudou (novas regras de allow/deny corrigidas) e você quer aplicar a versão atual sem desativar/reativar — preserva o backup original intacto.

**1.** Se `thoughts/modo-livre/active` NÃO existe → mostre:
```
Modo livre não está ativo neste projeto. Use `/modo-livre on` em vez de update.
```
e pare.

**2.** Aviso preventivo (mostre antes de sobrescrever):
```
⚠️ Vou sobrescrever .claude/settings.local.json com o JSON canônico atual.
   Se você editou esse arquivo manualmente após o `on`, suas edições serão perdidas.
   O backup ORIGINAL (pré-modo-livre) em thoughts/modo-livre/settings.local.json.bak fica intacto.
```

**3.** Sobrescreva `.claude/settings.local.json` com o conteúdo do reference `modo-livre-settings.json` (ver seção [JSON canônico](#json-canônico)).

**4.** Atualize o timestamp do marker (opcional, ajuda no debug):
```bash
date -Iseconds > thoughts/modo-livre/active
```

**5.** Avise:
```
✅ MODO LIVRE ATUALIZADO
Settings reescrito com o JSON canônico atual (<timestamp>).
Backup original preservado em thoughts/modo-livre/settings.local.json.bak.

⚠️ RECARREGUE A SESSÃO pro harness aplicar as novas regras:
   1. Ctrl+C
   2. claude (novamente)
```

## STATUS (`status` ou sem args válidos)

Mostre:
```
MODO LIVRE — status no projeto <basename de pwd>

Estado:        <ATIVO desde <timestamp marker> | INATIVO>
Marker:        <thoughts/modo-livre/active existe? sim/não>
Settings:      <.claude/settings.local.json existe? sim/não, tamanho em bytes>
Backup:        <thoughts/modo-livre/settings.local.json.bak existe? sim/não>

Subcomandos:
  /modo-livre on     — ativa (backup + escreve settings novo)
  /modo-livre off    — desativa e restaura backup
  /modo-livre update — reescreve settings com JSON canônico atual (preserva backup)
  /modo-livre status — este resumo
```

## Conflitos a detectar e avisar

- **Já ativo + `on`**: mostre estado e não sobrescreva
- **Não ativo + `off`**: nada a fazer
- **Backup órfão sem marker** (`thoughts/modo-livre/settings.local.json.bak` existe mas `thoughts/modo-livre/active` não): warning — sessão anterior travou? Pergunte se quer restaurar manualmente.
- **Marker sem backup correspondente quando havia settings prévio**: anomalia — pergunte como proceder, não sobrescreva nada.

## JSON canônico

O JSON canônico vive no reference `modo-livre-settings.json` — procure em `.claude/sdd-references/` do projeto, senão em `~/.claude/sdd-references/`. Leia o arquivo e aplique-o integralmente. **Se o reference não existir, PARE e avise o usuário** — nunca invente/reconstrua o JSON de permissões de memória (é segurança).

> **Atenção à sintaxe (se for ler/auditar o reference):** patterns Bash usam **espaço antes do `*`** (`Bash(curl *)`, não `Bash(curl*)`). Conforme docs oficiais: `Bash(npm run *)` "matches commands starting with `npm run`". Pra cobrir comando sem args E com args, inclua as duas formas: `Bash(git status)` E `Bash(git status *)`.

**Observações sobre o pattern matching:**

- **Três camadas — allow amplo + ask no humano + deny cirúrgico**: `Bash(git *)` libera tudo de git; `git commit`/`git push` (formas canônicas) ficam em **`ask`** — promptam SEMPRE, **em qualquer permission mode, inclusive `auto` e `bypassPermissions`** (regra do harness: avaliação é `deny → ask → allow`); e os denies bloqueiam o que nunca pode (`git push --force*`, `reset --hard`, `clean -f *`, variantes exóticas de commit/push). Fonte: [docs de permissions](https://code.claude.com/docs/en/permissions.md) — "Deny rules and explicit ask rules apply in every mode, including bypassPermissions".
- **Por que `ask` e não `deny` pra commit/push**: o toolkit define commit/push como decisão humana. Com deny, até o commit que o usuário acabou de aprovar na conversa (ex: opção 1/2 do fim do `/executor-plan`) era bloqueado pelo harness — fricção sem ganho. Com ask, o harness garante o humano no loop no momento exato, e o fluxo aprovado prossegue com 1 clique. **Force push continua deny** (nunca, nem com prompt). Borda conhecida: `git push origin main --force` (flag no FIM) não casa os denies de force e cai no ask — prompta em vez de bloquear; o humano nega ao ver
- **Auto mode é compatível**: com modo-livre ativo, ligar o permission mode `auto` (Claude Code ≥2.1.83, Sonnet/Opus 4.6+; Shift+Tab após opt-in, ou `claude --permission-mode auto`) zera os prompts de tudo que não é deny/ask — e as cercas deny/ask continuam valendo. Nesse mode o `allow` vira irrelevante (tudo já é aprovado); ele segue importando pro mode `default`/`acceptEdits`
- **Flags posicionais antes do subcomando burlam pattern matching ingênuo** — `Bash(git commit *)` matcha comandos que **começam** com `git commit`, mas NÃO matcha `git -C <path> commit` nem `git --git-dir=<dir> commit`. Por isso os denies cobrem explicitamente todas as variantes:
  - `Bash(git -C * commit)` / `Bash(git -C * commit *)`
  - `Bash(git --git-dir=* commit *)` / `Bash(git --work-tree=* commit *)`
  - Mesma lógica pra `push`, `reset --hard`, `clean -f*`, `checkout --`.
- **Aprendizado de incidente real**: um agente conseguiu burlar `Bash(git commit *)` usando `git -C /worktree/path commit -F /tmp/msg.txt`. Os denies atuais fecham esse vetor. Se aparecer outro flag global posicional (ex: `--literal-pathspecs`, `-c key=val`), adicionar variante correspondente.
- **MCP: allow exige servidor nomeado**: `mcp__*` global é INVÁLIDO em allow (o harness pula a regra e avisa toda sessão) — allow só aceita glob na posição da tool após servidor literal: `mcp__context7__*` ✅, `mcp__*` ❌. Deny/ask aceitam wildcard em qualquer posição. O canônico libera só o `context7` (pré-requisito do toolkit); pra liberar outros MCPs do seu projeto, adicione uma linha `mcp__<server>__*` por servidor no settings local (vão sobreviver ao `/modo-livre update`? NÃO — update sobrescreve; prefira adicioná-los via `/permissions` depois do update, ou aceite o prompt por sessão).
- **Docker conservador**: só leitura (`ps`, `images`, `logs`, `inspect`). `docker exec/rm/rmi/stop/kill/run` continuam pedindo prompt.
- **Publish bloqueado**: `npm/pnpm/yarn/cargo publish` denied pra não publicar pacote por engano.
- **rm bloqueado em formas com flags**: `rm -rf/-fr/-r/-f` denied. `rm arquivo.txt` solto continua pedindo prompt (não tem regra que o pegue).
- **Compound bash bloqueado**: `Bash(*&&*)`, `Bash(*||*)`, `Bash(*;*)` denied. O harness quebra o comando por esses separadores antes de fazer matching, então a deny pode ser redundante na prática — mas serve como sinal explícito + guardrail caso o parser do harness mude. Use **um Bash call por operação** (ver "Como compor comandos Bash" abaixo).

---

## Comportamento esperado enquanto MODO LIVRE estiver ATIVO

Estas regras valem SEMPRE que o agente trabalhar em um projeto com `/modo-livre on` aplicado. Os `deny` do harness são a primeira barreira; estas regras textuais são o segundo guardrail caso algo escape do pattern matching.

### NUNCA faça (sem exceção automática)

Você NUNCA deve executar os comandos abaixo. Se julgar que um deles é necessário, PARE, explique o motivo, e aguarde o usuário digitar autorização EXPLÍCITA na mensagem imediatamente seguinte. "Provavelmente ele quer" NÃO é autorização.

- `git commit` / `git push` **por iniciativa própria** (qualquer variante, incluindo `--amend`). Quando o fluxo de um command prevê commit/push E o usuário escolheu explicitamente (ex: opção 1/2 no fim do `/executor-plan`, push da branch no `/pr-draft`), emita a forma canônica (`git commit ...` / `git push ...`) — o harness vai promptar (regra `ask`) e o usuário confirma. Forma canônica SEMPRE: nunca `-C`/`--git-dir` pra commit/push (são deny e são burla)
- `git push --force` / `--force-with-lease` / `-f` — NUNCA, nem com prompt (deny). Se rebase exigir force push, instrua o usuário a rodar
- `gh pr merge` / `gh pr close` (criar e editar body de PR está liberado)
- `gh release create/delete` / `gh repo delete`
- `git reset --hard` / `git clean -f*` / `git checkout -- <path>`
- `rm` em QUALQUER forma (mesmo `rm arquivo.txt` solto)
- Qualquer comando destrutivo/irreversível que você perceber

NÃO tente burlar via:
- `bash -c`, `eval`, scripts, alias, ou redirecionamento
- Flags globais de `git` (`-C <path>`, `--git-dir=`, `--work-tree=`) — usar `git -C /worktree commit` pra rodar commit em outro dir É burla, mesmo que o pattern matching de allow/deny não pegue. Trate como se fosse `git commit` direto.
- Qualquer outro mecanismo de "rodar comando indireto"

Se o harness barrar algo, NÃO retente com variações — peça pro usuário rodar.

### PODE fazer livremente

- Ler/editar/criar arquivos (Edit, Write, Read)
- Web (WebFetch, WebSearch), MCPs, skills, subagentes
- Git leitura/local: `status`, `diff`, `log`, `show`, `blame`, `branch`, `checkout`, `switch`, `fetch`, `pull`, `stash`, `add`, `restore`, `rebase`, `merge`, `worktree`, `tag`
- gh leitura: `pr/issue view/list`, `pr diff/checks`, `repo view`, `api`, `run view`
- gh escrita não-destrutiva: `gh pr create` (abrir PR), `gh pr edit` (atualizar title/body/labels)
- Testes, builds, linters, install de deps (npm/pnpm/yarn/pip/uv/cargo/go/make)
- `cp`/`mv`/`mkdir`/`touch` dentro do projeto

### Comportamento

- Não pause a cada passo — trabalhe até terminar um bloco coeso
- TaskCreate pra planejar tarefas não-triviais
- Ao terminar um bloco: mostre `git status` + `git diff` e pergunte se pode commitar
- Se o harness negar algo, responda direto e siga — NÃO retente

### Como compor comandos Bash (importante)

O harness quebra comandos por `&&`, `||`, `;`, `|`, `&`, `|&` E **newlines**. Cada subcomando precisa casar uma regra independente. Padrões anti-pattern que rebentam o pattern matching:

❌ Newlines no meio de comandos compostos:
```bash
ls X 2>&1 || mkdir -p
   X && echo "ok"
```
(O parser quebra na newline e fica com `mkdir -p` solto sem args, que não casa `Bash(mkdir *)`.)

❌ Defensividade excessiva com chains:
```bash
test -d X || mkdir -p X && echo "ok"
```
(`mkdir -p` já é idempotente — não erra se X existe.)

✅ Comando único idempotente:
```bash
mkdir -p X
```

✅ Compostos numa linha só, sem newline:
```bash
git status && git diff --stat
```

❌ Subshells `(...)` sem necessidade:
```bash
(bun run typecheck 2>&1 | tail -15 && echo "---" && bunx vitest run)
```
(O parêntese de abertura confunde o pattern matching — `(bun` não casa `Bash(bun *)`.)

✅ Sem parênteses, em uma linha:
```bash
bun run typecheck 2>&1 | tail -15 && echo "---" && bunx vitest run
```

Regra prática: prefira **um Bash call por operação**. Se precisar combinar, fique em UMA LINHA, SEM parênteses, e garanta que cada subcomando tem regra de allow. Idempotência (mkdir -p, touch, cp -n) elimina a necessidade de chains "check-then-act".

### Paths: prefira RELATIVOS dentro do projeto

Quando o comando opera dentro do `cwd` (worktree ou repo principal), use paths **relativos**, NÃO absolutos:

❌ Path absoluto fora ou ambíguo em relação ao cwd:
```bash
find /home/user/codigos/org/projeto/apps/api/test -name "*.ts"
```
(Mesmo que o path absoluto seja válido, o harness pode pedir "allow reading from `test/` and `src/`" porque detecta paths externos ao cwd — especialmente em worktrees onde o cwd é diferente do repo principal.)

✅ Path relativo ao cwd:
```bash
find apps/api/test -name "*.ts"
```

Exceções legítimas pra path absoluto:
- `~/.claude/`, `~/.config/`, `/tmp/`, etc. (paths do sistema/usuário fora do projeto)
- Quando explicitamente cruzando projetos (ex: copiar arquivo do toolkit pra um projeto-alvo)
- Quando o cwd é completamente diferente (executando script de outro lugar)

**Worktrees:** se o cwd é uma worktree (ex: `~/codigos/org/projeto-feature/`) e você precisa ler arquivos do repo principal (`~/codigos/org/projeto/`), o user deve startar a sessão com `claude --add-dir /caminho/do/repo/principal`. Sem isso, o harness vai pedir prompt de "additional directory" pra cada acesso.
