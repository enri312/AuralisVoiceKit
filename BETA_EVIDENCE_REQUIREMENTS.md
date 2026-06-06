# Requisitos de evidencias beta

Este documento describe los campos JSON que pueden cerrar blockers de beta. No requiere audio, transcripciones, rutas locales completas ni nombres reales de dispositivos.

## Artifacts aceptados

- `manual-pilot-report.json`
- `output-pilot-report.json`
- `transcription-pilot-report.json`

## Requisitos por blocker

### windows_wasapi_capture

- Artifact: `manual-pilot-report.json`
- Comando sugerido: `python tools/manual_pilot.py --capture-test --backend wasapi --device default --sample-rate 48000 --expected-system Windows --confirm-input-reviewed --require-capture-backend-ready --json`
- Campos requeridos:
  - `project` = `AuralisVoiceKit`
  - `system` = `Windows`
  - `system_guard.expected_system_matched` = `True`
  - `capture_backend` = `wasapi`
  - `target_capture_backend.available` = `True`
  - `capture_backend_ready_required` = `True`
  - `hardware_capture_tested` = `True`
  - `input_review_confirmed` = `True`
  - `capture_checklist.input_review_confirmed` = `True`
  - `capture_checklist.ready_for_beta_evidence` = `True`
  - `manual_capture_command_card.artifact` = `manual-capture-command.md`
  - `manual_capture_command_card.blocker` = `windows_wasapi_capture`
  - `manual_capture_command_card.ready_for_beta_evidence` = `True`
  - `manual_capture_command_card.safe_to_share` = `True`
  - `manual_capture_command_card.uses_placeholders` = `True`
  - `manual_capture_command_card.preflight_uses_microphone` = `False`
  - `manual_capture_command_card.real_capture_requires_microphone` = `True`
  - `manual_capture_command_card.records_audio` = `False`
  - `manual_capture_command_card.records_audio_bytes` = `False`
  - `manual_capture_command_card.records_device_name` = `False`
  - `manual_capture_command_card.records_local_paths` = `False`
  - `passed` = `True`

### real_transcription_quality

- Artifact: `transcription-pilot-report.json`
- Comando sugerido: `python tools/transcription_pilot.py --real-transcription --audio sample.mp3 --audio-non-sensitive --confirm-audio-reviewed --confirm-reference-reviewed --backend whisper --model base --normalize --expected-text "Hola desde AuralisVoiceKit" --min-word-accuracy 0.75 --min-audio-seconds 0.2 --max-audio-seconds 60 --confirm-quality-reviewed --require-target-backend-ready --json`
- Campos requeridos:
  - `project` = `AuralisVoiceKit`
  - `real_transcription_requested` = `True`
  - `target_backend.available` = `True`
  - `target_backend_ready_required` = `True`
  - `preflight_readiness.status` = `ready`
  - `preflight_readiness.decision` = `ready_for_real_transcription`
  - `preflight_readiness.ready_for_model_run` = `True`
  - `preflight_readiness.must_rerun_preflight` = `False`
  - `preflight_readiness.safe_to_share` = `True`
  - `preflight_readiness.usable_as_beta_evidence` = `False`
  - `preflight_readiness.records_audio` = `False`
  - `preflight_readiness.records_transcripts` = `False`
  - `preflight_readiness.records_expected_text` = `False`
  - `preflight_readiness.records_audio_file_name` = `False`
  - `preflight_readiness.records_local_paths` = `False`
  - `preflight_readiness.backend_ready` = `True`
  - `preflight_readiness.audio_decoded` = `True`
  - `preflight_readiness.duration_gate_enabled` = `True`
  - `preflight_readiness.duration_gate_passed` = `True`
  - `audio_confirmed_non_sensitive` = `True`
  - `audio.generated_synthetic_audio` = `False`
  - `audio.audio_confirmed_non_sensitive` = `True`
  - `audio.decoded` = `True`
  - `audio.audio_file_name_redacted` = `True`
  - `audio.duration_gate.enabled` = `True`
  - `audio.duration_gate.passed` = `True`
  - `audio_review_confirmed` = `True`
  - `reference_review_confirmed` = `True`
  - `reference_privacy_scan.passed` = `True`
  - `quality_review_confirmed` = `True`
  - `passed` = `True`
  - `transcript.text_redacted` = `True`
  - `quality.enabled` = `True`
  - `quality.passed` = `True`
  - `quality.min_word_accuracy` = `>= 0.75`
  - `transcription_checklist.audio_review_confirmed` = `True`
  - `transcription_checklist.records_audio_path` = `False`
  - `transcription_checklist.records_audio_file_name` = `False`
  - `transcription_checklist.records_transcript_text` = `False`
  - `transcription_checklist.records_expected_text` = `False`
  - `transcription_checklist.records_expected_text_file_name` = `False`
  - `transcription_checklist.redacts_transcript_text` = `True`
  - `transcription_checklist.redacts_expected_text` = `True`
  - `transcription_checklist.reference_review_confirmed` = `True`
  - `transcription_checklist.reference_privacy_scan_passed` = `True`
  - `transcription_checklist.quality_review_confirmed` = `True`
  - `transcription_checklist.ready_for_beta_evidence` = `True`
