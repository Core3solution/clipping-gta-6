# Passagem de contexto entre sessões

Atualize ao fim de cada sessão de desenvolvimento, em poucas linhas. O hook de início de sessão mostra a seção "Próximos passos".

## Estado atual (17/11/2026)

- Branch `ptbr-operacao-lancamento`: perfil gta-br, PT-BR, Telegram, VODs, NVENC, zoom suave, `/clip-br`, estrutura de desenvolvimento (skills, agentes, hooks, regras).
- Suíte de testes verde. Nada testado ainda com rede real (Twitch, Telegram) nem com a GPU.

## Próximos passos

1. Instalar no PC (docs/pt-br/WINDOWS-WSL.md + scripts/devkit/install-local.sh) e rodar a suíte.
2. Criar o bot do Telegram e testar `telegram notify`.
3. Primeira produção real: `/clip-br <link de vídeo de GTA 6>`; revisar com o agente `qa-video`.
4. Teste da nuvem (docs/pt-br/NUVEM.md), primeiro com 1 bloco de VOD.
5. Depois: legendas animadas e callouts do Editonny, efeitos sonoros do woven-sfx, sinal de chat da Twitch.

## Decisões recentes

Ver `docs/pt-br/DECISOES.md` e `docs/pt-br/ECOSSISTEMA.md`.
