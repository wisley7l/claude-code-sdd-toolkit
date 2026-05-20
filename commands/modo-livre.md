---
description: MODO LIVRE — toggle do modo autônomo. `on` instala settings com allow amplo + deny dos perigosos. `off` restaura backup. NUNCA commita/pusha/rm sem autorização explícita.
argument-hint: [on|off|status]
---

# /modo-livre

Você está implementando o toggle do MODO LIVRE para o projeto **na pasta atual**.

Parseie `$ARGUMENTS` (case-insensitive, trim espaços):

- `on`, `ativar`, `ativa`, `enable`, ou vazio → **ATIVAR**
- `off`, `desativar`, `desativa`, `disable` → **DESATIVAR**
- `status`, `estado`, `state` → **STATUS**
- qualquer outra coisa → mostre status + lista de subcomandos

## Pré-cheques (toda invocação)

1. Confirme `pwd` — você está na raiz do projeto onde o modo será aplicado
2. Se `.claude/` não existe e o subcomando é `on`, crie com `mkdir -p .claude`
3. Marker file: `.claude/.modo-livre-active`
4. Backup file: `.claude/settings.local.json.bak-modo-livre`
5. Settings file: `.claude/settings.local.json`

## ATIVAR (`on`)

**1.** Se `.claude/.modo-livre-active` JÁ existe → mostre:
```
Modo livre já está ATIVO desde <timestamp do marker>.
Use `/modo-livre off` para desativar.
```
e pare.

**2.** Se `.claude/settings.local.json` existe → faça backup:
```bash
cp .claude/settings.local.json .claude/settings.local.json.bak-modo-livre
```
Se NÃO existe → não faça backup (não havia config anterior).

