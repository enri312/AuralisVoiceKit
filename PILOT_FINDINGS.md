# Hallazgos de pilotos

Este documento resume hallazgos de pilotos reales o semi-manuales. No debe incluir audio, transcripciones privadas, rutas locales completas ni nombres reales de dispositivos.

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

1. Ejecutar `python tools\output_pilot.py --speak --text "Hola desde AuralisVoiceKit" --json` solo con operador presente.
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