- Campos condicionales:
  - Si `target_backend.name` = `openai`:
    - `credentials.checked` = `True`
    - `credentials.openai_api_key_required` = `True`
    - `credentials.openai_api_key_present` = `True`
    - `credentials.records_openai_api_key` = `False`

### system_output_audible

- Artifact: `output-pilot-report.json`
- Comando sugerido: `python tools/output_pilot.py --speak --operator-present --confirm-audible --confirm-text-reviewed --confirm-voice-reviewed --require-output-backend-ready --expected-system "Windows|Linux|Darwin" --output-dir pilot_runs/output/system-real --text "Hola desde AuralisVoiceKit" --json`
- Campos requeridos:
  - `project` = `AuralisVoiceKit`
  - `backend` = `system`
  - `system_guard.expected_system_matched` = `True`
  - `target_output_backend.available` = `True`
  - `output_backend_ready_required` = `True`
  - `real_audio_requested` = `True`
  - `operator_confirmation_status` = `confirmed`
  - `text_review_confirmed` = `True`
  - `spoken_text_privacy_scan.passed` = `True`
  - `voice_review_confirmed` = `True`
  - `operator_checklist.expected_system_matched` = `True`
  - `operator_checklist.records_operator_identity` = `False`
  - `operator_checklist.redacts_spoken_text` = `True`
  - `operator_checklist.text_review_confirmed` = `True`
  - `operator_checklist.spoken_text_privacy_scan_passed` = `True`
  - `operator_checklist.voice_review_confirmed` = `True`
  - `operator_checklist.commands_available` = `True`
  - `operator_checklist.ready_for_real_audio` = `True`
  - `operator_checklist.ready_for_beta_evidence` = `True`
  - `next_system_output.uses_placeholders` = `True`
  - `next_system_output.records_spoken_text` = `False`
  - `next_system_output.records_operator_identity` = `False`
  - `system_output_command_card.artifact` = `system-output-next-step.md`
  - `system_output_command_card.blocker` = `system_output_audible`
  - `system_output_command_card.ready_for_beta_evidence` = `True`
  - `system_output_command_card.safe_to_share` = `True`
  - `system_output_command_card.uses_placeholders` = `True`
  - `system_output_command_card.preflight_plays_audio` = `False`
  - `system_output_command_card.real_output_requires_operator` = `True`
  - `system_output_command_card.records_audio` = `False`
  - `system_output_command_card.records_spoken_text` = `False`
  - `system_output_command_card.records_operator_identity` = `False`
  - `system_output_command_card.records_local_paths` = `False`
  - `passed` = `True`

### ubuntu_linux_capture

