# Changelog

Todas las notas importantes de AuralisVoiceKit se documentan aqui.

El formato sigue la idea de "Keep a Changelog" y el proyecto usa versionado semantico.

## [Unreleased]

## [0.75.0] - 2026-06-06

### Cambiado

- CI usa `windows-2025-vs2026` de forma explicita para anticipar la migracion de `windows-latest` anunciada por GitHub Actions.
- Gate de estabilidad y pruebas de workflows ahora bloquean regresiones a `windows-latest` en la matriz Windows.

## [0.74.0] - 2026-06-06

### Cambiado

- Workflows de release y PyPI actualizados a `actions/upload-artifact@v7.0.1`, que declara runtime `node24`.
- Gate de estabilidad y pruebas de workflows ahora bloquean regresiones a `actions/upload-artifact@v4` o `actions/upload-artifact@v5`.

## [0.73.0] - 2026-06-06

### Agregado

- Pruebas de workflows para bloquear regresiones a `actions/upload-artifact@v4`.

### Cambiado

- Workflow de release actualizado a `actions/upload-artifact@v5` para evitar la advertencia de Node.js 20 en GitHub Actions.
- `tools/stability_gate.py` ahora verifica el workflow de release junto con CI.

## [0.72.0] - 2026-06-06

### Agregado

- Artifact `real-pilot-findings-template.md` en `tools/pilot_run.py` para copiar hallazgos sanitizados a `PILOT_FINDINGS.md` despues de pilotos reales.
- Bloque JSON `real_pilot_findings_template` con politica explicita de no registrar audio, transcripciones, texto hablado, texto esperado, rutas locales, nombres reales de dispositivos ni identidad del operador.

### Cambiado

- README, `PILOTS.md`, docs HTML, roadmap y gate de estabilidad documentan la plantilla segura de hallazgos reales.

## [0.71.0] - 2026-06-06

### Agregado

- Artifact `real-pilot-handoff.md` en `tools/pilot_run.py` con orden recomendado, auditoria estricta y politica de contenido segura para el operador del piloto real.
- Bloque JSON `real_pilot_handoff` con `content_policy` para declarar que la tarjeta no registra audio, transcripciones, texto hablado, rutas locales ni identidad del operador.

### Cambiado

- README, `PILOTS.md`, docs HTML, roadmap y gate de estabilidad documentan el handoff seguro de pilotos reales.

## [0.70.0] - 2026-06-06

### Agregado

- Artifact `system-output-next-step.md` en `tools/output_pilot.py` con comando plantilla sanitizado para pasar del dry-run al piloto audible real.
- Bloque JSON `next_system_output` con `command_template`, `uses_placeholders` y garantias de no registrar texto hablado ni identidad del operador.
- `tools/pilot_run.py` ahora exige `artifacts.system_output_next_step` en la preparacion de salida audible.

### Cambiado

- README, `PILOTS.md`, docs HTML, roadmap, checklist beta y gate de estabilidad documentan la tarjeta segura previa a salida audible.

## [0.69.0] - 2026-06-06

### Agregado

- Artifact `real-transcription-next-step.md` en `tools/transcription_pilot.py` con comando plantilla sanitizado para pasar del preflight MP3/FLAC/WAV al piloto real.
- Bloque JSON `next_real_transcription` con `command_template`, `uses_placeholders` y garantias de no registrar rutas ni nombres reales de archivos.
- Pruebas para confirmar que el siguiente paso de transcripcion no filtra nombres de audio ni rutas locales.

### Cambiado

- `tools/pilot_run.py`, `tools/stability_gate.py`, README, `PILOTS.md`, docs HTML y roadmap documentan el nuevo artifact previo a transcripcion real.

## [0.68.0] - 2026-06-05

### Agregado

- Redaccion de nombres de archivos de audio de usuario y archivos de referencia en `tools/transcription_pilot.py`.
- Campos JSON `audio.audio_file_name_redacted`, `quality.expected_text_file_name_redacted`, `quality.expected_text_file_extension`, `transcription_checklist.records_audio_file_name` y `transcription_checklist.records_expected_text_file_name`.
- Requisitos beta para bloquear evidencias de transcripcion real que expongan nombres de archivos privados.

### Cambiado

- `tools/transcription_pilot.py` conserva extension/formato de audio y referencia, pero no nombres reales de archivos de usuario.
- `tools/beta_readiness.py`, `tools/pilot_run.py`, README, `PILOTS.md`, docs HTML, roadmap y gate de estabilidad documentan la nueva redaccion de nombres de archivos.

