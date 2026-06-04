# Compatibilidad

AuralisVoiceKit esta disenado para que el core funcione en Windows, Ubuntu/Linux y macOS sin dependencias externas obligatorias.

El backend `sounddevice` es opcional. Segun la documentacion de `python-sounddevice`, el modulo esta disponible para Linux, macOS y Windows, y usa PortAudio como capa de audio:

- https://python-sounddevice.readthedocs.io/
- https://python-sounddevice.readthedocs.io/en/0.4.7/installation.html

El backend `openai` tambien es opcional. Usa el cliente oficial de OpenAI y no agrega dependencias nativas de audio al core. Requiere una variable `OPENAI_API_KEY` configurada por el usuario cuando se llama al backend real.

El backend `whisper` tambien es opcional. Usa `faster-whisper` para transcripcion local, puede descargar modelos en el primer uso y puede requerir dependencias de ML mas pesadas segun plataforma. No cambia el paquete base.

MP3 y otros formatos comprimidos usan `ffmpeg` como herramienta externa opcional. El core sigue sin depender de `ffmpeg` para instalarse, importar o procesar WAV PCM16.

La busqueda de `ffmpeg` usa este orden:

1. Ejecutable disponible en `PATH`.
2. Variable `AURALIS_FFMPEG_PATH`.
3. Instalacion portable en `%LOCALAPPDATA%\AuralisTools\ffmpeg\bin\ffmpeg.exe` en Windows.

## Python

Version base soportada:

```text
Python >= 3.10
```

Politica:

- No usar limite superior artificial de Python.
- Mantener el core sin extensiones nativas.
- Probar versiones estables y prereleases cuando sea viable.
- Aislar dependencias nativas en extras opcionales.

CI prueba Python 3.10 a 3.14 en Windows, Ubuntu/Linux y macOS. Tambien hay un job experimental con `3.15-dev` en Ubuntu; ese job es de observacion temprana y puede fallar sin bloquear el desarrollo.

## Windows

Instalacion de desarrollo:

```powershell
cd E:\AuralisVoiceKit
py -m pip install -e .
py -m auralis_voicekit.cli doctor
```

Con captura por `sounddevice`:

```powershell
py -m pip install -e ".[sounddevice]"
py -m auralis_voicekit.cli doctor --devices
```

Con transcripcion por OpenAI:

```powershell
py -m pip install -e ".[openai]"
$env:OPENAI_API_KEY="tu_api_key"
choco install ffmpeg -y
py -m auralis_voicekit.cli transcribe sample.mp3 --backend openai
```

Con transcripcion local por Whisper:

```powershell
py -m pip install -e ".[whisper]"
py -m auralis_voicekit.cli transcribe sample.mp3 --backend whisper --model base
```

## Ubuntu/Linux

Instalacion de desarrollo:

```bash
cd AuralisVoiceKit
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m auralis_voicekit.cli doctor
```

Con captura por `sounddevice`, algunas distribuciones requieren PortAudio instalado por el sistema:

```bash
sudo apt update
sudo apt install libportaudio2
python -m pip install -e ".[sounddevice]"
python -m auralis_voicekit.cli doctor --devices
```

Con transcripcion por OpenAI:

```bash
python -m pip install -e ".[openai]"
export OPENAI_API_KEY="tu_api_key"
sudo apt update
sudo apt install ffmpeg
python -m auralis_voicekit.cli transcribe sample.mp3 --backend openai
```

Con transcripcion local por Whisper:

```bash
python -m pip install -e ".[whisper]"
sudo apt update
sudo apt install ffmpeg
python -m auralis_voicekit.cli transcribe sample.mp3 --backend whisper --model base
```

## macOS

Instalacion de desarrollo:

```bash
cd AuralisVoiceKit
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m auralis_voicekit.cli doctor
```

Con captura por `sounddevice`:

```bash
python -m pip install -e ".[sounddevice]"
python -m auralis_voicekit.cli doctor --devices
```

Si hay un problema con PortAudio, revisar la instalacion del backend con el gestor del sistema o con `conda-forge`.

Con transcripcion por OpenAI:

```bash
python -m pip install -e ".[openai]"
export OPENAI_API_KEY="tu_api_key"
brew install ffmpeg
python -m auralis_voicekit.cli transcribe sample.mp3 --backend openai
```

Con transcripcion local por Whisper:

```bash
python -m pip install -e ".[whisper]"
brew install ffmpeg
python -m auralis_voicekit.cli transcribe sample.mp3 --backend whisper --model base
```

## Diagnostico

Comandos utiles:

```bash
python -m auralis_voicekit.cli doctor
python -m auralis_voicekit.cli doctor --devices
python -m auralis_voicekit.cli doctor --devices --backend wav
python -m auralis_voicekit.cli doctor --capture-test --backend sounddevice --capture-seconds 0.25
python -m auralis_voicekit.cli doctor --capture-test --backend sounddevice --device default --json
python -m auralis_voicekit.cli doctor --wav sample.wav
python -m auralis_voicekit.cli doctor --json
python -m auralis_voicekit.cli devices --backend sounddevice
python -m auralis_voicekit.cli backends
python -m auralis_voicekit.cli normalize sample.mp3 normalized.wav
python -m auralis_voicekit.cli transcribe sample.wav --backend null --json
python -m auralis_voicekit.cli transcribe sample.mp3 --backend null --json
python -m auralis_voicekit.cli transcribe sample.mp3 --backend whisper --model base --json
python -m auralis_voicekit.cli transcribe-segments sample.wav --backend null --json
python -m auralis_voicekit.cli transcribe-segments sample.mp3 --backend null --json
python -m auralis_voicekit.cli transcribe-segments sample.mp3 --backend whisper --model base --json
```

El comando `doctor` debe poder ejecutarse aunque los extras no esten instalados.
