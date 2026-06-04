# Roadmap de AuralisVoiceKit

Este roadmap define como convertir AuralisVoiceKit en una libreria completa de voz para Python moderno, con Windows como primera plataforma y con compatibilidad futura como principio central.

## Norte del proyecto

AuralisVoiceKit debe permitir crear asistentes de voz sin depender obligatoriamente de PyAudio, sin bloquear versiones nuevas de Python y sin obligar al usuario a instalar compiladores para probar el paquete base.

La meta no es competir con todos los motores de voz a la vez. La meta es construir una capa clara, extensible y confiable que conecte captura, transcripcion, eventos y salida de audio.

## Reglas de compatibilidad

- El core debe seguir sin dependencias externas obligatorias.
- No se debe agregar un limite superior artificial de Python salvo que exista una incompatibilidad real.
- Cada backend nativo debe vivir en un extra opcional.
- Si un backend no esta instalado, la libreria debe explicar que falta sin romper el import principal.
- Las pruebas deben correr en la version actual de Python y en la siguiente version disponible o prerelease cuando sea viable.
- La API publica debe cambiar poco y con motivos claros.

## Estado actual

| Area | Estado |
| --- | --- |
| Core Python | Scaffold inicial |
| Modelos de audio | Inicial |
| Eventos | Inicial |
| CLI `doctor` | Inicial |
| Backend `null` | Funcional |
| Backend `sounddevice` | Scaffold opcional |
| Versionado | Politica inicial |
| Compatibilidad Windows/Linux/macOS | Documentacion inicial |
| Transcripcion real | Pendiente |
| Salida de voz real | Pendiente |
| CI multiplataforma | Pendiente |
| Publicacion en PyPI | Pendiente |

## Fase 0 - Base del proyecto

**Objetivo:** dejar una libreria instalable, importable y testeable.

Entregables:

- `pyproject.toml` con paquete editable.
- `src/auralis_voicekit` como estructura principal.
- Modelos `AudioFormat`, `AudioChunk`, `AudioDevice` y `TranscriptResult`.
- `VoiceKitConfig` con configuracion por defecto y variables de entorno.
- `EventBus` para eventos internos.
- Backend `null` para pruebas sin hardware.
- CLI `auralis doctor`.
- Tests unitarios basicos.

Criterio de salida:

- `python -m unittest discover -s tests` pasa.
- `python -m auralis_voicekit.cli doctor` corre sin instalar extras.
- `import auralis_voicekit` no intenta cargar backends nativos.

Estado: en progreso, con primer scaffold ya creado.

## Fase 1 - Captura real de microfono

**Objetivo:** grabar audio real sin PyAudio obligatorio.

Entregables:

- Backend `sounddevice` funcional para captura PCM16.
- Enumeracion de dispositivos de entrada.
- Seleccion de dispositivo por id, nombre o default.
- Start/stop robusto sin dejar streams abiertos.
- Eventos `capture.started`, `audio.chunk`, `capture.stopped` con payload seguro.
- Ejemplo `examples/capture_microphone.py`.
- Tests con mocks para no depender de hardware.

Criterio de salida:

- El usuario puede grabar chunks de audio desde un microfono en Windows.
- Si `sounddevice` no esta instalado, el error recomienda el extra correcto.
- La captura no registra bytes de audio en eventos cuando `privacy_mode=True`.

## Fase 2 - Utilidades de audio

**Objetivo:** dar herramientas basicas para preparar audio antes de transcribir.

Entregables:

- Calculo de RMS y nivel de energia.
- Calibracion de ruido ambiente.
- Deteccion simple de silencio.
- Segmentacion por voz/silencio.
- Normalizacion basica de volumen.
- Guardado opcional a WAV para depuracion.

Criterio de salida:

- Se puede escuchar, calibrar y segmentar una frase corta sin transcriptor real.
- Las utilidades trabajan con `AudioChunk` y no fuerzan dependencias externas.

## Fase 3 - Transcripcion

**Objetivo:** convertir audio en texto mediante backends intercambiables.

Entregables:

- Contrato estable para transcriptores.
- Backend local inicial, preferiblemente Whisper o faster-whisper como extra opcional.
- Backend por API como extra opcional.
- Resultado con texto, idioma, confianza aproximada y metadatos.
- Eventos `transcription.started` y `transcription.completed`.
- Manejo claro de errores y timeouts.

