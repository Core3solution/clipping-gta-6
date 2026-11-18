# Operar com o PC desligado

Há três caminhos, em ordem de prioridade. **Nenhum está validado ainda.** A operação na nuvem só será considerada funcional depois de um teste completo com o seu PC desligado.

## A. Claude Code na nuvem (prioridade, custo zero com o Max)

**Como funciona:** uma **rotina** do Claude Code roda `/clip-br` de hora em hora na nuvem da Anthropic. Cada execução começa de um clone novo do repositório:

1. instala as dependências (script de setup, em cache);
2. lê o Telegram;
3. baixa os blocos novos dos VODs da Twitch (`vods fetch`);
4. faz a curadoria e renderiza;
5. envia no Telegram;
6. faz commit de `state/`, para a próxima execução saber até onde já foi.

**Limites conhecidos (documentação, a confirmar na sua conta):**
- intervalo mínimo de 1 hora;
- teto diário de execuções (15 por dia no Max no lançamento das rotinas);
- o mesmo limite de uso da assinatura do chat e do Claude Code;
- sem GPU;
- disco apagado entre execuções;
- o YouTube costuma bloquear downloads de IP de datacenter. Use Twitch na nuvem e YouTube no PC.

### Passo a passo do teste (com o PC ligado, para acompanhar)

1. Suba este branch para o seu fork no GitHub.
2. Em claude.ai/code, crie um **ambiente** "gta-br":
   - **Rede:** *Full* para o primeiro teste. Depois troque para *Custom* com: `pypi.org`, `files.pythonhosted.org`, `huggingface.co`, `*.hf.co`, `*.twitch.tv`, `*.ttvnw.net`, `*.cloudfront.net`, `api.telegram.org`.
   - **Variáveis de ambiente:** `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `CLIPPER_PROFILE=gta-br`, `CLIPPER_TOP_HOOKS=1` e `CLIPPER_SKIP_VERIFY=1` (rodadas de produção não precisam rodar a suíte de testes a cada parada).
   - **Script de setup:** o conteúdo de `scripts/cloud-setup.sh`.
3. Abra uma sessão nesse ambiente, com o seu fork, e peça:
   > Rode `python3 -m unittest discover -s tests`, depois `python3 -m clipper vods fetch --max-chunks 1` e me diga quanto tempo levou cada etapa (download, transcrição). Depois rode `/clip-br` e entregue no Telegram.
4. Anote os tempos. O critério é: **1 bloco de 30 min processado e entregue em menos de ~15 min**. Isso dá folga para 3 streamers por hora.
5. Crie a **rotina** (claude.ai/code/routines, ou `/schedule` no CLI): repositório = seu fork, ambiente = "gta-br", horário = de hora em hora, prompt = `/clip-br`.
6. **Desligue o PC** e confira o Telegram nas 2 ou 3 horas seguintes. Só aí a nuvem está validada.

**Plano de contingência se ficar lento:** blocos de 15 min (`vods.chunk_minutes`), `transcribe_mode: hot` (só a parte mais barulhenta), `separate_voices: false`, ou um streamer por execução.

## B. Oracle Cloud Always Free (máquina persistente, gratuita com ressalvas)

**O que o Always Free oferece hoje** (documentação oficial, página de 12/06/2026; confira antes de criar):
- **Ampere A1 (ARM):** 2 OCPU e 12 GB de RAM no total.
- **Disco:** 200 GB.
- **Saída de dados:** 10 TB por mês.

**O que pesa contra:**
- Pede cartão de crédito.
- Instâncias só na home region, e "out of host capacity" é comum.
- VMs ociosas por 7 dias são recuperadas pela Oracle.
- O limite do A1 já foi cortado pela metade em 2026.

**Compatibilidade:** todas as nossas dependências rodam em ARM64 (FFmpeg, yt-dlp, onnxruntime, numpy, Pillow). Demucs fica lento com 2 OCPU.

**Se for usar:**
- Crie a VM **manualmente** no Console, escolhendo o shape `VM.Standard.A1.Flex`.
- **Não use** o `oracle.js` do repositório tools: ele cria um shape **pago** (E4.Flex).
- O `ORACLE/server-setup.sh` de lá serve como base de endurecimento, trocando a chave SSH.
- **O `SERVER/server-setup.sh` já vem com a chave SSH de outra pessoa preenchida: não rode sem editar.**
- Nessa máquina rodaria `clipper live watch` de verdade (gravação ao vivo), e o Claude entraria por rotina para a curadoria.

**Não criamos nenhum recurso.** Isso depende de você abrir a conta e aceitar os termos.

## C. Processamento local (sempre disponível)

O PC não precisa ficar ligado. Quando você ligar, rode `/clip-br` no Claude Code: `vods fetch` recupera tudo o que as lives deixaram nos VODs (dentro de `vods.lookback_hours`, 48 h por padrão), e a RTX 3060 acelera o render. Para gravar ao vivo durante um evento, deixe o PC ligado com `python3 -m clipper --profile gta-br live watch` rodando a cada 5 min (`schedule live`).

## Grok Bot

Fica para depois. Hoje ele vem na X Subscription, a partir de US$ 30 por mês, e não tem especificação oficial de CPU, RAM nem GPU. Só reavaliar se A e B falharem.
