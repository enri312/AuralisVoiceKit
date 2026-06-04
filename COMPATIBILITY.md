# Compatibilidad

AuralisVoiceKit esta disenado para que el core funcione en Windows, Ubuntu/Linux y macOS sin dependencias externas obligatorias.

El backend `sounddevice` es opcional. Segun la documentacion de `python-sounddevice`, el modulo esta disponible para Linux, macOS y Windows, y usa PortAudio como capa de audio:

- https://python-sounddevice.readthedocs.io/
- https://python-sounddevice.readthedocs.io/en/0.4.7/installation.html

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

## Diagnostico

Comandos utiles:

```bash
python -m auralis_voicekit.cli doctor
python -m auralis_voicekit.cli doctor --devices
python -m auralis_voicekit.cli doctor --devices --backend wav
python -m auralis_voicekit.cli doctor --wav sample.wav
python -m auralis_voicekit.cli doctor --json
python -m auralis_voicekit.cli devices --backend sounddevice
python -m auralis_voicekit.cli backends
```

El comando `doctor` debe poder ejecutarse aunque los extras no esten instalados.
