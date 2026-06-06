# Pilotos de AuralisVoiceKit

Este documento define como ejecutar pilotos seguros antes de acercarse a beta o `1.0.0`.

## Piloto automatizado seguro

Este piloto no abre microfono, no reproduce audio real, no usa red y no descarga modelos. Sirve para validar que el paquete esta listo para una prueba manual controlada.

Nota `v0.105.0`: el piloto seguro separa la ruta generica y la ruta OpenAI en `fixture_preflight_card`, `transcription_readiness_card`, `platform_pilot_matrix` y `real-pilot-command-pack.md`. Los comandos OpenAI usan `--preflight-backend openai`, `gpt-4o-mini-transcribe` y timeout 30 como plantilla segura sin ejecutar red ni modelo durante el preflight.

Nota `v0.106.0`: para OpenAI, agrega `--require-openai-api-key`; el reporte solo conserva `credentials.openai_api_key_present` y `credentials.records_openai_api_key=false`, nunca el valor de `OPENAI_API_KEY`.

Nota `v0.107.0`: la evidencia beta de transcripcion con backend `openai` debe conservar `credentials.checked=true`, `credentials.openai_api_key_required=true`, `credentials.openai_api_key_present=true` y `credentials.records_openai_api_key=false`; el valor de `OPENAI_API_KEY` sigue fuera de artifacts.

Nota `v0.108.0`: `tools/pilot_run.py` conserva esos campos como `conditional_required_fields` en el JSON y los muestra en `pilot-plan.md`, `real-pilot-command-pack.md`, `real-pilot-handoff.md` y `real-pilot-evidence-manifest.md` para que la ruta OpenAI no se ejecute sin evidencia sanitizada de credencial.

Nota `v0.109.0`: `tools/beta_readiness.py` lista evidencias aceptadas con fuentes relativas al directorio `--evidence`, por ejemplo `linux/manual-pilot-report.json`, sin rutas absolutas. English: accepted and ignored evidence sources are relative, public-safe paths so duplicated artifact names can be traced by platform.

Nota `v0.110.0`: `tools/beta_readiness.py --audit-evidence` agrega `blocker_summaries` y un `Resumen por blocker` en Markdown para mostrar candidato mas cercano y campos faltantes sin exponer contenido privado. English: evidence audits now summarize the closest candidate per beta blocker.

Nota `v0.111.0`: `tools/pilot_run.py` conserva esos `blocker_summaries` en `pilot-report.json` y los muestra en `pilot-plan.md` y `real-pilot-evidence-manifest.md`. English: safe-pilot artifacts now show per-blocker evidence summaries for operators.

Nota `v0.112.0`: `tools/beta_readiness.py --audit-evidence` y `tools/pilot_run.py` publican `next_evidence_focus` para mostrar el primer blocker beta activo, campos faltantes y candidato mas cercano sin rutas locales. English: operators now get a public-safe next evidence focus.

Nota `v0.113.0`: `tools/pilot_run.py` genera `real-pilot-next-evidence-focus.md`, una tarjeta dedicada para abrir el foco de evidencia sin recorrer todo el plan. English: safe pilots now write a focused next-evidence card.

Nota `v0.114.0`: la tarjeta `real-pilot-next-evidence-focus.md` incluye `Secuencia de preparacion` con los pasos seguros previos al piloto real enfocado. English: the focus card now shows the safe preparation sequence.

Nota `v0.115.0`: `tools/transcription_pilot.py` agrega `preflight_readiness` a `transcription-pilot-report.json`, `transcription-pilot-findings.md` y `real-transcription-next-step.md`, con estado listo/bloqueado/instalar backend/repetir preflight y un comando de repeticion sanitizado. English: transcription preflights now include a share-safe readiness summary.

Nota `v0.116.0`: el auditor beta ahora exige `preflight_readiness.status=ready`, `ready_for_model_run=true`, `must_rerun_preflight=false` y flags de privacidad seguros para cerrar `real_transcription_quality`. English: beta evidence requires a ready transcription preflight.

Nota `v0.117.0`: el fixture sintetico con `--run-preflight` muestra `preflight_readiness` en `pilot-audio-fixture-report.json` y `pilot-audio-fixture-findings.md`, para decidir si instalar backend o repetir preflight antes del MP3 real. English: fixture preflights surface readiness without opening the nested report.

Nota `v0.118.0`: la corrida real de transcripcion con `--require-target-backend-ready` mantiene `preflight_readiness.status=ready` si audio, backend, credenciales y guardas pasan antes del modelo. English: guarded real transcription reports can now satisfy the beta preflight-readiness contract.

