# Hallazgos de pilotos

Este documento resume hallazgos de pilotos reales o semi-manuales. No debe incluir audio, transcripciones privadas, rutas locales completas ni nombres reales de dispositivos.

## 2026-06-06 - Windows fixture MP3 sintetico con tarjeta de preflight

Comando ejecutado:

```powershell
python tools\pilot_audio_fixture.py --output-dir pilot_runs\transcription\fixture --format wav --format mp3 --duration 1.0 --sample-rate 16000 --run-preflight --min-audio-seconds 0.2 --max-audio-seconds 60 --json
```

Alcance:

- Sistema: Windows.
- Audio usado: sintetico publico generado por el runner.
- Audio privado: no.
- Red/modelos reales: no.
- Artifact de preparacion: `real-pilot-fixture-preflight.md` en el piloto seguro.

Resultado:

- Fixture WAV/MP3: `passed=true`.
- Preflight: `passed=true`.
- Audio decoded: `true`.
- Duration gate passed: `true`.
- Generated public fixture: `true`.
- Usable as beta evidence: `false`.

Acciones siguientes:

1. Revisar `real-pilot-fixture-preflight.md` antes de reemplazar `pilot-sample.mp3`.
2. Ejecutar `python tools\transcription_pilot.py --preflight-only --audio sample.mp3 --audio-non-sensitive --backend whisper --normalize --min-audio-seconds 0.2 --max-audio-seconds 60 --json` con MP3 propio no sensible.
3. Mantener la beta bloqueada hasta tener transcripcion real revisada con `--confirm-audio-reviewed`, `--confirm-reference-reviewed`, `reference_privacy_scan.passed=true` y `--confirm-quality-reviewed`.

## 2026-06-05 - Windows fixture MP3 sintetico con checklist de transcripcion

Comando ejecutado:

```powershell
python tools\pilot_audio_fixture.py --output-dir pilot_runs\transcription\20260605T1908Z-review-checklist --format mp3 --duration 0.5 --sample-rate 8000 --run-preflight --min-audio-seconds 0.2 --max-audio-seconds 1.0 --json
```

Alcance:

- Sistema: Windows.
- Audio usado: sintetico publico generado por el runner.
- Audio privado: no.
- Red/modelos reales: no.
- Backend de preflight: `whisper` como destino declarado, sin ejecutar modelo por `--preflight-only`.
- Artifact nuevo: `transcription-review-checklist.md`.

Resultado:

- Fixture MP3: `passed=true`.
- Preflight: `passed=true`.
- Audio decoded: `true`.
- Duration gate passed: `true`.
- `fixture_preflight_checklist`: generado.
- `transcription_checklist.ready_for_beta_evidence`: `false`, esperado porque no hubo backend real ni audio propio no sensible.
- Usable as beta evidence: `false`.

Acciones siguientes:

1. Reemplazar `pilot-sample.mp3` por un MP3 propio no sensible.
2. Ejecutar `python tools\transcription_pilot.py --preflight-only --audio sample.mp3 --audio-non-sensitive --backend whisper --normalize --min-audio-seconds 0.2 --max-audio-seconds 60 --json`.
3. Ejecutar transcripcion real solo despues de revisar `transcription-review-checklist.md` y preparar `--expected-text` o `--expected-text-file`.

## 2026-06-05 - Windows salida system dry-run con checklist de operador

Comando ejecutado:

```powershell
python tools\output_pilot.py --output-dir pilot_runs\output\20260605T1850Z-system-checklist --json
```

Alcance:

- Sistema: Windows.
- Backend diagnosticado: `system`.
- Audio reproducido: no.
- Modo: dry-run.
- Artifact nuevo: `output-operator-checklist.md`.
- Identidad del operador guardada: no.
- Texto completo guardado: no; comandos sanitizados con `<text-redacted>`.

Resultado:

- Piloto de salida: `passed=true`.
- `operator_confirmation_status`: `not-required`.
- `operator_checklist.records_operator_identity`: `false`.
- `operator_checklist.redacts_spoken_text`: `true`.
- Operator checklist ready for beta evidence: False.
- Comandos observados: 2.
- Voces reportadas por dry-run: 2.

Acciones siguientes:

