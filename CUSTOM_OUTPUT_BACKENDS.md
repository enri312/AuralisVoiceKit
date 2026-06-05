# Backends de salida personalizados

Esta guia muestra como conectar una salida de voz propia a AuralisVoiceKit. Sirve para TTS local, APIs externas, colas de audio, integraciones con juegos, bots, telefonia o pruebas que no deben reproducir sonido real.

English: this guide shows how to connect a custom speech output backend to AuralisVoiceKit for local TTS, external APIs, audio queues, games, bots, telephony or silent tests.

## Contrato minimo

Un backend de salida implementa `SpeechOutputBackend`:

```python
from auralis_voicekit import VoiceKitConfig
from auralis_voicekit.backends import BackendInfo


class MyOutputBackend:
    name = "my-output"

    def info(self) -> BackendInfo:
        return BackendInfo(name=self.name, kind="output")

    def speak(self, text: str, config: VoiceKitConfig) -> None:
        if not text.strip():
            return
        print(text)
```

El metodo `speak()` debe recibir texto limpio y decidir que hacer con el: reproducirlo, guardarlo, enviarlo a una API o ponerlo en una cola. Si no puede funcionar, debe lanzar `BackendNotAvailable` u otro error propio de AuralisVoiceKit.

English: `speak()` receives clean text and can play it, store it, send it to an API or enqueue it. If the backend cannot run, raise `BackendNotAvailable` or another AuralisVoiceKit error.

## Registro en AuralisVoiceKit

Registra el backend con `BackendRegistry.register_output()` y selecciona su nombre en `VoiceKitConfig.output_backend`:

```python
from auralis_voicekit import AuralisVoiceKit, VoiceKitConfig
from auralis_voicekit.backends import create_default_registry

registry = create_default_registry()
registry.register_output("my-output", MyOutputBackend)

kit = AuralisVoiceKit(
    VoiceKitConfig(output_backend="my-output"),
    registry=registry,
)
kit.speak("Hola desde mi backend")
```

Si tu backend necesita estado compartido para pruebas o inspeccion, registra una factory que devuelva la instancia que quieres observar:

```python
backend = MyOutputBackend()
registry.register_output("my-output", lambda: backend)
```

## Ejemplo sin sonido real

El ejemplo `examples/custom_output_backend.py` implementa un backend en memoria. Es util para tests, asistentes que delegan salida a otra app y automatizaciones que no deben reproducir audio:

```bash
python examples/custom_output_backend.py --json
```

Desde Python:

```python
from examples.custom_output_backend import create_memory_voice_kit

kit, backend = create_memory_voice_kit()
kit.speak("Mensaje para cola interna")
print(backend.utterances)
```

## Eventos y privacidad

`AuralisVoiceKit.speak()` emite `output.started` y `output.completed`. Esos eventos incluyen el backend de salida, pero no el texto hablado. Esto permite observar el flujo sin registrar contenido sensible.

English: `speak()` emits `output.started` and `output.completed` with backend metadata, not spoken text.

Para persistir eventos usa `PrivacyEventLogger`:

```python
from auralis_voicekit import PrivacyEventLogger

with PrivacyEventLogger("auralis-output-events.jsonl") as logger:
    unsubscribe = logger.subscribe(kit.events)
    kit.speak("No se guardara este texto en el evento")
    unsubscribe()
```

## Recomendaciones

- Mantener el backend pequeno: `info()` y `speak()` deben ser faciles de probar.
- Validar dependencias en `info()` sin reproducir audio ni abrir conexiones caras.
- No guardar texto hablado si no es necesario.
- Usar `output_voice`, `output_rate`, `output_volume` y `metadata` antes de inventar nuevos parametros.
- Hacer que `speak("")` o texto con espacios no haga nada.
- Probar con un backend en memoria antes de conectar TTS real.

English: keep the backend small, validate dependencies in `info()`, avoid storing spoken text, reuse `VoiceKitConfig` fields and test with an in-memory backend before real TTS.

