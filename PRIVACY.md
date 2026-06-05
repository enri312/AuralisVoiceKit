# Privacidad y logs

AuralisVoiceKit trata audio, texto transcrito y rutas de archivos como datos sensibles. Esta guia explica como observar el sistema sin guardar contenido privado por accidente.

English: AuralisVoiceKit treats audio, transcripts and file paths as sensitive data. This guide explains how to observe the system without accidentally storing private content.

## Defaults seguros

La configuracion por defecto usa:

```python
from auralis_voicekit import VoiceKitConfig

config = VoiceKitConfig()
print(config.privacy_mode)  # True
print(config.log_level)     # INFO
```

Con `privacy_mode=True`, los eventos emitidos por `AuralisVoiceKit` no incluyen audio crudo ni texto transcrito. Los eventos conservan estado operativo como backend, duracion e indicadores de finalizacion.

English: with `privacy_mode=True`, events emitted by `AuralisVoiceKit` avoid raw audio and transcript text while preserving operational metadata.

## Que se considera sensible

Trata como sensible:

- bytes de audio o muestras PCM;
- texto transcrito y prompts;
- tokens, claves privadas y cabeceras de autorizacion;
- rutas de archivos que puedan revelar nombres de usuario o proyectos;
- metadata de proveedor que pueda contener fragmentos de texto.

English: audio bytes, transcripts, prompts, tokens, file paths and provider metadata should be handled as sensitive by default.

## Exportar eventos como JSONL seguro

Usa `PrivacyEventLogger` para guardar eventos como JSON Lines con payload sanitizado:

```python
from auralis_voicekit import AuralisVoiceKit, PrivacyEventLogger

kit = AuralisVoiceKit()

with PrivacyEventLogger("auralis-events.jsonl") as logger:
    unsubscribe = logger.subscribe(kit.events)
    result = kit.transcribe(chunk)
    unsubscribe()
```

Cada linea contiene `type`, `source`, `timestamp` y `payload`. Campos como `text`, `prompt`, `token`, `path`, `audio` o `raw` se reemplazan por `[redacted]`.

English: each JSONL line contains event type, source, timestamp and a sanitized payload. Sensitive fields are replaced with `[redacted]`.

## Sanitizar payloads manualmente

Si ya tienes eventos propios, puedes sanitizar diccionarios antes de enviarlos a tu logger:

```python
from auralis_voicekit import PrivacyLogConfig, sanitize_event_payload

payload = {
    "backend": "openai",
    "text": "contenido privado",
    "metadata": {"path": "sample.mp3", "duration_seconds": 2.0},
}

safe_payload = sanitize_event_payload(payload)
print(safe_payload)

debug_payload = sanitize_event_payload(
    payload,
    PrivacyLogConfig(privacy_mode=False),
)
```

`privacy_mode=False` permite conservar campos como `text`, pero los bytes se resumen por tipo y longitud para evitar logs binarios enormes.

English: `privacy_mode=False` can preserve fields such as `text`, but byte values are still summarized by type and length.

## Variables de entorno

```bash
export AURALIS_PRIVACY_MODE=true
export AURALIS_LOG_LEVEL=INFO
```

En PowerShell:

```powershell
$env:AURALIS_PRIVACY_MODE="true"
$env:AURALIS_LOG_LEVEL="INFO"
```

`VoiceKitConfig.from_env()` lee estas variables. La libreria no configura el logger global de Python por si sola; la aplicacion decide si escribe a consola, archivo o sistema de observabilidad.

English: `VoiceKitConfig.from_env()` reads these variables. The library does not configure Python global logging by itself; the application chooses where logs go.

## Recomendaciones para asistentes

- Mantener `privacy_mode=True` en produccion.
- Registrar eventos de estado, no contenido de audio.
- Separar logs tecnicos de muestras de audio usadas para depuracion.
- Borrar archivos WAV temporales cuando terminen las pruebas.
- No registrar `OPENAI_API_KEY` ni prompts con datos personales.
- Revisar logs antes de compartir issues publicos.

English: keep privacy mode enabled in production, log state instead of content, delete temporary audio, and review logs before sharing public issues.
