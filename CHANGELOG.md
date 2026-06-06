# Changelog

Todas las notas importantes de AuralisVoiceKit se documentan aqui.

El formato sigue la idea de "Keep a Changelog" y el proyecto usa versionado semantico.

## [Unreleased]

## [0.160.0] - 2026-06-06

### Mejorado

- `tools/beta_readiness.py` agrega a `missing_terms` de `system_output_audible` los campos `System output command card python extra: not-set`, `System output command card pip command: not-set` y `System output dependency post-install plays audio: False`.

### Pruebas

- `tests/test_beta_readiness.py` valida que el reporte JSON y `BETA_CHECKLIST.md` muestren esos campos antes del piloto audible real.

## [0.159.0] - 2026-06-06

### Mejorado

- `tools/beta_readiness.py` ahora muestra en `missing_terms` los campos del readiness plan de salida `system`: `Target output backend readiness uses pip extra: False`, `Target output backend readiness python extra: not-set` y `Target output backend readiness pip command: not-set`.

### Pruebas

- `tests/test_beta_readiness.py` valida que el reporte JSON y `BETA_CHECKLIST.md` incluyan esas evidencias faltantes para guiar pilotos reales.

## [0.158.0] - 2026-06-06

### Agregado

- `target_output_backend.readiness_plan` ahora declara `uses_pip_extra=false`, `python_extra=null` y `pip_command=null` para salida `system`, alineando el plan de readiness con la command card y el vocabulario publico de extras opcionales.
- `tools/beta_readiness.py` exige esos campos antes de aceptar evidencia beta de salida audible.

### Pruebas

- Nuevas aserciones validan readiness plan estructurado en el runner de salida, contrato beta, piloto seguro y documentacion publica.

## [0.157.0] - 2026-06-06

### Agregado

- `tools/output_pilot.py` ahora agrega `uses_pip_extra=false`, `python_extra=null`, `pip_command=null` y `system_dependency_plan` a `system_output_command_card`, dejando explicito que la salida `system` usa dependencias del sistema y no extras pip.
- `tools/beta_readiness.py` exige ese plan seguro para cerrar evidencia beta de salida audible y rechaza command cards antiguos o con preflight que pueda reproducir audio.

### Pruebas

- Nuevas aserciones cubren el contrato beta de salida audible, el piloto seguro y artifacts Markdown/JSON con plan de dependencias del sistema.

## [0.156.0] - 2026-06-06

### Agregado

- `tools/transcription_pilot.py` ahora agrega `uses_pip_extra`, `python_extra` y `pip_command` a `real_transcription_command_card` para declarar el extra opcional de Whisper u OpenAI antes del piloto real.
- `tools/beta_readiness.py` exige esos campos para cerrar evidencia beta de transcripcion real y rechaza tarjetas con extra equivocado.

### Pruebas

- Nuevas aserciones cubren el contrato beta, el piloto seguro y el command card de transcripcion con extras opcionales estructurados.

## [0.155.0] - 2026-06-06

### Agregado

- `tools/beta_readiness.py` ahora exige `manual_capture_command_card.uses_pip_extra=true` y `manual_capture_command_card.python_extra` correcto para cerrar evidencia beta de captura Windows/WASAPI, Ubuntu/Linux y macOS.

### Pruebas

- Nuevas aserciones validan que el contrato beta, el auditor de evidencias y los fixtures de pilotos seguros rechacen tarjetas de captura sin extra estructurado.

## [0.154.0] - 2026-06-06

### Agregado

- `tools/manual_pilot.py` alinea `capture_readiness_plan` y `manual_capture_command_card` con el inventario publico agregando `uses_pip_extra` y `python_extra` para captura `sounddevice`, `wasapi` y `pyaudio`.

### Pruebas

- Nuevas aserciones validan extras estructurados para captura Linux/macOS, WASAPI y backends sin extra.

## [0.153.0] - 2026-06-06

### Agregado

- `tools/transcription_pilot.py` alinea `target_backend.install_plan` con el inventario publico agregando `uses_pip_extra` y `python_extra` sin quitar el campo historico `extra`.

### Pruebas

- Nuevas aserciones validan los alias publicos del plan de instalacion para Whisper, OpenAI y backends sin extra.

## [0.152.0] - 2026-06-06

### Agregado

- `backend_inventory()` y `auralis backends --json` ahora incluyen `install_plan` por backend con `uses_pip_extra`, `python_extra` y `pip_command` cuando corresponde.
- La salida textual de `auralis backends` muestra el comando pip del extra opcional para backends que lo usan.

### Pruebas

- Nuevas aserciones validan `install_plan` para `pyaudio`, `sounddevice`/`wasapi`, `whisper`, `openai` y backends incluidos sin extra.

## [0.151.0] - 2026-06-06

### Agregado

- Nueva API publica `backend_inventory()` para obtener desde Python el inventario seguro de backends sin rutas locales ni credenciales.
- `AuralisVoiceKit.backend_inventory()` expone el mismo reporte usando el registro configurado en la instancia.
- `auralis backends --json` ahora reutiliza el helper publico para mantener una sola politica de inventario.

### Pruebas

- Nuevas pruebas validan la API publica de inventario, el metodo de fachada y la ausencia de rutas locales en dependencias.

## [0.150.0] - 2026-06-06

### Agregado

- `auralis backends --json` ahora devuelve un reporte estructurado con version, backends registrados, disponibilidad, razones, dependencias publicas, politica de contenido y conteos por tipo sin exponer rutas locales.
- La documentacion publica explica el uso del reporte JSON de backends para preflights automatizados en Windows, Ubuntu/Linux y macOS.

### Pruebas

- Nueva prueba CLI valida el payload JSON de `backends`, incluyendo version, backends principales y conteos por categoria.

## [0.149.0] - 2026-06-06

### Agregado

- `tools/pilot_run.py` ahora genera `real-pilot-local-receipt.md`, una tarjeta publica para documentar resultado local, decision final, artifact sanitizado y auditoria posterior sin guardar identidad ni rutas.
- `real_pilot_local_receipt_card` resume placeholders de decision/resultado, items de recibo, soporte de go/no-go final, paquete de evidencia, cierre de auditoria y plantilla de hallazgos.
- `pilot-plan.md`, `real-pilot-handoff.md`, `real-pilot-audit-closure.md`, `real-pilot-evidence-package.md`, `real-pilot-operator-brief.md`, `real-pilot-run-sheet.md` y `real-pilot-final-go-no-go.md` enlazan el recibo local.

### Pruebas

- Nuevas pruebas validan el artifact de recibo local, sus placeholders, flags de privacidad, salida CLI y presencia en reportes Markdown.

## [0.148.0] - 2026-06-06

### Agregado

