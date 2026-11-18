# Operação GTA 6 Brasil

Este fork usa o clipping-gta-6 como motor de produção, adaptado ao público brasileiro. A IA encontra os momentos, entende o que aconteceu, edita, legenda, escreve título e descrição e entrega o MP4 pronto no seu Telegram. Você só aprova e publica. **Nada é publicado automaticamente.**

## Os dois modos

| Modo | Como usar | O que acontece |
| --- | --- | --- |
| Manual | `/clip-br <link>` no Claude Code (ou mandar o link para o bot do Telegram) | A IA decide trechos, início e fim, layout, efeitos e legendas, sem perguntas, e entrega no Telegram |
| Automático | `/clip-br` sem link (no PC ou numa rotina na nuvem) | Lê pedidos do Telegram, recupera VODs encerrados e a parte nova das lives em andamento, processa uploads novos e entrega no Telegram |

## Comandos novos do CLI

| Comando | Para que serve |
| --- | --- |
| `clipper --profile gta-br vods fetch` | Baixa os próximos blocos de VODs da Twitch (encerrados ou em andamento), transcreve e deixa prontos para o `/clip-br` |
| `clipper --profile gta-br vods fetch --dry-run` | Mostra o que baixaria, sem baixar |
| `clipper --profile gta-br vods status` | Até onde cada VOD já foi processado (`state/vods.json`) |
| `clipper --profile gta-br telegram send` | Envia ao Telegram os MP4 ainda não enviados (vídeo, legenda, botões Aprovar/Rejeitar e descrição para copiar) |
| `clipper --profile gta-br telegram poll` | Lê os toques em Aprovar/Rejeitar e os links que você mandou pelo celular |
| `clipper --profile gta-br telegram status` | Contagem de enviados, aprovados, rejeitados e pedidos pendentes |
| `clipper --profile gta-br telegram requests` | Links pendentes mandados pelo celular |
| `clipper --profile gta-br telegram chat-id` | Descobre o seu chat id (mande uma mensagem ao bot antes) |
| `clipper --profile gta-br telegram notify "texto"` | Mensagem simples para o seu chat |

Com `CLIPPER_PROFILE=gta-br` no `.env`, o `--profile gta-br` pode ser omitido.

## Onde cada coisa está

- `profiles/gta-br/`: perfil (palavras de empolgação em PT-BR, censura, encoder, VODs, exemplos de ganchos), `creators.yaml` (canais de upload; o canal oficial da Rockstar já está lá) e `live.yaml` (streamers da Twitch para lives e VODs).
- `.claude/commands/clip-br.md`: o roteiro que o Claude segue no `/clip-br` (curadoria, dois modelos de edição, textos em PT-BR, entrega).
- `state/`: progresso que precisa sobreviver entre execuções (VODs, Telegram). Pequeno, em JSON.
- `docs/pt-br/`: este guia, mais [WINDOWS-WSL.md](WINDOWS-WSL.md), [TELEGRAM.md](TELEGRAM.md), [NUVEM.md](NUVEM.md), [DECISOES.md](DECISOES.md), [DESENVOLVIMENTO.md](DESENVOLVIMENTO.md) e [ECOSSISTEMA.md](ECOSSISTEMA.md).

## Cadastrar streamers (só os autorizados)

```bash
python3 -m clipper --profile gta-br live add twitch:nome_do_canal      # lives e VODs da Twitch
python3 -m clipper --profile gta-br creators add @canal_do_youtube      # uploads do YouTube
```

`live add` só grava ou recupera transmissões cujo título fala de GTA 6. Para canais que não colocam isso no título, use `--any-title`. Todo corte sai com crédito ao criador e link da fonte na descrição.

## Os dois modelos de edição

- **A, Reação:** facecam em cima e gameplay embaixo, legenda em caixa, zoom só em fala gritada, impacto sonoro no desfecho.
- **B, Descoberta:** gameplay em tela cheia, legenda bold, rótulos de ação nos trechos sem fala, flash branco na revelação e música de suspense só em silêncio.

O Claude escolhe o modelo pelo tipo de momento. Os detalhes estão no `/clip-br`, seção 3.