Nota `v0.119.0`: `transcription-pilot-report.json`, `transcription-pilot-findings.md` y `real-transcription-next-step.md` incluyen `beta_evidence_gap` para listar campos faltantes y siguiente accion segura antes de auditar beta. English: transcription pilots now expose public-safe beta evidence gaps.

Nota `v0.120.0`: `tools/transcription_pilot.py` escribe `real-transcription-command.md` con comandos seguros de preflight MP3/WAV/FLAC, transcripcion real y auditoria beta; el preflight dedicado incluye revision de audio, guardas de duracion y guard estricto de backend. English: real transcription pilots now write a dedicated command card for the operator.

Nota `v0.121.0`: `tools/output_pilot.py` agrega `beta_evidence_gap` a `output-pilot-report.json`, `output-pilot-findings.md` y `system-output-next-step.md` para listar campos faltantes y siguiente accion segura de `system_output_audible`. English: system output pilots now expose public-safe beta evidence gaps.

Nota `v0.122.0`: `tools/manual_pilot.py` agrega `beta_evidence_gap` a `manual-pilot-report.json`, `pilot-findings.md` y `manual-capture-checklist.md` para captura Windows/WASAPI, Ubuntu/Linux y macOS sin guardar audio, nombres de dispositivos ni rutas locales. English: manual capture pilots now expose public-safe beta evidence gaps.

Nota `v0.123.0`: `tools/manual_pilot.py` escribe `manual-capture-command.md` y `manual_capture_command_card` con setup, preflight sin microfono, captura real y auditoria beta usando placeholders. English: manual capture pilots now write a public-safe command card.

Nota `v0.127.0`: `tools/beta_readiness.py --audit-evidence` agrega `privacy_audit` para detectar campos crudos sospechosos en artifacts JSON aceptados, como `transcript.text`, `expected_text`, `spoken_text`, `audio.path`, nombres de archivo sin redaccion o credenciales. El reporte muestra solo rutas de campos y motivos, nunca valores privados. English: evidence audits now block beta on suspicious raw fields without printing private values.

Nota `v0.128.0`: `tools/pilot_run.py` muestra `privacy_audit` en `pilot-report.json`, `pilot-plan.md`, `real-pilot-evidence-manifest.md` y `real-pilot-decision-gate.md`; si el escaneo falla, la compuerta beta queda bloqueada aunque el artifact JSON cierre un blocker funcional. English: safe-pilot artifacts now surface privacy-audit blockers before beta decisions.

```powershell
py tools\pilot_run.py --output-dir pilot_runs\safe --json
py tools\pilot_run.py --output-dir pilot_runs\safe --evidence pilot_runs\manual --evidence pilot_runs\output --evidence pilot_runs\transcription --json
```

El reporte generado incluye:

- estado de `tools/stability_gate.py`;
- diagnostico `doctor` con backend `wav`;
- demo de asistente local con logs sanitizados;
- demo de salida `system` en dry-run;
- benchmark offline exportado a JSON y CSV;
- resumen `beta_readiness`, `privacy_audit`, `next_evidence_focus` y pasos `next_beta_evidence_steps` para cerrar blockers beta con metadatos de guard backend estricto cuando aplica;
- campo `recommended_pilot_sequence` con el orden recomendado para pilotos reales, checklist de captura, checklist de operador para salida audible, fixture sintetico, preflight MP3 de transcripcion, checklist de revision de transcripcion, auditoria estricta, refresco del checklist beta y metadatos `strict_backend_guard_required`, `strict_backend_guard_flag` y `strict_backend_guard_field`;
- campo `platform_pilot_matrix` y seccion `Matriz por plataforma` para separar comandos Windows, Ubuntu/Linux, macOS, salida audible, transcripcion MP3 y guards estrictos de backend;
- artifacts `pilot-plan.md`, `real-pilot-handoff.md`, `real-pilot-command-pack.md`, `real-pilot-environment-checklist.md`, `real-pilot-fixture-preflight.md`, `real-pilot-transcription-readiness.md`, `real-pilot-system-output-readiness.md`, `real-pilot-evidence-manifest.md`, `real-pilot-decision-gate.md`, `real-pilot-next-evidence-focus.md` y `real-pilot-findings-template.md` con evidencias JSON aceptadas/ignoradas, `privacy_audit`, `fixture_preflight_card`, `transcription_readiness_card`, `system_output_readiness_card`, `evidence_manifest`, `pilot_decision_gate`, `next_evidence_focus`, `real_pilot_next_evidence_focus`, `next_evidence_focus_preparation_sequence`, secuencia recomendada, comandos pendientes, campos JSON requeridos, una tarjeta de traspaso segura para el operador, un paquete de comandos por plataforma, un checklist de entorno sin evidencia beta, una tarjeta de preflight de fixture sin evidencia beta, una tarjeta de readiness de transcripcion real sin evidencia beta, una tarjeta de readiness de salida audible sin evidencia beta, un manifiesto de evidencias pendientes/cerradas y escaneo de privacidad sin evidencia beta, una compuerta go/no-go para pilotos reales/beta/estable, una tarjeta del siguiente foco de evidencia con secuencia de preparacion y una plantilla sanitizada para `PILOT_FINDINGS.md`;
- lista de pasos manuales pendientes.