- `tools/pilot_run.py` ahora genera `real-pilot-final-go-no-go.md`, una tarjeta publica de decision local final antes de tocar hardware o ejecutar el comando real.
- `real_pilot_final_go_no_go_card` resume condiciones GO/NO-GO, items de revision, soporte de run sheet, seguridad de copia, confirmaciones humanas y auditoria posterior.
- `pilot-plan.md`, `real-pilot-handoff.md`, `real-pilot-audit-closure.md`, `real-pilot-evidence-package.md`, `real-pilot-operator-brief.md` y `real-pilot-run-sheet.md` enlazan la compuerta final.

### Pruebas

- Nuevas pruebas validan el artifact go/no-go final, sus flags de privacidad, salida CLI, fases de run sheet y presencia en reportes Markdown.

## [0.147.0] - 2026-06-06

### Agregado

- `tools/pilot_run.py` ahora genera `real-pilot-run-sheet.md`, una hoja publica por fases para que el operador local ejecute el siguiente piloto real en orden.
- `real_pilot_run_sheet_card` resume prerequisitos, ensayo, consentimiento/copia, ejecucion real, paquete de evidencia, auditoria estricta y refresco del checklist beta.
- `pilot-plan.md`, `real-pilot-handoff.md`, `real-pilot-rehearsal-card.md`, `real-pilot-audit-closure.md`, `real-pilot-evidence-package.md` y `real-pilot-operator-brief.md` enlazan la run sheet.

### Pruebas

- Nuevas pruebas validan el artifact de run sheet, fases requeridas, flags de privacidad, salida CLI y presencia en reportes Markdown.

## [0.146.0] - 2026-06-06

### Agregado

- `tools/pilot_run.py` ahora genera `real-pilot-operator-brief.md`, una tarjeta publica de una pagina para el operador local antes de ejecutar el siguiente piloto real.
- `real_pilot_operator_brief_card` resume foco activo, comando plantilla, artefactos antes/despues del piloto, confirmaciones humanas, pendientes de copia local, auditoria estricta y reglas de privacidad.
- `pilot-plan.md`, `real-pilot-handoff.md`, `real-pilot-rehearsal-card.md`, `real-pilot-audit-closure.md` y `real-pilot-evidence-package.md` enlazan el brief del operador.

### Pruebas

- Nuevas pruebas validan el artifact del brief, su estado `ready_for_local_operator_review`, sus flags de privacidad, su salida CLI y su presencia en reportes Markdown.

## [0.145.0] - 2026-06-06

### Agregado

- `tools/pilot_run.py` ahora genera `real-pilot-evidence-package.md`, una tarjeta publica para reunir el JSON real sanitizado, hallazgos, checklist beta y auditoria estricta despues del ensayo/ejecucion local.
- `real_pilot_evidence_package_card` lista artifacts esperados, campos JSON requeridos/faltantes, directorios sugeridos, checklist del paquete y reglas para no copiar audio, transcripciones, rutas, dispositivos ni identidad del operador.
- `pilot-plan.md`, `real-pilot-handoff.md`, `real-pilot-rehearsal-card.md` y `real-pilot-audit-closure.md` enlazan el paquete de evidencia sanitizada.

### Pruebas

- Nuevas pruebas validan el artifact del paquete, su estado `waiting_for_real_evidence`, sus flags de privacidad, su salida CLI y su presencia en reportes Markdown.

## [0.144.0] - 2026-06-06

### Agregado

- `tools/pilot_run.py` ahora genera `real-pilot-rehearsal-card.md`, una tarjeta publica de ensayo local antes de copiar o ejecutar el comando real del siguiente piloto.
- `real_pilot_rehearsal_card` lista comandos seguros de ensayo, artifacts de apoyo, checklist previo, estado del foco activo y reglas para no ejecutar hardware, microfono, audio real, modelos ni evidencia beta durante el ensayo.
- `pilot-plan.md`, `real-pilot-handoff.md`, `real-pilot-next-evidence-focus.md`, `real-pilot-decision-gate.md`, `real-pilot-hard-stop-card.md`, `real-pilot-evidence-intake-card.md`, `real-pilot-execution-card.md`, `real-pilot-consent-card.md` y `real-pilot-audit-closure.md` enlazan el ensayo local previo.

### Pruebas

- Nuevas pruebas validan el artifact de ensayo, sus flags de privacidad, su estado `ready_for_local_rehearsal`, su salida CLI y su presencia en reportes Markdown sin rutas locales ni contenido sensible.

## [0.143.0] - 2026-06-06

### Agregado

- `tools/pilot_run.py` ahora genera `real-pilot-audit-closure.md`, una tarjeta publica para cerrar el piloto real despues del JSON sanitizado.
- `real_pilot_audit_closure_card` lista auditoria estricta, refresco de `BETA_CHECKLIST.md`, plantilla de hallazgos, directorios sugeridos y checklist de cierre sin registrar audio, transcripciones, rutas, nombres de dispositivos ni identidad del operador.
- `pilot-plan.md`, `real-pilot-handoff.md`, `real-pilot-decision-gate.md`, `real-pilot-hard-stop-card.md`, `real-pilot-evidence-intake-card.md`, `real-pilot-execution-card.md` y `real-pilot-consent-card.md` enlazan el cierre de auditoria.

### Pruebas

- Nuevas pruebas validan el artifact de cierre, sus flags de privacidad, su estado `waiting_for_real_evidence` y su presencia en CLI/reportes Markdown.

## [0.142.0] - 2026-06-06

### Agregado

- `operator_gate.command_audit` ahora incluye `copy_safety`, separando plantilla segura de copia y revisiones locales pendientes antes de ejecutar el siguiente piloto real.
- `copy_safety` reporta estado `ready_for_local_review|blocked`, razones de bloqueo, items de revision, requisitos de consentimiento, confirmaciones humanas y guard backend estricto sin registrar audio, rutas ni identidad del operador.

### Pruebas

- Nuevas pruebas validan el bloque `copy_safety`, sus flags de privacidad y su presencia en `real-pilot-execution-card.md`.

## [0.141.0] - 2026-06-06

### Agregado

- `tools/pilot_run.py` ahora genera `real-pilot-consent-card.md`, una plantilla publica de consentimiento local antes de ejecutar hardware, audio real o flags `--confirm-*`.
- La tarjeta conserva el foco beta activo, revisiones previas, confirmaciones humanas, auditoria estricta y politica de contenido sin registrar identidad, firma, audio, rutas ni texto privado.
- `pilot-plan.md`, `real-pilot-handoff.md`, `real-pilot-decision-gate.md`, `real-pilot-hard-stop-card.md`, `real-pilot-evidence-intake-card.md` y `real-pilot-execution-card.md` enlazan la tarjeta de consentimiento.

### Pruebas

- Nuevas pruebas validan el artifact de consentimiento, sus flags de privacidad, el checklist local y su presencia en CLI/reportes Markdown.