## [0.67.0] - 2026-06-05

### Agregado

- Flag `tools/output_pilot.py --confirm-text-reviewed` para confirmar revision humana de privacidad del texto antes de reproducir salida real del sistema.
- Escaneo local y redactado `spoken_text_privacy_scan` en `tools/output_pilot.py` para bloquear patrones sensibles sin guardar coincidencias ni texto hablado.
- Campos JSON `text_review_confirmed`, `spoken_text_privacy_scan.passed`, `spoken_text_privacy_scan.risk_count`, `spoken_text_privacy_scan.risk_types` y `operator_checklist.spoken_text_privacy_scan_passed`.

### Cambiado

- `operator_checklist.ready_for_beta_evidence` ahora exige texto revisado y scan de privacidad aprobado antes de cerrar `system_output_audible`.
- `tools/beta_readiness.py --requirements`, auditoria de evidencias, `tools/pilot_run.py`, README, `PILOTS.md`, docs HTML, roadmap y gate de estabilidad documentan el nuevo requisito de salida audible.

## [0.66.0] - 2026-06-05

### Agregado

- Escaneo local y redactado `reference_privacy_scan` en `tools/transcription_pilot.py` para detectar patrones sensibles en el texto esperado sin guardar coincidencias.
- Campos JSON `reference_privacy_scan.passed`, `reference_privacy_scan.risk_count`, `reference_privacy_scan.risk_types` y `transcription_checklist.reference_privacy_scan_passed`.
- Pruebas para bloquear evidencia beta de transcripcion cuando la referencia contiene patrones sensibles aunque la revision humana este confirmada.

### Cambiado

- `transcription_checklist.ready_for_beta_evidence` ahora exige que el scan de privacidad de referencia pase antes de cerrar `real_transcription_quality`.
- `tools/beta_readiness.py --requirements`, auditoria de evidencias, `tools/pilot_run.py`, README, `PILOTS.md`, docs HTML, roadmap y gate de estabilidad documentan el nuevo requisito.

## [0.65.0] - 2026-06-05

### Agregado

- Flag `tools/transcription_pilot.py --confirm-reference-reviewed` para confirmar revision humana de privacidad del texto esperado antes de que una transcripcion real pueda contar como evidencia beta.
- Campo JSON `reference_review_confirmed` en `transcription-pilot-report.json` y `transcription_checklist.reference_review_confirmed` dentro del checklist de transcripcion.
- Pruebas para bloquear evidencia de transcripcion real cuando falta revision de privacidad de la referencia aunque audio y calidad esten revisados.

### Cambiado

- `transcription_checklist.ready_for_beta_evidence` ahora exige audio revisado, referencia revisada, backend real, duracion valida, calidad aprobada y revision humana de calidad.
- `tools/beta_readiness.py --requirements`, auditoria de evidencias, `tools/pilot_run.py`, README, `PILOTS.md`, docs HTML, roadmap y gate de estabilidad documentan el nuevo requisito.

## [0.64.0] - 2026-06-05

### Agregado

- Flag `tools/transcription_pilot.py --confirm-audio-reviewed` para confirmar revision humana de privacidad del audio antes de que una transcripcion real pueda contar como evidencia beta.
- Campo JSON `audio_review_confirmed` en `transcription-pilot-report.json` y `transcription_checklist.audio_review_confirmed` dentro del checklist de transcripcion.
- Pruebas para bloquear evidencia de transcripcion real cuando falta la revision de privacidad del audio aunque la calidad este revisada.

### Cambiado

- `transcription_checklist.ready_for_beta_evidence` ahora exige audio real no sensible, audio revisado, backend real, duracion valida, calidad aprobada y revision humana de calidad.
- `tools/beta_readiness.py --requirements`, auditoria de evidencias, `tools/pilot_run.py`, README, `PILOTS.md`, docs HTML, roadmap y gate de estabilidad documentan el nuevo requisito.

## [0.63.0] - 2026-06-05

### Agregado

- Flag `tools/output_pilot.py --expected-system` para confirmar que una evidencia de salida audible se genero en una plataforma soportada o esperada.
- Bloque JSON `system_guard` en `output-pilot-report.json` y campo `operator_checklist.expected_system_matched` dentro del checklist de operador.
- Pruebas para bloquear evidencia de salida audible cuando falta el guard de plataforma aunque audibilidad y revision de voz esten confirmadas.

### Cambiado

