# Auditoria técnica: gta-br, 18/11/2026

Feita no PC pessoal (WSL2, RTX 3060 12 GB, Ryzen 5 5500, 16 GB), depois do primeiro dia de produção no notebook. Aprovada pelo usuário em 18/11/2026. Nenhum código foi alterado e nada foi instalado durante a auditoria. O ZIP do Clipador de Live e os arquivos do Editonny foram lidos numa pasta temporária, sem executar nada.

Marcação: **[F]** = fato verificado (arquivo ou comando citado); **[H]** = hipótese a testar.

**O principal achado:** quase nada das ferramentas de edição foi aproveitado. Do Editonny, que é a única ferramenta especializada em edição, portamos **uma função** (o zoom `perspective`). Superpowers e Ponytail são ferramentas de *processo de desenvolvimento*: não editariam vídeo melhor mesmo se fossem usadas. Os 27 renders para 10 vídeos vêm de checagens que o QA por IA faz *depois* do render, quando um script poderia fazê-las *antes*. Isso também explica boa parte dos tokens gastos.

## 1. O que temos, o que foi incorporado e o que foi usado

| Ferramenta | Instalado | Incorporado ao código | Usado de fato |
| --- | --- | --- | --- |
| **clipping-gta-6** (upstream) | 5.902 linhas em `clipper/` [F] | Base de tudo | Render, sinais, ganchos e simulação foram usados na produção [F]. `dub.py`, `tts.py`, `voice_setup.py` e `speakers.py` (WhisperKit, só macOS) são ~800 linhas que o gta-br não usa [F]. |
| **Editonny** (MIT) | Não está instalado | Só o zoom `perspective` (`clipper/render.py`, `fx_filter`) [F] | O zoom, sim [F]. Todo o resto continua sem uso (ver §2). |
| **Vibe Coding Toolkit** (MIT) | Não é software: são docs e templates | Padrão `CLAUDE.md` → `AGENTS.md` e template de handoff [F] | O repositório é voltado a Next.js e ESLint (122 arquivos, maioria `templates/next`, `eslint`) [F]. Há docs úteis que não lemos: `10-hooks-best-practices`, `07-harness-evaluation`, `05-caveman` (economia de tokens). |
| **Superpowers** (14 skills) | Vendorizado em `.claude/skills/` [F] | N/A | Neste PC: **0 chamadas de skill em 3 sessões**, e não há planos salvos em `docs/` [F]. As sessões do notebook ficaram lá, então lá não dá para medir [H]. |
| **Ponytail** (5 skills) | Vendorizado [F] | N/A | Também 0 chamadas neste PC [F]. |
| **Agentes** | 4 (`qa-video`, `revisor`, `depurador`, `explorador`) [F] | N/A | `qa-video` foi usado nos 27 renders [F]. O `revisor` foi usado 2 vezes neste PC [F]. |
| **Hooks** | 3: `guard`, `session_context`, `verify_on_stop` [F] | N/A | Estão ativos. O `verify_on_stop` roda os 196 testes (~90 s) a cada parada com `.py` alterado [F]. |
| **Comandos** | `/clip-br` e mais 5 [F] | N/A | `/clip-br` foi usado na produção [F]. |

Sobre "falta de evidências de uso das skills de edição": **[F] não existe nenhuma skill de edição instalada.** As 19 skills são de processo. O Editonny é a ferramenta especializada, e ele não está instalado. Só uma técnica dele foi copiada.

## 2. Estamos recriando o que já existe?

Sim. O Editonny já tem, em código, o que o nosso QA por IA descobriu na tarde [F, lendo os módulos em `skills/editonny/engine/helpers/`]:

| Problema que o QA pegou (anatomia-do-corte) | Módulo do Editonny que já resolve por script |
| --- | --- |
| "Encanador começava dentro da palavra *Unless*" | `verify_cut.py` → `word_edge_probe` (corte no meio de palavra) |
| Silêncio morto, respiração | `quality_gate.py` (pausas ≥ 0,25 s), `tighten_cut.py` (encurta pausas sem dessincronizar) |
| Tela preta, LUFS, pico | `quality_gate.py` (preto ≥ 0,1 s, −14 LUFS ±1,5, TP < −1 dBTP), `verify_cut.py` |
| Texto sobre o rosto ou fora da área segura | `face_layout.py` (YuNet + zonas protegidas), `quality_gate.text_outside` |
| Legenda alucinada | `transcribe.py` (`loop_guard`, `silence_guard`, `known_phrase_guard`) |
| Legendas sem vida | `text_render.py` + `style_catalog.json`: **9 estilos animados** (`impact`, `word_box`, `giant_word`, `pulse`, `tape`, `paper`…) |
| Câmera parada | `camera_motion.py` (punch-in planejado nas palavras de ênfase), `track_faces.py` (rosto 10×/s, suavizado) |
| Efeitos sonoros | `make_sfx.py` (síntese procedural, sem problema de licença), `sound_plan.py` |