## [0.140.0] - 2026-06-06

### Agregado

- `tools/transcription_pilot.py` ahora incluye `real_transcription_operator_gate`, una compuerta publica para decidir si una transcripcion real esta lista para auditoria beta o sigue bloqueada.
- El gate lista confirmaciones de operador, comando seguro con placeholders, campos faltantes del contrato beta y flags de privacidad sin audio, rutas, transcripciones, texto esperado ni identidad del operador.
- `tools/beta_readiness.py` exige `real_transcription_operator_gate.ready_for_beta_audit=true`, contadores de faltantes en cero y comando seguro para aceptar evidencia beta de `real_transcription_quality`.

### Pruebas

- Nuevas pruebas cubren el gate bloqueado en dry-run, el gate listo con transcripcion real simulada y el rechazo de evidencia beta de transcripcion real con gate inseguro o sin placeholders.

## [0.139.0] - 2026-06-06

### Agregado

- `tools/output_pilot.py` ahora incluye `system_output_operator_gate`, una compuerta publica para decidir si la salida audible esta lista para auditoria beta o sigue bloqueada.
- El gate lista confirmaciones de operador, comando seguro con placeholders, campos faltantes del contrato beta y flags de privacidad sin audio, texto hablado, rutas locales ni identidad del operador.
- `tools/beta_readiness.py` exige `system_output_operator_gate.ready_for_beta_audit=true`, contadores de faltantes en cero y comando seguro para aceptar evidencia beta de salida audible.

### Pruebas

- Nuevas pruebas cubren el gate bloqueado en dry-run, el gate listo con salida real simulada y el rechazo de evidencia beta de salida audible con gate inseguro o sin placeholders.

## [0.138.0] - 2026-06-06

### Agregado

- `tools/beta_readiness.py` ahora exige `capture_operator_gate` para aceptar evidencia beta de captura Windows/WASAPI, Ubuntu/Linux y macOS.
- El contrato `--requirements` lista `capture_operator_gate.ready_for_beta_audit=true`, decision `ready_for_beta_audit`, contadores de faltantes en cero y flags de privacidad sin audio, bytes, dispositivos, rutas locales ni identidad del operador.
- La auditoria de evidencias y el checklist beta rechazan reportes de captura con gate bloqueado, comandos no copiable o confirmaciones faltantes.

### Pruebas

- Nuevas pruebas cubren evidencia de captura con gate inseguro/bloqueado y validan que el contrato Markdown incluya los campos de `capture_operator_gate`.

## [0.137.0] - 2026-06-06

### Agregado

- `tools/manual_pilot.py` ahora incluye `capture_operator_gate`, una compuerta publica para decidir si una captura manual esta lista para auditoria beta o sigue bloqueada.
- El gate lista confirmaciones requeridas, faltantes, comando real con placeholders, comando de auditoria y flags de privacidad sin guardar audio, bytes, nombres de dispositivos, rutas locales ni identidad del operador.
- `pilot-findings.md`, `manual-capture-checklist.md` y `manual-capture-command.md` muestran la decision del gate para reducir errores antes del primer piloto Windows/WASAPI real.

### Pruebas

- Nuevas pruebas cubren el gate bloqueado en dry-run y el gate listo para auditoria beta cuando captura, plataforma, backend y revisiones estan confirmadas.

## [0.136.0] - 2026-06-06

### Agregado

- `real_pilot_execution_card.operator_gate` ahora incluye `evidence_contract`, una ficha publica con blocker, artifact esperado, campos requeridos/faltantes, condicionales, directorios sugeridos y comandos de auditoria/refresco.
- `real-pilot-execution-card.md` muestra el contrato de evidencia beta junto al comando local para que el operador pueda cerrar el piloto real sin buscar requisitos en varios archivos.
- El contrato conserva flags publicos de privacidad y declara que no registra audio, transcripciones, texto hablado, texto esperado, rutas locales, dispositivos ni identidad del operador.

### Pruebas

- Nuevas pruebas validan que el contrato de evidencia del foco Windows/WASAPI queda serializado, renderizado y libre de datos sensibles.

## [0.135.0] - 2026-06-06

### Agregado

- `real_pilot_execution_card.operator_gate` ahora incluye `command_audit` para validar el comando local antes de que el operador lo copie.
- La auditoria confirma flags obligatorios como `--expected-system`, `--confirm-*` y guards estrictos de backend; si falta alguno, la compuerta queda bloqueada con `operator_command_audit_failed`.
- `real-pilot-execution-card.md` muestra estado, flags requeridos, presentes y faltantes sin registrar valores privados.

### Pruebas

- Nuevas pruebas validan que el comando del foco Windows/WASAPI conserva flags humanos, plataforma esperada y guard estricto antes de quedar listo para operador local.

## [0.134.0] - 2026-06-06

### Agregado

- `real_pilot_execution_card` ahora incluye `operator_gate`, una compuerta estructurada para decidir si el siguiente piloto real queda listo para operador local o bloqueado.
- La compuerta lista revisiones previas, confirmaciones humanas obligatorias, guard backend estricto, artifact JSON esperado y cierre de auditoria sin exponer audio, transcripciones, rutas locales, dispositivos ni identidad del operador.
- `real-pilot-execution-card.md` muestra la compuerta del operador en Markdown para preparar el piloto real seguro sin ejecutar hardware automaticamente.

### Pruebas

- Nuevas pruebas validan `operator_gate`, sus flags publicos de privacidad, las confirmaciones humanas y el cierre de auditoria.

## [0.133.0] - 2026-06-06

### Agregado

- `tools/pilot_run.py` ahora genera `real-pilot-execution-card.md`, una tarjeta publica para ejecutar el siguiente piloto real en orden, revisar confirmaciones humanas y cerrar con auditoria estricta.
- `pilot-report.json` incluye `real_pilot_execution_card` con foco actual, flags de privacidad y enlaces desde plan, handoff, foco, manifiesto, compuerta, alto operativo e ingesta de evidencia.
- La tarjeta resume pre-run, comando del foco, campos faltantes, directorios de ingesta, auditoria/refresco y condiciones de alto sin copiar audio, transcripciones, texto esperado, texto hablado real, rutas locales ni identidad del operador.

### Pruebas

- Nuevas pruebas validan que la tarjeta de ejecucion se escribe, se serializa, queda enlazada y mantiene politica publica segura.

## [0.132.0] - 2026-06-06

### Agregado

- `tools/pilot_run.py` ahora genera `real-pilot-evidence-intake-card.md`, una tarjeta publica para ubicar reportes reales sanitizados y ejecutar la auditoria estricta antes de refrescar `BETA_CHECKLIST.md`.
- La tarjeta lista directorios sugeridos, artifacts JSON aceptados, comandos de auditoria/refresco y reglas para mantener audio, transcripciones, texto esperado, texto hablado real, rutas locales e identidad del operador fuera del repositorio.
- `pilot-report.json` incluye `real_pilot_evidence_intake_card` con flags publicos de privacidad y enlaces desde plan, handoff, foco, manifiesto, compuerta y alto operativo.

