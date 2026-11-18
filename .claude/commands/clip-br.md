---
description: Produção GTA 6 Brasil sem perguntas. Com um link (modo manual) ou sem nada (modo automático), entrega os vídeos prontos no Telegram para aprovação
argument-hint: [link de vídeo ou VOD | vazio = rodada automática]
---

Produção automática do perfil `gta-br`. **Não pergunte nada ao usuário**: decida tudo você mesmo (trechos, início e fim, layout, efeitos, legendas, ganchos, títulos) seguindo as regras abaixo e as de `/clip` passo 7. Rode da raiz do projeto e passe `--profile gta-br` em todo `python3 -m clipper`. Leia `research/viral-gta-shorts.md` antes de escolher ganchos. **Nada é publicado em rede social**: o resultado vai para o Telegram, onde o usuário aprova ou rejeita.

Entrada: $ARGUMENTS

## 0. Telegram primeiro
Se `TELEGRAM_BOT_TOKEN` estiver configurado (`.env`), rode `python3 -m clipper --profile gta-br telegram poll` (registra Aprovar/Rejeitar e links enviados pelo celular) e `python3 -m clipper --profile gta-br telegram requests` (links pendentes). Sem Telegram configurado, pule as etapas de Telegram e entregue pela pasta `exports/gta-br/<data>/`.

## 1. Fontes desta rodada
- **Com link em $ARGUMENTS (modo manual):** só esse link. YouTube: `python3 -m clipper --profile gta-br run <link>` (stream acima de ~2 h: `--section` com a parte mais promissora). VOD da Twitch: adicione o canal com `live add twitch:<canal> --any-title` só se ele já estiver autorizado em `live.yaml`; caso contrário, use `run <link>` (o yt-dlp aceita VODs da Twitch).
- **Sem link (modo automático),** nesta ordem, parando quando houver material suficiente para `videos_per_run`:
  1. links pendentes do Telegram (mesmo tratamento do modo manual; depois `telegram requests --done <link>`);
  2. `python3 -m clipper --profile gta-br vods fetch` (VODs encerrados e a parte nova das lives em andamento, já transcritos);
  3. `python3 -m clipper --profile gta-br live jobs` (blocos gravados ao vivo, quando o PC estiver gravando);
  4. `python3 -m clipper --profile gta-br daily` (uploads novos dos criadores e do canal oficial).
  Se nada novo existir, rode `telegram notify "Sem material novo nesta rodada."` e pare.

## 2. Curadoria (entender o momento, não só o volume)
Para cada fonte, leia `candidates.md`, veja as folhas de quadros `review/cand_NN.jpg` e leia a transcrição em volta de cada candidato (`transcript.json`, uma palavra por linha: Grep `"s": 843.` e Read ao redor). Só aceite um momento se conseguir dizer, em uma frase cada: **o que aconteceu no jogo**, **por que o streamer reagiu**, **por que alguém que não viu a live entende e se importa** e **qual é o gatilho de clique** (lista do `/clip` passo 4). Procure também descobertas, detalhes escondidos, mecânicas novas, interações com NPCs e situações inesperadas que não têm pico de volume (seção "Scenario candidates"). Início: no primeiro fato relevante (sem "então galera", "tipo", "bom"). Fim: no resultado ou na reação ao resultado, nunca na decisão.

Classifique cada pick com `"source_kind"`: `oficial` (trailer ou material da Rockstar), `gameplay confirmado` (jogo rodando, de streamer ou criador), `análise` ou `especulação` (opinião, rumor, teoria). Especulação nunca é apresentada como fato no gancho, no título ou na descrição.

## 3. Dois modelos de edição (escolha um por vídeo)
- **Modelo A, "Reação"** (`clip_type` reaction ou comedy): facecam em cima e gameplay embaixo (`layout split`, use `clipper frame` para achar a facecam); `caption_style boxed`; `hook_style bold` (reaction) ou `box` (comedy); zoom só em fala gritada; `boom` no desfecho; sem música quando a fala preenche o vídeo. 9 a 35 s.
- **Modelo B, "Descoberta"** (`clip_type` gameplay, news, showcase ou scenario): gameplay em tela cheia (`layout fit`); `caption_style bold`; rótulos de ação em trechos sem fala (`*ENTRA NO CARRO*`); `flash` branco na revelação; música `suspense` ou `sneaky` só em trecho sem fala de 2 s ou mais. 20 a 58 s.
Efeitos só quando acrescentam (regras do `/clip` passo 7). Nunca o mesmo efeito em todos os vídeos.

## 4. Textos em português do Brasil
Ganchos, títulos, descrição, rótulos e `caption_fixes` em **PT-BR natural**, como o público brasileiro fala. Mesmas estruturas medidas na pesquisa, agora em português: promessa numérica ("3 detalhes que ninguém viu no *GTA 6*"), fato chocante, situação identificável ("Eu quando..."), negação ("Ele *NÃO* esperava..."), pergunta ("Por que a polícia...?"). Nome do streamer em pelo menos um gancho. Título com "GTA 6", até 100 caracteres, 1 ou 2 palavras em CAPS. Descrição: 1 ou 2 frases sobre o momento, sem revelar o desfecho; o crédito ("Corte de <canal>: <link>") e as hashtags do perfil são adicionados automaticamente. Escreva `picks.json` como no `/clip` passo 7, rode `clipper --profile gta-br check jobs/<id>/picks.json --job <id>` e `simulate`, e corrija todo **fail**.

## 5. Render, conferência e entrega
`python3 -m clipper --profile gta-br render <id> --picks jobs/<id>/picks.json --top-hooks 1` (um MP4 por vídeo: o gancho mais bem ranqueado). Extraia 1 quadro de cada MP4 com ffmpeg e olhe: legenda legível, facecam no lugar certo, nada cortado. Refaça o que estiver errado. Depois `python3 -m clipper --profile gta-br telegram send`. Para blocos de live, `live done <job>`. Termine com `python3 -m clipper --profile gta-br report "<resumo>"` e `telegram notify "<resumo curto: quantos vídeos, de quais streamers, o que foi descartado e por quê>"`.

## 6. Na nuvem (rotina)
Se estiver numa rotina do Claude Code na nuvem (clone novo a cada execução), no fim faça commit de `state/` (e só de `state/`) com a mensagem `estado: rodada <data hora>` e dê push no branch da rotina, para a próxima execução continuar de onde esta parou. Nunca faça commit de `.env`, `jobs/` ou `exports/`.
