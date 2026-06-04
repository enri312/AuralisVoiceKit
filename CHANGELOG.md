# Changelog

Todas las notas importantes de AuralisVoiceKit se documentan aqui.

El formato sigue la idea de "Keep a Changelog" y el proyecto usa versionado semantico.

## [Unreleased]

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
