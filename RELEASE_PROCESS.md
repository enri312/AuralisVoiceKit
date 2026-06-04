# Proceso de releases

Este proceso mantiene las versiones de AuralisVoiceKit simples y predecibles.

## Decision de version

| Tipo de cambio | Version | Ejemplo |
| --- | --- | --- |
| Correccion compatible | PATCH | `0.1.1` |
| Mejora compatible o backend nuevo | MINOR | `0.2.0` |
| Cambio incompatible de API | MAJOR | `1.0.0`, `2.0.0` |

Mientras el proyecto este en `0.x`, las mejoras grandes suben `MINOR` y las correcciones pequenas suben `PATCH`.

## Checklist

1. Revisar cambios desde la ultima version.
2. Decidir `PATCH`, `MINOR` o `MAJOR`.
3. Actualizar `src/auralis_voicekit/_version.py`.
4. Actualizar `CHANGELOG.md`.
5. Ejecutar tests locales.
6. Crear commit de release.
7. Crear tag anotado `vMAJOR.MINOR.PATCH`.
8. Subir rama y tag a GitHub.
9. Revisar el workflow de release.

## Comandos

```bash
python -m unittest discover -s tests
python -m auralis_voicekit.cli doctor
git add .
git commit -m "Release v0.1.0"
git tag -a v0.1.0 -m "AuralisVoiceKit v0.1.0"
git push origin main
git push origin v0.1.0
```

## Publicacion en PyPI

La primera etapa solo genera artefactos en GitHub Releases. La publicacion en PyPI se activara cuando la libreria tenga backend real y documentacion suficiente.
