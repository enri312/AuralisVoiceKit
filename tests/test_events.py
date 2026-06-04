import unittest

from auralis_voicekit import EventBus, VoiceEventType


class EventBusTests(unittest.TestCase):
    def test_emit_calls_specific_and_any_listeners(self):
        bus = EventBus()
        seen = []

        bus.subscribe(VoiceEventType.ANY, lambda event: seen.append(("any", event.type)))
        bus.subscribe(
            VoiceEventType.CAPTURE_STARTED,
            lambda event: seen.append(("specific", event.type)),
        )

        bus.emit(VoiceEventType.CAPTURE_STARTED)

        self.assertEqual(
            seen,
            [
                ("specific", VoiceEventType.CAPTURE_STARTED),
                ("any", VoiceEventType.CAPTURE_STARTED),
            ],
        )

    def test_unsubscribe(self):
        bus = EventBus()
        seen = []
        unsubscribe = bus.subscribe(VoiceEventType.ERROR, lambda event: seen.append(event.type))

        unsubscribe()
        bus.emit(VoiceEventType.ERROR)

        self.assertEqual(seen, [])


if __name__ == "__main__":
    unittest.main()
