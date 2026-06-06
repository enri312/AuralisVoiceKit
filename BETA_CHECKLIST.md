# Checklist de beta

Este documento se genera con `tools\beta_readiness.py`. No debe incluir audio, transcripciones, rutas locales completas ni nombres reales de dispositivos.

## Estado

- Version: `0.81.0`
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
  - Accion: Run tools/transcription_pilot.py with --real-transcription, non-sensitive audio, --expected-text or --expected-text-file, a meaningful --min-word-accuracy, --min-audio-seconds/--max-audio-seconds duration guards and --confirm-audio-reviewed before model use plus --confirm-reference-reviewed before scoring with reference_privacy_scan.passed=true, and --confirm-quality-reviewed after human review, then keep transcription-review-checklist.md and real-transcription-next-step.md.
  - Evidencia faltante: `Real transcription requested: True`, `Audio review confirmed: True`, `Reference review confirmed: True`, `Reference privacy scan passed: True`, `Quality review confirmed: True`, `Transcription checklist ready for beta evidence: True`
- [ ] `system_output_audible` (blocker) - Audible system output pilot
  - Accion: Run tools/output_pilot.py --speak --operator-present --confirm-audible --confirm-text-reviewed --confirm-voice-reviewed --expected-system "Windows|Linux|Darwin" --output-dir pilot_runs/output/system-real with a human operator, then keep output-operator-checklist.md, system-output-next-step.md, system_guard.expected_system_matched=true, operator_checklist.expected_system_matched=true, spoken_text_privacy_scan.passed=true and only sanitized findings.
  - Evidencia faltante: `Real audio requested: True`, `Operator confirmation status: confirmed`, `Text review confirmed: True`, `Spoken text privacy scan passed: True`, `Voice review confirmed: True`, `Operator checklist ready for beta evidence: True`
- [ ] `ubuntu_linux_capture` (blocker) - Ubuntu/Linux capture pilot
  - Accion: Run the manual capture pilot on Ubuntu/Linux with real hardware and --backend sounddevice or --backend pyaudio, --expected-system Linux --confirm-input-reviewed, then keep manual-capture-checklist.md, system_guard.expected_system_matched=true, capture_backend=sounddevice|pyaudio, input_review_confirmed=true, capture_checklist.input_review_confirmed=true and capture_checklist.ready_for_beta_evidence=true.
  - Evidencia faltante: `Sistema: Ubuntu/Linux`
- [ ] `macos_capture` (blocker) - macOS capture pilot
  - Accion: Run the manual capture pilot on macOS with real hardware and --backend sounddevice or --backend pyaudio, --expected-system Darwin --confirm-input-reviewed, then keep manual-capture-checklist.md, system_guard.expected_system_matched=true, capture_backend=sounddevice|pyaudio, input_review_confirmed=true, capture_checklist.input_review_confirmed=true and capture_checklist.ready_for_beta_evidence=true.
  - Evidencia faltante: `Sistema: macOS`

## Bugs conocidos

- `windows-wasapi-sample-rate`: resolved - Initial WASAPI invalid sample rate was fixed by exposing --sample-rate and passing at 48000 Hz.

## Siguientes acciones

- Run tools/transcription_pilot.py with --real-transcription, non-sensitive audio, --expected-text or --expected-text-file, a meaningful --min-word-accuracy, --min-audio-seconds/--max-audio-seconds duration guards and --confirm-audio-reviewed before model use plus --confirm-reference-reviewed before scoring with reference_privacy_scan.passed=true, and --confirm-quality-reviewed after human review, then keep transcription-review-checklist.md and real-transcription-next-step.md.
- Run tools/output_pilot.py --speak --operator-present --confirm-audible --confirm-text-reviewed --confirm-voice-reviewed --expected-system "Windows|Linux|Darwin" --output-dir pilot_runs/output/system-real with a human operator, then keep output-operator-checklist.md, system-output-next-step.md, system_guard.expected_system_matched=true, operator_checklist.expected_system_matched=true, spoken_text_privacy_scan.passed=true and only sanitized findings.
- Run the manual capture pilot on Ubuntu/Linux with real hardware and --backend sounddevice or --backend pyaudio, --expected-system Linux --confirm-input-reviewed, then keep manual-capture-checklist.md, system_guard.expected_system_matched=true, capture_backend=sounddevice|pyaudio, input_review_confirmed=true, capture_checklist.input_review_confirmed=true and capture_checklist.ready_for_beta_evidence=true.
- Run the manual capture pilot on macOS with real hardware and --backend sounddevice or --backend pyaudio, --expected-system Darwin --confirm-input-reviewed, then keep manual-capture-checklist.md, system_guard.expected_system_matched=true, capture_backend=sounddevice|pyaudio, input_review_confirmed=true, capture_checklist.input_review_confirmed=true and capture_checklist.ready_for_beta_evidence=true.
