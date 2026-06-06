# Hallazgos de pilotos

Este documento resume hallazgos de pilotos reales o semi-manuales. No debe incluir audio, transcripciones privadas, rutas locales completas ni nombres reales de dispositivos.

## 2026-06-06 - Auditoria beta exige salida audible redactada

Comando ejecutado:

```powershell
python tools\beta_readiness.py --requirements
```

Alcance:

- Sistema anfitrion: Windows.
- Version AuralisVoiceKit: `0.99.2`.
- Audio real reproducido: no.
- Texto hablado real usado: no.
- Tipo de piloto: auditoria de contrato beta.

Resultado:

- El contrato de salida audible ahora exige `operator_checklist.redacts_spoken_text=true`.
- El contrato tambien exige `operator_checklist.records_operator_identity=false`.
- La evidencia debe probar `operator_checklist.commands_available=true` y `operator_checklist.ready_for_real_audio=true`.
- `next_system_output` debe usar placeholders y declarar `records_spoken_text=false`.
- Evidencia beta: `false`; este hallazgo valida el contrato, no reemplaza el piloto audible con operador presente.

Acciones siguientes:

1. Ejecutar el dry-run de `tools/output_pilot.py` y revisar `output-operator-checklist.md`.
2. Ejecutar salida `system` real solo con operador presente y texto publico/no sensible.
3. Conservar solo artifacts sanitizados con texto hablado y operador redactados.

## 2026-06-06 - Auditoria beta exige audio real decodificado y transcript redactado

Comando ejecutado:

```powershell
python tools\beta_readiness.py --requirements
```

Alcance:

- Sistema anfitrion: Windows.
- Version AuralisVoiceKit: `0.99.1`.
- Audio real usado: no.
- Transcripcion real ejecutada: no.
- Tipo de piloto: auditoria de contrato beta.

Resultado:

- El contrato de evidencias beta ahora exige `audio.generated_synthetic_audio=false`.
- El contrato de evidencias beta ahora exige `audio.audio_confirmed_non_sensitive=true` y `audio.decoded=true`.
- El contrato de evidencias beta ahora exige `transcript.text_redacted=true`.
- El checklist de transcripcion ahora exige `transcription_checklist.redacts_transcript_text=true` y `transcription_checklist.redacts_expected_text=true`.
- Evidencia beta: `false`; este hallazgo valida el contrato, no reemplaza el piloto real con audio propio no sensible.

Acciones siguientes:

1. Ejecutar el preflight MP3 con audio propio no sensible y revisar que `audio.decoded=true`.
2. Ejecutar transcripcion real solo si el audio no es sintetico, paso la guarda de duracion y fue revisado como no sensible.
3. Conservar solo artifacts sanitizados con transcript y referencia redactados.

## 2026-06-06 - Fixture sintetico MP3 con preflight de duracion

Comando ejecutado:

```powershell
python tools\pilot_audio_fixture.py --output-dir pilot_runs\transcription\fixture-v0.99 --format wav --format mp3 --duration 1.0 --sample-rate 16000 --run-preflight --min-audio-seconds 0.2 --max-audio-seconds 60 --json
```

Alcance:

- Sistema anfitrion: Windows.
- Version AuralisVoiceKit: `0.99.0`.
- Audio real usado: no.
- Audio sintetico publico generado: si.
- Transcripcion real ejecutada: no.

Resultado:

- Fixture WAV: `passed=true`, duracion `1.0s`.
- Fixture MP3: `passed=true`, duracion `1.0s`.
- `ffmpeg.available`: `true`.
- Preflight MP3: `passed=true`.
- `preflight.duration_gate_passed`: `true`.
- Evidencia beta: `false`; el fixture y el preflight sintetico solo preparan el siguiente piloto con audio propio no sensible.

Acciones siguientes:

1. Reemplazar el MP3 sintetico por un MP3 propio no sensible.
2. Ejecutar `tools/transcription_pilot.py --preflight-only --audio <audio-path> --audio-non-sensitive --backend whisper --normalize --min-audio-seconds 0.2 --max-audio-seconds 60 --json`.
3. Ejecutar transcripcion real solo si el preflight mantiene `audio.duration_gate.enabled=true`, `audio.duration_gate.passed=true` y el backend objetivo esta disponible.