`pilot-plan.md`, `real-pilot-handoff.md`, `real-pilot-command-pack.md`, `real-pilot-environment-checklist.md`, `real-pilot-fixture-preflight.md`, `real-pilot-transcription-readiness.md`, `real-pilot-system-output-readiness.md`, `real-pilot-evidence-manifest.md`, `real-pilot-decision-gate.md` y `real-pilot-findings-template.md` estan pensados para compartirse en el equipo sin audio, transcripciones, texto hablado real, rutas locales completas, nombres reales de dispositivos ni identidad del operador.

## Piloto manual guiado

Este piloto genera bundle doctor, analisis `doctor-bundles`, reporte JSON, Markdown de hallazgos, `manual-capture-checklist.md` y `manual-capture-command.md`. Por defecto no abre el microfono; `--capture-test` es obligatorio para una prueba real de captura. Usa `--target-system Linux` o `--target-system Darwin` para preparar instrucciones de captura sin cambiar el sistema real del diagnostico, y `--expected-system Windows`, `--expected-system Linux` o `--expected-system Darwin` para confirmar que el artifact se genero en la plataforma esperada. El reporte incluye `target_capture_backend`, `capture_backend_ready_required`, `capture_readiness_plan` con `pip_command`, setup por sistema, `post_install_check`, `post_install_check_uses_microphone=false`, `real_capture_check_template`, `beta_evidence_gap` con campos faltantes, conteo y siguiente accion segura, y `manual_capture_command_card` con plantillas de setup, preflight sin microfono, captura real y auditoria beta; `--require-capture-backend-ready` falla temprano si falta el extra opcional antes de abrir microfono. Ubuntu/Linux documenta `libportaudio2` para `sounddevice` o `portaudio19-dev python3-dev` para `pyaudio`, y macOS documenta `brew install portaudio`. `--confirm-input-reviewed` se usa solo despues de revisar permisos del microfono, dispositivo de entrada y un entorno no sensible. En Ubuntu/Linux y macOS la evidencia beta acepta `--backend sounddevice` o `--backend pyaudio`; Windows mantiene `--backend wasapi`. El reporte no guarda bytes de audio, nombres privados de dispositivos ni rutas locales, y redacta el selector de dispositivo cuando no es `default` o un id numerico. English: capture readiness can be prepared and guarded without microphone access; beta capture evidence requires `system_guard.expected_system_matched=true`, `capture_backend=sounddevice|pyaudio` on Ubuntu/Linux and macOS, `target_capture_backend.available=true`, `capture_backend_ready_required=true`, `input_review_confirmed=true`, `capture_checklist.input_review_confirmed=true` and `capture_checklist.ready_for_beta_evidence=true`.