Isso é portável sem dependência nova:
- `text_render.py` usa **Pillow**, a mesma técnica dos nossos `captions.py` [F].
- O YuNet roda em **ONNX**. O `onnxruntime` já está no `.venv` [F]. O jeito simples (`cv2.FaceDetectorYN`) exige `opencv-python-headless`, que seria dependência nova.

O fluxo completo do Editonny também depende de HyperFrames (Chromium e npm) e tem integrações pagas opcionais (ElevenLabs, OpenRouter, Pexels); ver `DECISOES.md`, decisão 8.

## 3. Problemas da tarde, confrontados com o código

| Queixa | Causa no código |
| --- | --- |
| Legendas estranhas | **[F]** São imagens estáticas por estado. A palavra ativa só muda de cor, sem animação nenhuma (`captions.render_state`). O estilo `boxed` usa Bebas **116 px** e o `bold` usa Montserrat Black 84 px com contorno 8 (`captions.CAPTION_STYLES`). |
| Ganchos grandes demais | **[F]** Montserrat Black **88 px**, em maiúsculas, até 3 linhas, **na tela o vídeo inteiro**: `-loop 1 -t dur` em `render.encode_variant`. O texto passa da 3ª linha e é **cortado em silêncio**: `[:3]` em `captions.render_hook`. Foi isso que gerou o "…FINALMENTE". A regra dos "~28 caracteres" é um remendo no roteiro, não uma checagem. |
| Pouco uso do espaço vertical | **[F]** No layout `fit`, o jogo ocupa **1080×608 = 32% da altura**; o resto é fundo desfocado (`render.video_filter`). No `split`, a divisão é fixa em 768/1152, com recorte fixo. Não há tela cheia 9:16 seguindo a ação ou o rosto. |
| Layouts pouco dinâmicos e pouca variedade | **[F]** 2 modelos fixos no `/clip-br`, 3 estilos de legenda e 3 de gancho. O zoom só entra em fala gritada. |
| Excesso de renders (27 para 10) | **[F]** As checagens de borda de palavra, mudança de cena no último quadro e tamanho do gancho são feitas pelo `qa-video` *depois* do render. Cada reprovação custa um render inteiro e uma leitura de quadros por IA. |
| Muitos tokens | **[F]** O `transcript.json` tem **uma palavra por linha**, e a curadoria lê com Grep e Read ao redor. O QA lê quadros por IA. **[H]** Um resumo compacto por candidato (frases com tempo, pico do chat, uma folha de quadros) cortaria a maior parte. |

Divergências entre a anatomia e a realidade:
- **[F]** O HTML diz "24 blocos"; o `OPERACOES-2026-11-18.md` diz 26.
- **[F]** A anatomia apresenta o QA como "procura tela preta, imagem congelada, mede o volume", mas isso é a IA rodando ffmpeg à mão. Não existe script de QA no `clipper`.
- **[F]** A anatomia mostra o processo bem desenhado, mas o visual final depende de 3 estilos estáticos e de 2 layouts fixos.

## 4. Clipador de Live (ZIP de `Downloads`, SHA-256 `8e18b9aef624d285bf76e5a86e93fdf4d4ddc4f1b6e987ba9308cbb9604463bb`)

Versão 1.2.0: `clipador.py` (1.469 linhas) e `SKILL.md` (1.664 linhas; a skill traz uma cópia do código). O arquivo também está duplicado num formato de plugin.

**Licença: [F] nenhuma.** Não há `LICENSE` nem cabeçalho de copyright. O autor é "Rodolfo Mori" e o marketplace aponta para `SEU_USUARIO/clipador-de-live`, um repositório fictício, então a origem não pode ser verificada. **Não podemos copiar o código.** Podemos reimplementar as ideias.

**Segurança [F]:**
- Não usa `shell=True`, `eval` nem `exec`. A rede vai só para as plataformas e para o chat anônimo da Twitch (`justinfan`).
- O instalador baixa o **TwitchDownloaderCLI da release "latest"**, sem fixar versão nem checar hash.
- Faz `pip install` global sem lockfile (`streamlink`, `faster-whisper`, `websocket-client`, `opencv-python-headless<5`).
- Foi feito para Windows e PowerShell (`winget`).

