# Pilotos de AuralisVoiceKit

Este documento define como ejecutar pilotos seguros antes de acercarse a beta o `1.0.0`.

## Piloto automatizado seguro

Este piloto no abre microfono, no reproduce audio real, no usa red y no descarga modelos. Sirve para validar que el paquete esta listo para una prueba manual controlada.

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
- resumen `beta_readiness` y pasos `next_beta_evidence_steps` para cerrar blockers beta;
- campo `recommended_pilot_sequence` con el orden recomendado para pilotos reales, checklist de captura, checklist de operador para salida audible, fixture sintetico, preflight MP3 de transcripcion, checklist de revision de transcripcion, auditoria estricta y refresco del checklist beta;
- campo `platform_pilot_matrix` y seccion `Matriz por plataforma` para separar comandos Windows, Ubuntu/Linux, macOS, salida audible y transcripcion MP3;
- artifacts `pilot-plan.md`, `real-pilot-handoff.md` y `real-pilot-findings-template.md` con evidencias JSON aceptadas/ignoradas, secuencia recomendada, comandos pendientes, campos JSON requeridos, una tarjeta de traspaso segura para el operador y una plantilla sanitizada para `PILOT_FINDINGS.md`;
- lista de pasos manuales pendientes.

`pilot-plan.md`, `real-pilot-handoff.md` y `real-pilot-findings-template.md` estan pensados para compartirse en el equipo sin audio, transcripciones, texto hablado real, rutas locales completas, nombres reales de dispositivos ni identidad del operador.

## Piloto manual guiado

Este piloto genera bundle doctor, analisis `doctor-bundles`, reporte JSON, Markdown de hallazgos y `manual-capture-checklist.md`. Por defecto no abre el microfono; `--capture-test` es obligatorio para una prueba real de captura. Usa `--expected-system Windows`, `--expected-system Linux` o `--expected-system Darwin` para confirmar que el artifact se genero en la plataforma esperada, y `--confirm-input-reviewed` solo despues de revisar permisos del microfono, dispositivo de entrada y un entorno no sensible. En Ubuntu/Linux y macOS la evidencia beta acepta `--backend sounddevice` o `--backend pyaudio`; Windows mantiene `--backend wasapi`. El reporte no guarda bytes de audio y redacta el selector de dispositivo cuando no es `default` o un id numerico. English: beta capture evidence requires `system_guard.expected_system_matched=true`, `capture_backend=sounddevice|pyaudio` on Ubuntu/Linux and macOS, `input_review_confirmed=true`, `capture_checklist.input_review_confirmed=true` and `capture_checklist.ready_for_beta_evidence=true`.

