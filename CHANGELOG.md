# Changelog

Todas las notas importantes de AuralisVoiceKit se documentan aqui.

El formato sigue la idea de "Keep a Changelog" y el proyecto usa versionado semantico.

## [Unreleased]

## [0.26.0] - 2026-06-05

### Agregado

- Helper publico `windows_audio_error_hint()` para clasificar errores comunes de captura de audio en Windows.
- Modelo `WindowsAudioErrorHint` con categoria, mensaje, acciones recomendadas, backend, dispositivo y error original.
- `auralis doctor --capture-test` agrega `windows_audio_hint` estructurado cuando falla una captura en Windows.
- Pruebas unitarias para errores de permisos, dispositivo invalido, host API y diagnostico Windows.

### Cambiado

- README, compatibilidad, referencia API, documentacion HTML y roadmap documentan los nuevos mensajes accionables para audio Windows.
- El roadmap mueve la prioridad inmediata a benchmarks exportables a archivo JSON/CSV.

## [0.25.0] - 2026-06-05

### Agregado

- Guia `CUSTOM_OUTPUT_BACKENDS.md` en espanol e ingles para backends de salida personalizados.
- Ejemplo `examples/custom_output_backend.py` con backend de salida en memoria, sin reproducir audio real.
- Automatizacion `tools/stability_gate.py` para medir si el proyecto esta listo para pilotos reales o version estable.
- Paso de CI `Run stability gate` con requisito minimo `pilot`.
- Pruebas automatizadas para el ejemplo custom y el gate de estabilidad.

### Cambiado

- README, referencia API, documentacion HTML y roadmap documentan backends de salida custom y la automatizacion de estabilidad.
- El roadmap mueve la prioridad inmediata a mejorar mensajes especificos para errores comunes de audio en Windows.

## [0.24.0] - 2026-06-05

### Agregado

- Guia `PRIVACY.md` en espanol e ingles para privacidad y manejo de logs.
- Modulo publico `auralis_voicekit.privacy` con `PrivacyLogConfig`, `PrivacyEventLogger`, `sanitize_event_payload()` y `event_to_log_record()`.
- Exportacion JSONL de eventos con payload sanitizado y redaccion de campos sensibles.
- Pruebas unitarias para sanitizacion, conversion de eventos a logs y logger JSONL.

### Cambiado

- README, referencia API, documentacion HTML y roadmap enlazan la nueva guia de privacidad/logs.
- El roadmap mueve la prioridad inmediata a documentar patrones de backends de salida personalizados.

## [0.23.0] - 2026-06-05

### Agregado

- Ejemplo `examples/pypi_quickstart.py` para usuarios de PyPI.
- Flujo de ejemplo sin extras: genera audio sintetico, escribe WAV, segmenta y transcribe con backend `null`.
- Salida `--json` para validar rapidamente la integracion base.
- Pruebas automatizadas para la funcion `run_demo()` y para ejecutar el script como usuario final.

### Cambiado

- README, compatibilidad, documentacion HTML y roadmap enlazan el nuevo ejemplo PyPI.
- El roadmap mueve la prioridad inmediata a una guia de privacidad y manejo de logs.

## [0.22.0] - 2026-06-05

### Agregado

- Modelo `BenchmarkComparisonEntry` para representar una configuracion comparada.
- Modelo `BenchmarkComparisonReport` con ranking por latencia media de transcripcion.
- Helper publico `run_whisper_comparison_benchmarks()` para comparar configuraciones de `faster-whisper` en hardware local.
- CLI `auralis benchmark-whisper` con comparacion de modelos, dispositivos, compute types, beam sizes y salida JSON.
- Limite `--max-combinations` para evitar matrices de benchmark demasiado grandes por accidente.
- Pruebas unitarias para ranking, serializacion, limite de combinaciones y CLI.

### Cambiado

