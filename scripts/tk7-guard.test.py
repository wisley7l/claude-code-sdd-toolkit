import json
import pathlib
import subprocess
import sys

GUARD = str(pathlib.Path(__file__).resolve().with_name("tk7-guard"))

BLOQUEIA = [
    ("o comando do incidente", "gh api repos/OWNER/REPO/pulls/427/merge-async -X PUT -f merge_method=merge"),
    ("gh pr merge", "gh pr merge 427 --merge"),
    ("api merge simples", "gh api repos/o/r/pulls/1/merge -X PUT"),
    ("metodo antes do path", "gh api -X PUT repos/o/r/pulls/1/merge"),
    ("--method=PUT", "gh api --method=PUT repos/o/r/pulls/1/merge"),
    ("-XPUT colado", "gh api repos/o/r/pulls/1/merge -XPUT"),
    ("delete via api", "gh api repos/o/r/releases/9 -X DELETE"),
    ("branch protection", "gh api repos/o/r/branches/main/protection -X PUT --input p.json"),
    ("push --force", "git push --force origin main"),
    ("push -f", "git push -f"),
    ("push refspec +", "git push origin +main:main"),
    ("push -C com force", "git -C /tmp/x push --force"),
    ("escondido em composto", "npm test && gh pr merge 427"),
    ("repo delete", "gh repo delete o/r --yes"),
]

PASSA = [
    ("leitura de PR", "gh pr view 427 --json state,mergedAt"),
    ("comentarios via api", "gh api repos/o/r/pulls/427/comments"),
    ("api com POST inofensivo", "gh api repos/o/r/issues/77/comments -X POST -f body=oi"),
    ("criar PR", "gh pr create --fill"),
    ("push normal", "git push origin feat/x"),
    ("push -u", "git push -u origin feat/x"),
    ("commit", 'git commit -m "feat: x"'),
    ("merge local", "git merge origin/staging"),
    ("roadmap", "roadmap move 004 --to concluido --pr 427"),
    ("grep na palavra merge", "grep -rn merge skills/"),
    ("ls", "ls -la"),
    ("rebase de worktree", "git -C .worktrees/feat-b rebase feat/a"),
]


def roda(comando):
    entrada = json.dumps({"tool_name": "Bash", "tool_input": {"command": comando}})
    p = subprocess.run([GUARD], input=entrada, capture_output=True, text=True)
    return p.returncode, p.stderr.strip()


falhas = 0
print("--- deve BLOQUEAR (exit 2) ---")
for nome, cmd in BLOQUEIA:
    rc, _ = roda(cmd)
    ok = rc == 2
    falhas += 0 if ok else 1
    print(f"  {'ok  ' if ok else 'FALHA'} exit={rc}  {nome}")
print("--- deve PASSAR (exit 0) ---")
for nome, cmd in PASSA:
    rc, err = roda(cmd)
    ok = rc == 0
    falhas += 0 if ok else 1
    print(f"  {'ok  ' if ok else 'FALHA'} exit={rc}  {nome}" + (f"  <- {err.splitlines()[0]}" if not ok and err else ""))
print(f"\n{falhas} falha(s)")
sys.exit(1 if falhas else 0)
