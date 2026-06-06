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
| Backend `pyaudio` | Inicial funcional como compatibilidad opcional |
| Utilidades de audio | Normalizacion, calibracion y segmentacion inicial |
| Versionado | Politica inicial |
| Compatibilidad Windows/Linux/macOS | Documentacion inicial |
| Diagnostico doctor | Inicial estructurado con test de apertura, bundle sanitizado y analisis de bundles |
| Transcripcion real | Inicial por API y local opcional |
| Salida de voz real | Inicial con backend `system`, listado de voces, parametros de voz, cola simple de salida y ejemplo seguro |
| CI multiplataforma | Inicial con pruebas reales de MP3/FLAC, runner Windows 2025 VS2026 explicito y pip sin cache |
| Publicacion en PyPI | Preparada con workflow manual |
| Benchmarks de latencia | Inicial offline, comparativo para Whisper y exportacion JSON/CSV |
| Errores de ffmpeg | Inicial con diagnostico accionable |
| Documentacion API | Inicial para usuarios de PyPI |
| Ejemplos para PyPI | Quickstart inicial sin extras |
| Privacidad y logs | Guia inicial y exportacion JSONL sanitizada |
| Asistente local con privacidad | Ejemplo offline inicial con logs sanitizados |
| Backends de salida custom | Guia inicial y ejemplo en memoria |
| Automatizacion de estabilidad | Gate inicial para pilotos reales |
| Pilotos seguros | Runner automatizado, piloto manual guiado con checklist de captura, command card de captura y revision confirmada de entrada, piloto de salida system con checklist de operador, guard de plataforma, readiness por sistema operativo, scan de privacidad del texto hablado y revision de voz, piloto de transcripcion con checklist de revision, plan de instalacion de backend, comando dedicado de MP3/WAV/FLAC real y confirmacion humana de calidad, command pack por plataforma, checklist de entorno local, runbook, bundle doctor, analisis de bundles y checklist de beta |
| Mensajes Windows audio | Helper inicial para errores comunes |

Nota `v0.105.0`: el piloto seguro ya separa la ruta generica y la ruta OpenAI en tarjetas, matriz y command pack, con plantilla OpenAI segura (`--preflight-backend openai`, `gpt-4o-mini-transcribe`, timeout 30) sin red ni modelos durante preflight.

Nota `v0.106.0`: el piloto de transcripcion agrega `--require-openai-api-key` para OpenAI y solo registra presencia de `OPENAI_API_KEY` mediante `credentials.openai_api_key_present`, manteniendo `credentials.records_openai_api_key=false`.

Nota `v0.107.0`: el auditor beta ahora exige esos campos sanitizados de credencial cuando la evidencia real declara `target_backend.name=openai`, sin aceptar ni registrar el valor de `OPENAI_API_KEY`.

Nota `v0.108.0`: el piloto seguro propaga los `conditional_required_fields` del contrato beta a la secuencia recomendada, manifiesto de evidencias, handoff y command pack, incluyendo `credentials.checked` para la ruta OpenAI.

Nota `v0.109.0`: el auditor beta reporta evidencias aceptadas/ignoradas con rutas relativas seguras al lote `--evidence`, evitando rutas absolutas y distinguiendo artifacts repetidos por plataforma.

Nota `v0.110.0`: la auditoria de evidencias agrega `blocker_summaries` y un resumen por blocker con candidato mas cercano y campos faltantes, para orientar el siguiente piloto real sin inspeccionar cada JSON manualmente.

Nota `v0.111.0`: el piloto seguro propaga esos `blocker_summaries` a `pilot-report.json`, `pilot-plan.md` y `real-pilot-evidence-manifest.md`, manteniendo fuentes relativas y campos faltantes publicos.

Nota `v0.112.0`: la auditoria beta y el piloto seguro agregan `next_evidence_focus` para apuntar al primer blocker beta activo, con comando base, campos faltantes y candidato mas cercano publicos.

Nota `v0.113.0`: el piloto seguro genera `real-pilot-next-evidence-focus.md`, una tarjeta publica dedicada al siguiente foco de evidencia antes de tocar hardware, audio o texto real.

Nota `v0.114.0`: `real-pilot-next-evidence-focus.md` ahora incluye una secuencia de preparacion derivada de `recommended_pilot_sequence`, para ejecutar primero los pasos seguros previos al piloto real enfocado.

