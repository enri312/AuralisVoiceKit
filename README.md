# AuralisVoiceKit

[![CI](https://github.com/enri312/AuralisVoiceKit/actions/workflows/ci.yml/badge.svg)](https://github.com/enri312/AuralisVoiceKit/actions/workflows/ci.yml)
[![Release](https://github.com/enri312/AuralisVoiceKit/actions/workflows/release.yml/badge.svg)](https://github.com/enri312/AuralisVoiceKit/actions/workflows/release.yml)
[![Version](https://img.shields.io/github/v/release/enri312/AuralisVoiceKit?include_prereleases&label=version)](https://github.com/enri312/AuralisVoiceKit/releases)
[![Python](https://img.shields.io/badge/python-3.10%2B-3776AB.svg)](https://github.com/enri312/AuralisVoiceKit/blob/main/COMPATIBILITY.md)
[![License](https://img.shields.io/badge/license-MIT-2f855a.svg)](LICENSE)

AuralisVoiceKit es una libreria moderna de voz para Python, pensada primero para Windows y para asistentes personales, agentes locales y herramientas de automatizacion por voz.

El objetivo principal es evitar que la captura de microfono dependa obligatoriamente de PyAudio o de wheels que tardan en llegar a las versiones nuevas de Python. El paquete base debe poder instalarse de forma liviana, sin compiladores y sin dependencias nativas obligatorias.

> Estado actual: alpha tecnica. El repositorio ya define el core, los contratos de backends, una CLI de diagnostico, documentacion estatica y pruebas basicas. Los backends reales de captura/transcripcion se iran agregando por etapas.

## Problema que resuelve

SpeechRecognition sigue siendo util como interfaz de reconocimiento, pero su entrada por microfono depende de PyAudio. PyAudio suele depender de wheels especificos por version de CPython; cuando sale una version nueva de Python, esa espera puede bloquear proyectos que necesitan audio en Windows.

AuralisVoiceKit busca separar tres cosas que normalmente aparecen mezcladas:

1. Captura de audio desde microfono o dispositivo.
2. Transcripcion local o por API.
3. Eventos de voz y salida de audio para asistentes.

El core no debe quedar atado a una sola tecnologia de audio.

## Principios de diseno

- Windows primero, sin cerrar la puerta a Linux o macOS.
- Core puro en Python, sin extensiones C obligatorias.
- Compatibilidad con Python moderno y versiones futuras razonables.
- Sin limite superior artificial de Python en `pyproject.toml`.
- Backends opcionales para `sounddevice`, WASAPI, PyAudio, Whisper u otras APIs.
- Privacidad visible: eventos y logs no deben exponer audio crudo por defecto.
- API simple para asistentes personales, agentes locales y prototipos de voz.

## Instalacion de desarrollo

```powershell
cd E:\AuralisVoiceKit
py -m pip install -e .
```

El paquete base no instala dependencias de audio externas. Para probar el core sin microfono:

```powershell
py -m unittest discover -s tests
py -m auralis_voicekit.cli doctor
```

Cuando se agreguen backends opcionales:

```powershell
py -m pip install -e ".[sounddevice]"
```

Guias por sistema:

```text
COMPATIBILITY.md
```

## Uso rapido

```python
from auralis_voicekit import AuralisVoiceKit, AudioChunk, AudioFormat

kit = AuralisVoiceKit()

chunk = AudioChunk(
    data=b"\x00\x00" * 16000,
    format=AudioFormat(sample_rate=16000, channels=1, sample_width=2),
)

result = kit.transcribe(chunk)
print(result.text)
```

Por defecto se usa un backend `null`. Esto permite probar la integracion sin hardware, sin permisos de microfono y sin dependencias nativas.

## Captura real con sounddevice

El backend `sounddevice` es opcional y permite capturar audio PCM16 desde microfono sin depender de PyAudio:

```powershell
py -m pip install -e ".[sounddevice]"
py -m auralis_voicekit.cli devices --backend sounddevice
py examples\capture_microphone.py --seconds 3 --output capture.wav
```

Tambien se puede seleccionar dispositivo por id, nombre o `default`:

```powershell
py examples\capture_microphone.py --device default --seconds 3
py examples\capture_microphone.py --device "Nombre del microfono" --seconds 3
```

## Utilidades de audio

El core incluye helpers puros para PCM16, sin NumPy ni dependencias externas:

```python
from auralis_voicekit import is_silent_pcm16, peak_pcm16, rms_pcm16, write_wav

energy = rms_pcm16(chunk)
peak = peak_pcm16(chunk)
silent = is_silent_pcm16(chunk, threshold=0.01)
write_wav("capture.wav", [chunk])
```

## Arquitectura

```text
auralis_voicekit
  core
    config        Configuracion portable
    models        AudioChunk, AudioFormat, TranscriptResult, AudioDevice
    events        EventBus y eventos de voz
    kit           Fachada principal AuralisVoiceKit
  backends
    base          Contratos comunes
    null          Backend seguro para pruebas
    sounddevice   Backend opcional de captura real
    registry      Registro de backends
  audio           Utilidades PCM16 puras
  cli             Diagnostico y utilidades
```

## Backends previstos

| Backend | Estado | Uso previsto |
| --- | --- | --- |
| `null` | incluido | pruebas, demos, integracion temprana |
| `sounddevice` | inicial funcional | captura moderna multiplataforma |
| `wasapi` | pendiente | ruta principal optimizada para Windows |
| `pyaudio` | pendiente | compatibilidad con proyectos existentes |
| `whisper` | pendiente | transcripcion local |
| `openai` | pendiente | transcripcion por API |

## Uso con asistentes

AuralisVoiceKit puede funcionar como capa de voz para asistentes personales y agentes locales:

- escuchar comandos hablados;
- detectar dispositivos de microfono;
- calibrar ruido ambiente;
- enviar audio a un reconocedor;
- devolver texto limpio a un loop de agente;
- registrar eventos de voz sin exponer datos privados.

## Roadmap

El roadmap completo esta en:

```text
ROADMAP.md
```

Prioridad inmediata:

1. Completar backend `sounddevice`.
2. Agregar ejemplo de captura real.
3. Agregar pruebas con mocks de `sounddevice`.
4. Mejorar `auralis doctor` para listar dispositivos cuando el backend este instalado.
5. Agregar utilidades de energia y calibracion de ruido.

## Documentacion

La documentacion HTML inicial esta en:

```text
docs/index.html
```

Se puede abrir directamente en el navegador; no requiere servidor local.

Tambien hay documentos de soporte:

```text
ROADMAP.md
VERSIONING.md
RELEASE_PROCESS.md
CHANGELOG.md
COMPATIBILITY.md
CONTRIBUTING.md
```
