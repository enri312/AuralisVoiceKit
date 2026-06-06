# Checklist de beta

Este documento se genera con `tools\beta_readiness.py`. No debe incluir audio, transcripciones, rutas locales completas ni nombres reales de dispositivos.

## Estado

- Version: `0.124.0`
- Estado: `pilot`
- Listo para beta: `false`
- Gate de pilotos reales: `true`
- Evidencias JSON: `0`
- Evidencias ignoradas: `0`

## Bloqueadores para beta

- `windows_wasapi_capture`
- `real_transcription_quality`
- `system_output_audible`
- `ubuntu_linux_capture`
- `macos_capture`

## Checklist

- [x] `stability_gate_pilot` (blocker) - Stability gate allows real-world pilots
- [ ] `windows_wasapi_capture` (blocker) - Windows WASAPI capture pilot
  - Accion: Repeat the Windows WASAPI pilot with --sample-rate 48000, --expected-system Windows, --confirm-input-reviewed and --require-capture-backend-ready after checking permissions, input device and room privacy, then keep manual-capture-checklist.md, manual-capture-command.md and only sanitized findings.
  - Evidencia faltante: `Expected system matched: True`, `Target capture backend available: True`, `Capture backend readiness required: True`, `Input review confirmed: True`, `Manual capture command: manual-capture-command.md`
- [ ] `real_transcription_quality` (blocker) - Real transcription quality pilot
  - Accion: Run tools/transcription_pilot.py with --real-transcription, non-sensitive audio, --expected-text or --expected-text-file, a meaningful --min-word-accuracy, --min-audio-seconds/--max-audio-seconds duration guards and --confirm-audio-reviewed before model use plus --confirm-reference-reviewed before scoring with reference_privacy_scan.passed=true, preflight_decision.decision=ready_for_real_transcription or a repeated preflight after backend install, preflight_readiness.status=ready, preflight_readiness.ready_for_model_run=true, preflight_readiness.must_rerun_preflight=false and public-safe preflight_readiness redaction flags, --require-target-backend-ready before model execution, --timeout-seconds 30 when using --backend openai, --require-openai-api-key when using --backend openai, and --confirm-quality-reviewed after human review, then keep target_backend.available=true, target_backend_ready_required=true, credentials.checked=true, credentials.openai_api_key_required=true, credentials.openai_api_key_present=true and credentials.records_openai_api_key=false for OpenAI, transcription-review-checklist.md and real-transcription-next-step.md.
  - Evidencia faltante: `Real transcription requested: True`, `Target backend available: True`, `Target backend readiness required: True`, `Generated synthetic audio: False`, `Audio decode passed: True`, `Audio duration gate enabled: True`, `Audio duration gate passed: True`, `Transcript text redacted: True`, `Audio review confirmed: True`, `Reference review confirmed: True`, `Reference privacy scan passed: True`, `Quality review confirmed: True`, `Transcription checklist ready for beta evidence: True`
- [ ] `system_output_audible` (blocker) - Audible system output pilot
  - Accion: Run tools/output_pilot.py --speak --operator-present --confirm-audible --confirm-text-reviewed --confirm-voice-reviewed --require-output-backend-ready --expected-system "Windows|Linux|Darwin" --output-dir pilot_runs/output/system-real with a human operator, then keep output-operator-checklist.md, system-output-next-step.md, system_guard.expected_system_matched=true, target_output_backend.available=true, output_backend_ready_required=true, operator_checklist.expected_system_matched=true, spoken_text_privacy_scan.passed=true, operator_checklist.redacts_spoken_text=true, operator_checklist.records_operator_identity=false, operator_checklist.commands_available=true, operator_checklist.ready_for_real_audio=true, next_system_output.records_spoken_text=false and only sanitized findings.
  - Evidencia faltante: `Real audio requested: True`, `Output backend readiness required: True`, `Operator confirmation status: confirmed`, `Text review confirmed: True`, `Spoken text privacy scan passed: True`, `Voice review confirmed: True`, `Records operator identity: False`, `Redacts spoken text: True`, `Commands available: True`, `Ready for real audio: True`, `Operator checklist ready for beta evidence: True`
- [ ] `ubuntu_linux_capture` (blocker) - Ubuntu/Linux capture pilot
  - Accion: Run the manual capture pilot on Ubuntu/Linux with real hardware and --backend sounddevice or --backend pyaudio, --expected-system Linux --confirm-input-reviewed and --require-capture-backend-ready, then keep manual-capture-checklist.md, manual-capture-command.md, system_guard.expected_system_matched=true, capture_backend=sounddevice|pyaudio, target_capture_backend.available=true, capture_backend_ready_required=true, input_review_confirmed=true, capture_checklist.input_review_confirmed=true, capture_checklist.ready_for_beta_evidence=true and manual_capture_command_card safe-to-share redaction flags.
  - Evidencia faltante: `Sistema: Ubuntu/Linux`, `Target capture backend available: True`, `Capture backend readiness required: True`