Nota `v0.115.0`: el piloto de transcripcion agrega `preflight_readiness` para resumir si el preflight esta listo para modelo real, bloqueado, pendiente de instalacion de backend o pendiente de repeticion, con comando sanitizado para repetirlo.

Nota `v0.116.0`: el contrato beta y la auditoria de evidencias ahora requieren `preflight_readiness.status=ready` y flags publicos de privacidad antes de aceptar evidencia de transcripcion real.

Nota `v0.117.0`: el fixture sintetico propaga `preflight_readiness` al reporte principal del fixture para que el operador vea si el backend real falta, si debe repetir preflight o si ya esta listo para modelo.

Nota `v0.118.0`: el piloto real de transcripcion con guard estricto conserva `preflight_readiness.status=ready` cuando los checks previos al modelo pasan, cerrando la ruta tecnica para que `real_transcription_quality` pueda cumplir el contrato beta.

Nota `v0.119.0`: el piloto de transcripcion ahora expone `beta_evidence_gap` con faltantes y siguiente accion segura, reduciendo el trabajo manual para cerrar `real_transcription_quality` con un MP3 propio.

Nota `v0.120.0`: el piloto de transcripcion genera `real-transcription-command.md` con comandos seguros de preflight, corrida real y auditoria beta; el preflight recomendado ahora incluye guardas de duracion, revision de audio y guard estricto de backend.

Nota `v0.121.0`: el piloto de salida `system` expone `beta_evidence_gap` para `system_output_audible`, con campos faltantes y siguiente accion segura sin guardar texto hablado, identidad del operador ni rutas locales.

Nota `v0.122.0`: el piloto manual de captura expone `beta_evidence_gap` para Windows/WASAPI, Ubuntu/Linux y macOS, con campos faltantes y siguiente accion segura sin guardar audio, nombres de dispositivos ni rutas locales.

Nota `v0.123.0`: el piloto manual de captura genera `manual-capture-command.md`, una tarjeta publica con setup, preflight sin microfono, captura real y auditoria beta usando placeholders.

Nota `v0.124.0`: la evidencia beta de captura requiere `manual_capture_command_card` segura, con placeholders y flags que prueban que no guarda audio, bytes, nombres de dispositivos ni rutas locales.

Nota `v0.125.0`: la evidencia beta de salida audible requiere `system_output_command_card` segura, con placeholders, preflight sin audio, operador obligatorio para salida real y flags que prueban que no guarda audio, texto hablado, identidad del operador ni rutas locales.

Nota `v0.126.0`: la evidencia beta de transcripcion real requiere `real_transcription_command_card` segura, con placeholders, preflight sin modelo, audio real y revision humana de calidad obligatorios y flags que prueban que no guarda audio, rutas, transcripciones, texto esperado ni nombres de archivos.

Nota `v0.127.0`: la auditoria de evidencias beta agrega `privacy_audit`, que bloquea beta si artifacts JSON aceptados contienen campos crudos sospechosos y reporta solo rutas de campos, no valores privados.

Nota `v0.128.0`: el piloto seguro propaga `privacy_audit` a `pilot-report.json`, `pilot-plan.md`, `real-pilot-evidence-manifest.md` y `real-pilot-decision-gate.md`, manteniendo beta bloqueada si aparecen campos crudos aunque los blockers funcionales esten cerrados por JSON.

Nota `v0.129.0`: los hallazgos de `privacy_audit` ahora incluyen `action_es`, `action_en` y `safe_replacement`, para que el operador sepa como reemplazar texto, rutas, nombres o credenciales crudas por placeholders sin ver ni compartir valores privados.

Nota `v0.130.0`: `privacy_remediation_plan` agrupa esos hallazgos en pasos ordenados por artifact y campo, con `safe_to_share=true` y `records_private_values=false`, y el piloto seguro lo muestra en el plan, manifiesto y compuerta go/no-go.

Nota `v0.131.0`: `tools/pilot_run.py` genera `real-pilot-hard-stop-card.md`, una tarjeta publica con condiciones de alto, acciones minimas y politica de contenido antes de tocar hardware, audio real o flags `--confirm-*`.

Nota `v0.132.0`: `tools/pilot_run.py` genera `real-pilot-evidence-intake-card.md`, una tarjeta publica para ubicar reportes JSON reales sanitizados, ejecutar la auditoria estricta y refrescar el checklist beta sin copiar contenido privado.