### Pruebas

- Nuevas pruebas validan que la tarjeta se escribe, se serializa, queda enlazada y no registra contenido privado.

## [0.131.0] - 2026-06-06

### Agregado

- `tools/pilot_run.py` ahora genera `real-pilot-hard-stop-card.md`, una tarjeta publica de alto operativo antes de tocar hardware, audio real, texto hablado real o flags `--confirm-*`.
- El artifact se enlaza desde `pilot-plan.md`, `real-pilot-handoff.md`, `real-pilot-next-evidence-focus.md` y `real-pilot-decision-gate.md`.
- `pilot-report.json` incluye `real_pilot_hard_stop_card` con politica de contenido segura y flags que prueban que no registra audio, transcripciones, texto hablado, rutas locales, nombres de dispositivos ni identidad del operador.

### Pruebas

- Nuevas pruebas validan que la tarjeta se escribe, se serializa, queda enlazada y conserva la politica publica segura.

## [0.130.0] - 2026-06-06

### Agregado

- `tools/beta_readiness.py --audit-evidence` ahora genera `privacy_remediation_plan` con pasos ordenados por archivo/campo cuando `privacy_audit` encuentra contenido crudo.
- El plan marca `safe_to_share=true`, `records_private_values=false`, `status`, `step_count`, `next_action_es` y `next_action_en`.
- `tools/pilot_run.py` propaga ese plan a `pilot-report.json`, `pilot-plan.md`, `real-pilot-evidence-manifest.md` y `real-pilot-decision-gate.md`.

### Pruebas

- Nuevas pruebas validan el plan cuando no hay hallazgos y cuando una evidencia contiene texto/rutas crudas, manteniendo fuera los valores privados.

## [0.129.0] - 2026-06-06

### Cambiado

- `tools/beta_readiness.py --audit-evidence` ahora agrega acciones seguras de remediacion para cada hallazgo de `privacy_audit`.
- Los hallazgos incluyen `action_es`, `action_en` y `safe_replacement` para indicar si hay que reemplazar texto, rutas, nombres de archivo/dispositivo o credenciales por placeholders.
- `tools/pilot_run.py` muestra esas acciones en `pilot-plan.md`, `real-pilot-evidence-manifest.md` y `real-pilot-decision-gate.md` sin imprimir valores privados.

### Pruebas

- Nuevas pruebas validan las acciones de remediacion para texto y rutas crudas, y confirman que los valores privados siguen fuera de JSON y Markdown.

## [0.128.0] - 2026-06-06

### Cambiado

- `tools/pilot_run.py` ahora propaga `privacy_audit` desde la auditoria beta a `pilot-report.json`, `pilot-plan.md`, `real-pilot-evidence-manifest.md` y `real-pilot-decision-gate.md`.
- La compuerta go/no-go mantiene beta bloqueada si la auditoria de privacidad encuentra campos crudos sospechosos, aunque los blockers funcionales parezcan cerrados por JSON.
- El plan y el manifiesto muestran estado, conteo, campo y motivo de hallazgos de privacidad sin imprimir valores privados.

### Pruebas

- Nuevas pruebas verifican que un artifact aceptado con `transcript.text` crudo queda marcado por privacidad y que el valor privado no aparece en reportes JSON ni Markdown.

## [0.127.0] - 2026-06-06

### Cambiado

- `tools/beta_readiness.py --audit-evidence` ahora agrega `privacy_audit` para artifacts JSON aceptados.
- El escaneo de privacidad marca campos crudos sospechosos como `transcript.text`, `expected_text`, `spoken_text`, `audio.path`, nombres de archivo sin redaccion o credenciales crudas.
- `--fail-on-audit-gaps` ahora tambien falla si hay hallazgos de privacidad, aunque todos los blockers JSON esten satisfechos.
- El reporte Markdown de auditoria muestra solo nombres de campos y motivos; nunca imprime valores privados.

### Pruebas

- Nuevas pruebas validan que evidencias limpias siguen pasando y que artifacts con texto/rutas crudas quedan bloqueados sin filtrar esos valores en JSON o Markdown.

## [0.126.0] - 2026-06-06

### Cambiado

- `tools/transcription_pilot.py` ahora agrega `real_transcription_command_card` al reporte de transcripcion real.
- La evidencia beta de `real_transcription_quality` exige una tarjeta segura con placeholders, preflight sin modelo, audio real obligatorio para la corrida, revision humana de calidad y flags que prueban que no se guardan audio, rutas, transcripciones, texto esperado ni nombres de archivos.
- Los templates de preflight y transcripcion real ahora incluyen `--output-dir <pilot-output-dir>` para que la auditoria beta pueda usar el mismo directorio de artifacts.

### Pruebas

- Nuevas pruebas rechazan evidencia de transcripcion real si la tarjeta de comandos no es segura, no usa placeholders o registra contenido privado.

## [0.125.0] - 2026-06-06

### Cambiado

- `tools/output_pilot.py` ahora agrega `system_output_command_card` al reporte de salida audible.
- La evidencia beta de `system_output_audible` exige una tarjeta segura con placeholders, preflight sin audio, operador requerido para salida real y flags que prueban que no se guardan audio, texto hablado, identidad del operador ni rutas locales.
- `tools/pilot_run.py`, `BETA_EVIDENCE_REQUIREMENTS.md`, README y docs HTML reflejan el nuevo contrato de salida audible.

### Pruebas

- Nuevas pruebas rechazan evidencia de salida audible si la tarjeta de comandos no es segura, no usa placeholders o registra contenido privado.

## [0.124.0] - 2026-06-06

### Cambiado

- `tools/beta_readiness.py` ahora exige que la evidencia beta de captura incluya `manual_capture_command_card` segura y compartible.
- La evidencia Windows/WASAPI vuelve a requerir captura real actualizada con `target_capture_backend.available=true`, `capture_backend_ready_required=true`, `--expected-system` y revision de entrada confirmada.
- El contrato `BETA_EVIDENCE_REQUIREMENTS.md` documenta `manual_capture_command_card.safe_to_share`, placeholders y flags que prueban que no se guardan audio, bytes, nombres de dispositivos ni rutas locales.
- Las acciones siguientes de captura Ubuntu/Linux y macOS mencionan `manual-capture-command.md` junto con el checklist manual.

### Pruebas

- Nuevas pruebas rechazan evidencia de captura si la tarjeta de comandos no es segura, usa microfono en preflight o registra contenido privado.

## [0.123.0] - 2026-06-06