```powershell
py tools\manual_pilot.py --output-dir pilot_runs\manual\windows-safe --json
py tools\manual_pilot.py --backend sounddevice --target-system Linux --require-capture-backend-ready --json
py tools\manual_pilot.py --backend pyaudio --target-system Darwin --require-capture-backend-ready --json
py tools\manual_pilot.py --capture-test --backend wasapi --device default --sample-rate 48000 --expected-system Windows --confirm-input-reviewed --require-capture-backend-ready --json
py tools\manual_pilot.py --capture-test --backend sounddevice --device default --expected-system Linux --confirm-input-reviewed --require-capture-backend-ready --json
py tools\manual_pilot.py --capture-test --backend pyaudio --device default --expected-system Linux --confirm-input-reviewed --require-capture-backend-ready --json
py tools\manual_pilot.py --capture-test --backend sounddevice --device default --expected-system Darwin --confirm-input-reviewed --require-capture-backend-ready --json
py tools\manual_pilot.py --capture-test --backend pyaudio --device default --expected-system Darwin --confirm-input-reviewed --require-capture-backend-ready --json
py tools\output_pilot.py --output-dir pilot_runs\output\system-dry-run --json
py tools\output_pilot.py --speak --operator-present --confirm-audible --confirm-text-reviewed --confirm-voice-reviewed --require-output-backend-ready --expected-system "Windows|Linux|Darwin" --output-dir pilot_runs\output\system-real --text "Hola desde AuralisVoiceKit" --json
py tools\transcription_pilot.py --output-dir pilot_runs\transcription\safe --json
py tools\transcription_pilot.py --output-dir pilot_runs\transcription\quality-safe --expected-text "Hola desde AuralisVoiceKit" --min-word-accuracy 0 --json
py tools\pilot_audio_fixture.py --output-dir pilot_runs\transcription\fixture --format wav --format mp3 --run-preflight --json
py tools\pilot_audio_fixture.py --output-dir pilot_runs\transcription\fixture-openai --format mp3 --run-preflight --preflight-backend openai --preflight-model gpt-4o-mini-transcribe --preflight-timeout-seconds 30 --json
py tools\transcription_pilot.py --preflight-only --audio sample.mp3 --audio-non-sensitive --backend whisper --normalize --min-audio-seconds 0.2 --max-audio-seconds 60 --json
py tools\transcription_pilot.py --preflight-only --audio sample.mp3 --audio-non-sensitive --backend openai --model gpt-4o-mini-transcribe --normalize --timeout-seconds 30 --require-openai-api-key --min-audio-seconds 0.2 --max-audio-seconds 60 --json
py -m pip install "auralisvoicekit[whisper]"
py tools\transcription_pilot.py --preflight-only --audio sample.mp3 --audio-non-sensitive --confirm-audio-reviewed --backend whisper --model base --min-audio-seconds 0.2 --max-audio-seconds 60 --require-target-backend-ready --json
py tools\transcription_pilot.py --real-transcription --audio sample.mp3 --audio-non-sensitive --confirm-audio-reviewed --confirm-reference-reviewed --backend whisper --model base --normalize --expected-text "Hola desde AuralisVoiceKit" --min-word-accuracy 0.75 --min-audio-seconds 0.2 --max-audio-seconds 60 --confirm-quality-reviewed --require-target-backend-ready --json
py tools\transcription_pilot.py --real-transcription --audio sample.mp3 --audio-non-sensitive --confirm-audio-reviewed --confirm-reference-reviewed --backend openai --model gpt-4o-mini-transcribe --timeout-seconds 30 --expected-text-file <expected-text-path> --min-word-accuracy 0.75 --min-audio-seconds 0.2 --max-audio-seconds 60 --confirm-quality-reviewed --require-target-backend-ready --require-openai-api-key --json
py tools\beta_readiness.py --output BETA_CHECKLIST.md --json
py tools\beta_readiness.py --requirements
py tools\beta_readiness.py --audit-evidence --evidence pilot_runs\manual --evidence pilot_runs\output --evidence pilot_runs\transcription --json
py tools\beta_readiness.py --audit-evidence --evidence pilot_runs\manual --evidence pilot_runs\output --evidence pilot_runs\transcription --fail-on-audit-gaps --json
py tools\beta_readiness.py --evidence pilot_runs\manual --evidence pilot_runs\output --evidence pilot_runs\transcription --output BETA_CHECKLIST.md --json
```