**Compatibilidade [F]:** não combina com a nossa arquitetura. Ele tem pasta própria (`lives/`), não usa o `state/` e concorre com o `/clip-br`. **Recomendação: não instalar.** As ideias boas valem a reimplementação:

| Capacidade | Como o clipador faz | Comparação com o nosso |
| --- | --- | --- |
| **Análise do chat** | Conta *pessoas* distintas por janela de 15 s contra a mediana dos 10 min anteriores (z por MAD ou 2,5× o normal). Risada e susto pesam +0,5. Marca raid, sorteio e `!comando`. Twitch: VOD pelo TwitchDownloader, ao vivo por IRC. YouTube: replay pelo yt-dlp. **A Kick não é coberta.** | **Não temos nada disso.** É o maior ganho editorial. O YouTube sai pelo yt-dlp que já temos. A Twitch ao vivo dá para ler por IRC com `ssl`, só com a biblioteca padrão [H]. |
| **Download seletivo** | Mede o áudio da live inteira na **menor qualidade** (blocos de 10 min), acha os picos e baixa **só os segmentos HLS** de cada corte. | Nós baixamos tudo: **32 GB** só do Davy [F]. Nosso `vods.py` já baixa HLS da Kick por segmentos, então adaptar é pequeno [H]. |
| **Importar arquivo local** | `importar VIDEO --chat --deslocamento` | Exatamente a nossa pendência nº 1. |
| **Faster Whisper** | `small`, **CPU int8** | Não ganha do Parakeet, que já passou no QA em PT-BR [F]. Nenhum dos dois usa GPU. |
| **Rastreamento facial** | Haar cascade (detector antigo), 2 quadros/s, frente e perfil | Mais fraco que o YuNet do Editonny [H, pela literatura; não medido]. |
| **Enquadramento automático** | Decide sozinho: webcam no canto vira `split`; rosto grande vira recorte 9:16 que segue o rosto (zona morta, 8%/s). | A ideia do 9:16 cheio seguindo o rosto resolve a queixa do espaço vertical. |
| **Legendas** | ASS/libass, Arial 54, 3 palavras, palavra ativa amarela a 106% | É simples. O Editonny é melhor. |
| **Edição** | Sem efeitos e **sem título por cima**: "a legenda já é o gancho". Cortes de 15 a 45 s. **Nota de viral 0–10** com rubrica (gancho 3, contexto 2, final 2, emoção 2, chat 1). | Vale importar a rubrica para a curadoria. |

## 5. GPU, RAM e disco do PC

| Recurso | Fato | Como aproveitar |
| --- | --- | --- |
| **Render** | NVENC (`h264`, `hevc`, `av1`) e `-hwaccel cuda` disponíveis [F]. Já usamos NVENC no encode [F]. Os filtros rodam na CPU, inclusive o `gblur=sigma=40` em 1080×1920 [F]. | Fazer o desfoque em baixa resolução (216×384 → `gblur` → ampliar) [H: bem mais barato]. Usar NVDEC para decodificar o 1080p60. |
| **Transcrição** | O `.venv` tem `onnxruntime` **só CPU** e o `transcribe.py` força `providers=cpu` [F]. No notebook levou ~15–20 min por bloco de 30 min [F]. | Usar `onnxruntime-gpu` (Parakeet em CUDA) atrás de uma opção do perfil, mantendo a CPU na nuvem. **[H] ganho de 10× ou mais**: medir num bloco real antes de decidir. A alternativa é o faster-whisper `large-v3-turbo` em CUDA. Os 12 GB de VRAM sobram para os dois. |
| **Rosto e imagem** | N/A | O YuNet é minúsculo e a CPU basta. A GPU não é necessária aqui. |
| **Análise de vídeo** | N/A | Detecção de cena (`scdet`) na CPU, com decode por NVDEC. |
| **RAM** | O WSL enxerga **7,7 GiB** dos 16 GB. Não existe `.wslconfig` [F]. | Criar `.wslconfig` com `memory=12GB` (mudança no Windows; **adiada por decisão do usuário em 18/11**). |
| **Disco** | **C: tem 465 GB, 275 GB livres** [F]. O "1007 GB" do `df` no WSL é o limite virtual do VHDX, que ocupava 5,6 GB e cresce dentro do C: [F]. Não há D: neste PC [F]. | Um dia completo custa ~53 GB, então cabem uns 5 dias. Com download seletivo, cai muito [H]. O VHDX **não encolhe sozinho** depois de apagar arquivos (comportamento conhecido do WSL). |