Criterio de salida:

- El usuario puede transcribir un archivo WAV o un chunk capturado.
- El core sigue instalando sin dependencias de transcripcion.
- El texto transcrito no aparece en eventos si `privacy_mode=True`.

## Fase 4 - Salida de voz y audio

**Objetivo:** permitir respuestas habladas y eventos de salida.

Entregables:

- Contrato estable para salida de voz.
- Backend `null` para pruebas.
- Backend Windows inicial para TTS local si es viable.
- Backend por API como extra opcional.
- Cola simple de reproduccion.
- Eventos `output.started` y `output.completed`.

Criterio de salida:

- Un asistente puede llamar `kit.speak("texto")` sin conocer el backend.
- El backend de salida puede reemplazarse por uno custom.

## Fase 5 - Loop de asistente

**Objetivo:** ofrecer un flujo completo escuchar -> transcribir -> responder.

Entregables:

- API de alto nivel para sesiones de voz.
- Hooks para wake word o activacion externa.
- Integracion limpia con Alice o cualquier `AgentLoop`.
- Ejemplo `examples/assistant_loop.py`.
- Cancelacion y cierre ordenado.

Criterio de salida:

- Un asistente puede recibir texto limpio desde voz con pocas lineas de codigo.
- El loop puede detenerse sin procesos colgados ni streams abiertos.

## Fase 6 - Windows primero

**Objetivo:** pulir la experiencia real en Windows.

Entregables:

- Mejor diagnostico de permisos de microfono.
- Mejor reporte de dispositivos y host APIs.
- Investigacion de backend WASAPI dedicado.
- Mensajes especificos para errores comunes de audio en Windows.
- Guia de instalacion para PowerShell.

Criterio de salida:

- `auralis doctor` ayuda a diagnosticar microfono, backend y permisos.
- La documentacion explica claramente que hacer cuando no hay audio.

## Fase 7 - Calidad, CI y empaquetado

**Objetivo:** preparar la libreria para publicacion.

Entregables:

- Tests unitarios y de integracion con mocks.
- Linting y formateo.
- CI para Windows y Linux.
- Matriz de Python estable y prerelease.
- Build de wheel y sdist.
- Versionado semantico.
- Licencia y metadata final.

Criterio de salida:

- La libreria se puede publicar en PyPI.
- El paquete base se instala limpio con `pip install auralisvoicekit`.

## Fase 8 - Beta publica

**Objetivo:** validar la libreria con proyectos reales.

Entregables:

- Documentacion de API estable.
- Guias de captura, transcripcion, salida y privacidad.
- Ejemplos completos.
- Integracion piloto con Alice.
- Politica de compatibilidad y cambios.
- Checklist de bugs conocidos.

Criterio de salida:

- AuralisVoiceKit puede usarse en un asistente real sin depender de hacks locales.
- Hay una ruta clara hacia `1.0.0`.

## Fase 9 - Version 1.0

**Objetivo:** declarar una API estable para asistentes de voz.

Entregables:

- API publica congelada para `1.x`.
- Backends principales documentados.
- Tests de regresion para flujos clave.
- Documentacion completa.
- Publicacion en PyPI.
- Integracion estable con Alice.

Criterio de salida:

- Instalar, diagnosticar, capturar, transcribir y emitir eventos funciona de forma predecible.
- Los cambios futuros pueden agregarse sin romper usuarios existentes.

## Backlog tecnico

- Backend WASAPI dedicado.
- Backend PyAudio solo como compatibilidad opcional.
- Soporte para archivos WAV/FLAC como entrada.
- Adaptadores para modelos locales.
- Adaptadores para APIs externas.
- Wake word externo.
- Medidor de energia en tiempo real.
- Grabacion temporal con borrado seguro.
- Exportacion de logs sin contenido sensible.
- Benchmarks de latencia.

## Prioridad inmediata

1. Completar backend `sounddevice`.
2. Agregar ejemplo de captura real.
3. Agregar pruebas con mocks de `sounddevice`.
4. Mejorar `auralis doctor` para listar dispositivos cuando el backend este instalado.
5. Agregar utilidades de energia y calibracion de ruido.