`tools/output_pilot.py` no reproduce audio por defecto. El dry-run genera `output-operator-checklist.md`, `system-output-next-step.md`, `system_guard`, `target_output_backend`, `target_output_backend.readiness_plan`, `spoken_text_privacy_scan` y el bloque JSON `operator_checklist` para preparar el piloto audible sin registrar identidad del operador ni texto privado. El readiness plan enumera comandos candidatos (`powershell`, `say`, `spd-say` o `espeak`), setup por sistema y un `post_install_check` con `--require-output-backend-ready` que no reproduce audio; en Ubuntu/Linux documenta `sudo apt-get install -y speech-dispatcher espeak`. English: system output readiness includes OS-specific setup and a non-audible post-install check. La tarjeta de siguiente paso usa `<public-spoken-text>` como placeholder para no copiar texto hablado real en artifacts compartidos. El audio real requiere `--speak --operator-present`; para cerrar el blocker beta tambien debe usarse `--confirm-audible` cuando el operador confirme que escucho la salida, `--confirm-text-reviewed` despues de revisar que el texto hablado sea publico/no sensible, `--confirm-voice-reviewed` despues de revisar voz, volumen y pronunciacion, `--require-output-backend-ready` para fallar temprano si falta el comando de voz, y `--expected-system "Windows|Linux|Darwin"` para confirmar que la prueba se hizo en una plataforma soportada. La evidencia JSON debe incluir `system_guard.expected_system_matched=true`, `target_output_backend.available=true`, `output_backend_ready_required=true`, `text_review_confirmed=true`, `spoken_text_privacy_scan.passed=true`, `voice_review_confirmed=true`, `operator_checklist.expected_system_matched=true`, `operator_checklist.records_operator_identity=false`, `operator_checklist.redacts_spoken_text=true`, `operator_checklist.text_review_confirmed=true`, `operator_checklist.spoken_text_privacy_scan_passed=true`, `operator_checklist.voice_review_confirmed=true`, `operator_checklist.commands_available=true`, `operator_checklist.ready_for_real_audio=true`, `operator_checklist.ready_for_beta_evidence=true`, `next_system_output.uses_placeholders=true`, `next_system_output.records_spoken_text=false` y `next_system_output.records_operator_identity=false`. `--system` es solo para dry-runs y no se acepta con `--speak`. El reporte JSON y el Markdown redactan el texto completo dentro de comandos como `<text-redacted>`; el scan de texto hablado solo guarda estado, conteo y tipos de riesgo.

`tools/pilot_audio_fixture.py` genera audio sintetico publico en WAV/MP3/FLAC para ensayar ffmpeg; con `--run-preflight` tambien ejecuta un preflight seguro contra el MP3 generado. Marca `usable_as_beta_evidence=false` para no confundirlo con evidencia real. El preflight del fixture acepta `--preflight-backend`, `--preflight-model` y `--preflight-timeout-seconds`, util para generar una tarjeta OpenAI con `--timeout-seconds 30` sin red ni modelo. `tools/transcription_pilot.py` genera audio sintetico y usa `null` por defecto. `--preflight-only --audio PATH --audio-non-sensitive` decodifica MP3/FLAC/WAV, valida que el backend objetivo este registrado, reporta `target_backend.available`, `target_backend_ready_required`, dependencias, razon de instalacion y `target_backend.install_plan` con `pip_command`, notas Windows/Ubuntu/macOS y `post_install_check`, emite `preflight_decision` con `decision`, `blocking_reasons`, `backend_ready` y `next_action`, y escribe metadata sanitizada sin ejecutar Whisper/OpenAI; sirve para detectar problemas de ffmpeg, extras faltantes o nombres de backend antes del piloto real. `--require-target-backend-ready` vuelve obligatoria esa disponibilidad y falla con un error sanitizado si falta el extra del backend, incluyendo `python -m pip install "auralisvoicekit[whisper]"` o `python -m pip install "auralisvoicekit[openai]"` cuando aplique. `--require-openai-api-key` agrega una guarda de presencia de `OPENAI_API_KEY` para OpenAI sin guardar la credencial: solo publica `credentials.openai_api_key_present` y `credentials.records_openai_api_key=false`. English: fixture preflights can target OpenAI or Whisper and keep model/timeout/credential-presence details sanitized in the next-step artifact. Cada corrida escribe `transcription-review-checklist.md`, `real-transcription-next-step.md`, `real-transcription-command.md` y `transcription_checklist` para revisar privacidad, duracion, referencia, comandos y calidad sin copiar audio ni texto privado; las tarjetas usan placeholders como `<audio-path>`, `<expected-text-path>` y `<pilot-output-dir>`. `real-transcription-command.md` separa preflight MP3/WAV/FLAC, corrida real y auditoria beta. `--min-audio-seconds` y `--max-audio-seconds` agregan una guarda publica de duracion para rechazar audios vacios o demasiado largos antes de continuar. Los backends reales `whisper` y `openai` requieren `--real-transcription --audio PATH --audio-non-sensitive`; la evidencia beta exige `target_backend.available=true`, `target_backend_ready_required=true`, `audio.generated_synthetic_audio=false`, `audio.audio_confirmed_non_sensitive=true`, `audio.decoded=true`, `audio.audio_file_name_redacted=true`, `audio.duration_gate.enabled=true`, `audio.duration_gate.passed=true`, `transcript.text_redacted=true`, `--confirm-audio-reviewed` despues de revisar privacidad del audio, `--confirm-reference-reviewed` despues de revisar privacidad del texto esperado, `reference_privacy_scan.passed=true` sin riesgos de email/URL/secretos/numeros largos y `--confirm-quality-reviewed` despues de una revision humana local de calidad. Si el backend real es OpenAI, tambien usa `--require-openai-api-key` antes de la llamada real. El texto transcrito, el nombre del audio, el nombre del archivo de referencia y el valor de la credencial no se guardan completos en artifacts; el checklist exige `transcription_checklist.redacts_transcript_text=true` y `transcription_checklist.redacts_expected_text=true`; el scan de referencia solo guarda estado, conteo y tipos de riesgo. Con `--expected-text` o `--expected-text-file` calcula word accuracy, word error rate y character error rate sin guardar la transcripcion ni la referencia completa.