### Agregado

- `tools/manual_pilot.py` ahora escribe `manual-capture-command.md`, una tarjeta segura con comandos de setup, preflight sin microfono, captura real y auditoria beta.
- `manual_capture_command_card` queda en el JSON con plantillas de comando, placeholders y flags que confirman que no guarda audio, nombres de dispositivos ni rutas locales.
- `pilot-findings.md` enlaza la tarjeta de comandos para que el operador no tenga que abrir el JSON antes del piloto real.
- Nuevas pruebas verifican el artifact, los placeholders y la ausencia de rutas temporales.

## [0.122.0] - 2026-06-06

### Agregado

- `tools/manual_pilot.py` agrega `beta_evidence_gap` para captura manual en Windows/WASAPI, Ubuntu/Linux y macOS.
- `manual-pilot-report.json`, `pilot-findings.md` y `manual-capture-checklist.md` muestran campos faltantes, conteo y siguiente accion segura para cerrar evidencia beta de captura.
- El gap confirma que no guarda audio, bytes capturados, nombres privados de dispositivos ni rutas locales.
- Nuevas pruebas cubren dry-run y gaps listos para Ubuntu/Linux con `sounddevice` y macOS con `pyaudio`.

## [0.121.0] - 2026-06-06

### Agregado

- `tools/output_pilot.py` agrega `beta_evidence_gap` para el blocker `system_output_audible`.
- `output-pilot-findings.md` y `system-output-next-step.md` muestran campos beta faltantes, conteo y siguiente accion segura para salida audible.
- `next_system_output` propaga el gap y confirma que no guarda audio, texto hablado, identidad del operador ni rutas locales.
- Nuevas pruebas cubren el gap en dry-run y una corrida audible simulada sin reproducir audio real.

## [0.120.0] - 2026-06-06

### Agregado

- `tools/transcription_pilot.py` ahora escribe `real-transcription-command.md`, una tarjeta segura con comandos de preflight, transcripcion real y auditoria beta para MP3/WAV/FLAC propios.
- `next_real_transcription` incluye `preflight_command_template`, `audit_command_template`, `command_artifact` y flags publicos que confirman que no se guardan rutas locales.
- El comando de preflight generado conserva guardas de duracion, `--confirm-audio-reviewed`, `--require-target-backend-ready` y, para OpenAI, timeout 30 con `--require-openai-api-key`.
- Nuevas pruebas verifican que el comando dedicado no filtra nombres/rutas de audio y que la plantilla OpenAI mantiene timeout, duracion y guard de credencial.

## [0.119.0] - 2026-06-06

### Agregado

- `tools/transcription_pilot.py` agrega `beta_evidence_gap` al reporte real/preflight de transcripcion y a `next_real_transcription`.
- `transcription-pilot-findings.md` y `real-transcription-next-step.md` muestran campos beta faltantes, conteo y siguiente accion segura para `real_transcription_quality`.
- Nuevas pruebas cubren el gap en dry-run sintetico, preflight, OpenAI sin credencial y corrida real simulada con evidencia beta lista.

## [0.118.0] - 2026-06-06

### Corregido

- `tools/transcription_pilot.py --real-transcription --require-target-backend-ready` ahora conserva `preflight_readiness.status=ready` cuando los checks previos al modelo pasan.
- La evidencia real de transcripcion ya puede alinearse con el contrato beta que exige `preflight_readiness.ready_for_model_run=true` y `must_rerun_preflight=false`.
- Nueva prueba simula un backend real disponible sin usar Whisper/OpenAI y verifica que el reporte real sigue redactando ruta/nombre del audio.

## [0.117.0] - 2026-06-06

### Agregado

- `tools/pilot_audio_fixture.py --run-preflight` ahora propaga `preflight_readiness` al reporte y findings del fixture.
- El fixture resume si el preflight esta listo para modelo real, si debe repetirse y mantiene flags seguros contra audio, rutas, transcripciones y texto esperado.
- Nuevas pruebas verifican el resumen de readiness en fixture con y sin preflight MP3 disponible.

## [0.116.0] - 2026-06-06

### Agregado

- `tools/beta_readiness.py` ahora exige `preflight_readiness.status=ready` para aceptar evidencia de `real_transcription_quality`.
- El contrato de evidencias beta requiere que `preflight_readiness` confirme modelo listo, sin repeticion pendiente y sin audio, rutas, transcripciones ni texto esperado en artifacts.
- Nuevas pruebas cubren evidencia real de transcripcion con `preflight_readiness` bloqueado y los nuevos campos de requisitos.

## [0.115.0] - 2026-06-06

### Agregado

- `tools/transcription_pilot.py` ahora publica `preflight_readiness`, un resumen seguro con estado `ready`, `needs_backend_install`, `blocked` o `needs_preflight`.
- `transcription-pilot-findings.md` y `real-transcription-next-step.md` muestran si el preflight esta listo para modelo real, si debe repetirse y el comando sanitizado para repetirlo.
- Nuevas pruebas verifican que `preflight_readiness` no guarde rutas, nombres de audio, transcripciones ni texto esperado.

## [0.114.0] - 2026-06-06

### Agregado

- `real-pilot-next-evidence-focus.md` ahora incluye una `Secuencia de preparacion` derivada de `recommended_pilot_sequence`.
- Para el foco `real_transcription_quality`, la tarjeta muestra fixture sintetico, preflight MP3 propio y piloto real antes de auditar evidencias.
- Nuevas pruebas verifican que la secuencia de preparacion quede persistida en JSON y renderizada sin datos privados.

## [0.113.0] - 2026-06-06

### Agregado

- `tools/pilot_run.py` ahora genera `real-pilot-next-evidence-focus.md`, una tarjeta publica dedicada al siguiente blocker beta activo.
- `pilot-plan.md` y `real-pilot-handoff.md` enlazan la tarjeta de foco para que el operador no tenga que buscar dentro de artifacts largos.
- Nuevas pruebas verifican que la tarjeta no registre audio, transcripciones, texto hablado, rutas locales, nombres de dispositivos ni identidad del operador.

## [0.112.0] - 2026-06-06

### Agregado

- `tools/beta_readiness.py --audit-evidence` ahora expone `next_evidence_focus`, elegido desde los blockers beta activos y con campos faltantes publicos.
- `tools/pilot_run.py` propaga ese foco a `beta_readiness`, `evidence_manifest`, `pilot_decision_gate`, `pilot-plan.md`, `real-pilot-evidence-manifest.md` y `real-pilot-decision-gate.md`.
- Nuevas pruebas verifican el foco de evidencia en auditoria JSON/Markdown y en artifacts del piloto seguro.

## [0.111.0] - 2026-06-06

### Agregado

