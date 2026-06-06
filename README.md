# AuralisVoiceKit

[![CI](https://github.com/enri312/AuralisVoiceKit/actions/workflows/ci.yml/badge.svg)](https://github.com/enri312/AuralisVoiceKit/actions/workflows/ci.yml)
[![Release](https://github.com/enri312/AuralisVoiceKit/actions/workflows/release.yml/badge.svg)](https://github.com/enri312/AuralisVoiceKit/actions/workflows/release.yml)
[![Version](https://img.shields.io/github/v/release/enri312/AuralisVoiceKit?include_prereleases&label=version)](https://github.com/enri312/AuralisVoiceKit/releases)
[![Python](https://img.shields.io/badge/python-3.10%2B-3776AB.svg)](https://github.com/enri312/AuralisVoiceKit/blob/main/COMPATIBILITY.md)
[![License](https://img.shields.io/badge/license-MIT-2f855a.svg)](LICENSE)

AuralisVoiceKit es una libreria moderna de voz para Python, pensada primero para Windows y para asistentes personales, agentes locales y herramientas de automatizacion por voz.

English: AuralisVoiceKit is a modern voice toolkit for Python assistants, local agents and voice automation tools.

El objetivo principal es evitar que la captura de microfono dependa obligatoriamente de PyAudio o de wheels que tardan en llegar a las versiones nuevas de Python. El paquete base debe poder instalarse de forma liviana, sin compiladores y sin dependencias nativas obligatorias. Para MP3, FLAC y formatos comprimidos, AuralisVoiceKit usa `ffmpeg` como herramienta externa opcional.

> Estado actual: alpha tecnica con gate de pilotos reales y checklist de beta. El repositorio ya define el core, los contratos de backends, captura real inicial con `sounddevice`, `wasapi` y compatibilidad opcional `pyaudio`, diagnostico reforzado para WASAPI, bundles de diagnostico sanitizados y analizables, flujo WAV offline, transcripcion inicial por API y local opcional, sesiones de voz iniciales con activacion por frase/hook, una CLI de diagnostico, benchmarks offline y comparativos para Whisper exportables a JSON/CSV, errores accionables para `ffmpeg`, mensajes accionables para audio Windows, documentacion estatica, salida de voz del sistema con voces configurables, cola simple de salida y ejemplo seguro, salida custom en memoria, quickstart para PyPI sin extras, guia de privacidad/logs, ejemplo de asistente local con logs sanitizados, runner de piloto seguro, runner de piloto manual con checklist de captura, piloto de salida con checklist de operador y tarjeta de comando segura, piloto de transcripcion con checklist de revision y comando dedicado para MP3/WAV/FLAC real, preflight de fixture configurable por backend/modelo/timeout, scoring redactado, escaneo redactado de privacidad de referencia, redaccion de nombres de archivos de audio/referencia y confirmacion humana de calidad, checklist de beta automatizado, pruebas unitarias y pruebas reales de MP3/FLAC. Los backends reales se iran agregando por etapas.

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

Desde el repositorio clonado, el ejemplo pequeno de integracion para usuarios de PyPI funciona sin microfono, modelos ni credenciales:

```powershell
py examples\pypi_quickstart.py --json
```

Cuando se agreguen backends opcionales:

```powershell
py -m pip install -e ".[sounddevice]"
py -m pip install -e ".[pyaudio]"
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

Para ver el flujo base completo desde archivo WAV sintetico, segmentacion y transcripcion `null`, ejecuta:

```powershell
py examples\pypi_quickstart.py --json
```

## Captura real con sounddevice, WASAPI o PyAudio

El backend `sounddevice` es opcional y permite capturar audio PCM16 desde microfono sin depender de PyAudio:

```powershell
py -m pip install -e ".[sounddevice]"
py -m auralis_voicekit.cli devices --backend sounddevice
py -m auralis_voicekit.cli devices --backend wasapi
py examples\capture_microphone.py --seconds 3 --output capture.wav
```

El backend `pyaudio` tambien es opcional. Sirve como capa de compatibilidad para proyectos existentes que ya usan PortAudio/PyAudio; no se instala con el paquete base y no bloquea imports si falta el wheel:

```powershell
py -m pip install "auralisvoicekit[pyaudio]"
py -m pip install -e ".[pyaudio]"
py -m auralis_voicekit.cli devices --backend pyaudio
py -m auralis_voicekit.cli doctor --capture-test --backend pyaudio --device default --json
```

Tambien se puede seleccionar dispositivo por id, nombre o `default`:

```powershell
py examples\capture_microphone.py --device default --seconds 3
py examples\capture_microphone.py --device "Nombre del microfono" --seconds 3
```

En Windows tambien existe un backend `wasapi` inicial. Usa el extra `sounddevice`, pero filtra dispositivos por la host API WASAPI:

```powershell
py -m auralis_voicekit.cli doctor --devices --backend wasapi --json
py -m auralis_voicekit.cli doctor --capture-test --backend wasapi --device default --sample-rate 48000 --json
```

Ese diagnostico incluye host APIs reportadas por `sounddevice`, ids WASAPI, dispositivo de entrada default y el dispositivo WASAPI que se usaria al pedir `default`. English: the WASAPI diagnostic snapshot helps inspect real Windows hardware without opening an audio stream unless `--capture-test` is requested.

Cuando una captura falla en Windows, `auralis doctor --capture-test` agrega un `windows_audio_hint` con categoria y acciones concretas para permisos de microfono, dispositivo invalido, sample rate, canales o errores de host API:

```powershell
py -m auralis_voicekit.cli doctor --capture-test --backend wasapi --device default --sample-rate 48000 --json
```

Tambien se puede clasificar un error desde Python:

```python
from auralis_voicekit import windows_audio_error_hint

hint = windows_audio_error_hint(
    "PortAudioError: Invalid device [PaErrorCode -9996]",
    backend="wasapi",
    device="default",
    system="Windows",
)
print(hint.category)
print(hint.format_hint())
```

```python
from auralis_voicekit import AuralisVoiceKit, VoiceKitConfig
from auralis_voicekit.backends import inspect_wasapi_environment

snapshot = inspect_wasapi_environment()
print(snapshot.to_dict())

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
auralis voices --backend system
auralis speak "Hola desde AuralisVoiceKit" --backend system --voice "Microsoft Helena" --rate 2 --volume 80
py examples\system_output_demo.py --json
py examples\system_output_demo.py --system Windows --voice "Microsoft Helena" --rate 2 --volume 80 --json
```

Desde Python:

```python
from auralis_voicekit import AuralisVoiceKit, VoiceKitConfig

kit = AuralisVoiceKit(
    VoiceKitConfig(
        output_backend="system",
        output_voice="Microsoft Helena",
        output_rate=2,
        output_volume=80,
    )
)
kit.speak("Hola desde AuralisVoiceKit")
```

Para respuestas encadenadas, `AuralisVoiceKit` incluye una cola simple de salida. `queue_speech()` y `queue_speech_many()` encolan textos en orden, `drain_output_queue()` los envia secuencialmente al backend actual, `clear_output_queue()` descarta pendientes y `output_queue_size` informa cuantos items siguen esperando. Los eventos `output.started` / `output.completed` siguen saliendo por cada item drenado y no incluyen el texto hablado.

```python
kit.queue_speech_many([
    "Hola desde AuralisVoiceKit",
    "Preparando el siguiente paso",
])
kit.drain_output_queue(limit=1)
kit.drain_output_queue()
```

Rutas usadas por plataforma:

- Windows: PowerShell con SAPI, listado de voces instaladas, voz, velocidad y volumen.
- macOS: comando `say`, listado de voces, voz y velocidad.
- Ubuntu/Linux: `spd-say` o `espeak`; `espeak` permite voz, velocidad, volumen y listado de voces.

English: the `system` output backend can list voices and select voice/rate/volume when the operating system command supports those options.

El ejemplo `system_output_demo.py` usa dry-run por defecto: registra el comando que se ejecutaria, lista voces simuladas para Windows/macOS/Linux y emite eventos `output.*` sin reproducir audio. Para pilotos con artifacts, `tools/output_pilot.py` escribe `output-pilot-report.json`, `output-pilot-findings.md`, `output-operator-checklist.md` y `system-output-next-step.md` con el texto redactado en comandos, `target_output_backend.readiness_plan`, `beta_evidence_gap`, `system_output_command_card`, `system_output_operator_gate` y un scan `spoken_text_privacy_scan` que solo publica estado, conteo y tipos de riesgo. El readiness plan indica comandos candidatos, setup por sistema y un `post_install_check` sin audio; en Ubuntu/Linux recomienda `speech-dispatcher` o `espeak`, macOS usa `say` y Windows usa PowerShell/System.Speech. English: output pilots now expose a public-safe readiness plan before audible playback. La tarjeta de siguiente paso usa `<public-spoken-text>` y `<pilot-output-dir>` para no copiar texto hablado real ni rutas locales en artifacts compartidos; la evidencia beta exige `system_output_command_card.safe_to_share=true`, `uses_placeholders=true`, `preflight_plays_audio=false`, `real_output_requires_operator=true`, `records_spoken_text=false`, `records_operator_identity=false`, `records_local_paths=false`, `system_output_operator_gate.ready_for_beta_audit=true`, `system_output_operator_gate.command_safe_to_copy=true`, `system_output_operator_gate.missing_confirmation_count=0`, `system_output_operator_gate.missing_field_count=0`, `system_output_operator_gate.records_spoken_text=false` y `system_output_operator_gate.records_operator_identity=false`. Para un piloto real que pueda cerrar el blocker beta, usa `--speak --operator-present --confirm-audible --confirm-text-reviewed --confirm-voice-reviewed --require-output-backend-ready --expected-system "Windows|Linux|Darwin"` de forma explicita despues de revisar que el texto hablado sea publico/no sensible:

```powershell
py examples\system_output_demo.py --speak --text "Hola desde AuralisVoiceKit"
py tools\output_pilot.py --output-dir pilot_runs\output\system-dry-run --json
py tools\output_pilot.py --system Linux --require-output-backend-ready --json
py tools\output_pilot.py --speak --operator-present --confirm-audible --confirm-text-reviewed --confirm-voice-reviewed --require-output-backend-ready --expected-system "Windows|Linux|Darwin" --output-dir pilot_runs\output\system-real --text "Hola desde AuralisVoiceKit" --json
```

## Backends de salida personalizados

Un backend custom de salida implementa `info()` y `speak(text, config)`, se registra con `BackendRegistry.register_output()` y se selecciona con `VoiceKitConfig(output_backend="...")`.

```python
from auralis_voicekit import AuralisVoiceKit, VoiceKitConfig
from auralis_voicekit.backends import BackendInfo, create_default_registry

class QueueOutputBackend:
    name = "queue"

    def __init__(self):
        self.items = []

    def info(self):
        return BackendInfo(name=self.name, kind="output")

    def speak(self, text, config):
        if text.strip():
            self.items.append(text)

backend = QueueOutputBackend()
registry = create_default_registry()
registry.register_output("queue", lambda: backend)
kit = AuralisVoiceKit(VoiceKitConfig(output_backend="queue"), registry=registry)
kit.speak("Hola desde una salida custom")
```

Ejemplo ejecutable sin reproducir audio real:

```powershell
py examples\custom_output_backend.py --json
```

La guia completa esta en:

```text
CUSTOM_OUTPUT_BACKENDS.md
```

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
auralis transcribe sample.wav --backend openai --model gpt-4o-transcribe --timeout-seconds 30 --json
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
        transcription_timeout_seconds=30,
        language="es",
    )
)

result = kit.transcribe(chunk)
print(result.text)
```

El timeout es opcional. `transcription_timeout_seconds` tambien se puede configurar con `AURALIS_TRANSCRIPTION_TIMEOUT_SECONDS` o con `--timeout-seconds` en `auralis transcribe` y `auralis transcribe-segments`. English: the OpenAI backend passes the configured timeout to the official client; local Whisper runs remain local/model-bound and are not interrupted by this setting.

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
py examples\local_assistant_privacy_demo.py --json
```

`local_assistant_privacy_demo.py` corre offline y sin extras: genera audio sintetico, lo procesa con `VoiceSession`, responde con salida `null` y escribe eventos JSONL con `PrivacyEventLogger`. El payload incluye `privacy_checks` para confirmar que texto, path y token privados fueron redactados del log.

## Diagnostico

`auralis doctor` genera un reporte de compatibilidad del entorno:

```powershell
auralis doctor
auralis doctor --devices --backend wav
auralis doctor --devices --backend sounddevice
auralis doctor --devices --backend pyaudio
auralis doctor --capture-test --backend sounddevice --capture-seconds 0.25
auralis doctor --capture-test --backend pyaudio --device default --json
auralis doctor --capture-test --backend sounddevice --device default --json
auralis doctor --capture-test --backend wasapi --device 15 --sample-rate 48000 --json
auralis doctor --wav sample.wav
auralis doctor --json
auralis doctor --devices --backend wasapi --bundle reports/doctor-windows.json
auralis doctor-bundles reports/doctor-windows.json --output reports/doctor-analysis.json --json
```

La salida distingue entre `ok`, `warning` y `error`. Los warnings no bloquean el uso del core; por ejemplo, `sounddevice` o `pyaudio` pueden faltar y aun asi funcionar `null`, `wav`, lectura WAV y utilidades de audio. El flag `--capture-test` intenta abrir brevemente el backend de captura seleccionado y es util para diagnosticar permisos de microfono o errores de dispositivo.

Para pilotos o reportes de bugs, `--bundle` escribe un JSON sanitizado que redacta rutas locales y nombres de dispositivos, y no recoge audio ni transcripciones. `auralis doctor-bundles` agrupa bundles y resume sistemas, versiones Python, checks con warning/error, categorias y prioridades. English: doctor bundles are safe support artifacts for Windows, Ubuntu/Linux and macOS pilot reports.

## Benchmarks de latencia

`auralis benchmark` mide una linea base offline y determinista sin microfono, red ni extras nativos. Genera audio PCM16 sintetico, lo captura desde el backend `wav`, segmenta por RMS y transcribe los segmentos con el backend elegido.

```powershell
auralis benchmark
auralis benchmark --iterations 10 --duration 3 --json
auralis benchmark --iterations 10 --output reports/offline-benchmark.json
auralis benchmark --iterations 10 --output reports/offline-benchmark.csv --output-format csv
auralis benchmark --transcription-backend whisper --model base --iterations 3
auralis benchmark-whisper --models tiny,base --beam-sizes 1,5 --iterations 3 --json
auralis benchmark-whisper --models tiny,base --beam-sizes 1,5 --output reports/whisper.csv
```

Por defecto se usa `transcription:null`; eso mide el costo del pipeline, no un modelo real. Para medir transcripcion local real instala `.[whisper]` y usa `--transcription-backend whisper`.

`auralis benchmark-whisper` compara varias configuraciones de `faster-whisper` en el hardware local. Por defecto compara `tiny` y `base` con beam sizes `1` y `5`, y usa `--max-combinations` como proteccion para no lanzar una matriz enorme accidentalmente. English: this command is optional and only useful after installing the `whisper` extra.

`--output` escribe el reporte a archivo y el formato se infiere desde `.json` o `.csv`; `--output-format json|csv` permite fijarlo de forma explicita. English: benchmark exports are useful for CI artifacts, pilot runs and hardware comparisons.

Desde Python:

```python
from auralis_voicekit import (
    run_offline_benchmarks,
    run_whisper_comparison_benchmarks,
    write_benchmark_report,
)

report = run_offline_benchmarks(iterations=5)
for result in report.results:
    print(result.name, result.mean_ms, result.p95_ms)
write_benchmark_report(report, "reports/offline-benchmark.csv")

comparison = run_whisper_comparison_benchmarks(
    models=("tiny", "base"),
    beam_sizes=(1, 5),
    iterations=3,
)
print(comparison.to_dict()["rankings"])
write_benchmark_report(comparison, "reports/whisper.json")
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
    wasapi        Backend inicial de captura Windows WASAPI con diagnostico
    whisper       Backend opcional de transcripcion local
    openai        Backend opcional de transcripcion por API
    system        Backend opcional de salida de voz del sistema
    registry      Registro de backends
  audio           Utilidades PCM16, calibracion y segmentacion
  benchmarks      Latencia offline y comparativa para Whisper
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
| `wasapi` | inicial con diagnostico reforzado | captura Windows filtrada por host API WASAPI |
| `pyaudio` | inicial funcional | compatibilidad opcional con proyectos existentes basados en PyAudio |
| `whisper` | inicial funcional | transcripcion local opcional con faster-whisper |
| `openai` | inicial funcional | transcripcion por API |
| `system` | inicial con voces configurables | salida de voz con herramientas del sistema operativo y cola secuencial desde `AuralisVoiceKit` |

## Uso con asistentes

AuralisVoiceKit puede funcionar como capa de voz para asistentes personales y agentes locales:

- escuchar comandos hablados;
- detectar dispositivos de microfono;
- calibrar ruido ambiente;
- enviar audio a un reconocedor;
- devolver texto limpio a un loop de agente;
- registrar eventos de voz sin exponer datos privados.

`VoiceSession` tambien puede filtrar turnos por activacion inicial. Configura `activation_phrases` para una wake word sencilla o pasa `activation_hook` si el asistente decide la activacion desde otro modulo. `require_activation=True` se puede usar en `transcribe_chunks()`, `transcribe_file()`, `transcribe_wav()` y `listen_once()`; por defecto no filtra nada.

```python
from auralis_voicekit import VoiceSession, VoiceSessionConfig

session = VoiceSession(
    kit,
    VoiceSessionConfig(activation_phrases=("auralis",)),
)
turns = session.transcribe_file("sample.mp3", require_activation=True)

external_turns = session.transcribe_chunks(
    chunks,
    require_activation=True,
    activation_hook=lambda turn: turn.text.startswith("ok asistente"),
)
```

## Privacidad y logs

`privacy_mode=True` es el default. Los eventos del core no incluyen audio crudo ni texto transcrito, y el helper `PrivacyEventLogger` permite exportar eventos como JSONL con payload sanitizado:

```python
from auralis_voicekit import AuralisVoiceKit, PrivacyEventLogger

kit = AuralisVoiceKit()

with PrivacyEventLogger("auralis-events.jsonl") as logger:
    unsubscribe = logger.subscribe(kit.events)
    result = kit.transcribe(chunk)
    unsubscribe()
```

Ejemplo completo con asistente local y log sanitizado:

```powershell
py examples\local_assistant_privacy_demo.py --output-dir auralis_demo --json
```

La guia bilingue completa esta en:

```text
PRIVACY.md
```

## Automatizacion de estabilidad

El proyecto incluye un gate local y de CI para saber si estamos en alpha, listos para pilotos reales o listos para estable:

```powershell
py tools\stability_gate.py
py tools\stability_gate.py --json
py tools\stability_gate.py --min-stage pilot
```

Hoy el gate exige documentacion clave, privacidad/logs, guia de salida custom, ejemplos, PyPI, referencia API, ejemplo de asistente local con logs sanitizados, CI con Windows `windows-2025-vs2026`, pip sin cache y workflow de release con `actions/upload-artifact@v7.0.1`. Si pasa en etapa `pilot`, ya se puede empezar a probar con microfono real, voces del sistema y transcripcion real controlada antes de pensar en `1.0.0`.

Ruta portable del gate: `tools/stability_gate.py`.

Para evaluar si ya corresponde declarar beta publica, usa el checklist conservador. Por defecto no falla aunque existan blockers; con `--fail-on-blockers` sirve para auditorias estrictas del checklist y con `--fail-on-audit-gaps` convierte la auditoria JSON en gate estricto:

```powershell
py tools\beta_readiness.py --json
py tools\beta_readiness.py --output BETA_CHECKLIST.md
py tools\beta_readiness.py --requirements
py tools\beta_readiness.py --requirements --output BETA_EVIDENCE_REQUIREMENTS.md
py tools\beta_readiness.py --audit-evidence --evidence pilot_runs\manual\linux --json
py tools\beta_readiness.py --audit-evidence --evidence pilot_runs\manual --evidence pilot_runs\output --evidence pilot_runs\transcription --fail-on-audit-gaps --json
py tools\beta_readiness.py --evidence pilot_runs\manual\linux --evidence pilot_runs\output\real --json
py tools\beta_readiness.py --fail-on-blockers --json
```

El checklist generado vive en `BETA_CHECKLIST.md` y separa dos estados: listo para pilotos reales no significa listo para beta. El contrato versionado de evidencias vive en `BETA_EVIDENCE_REQUIREMENTS.md`; se regenera con `--requirements --output BETA_EVIDENCE_REQUIREMENTS.md` y enumera artifacts aceptados, campos JSON requeridos y reglas de privacidad antes de ejecutar pilotos reales. `--requirements` imprime los campos JSON necesarios para cada blocker antes de ejecutar pilotos reales, incluido `system_guard.expected_system_matched`, `capture_backend=sounddevice|pyaudio` en Ubuntu/Linux y macOS, `target_capture_backend.available=true`, `capture_backend_ready_required=true`, `input_review_confirmed=true`, `capture_checklist.input_review_confirmed=true`, `capture_checklist.ready_for_beta_evidence=true`, `manual_capture_command_card.safe_to_share=true`, `manual_capture_command_card.uses_placeholders=true`, `manual_capture_command_card.preflight_uses_microphone=false`, `manual_capture_command_card.real_capture_requires_microphone=true`, `manual_capture_command_card.records_audio=false`, `manual_capture_command_card.records_audio_bytes=false`, `manual_capture_command_card.records_device_name=false` y `manual_capture_command_card.records_local_paths=false` para captura real, `target_backend.available=true`, `target_backend_ready_required=true`, `audio.generated_synthetic_audio=false`, `audio.audio_confirmed_non_sensitive=true`, `audio.decoded=true`, `audio.audio_file_name_redacted=true`, `audio.duration_gate.enabled=true`, `audio.duration_gate.passed=true`, `transcript.text_redacted=true`, `audio_review_confirmed=true`, `reference_review_confirmed=true`, `reference_privacy_scan.passed=true`, `quality_review_confirmed=true`, `transcription_checklist.audio_review_confirmed=true`, `transcription_checklist.records_audio_path=false`, `transcription_checklist.records_audio_file_name=false`, `transcription_checklist.records_transcript_text=false`, `transcription_checklist.records_expected_text=false`, `transcription_checklist.records_expected_text_file_name=false`, `transcription_checklist.redacts_transcript_text=true`, `transcription_checklist.redacts_expected_text=true`, `transcription_checklist.reference_review_confirmed=true`, `transcription_checklist.reference_privacy_scan_passed=true`, `transcription_checklist.quality_review_confirmed=true`, `transcription_checklist.ready_for_beta_evidence=true`, `real_transcription_command_card.safe_to_share=true`, `real_transcription_command_card.uses_placeholders=true`, `real_transcription_command_card.preflight_runs_model=false`, `real_transcription_command_card.real_transcription_requires_user_audio=true`, `real_transcription_command_card.real_transcription_requires_quality_review=true`, `real_transcription_command_card.records_audio=false`, `real_transcription_command_card.records_audio_path=false`, `real_transcription_command_card.records_audio_file_name=false`, `real_transcription_command_card.records_transcript_text=false`, `real_transcription_command_card.records_expected_text=false`, `real_transcription_command_card.records_expected_text_file_name=false` y `real_transcription_command_card.records_local_paths=false` para transcripcion real, y `system_guard.expected_system_matched=true`, `target_output_backend.available=true`, `output_backend_ready_required=true`, `text_review_confirmed=true`, `spoken_text_privacy_scan.passed=true`, `voice_review_confirmed=true`, `operator_checklist.expected_system_matched=true`, `operator_checklist.records_operator_identity=false`, `operator_checklist.redacts_spoken_text=true`, `operator_checklist.text_review_confirmed=true`, `operator_checklist.spoken_text_privacy_scan_passed=true`, `operator_checklist.voice_review_confirmed=true`, `operator_checklist.commands_available=true`, `operator_checklist.ready_for_real_audio=true`, `operator_checklist.ready_for_beta_evidence=true`, `next_system_output.uses_placeholders=true`, `next_system_output.records_spoken_text=false`, `next_system_output.records_operator_identity=false`, `system_output_command_card.safe_to_share=true`, `system_output_command_card.uses_placeholders=true`, `system_output_command_card.preflight_plays_audio=false`, `system_output_command_card.real_output_requires_operator=true`, `system_output_command_card.records_audio=false`, `system_output_command_card.records_spoken_text=false`, `system_output_command_card.records_operator_identity=false`, `system_output_command_card.records_local_paths=false`, `system_output_operator_gate.ready_for_beta_audit=true`, `system_output_operator_gate.command_safe_to_copy=true`, `system_output_operator_gate.missing_confirmation_count=0`, `system_output_operator_gate.missing_field_count=0`, `system_output_operator_gate.records_spoken_text=false` y `system_output_operator_gate.records_operator_identity=false` para salida audible. `--audit-evidence` revisa artifacts reales, resume blockers cerrados/pendientes y explica que campo falta; `--fail-on-audit-gaps` devuelve codigo 1 si todavia faltan blockers o si algun artifact fue ignorado. `--evidence` acepta archivos o carpetas con JSON generados por `tools\manual_pilot.py`, `tools\output_pilot.py` y `tools\transcription_pilot.py`; solo cuenta artifacts con `project: AuralisVoiceKit`, reporta evidencias ignoradas con motivo (`missing_project`, `wrong_project`, `not_json_object`) y usa campos estructurados/nombres de artifacts, no transcripciones ni audio. English: real capture beta evidence requires `--confirm-input-reviewed`, `target_capture_backend.available=true`, `capture_backend_ready_required=true`, `sounddevice` or `pyaudio` on Ubuntu/Linux and macOS plus a safe `manual_capture_command_card`, real transcription beta evidence requires `target_backend.available=true`, `target_backend_ready_required=true`, non-synthetic decoded non-sensitive audio, redacted transcript and redacted audio/reference file names, `--confirm-audio-reviewed`, `--confirm-reference-reviewed`, `reference_privacy_scan.passed=true`, `--confirm-quality-reviewed` and a safe `real_transcription_command_card`, real output beta evidence requires `--confirm-text-reviewed`, `target_output_backend.available=true`, `output_backend_ready_required=true`, `spoken_text_privacy_scan.passed=true`, redacted spoken text, placeholder-only next steps, safe `system_output_command_card`, a ready `system_output_operator_gate`, `--confirm-voice-reviewed` and `--expected-system`, and readiness never copies private transcripts, spoken text or audio.

Desde `v0.140.0`, la transcripcion real tambien exige `real_transcription_operator_gate.ready_for_beta_audit=true`, `command_safe_to_copy=true`, `missing_confirmation_count=0`, `missing_field_count=0`, `records_audio=false`, `records_transcript_text=false`, `records_expected_text=false`, `records_expected_text_file_name=false`, `records_local_paths=false` y `records_operator_identity=false`. English: real transcription evidence now needs a public-safe operator gate in addition to the command card.

## Pilotos seguros

Nota `v0.105.0`: el piloto seguro tambien genera comandos OpenAI especificos en las tarjetas `fixture_preflight_card`, `transcription_readiness_card` y `real-pilot-command-pack.md`, usando `--preflight-backend openai`, `gpt-4o-mini-transcribe` y timeout 30 sin ejecutar red ni modelo durante el preflight.

Nota `v0.106.0`: para pilotos OpenAI, `tools/transcription_pilot.py` acepta `--require-openai-api-key`; solo registra si `OPENAI_API_KEY` esta presente mediante `credentials.openai_api_key_present` y mantiene `credentials.records_openai_api_key=false`.

Nota `v0.107.0`: el auditor beta acepta transcripcion real con OpenAI solo si el artifact incluye `credentials.checked=true`, `credentials.openai_api_key_required=true`, `credentials.openai_api_key_present=true` y `credentials.records_openai_api_key=false`; nunca pide ni guarda el valor de `OPENAI_API_KEY`.

Nota `v0.108.0`: el piloto seguro propaga esos requisitos condicionales a `next_beta_evidence_steps`, `recommended_pilot_sequence`, `evidence_manifest`, `pilot-plan.md`, `real-pilot-command-pack.md`, `real-pilot-handoff.md` y `real-pilot-evidence-manifest.md`, de modo que la ruta OpenAI no pierde `credentials.checked` ni los campos sanitizados de credencial.

Nota `v0.109.0`: el auditor beta lista evidencias aceptadas e ignoradas con rutas relativas seguras al directorio `--evidence`, por ejemplo `linux/manual-pilot-report.json`, para distinguir artifacts repetidos por plataforma sin exponer rutas locales absolutas. English: beta audits now expose public-safe relative evidence sources and `accepted_details` for real pilot batches.

Nota `v0.110.0`: `--audit-evidence` agrega `blocker_summaries` y un `Resumen por blocker` para indicar que evidencia cierra cada blocker, cuantos candidatos hubo y que artifact es el candidato mas cercano con sus campos faltantes. English: beta evidence audits now point to the closest candidate per blocker without exposing private content.

Nota `v0.111.0`: el piloto seguro propaga `blocker_summaries` a `pilot-report.json`, `pilot-plan.md` y `real-pilot-evidence-manifest.md`, asi el operador ve fuentes que cierran, candidato mas cercano y campos faltantes sin ejecutar el auditor por separado. English: safe-pilot artifacts now surface per-blocker beta evidence summaries.

Nota `v0.112.0`: el auditor beta y el piloto seguro exponen `next_evidence_focus` para senalar el primer blocker beta activo, su comando base, campos faltantes y candidato mas cercano sin publicar rutas privadas. English: beta audits and safe-pilot artifacts now show the next public-safe evidence focus.

Nota `v0.113.0`: el piloto seguro genera `real-pilot-next-evidence-focus.md`, una tarjeta dedicada al foco de evidencia siguiente con politica de contenido, artifacts de apoyo y condiciones antes de ejecutar. English: the safe pilot now writes a dedicated next-evidence-focus card.

Nota `v0.114.0`: `real-pilot-next-evidence-focus.md` incluye `Secuencia de preparacion` tomada de `recommended_pilot_sequence`, por ejemplo fixture sintetico, preflight MP3 propio y piloto real de transcripcion antes de auditar. English: the focus card now shows the safe preparation sequence before the real pilot.

Nota `v0.115.0`: `tools/transcription_pilot.py` agrega `preflight_readiness` en JSON y Markdown para saber si el preflight esta `ready`, `needs_backend_install`, `blocked` o `needs_preflight` antes de ejecutar Whisper/OpenAI. English: transcription preflights now expose a public-safe readiness summary and rerun command.

Nota `v0.116.0`: `tools/beta_readiness.py` exige `preflight_readiness.status=ready`, `ready_for_model_run=true` y redaccion segura para que una evidencia de transcripcion real pueda cerrar beta. English: beta evidence now requires a ready transcription preflight summary.

Nota `v0.117.0`: `tools/pilot_audio_fixture.py --run-preflight` propaga `preflight_readiness` al reporte del fixture y a sus findings para revisar el estado del preflight sin abrir el JSON interno. English: fixture preflights now surface the readiness summary.

Nota `v0.118.0`: `tools/transcription_pilot.py --real-transcription --require-target-backend-ready` conserva `preflight_readiness.status=ready` cuando los checks previos al modelo pasan, de modo que la evidencia real puede cumplir el contrato beta sin perder la readiness del preflight. English: guarded real transcription runs keep preflight readiness ready when the pre-model checks pass.

Nota `v0.119.0`: `tools/transcription_pilot.py` agrega `beta_evidence_gap` con campos faltantes, conteo y siguiente accion publica para saber si el reporte puede cerrar `real_transcription_quality`. English: transcription pilots now summarize beta evidence gaps without exposing audio, paths or transcripts.

Nota `v0.120.0`: cada piloto de transcripcion escribe `real-transcription-command.md`, una tarjeta segura con comandos de preflight MP3/WAV/FLAC, transcripcion real y auditoria beta; el preflight recomendado conserva guardas de duracion, revision de audio y guard estricto de backend. English: real transcription pilots now include a public-safe command card for preflight, model run and evidence audit.

Nota `v0.121.0`: `tools/output_pilot.py` agrega `beta_evidence_gap` para `system_output_audible`, mostrando campos faltantes y siguiente accion publica sin guardar texto hablado, identidad del operador ni rutas locales. English: system output pilots now summarize audible-output beta evidence gaps safely.

Nota `v0.122.0`: `tools/manual_pilot.py` agrega `beta_evidence_gap` para captura manual en Windows/WASAPI, Ubuntu/Linux y macOS, con campos faltantes y siguiente accion publica sin guardar audio, nombres de dispositivos ni rutas locales. English: manual capture pilots now summarize beta evidence gaps safely.

Nota `v0.123.0`: `tools/manual_pilot.py` escribe `manual-capture-command.md` con comandos seguros de setup, preflight sin microfono, captura real y auditoria beta usando placeholders. English: manual capture pilots now write a public-safe command card.

Nota `v0.124.0`: `tools/beta_readiness.py` exige `manual_capture_command_card` segura para cerrar evidencia beta de captura, con placeholders y flags que prueban que no se guardan audio, bytes, nombres de dispositivos ni rutas locales. English: capture beta evidence now requires a safe manual command card.

Nota `v0.125.0`: `tools/beta_readiness.py` exige `system_output_command_card` segura para cerrar evidencia beta de salida audible, con placeholders, preflight sin audio, operador obligatorio para salida real y flags que prueban que no se guardan audio, texto hablado, identidad del operador ni rutas locales. English: audible output beta evidence now requires a safe system output command card.

Nota `v0.126.0`: `tools/beta_readiness.py` exige `real_transcription_command_card` segura para cerrar evidencia beta de transcripcion real, con placeholders, preflight sin modelo, audio real y revision humana de calidad obligatorios y flags que prueban que no se guardan audio, rutas, transcripciones, texto esperado ni nombres de archivos. English: real transcription beta evidence now requires a safe command card.

Nota `v0.127.0`: `tools/beta_readiness.py --audit-evidence` agrega `privacy_audit` y bloquea beta si un artifact JSON aceptado contiene campos crudos sospechosos como `transcript.text`, `expected_text`, `spoken_text`, `audio.path`, nombres de archivo sin redaccion o credenciales; el reporte solo muestra nombres de campos, nunca valores privados. English: evidence audits now include a privacy scan that reports field paths only.

Nota `v0.128.0`: `tools/pilot_run.py` propaga `privacy_audit` a `pilot-report.json`, `pilot-plan.md`, `real-pilot-evidence-manifest.md` y `real-pilot-decision-gate.md`; la compuerta beta queda bloqueada si aparecen campos crudos sospechosos, incluso cuando una evidencia JSON cierra un blocker funcional. English: safe-pilot reports now surface privacy-audit blockers before beta decisions.

Nota `v0.129.0`: los hallazgos de `privacy_audit` ahora incluyen `action_es`, `action_en` y `safe_replacement` para reparar evidencias con placeholders como `<text-redacted>`, `<path-redacted>`, `<file-name-redacted>` o `<credential-redacted>` sin exponer valores privados. English: privacy audit findings now include safe remediation hints.

Nota `v0.130.0`: `privacy_remediation_plan` agrupa esos hallazgos en pasos ordenados por artifact/campo, declara `safe_to_share=true` y `records_private_values=false`, y aparece tambien en `pilot-plan.md`, `real-pilot-evidence-manifest.md` y `real-pilot-decision-gate.md`. English: privacy remediation is now an ordered public-safe plan.

Nota `v0.131.0`: `tools/pilot_run.py` ahora escribe `real-pilot-hard-stop-card.md`, una tarjeta segura para compartir con condiciones de alto antes de tocar hardware, audio real, texto hablado real o flags `--confirm-*`. English: safe pilots now include a real-world hard-stop card.

Nota `v0.132.0`: `tools/pilot_run.py` ahora escribe `real-pilot-evidence-intake-card.md`, una tarjeta publica para colocar reportes reales sanitizados, correr la auditoria estricta y refrescar `BETA_CHECKLIST.md` sin copiar contenido privado. English: safe pilots now include a public-safe evidence intake card.

Nota `v0.133.0`: `tools/pilot_run.py` ahora escribe `real-pilot-execution-card.md`, una tarjeta publica para ejecutar el siguiente piloto real en orden, revisar confirmaciones humanas, ubicar evidencia sanitizada y cerrar con auditoria estricta. English: safe pilots now include a public-safe execution card for the next real pilot.

Nota `v0.134.0`: `real_pilot_execution_card.operator_gate` declara si el siguiente piloto real esta listo para operador local, que revisiones previas y confirmaciones humanas faltan, que guard backend estricto aplica y que artifact JSON debe cerrarse con auditoria. English: the execution card now exposes a structured operator gate for safe local real-pilot runs.

Nota `v0.135.0`: `operator_gate.command_audit` valida que el comando local tenga flags obligatorios como `--expected-system`, `--confirm-*` y guards estrictos antes de marcarlo como copiable por un operador. English: the operator gate now audits required command flags before local real-pilot execution.

Nota `v0.136.0`: `operator_gate.evidence_contract` agrupa blocker, artifact JSON esperado, campos requeridos/faltantes, directorios sugeridos y comandos de auditoria/refresco en una ficha publica segura. English: the operator gate now includes a public-safe beta evidence contract.

Nota `v0.137.0`: `tools/manual_pilot.py` agrega `capture_operator_gate` en JSON y Markdown para decidir si la captura manual esta lista para auditoria beta o sigue bloqueada por confirmaciones, guardas o backend. English: manual capture pilots now include a public-safe operator gate.

Nota `v0.138.0`: `tools/beta_readiness.py` ahora exige `capture_operator_gate.ready_for_beta_audit=true` para aceptar evidencia beta de captura manual en Windows/WASAPI, Ubuntu/Linux y macOS. English: beta capture evidence now requires the manual capture operator gate.

Nota `v0.139.0`: `tools/output_pilot.py` y `tools/beta_readiness.py` agregan y exigen `system_output_operator_gate.ready_for_beta_audit=true` para aceptar evidencia beta de salida audible, con comando seguro, confirmaciones completas y sin texto hablado, rutas ni identidad del operador. English: audible output beta evidence now requires a public-safe operator gate.

Nota `v0.140.0`: `tools/transcription_pilot.py` y `tools/beta_readiness.py` agregan y exigen `real_transcription_operator_gate.ready_for_beta_audit=true` para aceptar evidencia beta de transcripcion real, con comando seguro, confirmaciones completas y sin audio, rutas, transcripciones, texto esperado ni identidad del operador. English: real transcription beta evidence now requires a public-safe operator gate.

Nota `v0.141.0`: `tools/pilot_run.py` ahora escribe `real-pilot-consent-card.md`, una plantilla publica de consentimiento local antes de usar hardware, audio real o flags `--confirm-*`; no registra identidad, firma, audio, rutas ni texto privado. English: safe pilots now include a public-safe local consent card.

Nota `v0.142.0`: `operator_gate.command_audit.copy_safety` separa plantilla segura, razones de bloqueo y revisiones locales pendientes antes de copiar o ejecutar el comando del siguiente piloto real. English: operator gates now expose copy-safety status before real-pilot command execution.

Nota `v0.143.0`: `tools/pilot_run.py` ahora escribe `real-pilot-audit-closure.md` y `real_pilot_audit_closure_card` para ordenar auditoria estricta, refresco de `BETA_CHECKLIST.md` y hallazgos sanitizados despues de generar el JSON real. English: safe pilots now include a public-safe audit closure card.

Nota `v0.144.0`: `tools/pilot_run.py` ahora escribe `real-pilot-rehearsal-card.md` y `real_pilot_rehearsal_card` para ensayar localmente sin hardware antes de copiar el comando real, revisando artifacts de apoyo, consentimiento, cierre de auditoria y comandos seguros. English: safe pilots now include a public-safe rehearsal card before real-pilot command execution.

`tools/pilot_run.py` ejecuta un piloto automatizado sin microfono, sin audio real, sin red y sin modelos. Genera un reporte con el gate, `doctor` usando backend `wav`, el demo de asistente local con logs sanitizados, salida `system` en dry-run, benchmarks offline exportados, `pilot-report.json`, `pilot-plan.md`, `real-pilot-handoff.md`, `real-pilot-command-pack.md`, `real-pilot-environment-checklist.md`, `real-pilot-fixture-preflight.md`, `real-pilot-transcription-readiness.md`, `real-pilot-system-output-readiness.md`, `real-pilot-evidence-manifest.md`, `real-pilot-decision-gate.md`, `real-pilot-next-evidence-focus.md`, `real-pilot-hard-stop-card.md`, `real-pilot-evidence-intake-card.md`, `real-pilot-execution-card.md`, `real-pilot-consent-card.md`, `real-pilot-audit-closure.md`, `real-pilot-rehearsal-card.md` y `real-pilot-findings-template.md`. El plan incluye evidencias JSON aceptadas/ignoradas, `next_beta_evidence_steps`, `recommended_pilot_sequence`, `platform_pilot_matrix`, `environment_checklist`, `fixture_preflight_card`, `transcription_readiness_card`, `system_output_readiness_card`, `evidence_manifest`, `pilot_decision_gate`, `real_pilot_handoff`, `real_pilot_command_pack`, `real_pilot_environment_checklist`, `real_pilot_fixture_preflight`, `real_pilot_transcription_readiness`, `real_pilot_system_output_readiness`, `real_pilot_evidence_manifest`, `real_pilot_decision_gate`, `real_pilot_next_evidence_focus`, `real_pilot_hard_stop_card`, `real_pilot_evidence_intake_card`, `real_pilot_execution_card`, `real_pilot_consent_card`, `real_pilot_audit_closure_card`, `real_pilot_rehearsal_card`, `operator_gate.command_audit.copy_safety` y `real_pilot_findings_template` con comandos separados para Windows, Ubuntu/Linux, macOS, salida audible y transcripcion MP3; los pasos que dependen de backend real exponen `strict_backend_guard_required`, `strict_backend_guard_flag` y `strict_backend_guard_field`; la captura manual espera `--expected-system`, `--confirm-input-reviewed`, `capture_backend=sounddevice|pyaudio` para Ubuntu/Linux y macOS, `system_guard.expected_system_matched`, `input_review_confirmed`, `capture_checklist.input_review_confirmed`, `manual-capture-checklist.md` y `capture_checklist.ready_for_beta_evidence`; si falta salida audible, inserta `system-output-operator-checklist` para revisar `output-operator-checklist.md` y `system-output-next-step.md` antes del audio real y pide `--confirm-text-reviewed`, `spoken_text_privacy_scan.passed`, `--expected-system "Windows|Linux|Darwin"`, `operator_checklist.text_review_confirmed`, `operator_checklist.spoken_text_privacy_scan_passed`, `operator_checklist.redacts_spoken_text`, `next_system_output.records_spoken_text=false`, `system_output_command_card.safe_to_share=true`, `system_output_command_card.uses_placeholders=true`, `system_output_command_card.records_spoken_text=false`, `system_output_command_card.records_operator_identity=false` y `operator_checklist.expected_system_matched`; si falta transcripcion real, la secuencia inicia con un fixture sintetico publico y sigue con `--preflight-only` para validar el MP3 propio con ffmpeg, reportar `target_backend.available`, `target_backend_ready_required`, dependencias y `target_backend.install_plan` del backend objetivo, `audio.audio_file_name_redacted`, guardas de duracion, `preflight_decision`, `transcription-review-checklist.md`, `real-transcription-next-step.md` y `real-transcription-command.md` sin ejecutar Whisper/OpenAI, luego pide `target_backend.available=true`, `target_backend_ready_required=true`, `audio.generated_synthetic_audio=false`, `audio.audio_confirmed_non_sensitive=true`, `audio.decoded=true`, `transcript.text_redacted=true`, `--confirm-audio-reviewed` antes de usar el modelo, `--confirm-reference-reviewed` antes del scoring, `reference_privacy_scan.passed=true` para la referencia, `transcription_checklist.records_audio_file_name=false`, `transcription_checklist.records_expected_text_file_name=false`, `real_transcription_command_card.safe_to_share=true`, `real_transcription_command_card.uses_placeholders=true` y `--confirm-quality-reviewed` solo despues de revisar localmente la calidad. `real-pilot-environment-checklist.md` resume Python, ffmpeg y backends opcionales antes de usar audio real y declara `usable_as_beta_evidence=false`; `real-pilot-fixture-preflight.md` convierte el fixture sintetico y el siguiente preflight con MP3 propio en una tarjeta segura con comandos, artifacts esperados, estado de ffmpeg, checks de backend y condiciones de alto sin contar como evidencia beta; `real-pilot-transcription-readiness.md` prepara la transcripcion real con fixture, preflight, backend objetivo, guard `--require-target-backend-ready`, plan de instalacion del extra opcional, revisiones de audio/referencia/calidad y condiciones de alto sin ejecutar modelos ni contar como evidencia beta; `real-pilot-system-output-readiness.md` prepara la salida audible con dry-run, checklist de operador, estado del backend `system`, comando con operador presente, flags obligatorios, tarjeta segura de comando y condiciones de alto sin contar como evidencia beta; `real-pilot-evidence-manifest.md` cruza blockers pendientes/cerrados, artifacts JSON esperados, campos requeridos, evidencias aceptadas/ignoradas y auditoria estricta sin contar como evidencia beta; `real-pilot-decision-gate.md` declara go/no-go para pilotos reales, beta y estable, el siguiente paso recomendado y condiciones de alto sin contar como evidencia beta; `real-pilot-next-evidence-focus.md` resume el blocker beta activo, comando base, artifacts de apoyo y condiciones antes de ejecutar; `real-pilot-hard-stop-card.md` separa condiciones de alto, acciones minimas y alcance permitido antes de tocar hardware, audio real, texto hablado real o flags `--confirm-*`; `real-pilot-evidence-intake-card.md` indica directorios sugeridos, artifacts JSON aceptados, auditoria estricta y reglas de ingesta para reportes reales sanitizados; `real-pilot-execution-card.md` ordena la ejecucion local del foco actual, confirmaciones humanas, guardas, ubicacion del JSON sanitizado, seguridad de copia del comando y cierre por auditoria; `real-pilot-consent-card.md` deja una plantilla de consentimiento local sin identidad ni firma antes de confirmar cualquier paso humano; `real-pilot-audit-closure.md` ordena auditoria estricta, refresco de checklist y hallazgos sanitizados antes de contar cualquier avance beta; `real-pilot-rehearsal-card.md` guia un ensayo sin hardware ni microfono con comandos seguros, checklist previo, artifacts de apoyo y regla de no copiar el comando real hasta revisar consentimiento y cierre de auditoria; `real-pilot-command-pack.md` agrupa comandos por plataforma, campos requeridos, guards estrictos y auditoria final para el operador; `real-pilot-handoff.md` es la tarjeta de traspaso y `real-pilot-findings-template.md` prepara el bloque sanitizado para `PILOT_FINDINGS.md`; todos usan placeholders y no incluyen audio, transcripciones, texto hablado real, rutas locales completas, nombres reales de dispositivos ni identidad del operador. English: the safe pilot can ingest JSON evidence and produce public-safe Markdown artifacts for accepted evidence, ignored artifacts, environment checks, a fixture preflight card, a transcription-readiness card with backend install plan and safe command card, a system-output readiness card, an evidence manifest, an evidence intake card, an execution card with copy-safety status, a consent card, an audit closure card, a rehearsal card, a go/no-go decision gate, a next-evidence-focus card, a hard-stop card, an ordered real-pilot sequence, a platform matrix, a real-pilot command pack, a handoff and a findings template.

```powershell
py tools\pilot_run.py --output-dir pilot_runs\safe --json
py tools\pilot_run.py --output-dir pilot_runs\safe --evidence pilot_runs\manual --evidence pilot_runs\output --evidence pilot_runs\transcription --json
```

`tools/manual_pilot.py` genera bundle doctor, analisis `doctor-bundles`, Markdown de hallazgos, `manual-capture-checklist.md` y `manual-capture-command.md`. Por defecto no abre microfono; para un piloto real de captura se debe pasar `--capture-test` de forma explicita. Usa `--target-system Linux` o `--target-system Darwin` para preparar instrucciones sin cambiar el sistema real del diagnostico, y `--expected-system Windows`, `--expected-system Linux` o `--expected-system Darwin` para bloquear evidencias generadas en la plataforma equivocada. El JSON incluye `target_capture_backend`, `capture_backend_ready_required`, `capture_readiness_plan` con `pip_command`, setup por sistema, `post_install_check`, `post_install_check_uses_microphone=false`, `real_capture_check_template`, `beta_evidence_gap` con campos faltantes, conteo y siguiente accion segura, y `manual_capture_command_card` con comandos plantilla de setup, preflight, captura real y auditoria beta; `--require-capture-backend-ready` falla temprano si falta el extra opcional antes de abrir microfono. En Ubuntu/Linux documenta `libportaudio2` para `sounddevice` o `portaudio19-dev python3-dev` para `pyaudio`, y en macOS documenta `brew install portaudio`. `--confirm-input-reviewed` se usa solo despues de revisar permisos del microfono, dispositivo de entrada y que el entorno no sea sensible. En Ubuntu/Linux y macOS la evidencia beta acepta `--backend sounddevice` o `--backend pyaudio`; Windows mantiene `--backend wasapi`. El JSON incluye `system_guard`, `input_review_confirmed`, `capture_checklist`, no guarda bytes de audio, nombres privados de dispositivos ni rutas locales, y redacta el selector de dispositivo cuando no es `default` o un id numerico. English: capture readiness exposes OS-specific install guidance, a strict backend guard, a command card and public-safe beta evidence gaps without opening the microphone; real capture evidence must include `system_guard.expected_system_matched=true`, `capture_backend=sounddevice|pyaudio` on Ubuntu/Linux and macOS, `target_capture_backend.available=true`, `capture_backend_ready_required=true`, `input_review_confirmed=true`, `capture_checklist.input_review_confirmed=true` and `capture_checklist.ready_for_beta_evidence=true`.

```powershell
py tools\manual_pilot.py --output-dir pilot_runs\manual\windows-safe --json
py tools\manual_pilot.py --backend sounddevice --target-system Linux --require-capture-backend-ready --json
py tools\manual_pilot.py --backend pyaudio --target-system Darwin --require-capture-backend-ready --json
py tools\manual_pilot.py --capture-test --backend wasapi --device default --sample-rate 48000 --expected-system Windows --confirm-input-reviewed --require-capture-backend-ready --json
py tools\manual_pilot.py --capture-test --backend sounddevice --device default --expected-system Linux --confirm-input-reviewed --require-capture-backend-ready --json
py tools\manual_pilot.py --capture-test --backend pyaudio --device default --expected-system Linux --confirm-input-reviewed --require-capture-backend-ready --json
py tools\manual_pilot.py --capture-test --backend sounddevice --device default --expected-system Darwin --confirm-input-reviewed --require-capture-backend-ready --json
py tools\manual_pilot.py --capture-test --backend pyaudio --device default --expected-system Darwin --confirm-input-reviewed --require-capture-backend-ready --json
```

`tools/output_pilot.py` prepara pilotos de salida `system` y resume `system_output_audible` con `beta_evidence_gap`. Por defecto es dry-run y no reproduce audio; siempre escribe `output-operator-checklist.md`, `system-output-next-step.md`, `system_guard`, `target_output_backend`, `target_output_backend.readiness_plan`, `spoken_text_privacy_scan` y `operator_checklist` en el JSON. El readiness plan enumera comandos candidatos (`powershell`, `say`, `spd-say` o `espeak`), setup por sistema y un `post_install_check` con `--require-output-backend-ready` que no reproduce audio; en Ubuntu/Linux documenta `sudo apt-get install -y speech-dispatcher espeak`. Con `--speak --operator-present --confirm-audible --confirm-text-reviewed --confirm-voice-reviewed --require-output-backend-ready --expected-system "Windows|Linux|Darwin"` usa voz real del sistema y registra artifacts sanitizados que pueden cerrar el blocker beta si `target_output_backend.available=true`, `output_backend_ready_required=true`, `text_review_confirmed=true`, `spoken_text_privacy_scan.passed=true`, `operator_checklist.text_review_confirmed=true`, `operator_checklist.spoken_text_privacy_scan_passed=true`, `operator_checklist.redacts_spoken_text=true`, `operator_checklist.records_operator_identity=false`, `operator_checklist.commands_available=true`, `operator_checklist.ready_for_real_audio=true`, `next_system_output.uses_placeholders=true` y `next_system_output.records_spoken_text=false`. `system-output-next-step.md` conserva un comando plantilla con `<public-spoken-text>` y no guarda el texto hablado completo. `--system` queda reservado para dry-runs y no se acepta con `--speak`:

```powershell
py tools\output_pilot.py --output-dir pilot_runs\output\system-dry-run --json
py tools\output_pilot.py --system Linux --require-output-backend-ready --json
py tools\output_pilot.py --speak --operator-present --confirm-audible --confirm-text-reviewed --confirm-voice-reviewed --require-output-backend-ready --expected-system "Windows|Linux|Darwin" --output-dir pilot_runs\output\system-real --text "Hola desde AuralisVoiceKit" --json
```

`tools/pilot_audio_fixture.py` genera WAV/MP3/FLAC sinteticos publicos para ensayar ffmpeg antes de usar audio privado; con `--run-preflight` tambien ejecuta un preflight seguro contra el MP3 generado y no cuenta como evidencia beta. Ese preflight se puede orientar con `--preflight-backend`, `--preflight-model` y `--preflight-timeout-seconds`, de modo que un operador prepare una plantilla OpenAI con timeout explicito sin ejecutar red ni modelo. `tools/transcription_pilot.py` prepara pilotos de transcripcion. Por defecto genera audio sintetico y usa backend `null`; con `--preflight-only` decodifica un archivo propio no sensible (por ejemplo MP3), valida que el backend objetivo este registrado, reporta `target_backend.available`, `target_backend_ready_required`, dependencias, razon de instalacion y `target_backend.install_plan` con `pip_command`, notas Windows/Ubuntu/macOS y `post_install_check`, emite `preflight_decision` con `decision`, `blocking_reasons`, `backend_ready` y `next_action`, y escribe metadata sanitizada sin ejecutar Whisper/OpenAI. `--require-target-backend-ready` convierte esa revision en un gate estricto que falla temprano si falta `auralisvoicekit[whisper]` u `auralisvoicekit[openai]`, mostrando el comando `python -m pip install "auralisvoicekit[whisper]"` o `python -m pip install "auralisvoicekit[openai]"` sin escribir rutas ni nombres privados. `--require-openai-api-key` valida que `OPENAI_API_KEY` exista para OpenAI sin guardar el valor; los artifacts solo reportan `credentials.openai_api_key_present` y `credentials.records_openai_api_key=false`. English: the fixture preflight can target Whisper or OpenAI and preserve a sanitized timeout and credential-presence check in the generated next-step command. Cada corrida escribe `transcription-review-checklist.md`, `real-transcription-next-step.md`, `real-transcription-command.md` y el bloque JSON `transcription_checklist` para revisar privacidad, duracion, referencia, comandos y calidad; las tarjetas contienen comandos plantilla con `<audio-path>`, `<expected-text-path>` y `<pilot-output-dir>` en vez de rutas locales o nombres reales. `real-transcription-command.md` separa preflight MP3/WAV/FLAC, corrida real y auditoria `tools/beta_readiness.py --audit-evidence`. `--min-audio-seconds` y `--max-audio-seconds` validan la duracion decodificada antes de continuar, util para rechazar archivos vacios o demasiado largos. Para `whisper` u `openai` exige `--real-transcription`, un archivo `--audio` y confirmacion `--audio-non-sensitive`; para que esa evidencia pueda cerrar beta tambien exige `target_backend.available=true`, `target_backend_ready_required=true`, `audio.audio_file_name_redacted=true`, `audio.duration_gate.enabled=true`, `audio.duration_gate.passed=true`, `--confirm-audio-reviewed` despues de revisar localmente la privacidad del audio, `--confirm-reference-reviewed` despues de revisar la privacidad del texto esperado, `reference_privacy_scan.passed=true` sin riesgos de email/URL/secretos/numeros largos y `--confirm-quality-reviewed` despues de revisar metricas redactadas y calidad de la transcripcion. Si usas `--backend openai`, agrega `--timeout-seconds 30` y `--require-openai-api-key`; el timeout se guarda como `transcription_timeout_seconds` y se pasa al cliente oficial como limite de red, mientras la credencial solo se registra como presencia/ausencia. El texto transcrito, el nombre del audio y el nombre del archivo de referencia quedan redactados en los artifacts; el scan de referencia solo guarda estado, conteo y tipos de riesgo. Si agregas `--expected-text` o `--expected-text-file`, calcula metricas de calidad como word accuracy y word error rate sin guardar la transcripcion ni el texto esperado:

```powershell
py tools\transcription_pilot.py --output-dir pilot_runs\transcription\safe --json
py tools\transcription_pilot.py --output-dir pilot_runs\transcription\quality-safe --expected-text "Hola desde AuralisVoiceKit" --min-word-accuracy 0 --json
py tools\pilot_audio_fixture.py --output-dir pilot_runs\transcription\fixture --format wav --format mp3 --run-preflight --json
py tools\pilot_audio_fixture.py --output-dir pilot_runs\transcription\fixture-openai --format mp3 --run-preflight --preflight-backend openai --preflight-model gpt-4o-mini-transcribe --preflight-timeout-seconds 30 --json
py tools\transcription_pilot.py --preflight-only --audio sample.mp3 --audio-non-sensitive --backend whisper --normalize --min-audio-seconds 0.2 --max-audio-seconds 60 --json
py -m pip install "auralisvoicekit[whisper]"
py tools\transcription_pilot.py --preflight-only --audio sample.mp3 --audio-non-sensitive --confirm-audio-reviewed --backend whisper --model base --min-audio-seconds 0.2 --max-audio-seconds 60 --require-target-backend-ready --json
py tools\transcription_pilot.py --real-transcription --audio sample.mp3 --audio-non-sensitive --confirm-audio-reviewed --confirm-reference-reviewed --backend whisper --model base --normalize --expected-text "Hola desde AuralisVoiceKit" --min-word-accuracy 0.75 --min-audio-seconds 0.2 --max-audio-seconds 60 --confirm-quality-reviewed --require-target-backend-ready --json
py tools\transcription_pilot.py --real-transcription --audio sample.mp3 --audio-non-sensitive --confirm-audio-reviewed --confirm-reference-reviewed --backend openai --model gpt-4o-mini-transcribe --timeout-seconds 30 --expected-text "Hola desde AuralisVoiceKit" --min-word-accuracy 0.75 --min-audio-seconds 0.2 --max-audio-seconds 60 --confirm-quality-reviewed --require-target-backend-ready --require-openai-api-key --json
```

`tools/beta_readiness.py` resume blockers de beta a partir del gate, `PILOT_FINDINGS.md` y artifacts JSON pasados con `--evidence`. Hoy marca como pendientes la transcripcion real con calidad, `target_backend.available=true`, `target_backend_ready_required=true`, `audio.generated_synthetic_audio=false`, `audio.audio_confirmed_non_sensitive=true`, `audio.decoded=true`, `audio.audio_file_name_redacted=true`, `audio.duration_gate.enabled=true`, `audio.duration_gate.passed=true`, `transcript.text_redacted=true`, `audio_review_confirmed=true`, `reference_review_confirmed=true`, `reference_privacy_scan.passed=true`, `quality_review_confirmed=true`, `transcription_checklist.audio_review_confirmed=true`, `transcription_checklist.records_audio_file_name=false`, `transcription_checklist.records_expected_text_file_name=false`, `transcription_checklist.redacts_transcript_text=true`, `transcription_checklist.redacts_expected_text=true`, `transcription_checklist.reference_review_confirmed=true`, `transcription_checklist.reference_privacy_scan_passed=true`, `transcription_checklist.quality_review_confirmed=true` y `transcription_checklist.ready_for_beta_evidence=true`; si `target_backend.name=openai`, tambien exige `credentials.checked=true`, `credentials.openai_api_key_required=true`, `credentials.openai_api_key_present=true` y `credentials.records_openai_api_key=false`. Tambien bloquea hasta tener salida `system` audible confirmada con `system_guard.expected_system_matched=true`, `text_review_confirmed=true`, `spoken_text_privacy_scan.passed=true`, `voice_review_confirmed=true`, `operator_checklist.expected_system_matched=true`, `operator_checklist.records_operator_identity=false`, `operator_checklist.redacts_spoken_text=true`, `operator_checklist.text_review_confirmed=true`, `operator_checklist.spoken_text_privacy_scan_passed=true`, `operator_checklist.voice_review_confirmed=true`, `operator_checklist.commands_available=true`, `operator_checklist.ready_for_real_audio=true`, `operator_checklist.ready_for_beta_evidence=true`, `next_system_output.uses_placeholders=true` y `next_system_output.records_spoken_text=false`, captura Ubuntu/Linux y captura macOS con `capture_backend=sounddevice|pyaudio`, `system_guard.expected_system_matched=true`, `input_review_confirmed=true`, `capture_checklist.input_review_confirmed=true` y `capture_checklist.ready_for_beta_evidence=true`.

Los pasos con hardware quedan documentados en:

```text
PILOTS.md
PILOT_FINDINGS.md
BETA_CHECKLIST.md
BETA_EVIDENCE_REQUIREMENTS.md
```

## Roadmap

El roadmap completo esta en:

```text
ROADMAP.md
```

Prioridad inmediata:

1. Ejecutar piloto de transcripcion real con audio propio no sensible usando `tools\transcription_pilot.py --real-transcription --audio ... --audio-non-sensitive --confirm-audio-reviewed --confirm-reference-reviewed --expected-text ... --min-word-accuracy 0.75 --min-audio-seconds 0.2 --max-audio-seconds 60 --confirm-quality-reviewed --require-target-backend-ready` solo despues de revisar localmente privacidad del audio, privacidad de la referencia, `audio.audio_file_name_redacted=true`, `reference_privacy_scan.passed=true`, `audio.duration_gate.enabled=true`, `audio.duration_gate.passed=true`, `transcription_checklist.records_audio_file_name=false`, `transcription_checklist.records_expected_text_file_name=false`, `target_backend.available=true`, `target_backend_ready_required=true`, `preflight_decision.decision=ready_for_real_transcription` o reinstalar el backend y repetir preflight, y calidad, conservando `transcription-review-checklist.md` junto con `real-transcription-next-step.md`.
2. Preparar `output-operator-checklist.md` y `system-output-next-step.md` con `tools\output_pilot.py --output-dir pilot_runs\output\system-dry-run --json` y luego ejecutar salida `system` real con `tools\output_pilot.py --speak --operator-present --confirm-audible --confirm-text-reviewed --confirm-voice-reviewed --require-output-backend-ready --expected-system "Windows|Linux|Darwin" --output-dir pilot_runs\output\system-real`, solo despues de revisar privacidad del texto hablado, `target_output_backend.available=true`, `output_backend_ready_required=true`, `spoken_text_privacy_scan.passed=true`, voz, volumen y pronunciacion.
3. Repetir captura con microfono en Ubuntu/Linux y macOS usando `--backend sounddevice` o `--backend pyaudio`, `--expected-system Linux` / `--expected-system Darwin`, `--confirm-input-reviewed` y conservar `manual-capture-checklist.md`.
4. Cerrar blockers de beta reportados por `tools\beta_readiness.py` y `BETA_CHECKLIST.md`.
5. Evaluar si el siguiente lote de pilotos permite declarar beta.

## Documentacion

La documentacion HTML principal esta en:

```text
docs/auralisvoicekit-documentacion.html
```

Se puede abrir directamente en el navegador; no requiere servidor local.

La referencia API para usuarios de PyPI esta en:

```text
docs/auralisvoicekit-api.html
```

Tambien hay documentos de soporte:

```text
ROADMAP.md
VERSIONING.md
RELEASE_PROCESS.md
CHANGELOG.md
COMPATIBILITY.md
CONTRIBUTING.md
PYPI.md
PRIVACY.md
CUSTOM_OUTPUT_BACKENDS.md
PILOTS.md
```