Nota `v0.133.0`: `tools/pilot_run.py` genera `real-pilot-execution-card.md`, una tarjeta publica para ejecutar el siguiente piloto real en orden, revisar confirmaciones humanas y cerrar con auditoria estricta antes de refrescar beta.

Nota `v0.134.0`: `real_pilot_execution_card.operator_gate` agrega decision `ready_for_local_operator|blocked`, revisiones previas, confirmaciones humanas, guard backend estricto, artifact JSON esperado y cierre de auditoria para que el siguiente piloto real se ejecute solo con operador local y evidencia sanitizada.

Nota `v0.135.0`: `operator_gate.command_audit` valida flags obligatorios del comando local (`--expected-system`, confirmaciones humanas y guards estrictos) antes de permitir copiarlo para el siguiente piloto real.

Nota `v0.136.0`: `operator_gate.evidence_contract` agrega el contrato publico de evidencia beta del foco activo, con artifact esperado, campos requeridos/faltantes, condicionales, directorios de ingesta y auditoria/refresco.

Nota `v0.137.0`: `tools/manual_pilot.py` agrega `capture_operator_gate` para declarar si la captura manual esta lista para auditoria beta o bloqueada por confirmaciones humanas, guard de backend, plataforma esperada o evidencia faltante.

Nota `v0.138.0`: `tools/beta_readiness.py` incorpora `capture_operator_gate` al contrato de evidencia beta de captura, bloqueando reportes manuales que no declaren `ready_for_beta_audit`.

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
- Backend `pyaudio` funcional para compatibilidad con proyectos existentes. Estado: inicial como extra opcional sin import obligatorio.
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
- Manejo claro de errores y timeouts. Estado: inicial con `transcription_timeout_seconds`, `AURALIS_TRANSCRIPTION_TIMEOUT_SECONDS`, `--timeout-seconds` en CLI y piloto de transcripcion, timeout aplicado al backend `openai` y plantilla segura con timeout OpenAI por defecto.

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
- Cola simple de reproduccion. Estado: inicial con `queue_speech()`, `queue_speech_many()`, `drain_output_queue()`, `clear_output_queue()` y `output_queue_size`.
- Eventos `output.started` y `output.completed`. Estado: inicial.

Criterio de salida:

- Un asistente puede llamar `kit.speak("texto")` sin conocer el backend. Estado: inicial.
- El usuario puede inspeccionar voces con `auralis voices --backend system`. Estado: inicial.
- El backend de salida puede reemplazarse por uno custom.

## Fase 5 - Loop de asistente

**Objetivo:** ofrecer un flujo completo escuchar -> transcribir -> responder.

Entregables:

- API de alto nivel para sesiones de voz. Estado: inicial con `VoiceSession`.
- Hooks para wake word o activacion externa. Estado: inicial con `activation_phrases`, `require_activation`, `activation_hook` y `turn_is_activated()`.
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
- CI para Windows, Ubuntu/Linux y macOS. Estado: Windows usa `windows-2025-vs2026` explicito para anticipar la migracion de GitHub Actions y pip cache queda desactivado para evitar warnings de cache del runner.
- Matriz de Python estable y prerelease.
- Pruebas reales de MP3 y FLAC con `ffmpeg` en Windows, Ubuntu/Linux y macOS. Estado: inicial.
- Benchmarks basicos de latencia para captura offline, segmentacion y transcripcion. Estado: inicial con exportacion JSON/CSV.
- Benchmarks comparativos opcionales para Whisper/faster-whisper en hardware local. Estado: inicial con exportacion JSON/CSV.
- Mensajes accionables cuando `ffmpeg` falta, falla o no produce audio. Estado: inicial.
- Build de wheel y sdist.
- Versionado semantico.
- Licencia y metadata final.
- Workflow manual para TestPyPI/PyPI con Trusted Publishing. Estado: inicial.
- Gate de estabilidad para CI. Estado: inicial con `tools/stability_gate.py` y workflow de release verificado con `actions/upload-artifact@v7.0.1`.
- Runner de piloto automatizado seguro. Estado: inicial con `tools/pilot_run.py`.
- Runner de piloto manual guiado. Estado: inicial con `tools/manual_pilot.py`, `manual-capture-checklist.md`, `manual-capture-command.md`, `manual_capture_command_card`, `capture_checklist`, `target_capture_backend`, `capture_backend_ready_required`, `capture_readiness_plan`, `beta_evidence_gap`, `--target-system` para preparar Ubuntu/Linux o macOS sin abrir microfono, setup PortAudio por sistema, `post_install_check` sin microfono, guard `--require-capture-backend-ready`, `system_guard`, `--expected-system`, `--confirm-input-reviewed`, `input_review_confirmed`, redaccion de selector de dispositivo y sin captura real salvo `--capture-test`.

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
- Checklist de bugs conocidos. Estado: inicial con `tools/beta_readiness.py`, `BETA_CHECKLIST.md`, `BETA_EVIDENCE_REQUIREMENTS.md`, ingesta de evidencias JSON con `--evidence`, requisitos de evidencias con `--requirements`, auditoria de artifacts con `--audit-evidence`, fallo estricto con `--fail-on-audit-gaps`, resumen de blockers cerrados/pendientes por evidencia, validacion de `project: AuralisVoiceKit`, checklist de captura real con `input_review_confirmed` y `capture_backend=sounddevice|pyaudio` para Ubuntu/Linux y macOS, checklist de revision para transcripcion real con `target_backend.available=true`, `target_backend_ready_required=true`, `audio.generated_synthetic_audio=false`, `audio.audio_confirmed_non_sensitive=true`, `audio.decoded=true`, `audio.audio_file_name_redacted`, `audio.duration_gate.enabled`, `audio.duration_gate.passed`, `transcript.text_redacted=true`, `audio_review_confirmed`, `reference_review_confirmed`, `reference_privacy_scan.passed`, `transcription_checklist.records_audio_file_name=false`, `transcription_checklist.records_expected_text_file_name=false`, `transcription_checklist.redacts_transcript_text=true`, `transcription_checklist.redacts_expected_text=true` y `quality_review_confirmed`, checklist de operador para salida audible con `target_output_backend.available=true`, `output_backend_ready_required=true`, `text_review_confirmed`, `spoken_text_privacy_scan.passed`, `voice_review_confirmed`, `operator_checklist.redacts_spoken_text=true`, `operator_checklist.records_operator_identity=false`, `operator_checklist.commands_available=true`, `operator_checklist.ready_for_real_audio=true` y `next_system_output.records_spoken_text=false`, guard `system_guard.expected_system_matched` para salida audible y motivos seguros para evidencias ignoradas.

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
- Backend PyAudio solo como compatibilidad opcional. Estado: inicial funcional con carga perezosa y tests sin hardware.
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
- Pilotos seguros. Estado: runner automatizado, piloto manual guiado con `tools/manual_pilot.py`, artifact `manual-capture-checklist.md`, artifact `manual-capture-command.md`, `manual_capture_command_card`, `target_capture_backend`, `capture_backend_ready_required`, `capture_readiness_plan`, `--target-system`, setup PortAudio para Ubuntu/Linux y macOS, `post_install_check` sin microfono, guard `--require-capture-backend-ready`, guard `--expected-system`, guard `--confirm-input-reviewed`, requisito `system_guard.expected_system_matched`, requisito `capture_backend=sounddevice|pyaudio` para captura Ubuntu/Linux y macOS, requisito `input_review_confirmed`, requisito `capture_checklist.input_review_confirmed`, requisito `capture_checklist.ready_for_beta_evidence`, requisito `manual_capture_command_card.safe_to_share=true`, requisito `manual_capture_command_card.uses_placeholders=true`, requisito `manual_capture_command_card.preflight_uses_microphone=false`, requisito `manual_capture_command_card.real_capture_requires_microphone=true`, requisito `manual_capture_command_card.records_audio=false`, requisito `manual_capture_command_card.records_audio_bytes=false`, requisito `manual_capture_command_card.records_device_name=false`, requisito `manual_capture_command_card.records_local_paths=false`, redaccion de selector de dispositivo, piloto de salida `system` con `tools/output_pilot.py`, artifacts `output-operator-checklist.md` y `system-output-next-step.md`, tarjeta `system_output_readiness_card`, artifact `real-pilot-system-output-readiness.md`, politica `usable_as_beta_evidence=false`, guard `--expected-system`, requisito `system_guard.expected_system_matched`, requisito `target_output_backend.available`, requisito `output_backend_ready_required`, requisito `text_review_confirmed`, requisito `spoken_text_privacy_scan.passed`, requisito `operator_checklist.expected_system_matched`, requisito `operator_checklist.records_operator_identity=false`, requisito `operator_checklist.redacts_spoken_text=true`, requisito `operator_checklist.text_review_confirmed`, requisito `operator_checklist.spoken_text_privacy_scan_passed`, requisito `voice_review_confirmed`, requisito `operator_checklist.voice_review_confirmed`, requisito `operator_checklist.commands_available=true`, requisito `operator_checklist.ready_for_real_audio=true`, requisito `operator_checklist.ready_for_beta_evidence`, requisito `next_system_output.uses_placeholders=true`, requisito `next_system_output.records_spoken_text=false`, requisito `next_system_output.records_operator_identity=false`, tarjeta de comando audible con placeholders, guard `--confirm-text-reviewed`, guard `--confirm-voice-reviewed`, guard `--require-output-backend-ready`, fixture sintetico con `tools/pilot_audio_fixture.py --run-preflight`, `--preflight-backend`, `--preflight-model`, `--preflight-timeout-seconds`, tarjeta `fixture_preflight_card`, artifact `real-pilot-fixture-preflight.md` y politica `usable_as_beta_evidence=false`, tarjeta `transcription_readiness_card`, artifact `real-pilot-transcription-readiness.md`, politica `usable_as_beta_evidence=false`, piloto de transcripcion con `tools/transcription_pilot.py`, artifacts `transcription-review-checklist.md` y `real-transcription-next-step.md`, requisito `target_backend.available`, requisito `target_backend_ready_required`, requisito `audio.generated_synthetic_audio=false`, requisito `audio.audio_confirmed_non_sensitive=true`, requisito `audio.decoded=true`, requisito `audio.audio_file_name_redacted`, requisito `transcript.text_redacted=true`, requisito `audio_review_confirmed`, requisito `reference_review_confirmed`, requisito `reference_privacy_scan.passed`, requisito `quality_review_confirmed`, requisito `transcription_checklist.records_audio_file_name=false`, requisito `transcription_checklist.records_expected_text_file_name=false`, requisito `transcription_checklist.redacts_transcript_text=true`, requisito `transcription_checklist.redacts_expected_text=true`, requisito `transcription_checklist.audio_review_confirmed`, requisito `transcription_checklist.reference_review_confirmed`, requisito `transcription_checklist.reference_privacy_scan_passed`, requisito `transcription_checklist.quality_review_confirmed`, requisito `transcription_checklist.ready_for_beta_evidence`, preflight MP3 seguro con `--preflight-only`, validacion de backend objetivo registrado, reporte de disponibilidad/dependencias, `preflight_decision` con `decision`, `blocking_reasons`, `backend_ready` y `next_action`, y gate `--require-target-backend-ready` antes de transcripcion real, tarjeta de comando real con placeholders, guardas de duracion con `--min-audio-seconds` y `--max-audio-seconds`, scoring redactado con `--expected-text`, redaccion de nombres de archivos de audio/referencia, scan redactado de privacidad de referencia, guard `--confirm-audio-reviewed`, guard `--confirm-reference-reviewed`, guard `--confirm-quality-reviewed`, checklist de beta con `tools/beta_readiness.py`, contrato versionado `BETA_EVIDENCE_REQUIREMENTS.md`, ingesta de evidencias JSON con `--evidence`, requisitos de evidencias con `--requirements`, auditoria de artifacts con `--audit-evidence`, fallo estricto con `--fail-on-audit-gaps`, plan dinamico `next_beta_evidence_steps`, metadatos `strict_backend_guard_required`, `strict_backend_guard_flag` y `strict_backend_guard_field`, secuencia operativa `recommended_pilot_sequence` con paso `system-output-operator-checklist`, matriz por plataforma `platform_pilot_matrix`, checklist local `environment_checklist`, artifact `real-pilot-environment-checklist.md` y `usable_as_beta_evidence=false`, manifiesto `evidence_manifest`, artifact `real-pilot-evidence-manifest.md`, blockers pendientes/cerrados, artifacts JSON esperados, evidencias aceptadas/ignoradas y `usable_as_beta_evidence=false`, compuerta `pilot_decision_gate`, artifact `real-pilot-decision-gate.md`, decisiones go/no-go para pilotos reales, beta y estable, siguiente paso recomendado, condiciones de alto y `usable_as_beta_evidence=false`, handoff operativo `real_pilot_handoff` y artifact `real-pilot-handoff.md`, paquete operativo `real_pilot_command_pack` y artifact `real-pilot-command-pack.md`, plantilla sanitizada `real_pilot_findings_template` y artifact `real-pilot-findings-template.md`, resumen de evidencias aceptadas/ignoradas y artifact `pilot-plan.md` en `tools/pilot_run.py`, resumen de blockers cerrados/pendientes por evidencia, validacion de `project: AuralisVoiceKit`, motivos seguros para evidencias ignoradas, runbook inicial con `PILOTS.md`, hallazgos en `PILOT_FINDINGS.md`, blockers en `BETA_CHECKLIST.md`, bundles `doctor` sanitizados, analisis `doctor-bundles`, control explicito de sample rate para pilotos WASAPI, primera captura Windows real aprobada a 48000 Hz, dry-run Windows de salida `system` aprobado, guards `--operator-present`, `--confirm-audible` y `--confirm-text-reviewed` listos para audio real y dry-run Windows de transcripcion sintetica aprobado.
- Mensajes Windows audio. Estado: inicial para permisos, dispositivo, sample rate, canales y host API.
- Ejemplo de salida `system`. Estado: inicial con dry-run aprobado, `output-operator-checklist.md`, `system-output-next-step.md`, `target_output_backend.available`, `output_backend_ready_required`, `spoken_text_privacy_scan.passed`, `operator_checklist.redacts_spoken_text=true`, `next_system_output.records_spoken_text=false`, `--speak --operator-present --confirm-audible --confirm-text-reviewed --confirm-voice-reviewed --require-output-backend-ready --expected-system` para pilotos reales y runner `tools/output_pilot.py`.