- `tools/pilot_run.py` ahora incorpora `blocker_summaries` del auditor beta dentro de `beta_readiness` y `evidence_manifest`.
- `pilot-plan.md` y `real-pilot-evidence-manifest.md` muestran un resumen por blocker con fuentes que cierran, candidato mas cercano y campos faltantes.
- Nuevas pruebas verifican que el piloto seguro preserve esos resumenes sin rutas locales completas.

## [0.110.0] - 2026-06-06

### Agregado

- `tools/beta_readiness.py --audit-evidence` ahora incluye `blocker_summaries` con estado por blocker, fuentes que cierran evidencia, cantidad de candidatos y candidato mas cercano.
- El Markdown de auditoria agrega `Resumen por blocker` para ver que artifact esta mas cerca de cerrar cada pendiente y que campos faltan, sin exponer rutas absolutas.
- Nuevas pruebas cubren resumen por blocker, candidatos cercanos, campos faltantes y salida publica segura.

## [0.109.0] - 2026-06-06

### Agregado

- `tools/beta_readiness.py` ahora conserva fuentes publicas relativas al directorio `--evidence` para evidencias aceptadas e ignoradas.
- El checklist Markdown muestra una seccion de evidencias aceptadas con artifact y ruta relativa segura, util cuando hay varios `manual-pilot-report.json` por plataforma.
- La auditoria JSON expone `accepted_details` sin rutas absolutas para rastrear lotes de pilotos reales sin publicar carpetas locales.

## [0.108.0] - 2026-06-06

### Agregado

- `tools/pilot_run.py` ahora propaga `conditional_required_fields` desde el contrato beta hacia `next_beta_evidence_steps`, `recommended_pilot_sequence` y `evidence_manifest`.
- `real-pilot-command-pack.md`, `real-pilot-handoff.md`, `pilot-plan.md` y `real-pilot-evidence-manifest.md` muestran los campos condicionales OpenAI que aplican cuando `target_backend.name=openai`.
- El preflight OpenAI del piloto seguro lista `credentials.checked` junto con presencia/requerimiento de `OPENAI_API_KEY` y la garantia `records_openai_api_key=false`.

## [0.107.0] - 2026-06-06

### Agregado

- `tools/beta_readiness.py` ahora exige evidencia sanitizada de credencial cuando un piloto de transcripcion real usa backend `openai`.
- El contrato de evidencias beta agrega campos condicionales para OpenAI: `credentials.checked`, `credentials.openai_api_key_required`, `credentials.openai_api_key_present` y `credentials.records_openai_api_key=false`.
- README, `PILOTS.md`, roadmap y documentacion HTML aclaran que el auditor nunca necesita ni registra el valor de `OPENAI_API_KEY`.

## [0.106.0] - 2026-06-06

### Agregado

- `tools/transcription_pilot.py` ahora acepta `--require-openai-api-key` para validar presencia de `OPENAI_API_KEY` sin guardar el valor de la credencial.
- Los artifacts de transcripcion reportan `credentials.openai_api_key_present`, `credentials.openai_api_key_required` y `credentials.records_openai_api_key=false`.
- La ruta OpenAI del piloto seguro y las plantillas de transcripcion real agregan la guarda de credencial antes de llamadas reales a la API.

## [0.105.0] - 2026-06-06

### Agregado

- `tools/pilot_run.py` ahora incluye comandos seguros especificos para OpenAI en `fixture_preflight_card`, `transcription_readiness_card`, `real-pilot-fixture-preflight.md`, `real-pilot-transcription-readiness.md` y `real-pilot-command-pack.md`.
- El paquete de comandos de pilotos reales ahora separa el fixture/preflight generico de la ruta OpenAI con `--preflight-backend openai`, `--preflight-model gpt-4o-mini-transcribe` y `--preflight-timeout-seconds 30`.
- Nuevas pruebas verifican que el piloto seguro publique la ruta OpenAI sin audio, sin red, sin modelos y con placeholders seguros.

## [0.104.0] - 2026-06-06

### Agregado

- `tools/pilot_audio_fixture.py --run-preflight` ahora acepta `--preflight-backend`, `--preflight-model` y `--preflight-timeout-seconds`.
- El preflight de fixture conserva backend, modelo, timeout y disponibilidad del backend objetivo en el reporte sanitizado y en findings.
- Los ejemplos de pilotos documentan como preparar una plantilla OpenAI con `--timeout-seconds 30` desde un fixture sintetico sin ejecutar red ni modelo.
- Las plantillas CLI de transcripcion formatean valores enteros como `30` en vez de `30.0` para facilitar copiar comandos.

## [0.103.0] - 2026-06-06

### Agregado

- `tools/transcription_pilot.py` ahora acepta `--timeout-seconds` y lo conserva como `transcription_timeout_seconds` en el reporte sanitizado.
- La plantilla `real-transcription-next-step.md` agrega `--timeout-seconds 30` automaticamente cuando el backend objetivo es `openai`.
- Los artifacts de piloto seguro y checklist beta recomiendan timeout explicito para pilotos reales con OpenAI.

## [0.102.0] - 2026-06-06

### Agregado

- `VoiceKitConfig` ahora acepta `transcription_timeout_seconds` y la variable `AURALIS_TRANSCRIPTION_TIMEOUT_SECONDS`.
- El backend `openai` pasa el timeout configurado al cliente `OpenAI(timeout=...)` y lo registra en metadata tecnica como `timeout_seconds`.
- La CLI agrega `--timeout-seconds` en `auralis transcribe` y `auralis transcribe-segments`, con validacion clara para valores invalidos.

## [0.101.0] - 2026-06-06

### Agregado

- `VoiceSessionConfig` ahora acepta `activation_phrases` y `activation_case_sensitive` para filtrar turnos por wake word o frase de activacion.
- `VoiceSession` ahora expone `turn_is_activated()` y acepta `require_activation=True` con `activation_hook` opcional en `transcribe_segments()`, `transcribe_chunks()`, `transcribe_wav()`, `transcribe_file()` y `listen_once()`.
- Nuevas pruebas cubren activacion por frase, activacion por hook externo, normalizacion de una frase individual y rechazo de frases vacias.

## [0.100.0] - 2026-06-06

### Agregado

- `AuralisVoiceKit` ahora incluye una cola simple de salida con `queue_speech()`, `queue_speech_many()`, `drain_output_queue()`, `clear_output_queue()` y `output_queue_size`.
- La cola drena textos en orden usando el backend de salida actual, emite los eventos `output.started` / `output.completed` existentes por cada item y no publica el texto hablado en payloads de eventos.
- Nuevas pruebas cubren drenado en orden, limite de drenado, limpieza de cola, rechazo de limite negativo y retencion del item actual si el backend falla.

## [0.99.3] - 2026-06-06

### Agregado

