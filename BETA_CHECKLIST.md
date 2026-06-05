# Checklist de beta

Este documento se genera con `tools\beta_readiness.py`. No debe incluir audio, transcripciones, rutas locales completas ni nombres reales de dispositivos.

## Estado

- Version: `0.52.0`
- Estado: `pilot`
- Listo para beta: `false`
- Gate de pilotos reales: `true`
- Evidencias JSON: `0`
- Evidencias ignoradas: `0`

## Bloqueadores para beta

- `real_transcription_quality`
- `system_output_audible`
- `ubuntu_linux_capture`
- `macos_capture`

## Checklist

- [x] `stability_gate_pilot` (blocker) - Stability gate allows real-world pilots
- [x] `windows_wasapi_capture` (blocker) - Windows WASAPI capture pilot
- [ ] `real_transcription_quality` (blocker) - Real transcription quality pilot
  - Accion: Run tools/transcription_pilot.py with --real-transcription, non-sensitive audio, --expected-text or --expected-text-file, and a meaningful --min-word-accuracy.
  - Evidencia faltante: `Real transcription requested: True`
- [ ] `system_output_audible` (blocker) - Audible system output pilot
  - Accion: Run tools/output_pilot.py --speak --operator-present --confirm-audible with a human operator and record only sanitized findings.
  - Evidencia faltante: `Real audio requested: True`, `Operator confirmation status: confirmed`
- [ ] `ubuntu_linux_capture` (blocker) - Ubuntu/Linux capture pilot
  - Accion: Run the manual capture pilot on Ubuntu/Linux with real hardware and sanitized artifacts.
  - Evidencia faltante: `Sistema: Ubuntu/Linux`
- [ ] `macos_capture` (blocker) - macOS capture pilot
  - Accion: Run the manual capture pilot on macOS with real hardware and sanitized artifacts.
  - Evidencia faltante: `Sistema: macOS`

## Bugs conocidos

- `windows-wasapi-sample-rate`: resolved - Initial WASAPI invalid sample rate was fixed by exposing --sample-rate and passing at 48000 Hz.

## Siguientes acciones

- Run tools/transcription_pilot.py with --real-transcription, non-sensitive audio, --expected-text or --expected-text-file, and a meaningful --min-word-accuracy.
- Run tools/output_pilot.py --speak --operator-present --confirm-audible with a human operator and record only sanitized findings.
- Run the manual capture pilot on Ubuntu/Linux with real hardware and sanitized artifacts.
- Run the manual capture pilot on macOS with real hardware and sanitized artifacts.