`tools/beta_readiness.py` no ejecuta hardware ni red. Lee el gate, `PILOT_FINDINGS.md` y artifacts JSON pasados con `--evidence`, genera `BETA_CHECKLIST.md` y marca blockers hasta que haya evidencia real de transcripcion, salida audible y pilotos Ubuntu/Linux y macOS. `--requirements` imprime los campos JSON esperados por cada blocker, incluidos `system_guard.expected_system_matched`, `capture_backend=sounddevice|pyaudio` en Ubuntu/Linux y macOS, `input_review_confirmed`, `capture_checklist.input_review_confirmed` y `capture_checklist.ready_for_beta_evidence` para captura real, `target_backend.available`, `target_backend_ready_required`, `audio.generated_synthetic_audio`, `audio.audio_confirmed_non_sensitive`, `audio.decoded`, `audio.audio_file_name_redacted`, `audio.duration_gate.enabled`, `audio.duration_gate.passed`, `transcript.text_redacted`, `audio_review_confirmed`, `reference_review_confirmed`, `reference_privacy_scan.passed`, `quality_review_confirmed`, `transcription_checklist.audio_review_confirmed`, `transcription_checklist.records_audio_file_name`, `transcription_checklist.records_expected_text_file_name`, `transcription_checklist.redacts_transcript_text`, `transcription_checklist.redacts_expected_text`, `transcription_checklist.reference_review_confirmed`, `transcription_checklist.reference_privacy_scan_passed`, `transcription_checklist.quality_review_confirmed` y `transcription_checklist.ready_for_beta_evidence` para transcripcion real, y, si `target_backend.name=openai`, `credentials.checked`, `credentials.openai_api_key_required`, `credentials.openai_api_key_present` y `credentials.records_openai_api_key=false`; tambien exige `system_guard.expected_system_matched`, `target_output_backend.available`, `output_backend_ready_required`, `text_review_confirmed`, `spoken_text_privacy_scan.passed`, `voice_review_confirmed`, `operator_checklist.expected_system_matched`, `operator_checklist.records_operator_identity`, `operator_checklist.redacts_spoken_text`, `operator_checklist.text_review_confirmed`, `operator_checklist.spoken_text_privacy_scan_passed`, `operator_checklist.voice_review_confirmed`, `operator_checklist.commands_available`, `operator_checklist.ready_for_real_audio`, `operator_checklist.ready_for_beta_evidence`, `next_system_output.uses_placeholders`, `next_system_output.records_spoken_text` y `next_system_output.records_operator_identity` para salida audible; `--audit-evidence` revisa artifacts reales, resume blockers cerrados/pendientes y explica que campo falta; `--fail-on-audit-gaps` devuelve codigo 1 si quedan blockers o artifacts ignorados. Las evidencias se toman de `manual-pilot-report.json`, `output-pilot-report.json` y `transcription-pilot-report.json`; solo cuentan si declaran `project: AuralisVoiceKit`. El checklist reporta evidencias ignoradas con motivos seguros (`missing_project`, `wrong_project`, `not_json_object`) y no copia transcripciones, nombres de archivos privados, rutas completas ni valores de credenciales. English: strict evidence audit requires target transcription backend availability, OpenAI credential-presence proof without the API key value, human-reviewed capture input with sounddevice or pyaudio on Ubuntu/Linux and macOS, passing reference privacy scan, reviewed spoken output text and output quality without exposing private audio, transcripts, file names, spoken text or full local paths.

Los hallazgos resumidos se mantienen en:

```text
PILOT_FINDINGS.md
BETA_CHECKLIST.md
```

## Checklist manual

Ejecutar estos pasos solo cuando haya hardware, permisos y tiempo para revisar resultados.