- `tools/transcription_pilot.py` ahora emite `preflight_decision` para resumir si el preflight de audio propio puede avanzar, debe instalar backend o queda bloqueado.
- `real-transcription-next-step.md`, findings y salida CLI muestran la decision de preflight sin copiar rutas locales, nombres de audio, transcripciones ni texto esperado.
- Nuevas pruebas cubren que la decision bloquee preflights sin guardas de duracion y mantenga artifacts publicos.

## [0.99.2] - 2026-06-06

### Agregado

- `tools/beta_readiness.py` ahora exige que la evidencia beta de salida audible mantenga `operator_checklist.redacts_spoken_text=true`.
- El contrato de salida audible tambien exige no registrar identidad del operador, tener comandos disponibles y usar `next_system_output` con placeholders sin texto hablado.
- `tools/pilot_run.py`, README, `PILOTS.md`, roadmap y documentacion HTML reflejan los nuevos campos requeridos para `system_output_audible`.
- Nuevas pruebas bloquean artifacts de salida audible que omiten redaccion de texto hablado, placeholders o readiness real de comandos.

## [0.99.1] - 2026-06-06

### Agregado

- `tools/beta_readiness.py` ahora exige que la evidencia beta de transcripcion real use audio no sintetico, no sensible y decodificado.
- El contrato de evidencias tambien exige `transcript.text_redacted=true` y redaccion explicita de transcripcion/referencia en `transcription_checklist`.
- `tools/pilot_run.py`, README, `PILOTS.md`, roadmap y documentacion HTML documentan los nuevos campos de privacidad para pilotos reales.
- Nuevas pruebas cubren artifacts que intentan cerrar `real_transcription_quality` con audio sintetico, audio sin decodificar o transcript no redactado.

## [0.99.0] - 2026-06-06

### Agregado

- `tools/beta_readiness.py` ahora exige `audio.duration_gate.enabled=true` y `audio.duration_gate.passed=true` para cerrar el blocker de transcripcion real.
- `BETA_EVIDENCE_REQUIREMENTS.md`, README, `PILOTS.md`, roadmap y documentacion HTML documentan que la evidencia beta de transcripcion debe usar guardas de duracion.
- Nuevas pruebas cubren evidencias de transcripcion real sin guarda de duracion activa.

## [0.98.0] - 2026-06-06

### Agregado

- `tools/beta_readiness.py` ahora exige `target_capture_backend.available=true` y `capture_backend_ready_required=true` para cerrar los blockers de captura Ubuntu/Linux y macOS.
- El contrato `BETA_EVIDENCE_REQUIREMENTS.md`, README, `PILOTS.md` y la documentacion HTML explicitan que la evidencia beta debe probar disponibilidad del backend antes de abrir microfono.
- Nuevas pruebas cubren evidencias de captura con backend no disponible o sin guard estricto.

## [0.97.0] - 2026-06-06

### Agregado

- `tools/manual_pilot.py` ahora reporta `target_capture_backend` y `capture_backend_ready_required` para revisar disponibilidad del backend de captura antes de abrir microfono.
- Nuevo flag `--require-capture-backend-ready` para fallar temprano si falta `sounddevice`, `pyaudio` o el backend seleccionado, con error sanitizado que incluye setup y re-chequeo.
- README, `PILOTS.md`, documentacion HTML y roadmap documentan el guard estricto de captura para pilotos Ubuntu/Linux, macOS y Windows.

## [0.96.0] - 2026-06-06

### Agregado

- `tools/manual_pilot.py` ahora expone `capture_readiness_plan` con comando pip, setup PortAudio por plataforma, `post_install_check` sin microfono y plantilla de captura real.
- Nuevo flag `--target-system` para preparar instrucciones Ubuntu/Linux o macOS sin alterar el sistema real del diagnostico ni cerrar evidencia beta.
- README, `PILOTS.md`, roadmap, documentacion HTML y referencia API documentan la preparacion de captura con `sounddevice`/`pyaudio` en Ubuntu/Linux y macOS.

## [0.95.0] - 2026-06-06

### Agregado

- `tools/output_pilot.py` ahora expone `target_output_backend.readiness_plan` con comandos candidatos, setup por sistema operativo y `post_install_check` sin audio para preparar salida audible `system`.
- El guard `--require-output-backend-ready` ahora incluye setup y comando de re-chequeo cuando falta `powershell`, `say`, `spd-say` o `espeak`.
- README, `PILOTS.md`, documentacion HTML y referencia API documentan la preparacion de salida audible en Windows, Ubuntu/Linux y macOS.

## [0.94.0] - 2026-06-06

### Agregado

- `tools/transcription_pilot.py` ahora expone `target_backend.install_plan` con comando pip del extra opcional, notas Windows/Ubuntu/macOS y `post_install_check` para verificar `--require-target-backend-ready` antes de usar audio/modelos reales.
- Los artifacts `transcription-pilot-findings.md` y `real-transcription-next-step.md` muestran el comando de instalacion y el chequeo posterior sin registrar rutas ni nombres privados.
- README, `PILOTS.md`, roadmap, documentacion HTML y referencia API documentan el plan de instalacion para backends `whisper` y `openai`.

## [0.93.0] - 2026-06-06

### Agregado

- `tools/pilot_run.py` ahora genera `real-pilot-transcription-readiness.md`, una tarjeta segura para preparar transcripcion real antes de ejecutar Whisper/OpenAI u otro backend real.
- El reporte `pilot-report.json` expone `transcription_readiness_card` y `real_pilot_transcription_readiness` con comandos de fixture/preflight/transcripcion real, estado de ffmpeg, disponibilidad de backend objetivo, campos requeridos y condiciones de alto sin registrar audio, transcripciones, texto esperado, rutas locales, nombres de dispositivos ni identidad del operador.
- README, `PILOTS.md`, roadmap, documentacion HTML y referencia API documentan la tarjeta de readiness de transcripcion real como preparacion publica que no cuenta como evidencia beta.

## [0.92.0] - 2026-06-06

### Agregado

- `tools/pilot_run.py` ahora genera `real-pilot-system-output-readiness.md`, una tarjeta segura para preparar la salida audible `system` antes de usar `--speak`.
- El reporte `pilot-report.json` expone `system_output_readiness_card` y `real_pilot_system_output_readiness` con comandos dry-run/audible, artifacts esperados, estado del backend `system`, campos requeridos y condiciones de alto sin registrar audio, texto hablado, rutas locales, nombres de dispositivos ni identidad del operador.
- README, `PILOTS.md`, roadmap, documentacion HTML y referencia API documentan la tarjeta de readiness de salida audible como preparacion publica que no cuenta como evidencia beta.

## [0.91.0] - 2026-06-06

### Agregado