## 6. Arquitetura recomendada (evolução, não reescrita)

```
CAPTURA            live.py (ao vivo) · vods.py (Kick/Twitch HLS) · NOVO import de MP4 · NOVO chat (Twitch IRC, YouTube replay)
   ↓
TRIAGEM (script)   NOVO: varredura de áudio barata + picos de chat + clipes do público → janelas candidatas
   ↓
DOWNLOAD SELETIVO  só as janelas (±90 s) em 1080p60     ← hoje baixamos tudo
   ↓
TRANSCRIÇÃO        Parakeet, GPU opcional, só as janelas
   ↓
CURADORIA (Claude) NOVO resumo compacto por candidato (frases+tempo, chat, 1 folha) + rubrica 0–10
   ↓
RECEITA            picks.json
   ↓
CHECAGEM (script)  check/simulate + NOVO: borda de palavra, gancho cabe no banner, troca de cena no fim, rosto no recorte
   ↓
RENDER             NOVO: estilos animados (Editonny), gancho menor e só nos primeiros segundos, layout 9:16 cheio seguindo ação/rosto
   ↓
QA (script→IA)     NOVO quality_gate em script; a IA só olha 1 folha por vídeo aprovado
   ↓
ENTREGA            telegram.py (já existe; falta o teste real)
```

## 7. Plano por etapas (cada uma com TDD, pequena e aditiva)

| # | Etapa | Ganho | Dependência nova |
| --- | --- | --- | --- |
| 0 | `.wslconfig` (RAM), bot do Telegram, benchmark do Parakeet CPU vs GPU num MP4 de teste | Base | Nenhuma no projeto |
| 1 | **Importar MP4 local** em blocos (spec no `OPERACOES-2026-11-18.md`) + chat de arquivo | Destrava Paulinho, Alanzoka e Tonyboy | Nenhuma |
| 2 | **Checagens determinísticas pré e pós render** (ideias do `verify_cut`/`quality_gate`); o gancho que não cabe passa a reprovar no `check` | Menos renders e menos tokens | Nenhuma |
| 3 | **Visual:** estilos de legenda animados portados do `text_render` (MIT, com crédito), gancho redesenhado (menor, por tempo), layout `fit` com zoom no jogo | Ataca as 3 queixas visuais | Nenhuma (Pillow) |
| 4 | **Sinal de chat** (YouTube replay pelo yt-dlp, Twitch IRC pela biblioteca padrão) no mapa de candidatos | Escolha editorial melhor | Nenhuma [H] |
| 5 | **Triagem por áudio + download seletivo** | Disco e tempo; escala para vários streamers | Nenhuma |
| 6 | **Rosto:** YuNet + 9:16 seguindo o rosto e a facecam detectada sozinha (dispensa o `clipper frame`) | Enquadramento sem a IA olhando quadros | `opencv-python-headless` (justificar) ou YuNet direto no `onnxruntime` |
| 7 | **Transcrição na GPU**, atrás de uma opção do perfil | 15–20 min → [H] 1–2 min por bloco | `onnxruntime-gpu` + libs CUDA (~2–3 GB) |
| 8 | Resumo compacto para a curadoria + rubrica 0–10 no `/clip-br`; QA por IA só no final | Tokens | Nenhuma |

Ordem sugerida na auditoria: **1 → 2 → 3** primeiro. As etapas 2 e 3 resolvem a insatisfação visual e o retrabalho sem nenhuma dependência nova.

## Decisões do usuário (18/11/2026, após a auditoria)

- Aprovados: importação de MP4, checagens determinísticas pré e pós render, análise de chat, download seletivo, legendas animadas, enquadramento inteligente, efeitos sonoros, movimentos de câmera e layouts dinâmicos.
- **Testar a skill completa do Editonny antes de portar recursos individuais**, e comparar a edição atual com uma feita pelo Editonny assim que houver material.
- Clipador de Live: só ideias, sem copiar código (sem licença).
- Transcrição por GPU: testar antes de definir o motor definitivo.
- Dependências gratuitas autorizadas, se justificadas, testadas e instaladas sem afetar o ambiente das outras sessões.
- RAM do WSL: não alterar agora; não reiniciar o WSL.
- Superpowers e Ponytail devem ser usados de fato no desenvolvimento.
- Nada é publicado automaticamente.
