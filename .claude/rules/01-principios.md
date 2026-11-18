# Princípios de trabalho (sempre ativos)

- **Menor mudança completa** (skill `ponytail`): reutilize o que já existe no clipper antes de criar; nada de abstração, opção ou dependência que ninguém pediu. Termine tudo o que a mudança exige (chamadas, testes, docs).
- **Comportamento original preservado**: perfis `gta6` e `gta-rp` e o inglês não mudam. Adaptações entram como camada (perfil, configuração, padrão bilíngue).
- **Script antes de IA**: o que um script resolve de forma determinística não vai para LLM nem subagente.
- **Custo zero**: nenhuma API, serviço ou dependência paga. Dependência nova só com justificativa e no `pyproject.toml`/`uv.lock`.
- **Nada publicado automaticamente** em rede social. Telegram só entrega para aprovação.
- **Diga o que foi testado e o que não foi.** Nunca afirme que algo funciona sem rodar (skill `verification-before-completion`).