## 2026-06-06 - Auditoria beta exige guardas de duracion para transcripcion real

Comando ejecutado:

```powershell
python tools\beta_readiness.py --requirements
```

Alcance:

- Sistema anfitrion: Windows.
- Version AuralisVoiceKit: `0.99.0`.
- Audio real usado: no.
- Transcripcion real ejecutada: no.
- Tipo de piloto: auditoria de contrato beta.

Resultado:

- El contrato de evidencias beta ahora exige `audio.duration_gate.enabled=true`.
- El contrato de evidencias beta ahora exige `audio.duration_gate.passed=true`.
- El blocker `real_transcription_quality` ya no se cierra con JSON que omita `--min-audio-seconds` y `--max-audio-seconds`.
- Evidencia beta: `false`; este hallazgo valida el contrato, no reemplaza el piloto real con audio propio no sensible.

Acciones siguientes:

1. Ejecutar `tools/pilot_audio_fixture.py --run-preflight --min-audio-seconds 0.2 --max-audio-seconds 60 --json` para revisar ffmpeg sin audio privado.
2. Ejecutar `tools/transcription_pilot.py --real-transcription --audio <audio-path> --audio-non-sensitive --confirm-audio-reviewed --confirm-reference-reviewed --min-audio-seconds 0.2 --max-audio-seconds 60 --confirm-quality-reviewed --require-target-backend-ready --json` solo con audio propio no sensible.
3. Conservar un `transcription-pilot-report.json` sanitizado con `audio.duration_gate.enabled=true` y `audio.duration_gate.passed=true`.

## 2026-06-06 - Auditoria beta exige backend de captura real para Linux/macOS

Comando ejecutado:

```powershell
python tools\beta_readiness.py --requirements
```

Alcance:

- Sistema anfitrion: Windows.
- Version AuralisVoiceKit: `0.98.0`.
- Microfono abierto: no.
- Audio real guardado: no.
- Tipo de piloto: auditoria de contrato beta, sin captura real.

Resultado:

- El contrato de evidencias beta ahora exige `target_capture_backend.available=true`.
- El contrato de evidencias beta ahora exige `capture_backend_ready_required=true`.
- Los blockers `ubuntu_linux_capture` y `macos_capture` ya no se cierran con JSON que omita el guard estricto de backend.
- Evidencia beta: `false`; este hallazgo valida el contrato, no reemplaza pilotos reales en Ubuntu/Linux ni macOS.

Acciones siguientes:

1. Ejecutar `tools/manual_pilot.py --capture-test --backend sounddevice --device default --expected-system Linux --confirm-input-reviewed --require-capture-backend-ready --json` en Ubuntu/Linux real.
2. Ejecutar el mismo flujo en macOS con `--expected-system Darwin`.
3. Guardar solo JSON/checklists sanitizados que incluyan `target_capture_backend.available=true` y `capture_backend_ready_required=true`.

## 2026-06-06 - Windows dry-run de guard estricto para captura Ubuntu/Linux

Comando ejecutado:

```powershell
python tools\manual_pilot.py --output-dir pilot_runs\manual\capture-backend-ready-linux --target-system Linux --require-capture-backend-ready --json
```

Alcance:

- Sistema anfitrion: Windows.
- Sistema objetivo para instrucciones: Ubuntu/Linux.
- Version AuralisVoiceKit: `0.97.0`.
- Microfono abierto: no.
- Audio real guardado: no.
- Guard estricto: `--require-capture-backend-ready`.

Resultado:

- Dry-run: `passed=true`.
- `capture_backend`: `sounddevice`, elegido por defecto al usar `--target-system Linux`.
- `target_capture_backend.available`: `true`.
- `capture_backend_ready_required`: `true`.
- `capture_readiness_plan.post_install_check`: incluye `--require-capture-backend-ready` y no abre microfono.
- `capture_readiness_plan.real_capture_check_template`: conserva `--capture-test`, `--expected-system Linux`, `--confirm-input-reviewed` y `--require-capture-backend-ready`.
- Evidencia beta: `false`; falta Ubuntu/Linux real, microfono real, revision de entrada y `capture_checklist.ready_for_beta_evidence=true`.

