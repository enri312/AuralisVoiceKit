from auralis_voicekit.backends import create_default_registry


def main() -> int:
    registry = create_default_registry()
    backend = registry.create_capture("sounddevice")
    for device in backend.list_devices():
        marker = " (default)" if device.is_default else ""
        print(f"{device.id}: {device.name}{marker}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