- `tools/pilot_run.py` ahora genera `real-pilot-fixture-preflight.md`, una tarjeta segura para preparar el fixture sintetico de transcripcion y el siguiente preflight con MP3 propio no sensible.
- El reporte `pilot-report.json` expone `fixture_preflight_card` y `real_pilot_fixture_preflight` con comandos, artifacts esperados, estado de ffmpeg, checks de backend y condiciones de alto sin registrar audio, transcripciones, texto esperado, rutas locales ni identidad del operador.
- README, `PILOTS.md`, roadmap, documentacion HTML y referencia API documentan la tarjeta de preflight de fixture como preparacion publica que no cuenta como evidencia beta.

## [0.90.0] - 2026-06-06

### Agregado

- `tools/pilot_run.py` ahora genera `real-pilot-decision-gate.md` con go/no-go separado para pilotos reales, beta y version estable.
- El reporte `pilot-report.json` expone `pilot_decision_gate` y `real_pilot_decision_gate`, incluyendo siguiente paso recomendado, condiciones de alto y advertencias de entorno sin registrar audio, transcripciones, texto hablado, rutas locales ni identidad del operador.
- README, `PILOTS.md`, roadmap, documentacion HTML y referencia API documentan la compuerta de decision para operadores.

## [0.89.0] - 2026-06-06

### Agregado

- `tools/pilot_run.py` ahora genera `real-pilot-evidence-manifest.md` para cruzar blockers beta pendientes/cerrados, artifacts JSON esperados, campos requeridos, evidencias aceptadas/ignoradas y auditoria estricta.
- El reporte `pilot-report.json` expone `evidence_manifest` y `real_pilot_evidence_manifest` con politica segura: no cuenta como evidencia beta, no registra audio, transcripciones, texto hablado, rutas locales, nombres de dispositivos ni identidad del operador.
- README, `PILOTS.md`, roadmap, documentacion HTML y referencia API documentan el manifiesto de evidencias para pilotos reales.

## [0.88.0] - 2026-06-06

### Agregado

- `tools/pilot_run.py` ahora genera `real-pilot-environment-checklist.md` para revisar Python, ffmpeg, salida `system` y backends opcionales antes de pilotos reales.
- El reporte JSON del piloto seguro expone `environment_checklist` y `real_pilot_environment_checklist`, marcando este preflight como `usable_as_beta_evidence=false`.

## [0.87.0] - 2026-06-06

### Agregado

- `tools/pilot_run.py` ahora genera `real-pilot-command-pack.md`, un paquete seguro de comandos por plataforma para pilotos reales.
- El reporte JSON del piloto seguro expone `real_pilot_command_pack` con politica de contenido, campos requeridos, guards estrictos y auditoria final.

## [0.86.0] - 2026-06-06

### Cambiado

- `tools/pilot_run.py` ahora expone `strict_backend_guard_required`, `strict_backend_guard_flag` y `strict_backend_guard_field` en la secuencia recomendada y la matriz de pilotos reales.
- `pilot-plan.md` y `real-pilot-handoff.md` muestran explicitamente el flag y el campo JSON que debe conservar cada guard estricto de backend.

## [0.85.0] - 2026-06-06

### Cambiado

- `tools/beta_readiness.py` ahora exige `target_backend_ready_required=true` y `output_backend_ready_required=true` para cerrar evidencias beta reales con los guards estrictos de backend.
- `tools/pilot_run.py` documenta esos guards estrictos en la matriz de pilotos reales.

## [0.84.0] - 2026-06-06

### Cambiado

- `tools/beta_readiness.py` ahora exige `target_backend.available=true` para que una evidencia real de transcripcion pueda cerrar el blocker `real_transcription_quality`.
- `tools/pilot_run.py` agrega `target_backend.available` al preflight recomendado de transcripcion y a la matriz de pilotos reales.

## [0.83.0] - 2026-06-06

### Agregado

- `tools/output_pilot.py` ahora reporta `target_output_backend` con disponibilidad, dependencias y razon del backend `system`.
- Flag `tools/output_pilot.py --require-output-backend-ready` para fallar temprano, con error sanitizado, si el comando de voz del sistema no esta disponible antes de un piloto audible.

## [0.82.0] - 2026-06-06

### Agregado

- Flag `tools/transcription_pilot.py --require-target-backend-ready` para fallar temprano, con error sanitizado, cuando el backend objetivo de transcripcion no tenga sus dependencias opcionales instaladas.
- El comando plantilla de `real-transcription-next-step.md` ahora incluye el gate estricto de backend antes de ejecutar Whisper/OpenAI.

## [0.81.0] - 2026-06-06

### Cambiado

- `tools/transcription_pilot.py --preflight-only` ahora reporta `target_backend` con disponibilidad, dependencias y razon del backend objetivo antes de ejecutar una transcripcion real.
- `transcription-pilot-findings.md` y `real-transcription-next-step.md` indican revisar `target_backend.available=true` para detectar extras faltantes como `auralisvoicekit[whisper]` u `auralisvoicekit[openai]` sin exponer audio privado.

## [0.80.0] - 2026-06-06

### Cambiado

- `tools/transcription_pilot.py --preflight-only` ahora valida que el backend objetivo de transcripcion este registrado antes de preparar el siguiente paso real.
- El preflight de transcripcion evita generar tarjetas de piloto real con nombres de backend invalidos y devuelve el listado de backends disponibles.

## [0.79.0] - 2026-06-06

### Cambiado

- La evidencia beta de captura en Ubuntu/Linux y macOS ahora acepta `sounddevice` o `pyaudio`, manteniendo WASAPI como requisito dedicado para Windows.
- `manual_pilot.py`, `beta_readiness.py`, el plan de pilotos y la documentacion publica ahora reflejan el backend PyAudio como ruta valida para pilotos reales multiplataforma.

## [0.78.0] - 2026-06-06

### Agregado

- Backend opcional `pyaudio` para captura PCM16, con listado de dispositivos, seleccion por id/nombre/default y cierre robusto de streams.
- Extra `auralisvoicekit[pyaudio]` y diagnostico `doctor` para reportar la dependencia opcional sin romper el paquete base.

### Cambiado

- README, roadmap, docs HTML y stability gate ahora documentan y verifican la compatibilidad opcional con PyAudio.

## [0.77.0] - 2026-06-06

### Agregado

- `BETA_EVIDENCE_REQUIREMENTS.md` como contrato versionado y seguro de evidencias JSON para pilotos reales antes de beta.

### Cambiado

- Gate de estabilidad, README, roadmap y docs HTML ahora verifican y enlazan el contrato de evidencias beta.

## [0.76.0] - 2026-06-06

### Cambiado

- CI desactiva la cache de pip con `PIP_NO_CACHE_DIR=1` y el aviso de version de pip para evitar warnings no bloqueantes de cache corrupta durante `actions/setup-python` en macOS.
- Gate de estabilidad y pruebas de workflows ahora verifican la configuracion de pip sin cache en CI.

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
