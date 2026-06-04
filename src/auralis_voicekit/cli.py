"""Command line helpers for AuralisVoiceKit."""

from __future__ import annotations

import argparse
from importlib.util import find_spec
import platform
import sys

from ._version import __version__
from .backends import create_default_registry
from .exceptions import BackendNotAvailable
from .models import AudioDevice


def _optional_status(module_name: str) -> str:
    return "available" if find_spec(module_name) is not None else "missing"


def _print_device(device: AudioDevice) -> None:
    marker = " default" if device.is_default else ""
    channels = f", channels={device.channels}" if device.channels is not None else ""
    host_api = f", host_api={device.host_api}" if device.host_api else ""
    print(f"  [{device.id}] {device.name}{marker} ({device.kind}{channels}{host_api})")


def _print_devices(backend_name: str) -> int:
    registry = create_default_registry()
    try:
        backend = registry.create_capture(backend_name)
        devices = list(backend.list_devices())
    except BackendNotAvailable as exc:
        print(f"Cannot list devices for capture backend {backend_name!r}: {exc}")
        return 1

    print(f"Input devices from capture backend {backend_name!r}:")
    if not devices:
        print("  No input devices found.")
        return 0
    for device in devices:
        _print_device(device)
    return 0


def _print_doctor(show_devices: bool = False, device_backend: str = "sounddevice") -> int:
    print(f"AuralisVoiceKit {__version__}")
    print(f"Python: {sys.version.split()[0]}")
    print(f"Platform: {platform.platform()}")
    print(f"Implementation: {platform.python_implementation()}")
    print()
    print("Optional dependencies:")
    print(f"  sounddevice: {_optional_status('sounddevice')}")
    print()
    print("Backend registry:")
    for info in create_default_registry().backend_info():
        status = "ok" if info.available else "missing"
        reason = f" - {info.reason}" if info.reason else ""
        print(f"  {info.kind}:{info.name} [{status}]{reason}")
    if show_devices:
        print()
        return _print_devices(device_backend)
    return 0


def _print_backends() -> int:
    for info in create_default_registry().backend_info():
        deps = ", ".join(info.dependencies) if info.dependencies else "none"
        status = "available" if info.available else "unavailable"
        print(f"{info.kind}:{info.name} - {status} - deps: {deps}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="auralis")
    subparsers = parser.add_subparsers(dest="command")
    doctor_parser = subparsers.add_parser("doctor", help="show runtime compatibility information")
    doctor_parser.add_argument(
        "--devices",
        action="store_true",
        help="list input devices after the compatibility report",
    )
    doctor_parser.add_argument(
        "--backend",
        default="sounddevice",
        help="capture backend used when listing devices",
    )
    subparsers.add_parser("backends", help="list registered backends")
    devices_parser = subparsers.add_parser("devices", help="list input devices")
    devices_parser.add_argument("--backend", default="sounddevice", help="capture backend to inspect")
    args = parser.parse_args(argv)

    if args.command is None:
        return _print_doctor()
    if args.command == "doctor":
        return _print_doctor(show_devices=args.devices, device_backend=args.backend)
    if args.command == "backends":
        return _print_backends()
    if args.command == "devices":
        return _print_devices(args.backend)
    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
