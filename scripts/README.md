# `ouvir` — ouça a última resposta do Claude Code em voz alta

Um comando de terminal que lê **a última resposta do Claude Code na sessão atual** e fala em voz alta. Por padrão usa TTS **local** em pt-BR (sem nuvem, sem custo, sem enviar nada pra fora); opcionalmente pode usar provedores **cloud** (MiniMax, Groq) pra voz mais natural.

Útil pra acompanhar uma resposta longa enquanto você olha pra outra coisa, ou por acessibilidade.

> É um **extra** do toolkit (não um slash command). Instalação opt-in e isolada em `~/.local` — não precisa de `sudo`.

---

## Como funciona

1. Descobre a pasta da sessão a partir do diretório atual (o Claude Code troca `/` por `-` no caminho — `/home/voce/meu-projeto` vira `-home-voce-meu-projeto`).
2. Identifica **a sessão daquela aba** (ver "Qual sessão é lida" abaixo) e localiza o transcript `.jsonl` correspondente **em todas as instalações** `~/.claude*/projects/` (cobre instalações múltiplas ou com nome customizado).
3. Lê a última mensagem do assistente que seja `type=="assistant"`, **não** seja de subagente (`isSidechain` falso/ausente) e tenha texto de fato (pula mensagens que são só chamada de ferramenta).
4. Remove a marcação Markdown (negrito, headers, blocos de código, links…) pra não soletrar símbolos.
5. Sintetiza pelo **engine** escolhido, com fallback em cascata (ver abaixo).

Sem dependências além do **Python 3** (já vem no sistema) e de um **player de áudio** (`pw-play`/`paplay`/`aplay`, presentes por padrão em Pop!_OS/Ubuntu).

---

## Qual sessão é lida (várias abas)

Se você tem **várias abas abertas no mesmo projeto**, cada uma é uma sessão diferente do Claude Code (transcripts `.jsonl` distintos na mesma pasta). Pra não ler a resposta da aba errada, o `ouvir`:

- **Crava a sessão da aba** quando é rodado de dentro dela — ele herda a variável `CLAUDE_CODE_SESSION_ID` (que o Claude Code exporta) e lê exatamente aquele transcript. **Por isso, com múltiplas abas, dispare com `!ouvir`** (dentro da sessão): assim ele pega a sessão certa.
- **Cai pro mais recente** do diretório só quando roda em terminal puro (sem sessão associada).
- **Override manual**: `ouvir --session <id>` ou `OUVIR_SESSION_ID=<id> ouvir` força uma sessão específica.
- **Parar o áudio**: num terminal real, enquanto a fala toca, **`Esc`, `q` ou `Ctrl+C`** interrompem. De outra aba (ou quando não está em foreground), `ouvir --stop` mata só o áudio **desta** sessão (cada aba para o seu, via pidfile por sessão).

## Engines e fallback

O `ouvir` suporta vários engines de TTS e tenta um após o outro. **A cadeia sempre termina nos engines locais (piper → espeak)** — então se um provedor cloud falhar (key expirada, rate limit, mudança de plano, rede fora), o `ouvir` continua falando localmente. Você nunca fica mudo por causa de token.

| Engine | Tipo | Idioma | Precisa |
|---|---|---|---|
| `piper` | local | pt-BR (voz natural) | binário piper + modelo `.onnx` |
| `espeak` | local | pt-BR (robótico) | `espeak-ng` |
| `minimax` | **cloud** | pt-BR ✅ (40+ idiomas) | `MINIMAX_API_KEY` + `voice_id` |
| `groq` | **cloud** | **EN/AR só** (hoje) | `GROQ_API_KEY` |

Escolha com a variável `OUVIR_ENGINE`:

```bash
ouvir                          # default: auto = piper, espeak (100% local)
OUVIR_ENGINE=minimax ouvir     # MiniMax (pt-BR), com fallback local automático
OUVIR_ENGINE=groq ouvir        # Groq (EN/AR), com fallback local automático
OUVIR_ENGINE="minimax,piper" ouvir   # ordem exata que você quiser
```

> **Privacidade:** engines cloud **enviam o texto da resposta** pro provedor (pode conter trecho de código/contexto). Por isso o default é **local** e o cloud só é usado quando você pede explicitamente em `OUVIR_ENGINE`. Para fixar uma preferência, exporte a variável no seu `~/.zshrc`.

### MiniMax (recomendado pra pt-BR cloud)