- `operator_checklist.ready_for_beta_evidence` ahora exige salida real, operador presente, audio audible, revision de voz, comando disponible y plataforma esperada confirmada.
- `tools/output_pilot.py` rechaza `--system` junto con `--speak`; `--system` queda reservado para dry-runs.
- `tools/beta_readiness.py --requirements`, auditoria de evidencias, `tools/pilot_run.py`, README, `PILOTS.md`, docs HTML, roadmap y gate de estabilidad documentan el nuevo requisito.

## [0.62.0] - 2026-06-05

### Agregado

- Flag `tools/manual_pilot.py --confirm-input-reviewed` para confirmar revision humana de permisos de microfono, dispositivo de entrada y entorno no sensible antes de que una captura real pueda contar como evidencia beta.
- Campo JSON `input_review_confirmed` en `manual-pilot-report.json` y `capture_checklist.input_review_confirmed` dentro del checklist de captura.
- Pruebas para bloquear evidencia de captura cuando falta revision de entrada aunque la captura real y el guard de plataforma hayan pasado.

### Cambiado

- `capture_checklist.ready_for_beta_evidence` ahora exige captura real, backend real, plataforma esperada, resultado aprobado y revision de entrada confirmada.
- `tools/beta_readiness.py --requirements`, auditoria de evidencias, `tools/pilot_run.py`, README, `PILOTS.md`, docs HTML, roadmap y gate de estabilidad documentan el nuevo requisito.

## [0.61.0] - 2026-06-05

### Agregado

- Flag `tools/output_pilot.py --confirm-voice-reviewed` para confirmar revision humana de voz, volumen y pronunciacion antes de que salida audible real pueda contar como evidencia beta.
- Campo JSON `voice_review_confirmed` en `output-pilot-report.json` y `operator_checklist.voice_review_confirmed` dentro del checklist de operador.
- Pruebas para bloquear evidencia de salida audible cuando falta revision de voz aunque `--confirm-audible` este presente.

### Cambiado

- `operator_checklist.ready_for_beta_evidence` ahora exige salida real, operador presente, audio audible confirmado, revision de voz confirmada y comando disponible.
- `tools/beta_readiness.py --requirements`, auditoria de evidencias, `tools/pilot_run.py`, README, `PILOTS.md`, docs HTML, roadmap y gate de estabilidad documentan el nuevo requisito.

## [0.60.0] - 2026-06-05

### Agregado

- Flag `tools/transcription_pilot.py --confirm-quality-reviewed` para confirmar revision humana de calidad antes de que una transcripcion real pueda contar como evidencia beta.
- Campo JSON `quality_review_confirmed` en `transcription-pilot-report.json` y `transcription_checklist.quality_review_confirmed` dentro del checklist de revision.
- Pruebas para evitar que una evidencia de transcripcion cierre beta sin confirmacion explicita de calidad.

### Cambiado

- `transcription_checklist.ready_for_beta_evidence` ahora exige transcripcion real, audio no sensible, calidad redactada suficiente y `--confirm-quality-reviewed`.
- `tools/beta_readiness.py --requirements`, auditoria de evidencias, `tools/pilot_run.py`, README, `PILOTS.md`, docs HTML, roadmap y gate de estabilidad documentan el nuevo requisito.

## [0.59.0] - 2026-06-05

### Agregado

- Flag `tools/manual_pilot.py --expected-system` para validar que una evidencia de captura real se genero en la plataforma esperada.
- Bloque JSON `system_guard` en `manual-pilot-report.json`, con `expected_system`, `actual_system` y `expected_system_matched`.
- Pruebas para guard de plataforma correcto, mismatch y bloqueo de evidencia beta sin guard.

### Cambiado

- `tools/beta_readiness.py --requirements` y la auditoria de evidencias ahora requieren `system_guard.expected_system_matched=true` para cerrar blockers de captura por JSON.
- `tools/pilot_run.py`, README, `PILOTS.md`, docs HTML, roadmap y gate de estabilidad documentan `--expected-system` para Windows, Ubuntu/Linux y macOS.

## [0.58.0] - 2026-06-05

### Agregado

- Artifact `manual-capture-checklist.md` generado por `tools/manual_pilot.py` para preparar pilotos de captura real sin guardar audio ni rutas privadas.
- Bloque JSON `capture_checklist` con checklist antes/despues de capturar, estados `ready_for_real_capture` / `ready_for_beta_evidence` y confirmacion `records_audio_bytes=false`.
- Paso seco `microphone-capture-checklist` y referencias a `manual-capture-checklist.md` dentro de `tools/pilot_run.py`.