## Prioridad inmediata

1. Generar fixture sintetico con `tools/pilot_audio_fixture.py --run-preflight` y, si el backend real sera OpenAI, usar `--preflight-backend openai --preflight-model gpt-4o-mini-transcribe --preflight-timeout-seconds 30`, revisar `real-pilot-fixture-preflight.md` y `real-pilot-transcription-readiness.md`, validar ffmpeg, revisar `target_backend.available=true`, `target_backend_ready_required=true`, `transcription-review-checklist.md` y `real-transcription-next-step.md`, y ejecutar piloto de transcripcion real con audio propio no sensible usando `tools/transcription_pilot.py` con `--expected-text` o `--expected-text-file`, `--min-audio-seconds`, `--max-audio-seconds`, `--confirm-audio-reviewed`, `--confirm-reference-reviewed`, `--require-target-backend-ready`, `--timeout-seconds 30` y `--require-openai-api-key` si el backend real es `openai`, `credentials.checked=true`, `credentials.openai_api_key_required=true`, `credentials.openai_api_key_present=true`, `credentials.records_openai_api_key=false`, `audio.audio_file_name_redacted=true`, `reference_privacy_scan.passed=true`, `audio.generated_synthetic_audio=false`, `audio.audio_confirmed_non_sensitive=true`, `audio.decoded=true`, `audio.duration_gate.enabled=true`, `audio.duration_gate.passed=true`, `preflight_decision.decision=ready_for_real_transcription` antes de usar el modelo, `transcript.text_redacted=true`, `transcription_checklist.records_audio_file_name=false`, `transcription_checklist.records_expected_text_file_name=false`, `transcription_checklist.redacts_transcript_text=true`, `transcription_checklist.redacts_expected_text=true` y `--confirm-quality-reviewed` solo despues de revisar privacidad del audio, privacidad de la referencia y calidad localmente.
2. Preparar `output-operator-checklist.md`, `system-output-next-step.md` y `real-pilot-system-output-readiness.md` con `tools/output_pilot.py --output-dir pilot_runs/output/system-dry-run --json` y ejecutar piloto manual de salida `system` con `tools/output_pilot.py --speak --operator-present --confirm-audible --confirm-text-reviewed --confirm-voice-reviewed --require-output-backend-ready --expected-system "Windows|Linux|Darwin" --output-dir pilot_runs/output/system-real` solo despues de revisar privacidad del texto, `target_output_backend.available=true`, `output_backend_ready_required=true`, `spoken_text_privacy_scan.passed=true`, `operator_checklist.redacts_spoken_text=true`, `next_system_output.records_spoken_text=false`, voz, volumen y pronunciacion.
3. Repetir captura con microfono en Ubuntu/Linux y macOS usando `--backend sounddevice` o `--backend pyaudio`, `--expected-system`, `--confirm-input-reviewed` y conservando `manual-capture-checklist.md`.
4. Cerrar blockers de beta reportados por `tools/beta_readiness.py --evidence ...` y `BETA_CHECKLIST.md`.
5. Evaluar si el siguiente lote de pilotos permite declarar beta.
