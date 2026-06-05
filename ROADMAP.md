# Roadmap de AuralisVoiceKit

Este roadmap define como convertir AuralisVoiceKit en una libreria completa de voz para Python moderno, con Windows como primera plataforma y con compatibilidad futura como principio central.

## Norte del proyecto

AuralisVoiceKit debe permitir crear asistentes de voz sin depender obligatoriamente de PyAudio, sin bloquear versiones nuevas de Python y sin obligar al usuario a instalar compiladores para probar el paquete base.

La meta no es competir con todos los motores de voz a la vez. La meta es construir una capa clara, extensible y confiable que conecte captura, transcripcion, eventos y salida de audio.

## Reglas de compatibilidad

- El core debe seguir sin dependencias externas obligatorias.
- No se debe agregar un limite superior artificial de Python salvo que exista una incompatibilidad real.
- Cada backend nativo debe vivir en un extra opcional.
- Si un backend no esta instalado, la libreria debe explicar que falta sin romper el import principal.
- Las pruebas deben correr en la version actual de Python y en la siguiente version disponible o prerelease cuando sea viable.
- La API publica debe cambiar poco y con motivos claros.

## Estado actual

| Area | Estado |
| --- | --- |
| Core Python | Inicial funcional |
| Modelos de audio | Inicial |
| Eventos | Inicial |
| Sesiones de voz | Inicial funcional con cancelacion |
| CLI `doctor` | Inicial con test de captura |
| Backend `null` | Funcional |
| Backend `wav` | Inicial funcional |
| Backend `sounddevice` | Inicial funcional |
| Backend `wasapi` | Inicial con diagnostico reforzado |
| Utilidades de audio | Normalizacion, calibracion y segmentacion inicial |
| Versionado | Politica inicial |
| Compatibilidad Windows/Linux/macOS | Documentacion inicial |
| Diagnostico doctor | Inicial estructurado con test de apertura, bundle sanitizado y analisis de bundles |
| Transcripcion real | Inicial por API y local opcional |
| Salida de voz real | Inicial con backend `system`, listado de voces, parametros de voz y ejemplo seguro |
| CI multiplataforma | Inicial con pruebas reales de MP3 y FLAC |
| Publicacion en PyPI | Preparada con workflow manual |
| Benchmarks de latencia | Inicial offline, comparativo para Whisper y exportacion JSON/CSV |
| Errores de ffmpeg | Inicial con diagnostico accionable |
| Documentacion API | Inicial para usuarios de PyPI |
| Ejemplos para PyPI | Quickstart inicial sin extras |
| Privacidad y logs | Guia inicial y exportacion JSONL sanitizada |
| Asistente local con privacidad | Ejemplo offline inicial con logs sanitizados |
| Backends de salida custom | Guia inicial y ejemplo en memoria |
| Automatizacion de estabilidad | Gate inicial para pilotos reales |
| Pilotos seguros | Runner automatizado, piloto manual guiado, piloto de salida system, runbook, bundle doctor y analisis de bundles |
| Mensajes Windows audio | Helper inicial para errores comunes |

## Fase 0 - Base del proyecto

**Objetivo:** dejar una libreria instalable, importable y testeable.

Entregables:

- `pyproject.toml` con paquete editable.
- `src/auralis_voicekit` como estructura principal.
- Modelos `AudioFormat`, `AudioChunk`, `AudioDevice` y `TranscriptResult`.
- `VoiceKitConfig` con configuracion por defecto y variables de entorno.
- `EventBus` para eventos internos.
- Backend `null` para pruebas sin hardware.
- CLI `auralis doctor`.
- Tests unitarios basicos.

Criterio de salida:

- `python -m unittest discover -s tests` pasa.
- `python -m auralis_voicekit.cli doctor` corre sin instalar extras.
- `python -m auralis_voicekit.cli doctor --bundle reports/doctor.json` genera un reporte sanitizado.
- `python -m auralis_voicekit.cli doctor-bundles reports/doctor.json --json` resume hallazgos de pilotos.
- `python tools/manual_pilot.py --json` genera artifacts de piloto manual sin abrir microfono por defecto.
- `import auralis_voicekit` no intenta cargar backends nativos.

Estado: completada para la base inicial.

## Fase 1 - Captura real de microfono

**Objetivo:** grabar audio real sin PyAudio obligatorio.

Entregables:

- Backend `sounddevice` funcional para captura PCM16. Estado: inicial.
- Backend `wasapi` funcional para captura Windows con host API WASAPI. Estado: inicial con diagnostico reforzado.
- Enumeracion de dispositivos de entrada. Estado: inicial.
- Seleccion de dispositivo por id, nombre o default. Estado: inicial.
- Start/stop robusto sin dejar streams abiertos. Estado: inicial.
- Eventos `capture.started`, `audio.chunk`, `capture.stopped` con payload seguro.
- Ejemplo `examples/capture_microphone.py`. Estado: creado.
- Snapshot de diagnostico WASAPI con host APIs, default y dispositivo seleccionado. Estado: inicial.
- Bundle de diagnostico sanitizado para pilotos y reportes de bugs. Estado: inicial con `auralis doctor --bundle`.
- Analisis de bundles doctor para agrupar sistemas, checks, categorias y prioridades. Estado: inicial con `auralis doctor-bundles`.
- Tests con mocks para no depender de hardware. Estado: inicial.

