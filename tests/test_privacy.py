import io
import json
import unittest

from auralis_voicekit import (
    EventBus,
    PrivacyEventLogger,
    PrivacyLogConfig,
    VoiceEventType,
    event_to_log_record,
    sanitize_event_payload,
)


class PrivacyTests(unittest.TestCase):
    def test_sanitize_event_payload_redacts_sensitive_fields(self):
        payload = {
            "backend": "openai",
            "text": "transcripcion privada",
            "metadata": {
                "path": r"C:\Users\demo\secret.wav",
                "token": "abc123",
                "duration_seconds": 1.5,
            },
            "blob": b"audio bytes",
        }

        safe = sanitize_event_payload(payload)

        self.assertEqual(safe["backend"], "openai")
        self.assertEqual(safe["text"], "[redacted]")
        self.assertEqual(safe["metadata"]["path"], "[redacted]")
        self.assertEqual(safe["metadata"]["token"], "[redacted]")
        self.assertEqual(safe["metadata"]["duration_seconds"], 1.5)
        self.assertEqual(safe["blob"]["type"], "bytes")
        self.assertEqual(safe["blob"]["length"], len(b"audio bytes"))
        self.assertEqual(safe["blob"]["content"], "[redacted]")

    def test_event_to_log_record_can_preserve_text_when_privacy_is_disabled(self):
        event = EventBus().emit(
            VoiceEventType.TRANSCRIPTION_COMPLETED,
            {"backend": "null", "text": "hola"},
        )

        record = event_to_log_record(event, PrivacyLogConfig(privacy_mode=False))

        self.assertEqual(record["type"], "transcription.completed")
        self.assertEqual(record["payload"]["backend"], "null")
        self.assertEqual(record["payload"]["text"], "hola")
        self.assertIn("timestamp", record)

    def test_privacy_event_logger_writes_sanitized_jsonl(self):
        stream = io.StringIO()
        bus = EventBus()
        logger = PrivacyEventLogger(stream)
        unsubscribe = logger.subscribe(bus)

        bus.emit(VoiceEventType.TRANSCRIPTION_COMPLETED, {"backend": "openai", "text": "privado"})
        unsubscribe()

        record = json.loads(stream.getvalue())
        self.assertEqual(record["type"], "transcription.completed")
        self.assertEqual(record["payload"]["backend"], "openai")
        self.assertEqual(record["payload"]["text"], "[redacted]")


if __name__ == "__main__":
    unittest.main()