### Cambiado

- `tools/beta_readiness.py --requirements` y la auditoria de evidencias ahora requieren `capture_checklist.ready_for_beta_evidence=true` para cerrar blockers de captura por JSON.
- `tools/manual_pilot.py` redacta selectores de dispositivo no triviales en `manual-pilot-report.json`.
- README, `PILOTS.md`, docs HTML y roadmap documentan el checklist de captura y el nuevo contrato de evidencia.

## [0.57.0] - 2026-06-05

### Agregado

- Artifact `transcription-review-checklist.md` generado por `tools/transcription_pilot.py` en dry-run, preflight y pilotos reales.
- Bloque JSON `transcription_checklist` con redaccion de audio/transcripcion/referencia, checklist antes/despues de transcribir y estados `ready_for_real_transcription` / `ready_for_beta_evidence`.
- Validaciones de pruebas para preflight MP3 con ffmpeg y checklist de revision sin ejecutar Whisper/OpenAI.

### Cambiado

- `tools/beta_readiness.py --requirements` y la auditoria de evidencias ahora requieren `transcription_checklist.ready_for_beta_evidence=true` para cerrar `real_transcription_quality`.
- `recommended_pilot_sequence`, README, `PILOTS.md`, docs HTML, roadmap y gate de estabilidad documentan `transcription-review-checklist.md`.

## [0.56.0] - 2026-06-05

### Agregado

- Artifact `output-operator-checklist.md` generado por `tools/output_pilot.py` para preparar pilotos de salida audible sin guardar identidad del operador, texto privado ni rutas locales.
- Bloque JSON `operator_checklist` con `ready_for_real_audio`, `ready_for_beta_evidence`, estado de redaccion y checklist antes/despues de playback.
- Paso `system-output-operator-checklist` en `recommended_pilot_sequence` para revisar el checklist antes de ejecutar audio real.

### Cambiado

- `tools/beta_readiness.py --requirements` y la auditoria de evidencias ahora requieren `operator_checklist.ready_for_beta_evidence=true` para cerrar el blocker `system_output_audible` por JSON.
- README, `PILOTS.md`, docs HTML, roadmap y gate de estabilidad documentan el artifact del checklist y el directorio recomendado `pilot_runs/output/system-real`.

## [0.55.0] - 2026-06-05

### Agregado

- Flag `tools/pilot_audio_fixture.py --run-preflight` para generar un MP3 sintetico publico y ejecutar automaticamente `tools/transcription_pilot.py --preflight-only` contra ese fixture.
- Campo `preflight` en `pilot-audio-fixture-report.json`, con `preflight.passed`, `audio_decoded` y `duration_gate_passed`.
- Pruebas para fallo seguro sin ffmpeg y preflight MP3 exitoso con ffmpeg real.

### Cambiado

- `recommended_pilot_sequence`, `platform_pilot_matrix`, README, `PILOTS.md`, docs HTML, roadmap y gate de estabilidad recomiendan el fixture con preflight integrado antes del MP3 propio.

## [0.54.0] - 2026-06-05

### Agregado

- Nueva herramienta `tools/pilot_audio_fixture.py` para generar fixtures sinteticos publicos WAV/MP3/FLAC antes de usar audio propio en pilotos de transcripcion.
- Paso `transcription-audio-fixture` en `recommended_pilot_sequence` y `platform_pilot_matrix`, marcado como ensayo seguro y no como evidencia beta.
- Pruebas unitarias del fixture WAV y prueba de integracion MP3 con ffmpeg.

### Cambiado

- README, `PILOTS.md`, docs HTML, roadmap y gate de estabilidad documentan el fixture sintetico previo al preflight MP3 real.

## [0.53.0] - 2026-06-05

### Agregado

- Guardas opcionales `--min-audio-seconds` y `--max-audio-seconds` en `tools/transcription_pilot.py` para validar la duracion decodificada de audios MP3/FLAC/WAV antes del preflight o piloto real.
- Campo sanitizado `audio.duration_gate` en artifacts de transcripcion, con motivo de aprobacion/fallo sin guardar audio, transcripciones ni rutas completas.
- Pruebas para preflight exitoso, fallo por audio demasiado corto y validacion de limites inconsistentes.

### Cambiado

- README, `PILOTS.md`, docs HTML, roadmap, checklist beta, planes de piloto y gate de estabilidad recomiendan limites de duracion para pilotos MP3 no sensibles.

## [0.52.0] - 2026-06-05

### Agregado