- Artifact: `manual-pilot-report.json`
- Comando sugerido: `python tools/manual_pilot.py --capture-test --backend sounddevice --device default --expected-system Linux --confirm-input-reviewed --require-capture-backend-ready --json`
- Nota: If PyAudio is the installed capture stack, use --backend pyaudio with the same flags.
- Campos requeridos:
  - `project` = `AuralisVoiceKit`
  - `system` = `Linux | Ubuntu/Linux | Ubuntu`
  - `system_guard.expected_system_matched` = `True`
  - `capture_backend` = `sounddevice | pyaudio`
  - `target_capture_backend.available` = `True`
  - `capture_backend_ready_required` = `True`
  - `hardware_capture_tested` = `True`
  - `input_review_confirmed` = `True`
  - `capture_checklist.input_review_confirmed` = `True`
  - `capture_checklist.ready_for_beta_evidence` = `True`
  - `manual_capture_command_card.artifact` = `manual-capture-command.md`
  - `manual_capture_command_card.blocker` = `ubuntu_linux_capture`
  - `manual_capture_command_card.ready_for_beta_evidence` = `True`
  - `manual_capture_command_card.safe_to_share` = `True`
  - `manual_capture_command_card.uses_placeholders` = `True`
  - `manual_capture_command_card.preflight_uses_microphone` = `False`
  - `manual_capture_command_card.real_capture_requires_microphone` = `True`
  - `manual_capture_command_card.records_audio` = `False`
  - `manual_capture_command_card.records_audio_bytes` = `False`
  - `manual_capture_command_card.records_device_name` = `False`
  - `manual_capture_command_card.records_local_paths` = `False`
  - `passed` = `True`

### macos_capture

- Artifact: `manual-pilot-report.json`
- Comando sugerido: `python tools/manual_pilot.py --capture-test --backend sounddevice --device default --expected-system Darwin --confirm-input-reviewed --require-capture-backend-ready --json`
- Nota: If PyAudio is the installed capture stack, use --backend pyaudio with the same flags.
- Campos requeridos:
  - `project` = `AuralisVoiceKit`
  - `system` = `Darwin | macOS | Mac`
  - `system_guard.expected_system_matched` = `True`
  - `capture_backend` = `sounddevice | pyaudio`
  - `target_capture_backend.available` = `True`
  - `capture_backend_ready_required` = `True`
  - `hardware_capture_tested` = `True`
  - `input_review_confirmed` = `True`
  - `capture_checklist.input_review_confirmed` = `True`
  - `capture_checklist.ready_for_beta_evidence` = `True`
  - `manual_capture_command_card.artifact` = `manual-capture-command.md`
  - `manual_capture_command_card.blocker` = `macos_capture`
  - `manual_capture_command_card.ready_for_beta_evidence` = `True`
  - `manual_capture_command_card.safe_to_share` = `True`
  - `manual_capture_command_card.uses_placeholders` = `True`
  - `manual_capture_command_card.preflight_uses_microphone` = `False`
  - `manual_capture_command_card.real_capture_requires_microphone` = `True`
  - `manual_capture_command_card.records_audio` = `False`
  - `manual_capture_command_card.records_audio_bytes` = `False`
  - `manual_capture_command_card.records_device_name` = `False`
  - `manual_capture_command_card.records_local_paths` = `False`
  - `passed` = `True`

## Privacidad

- No audio bytes are required in beta evidence.
- No full transcript or expected text is required in beta readiness evidence.
- User audio file names and expected-text file names must be redacted.
- OpenAI evidence records credential presence only, never the API key value.
- Reference privacy scans expose only pass/fail, risk counts and risk types.
- Spoken text privacy scans expose only pass/fail, risk counts and risk types.
- Manual capture command cards must use placeholders and must not record audio, device names or local paths.
- System output command cards must use placeholders and must not record audio, spoken text, operator identity or local paths.
- Only structured fields and sanitized artifact names are used.
