# AuralisVoiceKit

[![CI](https://github.com/enri312/AuralisVoiceKit/actions/workflows/ci.yml/badge.svg)](https://github.com/enri312/AuralisVoiceKit/actions/workflows/ci.yml)
[![Release](https://github.com/enri312/AuralisVoiceKit/actions/workflows/release.yml/badge.svg)](https://github.com/enri312/AuralisVoiceKit/actions/workflows/release.yml)
[![Version](https://img.shields.io/github/v/release/enri312/AuralisVoiceKit?include_prereleases&label=version)](https://github.com/enri312/AuralisVoiceKit/releases)
[![Python](https://img.shields.io/badge/python-3.10%2B-3776AB.svg)](https://github.com/enri312/AuralisVoiceKit/blob/main/COMPATIBILITY.md)
[![License](https://img.shields.io/badge/license-MIT-2f855a.svg)](LICENSE)

AuralisVoiceKit es una libreria moderna de voz para Python, pensada primero para Windows y para asistentes personales, agentes locales y herramientas de automatizacion por voz.

El objetivo principal es evitar que la captura de microfono dependa obligatoriamente de PyAudio o de wheels que tardan en llegar a las versiones nuevas de Python. El paquete base debe poder instalarse de forma liviana, sin compiladores y sin dependencias nativas obligatorias.

> Estado actual: alpha tecnica. El repositorio ya define el core, los contratos de backends, captura real inicial, flujo WAV offline, transcripcion inicial por API, una CLI de diagnostico, documentacion estatica y pruebas basicas. Los backends reales se iran agregando por etapas.

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
py -m pip install -e ".[openai]"
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
from auralis_voicekit import (
    VoiceActivityDetector,
    calibrate_noise_pcm16,
    is_silent_pcm16,
    peak_pcm16,
    rms_pcm16,
    write_wav,
)

energy = rms_pcm16(chunk)
peak = peak_pcm16(chunk)
silent = is_silent_pcm16(chunk, threshold=0.01)
write_wav("capture.wav", [chunk])
```

Tambien se puede calibrar ruido ambiente y segmentar voz sin depender de modelos externos:

```python
profile = calibrate_noise_pcm16(noise_chunks)
detector = VoiceActivityDetector(noise_profile=profile)
segments = detector.segment(recorded_chunks)
```

Ejemplo completo:

```powershell
py examples\capture_voice_segments.py --calibrate-seconds 1 --record-seconds 5
```

## Flujo offline con WAV

Para desarrollar sin microfono se puede leer un WAV PCM16 y segmentarlo:

```powershell
py -m auralis_voicekit.cli wav-info sample.wav
py examples\segment_wav.py sample.wav --output-dir wav_segments
```

Tambien se puede usar el archivo como backend de captura:

```python
from auralis_voicekit import AuralisVoiceKit, VoiceKitConfig

chunks = []
kit = AuralisVoiceKit(
    VoiceKitConfig(
        capture_backend="wav",
        input_file="sample.wav",
        capture_block_ms=50,
    )
)
kit.start_capture(chunks.append)
```

## Transcripcion por API con OpenAI

El backend `openai` es opcional. Permite transcribir un WAV PCM16 usando la API de audio de OpenAI sin agregar dependencias nativas al paquete base.

```powershell
py -m pip install -e ".[openai]"
$env:OPENAI_API_KEY="tu_api_key"
auralis transcribe sample.wav --backend openai --language es
auralis transcribe sample.wav --backend openai --model gpt-4o-transcribe --json
py examples\transcribe_wav.py sample.wav --backend openai
```

Tambien se puede usar desde Python:

```python
from auralis_voicekit import AuralisVoiceKit, VoiceKitConfig, read_wav_as_chunk

chunk = read_wav_as_chunk("sample.wav")
kit = AuralisVoiceKit(
    VoiceKitConfig(
        transcription_backend="openai",
        transcription_model="gpt-4o-mini-transcribe",
        language="es",
    )
)

result = kit.transcribe(chunk)
print(result.text)
```

Segun la documentacion oficial de OpenAI para speech-to-text, los modelos soportados incluyen `gpt-4o-transcribe`, `gpt-4o-mini-transcribe` y `whisper-1`, con limite de carga de archivo de 25 MB:

```text
https://platform.openai.com/docs/guides/speech-to-text
```

## Diagnostico

`auralis doctor` genera un reporte de compatibilidad del entorno:

```powershell
auralis doctor
auralis doctor --devices --backend wav
auralis doctor --devices --backend sounddevice
auralis doctor --wav sample.wav
auralis doctor --json
```

La salida distingue entre `ok`, `warning` y `error`. Los warnings no bloquean el uso del core; por ejemplo, `sounddevice` puede faltar y aun asi funcionar `null`, `wav`, lectura WAV y utilidades de audio.

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
    wav_file      Backend offline para WAV PCM16
    sounddevice   Backend opcional de captura real
    openai        Backend opcional de transcripcion por API
    registry      Registro de backends
  audio           Utilidades PCM16, calibracion y segmentacion
  cli             Diagnostico y utilidades
  diagnostics     Reportes doctor estructurados
```

## Backends previstos

| Backend | Estado | Uso previsto |
| --- | --- | --- |
| `null` | incluido | pruebas, demos, integracion temprana |
| `wav` | inicial funcional | pruebas offline con WAV PCM16 |
| `sounddevice` | inicial funcional | captura moderna multiplataforma |
| `wasapi` | pendiente | ruta principal optimizada para Windows |
| `pyaudio` | pendiente | compatibilidad con proyectos existentes |
| `whisper` | pendiente | transcripcion local |
| `openai` | inicial funcional | transcripcion por API |

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

1. Crear ejemplo de loop escuchar -> segmentar -> transcribir.
2. Agregar normalizacion basica de volumen.
3. Preparar backend local de transcripcion como extra opcional.
4. Mejorar `auralis doctor` con una prueba corta de apertura de dispositivo bajo demanda.
5. Explorar soporte FLAC sin cargar el core con dependencias nativas.

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