- Campo `platform_pilot_matrix` en `tools/pilot_run.py` con comandos y estados por Windows, Ubuntu/Linux, macOS, salida audible y transcripcion MP3.
- Seccion `Matriz por plataforma` en `pilot-plan.md` para separar blockers cerrados, pendientes y pasos recomendados sin exponer rutas locales.
- Pruebas para validar que la matriz cambia de estado al ingerir evidencias JSON.

### Cambiado

- README, `PILOTS.md`, docs HTML, roadmap y gate de estabilidad documentan la matriz por plataforma.

## [0.51.0] - 2026-06-05

### Agregado

- Flag `tools/transcription_pilot.py --preflight-only` para decodificar y resumir un audio propio no sensible sin ejecutar Whisper/OpenAI.
- Campos sanitizados de preflight (`preflight_only`, `audio.decoded`, `audio.decoder`, `audio.source_format`, `audio.normalized`) en el reporte de transcripcion.
- Paso `transcription-audio-preflight` dentro de `recommended_pilot_sequence` antes del piloto de transcripcion real.
- Pruebas para preflight local, CLI y plan recomendado.

### Cambiado

- README, `PILOTS.md`, docs HTML, roadmap y gate de estabilidad documentan el preflight MP3 seguro.

## [0.50.0] - 2026-06-05

### Agregado

- Campo `recommended_pilot_sequence` en `tools/pilot_run.py` con orden de pilotos reales, auditoria estricta y refresco de checklist beta.
- Seccion `Secuencia recomendada` en `pilot-plan.md` con comandos, artifacts, campos requeridos y flags de hardware, operador y audio no sensible.
- Pruebas para asegurar que la secuencia recomendada se mantiene en JSON y Markdown.

### Cambiado

- README, `PILOTS.md`, docs HTML, roadmap y gate de estabilidad documentan la secuencia operativa del piloto real.

## [0.49.0] - 2026-06-05

### Agregado

- Resumen de evidencias JSON aceptadas e ignoradas en `tools/pilot_run.py` y `pilot-plan.md`.
- Campos `accepted_json_artifacts`, `ignored_json_artifacts` y `satisfied_json_blockers` dentro de `beta_readiness`.
- Pruebas para evidencias aceptadas/ignoradas dentro del plan de pilotos.

### Cambiado

- README, `PILOTS.md`, docs HTML, roadmap y gate de estabilidad documentan el resumen de evidencias del plan.

## [0.48.0] - 2026-06-05

### Agregado

- Artifact `pilot-plan.md` generado por `tools/pilot_run.py` con estado beta, checks seguros, comandos reales pendientes y campos JSON requeridos.
- Pruebas para verificar que el plan de pilotos no expone rutas locales completas y contiene comandos beta accionables.

### Cambiado

- README, `PILOTS.md`, docs HTML, roadmap y gate de estabilidad documentan `pilot-plan.md`.

## [0.47.0] - 2026-06-05

### Agregado

- `tools/pilot_run.py --evidence` para incluir artifacts JSON reales en el piloto seguro.
- Resumen `beta_readiness` y `next_beta_evidence_steps` en el reporte de piloto seguro, con comandos concretos para cerrar blockers beta pendientes.
- Pruebas para el plan dinamico de evidencias beta dentro del piloto seguro.

### Cambiado

- README, `PILOTS.md`, docs HTML, roadmap y gate de estabilidad documentan el plan dinamico de evidencias.

## [0.46.0] - 2026-06-05

### Agregado

- Flag `tools/beta_readiness.py --fail-on-audit-gaps` para convertir `--audit-evidence` en gate estricto cuando faltan blockers o hay artifacts ignorados.
- Pruebas CLI para auditoria estricta con blockers pendientes, artifacts ignorados y evidencias JSON completas.

### Cambiado

- README, `PILOTS.md`, docs HTML, roadmap y gate de estabilidad documentan la auditoria estricta de evidencias.

## [0.45.0] - 2026-06-05

### Agregado

- Resumen global en `tools/beta_readiness.py --audit-evidence` con `satisfied_blockers`, `missing_blockers` y `ready_for_beta_by_evidence`.
- Markdown de auditoria con blockers cerrados y pendientes por evidencias JSON.
- Pruebas automatizadas para auditoria de evidencias con cobertura completa de blockers.

### Cambiado

- README, `PILOTS.md`, docs HTML, roadmap y gate de estabilidad documentan el resumen global de blockers.

## [0.44.0] - 2026-06-05

### Agregado