1. Ejecutar `python tools\output_pilot.py --speak --operator-present --confirm-audible --output-dir pilot_runs\output\system-real --text "Hola desde AuralisVoiceKit" --json` solo con operador presente.
2. Verificar que `operator_checklist.ready_for_beta_evidence=true` antes de usar el JSON como evidencia beta.
3. Registrar solo voz, volumen, audibilidad y fallos tecnicos; no guardar texto privado ni nombres del operador.

## 2026-06-05 - Windows transcripcion dry-run con scoring redactado

Comando ejecutado:

```powershell
python tools\transcription_pilot.py --output-dir pilot_runs\transcription\20260605T1532Z-quality-safe --expected-text "Hola desde AuralisVoiceKit" --min-word-accuracy 0 --duration 0.3 --sample-rate 8000 --json
```

Alcance:

- Sistema: Windows.
- Backend diagnosticado: `null`.
- Audio usado: sintetico generado por el runner.
- Red/modelos reales: no.
- Texto esperado completo guardado: no.
- Texto transcrito completo guardado: no.

Resultado:

- Piloto de transcripcion: `passed=true`.
- Quality reference provided: `true`.
- Word accuracy: `0.0`.
- Word error rate: `1.0`.
- Quality gate passed: `true` con umbral `0`.
- Resultado esperado: backend `null` no transcribe, asi que la metrica queda lista sin simular calidad real.

Acciones siguientes:

1. Ejecutar `python tools\transcription_pilot.py --real-transcription --audio sample.mp3 --audio-non-sensitive --backend whisper --model base --normalize --expected-text "Hola desde AuralisVoiceKit" --min-word-accuracy 0.75 --json` con audio propio no sensible.
2. Si se usa un texto esperado desde archivo, pasar `--expected-text-file reference.txt` y no subir ese archivo si contiene contenido privado.
3. Registrar solo metricas agregadas y hallazgos tecnicos; no pegar transcripciones completas.

## 2026-06-05 - Windows transcripcion dry-run sintetica

Comando ejecutado:

```powershell
python tools\transcription_pilot.py --output-dir pilot_runs\transcription\20260605T1521Z-safe --duration 0.3 --sample-rate 8000 --json
```

Alcance:

- Sistema: Windows.
- Backend diagnosticado: `null`.
- Audio usado: sintetico generado por el runner.
- Red/modelos reales: no.
- Texto completo guardado: no.

Resultado:

- Piloto de transcripcion: `passed=true`.
- Duracion de audio: 0.3 segundos.
- Sample rate: 8000 Hz.
- Transcript characters: 0.
- Texto transcrito redactado en artifacts.

Acciones siguientes:

1. Ejecutar `python tools\transcription_pilot.py --real-transcription --audio sample.mp3 --audio-non-sensitive --backend whisper --model base --normalize --json` con audio propio no sensible.
2. Si se usa OpenAI, confirmar credenciales y evitar audio privado.
3. Registrar solo calidad general, backend/modelo y hallazgos tecnicos; no pegar transcripciones completas.

## 2026-06-05 - Windows salida system dry-run con guard de operador

Comando ejecutado:

```powershell
python tools\output_pilot.py --output-dir pilot_runs\output\20260605T1512Z-system-dry-run-guard --json
```

Alcance:

- Sistema: Windows.
- Backend diagnosticado: `system`.
- Audio reproducido: no.
- Modo: dry-run.
- Guard de seguridad: audio real requiere `--speak --operator-present`.

Resultado:

- Piloto de salida: `passed=true`.
- `operator_confirmation_status`: `not-required`.
- Comandos observados: 2.
- Texto completo redactado como `<text-redacted>`.

Acciones siguientes:

1. Ejecutar audio real solo con `python tools\output_pilot.py --speak --operator-present --text "Hola desde AuralisVoiceKit" --json`.
2. Agregar `--confirm-audible` si el operador confirma que la salida fue audible.
3. Registrar voz, volumen y cualquier fallo de comando por plataforma.

## 2026-06-05 - Windows salida system dry-run

Comando ejecutado:

```powershell
python tools\output_pilot.py --output-dir pilot_runs\output\20260605T1500Z-system-dry-run --json
```

Alcance:

- Sistema: Windows.
- Backend diagnosticado: `system`.
- Audio reproducido: no.
- Modo: dry-run.
- Texto completo guardado: no; comandos sanitizados con `<text-redacted>`.

Resultado:

- Piloto de salida: `passed=true`.
- Eventos observados: `output.started`, `output.completed`.
- Voces reportadas por dry-run: 2.
- Comandos observados: 2.
- Sin errores de salida ni listado de voces.

Acciones siguientes:

1. Ejecutar `python tools\output_pilot.py --speak --operator-present --text "Hola desde AuralisVoiceKit" --json` solo con operador presente.
2. Confirmar audibilidad, voz seleccionada y volumen.
3. Repetir salida `system` en Ubuntu/Linux y macOS.

## 2026-06-05 - Windows WASAPI captura real a 48000 Hz

Comando ejecutado:

```powershell
python tools\manual_pilot.py --output-dir pilot_runs\manual\20260605T1448Z-windows-wasapi-48000 --backend wasapi --device 15 --sample-rate 48000 --capture-test --capture-seconds 0.25 --json
```

Alcance:

- Sistema: Windows.
- Backend diagnosticado: `wasapi`.
- Microfono abierto: si, durante 0.25 segundos.
- Sample rate: 48000 Hz.
- Audio guardado: no.
- Red/modelos: no.

Resultado:

- Estado doctor: `warning`.
- Piloto manual: `passed=true`.
- Check `capture-test:wasapi`: `ok`.
- Prioridad mas alta: `low`.
- Sin problemas `high`.
- Warnings esperados: extras `openai` y `faster_whisper` no instalados.

Acciones siguientes:

1. Ejecutar piloto de salida `system` con voz real y operador presente.
2. Ejecutar piloto de transcripcion real con audio propio no sensible.
3. Repetir captura en Ubuntu/Linux y macOS cuando haya hardware disponible.

## 2026-06-05 - Windows WASAPI captura real inicial

Comando ejecutado:

```powershell
python tools\manual_pilot.py --output-dir pilot_runs\manual\20260605T1448Z-windows-wasapi-capture --backend wasapi --device 15 --capture-test --capture-seconds 0.25 --json
```

Alcance:

- Sistema: Windows.
- Backend diagnosticado: `wasapi`.
- Microfono abierto: si, durante 0.25 segundos.
- Audio guardado: no.
- Red/modelos: no.
- Extra `sounddevice`: instalado y disponible.
- Dispositivos WASAPI de entrada detectados: 2.

Resultado:

- Estado doctor: `error`.
- Prioridad mas alta: `high`.
- Categoria: `windows_audio:sample_rate`.
- Error: `Invalid sample rate [PaErrorCode -9997]`.
- El dispositivo probado reporto frecuencia default de 48000 Hz en el snapshot WASAPI.

Acciones siguientes:

1. Completado: soporte `--sample-rate` publicado en `auralis doctor` y `tools/manual_pilot.py`.
2. Completado: reintento con `--sample-rate 48000` paso correctamente.
3. Mantener 44100 como alternativa si otro dispositivo rechaza 48000.

## 2026-06-05 - Windows manual seguro sin captura

Comando ejecutado:

```powershell
python tools\manual_pilot.py --output-dir pilot_runs\manual\20260605T1437Z-windows-safe --json
```

Alcance:

- Sistema: Windows.
- Backend diagnosticado: `wasapi`.
- Microfono abierto: no.
- Red/modelos: no.
- Artifact local generado: bundle doctor, analisis doctor-bundles, reporte JSON y Markdown de hallazgos.

Resultado:

- Estado doctor: `warning`.
- Prioridad mas alta: `low`.
- Sin problemas `high`.
- `ffmpeg` disponible.
- Bloqueo para el siguiente piloto con microfono: falta el extra opcional `sounddevice`.
- Warnings esperados de extras no instalados: `sounddevice`, `openai`, `faster_whisper`.

Acciones siguientes:

1. Instalar `auralisvoicekit[sounddevice]` o el extra local equivalente.
2. Ejecutar `python tools\manual_pilot.py --capture-test --backend wasapi --device default --sample-rate 48000 --json`.
3. Revisar el nuevo `doctor-analysis.json` con foco en categorias `windows_audio:*`.
4. Actualizar este documento con el resultado del piloto de captura real.