```powershell
py tools\manual_pilot.py --output-dir pilot_runs\manual\windows-safe --json
py tools\manual_pilot.py --capture-test --backend wasapi --device default --sample-rate 48000 --expected-system Windows --confirm-input-reviewed --json
py tools\manual_pilot.py --capture-test --backend sounddevice --device default --expected-system Linux --confirm-input-reviewed --json
py tools\manual_pilot.py --capture-test --backend pyaudio --device default --expected-system Linux --confirm-input-reviewed --json
py tools\manual_pilot.py --capture-test --backend sounddevice --device default --expected-system Darwin --confirm-input-reviewed --json
py tools\manual_pilot.py --capture-test --backend pyaudio --device default --expected-system Darwin --confirm-input-reviewed --json
py tools\output_pilot.py --output-dir pilot_runs\output\system-dry-run --json
py tools\output_pilot.py --speak --operator-present --confirm-audible --confirm-text-reviewed --confirm-voice-reviewed --require-output-backend-ready --expected-system "Windows|Linux|Darwin" --output-dir pilot_runs\output\system-real --text "Hola desde AuralisVoiceKit" --json
py tools\transcription_pilot.py --output-dir pilot_runs\transcription\safe --json
py tools\transcription_pilot.py --output-dir pilot_runs\transcription\quality-safe --expected-text "Hola desde AuralisVoiceKit" --min-word-accuracy 0 --json
py tools\pilot_audio_fixture.py --output-dir pilot_runs\transcription\fixture --format wav --format mp3 --run-preflight --json
py tools\transcription_pilot.py --preflight-only --audio sample.mp3 --audio-non-sensitive --backend whisper --normalize --min-audio-seconds 0.2 --max-audio-seconds 60 --json
py tools\transcription_pilot.py --real-transcription --audio sample.mp3 --audio-non-sensitive --confirm-audio-reviewed --confirm-reference-reviewed --backend whisper --model base --normalize --expected-text "Hola desde AuralisVoiceKit" --min-word-accuracy 0.75 --min-audio-seconds 0.2 --max-audio-seconds 60 --confirm-quality-reviewed --require-target-backend-ready --json
py tools\beta_readiness.py --output BETA_CHECKLIST.md --json
py tools\beta_readiness.py --requirements
py tools\beta_readiness.py --audit-evidence --evidence pilot_runs\manual --evidence pilot_runs\output --evidence pilot_runs\transcription --json
py tools\beta_readiness.py --audit-evidence --evidence pilot_runs\manual --evidence pilot_runs\output --evidence pilot_runs\transcription --fail-on-audit-gaps --json
py tools\beta_readiness.py --evidence pilot_runs\manual --evidence pilot_runs\output --evidence pilot_runs\transcription --output BETA_CHECKLIST.md --json
```

`tools/output_pilot.py` no reproduce audio por defecto. El dry-run genera `output-operator-checklist.md`, `system-output-next-step.md`, `system_guard`, `target_output_backend`, `spoken_text_privacy_scan` y el bloque JSON `operator_checklist` para preparar el piloto audible sin registrar identidad del operador ni texto privado. La tarjeta de siguiente paso usa `<public-spoken-text>` como placeholder para no copiar texto hablado real en artifacts compartidos. El audio real requiere `--speak --operator-present`; para cerrar el blocker beta tambien debe usarse `--confirm-audible` cuando el operador confirme que escucho la salida, `--confirm-text-reviewed` despues de revisar que el texto hablado sea publico/no sensible, `--confirm-voice-reviewed` despues de revisar voz, volumen y pronunciacion, `--require-output-backend-ready` para fallar temprano si falta el comando de voz, y `--expected-system "Windows|Linux|Darwin"` para confirmar que la prueba se hizo en una plataforma soportada. La evidencia JSON debe incluir `system_guard.expected_system_matched=true`, `target_output_backend.available=true`, `text_review_confirmed=true`, `spoken_text_privacy_scan.passed=true`, `voice_review_confirmed=true`, `operator_checklist.expected_system_matched=true`, `operator_checklist.text_review_confirmed=true`, `operator_checklist.spoken_text_privacy_scan_passed=true`, `operator_checklist.voice_review_confirmed=true` y `operator_checklist.ready_for_beta_evidence=true`. `--system` es solo para dry-runs y no se acepta con `--speak`. El reporte JSON y el Markdown redactan el texto completo dentro de comandos como `<text-redacted>`; el scan de texto hablado solo guarda estado, conteo y tipos de riesgo.

