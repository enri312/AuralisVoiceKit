import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
PYPI_QUICKSTART = ROOT / "examples" / "pypi_quickstart.py"
CUSTOM_OUTPUT_BACKEND = ROOT / "examples" / "custom_output_backend.py"
SYSTEM_OUTPUT_DEMO = ROOT / "examples" / "system_output_demo.py"
LOCAL_ASSISTANT_PRIVACY_DEMO = ROOT / "examples" / "local_assistant_privacy_demo.py"


def _load_pypi_quickstart():
    spec = importlib.util.spec_from_file_location("pypi_quickstart", PYPI_QUICKSTART)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_custom_output_backend():
    spec = importlib.util.spec_from_file_location("custom_output_backend", CUSTOM_OUTPUT_BACKEND)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_system_output_demo():
    spec = importlib.util.spec_from_file_location("system_output_demo", SYSTEM_OUTPUT_DEMO)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_local_assistant_privacy_demo():
    spec = importlib.util.spec_from_file_location(
        "local_assistant_privacy_demo",
        LOCAL_ASSISTANT_PRIVACY_DEMO,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ExampleTests(unittest.TestCase):
    def test_pypi_quickstart_run_demo_writes_wav_and_turns(self):
        module = _load_pypi_quickstart()

        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "quickstart.wav"
            payload = module.run_demo(output=str(output), duration_seconds=0.5, chunk_duration_ms=100)

            self.assertTrue(output.exists())
            self.assertEqual(payload["output"], str(output))
            self.assertGreaterEqual(payload["chunks"], 1)
            self.assertGreaterEqual(len(payload["turns"]), 1)
            self.assertEqual(payload["transcription_backend"], "null")

    def test_pypi_quickstart_script_outputs_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "quickstart.wav"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(PYPI_QUICKSTART),
                    "--output",
                    str(output),
                    "--duration",
                    "0.5",
                    "--chunk-ms",
                    "100",
                    "--json",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

        payload = json.loads(completed.stdout)
        self.assertEqual(payload["transcription_backend"], "null")
        self.assertGreaterEqual(len(payload["turns"]), 1)

    def test_custom_output_backend_demo_collects_utterances_and_events(self):
        module = _load_custom_output_backend()

        payload = module.run_demo("Hola custom")

        self.assertEqual(payload["backend"], "memory")
        self.assertEqual(payload["utterances"], ["Hola custom"])
        self.assertEqual(
            [event["type"] for event in payload["events"]],
            ["output.started", "output.completed"],
        )

    def test_custom_output_backend_script_outputs_json(self):
        completed = subprocess.run(
            [
                sys.executable,
                str(CUSTOM_OUTPUT_BACKEND),
                "--text",
                "Hola JSON",
                "--json",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        payload = json.loads(completed.stdout)
        self.assertEqual(payload["backend"], "memory")
        self.assertEqual(payload["utterances"], ["Hola JSON"])

    def test_system_output_demo_dry_run_uses_system_backend_without_audio(self):
        module = _load_system_output_demo()

        payload = module.run_demo(
            "Hola system",
            system="Darwin",
            voice="Monica",
            rate=180,
        )

        self.assertTrue(payload["dry_run"])
        self.assertEqual(payload["backend"], "system")
        self.assertTrue(payload["spoken"])
        self.assertEqual(payload["voices"][0]["id"], "Monica")
        self.assertEqual(
            [event["type"] for event in payload["events"]],
            ["output.started", "output.completed"],
        )
        self.assertEqual(
            payload["commands"][-1]["argv"],
            ["/usr/bin/say", "-v", "Monica", "-r", "180", "Hola system"],
        )

    def test_system_output_demo_script_outputs_json(self):
        completed = subprocess.run(
            [
                sys.executable,
                str(SYSTEM_OUTPUT_DEMO),
                "--system",
                "Linux",
                "--text",
                "Hola JSON system",
                "--voice",
                "spanish",
                "--rate",
                "160",
                "--volume",
                "80",
                "--json",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        payload = json.loads(completed.stdout)
        self.assertTrue(payload["dry_run"])
        self.assertEqual(payload["system"], "Linux")
        self.assertEqual(payload["voices"][0]["id"], "spanish")
        self.assertEqual(
            payload["commands"][-1]["argv"],
            [
                "/usr/bin/espeak",
                "-v",
                "spanish",
                "-s",
                "160",
                "-a",
                "80",
                "Hola JSON system",
            ],
        )

    def test_local_assistant_privacy_demo_writes_sanitized_logs(self):
        module = _load_local_assistant_privacy_demo()

        with tempfile.TemporaryDirectory() as tmpdir:
            payload = module.run_demo(output_dir=tmpdir, duration_seconds=0.5, chunk_duration_ms=100)
            log_path = Path(payload["log_path"])

            self.assertTrue(Path(payload["input_wav"]).exists())
            self.assertTrue(log_path.exists())
            self.assertGreaterEqual(len(payload["turns"]), 1)
            self.assertEqual(payload["responses"], payload["utterances"])
            self.assertTrue(payload["privacy_checks"]["text_redacted"])
            self.assertTrue(payload["privacy_checks"]["path_redacted"])
            self.assertTrue(payload["privacy_checks"]["token_redacted"])

            log_text = log_path.read_text(encoding="utf-8")

        self.assertIn("transcription.completed", payload["log_event_types"])
        self.assertIn("output.completed", payload["log_event_types"])
        self.assertNotIn(module.DEMO_PRIVATE_COMMAND, log_text)
        self.assertNotIn(module.DEMO_PRIVATE_TOKEN, log_text)
        self.assertIn("[redacted]", log_text)

    def test_local_assistant_privacy_demo_script_outputs_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            completed = subprocess.run(
                [
                    sys.executable,
                    str(LOCAL_ASSISTANT_PRIVACY_DEMO),
                    "--output-dir",
                    tmpdir,
                    "--duration",
                    "0.5",
                    "--chunk-ms",
                    "100",
                    "--json",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

        payload = json.loads(completed.stdout)
        self.assertGreaterEqual(len(payload["turns"]), 1)
        self.assertTrue(payload["privacy_checks"]["text_redacted"])
        self.assertTrue(payload["privacy_checks"]["path_redacted"])
        self.assertTrue(payload["privacy_checks"]["token_redacted"])


if __name__ == "__main__":
    unittest.main()
