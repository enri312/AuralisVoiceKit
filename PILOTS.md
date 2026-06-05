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
- artifact `pilot-plan.md` con comandos pendientes y campos JSON requeridos;
- lista de pasos manuales pendientes.

`pilot-plan.md` esta pensado para compartirse en el equipo sin audio, transcripciones, rutas locales completas ni nombres reales de dispositivos.

## Piloto manual guiado

Este piloto genera bundle doctor, analisis `doctor-bundles`, reporte JSON y Markdown de hallazgos. Por defecto no abre el microfono; `--capture-test` es obligatorio para una prueba real de captura.

```powershell
py tools\manual_pilot.py --output-dir pilot_runs\manual\windows-safe --json
py tools\manual_pilot.py --capture-test --backend wasapi --device default --sample-rate 48000 --json
py tools\output_pilot.py --output-dir pilot_runs\output\system-dry-run --json
py tools\output_pilot.py --speak --operator-present --confirm-audible --text "Hola desde AuralisVoiceKit" --json
py tools\transcription_pilot.py --output-dir pilot_runs\transcription\safe --json
py tools\transcription_pilot.py --output-dir pilot_runs\transcription\quality-safe --expected-text "Hola desde AuralisVoiceKit" --min-word-accuracy 0 --json
py tools\transcription_pilot.py --real-transcription --audio sample.mp3 --audio-non-sensitive --backend whisper --model base --normalize --expected-text "Hola desde AuralisVoiceKit" --min-word-accuracy 0.75 --json
py tools\beta_readiness.py --output BETA_CHECKLIST.md --json
py tools\beta_readiness.py --requirements
py tools\beta_readiness.py --audit-evidence --evidence pilot_runs\manual --evidence pilot_runs\output --evidence pilot_runs\transcription --json
py tools\beta_readiness.py --audit-evidence --evidence pilot_runs\manual --evidence pilot_runs\output --evidence pilot_runs\transcription --fail-on-audit-gaps --json
py tools\beta_readiness.py --evidence pilot_runs\manual --evidence pilot_runs\output --evidence pilot_runs\transcription --output BETA_CHECKLIST.md --json
```

`tools/output_pilot.py` no reproduce audio por defecto. El audio real requiere `--speak --operator-present`; para cerrar el blocker beta tambien debe usarse `--confirm-audible` cuando el operador confirme que escucho la salida. El reporte JSON y el Markdown redactan el texto completo dentro de comandos como `<text-redacted>`.

`tools/transcription_pilot.py` genera audio sintetico y usa `null` por defecto. Los backends reales `whisper` y `openai` requieren `--real-transcription --audio PATH --audio-non-sensitive`, y el texto transcrito no se guarda completo en artifacts. Con `--expected-text` o `--expected-text-file` calcula word accuracy, word error rate y character error rate sin guardar la transcripcion ni la referencia completa.

`tools/beta_readiness.py` no ejecuta hardware ni red. Lee el gate, `PILOT_FINDINGS.md` y artifacts JSON pasados con `--evidence`, genera `BETA_CHECKLIST.md` y marca blockers hasta que haya evidencia real de transcripcion, salida audible y pilotos Ubuntu/Linux y macOS. `--requirements` imprime los campos JSON esperados por cada blocker; `--audit-evidence` revisa artifacts reales, resume blockers cerrados/pendientes y explica que campo falta; `--fail-on-audit-gaps` devuelve codigo 1 si quedan blockers o artifacts ignorados. Las evidencias se toman de `manual-pilot-report.json`, `output-pilot-report.json` y `transcription-pilot-report.json`; solo cuentan si declaran `project: AuralisVoiceKit`. El checklist reporta evidencias ignoradas con motivos seguros (`missing_project`, `wrong_project`, `not_json_object`) y no copia transcripciones ni rutas completas. English: strict evidence audit can fail CI without exposing private audio, transcripts or full local paths.

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
python tools\manual_pilot.py --capture-test --backend wasapi --device default --sample-rate 48000 --json
python tools\output_pilot.py --speak --operator-present --confirm-audible --text "Hola desde AuralisVoiceKit" --json
python tools\transcription_pilot.py --real-transcription --audio sample.mp3 --audio-non-sensitive --backend whisper --model base --normalize --expected-text "Hola desde AuralisVoiceKit" --min-word-accuracy 0.75 --json
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

- Piloto automatizado seguro: preparado con `tools/pilot_run.py`.
- Piloto manual guiado: preparado con `tools/manual_pilot.py`.
- Analisis de bundles doctor: preparado con `auralis doctor-bundles`.
- Pilotos manuales con microfono real: primer piloto Windows/WASAPI aprobado con `--sample-rate 48000`; Ubuntu/Linux y macOS pendientes.
- Pilotos manuales con salida `system` real: runner preparado con `tools/output_pilot.py`; dry-run Windows aprobado, guards `--operator-present` y `--confirm-audible` listos, audio real pendiente con operador presente.
- Pilotos manuales con transcripcion real: runner preparado con `tools/transcription_pilot.py`; dry-run sintetico Windows aprobado, scoring redactado preparado y audio real pendiente con archivo no sensible.
- Checklist de beta: preparado con `tools/beta_readiness.py`; acepta artifacts JSON con `--evidence`; estado actual `pilot`, beta bloqueada por pilotos reales pendientes.