`tools/pilot_audio_fixture.py` genera audio sintetico publico en WAV/MP3/FLAC para ensayar ffmpeg; con `--run-preflight` tambien ejecuta un preflight seguro contra el MP3 generado. Marca `usable_as_beta_evidence=false` para no confundirlo con evidencia real. `tools/transcription_pilot.py` genera audio sintetico y usa `null` por defecto. `--preflight-only --audio PATH --audio-non-sensitive` decodifica MP3/FLAC/WAV, valida que el backend objetivo este registrado, reporta `target_backend.available`, dependencias y razon de instalacion, y escribe metadata sanitizada sin ejecutar Whisper/OpenAI; sirve para detectar problemas de ffmpeg, extras faltantes o nombres de backend antes del piloto real. `--require-target-backend-ready` vuelve obligatoria esa disponibilidad y falla con un error sanitizado si falta el extra del backend. Cada corrida escribe `transcription-review-checklist.md`, `real-transcription-next-step.md` y `transcription_checklist` para revisar privacidad, duracion, referencia y calidad sin copiar audio ni texto privado; la tarjeta de siguiente paso usa placeholders como `<audio-path>` y `<expected-text-path>`. `--min-audio-seconds` y `--max-audio-seconds` agregan una guarda publica de duracion para rechazar audios vacios o demasiado largos antes de continuar. Los backends reales `whisper` y `openai` requieren `--real-transcription --audio PATH --audio-non-sensitive`; la evidencia beta exige `audio.audio_file_name_redacted=true`, `--confirm-audio-reviewed` despues de revisar privacidad del audio, `--confirm-reference-reviewed` despues de revisar privacidad del texto esperado, `reference_privacy_scan.passed=true` sin riesgos de email/URL/secretos/numeros largos y `--confirm-quality-reviewed` despues de una revision humana local de calidad. El texto transcrito, el nombre del audio y el nombre del archivo de referencia no se guardan completos en artifacts; el scan de referencia solo guarda estado, conteo y tipos de riesgo. Con `--expected-text` o `--expected-text-file` calcula word accuracy, word error rate y character error rate sin guardar la transcripcion ni la referencia completa.

`tools/beta_readiness.py` no ejecuta hardware ni red. Lee el gate, `PILOT_FINDINGS.md` y artifacts JSON pasados con `--evidence`, genera `BETA_CHECKLIST.md` y marca blockers hasta que haya evidencia real de transcripcion, salida audible y pilotos Ubuntu/Linux y macOS. `--requirements` imprime los campos JSON esperados por cada blocker, incluidos `system_guard.expected_system_matched`, `capture_backend=sounddevice|pyaudio` en Ubuntu/Linux y macOS, `input_review_confirmed`, `capture_checklist.input_review_confirmed` y `capture_checklist.ready_for_beta_evidence` para captura real, `audio.audio_file_name_redacted`, `audio_review_confirmed`, `reference_review_confirmed`, `reference_privacy_scan.passed`, `quality_review_confirmed`, `transcription_checklist.audio_review_confirmed`, `transcription_checklist.records_audio_file_name`, `transcription_checklist.records_expected_text_file_name`, `transcription_checklist.reference_review_confirmed`, `transcription_checklist.reference_privacy_scan_passed`, `transcription_checklist.quality_review_confirmed` y `transcription_checklist.ready_for_beta_evidence` para transcripcion real, y `system_guard.expected_system_matched`, `text_review_confirmed`, `spoken_text_privacy_scan.passed`, `voice_review_confirmed`, `operator_checklist.expected_system_matched`, `operator_checklist.text_review_confirmed`, `operator_checklist.spoken_text_privacy_scan_passed`, `operator_checklist.voice_review_confirmed` y `operator_checklist.ready_for_beta_evidence` para salida audible; `--audit-evidence` revisa artifacts reales, resume blockers cerrados/pendientes y explica que campo falta; `--fail-on-audit-gaps` devuelve codigo 1 si quedan blockers o artifacts ignorados. Las evidencias se toman de `manual-pilot-report.json`, `output-pilot-report.json` y `transcription-pilot-report.json`; solo cuentan si declaran `project: AuralisVoiceKit`. El checklist reporta evidencias ignoradas con motivos seguros (`missing_project`, `wrong_project`, `not_json_object`) y no copia transcripciones, nombres de archivos privados ni rutas completas. English: strict evidence audit requires human-reviewed capture input with sounddevice or pyaudio on Ubuntu/Linux and macOS, passing reference privacy scan, reviewed spoken output text and output quality without exposing private audio, transcripts, file names, spoken text or full local paths.

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
python tools\manual_pilot.py --capture-test --backend wasapi --device default --sample-rate 48000 --expected-system Windows --confirm-input-reviewed --json
python tools\manual_pilot.py --capture-test --backend sounddevice --device default --expected-system Linux --confirm-input-reviewed --json
python tools\manual_pilot.py --capture-test --backend pyaudio --device default --expected-system Linux --confirm-input-reviewed --json
python tools\manual_pilot.py --capture-test --backend sounddevice --device default --expected-system Darwin --confirm-input-reviewed --json
python tools\manual_pilot.py --capture-test --backend pyaudio --device default --expected-system Darwin --confirm-input-reviewed --json
python tools\output_pilot.py --output-dir pilot_runs\output\system-dry-run --json
python tools\output_pilot.py --speak --operator-present --confirm-audible --confirm-text-reviewed --confirm-voice-reviewed --require-output-backend-ready --expected-system "Windows|Linux|Darwin" --output-dir pilot_runs\output\system-real --text "Hola desde AuralisVoiceKit" --json
python tools\pilot_audio_fixture.py --output-dir pilot_runs\transcription\fixture --format wav --format mp3 --run-preflight --json
python tools\transcription_pilot.py --preflight-only --audio sample.mp3 --audio-non-sensitive --backend whisper --normalize --min-audio-seconds 0.2 --max-audio-seconds 60 --json
python tools\transcription_pilot.py --real-transcription --audio sample.mp3 --audio-non-sensitive --confirm-audio-reviewed --confirm-reference-reviewed --backend whisper --model base --normalize --expected-text "Hola desde AuralisVoiceKit" --min-word-accuracy 0.75 --min-audio-seconds 0.2 --max-audio-seconds 60 --confirm-quality-reviewed --require-target-backend-ready --json
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