- Modo `tools/beta_readiness.py --audit-evidence` para auditar artifacts JSON contra los requisitos de beta.
- Reporte JSON/Markdown que muestra artifacts aceptados, blockers cerrados y campos faltantes o no coincidentes sin copiar audio, transcripciones ni rutas completas.
- Pruebas automatizadas para auditoria de evidencias aceptadas, ignoradas y salidas CLI seguras.

### Cambiado

- README, `PILOTS.md`, docs HTML, roadmap y gate de estabilidad enlazan la nueva auditoria de evidencias.

## [0.43.0] - 2026-06-05

### Agregado

- Modo `tools/beta_readiness.py --requirements` para imprimir los campos JSON que necesita cada blocker de beta.
- Reporte JSON/Markdown de requisitos de evidencias con artifacts aceptados, comandos sugeridos y notas de privacidad.
- Pruebas automatizadas para el contrato de evidencias beta y la salida CLI `--requirements`.

### Cambiado

- README, `PILOTS.md`, docs HTML, roadmap y gate de estabilidad enlazan el nuevo modo de requisitos.

## [0.42.0] - 2026-06-05

### Agregado

- Diagnostico de evidencias beta ignoradas con `ignored_details` en JSON y seccion Markdown cuando corresponde.
- Motivos seguros y bilingues para artifacts ignorados: `missing_project`, `wrong_project` y `not_json_object`.
- Pruebas automatizadas para motivos de evidencias ignoradas sin exponer rutas locales.

### Cambiado

- README, `PILOTS.md`, docs HTML, roadmap y gate de estabilidad documentan y exigen los motivos de evidencias ignoradas.

## [0.41.0] - 2026-06-05

### Agregado

- Validacion estricta de evidencias beta: `tools/beta_readiness.py --evidence` solo acepta artifacts con `project: AuralisVoiceKit`.
- Conteo de evidencias ignoradas en el reporte JSON y en `BETA_CHECKLIST.md`.
- Prueba automatizada para artifacts ignorados que parecen validos pero no identifican el proyecto.

### Cambiado

- El checklist de beta muestra evidencias aceptadas e ignoradas sin exponer rutas locales completas.
- El gate de estabilidad exige que el runner de beta readiness mantenga el conteo de evidencias ignoradas.

## [0.40.0] - 2026-06-05

### Agregado

- `tools/beta_readiness.py --evidence` para aceptar archivos o carpetas con artifacts JSON de pilotos reales.
- Cierre estructurado de blockers de beta desde `manual-pilot-report.json`, `output-pilot-report.json` y `transcription-pilot-report.json`.
- Requisito de calidad para transcripcion real de beta: audio no sensible, scoring habilitado y `min_word_accuracy >= 0.75`.
- Pruebas automatizadas que demuestran que artifacts JSON validos pueden cerrar blockers sin copiar transcripciones ni audio.

### Cambiado

- README, `PILOTS.md`, docs HTML, roadmap, gate de estabilidad y `BETA_CHECKLIST.md` documentan la ingesta de evidencias con `--evidence`.

## [0.39.0] - 2026-06-05

### Agregado

- Herramienta `tools/beta_readiness.py` para generar reportes JSON/Markdown de readiness para beta publica.
- `BETA_CHECKLIST.md` generado con blockers actuales: transcripcion real con calidad, salida `system` audible confirmada, captura Ubuntu/Linux y captura macOS.
- Modo `--fail-on-blockers` para auditorias estrictas de beta.
- Pruebas automatizadas para el checklist de beta y su salida CLI.

### Cambiado

- README, `PILOTS.md`, docs HTML, roadmap y gate de estabilidad enlazan el nuevo checklist de beta.
- `tools/pilot_run.py` incluye `beta-readiness` como paso manual pendiente.
- `tools/stability_gate.py` exige que el runner y el checklist de beta existan antes de conservar el estado `pilot`.

## [0.38.0] - 2026-06-05

### Agregado

- Scoring redactado en `tools/transcription_pilot.py` con `--expected-text` y `--expected-text-file`.
- Metricas de calidad para pilotos de transcripcion: word accuracy, word error rate, character error rate y exact match normalizado.
- Umbral opcional `--min-word-accuracy` para que un piloto falle cuando la calidad no alcanza el minimo definido.
- Hallazgo Windows de dry-run con scoring redactado, sin guardar transcripcion ni texto esperado completo.

### Cambiado

- README, `PILOTS.md`, docs HTML, roadmap, runner seguro y gate de estabilidad documentan el scoring redactado del piloto de transcripcion.