- README, documentacion HTML, referencia API y roadmap documentan los benchmarks comparativos de Whisper.
- El roadmap mueve la prioridad inmediata a preparar un ejemplo pequeno de integracion para usuarios de PyPI.

## [0.21.0] - 2026-06-04

### Agregado

- Modelo `WasapiDiagnosticSnapshot` para inspeccionar el entorno WASAPI sin abrir el microfono.
- Helper `inspect_wasapi_environment()` en `auralis_voicekit.backends`.
- Detalles WASAPI en `auralis doctor --devices --backend wasapi --json`: host APIs, ids WASAPI, dispositivo default, dispositivo seleccionado y conteos de entradas.
- Resumen WASAPI legible en la salida de texto de `auralis doctor`.
- Cobertura de pruebas para snapshot WASAPI, host API faltante y diagnostico `doctor` con `sounddevice` simulado.

### Cambiado

- `auralis doctor --capture-test --backend wasapi` incluye formato solicitado y snapshot WASAPI en sus detalles de exito o error.
- README, compatibilidad, roadmap y documentacion HTML describen el diagnostico WASAPI reforzado.
- El roadmap mueve la prioridad inmediata a benchmarks comparativos opcionales para `whisper` en hardware real.

## [0.20.0] - 2026-06-04

### Agregado

- Modelo `SystemVoice` para representar voces del sistema operativo.
- Metodo `list_voices()` en el backend de salida `system`.
- CLI `auralis voices --backend system` con salida de texto o JSON.
- Configuracion `output_voice`, `output_rate` y `output_volume` en `VoiceKitConfig`.
- Variables de entorno `AURALIS_OUTPUT_VOICE`, `AURALIS_OUTPUT_RATE` y `AURALIS_OUTPUT_VOLUME`.
- Flags `--voice`, `--rate` y `--volume` para `auralis speak`.

### Cambiado

- El backend `system` aplica voz, velocidad y volumen cuando Windows/SAPI, macOS `say`, `spd-say` o `espeak` lo soportan.
- README, roadmap y documentacion HTML describen la configuracion de voces del sistema.
- El roadmap mueve la prioridad inmediata a robustecer WASAPI con pruebas manuales en hardware Windows real.

## [0.19.0] - 2026-06-04

### Agregado

- Pagina `docs/auralisvoicekit-api.html` como referencia API inicial para usuarios de PyPI.
- Documentacion de modelos, configuracion, fachada, utilidades de audio, sesiones, eventos, diagnostico, benchmarks, errores y backends personalizados.
- Prueba de documentacion que verifica que todos los simbolos publicos exportados desde `auralis_voicekit` aparezcan en la referencia API.

### Cambiado

- La metadata `Documentation` de PyPI apunta ahora a la referencia API.
- README y documentacion HTML principal enlazan la nueva pagina API.
- El roadmap marca la documentacion API para PyPI como estado inicial y mueve la prioridad inmediata a configuracion de voces del backend `system`.

## [0.18.0] - 2026-06-04

### Agregado

- Helpers publicos `ffmpeg_install_hint()` y `ffmpeg_search_locations()` para diagnosticar instalaciones de `ffmpeg`.
- Mensajes de error accionables cuando `ffmpeg` falta, no puede ejecutarse, falla al decodificar o no produce audio PCM16.
- Metadata `ffmpeg_executable` en chunks decodificados mediante `ffmpeg`.
- Cobertura de pruebas para `AURALIS_FFMPEG_PATH` invalido, stderr largo, salida vacia, rutas explicitas, `doctor`, `transcribe` y `normalize`.

### Cambiado

- `auralis doctor` ahora incluye detalles de busqueda de `ffmpeg` y sugerencias especificas por sistema operativo.
- El roadmap marca el endurecimiento de errores de `ffmpeg` como estado inicial y mueve la prioridad inmediata a documentacion API para PyPI.

## [0.17.0] - 2026-06-04

### Agregado

