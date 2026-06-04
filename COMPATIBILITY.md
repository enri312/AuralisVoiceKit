# Compatibilidad

AuralisVoiceKit esta disenado para que el core funcione en Windows, Ubuntu/Linux y macOS sin dependencias externas obligatorias.

El backend `sounddevice` es opcional. Segun la documentacion de `python-sounddevice`, el modulo esta disponible para Linux, macOS y Windows, y usa PortAudio como capa de audio:

- https://python-sounddevice.readthedocs.io/
- https://python-sounddevice.readthedocs.io/en/0.4.7/installation.html

El backend `wasapi` es opcional y solo funciona en Windows. Reutiliza el extra `sounddevice`, pero filtra dispositivos por la host API WASAPI para dar una ruta mas directa al stack moderno de audio de Windows.

El backend `openai` tambien es opcional. Usa el cliente oficial de OpenAI y no agrega dependencias nativas de audio al core. Requiere una variable `OPENAI_API_KEY` configurada por el usuario cuando se llama al backend real.

El backend `whisper` tambien es opcional. Usa `faster-whisper` para transcripcion local, puede descargar modelos en el primer uso y puede requerir dependencias de ML mas pesadas segun plataforma. No cambia el paquete base.

MP3, FLAC y otros formatos comprimidos usan `ffmpeg` como herramienta externa opcional. El core sigue sin depender de `ffmpeg` para instalarse, importar o procesar WAV PCM16.

El backend de salida `system` usa herramientas del sistema operativo cuando estan disponibles: PowerShell/SAPI en Windows, `say` en macOS y `spd-say` o `espeak` en Ubuntu/Linux. El backend `null` sigue siendo el default.

La busqueda de `ffmpeg` usa este orden:

1. Ruta explicita pasada por `--ffmpeg` o por la API, cuando contiene separadores de ruta.
2. Ejecutable disponible en `PATH`.
3. Variable `AURALIS_FFMPEG_PATH`.
4. Instalacion portable en `%LOCALAPPDATA%\AuralisTools\ffmpeg\bin\ffmpeg.exe` en Windows.

Cuando `ffmpeg` falta o falla, el error incluye el ejecutable solicitado, las rutas revisadas, sugerencia de instalacion por sistema operativo, comando usado, `stderr` truncado y un comando de inspeccion con `ffmpeg -hide_banner -i`.

Helpers disponibles desde Python:

```python
from auralis_voicekit import ffmpeg_install_hint, ffmpeg_search_locations

print(ffmpeg_install_hint())
print(ffmpeg_search_locations())
```

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

CI prueba Python 3.10 a 3.14 en Windows, Ubuntu/Linux y macOS. Tambien hay un job experimental con `3.15-dev` en Ubuntu; ese job es de observacion temprana y puede fallar sin bloquear el desarrollo. La ruta de audio comprimido se valida aparte con MP3 y FLAC reales mediante `ffmpeg` en Windows, Ubuntu/Linux y macOS.

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
py -m auralis_voicekit.cli devices --backend wasapi
```

Con transcripcion por OpenAI:

```powershell
py -m pip install -e ".[openai]"
$env:OPENAI_API_KEY="tu_api_key"
choco install ffmpeg -y
py -m auralis_voicekit.cli transcribe sample.mp3 --backend openai
```

Alternativa con ruta explicita:

```powershell
$env:AURALIS_FFMPEG_PATH="C:\Tools\ffmpeg\bin\ffmpeg.exe"
py -m auralis_voicekit.cli transcribe sample.mp3 --backend null --ffmpeg "C:\Tools\ffmpeg\bin\ffmpeg.exe"
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
python -m auralis_voicekit.cli doctor --devices --backend wasapi
python -m auralis_voicekit.cli doctor --capture-test --backend sounddevice --capture-seconds 0.25
python -m auralis_voicekit.cli doctor --capture-test --backend sounddevice --device default --json
python -m auralis_voicekit.cli doctor --wav sample.wav
python -m auralis_voicekit.cli doctor --json
python -m auralis_voicekit.cli benchmark --iterations 5
python -m auralis_voicekit.cli benchmark --iterations 5 --json
python -m auralis_voicekit.cli transcribe sample.mp3 --backend null --ffmpeg /path/to/ffmpeg
python -m auralis_voicekit.cli devices --backend sounddevice
python -m auralis_voicekit.cli devices --backend wasapi
python -m auralis_voicekit.cli backends
python -m auralis_voicekit.cli speak "Hola" --backend null --json
python -m auralis_voicekit.cli speak "Hola" --backend system
python -m auralis_voicekit.cli normalize sample.mp3 normalized.wav
python -m auralis_voicekit.cli normalize sample.flac normalized.wav
python -m auralis_voicekit.cli transcribe sample.wav --backend null --json
python -m auralis_voicekit.cli transcribe sample.mp3 --backend null --json
python -m auralis_voicekit.cli transcribe sample.flac --backend null --json
python -m auralis_voicekit.cli transcribe sample.mp3 --backend whisper --model base --json
python -m auralis_voicekit.cli transcribe-segments sample.wav --backend null --json
python -m auralis_voicekit.cli transcribe-segments sample.mp3 --backend null --json
python -m auralis_voicekit.cli transcribe-segments sample.flac --backend null --json
python -m auralis_voicekit.cli transcribe-segments sample.mp3 --backend whisper --model base --json
```

El comando `doctor` debe poder ejecutarse aunque los extras no esten instalados.

Para ejecutar las pruebas reales de MP3 y FLAC localmente se necesita `ffmpeg` disponible:

```bash
AURALIS_RUN_FFMPEG_INTEGRATION=1 python -m unittest tests.test_ffmpeg_integration
```

En PowerShell:

```powershell
$env:AURALIS_RUN_FFMPEG_INTEGRATION="1"
py -m unittest tests.test_ffmpeg_integration
Remove-Item Env:\AURALIS_RUN_FFMPEG_INTEGRATION
```
