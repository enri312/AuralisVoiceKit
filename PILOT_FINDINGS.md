# Hallazgos de pilotos

Este documento resume hallazgos de pilotos reales o semi-manuales. No debe incluir audio, transcripciones privadas, rutas locales completas ni nombres reales de dispositivos.

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
2. Ejecutar `python tools\manual_pilot.py --capture-test --backend wasapi --device default --json`.
3. Revisar el nuevo `doctor-analysis.json` con foco en categorias `windows_audio:*`.
4. Actualizar este documento con el resultado del piloto de captura real.