**3.** Escreva `.claude/settings.local.json` com o conteúdo da seção [JSON canônico](#json-canônico) abaixo.

**4.** Crie o marker com timestamp ISO 8601:
```bash
date -Iseconds > .claude/.modo-livre-active
```

**5.** Cheque `.gitignore`:
- Adicione `.claude/settings.local.json` se não estiver (geralmente já está)
- Adicione `.claude/.modo-livre-active`
- Adicione `.claude/settings.local.json.bak-modo-livre`

Use `grep -F` pra checar antes de adicionar — não duplique.

**6.** Avise ao usuário:
```
✅ MODO LIVRE ATIVADO
Marker: .claude/.modo-livre-active (<timestamp>)
Backup: <"presente em .claude/settings.local.json.bak-modo-livre" OU "nenhum (sem config anterior)">

⚠️ RECARREGUE A SESSÃO pro harness aplicar:
   1. Ctrl+C
   2. claude (novamente, na mesma pasta)

As regras NUNCA (commit/push/rm/etc) continuam valendo —
elas são guardrail comportamental, não só do harness.
```

## DESATIVAR (`off`)

**1.** Se `.claude/.modo-livre-active` NÃO existe → mostre:
```
Modo livre não está ativo. Nada a desativar.
```
e pare.

**2.** Restaurar settings:
- Se `.claude/settings.local.json.bak-modo-livre` existe → `mv` ele de volta:
  ```bash
  mv .claude/settings.local.json.bak-modo-livre .claude/settings.local.json
  ```
- Se NÃO existe (não havia config antes) → `rm .claude/settings.local.json`

**3.** Remova o marker:
```bash
rm .claude/.modo-livre-active
```

**4.** Se `.claude/` ficou vazio → `rmdir .claude` (tentativa, ignore erro se não vazio).

**5.** Avise:
```
✅ MODO LIVRE DESATIVADO
Settings restaurado: <"backup aplicado" OU "removido (não havia anterior)">

⚠️ RECARREGUE A SESSÃO pro harness aplicar:
   1. Ctrl+C
   2. claude (novamente)
```

## STATUS (`status` ou sem args válidos)

Mostre:
```
MODO LIVRE — status no projeto <basename de pwd>

Estado:        <ATIVO desde <timestamp marker> | INATIVO>
Marker:        <.claude/.modo-livre-active existe? sim/não>
Settings:      <.claude/settings.local.json existe? sim/não, tamanho em bytes>
Backup:        <.claude/settings.local.json.bak-modo-livre existe? sim/não>
.gitignore:    <todos os 3 paths listados? sim/parcial/não>

Subcomandos:
  /modo-livre on     — ativa
  /modo-livre off    — desativa e restaura backup
  /modo-livre status — este resumo
```

## Conflitos a detectar e avisar

- **Já ativo + `on`**: mostre estado e não sobrescreva
- **Não ativo + `off`**: nada a fazer
- **Backup órfão sem marker** (`.bak-modo-livre` existe mas `.modo-livre-active` não): warning — sessão anterior travou? Pergunte se quer restaurar manualmente.
- **Marker sem backup correspondente quando havia settings prévio**: anomalia — pergunte como proceder, não sobrescreva nada.

## JSON canônico

Este é o conteúdo exato pra escrever em `.claude/settings.local.json` no `on`:

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
      "Bash(git status*)",
      "Bash(git diff*)",
      "Bash(git log*)",
      "Bash(git show*)",
      "Bash(git blame*)",
      "Bash(git branch*)",
      "Bash(git checkout*)",
      "Bash(git switch*)",
      "Bash(git fetch*)",
      "Bash(git pull*)",
      "Bash(git stash*)",
      "Bash(git add*)",
      "Bash(git restore*)",
      "Bash(git rebase*)",
      "Bash(git merge*)",
      "Bash(git worktree*)",
      "Bash(git remote*)",
      "Bash(git tag*)",
      "Bash(git config --get*)",
      "Bash(git config --list*)",
      "Bash(gh pr view*)",
      "Bash(gh pr list*)",
      "Bash(gh pr diff*)",
      "Bash(gh pr checks*)",
      "Bash(gh pr status*)",
      "Bash(gh issue view*)",
      "Bash(gh issue list*)",
      "Bash(gh issue status*)",
      "Bash(gh repo view*)",
      "Bash(gh api*)",
      "Bash(gh auth status*)",
      "Bash(gh run view*)",
      "Bash(gh run list*)",
      "Bash(gh search*)",
      "Bash(gh label list*)",
      "Bash(ls*)",
      "Bash(pwd)",
      "Bash(cd *)",
      "Bash(echo*)",
      "Bash(printf*)",
      "Bash(which*)",
      "Bash(whereis*)",
      "Bash(file*)",
      "Bash(stat*)",
      "Bash(wc*)",
      "Bash(head*)",
      "Bash(tail*)",
      "Bash(sort*)",
      "Bash(uniq*)",
      "Bash(cut*)",
      "Bash(tr*)",
      "Bash(cat*)",
      "Bash(rg*)",
      "Bash(grep*)",
      "Bash(find*)",
      "Bash(fd*)",
      "Bash(tree*)",
      "Bash(node*)",
      "Bash(npm*)",
      "Bash(pnpm*)",
      "Bash(yarn*)",
      "Bash(npx*)",
      "Bash(bun*)",
      "Bash(deno*)",
      "Bash(python*)",
      "Bash(python3*)",
      "Bash(pip*)",
      "Bash(pip3*)",
      "Bash(pipx*)",
      "Bash(uv*)",
      "Bash(pytest*)",
      "Bash(go *)",
      "Bash(cargo*)",
      "Bash(rustc*)",
      "Bash(make*)",
      "Bash(just*)",
      "Bash(docker ps*)",
      "Bash(docker images*)",
      "Bash(docker logs*)",
      "Bash(curl*)",
      "Bash(wget*)",
      "Bash(jq*)",
      "Bash(yq*)",
      "Bash(mkdir*)",
      "Bash(touch*)",
      "Bash(cp *)",
      "Bash(mv *)",
      "Bash(ln*)",
      "Bash(diff*)",
      "Bash(date*)",
      "Bash(env*)",
      "Bash(true)",
      "Bash(false)",
      "mcp__*"
    ],
    "deny": [
      "Bash(git commit*)",
      "Bash(git push*)",
      "Bash(git reset --hard*)",
      "Bash(git clean -f*)",
      "Bash(git clean -d*)",
      "Bash(git clean -x*)",
      "Bash(git checkout -- *)",
      "Bash(gh pr create*)",
      "Bash(gh pr merge*)",
      "Bash(gh pr close*)",
      "Bash(gh pr edit*)",
      "Bash(gh release create*)",
      "Bash(gh release delete*)",
      "Bash(gh repo delete*)",
      "Bash(rm -rf*)",
      "Bash(rm -fr*)",
      "Bash(rm -r*)",
      "Bash(rm -f*)"
    ]
  }
}
```

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