## [0.37.0] - 2026-06-05

### Agregado

- Herramienta `tools/transcription_pilot.py` para pilotos de transcripcion con artifacts JSON/Markdown.
- Modo seguro por defecto: audio sintetico y backend `null`, sin red, modelos reales ni audio privado.
- Guardias `--real-transcription`, `--audio` y `--audio-non-sensitive` antes de usar `whisper` u `openai`.
- Reportes de transcripcion con texto redactado, longitud estimada y metadatos sanitizados.
- Hallazgo de piloto de transcripcion Windows dry-run documentado con audio sintetico y backend `null`.
- Pruebas automatizadas del runner de piloto de transcripcion.

### Cambiado

- `tools/pilot_run.py`, `PILOTS.md`, README, docs HTML, roadmap y gate de estabilidad apuntan al nuevo runner de transcripcion.

## [0.36.0] - 2026-06-05

### Agregado

- `tools/output_pilot.py` exige `--operator-present` junto con `--speak` antes de reproducir audio real.
- Flag `--confirm-audible` para registrar que el operador confirmo salida audible.
- Estado `operator_confirmation_status` en el reporte JSON y Markdown del piloto de salida.

### Cambiado

- README, `PILOTS.md`, docs HTML, roadmap, gate de estabilidad y pasos manuales usan `--speak --operator-present`.

## [0.35.0] - 2026-06-05

### Agregado

- Herramienta `tools/output_pilot.py` para pilotos de salida `system` con artifacts JSON/Markdown.
- Modo dry-run por defecto para el piloto de salida y `--speak` explicito para reproducir audio real.
- Sanitizacion de comandos del piloto de salida: el texto solicitado se guarda como `<text-redacted>`.
- Hallazgo de piloto de salida Windows dry-run documentado sin reproducir audio real.
- Pruebas automatizadas del runner de piloto de salida.

### Cambiado

- `tools/pilot_run.py`, `PILOTS.md`, README, docs HTML y el gate de estabilidad apuntan al nuevo runner de salida `system`.

## [0.34.0] - 2026-06-05

### Agregado

- `auralis doctor --capture-test` acepta `--sample-rate` para probar hardware real con frecuencias como 48000 Hz en WASAPI.
- `tools/manual_pilot.py` acepta `--sample-rate` y registra ese valor en el reporte JSON y Markdown del piloto.
- Hallazgos de piloto real Windows/WASAPI documentados: primera captura corta fallo por sample rate invalido y el reintento a 48000 Hz paso correctamente.

### Cambiado

- El gate de estabilidad exige que el runner manual documente `--sample-rate`.
- README, `PILOTS.md`, referencia HTML, roadmap y pasos de piloto recomiendan sample rate explicito para WASAPI.

## [0.33.0] - 2026-06-05

### Agregado

- Herramienta `tools/manual_pilot.py` para ejecutar un piloto manual guiado con bundle doctor, analisis `doctor-bundles`, reporte JSON y Markdown de hallazgos.
- Modo seguro por defecto en el piloto manual: no abre el microfono salvo que se use `--capture-test`.
- Documento `PILOT_FINDINGS.md` con el primer hallazgo Windows seguro: `ffmpeg` disponible y captura real pendiente por falta de `sounddevice`.
- Pruebas automatizadas para el runner de piloto manual.

### Cambiado

- `analyze_doctor_bundles()` usa nombres de bundle en vez de rutas locales para evitar filtrar paths en reportes compartibles.
- `tools/pilot_run.py` apunta el paso manual de microfono al nuevo runner `tools/manual_pilot.py`.
- README, `PILOTS.md`, referencia API, documentacion HTML y roadmap documentan el flujo de piloto manual guiado.
- `tools/stability_gate.py` exige ahora el runner de piloto manual y el documento de hallazgos.
- `.gitignore` ignora `pilot_runs/` para evitar subir artifacts locales.

## [0.32.0] - 2026-06-05

### Agregado

- Analizador de bundles doctor con `DoctorBundleAnalysis`, `DoctorBundleIssue` y `analyze_doctor_bundles()`.
- Constante publica `DOCTOR_BUNDLE_ANALYSIS_SCHEMA` y helper `write_doctor_bundle_analysis()`.
- Comando `auralis doctor-bundles` para resumir bundles sanitizados por sistema, version Python, checks, categorias y prioridades.
- Soporte `--output` y `--json` para guardar analisis de pilotos en JSON.
- Pruebas unitarias para clasificacion de hallazgos, salida CLI y errores de bundles invalidos.

