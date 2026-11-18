# Telegram: entrega e aprovação pelo celular

O Telegram é gratuito e você não precisa construir nenhuma interface.

## Configurar (5 minutos)

1. No Telegram, abra **@BotFather** e envie `/newbot`. Escolha um nome e um usuário terminado em `bot`. Guarde o **token**.
2. Abra o seu bot novo e mande qualquer mensagem (por exemplo, "oi").
3. No projeto, coloque o token no `.env`:
   ```
   TELEGRAM_BOT_TOKEN=123456789:ABC...
   ```
4. Descubra o seu chat id: `python3 -m clipper --profile gta-br telegram chat-id`. Copie o número para `TELEGRAM_CHAT_ID=` no `.env`.
5. Teste: `python3 -m clipper --profile gta-br telegram notify "teste"`.

O `.env` nunca vai para o GitHub (está no `.gitignore`). Na nuvem, o token vai nas **variáveis de ambiente** do ambiente do Claude Code, nunca num arquivo do repositório.

## O que chega em cada vídeo

- O **MP4 final**, para baixar e publicar.
- Na legenda da mensagem: título sugerido, gancho que aparece na tela, tipo do vídeo e da fonte (oficial, gameplay confirmado, análise ou especulação), duração, **crédito ao criador**, **link da fonte** com o minuto exato e hashtags.
- Os botões **✅ Aprovar** e **❌ Rejeitar**.
- Logo abaixo, uma mensagem com a **descrição completa para copiar** (com crédito e hashtags).

O seu toque é registrado na próxima rodada (`telegram poll`), e o botão vira "✅ Aprovado" ou "❌ Rejeitado". Aprovar **não publica nada**; o registro serve para você se organizar e, depois, para a IA aprender o que você aprova.

## Pedir um vídeo pelo celular

Mande um link (YouTube ou VOD da Twitch) para o bot. Ele responde "Recebido" na próxima rodada e o link entra na fila. O `/clip-br` automático processa esses pedidos primeiro.

O bot só obedece ao seu chat (`TELEGRAM_CHAT_ID`). Mensagens de outras pessoas são ignoradas.

## Limites

- Bots só enviam arquivos de até **50 MB**. Um Short de 60 s em 1080x1920 fica bem abaixo disso. Um arquivo maior é pulado e reportado.
- O bot não fica ligado o tempo todo: ele lê os seus toques e pedidos a cada rodada, ou quando você roda `telegram poll`.
