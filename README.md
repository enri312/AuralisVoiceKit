# AuralisVoiceKit

[![CI](https://github.com/enri312/AuralisVoiceKit/actions/workflows/ci.yml/badge.svg)](https://github.com/enri312/AuralisVoiceKit/actions/workflows/ci.yml)
[![Release](https://github.com/enri312/AuralisVoiceKit/actions/workflows/release.yml/badge.svg)](https://github.com/enri312/AuralisVoiceKit/actions/workflows/release.yml)
[![Version](https://img.shields.io/github/v/release/enri312/AuralisVoiceKit?include_prereleases&label=version)](https://github.com/enri312/AuralisVoiceKit/releases)
[![Python](https://img.shields.io/badge/python-3.10%2B-3776AB.svg)](https://github.com/enri312/AuralisVoiceKit/blob/main/COMPATIBILITY.md)
[![License](https://img.shields.io/badge/license-MIT-2f855a.svg)](LICENSE)

AuralisVoiceKit es una libreria moderna de voz para Python, pensada primero para Windows y para asistentes personales, agentes locales y herramientas de automatizacion por voz.

English: AuralisVoiceKit is a modern voice toolkit for Python assistants, local agents and voice automation tools.

El objetivo principal es evitar que la captura de microfono dependa obligatoriamente de PyAudio o de wheels que tardan en llegar a las versiones nuevas de Python. El paquete base debe poder instalarse de forma liviana, sin compiladores y sin dependencias nativas obligatorias. Para MP3, FLAC y formatos comprimidos, AuralisVoiceKit usa `ffmpeg` como herramienta externa opcional.

> Estado actual: alpha tecnica. El repositorio ya define el core, los contratos de backends, captura real inicial, flujo WAV offline, transcripcion inicial por API y local opcional, sesiones de voz iniciales, una CLI de diagnostico, benchmarks offline de latencia, errores accionables para `ffmpeg`, documentacion estatica, pruebas unitarias y pruebas reales de MP3/FLAC. Los backends reales se iran agregando por etapas.

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

Cuando este publicado en PyPI, la instalacion normal sera:

```powershell
py -m pip install auralisvoicekit
```

Cuando se agreguen backends opcionales:

```powershell
py -m pip install -e ".[sounddevice]"
py -m pip install -e ".[openai]"
py -m pip install -e ".[whisper]"
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

Por defecto se usa un backend `null`. Esto permite probar la integracion sin hardware, sin permisos de microfono, sin credenciales y sin dependencias nativas. En la CLI, `auralis transcribe` y `auralis transcribe-segments` tambien arrancan con `null`; usa `--backend whisper` o `--backend openai` cuando quieras un transcriptor real.

## Captura real con sounddevice

El backend `sounddevice` es opcional y permite capturar audio PCM16 desde microfono sin depender de PyAudio:

```powershell
py -m pip install -e ".[sounddevice]"
py -m auralis_voicekit.cli devices --backend sounddevice
py -m auralis_voicekit.cli devices --backend wasapi
py examples\capture_microphone.py --seconds 3 --output capture.wav
```

Tambien se puede seleccionar dispositivo por id, nombre o `default`:

```powershell
py examples\capture_microphone.py --device default --seconds 3
py examples\capture_microphone.py --device "Nombre del microfono" --seconds 3
```

En Windows tambien existe un backend `wasapi` inicial. Usa el extra `sounddevice`, pero filtra dispositivos por la host API WASAPI:

```python
from auralis_voicekit import AuralisVoiceKit, VoiceKitConfig

kit = AuralisVoiceKit(
    VoiceKitConfig(
        capture_backend="wasapi",
        input_device="default",
    )
)
```

## Salida de voz del sistema

El backend `system` permite hablar usando herramientas ya presentes o instalables en el sistema operativo. El backend `null` sigue siendo el default para evitar reproducir audio por accidente.

```powershell
auralis speak "Hola desde AuralisVoiceKit" --backend null --json
auralis speak "Hola desde AuralisVoiceKit" --backend system
```

Desde Python:

```python
from auralis_voicekit import AuralisVoiceKit, VoiceKitConfig

kit = AuralisVoiceKit(VoiceKitConfig(output_backend="system"))
kit.speak("Hola desde AuralisVoiceKit")
```

Rutas usadas por plataforma:

- Windows: PowerShell con SAPI.
- macOS: comando `say`.
- Ubuntu/Linux: `spd-say` o `espeak`.

## Utilidades de audio

El core incluye helpers puros para PCM16, sin NumPy ni dependencias externas:

```python
from auralis_voicekit import (
    VoiceActivityDetector,
    calibrate_noise_pcm16,
    is_silent_pcm16,
    normalize_pcm16,
    peak_pcm16,
    rms_pcm16,
    write_wav,
)

energy = rms_pcm16(chunk)
peak = peak_pcm16(chunk)
silent = is_silent_pcm16(chunk, threshold=0.01)
normalized = normalize_pcm16(chunk, target_peak=0.95)
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
auralis normalize sample.mp3 normalized.wav --target-peak 0.95
auralis normalize sample.flac normalized.wav --target-peak 0.95
py examples\normalize_audio.py sample.mp3 normalized.wav
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

El backend `openai` es opcional. Permite transcribir WAV PCM16, MP3, FLAC u otros formatos soportados por `ffmpeg` usando la API de audio de OpenAI sin agregar dependencias nativas al paquete base.

```powershell
py -m pip install -e ".[openai]"
$env:OPENAI_API_KEY="tu_api_key"
auralis transcribe sample.wav --backend openai --language es
auralis transcribe sample.mp3 --backend openai --language es
auralis transcribe sample.flac --backend openai --language es
auralis transcribe sample.mp3 --backend openai --normalize --target-peak 0.95
auralis transcribe sample.wav --backend openai --model gpt-4o-transcribe --json
py examples\transcribe_wav.py sample.mp3 --backend openai
```

Tambien se puede usar desde Python:

```python
from auralis_voicekit import AuralisVoiceKit, VoiceKitConfig, read_audio_as_chunk

chunk = read_audio_as_chunk("sample.mp3")
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

Para MP3, FLAC y otros formatos comprimidos, instala `ffmpeg` y asegurate de que `ffmpeg` este disponible en `PATH`. `auralis doctor` reporta si lo encuentra y muestra donde lo busco.

Si `ffmpeg` falta o falla, AuralisVoiceKit devuelve un error accionable con:

- ejecutable solicitado;
- rutas revisadas, incluyendo `AURALIS_FFMPEG_PATH`;
- sugerencia de instalacion segun Windows, Ubuntu/Linux o macOS;
- comando de `ffmpeg` usado para decodificar;
- `stderr` de `ffmpeg`, truncado si es demasiado largo;
- comando de inspeccion para probar el archivo manualmente.

En Windows, la libreria tambien detecta una instalacion portable en:

```text
%LOCALAPPDATA%\AuralisTools\ffmpeg\bin\ffmpeg.exe
```

Tambien puedes apuntar a un ejecutable concreto con `AURALIS_FFMPEG_PATH` o con `--ffmpeg` en la CLI.

```powershell
$env:AURALIS_FFMPEG_PATH="C:\Tools\ffmpeg\bin\ffmpeg.exe"
auralis transcribe sample.mp3 --backend null --ffmpeg "C:\Tools\ffmpeg\bin\ffmpeg.exe"
auralis doctor --json
```

Desde Python tambien puedes consultar las rutas y sugerencias:

```python
from auralis_voicekit import ffmpeg_install_hint, ffmpeg_search_locations

print(ffmpeg_install_hint())
print(ffmpeg_search_locations())
```

Las pruebas de integracion reales para MP3 y FLAC se ejecutan solo cuando se activa una variable de entorno, asi el paquete base sigue testeandose sin herramientas externas:

```powershell
$env:AURALIS_RUN_FFMPEG_INTEGRATION="1"
py -m unittest tests.test_ffmpeg_integration
Remove-Item Env:\AURALIS_RUN_FFMPEG_INTEGRATION
```

En Ubuntu/Linux o macOS:

```bash
AURALIS_RUN_FFMPEG_INTEGRATION=1 python -m unittest tests.test_ffmpeg_integration
```

## Transcripcion local con Whisper

El backend `whisper` es opcional y usa `faster-whisper` para transcribir en la maquina local. No requiere API key, pero puede descargar modelos en el primer uso y agrega dependencias de ML fuera del core.

```powershell
py -m pip install -e ".[whisper]"
auralis transcribe sample.wav --backend whisper --model base --language es
auralis transcribe sample.mp3 --backend whisper --model base --normalize --json
auralis transcribe-segments sample.mp3 --backend whisper --model small --normalize --json
```

Tambien se puede usar desde Python:

```python
from auralis_voicekit import AuralisVoiceKit, VoiceKitConfig, read_audio_as_chunk

chunk = read_audio_as_chunk("sample.mp3")
kit = AuralisVoiceKit(
    VoiceKitConfig(
        transcription_backend="whisper",
        transcription_model="base",
        transcription_device="auto",
        transcription_compute_type="default",
        transcription_beam_size=5,
        transcription_vad_filter=False,
        language="es",
    )
)

result = kit.transcribe(chunk)
print(result.text)
```

Referencia del backend local:

```text
https://github.com/SYSTRAN/faster-whisper
```

## Loop de asistente

`VoiceSession` ofrece un flujo de alto nivel para leer o capturar audio, segmentar voz y transcribir cada turno:

```python
from auralis_voicekit import (
    AuralisVoiceKit,
    VoiceKitConfig,
    VoiceSession,
    VoiceSessionConfig,
)

kit = AuralisVoiceKit(
    VoiceKitConfig(
        transcription_backend="openai",
        transcription_model="gpt-4o-mini-transcribe",
        language="es",
    )
)
with VoiceSession(kit, VoiceSessionConfig(chunk_duration_ms=50)) as session:
    for turn in session.transcribe_wav("sample.wav"):
        print(turn.index, turn.text)
```

Las sesiones se pueden cancelar desde otro hilo, desde un callback o con cierre de contexto:

```python
with VoiceSession(kit) as session:
    turns = session.listen_once(
        30.0,
        on_turn=lambda turn: False,  # devuelve False para detener el loop
    )
```

Desde CLI se puede segmentar y transcribir un WAV:

```powershell
auralis transcribe-segments sample.wav --backend openai --language es --json
auralis transcribe-segments sample.mp3 --backend openai --language es --json
auralis transcribe-segments sample.mp3 --backend whisper --model base --language es --json
auralis transcribe-segments sample.mp3 --backend openai --normalize --json
auralis transcribe-segments sample.wav --backend null --json
```

Ejemplo completo de loop:

```powershell
py examples\assistant_loop.py --file sample.mp3 --transcription-backend openai
py examples\assistant_loop.py --seconds 5 --capture-backend sounddevice --transcription-backend openai
py examples\assistant_loop.py --seconds 30 --capture-backend sounddevice --transcription-backend whisper --model base
```

## Diagnostico

`auralis doctor` genera un reporte de compatibilidad del entorno:

```powershell
auralis doctor
auralis doctor --devices --backend wav
auralis doctor --devices --backend sounddevice
auralis doctor --capture-test --backend sounddevice --capture-seconds 0.25
auralis doctor --capture-test --backend sounddevice --device default --json
auralis doctor --wav sample.wav
auralis doctor --json
```

La salida distingue entre `ok`, `warning` y `error`. Los warnings no bloquean el uso del core; por ejemplo, `sounddevice` puede faltar y aun asi funcionar `null`, `wav`, lectura WAV y utilidades de audio. El flag `--capture-test` intenta abrir brevemente el backend de captura seleccionado y es util para diagnosticar permisos de microfono o errores de dispositivo.

## Benchmarks de latencia

`auralis benchmark` mide una linea base offline y determinista sin microfono, red ni extras nativos. Genera audio PCM16 sintetico, lo captura desde el backend `wav`, segmenta por RMS y transcribe los segmentos con el backend elegido.

```powershell
auralis benchmark
auralis benchmark --iterations 10 --duration 3 --json
auralis benchmark --transcription-backend whisper --model base --iterations 3
```

Por defecto se usa `transcription:null`; eso mide el costo del pipeline, no un modelo real. Para medir transcripcion local real instala `.[whisper]` y usa `--transcription-backend whisper`.

Desde Python:

```python
from auralis_voicekit import run_offline_benchmarks

report = run_offline_benchmarks(iterations=5)
for result in report.results:
    print(result.name, result.mean_ms, result.p95_ms)
```

## Arquitectura

```text
auralis_voicekit
  core
    config        Configuracion portable
    models        AudioChunk, AudioFormat, TranscriptResult, AudioDevice
    events        EventBus y eventos de voz
    kit           Fachada principal AuralisVoiceKit
    session       VoiceSession, VoiceSessionConfig y VoiceTurn
  backends
    base          Contratos comunes
    null          Backend seguro para pruebas
    wav_file      Backend offline para WAV PCM16
    sounddevice   Backend opcional de captura real
    wasapi        Backend inicial de captura Windows WASAPI
    whisper       Backend opcional de transcripcion local
    openai        Backend opcional de transcripcion por API
    system        Backend opcional de salida de voz del sistema
    registry      Registro de backends
  audio           Utilidades PCM16, calibracion y segmentacion
  benchmarks      Latencia offline para captura, segmentacion y transcripcion
  ffmpeg          Decodificacion opcional de MP3/FLAC a PCM16 con errores accionables
  cli             Diagnostico y utilidades
  diagnostics     Reportes doctor estructurados
```

## Backends previstos

| Backend | Estado | Uso previsto |
| --- | --- | --- |
| `null` | incluido | pruebas, demos, integracion temprana |
| `wav` | inicial funcional | pruebas offline con WAV PCM16 |
| `sounddevice` | inicial funcional | captura moderna multiplataforma |
| `wasapi` | inicial funcional | captura Windows filtrada por host API WASAPI |
| `pyaudio` | pendiente | compatibilidad con proyectos existentes |
| `whisper` | inicial funcional | transcripcion local opcional con faster-whisper |
| `openai` | inicial funcional | transcripcion por API |
| `system` | inicial funcional | salida de voz con herramientas del sistema operativo |

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

1. Preparar una pagina de documentacion API mas completa para usuarios de PyPI.
2. Mejorar la configuracion de voces para el backend `system`.
3. Robustecer WASAPI con pruebas manuales en hardware Windows real.
4. Agregar benchmarks comparativos opcionales para `whisper` en hardware real.
5. Preparar un ejemplo pequeno de integracion para usuarios de PyPI.

## Documentacion

La documentacion HTML principal esta en:

```text
docs/auralisvoicekit-documentacion.html
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
PYPI.md
```