- [ ] `macos_capture` (blocker) - macOS capture pilot
  - Accion: Run the manual capture pilot on macOS with real hardware and --backend sounddevice or --backend pyaudio, --expected-system Darwin --confirm-input-reviewed and --require-capture-backend-ready, then keep manual-capture-checklist.md, manual-capture-command.md, system_guard.expected_system_matched=true, capture_backend=sounddevice|pyaudio, target_capture_backend.available=true, capture_backend_ready_required=true, input_review_confirmed=true, capture_checklist.input_review_confirmed=true, capture_checklist.ready_for_beta_evidence=true and manual_capture_command_card safe-to-share redaction flags.
  - Evidencia faltante: `Sistema: macOS`, `Target capture backend available: True`, `Capture backend readiness required: True`

## Bugs conocidos

- `windows-wasapi-sample-rate`: resolved - Initial WASAPI invalid sample rate was fixed by exposing --sample-rate and passing at 48000 Hz.

## Siguientes acciones

- Repeat the Windows WASAPI pilot with --sample-rate 48000, --expected-system Windows, --confirm-input-reviewed and --require-capture-backend-ready after checking permissions, input device and room privacy, then keep manual-capture-checklist.md, manual-capture-command.md and only sanitized findings.
- Run tools/transcription_pilot.py with --real-transcription, non-sensitive audio, --expected-text or --expected-text-file, a meaningful --min-word-accuracy, --min-audio-seconds/--max-audio-seconds duration guards and --confirm-audio-reviewed before model use plus --confirm-reference-reviewed before scoring with reference_privacy_scan.passed=true, preflight_decision.decision=ready_for_real_transcription or a repeated preflight after backend install, preflight_readiness.status=ready, preflight_readiness.ready_for_model_run=true, preflight_readiness.must_rerun_preflight=false and public-safe preflight_readiness redaction flags, --require-target-backend-ready before model execution, --timeout-seconds 30 when using --backend openai, --require-openai-api-key when using --backend openai, and --confirm-quality-reviewed after human review, then keep target_backend.available=true, target_backend_ready_required=true, credentials.checked=true, credentials.openai_api_key_required=true, credentials.openai_api_key_present=true and credentials.records_openai_api_key=false for OpenAI, transcription-review-checklist.md and real-transcription-next-step.md.
- Run tools/output_pilot.py --speak --operator-present --confirm-audible --confirm-text-reviewed --confirm-voice-reviewed --require-output-backend-ready --expected-system "Windows|Linux|Darwin" --output-dir pilot_runs/output/system-real with a human operator, then keep output-operator-checklist.md, system-output-next-step.md, system_guard.expected_system_matched=true, target_output_backend.available=true, output_backend_ready_required=true, operator_checklist.expected_system_matched=true, spoken_text_privacy_scan.passed=true, operator_checklist.redacts_spoken_text=true, operator_checklist.records_operator_identity=false, operator_checklist.commands_available=true, operator_checklist.ready_for_real_audio=true, next_system_output.records_spoken_text=false and only sanitized findings.
- Run the manual capture pilot on Ubuntu/Linux with real hardware and --backend sounddevice or --backend pyaudio, --expected-system Linux --confirm-input-reviewed and --require-capture-backend-ready, then keep manual-capture-checklist.md, manual-capture-command.md, system_guard.expected_system_matched=true, capture_backend=sounddevice|pyaudio, target_capture_backend.available=true, capture_backend_ready_required=true, input_review_confirmed=true, capture_checklist.input_review_confirmed=true, capture_checklist.ready_for_beta_evidence=true and manual_capture_command_card safe-to-share redaction flags.
- Run the manual capture pilot on macOS with real hardware and --backend sounddevice or --backend pyaudio, --expected-system Darwin --confirm-input-reviewed and --require-capture-backend-ready, then keep manual-capture-checklist.md, manual-capture-command.md, system_guard.expected_system_matched=true, capture_backend=sounddevice|pyaudio, target_capture_backend.available=true, capture_backend_ready_required=true, input_review_confirmed=true, capture_checklist.input_review_confirmed=true, capture_checklist.ready_for_beta_evidence=true and manual_capture_command_card safe-to-share redaction flags.
