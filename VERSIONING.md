# Versionado de AuralisVoiceKit

AuralisVoiceKit usa versionado semantico: `MAJOR.MINOR.PATCH`.

## Politica

- `0.x`: etapa alpha/beta. La API puede cambiar, pero cada cambio debe quedar explicado en `CHANGELOG.md`.
- `1.x`: API publica estable para asistentes de voz.
- `PATCH`: correcciones internas, bugs, documentacion y mejoras compatibles.
- `MINOR`: nuevas funciones compatibles, nuevos backends opcionales o ampliaciones de API.
- `MAJOR`: cambios incompatibles en la API publica.

## Compatibilidad con Python

El paquete base declara `requires-python = ">=3.10"` y no usa limite superior artificial. Si una version futura de Python rompe algo real, se documenta el problema y se corrige el backend afectado antes de restringir el paquete completo.

La version del paquete vive en:

```text
src/auralis_voicekit/_version.py
```

`pyproject.toml` lee esa version mediante Hatchling. No se debe duplicar manualmente la version en varios archivos.

## Compatibilidad de sistemas

El core debe funcionar en:

- Windows
- Ubuntu y otras distribuciones Linux razonables
- macOS

Los backends pueden tener requisitos propios. Por ejemplo, `sounddevice` depende de PortAudio a traves del paquete `sounddevice`, y cada sistema puede requerir configuracion de audio diferente.

## Criterio para subir version

Antes de cambiar version:

1. Actualizar `CHANGELOG.md`.
2. Ejecutar tests.
3. Ejecutar `auralis doctor`.
4. Verificar que el paquete base importa sin extras.
5. Confirmar si el cambio es `PATCH`, `MINOR` o `MAJOR`.

## Cadencia de tags y releases

Durante la etapa alpha, las mejoras pueden quedar documentadas en `[Unreleased]` sin crear tag inmediato. Para evitar llenar GitHub con releases demasiado pequenas, se crea tag y GitHub Release solo cuando haya 5 mejoras o commits publicables desde el ultimo tag, o cuando el usuario pida publicar explicitamente.

Antes de taggear, contar los cambios pendientes:

```text
git describe --tags --abbrev=0
git log <ultimo_tag>..HEAD --oneline
python tools/release_batch_status.py --json
```

Si hay menos de 5 commits/mejoras publicables, el cambio queda como pendiente o version de desarrollo en `CHANGELOG.md`; no se sube tag ni GitHub Release todavia. Para automatizaciones, `python tools/release_batch_status.py --fail-if-not-ready` devuelve codigo 1 cuando aun no corresponde tag. El JSON expone `batch_state` (`fresh`, `collecting` o `ready`) y `publishable_commits_needed` para distinguir un lote recien reiniciado de un lote en progreso.

English: alpha releases are batched; tag only after 5 publishable improvements since the latest tag, unless an explicit release is requested.

## GitHub Releases

Las releases se manejan con tags anotados:

```text
vMAJOR.MINOR.PATCH
```

Ejemplos:

- `v0.1.1` para un fix pequeno.
- `v0.2.0` para una mejora grande compatible.
- `v1.0.0` para primera API estable.

El workflow `.github/workflows/release.yml` construye los artefactos cuando se sube un tag con ese formato.

## PyPI

La publicacion en PyPI es manual durante la etapa alpha. El workflow `.github/workflows/publish-pypi.yml` publica un tag existente en TestPyPI o PyPI usando Trusted Publishing.

Checklist corto:

1. Publicar tag y GitHub Release.
2. Probar `index=testpypi`.
3. Validar instalacion limpia.
4. Publicar `index=pypi`.

Los pasos completos estan en `PYPI.md`.
