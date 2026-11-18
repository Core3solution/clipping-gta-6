# Rodar no Windows (WSL2 + RTX 3060)

O projeto usa recursos de Linux, como `fcntl`, apt e systemd. No Windows ele roda dentro do WSL2 com Ubuntu, e a RTX 3060 fica disponível lá dentro para o FFmpeg codificar com NVENC.

## 1. Instalar o WSL2 (uma vez, ~15 min)

No PowerShell **como administrador**:

```powershell
wsl --install -d Ubuntu
```

Reinicie, abra "Ubuntu" no menu Iniciar e crie usuário e senha. O driver NVIDIA normal do Windows já expõe a GPU ao WSL; não instale driver dentro do Ubuntu. Confira com `nvidia-smi` dentro do Ubuntu.

## 2. Ferramentas no Ubuntu

```bash
sudo apt update && sudo apt install -y git python3-pip python3-venv ffmpeg fonts-dejavu-core
ffmpeg -hide_banner -encoders | grep nvenc     # deve listar h264_nvenc
```

Se o FFmpeg do apt não listar `h264_nvenc`, o projeto usa `libx264` sozinho (`video_encoder: auto`). Funciona, só fica mais lento.

Instale o Claude Code pelo instalador oficial para Linux (veja code.claude.com) e entre com a sua conta Max.

## 3. Projeto

Trabalhe dentro do sistema de arquivos do Linux (`~/`), não em `/mnt/c/`: o acesso a arquivos é muito mais rápido.

```bash
cd ~
git clone https://github.com/<seu-usuario>/clipping-gta-6.git
cd clipping-gta-6
git checkout ptbr-operacao-lancamento
python3 -m venv .venv && . .venv/bin/activate
pip install -U yt-dlp "onnx-asr[cpu,hub]==0.12.0" numpy pillow pyyaml
cp .env.example .env            # depois preencha o Telegram (TELEGRAM.md)
python3 -m unittest discover -s tests
claude --model sonnet
```

Dentro do Claude Code: `/clip-br <link de um vídeo de GTA 6>`.

## 4. Onde ficam os vídeos

`exports/gta-br/<data>/video N/`. No Explorador do Windows, acesse `\\wsl$\Ubuntu\home\<usuario>\clipping-gta-6\exports`. Com o Telegram configurado, eles chegam no celular.

## Notas

- **Desligar o PC:** pode desligar. Os VODs da Twitch são recuperados depois por `vods fetch`. Só a gravação ao vivo (`live watch`) precisa do PC ligado.
- **Memória:** 16 GB bastam. Se o WSL ficar lento, limite a memória em `%UserProfile%\.wslconfig` (`[wsl2]` e `memory=10GB`).
- **Demucs** (separação de vozes) é o passo mais pesado. Para testes rápidos, use `separate_voices: false` no perfil.