[Docs](https://platform.minimax.io/docs/api-reference/speech-t2a-http). Precisa de uma API key, um `voice_id` da sua conta e (em algumas contas) o Group ID:

```bash
export MINIMAX_API_KEY="sk-..."
export OUVIR_MINIMAX_VOICE="<voice_id da sua conta>"   # obrigatório
export MINIMAX_GROUP_ID="..."                          # se sua conta exigir
# opcionais:
export OUVIR_MINIMAX_MODEL="speech-02-turbo"           # ou speech-02-hd
export OUVIR_MINIMAX_BASE="https://api.minimax.io/v1/t2a_v2"
OUVIR_ENGINE=minimax ouvir
```

### Groq (rápido/barato, mas EN/AR)

[Docs](https://console.groq.com/docs/text-to-speech). Hoje as vozes são só inglês e árabe — pra pt-BR a fonética sai errada. Útil pra ouvir respostas em inglês:

```bash
export GROQ_API_KEY="gsk_..."
export OUVIR_GROQ_VOICE="Fritz-PlayAI"   # opcional
OUVIR_ENGINE=groq ouvir
```

> As chaves vão **sempre** em variáveis de ambiente, nunca no repositório.

---

## Instalação rápida (recomendada)

Do diretório do toolkit:

```bash
./scripts/install-ouvir.sh
```

Instala, **sem sudo**, em `~/.local`: o comando `ouvir`, o binário **piper** e o modelo de voz **pt_BR-faber-medium**. (Os engines cloud não precisam de instalação — só das variáveis de ambiente acima.)

Se `~/.local/bin` não estiver no `PATH`, o instalador avisa — adicione ao `~/.zshrc`/`~/.bashrc`:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Depois, dentro de **qualquer projeto com sessão ativa do Claude Code**:

```bash
ouvir              # menu interativo (↑/↓ + Enter) pra escolher qual resposta ouvir
ouvir -l           # fala a última resposta (last)
ouvir 3            # fala a 3ª resposta de trás pra frente (1 = última)
ouvir --grep métricas   # fala a resposta mais recente que menciona "métricas"
ouvir --stop       # para o áudio que está tocando nesta sessão (Ctrl+C também para)
ouvir --text-only  # só imprime o texto que seria falado (debug, sem áudio)
!ouvir             # de dentro de uma sessão do Claude Code (o prefixo ! roda shell)
```

---

## Escolher qual parte da conversa ouvir

Rodando `ouvir` **num terminal real**, você cai num **menu interativo**: `↑`/`↓`
(ou `j`/`k`) navegam, `Enter` toca a resposta selecionada, `q` (ou `Esc`) cancela.
A lista mostra 1 = mais recente, com hora + um trecho de cada resposta.

```bash
ouvir               # menu interativo (default)
ouvir -l            # atalho: fala a última, sem abrir o menu
ouvir 5             # fala a 5ª de trás pra frente
ouvir --grep weave  # fala a mais recente que fala de "weave"
ouvir --list 30     # imprime a lista numerada (sem menu), olhando mais fundo
```

**Via `!ouvir` dentro do Claude Code não há terminal interativo** (o stdin não é
um TTY), então o menu **cai automaticamente pra lista numerada** — aí você escolhe
com `!ouvir <N>`. O `--grep` é o caminho quando você lembra **do assunto** mas não
do número. Só respostas do assistente principal entram na lista (sub-agentes são
ignorados).

---

## Instalação manual

<details>
<summary>Passo a passo, se preferir não usar o instalador</summary>

```bash
# 1. o script
install -m 0755 scripts/ouvir ~/.local/bin/ouvir

# 2. piper (binário Linux x86_64; veja github.com/rhasspy/piper/releases p/ outras arquiteturas)
mkdir -p ~/.local/share/piper-bin ~/.local/share/piper
curl -fsSL -o /tmp/piper.tar.gz \
  https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_linux_x86_64.tar.gz
tar -xzf /tmp/piper.tar.gz -C ~/.local/share/piper-bin
printf '#!/bin/sh\nexec "$HOME/.local/share/piper-bin/piper/piper" "$@"\n' > ~/.local/bin/piper
chmod +x ~/.local/bin/piper

# 3. modelo de voz pt-BR
BASE=https://huggingface.co/rhasspy/piper-voices/resolve/main/pt/pt_BR/faber/medium
curl -fsSL -o ~/.local/share/piper/pt_BR-faber-medium.onnx      "$BASE/pt_BR-faber-medium.onnx"
curl -fsSL -o ~/.local/share/piper/pt_BR-faber-medium.onnx.json "$BASE/pt_BR-faber-medium.onnx.json"
```

</details>

### Fallback sem piper: espeak-ng

```bash
sudo apt install espeak-ng     # única etapa que pede sudo
```

---

## Trocar a voz do piper

Modelo padrão: `pt_BR-faber-medium`. Outras vozes pt-BR em
[rhasspy/piper-voices](https://huggingface.co/rhasspy/piper-voices/tree/main/pt/pt_BR).
Baixe o `.onnx` + `.onnx.json` pra `~/.local/share/piper/` e aponte com `OUVIR_PIPER_MODEL`.

---

## Configuração (variáveis de ambiente)

| Variável | Default | Pra quê |
|---|---|---|
| `OUVIR_ENGINE` | `auto` (= `piper,espeak`) | Ordem dos engines (locais sempre anexados no fim) |
| `OUVIR_CLAUDE_GLOB` | `~/.claude*` | Onde procurar as instalações/transcripts |
| `OUVIR_SESSION_ID` | `$CLAUDE_CODE_SESSION_ID` | Força a sessão a ler (senão usa a da aba; ou `--session <id>`) |
| `OUVIR_PIPER_MODEL` | `~/.local/share/piper/pt_BR-faber-medium.onnx` | Modelo do piper |
| `OUVIR_ESPEAK_VOICE` | `pt-br` | Voz do espeak-ng |
| `OUVIR_RESPELL` | `on` | Reescrita de termos EN pra grafia falável em pt-BR. `off` desliga |
| `OUVIR_PRON_FILE` | `~/.config/ouvir/pronuncias.tsv` | Dicionário de pronúncia do usuário (override/extensão dos defaults) |
| `OUVIR_DRY_RUN` | — | Se setada, só imprime o texto (igual `--text-only`) |
| `MINIMAX_API_KEY` | — | Ativa o engine `minimax` |
| `OUVIR_MINIMAX_VOICE` | — | `voice_id` da sua conta MiniMax (obrigatório p/ minimax) |
| `MINIMAX_GROUP_ID` | — | Group ID, se sua conta exigir |
| `OUVIR_MINIMAX_MODEL` | `speech-02-turbo` | Modelo MiniMax |
| `OUVIR_MINIMAX_BASE` | `https://api.minimax.io/v1/t2a_v2` | Endpoint MiniMax |
| `GROQ_API_KEY` | — | Ativa o engine `groq` |
| `OUVIR_GROQ_VOICE` | `Fritz-PlayAI` | Voz do Groq |
| `OUVIR_GROQ_MODEL` | `playai-tts` | Modelo do Groq |

---

## Pronúncia de termos em inglês (respelling)

Os engines pt-BR (piper/minimax) leem termos técnicos em inglês com fonética
portuguesa — "deploy" vira "dê-plói", "cache" vira "cachê", "merge" vira "mergе",
"shopify" vira "shopifí". Antes de falar, o `ouvir` reescreve esses termos numa
grafia que o modelo pt-BR fala como o dev BR pronuncia. Vale pra **todos** os
engines (piper, espeak, minimax), porque acontece no texto, antes do TTS.

Já vem com um dicionário embutido (deploy, commit, merge, branch, pull request,
cache, endpoint, backend, PR, API, CI/CD, shopify, checkout, gateway, …). Pra
**calibrar ou estender** sem tocar no script, crie seu arquivo:

```bash
mkdir -p ~/.config/ouvir
cp scripts/ouvir-pronuncias.example.tsv ~/.config/ouvir/pronuncias.tsv
# edite ouvindo — a grafia certa é a que soa bem na SUA voz
```

Formato: uma linha `termo<TAB>grafia` (também aceita `termo = grafia` / `termo -> grafia`).
`#` comenta. Um `termo` sozinho (sem grafia) **remove** um default embutido. Termos
multi-palavra têm prioridade; plurais são entradas separadas.

Pra conferir o que **será falado** sem tocar áudio, use `ouvir --text-only`.
Pra desligar tudo: `export OUVIR_RESPELL=off`.

---

## Limitações

- Lê **uma** resposta (a última). Não acompanha streaming ao vivo.
- O strip de Markdown é pragmático — blocos de código são removidos (não lidos).
- Binários piper pré-compilados: Linux x86_64/aarch64/armv7l. Em macOS/Windows, use espeak-ng/cloud ou veja o repo do piper.
- **Engines cloud (groq/minimax) não foram testados ponta-a-ponta** neste repositório (precisam de API key). A implementação segue as docs oficiais; se algo divergir com a sua conta, é fácil ajustar (ex.: formato de áudio do MiniMax). Áudio `mp3` (MiniMax) exige um player de mp3 (`ffplay`/`mpv`/`mpg123`); sem ele, o `ouvir` cai pro piper.

---

## Privacidade

Por padrão tudo é **local**: o transcript já está no seu disco e o piper/espeak rodam na sua máquina. O script só lê arquivos dentro de `~/.claude*/` e nunca escreve neles. Engines cloud são **opt-in** e enviam apenas o texto da resposta ao provedor que você configurar.