```powershell
auralis doctor --devices --backend sounddevice --json
auralis doctor --capture-test --backend sounddevice --device default --bundle pilot_runs\manual\doctor-capture.json --json
auralis doctor-bundles pilot_runs\manual\doctor-capture.json --output pilot_runs\manual\doctor-analysis.json --json
python tools\manual_pilot.py --backend sounddevice --target-system Linux --require-capture-backend-ready --json
python tools\manual_pilot.py --backend pyaudio --target-system Darwin --require-capture-backend-ready --json
python tools\manual_pilot.py --capture-test --backend wasapi --device default --sample-rate 48000 --expected-system Windows --confirm-input-reviewed --require-capture-backend-ready --json
python tools\manual_pilot.py --capture-test --backend sounddevice --device default --expected-system Linux --confirm-input-reviewed --require-capture-backend-ready --json
python tools\manual_pilot.py --capture-test --backend pyaudio --device default --expected-system Linux --confirm-input-reviewed --require-capture-backend-ready --json
python tools\manual_pilot.py --capture-test --backend sounddevice --device default --expected-system Darwin --confirm-input-reviewed --require-capture-backend-ready --json
python tools\manual_pilot.py --capture-test --backend pyaudio --device default --expected-system Darwin --confirm-input-reviewed --require-capture-backend-ready --json
python tools\output_pilot.py --output-dir pilot_runs\output\system-dry-run --json
python tools\output_pilot.py --speak --operator-present --confirm-audible --confirm-text-reviewed --confirm-voice-reviewed --require-output-backend-ready --expected-system "Windows|Linux|Darwin" --output-dir pilot_runs\output\system-real --text "Hola desde AuralisVoiceKit" --json
python tools\pilot_audio_fixture.py --output-dir pilot_runs\transcription\fixture --format wav --format mp3 --run-preflight --json
python tools\pilot_audio_fixture.py --output-dir pilot_runs\transcription\fixture-openai --format mp3 --run-preflight --preflight-backend openai --preflight-model gpt-4o-mini-transcribe --preflight-timeout-seconds 30 --json
python tools\transcription_pilot.py --preflight-only --audio sample.mp3 --audio-non-sensitive --backend whisper --normalize --min-audio-seconds 0.2 --max-audio-seconds 60 --json
python tools\transcription_pilot.py --preflight-only --audio sample.mp3 --audio-non-sensitive --backend openai --model gpt-4o-mini-transcribe --normalize --timeout-seconds 30 --require-openai-api-key --min-audio-seconds 0.2 --max-audio-seconds 60 --json
python -m pip install "auralisvoicekit[whisper]"
python tools\transcription_pilot.py --preflight-only --audio sample.mp3 --audio-non-sensitive --confirm-audio-reviewed --backend whisper --model base --min-audio-seconds 0.2 --max-audio-seconds 60 --require-target-backend-ready --json
python tools\transcription_pilot.py --real-transcription --audio sample.mp3 --audio-non-sensitive --confirm-audio-reviewed --confirm-reference-reviewed --backend whisper --model base --normalize --expected-text "Hola desde AuralisVoiceKit" --min-word-accuracy 0.75 --min-audio-seconds 0.2 --max-audio-seconds 60 --confirm-quality-reviewed --require-target-backend-ready --json
python tools\transcription_pilot.py --real-transcription --audio sample.mp3 --audio-non-sensitive --confirm-audio-reviewed --confirm-reference-reviewed --backend openai --model gpt-4o-mini-transcribe --timeout-seconds 30 --expected-text-file <expected-text-path> --min-word-accuracy 0.75 --min-audio-seconds 0.2 --max-audio-seconds 60 --confirm-quality-reviewed --require-target-backend-ready --require-openai-api-key --json
python tools\beta_readiness.py --requirements
python tools\beta_readiness.py --audit-evidence --evidence pilot_runs\manual --evidence pilot_runs\output --evidence pilot_runs\transcription --json
python tools\beta_readiness.py --audit-evidence --evidence pilot_runs\manual --evidence pilot_runs\output --evidence pilot_runs\transcription --fail-on-audit-gaps --json
python tools\beta_readiness.py --evidence pilot_runs\manual --evidence pilot_runs\output --evidence pilot_runs\transcription --output BETA_CHECKLIST.md --fail-on-blockers --json
python examples\local_assistant_privacy_demo.py --output-dir pilot_runs\assistant --json
```