Acciones siguientes:

1. Ejecutar este mismo guard en Ubuntu/Linux real despues de instalar `auralisvoicekit[sounddevice]` y PortAudio.
2. Abrir el microfono solo despues de que `target_capture_backend.available=true` y de revisar permisos/dispositivo/entorno.
3. Repetir el mismo flujo con `--target-system Darwin` y `--backend sounddevice` o `--backend pyaudio` en macOS.

## 2026-06-06 - Windows dry-run de readiness para captura Ubuntu/Linux

Comando ejecutado:

```powershell
python tools\manual_pilot.py --output-dir pilot_runs\manual\capture-readiness-linux --backend sounddevice --target-system Linux --json
```

Alcance:

- Sistema anfitrion: Windows.
- Sistema objetivo para instrucciones: Ubuntu/Linux.
- Version AuralisVoiceKit: `0.96.0`.
- Microfono abierto: no.
- Audio real guardado: no.
- Artifact de preparacion: `manual-capture-checklist.md`.

Resultado:

- Dry-run: `passed=true`.
- `capture_backend`: `sounddevice`.
- `capture_readiness_plan.pip_command`: `python -m pip install "auralisvoicekit[sounddevice]"`.
- `capture_readiness_plan.setup_commands`: `sudo apt-get update` y `sudo apt-get install -y libportaudio2`.
- `capture_readiness_plan.post_install_check`: usa `--target-system Linux --json` sin abrir microfono.
- `capture_readiness_plan.real_capture_check_template`: conserva `--capture-test`, `--expected-system Linux` y `--confirm-input-reviewed`.
- Evidencia beta: `false`; falta Ubuntu/Linux real, microfono real, revision de entrada y `capture_checklist.ready_for_beta_evidence=true`.

Acciones siguientes:

1. Ejecutar el `post_install_check` en Ubuntu/Linux real despues de instalar el extra y PortAudio.
2. Ejecutar captura real solo despues de revisar permisos de microfono, dispositivo y entorno no sensible.
3. Mantener beta bloqueada hasta que `system_guard.expected_system_matched=true`, `input_review_confirmed=true` y `capture_checklist.ready_for_beta_evidence=true`.

## 2026-06-06 - Windows dry-run de readiness para salida system en Ubuntu/Linux

Comando ejecutado:

```powershell
python tools\output_pilot.py --output-dir pilot_runs\output\readiness-plan-linux --system Linux --text "Hola desde AuralisVoiceKit" --json
```

Alcance:

- Sistema anfitrion: Windows.
- Sistema objetivo simulado para comandos: Ubuntu/Linux.
- Version AuralisVoiceKit: `0.95.0`.
- Audio real: no.
- Operador presente: no.
- Texto hablado completo guardado: no; comandos sanitizados con `<text-redacted>`.

Resultado:

- Dry-run: `passed=true`.
- `target_output_backend.available`: `false`, esperado porque el host Windows no tiene `spd-say`/`espeak` en PATH.
- `target_output_backend.readiness_plan.setup_commands`: `sudo apt-get update` y `sudo apt-get install -y speech-dispatcher espeak`.
- `target_output_backend.readiness_plan.post_install_check`: usa `--system Linux --require-output-backend-ready --json` sin reproducir audio.
- `spoken_text_privacy_scan.passed`: `true`.
- Evidencia beta: `false`; falta audio real, operador, plataforma objetivo real y revision de voz.

Acciones siguientes:

1. Ejecutar el `post_install_check` en Ubuntu/Linux real despues de instalar `speech-dispatcher` o `espeak`.
2. Ejecutar salida real solo con operador presente y texto publico/no sensible.
3. Mantener beta bloqueada hasta que `target_output_backend.available=true`, `output_backend_ready_required=true`, `operator_checklist.voice_review_confirmed=true` y `operator_checklist.ready_for_beta_evidence=true`.

## 2026-06-06 - Windows preflight MP3 con plan de instalacion de backend

Comandos ejecutados:

```powershell
python tools\pilot_audio_fixture.py --output-dir pilot_runs\transcription\install-plan-fixture --format wav --format mp3 --json
python tools\transcription_pilot.py --output-dir pilot_runs\transcription\install-plan-preflight --preflight-only --audio pilot_runs\transcription\install-plan-fixture\pilot-sample.mp3 --audio-non-sensitive --backend whisper --normalize --min-audio-seconds 0.2 --max-audio-seconds 60 --json
```

Alcance:

- Sistema: Windows.
- Version AuralisVoiceKit: `0.94.0`.
- Audio real: no; fixture sintetico publico.
- Red/modelos reales: no.
- Artifact de preparacion: `real-transcription-next-step.md`.
- Texto esperado, transcripcion, nombres de archivos privados y rutas locales guardadas: no.

Resultado:

- Preflight: `passed=true`.
- Audio MP3 decodificado con ffmpeg: `audio.decoded=true`.
- Redaccion del nombre de audio: `audio.audio_file_name_redacted=true`.
- `target_backend.available`: `false`, esperado porque falta instalar `faster-whisper`.
- `target_backend.install_plan.pip_command`: `python -m pip install "auralisvoicekit[whisper]"`.
- `target_backend.install_plan.post_install_check`: usa `--require-target-backend-ready` antes de quitar `--preflight-only`.
- Evidencia beta: `false`; no hubo audio real, referencia revisada ni calidad humana.

Acciones siguientes:

1. Instalar el extra opcional del backend real en el mismo entorno virtual.
2. Repetir el preflight con `--require-target-backend-ready` y un MP3 propio no sensible.
3. Ejecutar `--real-transcription` solo despues de revisar privacidad del audio, referencia esperada y calidad local.

## 2026-06-06 - Windows readiness de transcripcion real sin modelo

Comando ejecutado:

```powershell
python tools\pilot_run.py --output-dir pilot_runs\safe --json
```

Alcance:

- Sistema: Windows.
- Version AuralisVoiceKit: `0.93.0`.
- Audio real: no.
- Red/modelos reales: no.
- Artifact de preparacion: `real-pilot-transcription-readiness.md`.
- Texto esperado, transcripcion, nombres de archivos y rutas locales guardadas: no.

Resultado:

- Piloto seguro: `passed=true`.
- ffmpeg para audio comprimido: `ok`.
- `transcription_readiness_card.status`: `recommended`.
- `transcription_readiness_card.usable_as_beta_evidence`: `false`.
- `local-real-transcription-ready`: `warning`, esperado porque falta instalar un backend real (`auralisvoicekit[whisper]` u `auralisvoicekit[openai]`).

Acciones siguientes:

1. Instalar o confirmar un backend real de transcripcion antes de usar `--real-transcription`.
2. Reemplazar `sample.mp3` solo localmente por un MP3 propio no sensible y ejecutar primero `--preflight-only`.
3. Mantener la beta bloqueada hasta tener evidencia real con `target_backend.available=true`, `target_backend_ready_required=true`, `reference_privacy_scan.passed=true` y `--confirm-quality-reviewed`.

## 2026-06-06 - Windows salida system dry-run con tarjeta de readiness

Comando ejecutado:

```powershell
python tools\output_pilot.py --output-dir pilot_runs\output\system-dry-run --json
```

Alcance:

- Sistema: Windows.
- Backend diagnosticado: `system`.
- Audio reproducido: no.
- Modo: dry-run.
- Artifact de preparacion: `real-pilot-system-output-readiness.md` en el piloto seguro.
- Texto completo guardado: no; comandos sanitizados con `<text-redacted>`.

Resultado:

- Piloto de salida: `passed=true`.
- Real audio requested: `false`.
- Operator confirmation status: `not-required`.
- Spoken text privacy scan: `passed`.
- Operator checklist ready for beta evidence: `false`, esperado porque no hubo audio real ni operador presente.

Acciones siguientes:

1. Revisar `real-pilot-system-output-readiness.md`, `output-operator-checklist.md` y `system-output-next-step.md`.
2. Ejecutar audio real solo con operador presente y texto publico/no sensible.
3. Mantener la beta bloqueada hasta que el piloto audible real use `--confirm-audible`, `--confirm-text-reviewed`, `--confirm-voice-reviewed`, `--require-output-backend-ready` y `--expected-system "Windows|Linux|Darwin"`.

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
