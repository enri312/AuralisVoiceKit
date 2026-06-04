# Contribuir a AuralisVoiceKit

Gracias por ayudar a construir AuralisVoiceKit.

## Principios

- El core debe instalarse sin dependencias externas obligatorias.
- Los backends nativos deben vivir como extras opcionales.
- Los errores deben explicar que falta y como instalarlo.
- La privacidad por defecto no debe exponer audio crudo ni texto transcrito en eventos.
- Windows, Ubuntu/Linux y macOS deben estar considerados desde el diseno.

## Flujo de trabajo

1. Crear una rama desde `main`.
2. Hacer cambios pequenos y verificables.
3. Actualizar tests.
4. Actualizar documentacion si cambia la API o el comportamiento.
5. Ejecutar pruebas.
6. Abrir un Pull Request.

## Nombres de ramas

- `feature/...` para funciones nuevas compatibles.
- `fix/...` para correcciones.
- `docs/...` para documentacion.
- `release/...` para preparar una version.

## Verificacion local

```bash
python -m pip install -e .
python -m unittest discover -s tests
python -m auralis_voicekit.cli doctor
```

Con backend opcional:

```bash
python -m pip install -e ".[sounddevice]"
python -m auralis_voicekit.cli doctor --devices
```

## Cambios de version

Antes de cambiar la version, revisar `VERSIONING.md` y `RELEASE_PROCESS.md`.