- Piloto automatizado seguro: preparado con `tools/pilot_run.py`, `pilot-plan.md`, `real-pilot-handoff.md` y `real-pilot-findings-template.md`.
- Piloto manual guiado: preparado con `tools/manual_pilot.py`, `manual-capture-checklist.md` y `capture_checklist`.
- Analisis de bundles doctor: preparado con `auralis doctor-bundles`.
- Pilotos manuales con microfono real: primer piloto Windows/WASAPI aprobado con `--sample-rate 48000`; Ubuntu/Linux y macOS pendientes con `--expected-system`, `--confirm-input-reviewed`, `input_review_confirmed`, `capture_checklist.input_review_confirmed` y `manual-capture-checklist.md`.
- Pilotos manuales con salida `system` real: runner preparado con `tools/output_pilot.py`; dry-run Windows aprobado, `output-operator-checklist.md`, `system-output-next-step.md`, `system_guard.expected_system_matched`, `target_output_backend.available`, `text_review_confirmed`, `spoken_text_privacy_scan.passed`, `operator_checklist.expected_system_matched`, `operator_checklist.text_review_confirmed`, `operator_checklist.spoken_text_privacy_scan_passed`, `operator_checklist.voice_review_confirmed` y `operator_checklist.ready_for_beta_evidence` listos, guards `--operator-present`, `--confirm-audible`, `--confirm-text-reviewed`, `--confirm-voice-reviewed`, `--require-output-backend-ready` y `--expected-system` listos, audio real pendiente con operador presente.
- Pilotos manuales con transcripcion real: runner preparado con `tools/transcription_pilot.py`; fixture sintetico publico, dry-run sintetico Windows, preflight con `target_backend.available`, dependencias y `--require-target-backend-ready`, `transcription-review-checklist.md`, `real-transcription-next-step.md`, scoring redactado, scan redactado `reference_privacy_scan.passed`, redaccion `audio.audio_file_name_redacted`, `transcription_checklist.records_audio_file_name=false`, `transcription_checklist.records_expected_text_file_name=false`, guardas de duracion, `--confirm-audio-reviewed`, `--confirm-reference-reviewed` y `--confirm-quality-reviewed` preparados, audio real pendiente con archivo no sensible.
- Checklist de beta: preparado con `tools/beta_readiness.py`; acepta artifacts JSON con `--evidence`; estado actual `pilot`, beta bloqueada por pilotos reales pendientes.