- Modulo `benchmarks` con reportes estructurados para latencia offline de captura, segmentacion y transcripcion.
- Generador determinista de audio PCM16 sintetico para medir sin microfono, red ni dependencias externas.
- CLI `auralis benchmark` con salida de texto o JSON.
- Pruebas unitarias para la API publica de benchmarks y el comando CLI.

### Cambiado

- El roadmap marca benchmarks de latencia como estado inicial y mueve la prioridad inmediata a endurecer errores de `ffmpeg`.
- La documentacion incluye comandos para medir la linea base `transcription:null` y backends reales como `whisper` cuando esten instalados.

## [0.16.0] - 2026-06-04

### Agregado

- Backend de captura `wasapi` para Windows, construido sobre el extra opcional `sounddevice`.
- Filtrado de dispositivos por host API WASAPI y seleccion de dispositivo WASAPI por defecto.
- Pruebas unitarias para disponibilidad, filtrado de dispositivos, seleccion default y apertura simulada de stream WASAPI.

### Cambiado

- El roadmap marca WASAPI como backend inicial y mueve la prioridad inmediata a benchmarks de latencia.
- La documentacion ahora muestra `auralis devices --backend wasapi` y configuracion Python con `capture_backend="wasapi"`.

## [0.15.0] - 2026-06-04

### Agregado

- Backend de salida `system` para hablar usando herramientas del sistema operativo.
- Soporte inicial de salida real: Windows con PowerShell/SAPI, macOS con `say`, Ubuntu/Linux con `spd-say` o `espeak`.
- CLI `auralis speak "texto" --backend system` con salida JSON opcional.
- Pruebas unitarias para comandos de salida por sistema, CLI `speak`, eventos de salida y diagnostico.

### Cambiado

- El roadmap marca salida de voz real como estado inicial y mueve la prioridad inmediata a WASAPI dedicado.

## [0.14.0] - 2026-06-04

### Agregado

- Guia `PYPI.md` para publicar en TestPyPI y PyPI con Trusted Publishing.
- Workflow manual `.github/workflows/publish-pypi.yml` para publicar tags existentes sin guardar tokens.
- URLs de proyecto en `pyproject.toml` para mejorar la metadata visible en PyPI.
- Herramientas `build` y `twine` en el extra `dev` para validar artefactos antes de publicar.

### Cambiado

- El proceso de release documenta la ruta GitHub Release -> TestPyPI -> PyPI.
- El roadmap marca la publicacion en PyPI como preparada y mueve la siguiente prioridad a salida de voz real.

## [0.13.0] - 2026-06-04

### Agregado

- Pruebas de integracion reales para FLAC usando `ffmpeg` como herramienta externa opcional.
- Cobertura real de FLAC para `read_audio_as_chunk()`, `read_audio()`, `auralis transcribe --backend null` y `auralis normalize`.
- Documentacion de uso y compatibilidad para MP3/FLAC sin agregar dependencias nativas al paquete base.

### Cambiado

- El roadmap marca FLAC como soporte inicial validado via `ffmpeg` y mueve la prioridad inmediata a la preparacion de publicacion en PyPI.

## [0.12.0] - 2026-06-04

### Agregado

- Pruebas de integracion reales para MP3 que generan un WAV PCM16, lo convierten a MP3 con `ffmpeg` y lo vuelven a decodificar con AuralisVoiceKit.
- Job `compressed-audio` en CI para ejecutar esas pruebas en Windows, Ubuntu/Linux y macOS.
- Cobertura real de MP3 para `read_audio_as_chunk()`, `read_audio()`, `auralis transcribe --backend null` y `auralis normalize`.

### Cambiado

- La prioridad del roadmap pasa de validar MP3 con `ffmpeg` a explorar FLAC, documentacion de PyPI y salida de voz real.

## [0.11.0] - 2026-06-04

### Agregado

