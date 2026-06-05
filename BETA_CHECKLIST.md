# Checklist de beta

Este documento se genera con `tools\beta_readiness.py`. No debe incluir audio, transcripciones, rutas locales completas ni nombres reales de dispositivos.

## Estado

- Version: `0.60.0`
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
  - Accion: Run tools/transcription_pilot.py with --real-transcription, non-sensitive audio, --expected-text or --expected-text-file, a meaningful --min-word-accuracy, --min-audio-seconds/--max-audio-seconds duration guards and --confirm-quality-reviewed after human review, then keep transcription-review-checklist.md.
  - Evidencia faltante: `Real transcription requested: True`, `Quality review confirmed: True`, `Transcription checklist ready for beta evidence: True`
- [ ] `system_output_audible` (blocker) - Audible system output pilot
  - Accion: Run tools/output_pilot.py --speak --operator-present --confirm-audible --output-dir pilot_runs/output/system-real with a human operator, then keep output-operator-checklist.md and only sanitized findings.
  - Evidencia faltante: `Real audio requested: True`, `Operator confirmation status: confirmed`, `Operator checklist ready for beta evidence: True`
- [ ] `ubuntu_linux_capture` (blocker) - Ubuntu/Linux capture pilot
  - Accion: Run the manual capture pilot on Ubuntu/Linux with real hardware and --expected-system Linux, then keep manual-capture-checklist.md, system_guard.expected_system_matched=true and capture_checklist.ready_for_beta_evidence=true.
  - Evidencia faltante: `Sistema: Ubuntu/Linux`
- [ ] `macos_capture` (blocker) - macOS capture pilot
  - Accion: Run the manual capture pilot on macOS with real hardware and --expected-system Darwin, then keep manual-capture-checklist.md, system_guard.expected_system_matched=true and capture_checklist.ready_for_beta_evidence=true.
  - Evidencia faltante: `Sistema: macOS`

## Bugs conocidos

- `windows-wasapi-sample-rate`: resolved - Initial WASAPI invalid sample rate was fixed by exposing --sample-rate and passing at 48000 Hz.

## Siguientes acciones

- Run tools/transcription_pilot.py with --real-transcription, non-sensitive audio, --expected-text or --expected-text-file, a meaningful --min-word-accuracy, --min-audio-seconds/--max-audio-seconds duration guards and --confirm-quality-reviewed after human review, then keep transcription-review-checklist.md.
- Run tools/output_pilot.py --speak --operator-present --confirm-audible --output-dir pilot_runs/output/system-real with a human operator, then keep output-operator-checklist.md and only sanitized findings.
- Run the manual capture pilot on Ubuntu/Linux with real hardware and --expected-system Linux, then keep manual-capture-checklist.md, system_guard.expected_system_matched=true and capture_checklist.ready_for_beta_evidence=true.
- Run the manual capture pilot on macOS with real hardware and --expected-system Darwin, then keep manual-capture-checklist.md, system_guard.expected_system_matched=true and capture_checklist.ready_for_beta_evidence=true.