### Cambiado

- README, `PILOTS.md`, referencia API, documentacion HTML y roadmap documentan el flujo generar bundle -> analizar bundle.
- `tools/stability_gate.py` exige ahora la API de analisis de bundles doctor como parte de la etapa de pilotos.
- La prioridad inmediata pasa a ejecutar un piloto manual Windows y revisar su bundle con `auralis doctor-bundles`.

## [0.31.0] - 2026-06-05

### Agregado

- Bundle de diagnostico sanitizado para pilotos y reportes de bugs con `create_doctor_bundle()` y `write_doctor_bundle()`.
- Helper publico `sanitize_doctor_report()` y constante `DOCTOR_BUNDLE_SCHEMA`.
- Flag `auralis doctor --bundle <archivo.json>` para escribir reportes compartibles sin audio, transcripciones, rutas locales ni nombres de dispositivos.
- Pruebas unitarias para sanitizacion, escritura del bundle y CLI.

### Cambiado

- README, referencia API, documentacion HTML y roadmap documentan los bundles `doctor`.
- `tools/stability_gate.py` exige ahora la API de bundle de diagnostico como parte de la etapa de pilotos.
- La prioridad inmediata pasa a recolectar y analizar bundles de pilotos Windows reales.

## [0.30.0] - 2026-06-05

### Agregado

- Herramienta `tools/pilot_run.py` para ejecutar un piloto automatizado seguro sin microfono, audio real, red ni modelos.
- Runbook `PILOTS.md` con checklist manual, comandos recomendados y plantilla de hallazgos.
- Reporte JSON de piloto con gate de estabilidad, doctor `wav`, asistente local con privacidad, salida `system` dry-run y benchmark offline exportado.
- Pruebas automatizadas para el runner de piloto seguro.

### Cambiado

- `tools/stability_gate.py` exige ahora el runbook de pilotos y el runner seguro.
- README, documentacion HTML y roadmap documentan la ruta de pilotos.
- El roadmap mueve la prioridad inmediata a diagnostico Windows basado en hallazgos reales.

## [0.29.0] - 2026-06-05

### Agregado

- Ejemplo `examples/local_assistant_privacy_demo.py` para un asistente local offline con logs sanitizados.
- Flujo completo sin extras: audio sintetico, WAV temporal, `VoiceSession`, transcripcion `null`, respuesta `null` y JSONL con `PrivacyEventLogger`.
- Checks de privacidad en el payload del ejemplo para confirmar que texto, path y token privados no se filtran al log.
- Pruebas automatizadas del ejemplo como modulo y como script.

### Cambiado

- `tools/stability_gate.py` exige ahora el ejemplo de asistente local con privacidad como parte del estado `pilot`.
- README, referencia API, documentacion HTML y roadmap documentan el nuevo ejemplo.
- El roadmap mueve la prioridad inmediata a pilotos reales guiados por `tools/stability_gate.py`.

## [0.28.0] - 2026-06-05

### Agregado

- Ejemplo `examples/system_output_demo.py` para probar el backend de salida `system`.
- Modo dry-run por defecto para simular comandos Windows, macOS o Linux sin reproducir audio real.
- Flag `--speak` para ejecutar un piloto manual real con la herramienta de voz del sistema operativo.
- Salida JSON con voces detectadas, eventos `output.*`, comandos simulados y errores accionables.
- Pruebas automatizadas para el ejemplo y su ejecucion como script.

### Cambiado

- `tools/stability_gate.py` exige ahora el ejemplo de salida `system` como parte del estado `pilot`.
- README, referencia API, documentacion HTML y roadmap documentan el nuevo ejemplo seguro.
- El roadmap mueve la prioridad inmediata a ejemplos de asistente local con logs sanitizados.

## [0.27.0] - 2026-06-05

### Agregado

- Helper publico `write_benchmark_report()` para exportar reportes de benchmark a JSON o CSV.
- Helpers `benchmark_report_to_csv_rows()` y `benchmark_comparison_to_csv_rows()` para integrar reportes con pipelines externos.
- Flags `--output` y `--output-format` en `auralis benchmark` y `auralis benchmark-whisper`.
- CSV estable para benchmarks offline y comparaciones de Whisper, con metadata, warnings y rankings.
- Pruebas unitarias para exportacion por API y CLI.

### Cambiado

- README, referencia API, documentacion HTML y roadmap documentan los benchmarks exportables.
- El roadmap mueve la prioridad inmediata al ejemplo de salida de voz con backend `system`.

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