- Check bajo demanda `capture-test:<backend>` en `auralis doctor` para probar apertura breve de captura.
- Flags `auralis doctor --capture-test`, `--capture-seconds` y `--device`.
- Detalles JSON del test de captura: backend, dispositivo, duracion solicitada, duracion real, chunks y bytes recibidos.
- Pruebas de diagnostico y CLI para captura `null`, errores de backend e intervalos invalidos.

### Cambiado

- La descripcion publica del repositorio y la metadata del paquete ahora son bilingues: espanol e ingles.
- El roadmap marca el test de apertura de captura como estado inicial y mueve la prioridad siguiente.

## [0.10.0] - 2026-06-04

### Agregado

- `VoiceSession.cancel()` para pedir que los loops activos se detengan de forma ordenada.
- `VoiceSession.reset_cancel()` para reutilizar una sesion cancelada.
- `VoiceSession.close()` y soporte de contexto `with VoiceSession(...)` para detener captura activa al salir.
- Propiedades `VoiceSession.is_cancelled` y `VoiceSession.is_closed`.
- `VoiceSessionConfig.capture_poll_interval_ms` para controlar la rapidez con que una captura despierta ante cancelacion.
- Callbacks `on_turn` y `on_chunk` que pueden devolver `False` para cancelar el flujo actual.
- Parametro `on_chunk` en `VoiceSession.listen_once()`.
- Pruebas de cancelacion por hilo externo, callback, cierre y contexto.

### Cambiado

- `examples/assistant_loop.py` usa cierre con contexto y maneja `KeyboardInterrupt` con salida ordenada.
- Renombrada la documentacion HTML principal de `docs/index.html` a `docs/auralisvoicekit-documentacion.html`.

## [0.9.0] - 2026-06-04

### Agregado

- Backend opcional `whisper` para transcripcion local usando `faster-whisper`.
- Extra `whisper` para instalar dependencias locales de ML sin afectar el paquete base.
- Configuracion `transcription_device`, `transcription_compute_type`, `transcription_beam_size` y `transcription_vad_filter`.
- Variables de entorno `AURALIS_TRANSCRIPTION_DEVICE`, `AURALIS_TRANSCRIPTION_COMPUTE_TYPE`, `AURALIS_TRANSCRIPTION_BEAM_SIZE` y `AURALIS_TRANSCRIPTION_VAD_FILTER`.
- Flags `--device`, `--compute-type`, `--beam-size` y `--vad-filter` en `auralis transcribe` y `auralis transcribe-segments`.
- Check de diagnostico para la dependencia opcional `faster-whisper`.

### Cambiado

- `auralis transcribe` y `auralis transcribe-segments` usan `null` como backend por defecto. OpenAI y Whisper ahora se eligen de forma explicita con `--backend openai` o `--backend whisper`.
- `VoiceKitConfig.transcription_model` usa `auto` por defecto; cada backend real resuelve su modelo interno cuando se selecciona de forma explicita.

## [0.8.0] - 2026-06-04

### Agregado

- Normalizacion PCM16 pura con `apply_gain_pcm16`, `normalize_pcm16` y `normalize_chunks_pcm16`.
- CLI `auralis normalize input output.wav` para generar WAV normalizado desde WAV o MP3.
- Flags `--normalize`, `--target-peak` y `--max-gain` en `auralis transcribe`.
- Normalizacion opcional de segmentos en `VoiceSession` y `auralis transcribe-segments`.
- Ejemplo `examples/normalize_audio.py`.
- Pruebas de ganancia, clipping, normalizacion por chunks, CLI y sesiones.

## [0.7.0] - 2026-06-04

### Agregado

- `VoiceSession`, `VoiceSessionConfig` y `VoiceTurn` para flujos escuchar -> segmentar -> transcribir.
- Metodo `VoiceSession.transcribe_file()` para procesar WAV, MP3 y audio soportado por `ffmpeg`.
- Metodo `VoiceSession.listen_once()` para capturar durante un intervalo y transcribir segmentos.
- CLI `auralis transcribe-segments archivo.wav` con salida de texto o JSON.
- Lectura generica `read_audio_as_chunk()` y `read_audio()` con decodificacion opcional mediante `ffmpeg`.
- Check `executable:ffmpeg` en `auralis doctor`.
- Ejemplo `examples/assistant_loop.py`.
- Pruebas de sesion, callbacks, segmentacion por WAV y CLI.

