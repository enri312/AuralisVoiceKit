# AuralisVoiceKit

[![CI](https://github.com/enri312/AuralisVoiceKit/actions/workflows/ci.yml/badge.svg)](https://github.com/enri312/AuralisVoiceKit/actions/workflows/ci.yml)
[![Release](https://github.com/enri312/AuralisVoiceKit/actions/workflows/release.yml/badge.svg)](https://github.com/enri312/AuralisVoiceKit/actions/workflows/release.yml)
[![Version](https://img.shields.io/github/v/release/enri312/AuralisVoiceKit?include_prereleases&label=version)](https://github.com/enri312/AuralisVoiceKit/releases)
[![Python](https://img.shields.io/badge/python-3.10%2B-3776AB.svg)](https://github.com/enri312/AuralisVoiceKit/blob/main/COMPATIBILITY.md)
[![License](https://img.shields.io/badge/license-MIT-2f855a.svg)](LICENSE)

AuralisVoiceKit es una libreria moderna de voz para Python, pensada primero para Windows y para asistentes personales, agentes locales y herramientas de automatizacion por voz.

English: AuralisVoiceKit is a modern voice toolkit for Python assistants, local agents and voice automation tools.

El objetivo principal es evitar que la captura de microfono dependa obligatoriamente de PyAudio o de wheels que tardan en llegar a las versiones nuevas de Python. El paquete base debe poder instalarse de forma liviana, sin compiladores y sin dependencias nativas obligatorias. Para MP3, FLAC y formatos comprimidos, AuralisVoiceKit usa `ffmpeg` como herramienta externa opcional.

> Estado actual: alpha tecnica con gate de pilotos reales y checklist de beta. El repositorio ya define el core, los contratos de backends, captura real inicial, diagnostico reforzado para WASAPI, bundles de diagnostico sanitizados y analizables, flujo WAV offline, transcripcion inicial por API y local opcional, sesiones de voz iniciales, una CLI de diagnostico, benchmarks offline y comparativos para Whisper exportables a JSON/CSV, errores accionables para `ffmpeg`, mensajes accionables para audio Windows, documentacion estatica, salida de voz del sistema con voces configurables y ejemplo seguro, salida custom en memoria, quickstart para PyPI sin extras, guia de privacidad/logs, ejemplo de asistente local con logs sanitizados, runner de piloto seguro, runner de piloto manual, piloto de transcripcion con scoring redactado, checklist de beta automatizado, pruebas unitarias y pruebas reales de MP3/FLAC. Los backends reales se iran agregando por etapas.

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

Rutas usadas por plataforma:

- Windows: PowerShell con SAPI, listado de voces instaladas, voz, velocidad y volumen.
- macOS: comando `say`, listado de voces, voz y velocidad.
- Ubuntu/Linux: `spd-say` o `espeak`; `espeak` permite voz, velocidad, volumen y listado de voces.

English: the `system` output backend can list voices and select voice/rate/volume when the operating system command supports those options.

El ejemplo `system_output_demo.py` usa dry-run por defecto: registra el comando que se ejecutaria, lista voces simuladas para Windows/macOS/Linux y emite eventos `output.*` sin reproducir audio. Para pilotos con artifacts, `tools/output_pilot.py` escribe JSON y Markdown con el texto redactado en comandos. Para un piloto real que pueda cerrar el blocker beta, usa `--speak --operator-present --confirm-audible` de forma explicita:

```powershell
py examples\system_output_demo.py --speak --text "Hola desde AuralisVoiceKit"
py tools\output_pilot.py --output-dir pilot_runs\output\system-dry-run --json
py tools\output_pilot.py --speak --operator-present --confirm-audible --text "Hola desde AuralisVoiceKit" --json
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
py examples\local_assistant_privacy_demo.py --json
```

`local_assistant_privacy_demo.py` corre offline y sin extras: genera audio sintetico, lo procesa con `VoiceSession`, responde con salida `null` y escribe eventos JSONL con `PrivacyEventLogger`. El payload incluye `privacy_checks` para confirmar que texto, path y token privados fueron redactados del log.

## Diagnostico

`auralis doctor` genera un reporte de compatibilidad del entorno:

```powershell
auralis doctor
auralis doctor --devices --backend wav
auralis doctor --devices --backend sounddevice
auralis doctor --capture-test --backend sounddevice --capture-seconds 0.25
auralis doctor --capture-test --backend sounddevice --device default --json
auralis doctor --capture-test --backend wasapi --device 15 --sample-rate 48000 --json
auralis doctor --wav sample.wav
auralis doctor --json
auralis doctor --devices --backend wasapi --bundle reports/doctor-windows.json
auralis doctor-bundles reports/doctor-windows.json --output reports/doctor-analysis.json --json
```

La salida distingue entre `ok`, `warning` y `error`. Los warnings no bloquean el uso del core; por ejemplo, `sounddevice` puede faltar y aun asi funcionar `null`, `wav`, lectura WAV y utilidades de audio. El flag `--capture-test` intenta abrir brevemente el backend de captura seleccionado y es util para diagnosticar permisos de microfono o errores de dispositivo.

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
| `pyaudio` | pendiente | compatibilidad con proyectos existentes |
| `whisper` | inicial funcional | transcripcion local opcional con faster-whisper |
| `openai` | inicial funcional | transcripcion por API |
| `system` | inicial con voces configurables | salida de voz con herramientas del sistema operativo |

## Uso con asistentes

AuralisVoiceKit puede funcionar como capa de voz para asistentes personales y agentes locales:

- escuchar comandos hablados;
- detectar dispositivos de microfono;
- calibrar ruido ambiente;
- enviar audio a un reconocedor;
- devolver texto limpio a un loop de agente;
- registrar eventos de voz sin exponer datos privados.

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

Hoy el gate exige documentacion clave, privacidad/logs, guia de salida custom, ejemplos, PyPI, referencia API, ejemplo de asistente local con logs sanitizados y CI. Si pasa en etapa `pilot`, ya se puede empezar a probar con microfono real, voces del sistema y transcripcion real controlada antes de pensar en `1.0.0`.

Ruta portable del gate: `tools/stability_gate.py`.

Para evaluar si ya corresponde declarar beta publica, usa el checklist conservador. Por defecto no falla aunque existan blockers; con `--fail-on-blockers` sirve para auditorias estrictas del checklist y con `--fail-on-audit-gaps` convierte la auditoria JSON en gate estricto:

```powershell
py tools\beta_readiness.py --json
py tools\beta_readiness.py --output BETA_CHECKLIST.md
py tools\beta_readiness.py --requirements
py tools\beta_readiness.py --audit-evidence --evidence pilot_runs\manual\linux --json
py tools\beta_readiness.py --audit-evidence --evidence pilot_runs\manual --evidence pilot_runs\output --evidence pilot_runs\transcription --fail-on-audit-gaps --json
py tools\beta_readiness.py --evidence pilot_runs\manual\linux --evidence pilot_runs\output\real --json
py tools\beta_readiness.py --fail-on-blockers --json
```

El checklist generado vive en `BETA_CHECKLIST.md` y separa dos estados: listo para pilotos reales no significa listo para beta. `--requirements` imprime los campos JSON necesarios para cada blocker antes de ejecutar pilotos reales. `--audit-evidence` revisa artifacts reales, resume blockers cerrados/pendientes y explica que campo falta; `--fail-on-audit-gaps` devuelve codigo 1 si todavia faltan blockers o si algun artifact fue ignorado. `--evidence` acepta archivos o carpetas con JSON generados por `tools\manual_pilot.py`, `tools\output_pilot.py` y `tools\transcription_pilot.py`; solo cuenta artifacts con `project: AuralisVoiceKit`, reporta evidencias ignoradas con motivo (`missing_project`, `wrong_project`, `not_json_object`) y usa campos estructurados/nombres de artifacts, no transcripciones ni audio. English: beta readiness requires real pilot evidence, can fail CI on audit gaps, explains ignored artifacts, and never copies private transcripts or audio.

## Pilotos seguros

`tools/pilot_run.py` ejecuta un piloto automatizado sin microfono, sin audio real, sin red y sin modelos. Genera un reporte con el gate, `doctor` usando backend `wav`, el demo de asistente local con logs sanitizados, salida `system` en dry-run, benchmarks offline exportados, `pilot-report.json` y `pilot-plan.md`. El plan incluye evidencias JSON aceptadas/ignoradas, `next_beta_evidence_steps`, `recommended_pilot_sequence` y `platform_pilot_matrix` con comandos separados para Windows, Ubuntu/Linux, macOS, salida audible y transcripcion MP3; si falta transcripcion real, la secuencia inicia con un fixture sintetico publico y sigue con `--preflight-only` para validar el MP3 propio con ffmpeg y guardas de duracion sin ejecutar Whisper/OpenAI. English: the safe pilot can ingest JSON evidence and produce a public-safe Markdown plan for accepted evidence, ignored artifacts, an ordered real-pilot sequence and a platform matrix.

```powershell
py tools\pilot_run.py --output-dir pilot_runs\safe --json
py tools\pilot_run.py --output-dir pilot_runs\safe --evidence pilot_runs\manual --evidence pilot_runs\output --evidence pilot_runs\transcription --json
```

`tools/manual_pilot.py` genera bundle doctor, analisis `doctor-bundles` y Markdown de hallazgos. Por defecto no abre microfono; para un piloto real de captura se debe pasar `--capture-test` de forma explicita:

```powershell
py tools\manual_pilot.py --output-dir pilot_runs\manual\windows-safe --json
py tools\manual_pilot.py --capture-test --backend wasapi --device default --sample-rate 48000 --json
```

`tools/output_pilot.py` prepara pilotos de salida `system`. Por defecto es dry-run y no reproduce audio; con `--speak --operator-present --confirm-audible` usa voz real del sistema y registra artifacts sanitizados que pueden cerrar el blocker beta:

```powershell
py tools\output_pilot.py --output-dir pilot_runs\output\system-dry-run --json
py tools\output_pilot.py --speak --operator-present --confirm-audible --text "Hola desde AuralisVoiceKit" --json
```

`tools/pilot_audio_fixture.py` genera WAV/MP3/FLAC sinteticos publicos para ensayar ffmpeg antes de usar audio privado; con `--run-preflight` tambien ejecuta un preflight seguro contra el MP3 generado y no cuenta como evidencia beta. `tools/transcription_pilot.py` prepara pilotos de transcripcion. Por defecto genera audio sintetico y usa backend `null`; con `--preflight-only` decodifica un archivo propio no sensible (por ejemplo MP3) y escribe metadata sanitizada sin ejecutar Whisper/OpenAI. `--min-audio-seconds` y `--max-audio-seconds` validan la duracion decodificada antes de continuar, util para rechazar archivos vacios o demasiado largos. Para `whisper` u `openai` exige `--real-transcription`, un archivo `--audio` y confirmacion `--audio-non-sensitive`. El texto transcrito queda redactado en los artifacts. Si agregas `--expected-text` o `--expected-text-file`, calcula metricas de calidad como word accuracy y word error rate sin guardar la transcripcion ni el texto esperado:

```powershell
py tools\transcription_pilot.py --output-dir pilot_runs\transcription\safe --json
py tools\transcription_pilot.py --output-dir pilot_runs\transcription\quality-safe --expected-text "Hola desde AuralisVoiceKit" --min-word-accuracy 0 --json
py tools\pilot_audio_fixture.py --output-dir pilot_runs\transcription\fixture --format wav --format mp3 --run-preflight --json
py tools\transcription_pilot.py --preflight-only --audio sample.mp3 --audio-non-sensitive --backend whisper --normalize --min-audio-seconds 0.2 --max-audio-seconds 60 --json
py tools\transcription_pilot.py --real-transcription --audio sample.mp3 --audio-non-sensitive --backend whisper --model base --normalize --expected-text "Hola desde AuralisVoiceKit" --min-word-accuracy 0.75 --min-audio-seconds 0.2 --max-audio-seconds 60 --json
```

`tools/beta_readiness.py` resume blockers de beta a partir del gate, `PILOT_FINDINGS.md` y artifacts JSON pasados con `--evidence`. Hoy marca como pendientes la transcripcion real con calidad, salida `system` audible confirmada, captura Ubuntu/Linux y captura macOS.

Los pasos con hardware quedan documentados en:

```text
PILOTS.md
PILOT_FINDINGS.md
BETA_CHECKLIST.md
```

## Roadmap

El roadmap completo esta en:

```text
ROADMAP.md
```

Prioridad inmediata:

1. Ejecutar piloto de transcripcion real con audio propio no sensible usando `tools\transcription_pilot.py --real-transcription --audio ... --audio-non-sensitive --expected-text ... --min-word-accuracy 0.75 --min-audio-seconds 0.2 --max-audio-seconds 60`.
2. Ejecutar piloto manual de salida `system` con `tools\output_pilot.py --speak --operator-present --confirm-audible`.
3. Repetir captura con microfono en Ubuntu/Linux y macOS.
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
