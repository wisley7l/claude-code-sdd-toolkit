---
description: MODO LIVRE — toggle do modo autônomo. `on` instala settings com allow amplo + deny dos perigosos. `off` restaura backup. `update` reescreve settings com JSON canônico atual (sem mexer no backup). NUNCA commita/pusha/rm sem autorização explícita.
argument-hint: [on|off|update|status]
---

# /modo-livre

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

**3.** Escreva `.claude/settings.local.json` com o conteúdo da seção [JSON canônico](#json-canônico) abaixo.

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

As regras NUNCA (commit/push/rm/etc) continuam valendo —
elas são guardrail comportamental, não só do harness.
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

**3.** Sobrescreva `.claude/settings.local.json` com o conteúdo da seção [JSON canônico](#json-canônico).

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

Este é o conteúdo exato pra escrever em `.claude/settings.local.json` no `on`:

> **Atenção à sintaxe:** patterns Bash usam **espaço antes do `*`** (`Bash(curl *)`, não `Bash(curl*)`). Conforme docs oficiais: `Bash(npm run *)` "matches commands starting with `npm run`". Pra cobrir comando sem args E com args, inclua as duas formas: `Bash(git status)` E `Bash(git status *)`.

```json
{
  "permissions": {
    "defaultMode": "acceptEdits",
    "allow": [
      "Edit",
      "Write",
      "Read",
      "WebFetch",
      "WebSearch",
      "Agent",
      "Skill",
      "Bash(git *)",
      "Bash(gh *)",
      "Bash(ls)",
      "Bash(ls *)",
      "Bash(pwd)",
      "Bash(cd *)",
      "Bash(cat *)",
      "Bash(rg *)",
      "Bash(grep *)",
      "Bash(find *)",
      "Bash(fd *)",
      "Bash(tree)",
      "Bash(tree *)",
      "Bash(echo *)",
      "Bash(printf *)",
      "Bash(which *)",
      "Bash(whereis *)",
      "Bash(file *)",
      "Bash(stat *)",
      "Bash(wc *)",
      "Bash(head *)",
      "Bash(tail *)",
      "Bash(sort *)",
      "Bash(uniq *)",
      "Bash(cut *)",
      "Bash(tr *)",
      "Bash(node *)",
      "Bash(npm *)",
      "Bash(pnpm *)",
      "Bash(yarn *)",
      "Bash(npx *)",
      "Bash(bun *)",
      "Bash(deno *)",
      "Bash(python *)",
      "Bash(python3 *)",
      "Bash(pip *)",
      "Bash(pip3 *)",
      "Bash(pipx *)",
      "Bash(uv *)",
      "Bash(pytest *)",
      "Bash(go *)",
      "Bash(cargo *)",
      "Bash(rustc *)",
      "Bash(make *)",
      "Bash(just *)",
      "Bash(docker ps)",
      "Bash(docker ps *)",
      "Bash(docker images)",
      "Bash(docker images *)",
      "Bash(docker logs *)",
      "Bash(docker inspect *)",
      "Bash(curl *)",
      "Bash(wget *)",
      "Bash(jq *)",
      "Bash(yq *)",
      "Bash(mkdir *)",
      "Bash(touch *)",
      "Bash(cp *)",
      "Bash(mv *)",
      "Bash(ln *)",
      "Bash(diff *)",
      "Bash(date)",
      "Bash(date *)",
      "Bash(env)",
      "Bash(env *)",
      "Bash(true)",
      "Bash(false)",
      "mcp__*"
    ],
    "deny": [
      "Bash(git commit)",
      "Bash(git commit *)",
      "Bash(git push)",
      "Bash(git push *)",
      "Bash(git reset --hard)",
      "Bash(git reset --hard *)",
      "Bash(git clean -f *)",
      "Bash(git clean -d *)",
      "Bash(git clean -x *)",
      "Bash(git clean -fd *)",
      "Bash(git clean -fdx *)",
      "Bash(git checkout -- *)",
      "Bash(gh pr create)",
      "Bash(gh pr create *)",
      "Bash(gh pr merge)",
      "Bash(gh pr merge *)",
      "Bash(gh pr close *)",
      "Bash(gh pr edit *)",
      "Bash(gh release create *)",
      "Bash(gh release delete *)",
      "Bash(gh repo delete *)",
      "Bash(rm -rf *)",
      "Bash(rm -fr *)",
      "Bash(rm -r *)",
      "Bash(rm -f *)",
      "Bash(npm publish)",
      "Bash(npm publish *)",
      "Bash(pnpm publish)",
      "Bash(pnpm publish *)",
      "Bash(yarn publish)",
      "Bash(yarn publish *)",
      "Bash(cargo publish)",
      "Bash(cargo publish *)"
    ]
  }
}
```

**Observações sobre o pattern matching:**

- **Allow amplo + deny cirúrgico** pra `git` e `gh`: `Bash(git *)` libera tudo de git, mas os denies (`git commit`, `git push`, `git reset --hard`, `git clean -f *`) bloqueiam o que não pode. Deny tem precedência sobre allow.
- **Docker conservador**: só leitura (`ps`, `images`, `logs`, `inspect`). `docker exec/rm/rmi/stop/kill/run` continuam pedindo prompt.
- **Publish bloqueado**: `npm/pnpm/yarn/cargo publish` denied pra não publicar pacote por engano.
- **rm bloqueado em formas com flags**: `rm -rf/-fr/-r/-f` denied. `rm arquivo.txt` solto continua pedindo prompt (não tem regra que o pegue).

---

## Comportamento esperado enquanto MODO LIVRE estiver ATIVO

Estas regras valem SEMPRE que o agente trabalhar em um projeto com `/modo-livre on` aplicado. Os `deny` do harness são a primeira barreira; estas regras textuais são o segundo guardrail caso algo escape do pattern matching.

### NUNCA faça (sem exceção automática)

Você NUNCA deve executar os comandos abaixo. Se julgar que um deles é necessário, PARE, explique o motivo, e aguarde o usuário digitar autorização EXPLÍCITA na mensagem imediatamente seguinte. "Provavelmente ele quer" NÃO é autorização.

- `git commit` (qualquer variante, incluindo `--amend`)
- `git push` (qualquer variante: `--force`, `--force-with-lease`, `-f`)
- `gh pr create` / `gh pr merge` / `gh pr close` / `gh pr edit`
- `gh release create/delete` / `gh repo delete`
- `git reset --hard` / `git clean -f*` / `git checkout -- <path>`
- `rm` em QUALQUER forma (mesmo `rm arquivo.txt` solto)
- Qualquer comando destrutivo/irreversível que você perceber

NÃO tente burlar via `bash -c`, `eval`, scripts, alias, ou redirecionamento. Se o harness barrar algo, NÃO retente com variações — peça pro usuário rodar.

### PODE fazer livremente

- Ler/editar/criar arquivos (Edit, Write, Read)
- Web (WebFetch, WebSearch), MCPs, skills, subagentes
- Git leitura/local: `status`, `diff`, `log`, `show`, `blame`, `branch`, `checkout`, `switch`, `fetch`, `pull`, `stash`, `add`, `restore`, `rebase`, `merge`, `worktree`, `tag`
- gh leitura: `pr/issue view/list`, `pr diff/checks`, `repo view`, `api`, `run view`
- Testes, builds, linters, install de deps (npm/pnpm/yarn/pip/uv/cargo/go/make)
- `cp`/`mv`/`mkdir`/`touch` dentro do projeto

### Comportamento

- Não pause a cada passo — trabalhe até terminar um bloco coeso
- TaskCreate pra planejar tarefas não-triviais
- Ao terminar um bloco: mostre `git status` + `git diff` e pergunte se pode commitar
- Se o harness negar algo, responda direto e siga — NÃO retente