### Cambiado

- El workflow de release opta por Node 24 para evitar la advertencia de acciones Node 20.

## [0.6.0] - 2026-06-04

### Agregado

- Backend opcional `openai` para transcripcion por API usando WAV PCM16.
- Extra `openai` para instalar el cliente oficial sin afectar el paquete base.
- CLI `auralis transcribe archivo.wav` con salida de texto o JSON.
- Configuracion `transcription_model`, `transcription_prompt` y `transcription_response_format`.
- Variables de entorno `AURALIS_TRANSCRIPTION_MODEL`, `AURALIS_TRANSCRIPTION_PROMPT` y `AURALIS_TRANSCRIPTION_RESPONSE_FORMAT`.
- Helpers `chunk_to_wav_bytes` y `read_wav_as_chunk`.
- Checks de diagnostico para la dependencia opcional `openai`.

## [0.5.0] - 2026-06-04

### Agregado

- Modulo `diagnostics` con `DiagnosticCheck`, `DiagnosticStatus`, `DoctorReport` y `run_doctor`.
- Salida estructurada JSON para `auralis doctor --json`.
- Validacion WAV desde `auralis doctor --wav archivo.wav`.
- Sugerencias por sistema operativo en el diagnostico.
- Checks de dependencias opcionales, backends y dispositivos.

## [0.4.0] - 2026-06-04

### Agregado

- Lectura de WAV PCM16 con `read_wav_metadata`, `iter_wav_chunks` y `read_wav`.
- Metadata `WavMetadata`.
- Backend de captura `wav` para pruebas offline sin microfono.
- Configuracion `input_file` y variable `AURALIS_INPUT_FILE`.
- CLI `auralis wav-info`.
- Ejemplo `examples/segment_wav.py`.

## [0.3.0] - 2026-06-04

### Agregado

- `NoiseProfile`, `VoiceActivityConfig`, `VoiceSegment` y `VoiceActivityDetector`.
- Calibracion de ruido ambiente con `calibrate_noise_pcm16`.
- Segmentacion voz/silencio con `segment_voice_pcm16`.
- Ejemplo `examples/capture_voice_segments.py` para calibrar ruido, grabar y guardar segmentos WAV.
- Publicacion automatica de assets en GitHub Releases desde el workflow de release.

## [0.2.0] - 2026-06-04

### Agregado

- Utilidades puras para energia RMS, pico, silencio y escritura WAV PCM16.
- Ejemplo `examples/capture_microphone.py` para grabar microfono a WAV con `sounddevice`.
- Seleccion de dispositivo de entrada por id, nombre o `default` en el backend `sounddevice`.
- Configuracion `capture_block_ms`, `capture_latency` y calculo `capture_block_frames`.
- Flag CLI `auralis --version`.
- Job experimental de CI para el proximo Python disponible.

### Cambiado

- Se agregaron badges de CI, release, version, Python y licencia al README.
- Se eliminaron referencias internas de la documentacion publica.
- El backend `sounddevice` ahora cierra el stream si falla el inicio y usa blocksize configurable.
- CI usa versiones modernas de acciones oficiales compatibles con Node 24.

## [0.1.0] - 2026-06-04

### Agregado

- Core inicial sin dependencias obligatorias.
- Modelos `AudioFormat`, `AudioChunk`, `AudioDevice` y `TranscriptResult`.
- Configuracion `VoiceKitConfig`.
- Sistema de eventos `EventBus`.
- Backend `null` para captura, transcripcion y salida.
- Scaffold del backend opcional `sounddevice`.
- CLI `auralis doctor` y `auralis backends`.
- README, documentacion HTML y roadmap.
- Politica de versionado.