`doctor-analysis.json` resume prioridades por bundle. Un problema de captura real en Windows suele aparecer como prioridad alta con categoria `windows_audio:*`; warnings de dependencias opcionales suelen quedar en prioridad baja.

## Plantilla de hallazgos

```text
Fecha:
Sistema operativo:
Python:
AuralisVoiceKit:
Hardware de microfono:
Salida de voz:
Backend de transcripcion:
Comandos ejecutados:
Resultado:
Errores o warnings:
Logs o reportes generados:
Analisis doctor-bundles:
Acciones siguientes:
```

## Estado actual

- Piloto automatizado seguro: preparado con `tools/pilot_run.py`, `pilot-plan.md`, `real-pilot-handoff.md`, `real-pilot-command-pack.md`, `real-pilot-environment-checklist.md`, `real-pilot-fixture-preflight.md`, `real-pilot-transcription-readiness.md`, `real-pilot-system-output-readiness.md`, `real-pilot-evidence-manifest.md`, `real-pilot-decision-gate.md` y `real-pilot-findings-template.md`.
- Piloto manual guiado: preparado con `tools/manual_pilot.py`, `manual-capture-checklist.md` y `capture_checklist`.
- Analisis de bundles doctor: preparado con `auralis doctor-bundles`.
- Pilotos manuales con microfono real: primer piloto Windows/WASAPI aprobado con `--sample-rate 48000`; Ubuntu/Linux y macOS pendientes con `--expected-system`, `--confirm-input-reviewed`, `input_review_confirmed`, `capture_checklist.input_review_confirmed` y `manual-capture-checklist.md`.
- Pilotos manuales con salida `system` real: runner preparado con `tools/output_pilot.py`; dry-run Windows aprobado, tarjeta `real-pilot-system-output-readiness.md`, `output-operator-checklist.md`, `system-output-next-step.md`, `system_guard.expected_system_matched`, `target_output_backend.available`, `target_output_backend.readiness_plan`, `output_backend_ready_required`, `text_review_confirmed`, `spoken_text_privacy_scan.passed`, `operator_checklist.expected_system_matched`, `operator_checklist.records_operator_identity=false`, `operator_checklist.redacts_spoken_text=true`, `operator_checklist.text_review_confirmed`, `operator_checklist.spoken_text_privacy_scan_passed`, `operator_checklist.voice_review_confirmed`, `operator_checklist.commands_available=true`, `operator_checklist.ready_for_real_audio=true`, `operator_checklist.ready_for_beta_evidence`, `next_system_output.uses_placeholders=true` y `next_system_output.records_spoken_text=false` listos, guards `--operator-present`, `--confirm-audible`, `--confirm-text-reviewed`, `--confirm-voice-reviewed`, `--require-output-backend-ready` y `--expected-system` listos, audio real pendiente con operador presente.
- Pilotos manuales con transcripcion real: runner preparado con `tools/transcription_pilot.py`; fixture sintetico publico, tarjeta `real-pilot-fixture-preflight.md` con comandos, artifacts esperados, estado de ffmpeg y condiciones de alto, tarjeta `real-pilot-transcription-readiness.md` con backend objetivo, `target_backend.install_plan`, guard `--require-target-backend-ready`, revisiones de audio/referencia/calidad y condiciones de alto, dry-run sintetico Windows, preflight con `target_backend.available`, `target_backend_ready_required`, dependencias, comando de instalacion del extra opcional, `preflight_decision`, `--require-target-backend-ready`, `transcription-review-checklist.md`, `real-transcription-next-step.md`, scoring redactado, scan redactado `reference_privacy_scan.passed`, requisito beta `target_backend.available=true`, `target_backend_ready_required=true`, `audio.generated_synthetic_audio=false`, `audio.audio_confirmed_non_sensitive=true`, `audio.decoded=true`, redaccion `audio.audio_file_name_redacted`, `audio.duration_gate.enabled=true`, `audio.duration_gate.passed=true`, `transcript.text_redacted=true`, `transcription_checklist.records_audio_file_name=false`, `transcription_checklist.records_expected_text_file_name=false`, `transcription_checklist.redacts_transcript_text=true`, `transcription_checklist.redacts_expected_text=true`, guardas de duracion, `--confirm-audio-reviewed`, `--confirm-reference-reviewed` y `--confirm-quality-reviewed` preparados, audio real pendiente con archivo no sensible.
- Checklist de beta: preparado con `tools/beta_readiness.py`; acepta artifacts JSON con `--evidence`; estado actual `pilot`, beta bloqueada por pilotos reales pendientes.
