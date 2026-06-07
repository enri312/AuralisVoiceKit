# Proceso de releases

Este proceso mantiene las versiones de AuralisVoiceKit simples y predecibles.

## Decision de version

| Tipo de cambio | Version | Ejemplo |
| --- | --- | --- |
| Correccion compatible | PATCH | `0.1.1` |
| Mejora compatible o backend nuevo | MINOR | `0.2.0` |
| Cambio incompatible de API | MAJOR | `1.0.0`, `2.0.0` |

Mientras el proyecto este en `0.x`, las mejoras grandes suben `MINOR` y las correcciones pequenas suben `PATCH`.

## Cadencia de publicacion

No se crea tag ni GitHub Release en cada mejora. Durante alpha, las mejoras se acumulan en `CHANGELOG.md` bajo `[Unreleased]` y se publica un tag solo cuando haya 5 mejoras o commits publicables desde el ultimo tag, o cuando el usuario pida publicar explicitamente.

Antes de crear un tag, contar el lote pendiente:

```bash
git describe --tags --abbrev=0
git log <ultimo_tag>..HEAD --oneline
```

Si el conteo es menor a 5, se puede hacer commit y push, pero se deja la version como pendiente/desarrollo y no se dispara release. English: alpha releases are batched; tag only after 5 publishable improvements unless explicitly requested.

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
10. Si se publicara en PyPI, probar primero el workflow manual `Publish to PyPI` con `index=testpypi`.

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

La primera etapa genera artefactos en GitHub Releases. La publicacion en PyPI queda separada en el workflow manual `.github/workflows/publish-pypi.yml` para evitar subidas accidentales durante la etapa alpha.

La ruta recomendada es:

1. Crear y subir el tag.
2. Esperar que CI y `Release` pasen en GitHub.
3. Ejecutar `Publish to PyPI` con `index=testpypi`.
4. Instalar desde TestPyPI en un entorno limpio y correr `auralis doctor`.
5. Ejecutar `Publish to PyPI` con `index=pypi`.

La guia completa esta en:

```text
PYPI.md
```