Criterio de salida:

- El usuario puede grabar chunks de audio desde un microfono en Windows.
- Si `sounddevice` no esta instalado, el error recomienda el extra correcto.
- La captura no registra bytes de audio en eventos cuando `privacy_mode=True`.

## Fase 2 - Utilidades de audio

**Objetivo:** dar herramientas basicas para preparar audio antes de transcribir.

Entregables:

- Calculo de RMS y nivel de energia. Estado: inicial.
- Calibracion de ruido ambiente. Estado: inicial.
- Deteccion simple de silencio. Estado: inicial.
- Segmentacion por voz/silencio. Estado: inicial.
- Normalizacion basica de volumen. Estado: inicial.
- Guardado opcional a WAV para depuracion. Estado: inicial.

Criterio de salida:

- Se puede escuchar, calibrar y segmentar una frase corta sin transcriptor real.
- Las utilidades trabajan con `AudioChunk` y no fuerzan dependencias externas.

## Fase 3 - Transcripcion

**Objetivo:** convertir audio en texto mediante backends intercambiables.

Entregables:

- Contrato estable para transcriptores.
- Backend local inicial con Whisper/faster-whisper como extra opcional. Estado: inicial con `whisper`.
- Backend por API como extra opcional. Estado: inicial con `openai`.
- Resultado con texto, idioma, confianza aproximada y metadatos.
- Eventos `transcription.started` y `transcription.completed`.
- Manejo claro de errores y timeouts.

Criterio de salida:

- El usuario puede transcribir un archivo WAV o un chunk capturado.
- El core sigue instalando sin dependencias de transcripcion.
- El texto transcrito no aparece en eventos si `privacy_mode=True`.

## Fase 4 - Salida de voz y audio

**Objetivo:** permitir respuestas habladas y eventos de salida.

Entregables:

- Contrato estable para salida de voz.
- Backend `null` para pruebas.
- Backend `system` inicial para TTS local por sistema operativo. Estado: inicial.
- Listado de voces disponibles en Windows, macOS y Linux con `espeak`. Estado: inicial.
- Seleccion de voz, velocidad y volumen cuando el comando del sistema lo soporta. Estado: inicial.
- Guia de backends de salida personalizados. Estado: inicial con `CUSTOM_OUTPUT_BACKENDS.md`.
- Ejemplo de backend de salida en memoria. Estado: inicial con `examples/custom_output_backend.py`.
- Ejemplo seguro de salida `system` con dry-run y piloto real opt-in. Estado: inicial con `examples/system_output_demo.py`.
- Backend Windows inicial para TTS local si es viable. Estado: inicial via PowerShell/SAPI.
- Backend por API como extra opcional.
- Cola simple de reproduccion.
- Eventos `output.started` y `output.completed`. Estado: inicial.

Criterio de salida:

- Un asistente puede llamar `kit.speak("texto")` sin conocer el backend. Estado: inicial.
- El usuario puede inspeccionar voces con `auralis voices --backend system`. Estado: inicial.
- El backend de salida puede reemplazarse por uno custom.

## Fase 5 - Loop de asistente

**Objetivo:** ofrecer un flujo completo escuchar -> transcribir -> responder.

Entregables:

- API de alto nivel para sesiones de voz. Estado: inicial con `VoiceSession`.
- Hooks para wake word o activacion externa.
- Integracion limpia con loops de agente externos.
- Ejemplo `examples/assistant_loop.py`. Estado: creado.
- Ejemplo local offline con logs sanitizados. Estado: inicial con `examples/local_assistant_privacy_demo.py`.
- Cancelacion y cierre ordenado. Estado: inicial.

Criterio de salida:

- Un asistente puede recibir texto limpio desde voz con pocas lineas de codigo.
- El loop puede detenerse sin procesos colgados ni streams abiertos.

## Fase 6 - Windows primero

**Objetivo:** pulir la experiencia real en Windows.

Entregables:

- Mejor diagnostico de permisos de microfono. Estado: inicial con sugerencias por OS y test de apertura bajo demanda.
- Mejor reporte de dispositivos y host APIs. Estado: inicial con snapshot WASAPI.
- Investigacion de backend WASAPI dedicado. Estado: inicial.
- Mensajes especificos para errores comunes de audio en Windows. Estado: inicial con `windows_audio_error_hint()`.
- Guia de instalacion para PowerShell.

Criterio de salida:

- `auralis doctor` ayuda a diagnosticar microfono, backend, host APIs y permisos. Estado: inicial con `--capture-test` y snapshot WASAPI.
- La documentacion explica claramente que hacer cuando no hay audio.

## Fase 7 - Calidad, CI y empaquetado

**Objetivo:** preparar la libreria para publicacion.

Entregables:

- Tests unitarios y de integracion con mocks.
- Linting y formateo.
- CI para Windows, Ubuntu/Linux y macOS.
- Matriz de Python estable y prerelease.
- Pruebas reales de MP3 y FLAC con `ffmpeg` en Windows, Ubuntu/Linux y macOS. Estado: inicial.
- Benchmarks basicos de latencia para captura offline, segmentacion y transcripcion. Estado: inicial con exportacion JSON/CSV.
- Benchmarks comparativos opcionales para Whisper/faster-whisper en hardware local. Estado: inicial con exportacion JSON/CSV.
- Mensajes accionables cuando `ffmpeg` falta, falla o no produce audio. Estado: inicial.
- Build de wheel y sdist.
- Versionado semantico.
- Licencia y metadata final.
- Workflow manual para TestPyPI/PyPI con Trusted Publishing. Estado: inicial.
- Gate de estabilidad para CI. Estado: inicial con `tools/stability_gate.py`.
- Runner de piloto automatizado seguro. Estado: inicial con `tools/pilot_run.py`.
- Runner de piloto manual guiado. Estado: inicial con `tools/manual_pilot.py`, sin captura real salvo `--capture-test`.

Criterio de salida:

- La libreria se puede publicar en PyPI.
- El paquete base se instala limpio con `pip install auralisvoicekit`.

## Fase 8 - Beta publica

**Objetivo:** validar la libreria con proyectos reales.

Entregables:

- Documentacion de API estable.
- Referencia API HTML para usuarios de PyPI. Estado: inicial.
- Ejemplo pequeno de integracion para usuarios de PyPI. Estado: inicial con `examples/pypi_quickstart.py`.
- Guias de captura, transcripcion, salida y privacidad. Privacidad/logs: guia inicial con `PRIVACY.md`.
- Ejemplos completos.
- Integracion piloto con un asistente local de referencia.
- Politica de compatibilidad y cambios.
- Checklist de bugs conocidos.

Criterio de salida:

- AuralisVoiceKit puede usarse en un asistente real sin depender de hacks locales.
- Hay una ruta clara hacia `1.0.0`.

## Fase 9 - Version 1.0

**Objetivo:** declarar una API estable para asistentes de voz.

Entregables:

- API publica congelada para `1.x`.
- Backends principales documentados.
- Tests de regresion para flujos clave.
- Documentacion completa.
- Publicacion en PyPI.
- Integracion estable con asistentes locales y agentes externos.

Criterio de salida:

- Instalar, diagnosticar, capturar, transcribir y emitir eventos funciona de forma predecible.
- Los cambios futuros pueden agregarse sin romper usuarios existentes.

## Backlog tecnico

- Backend WASAPI dedicado. Estado: inicial sobre `sounddevice` con diagnostico reforzado.
- Backend PyAudio solo como compatibilidad opcional.
- Backend de salida `system`. Estado: inicial con listado de voces, seleccion de voz, velocidad, volumen y ejemplo seguro.
- Soporte para archivos WAV/FLAC como entrada. WAV PCM16 completado; FLAC inicial validado via `ffmpeg`.
- Adaptadores para modelos locales. Whisper inicial completado.
- Adaptadores para APIs externas. OpenAI inicial completado.
- Decodificacion MP3/FLAC mediante `ffmpeg` externo opcional. Estado: inicial con pruebas CI multiplataforma y errores accionables.
- Normalizacion de volumen PCM16. Estado: inicial.
- Wake word externo.
- Medidor de energia en tiempo real.
- Grabacion temporal con borrado seguro.
- Exportacion de logs sin contenido sensible. Estado: inicial con `PrivacyEventLogger`.
- Benchmarks de latencia. Estado: inicial offline, comparativo para Whisper y exportacion JSON/CSV.
- Publicacion en PyPI. Estado: workflow y guia inicial.
- Ejemplo PyPI sin extras. Estado: inicial.
- Ejemplo de asistente local con logs sanitizados. Estado: inicial con `examples/local_assistant_privacy_demo.py`.
- Backends de salida personalizados. Estado: guia y ejemplo inicial.
- Automatizacion de estabilidad. Estado: gate inicial listo para CI y uso local.
- Pilotos seguros. Estado: runner automatizado, piloto manual guiado con `tools/manual_pilot.py`, piloto de salida `system` con `tools/output_pilot.py`, runbook inicial con `PILOTS.md`, hallazgos en `PILOT_FINDINGS.md`, bundles `doctor` sanitizados, analisis `doctor-bundles`, control explicito de sample rate para pilotos WASAPI, primera captura Windows real aprobada a 48000 Hz y dry-run Windows de salida `system` aprobado.
- Mensajes Windows audio. Estado: inicial para permisos, dispositivo, sample rate, canales y host API.
- Ejemplo de salida `system`. Estado: inicial con dry-run aprobado, `--speak` para pilotos reales y runner `tools/output_pilot.py`.

## Prioridad inmediata

1. Ejecutar piloto manual de salida `system` con `tools/output_pilot.py --speak` y operador presente.
2. Ejecutar piloto de transcripcion real con audio propio no sensible.
3. Repetir captura con microfono en Ubuntu/Linux y macOS.
4. Preparar checklist de bugs conocidos para beta publica.
5. Evaluar si el siguiente lote de pilotos permite declarar beta.
