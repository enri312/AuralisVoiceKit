# Publicacion en PyPI

Esta guia deja AuralisVoiceKit listo para publicar en PyPI sin guardar tokens en GitHub. English: this guide prepares AuralisVoiceKit for tokenless PyPI publishing with Trusted Publishing.

## Estado actual

- Nombre de paquete: `auralisvoicekit`.
- Import principal: `auralis_voicekit`.
- Version: se lee desde `src/auralis_voicekit/_version.py`.
- Build backend: Hatchling.
- Artefactos esperados: wheel universal `py3-none-any` y sdist.
- Workflow manual: `.github/workflows/publish-pypi.yml`.

## Modelo de publicacion

AuralisVoiceKit usa dos pasos separados:

1. GitHub Release: se crea con el tag `vMAJOR.MINOR.PATCH` y adjunta `dist/*`.
2. PyPI/TestPyPI: se ejecuta manualmente desde GitHub Actions usando Trusted Publishing.

Esto evita publicar por accidente cada tag alpha y permite probar primero en TestPyPI.

## Trusted Publisher

Configura un publisher pendiente en PyPI y otro en TestPyPI con estos datos:

```text
Project name: auralisvoicekit
Owner: enri312
Repository name: AuralisVoiceKit
Workflow filename: publish-pypi.yml
Environment name for PyPI: pypi
Environment name for TestPyPI: testpypi
```

No agregues `PYPI_API_TOKEN` ni `TEST_PYPI_API_TOKEN` si usas Trusted Publishing. El workflow recibe una identidad temporal desde GitHub Actions mediante OIDC.

## Primera prueba en TestPyPI

1. Confirma que existe un tag publicado, por ejemplo `v0.14.0`.
2. En GitHub, abre `Actions`.
3. Ejecuta `Publish to PyPI`.
4. Usa:

```text
index: testpypi
tag: v0.14.0
```

5. Instala desde TestPyPI en un entorno limpio:

```bash
python -m venv .venv-testpypi
source .venv-testpypi/bin/activate
python -m pip install --upgrade pip
python -m pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ auralisvoicekit
python -m auralis_voicekit.cli doctor
```

Si estas trabajando desde el repositorio clonado, tambien puedes probar el flujo base sin extras:

```bash
python examples/pypi_quickstart.py --json
```

En PowerShell:

```powershell
py -m venv .venv-testpypi
.\.venv-testpypi\Scripts\Activate.ps1
py -m pip install --upgrade pip
py -m pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ auralisvoicekit
py -m auralis_voicekit.cli doctor
```

## Publicacion final en PyPI

Cuando TestPyPI este bien:

1. Ejecuta `Publish to PyPI` otra vez.
2. Usa:

```text
index: pypi
tag: v0.14.0
```

3. Prueba instalacion normal:

```bash
python -m venv .venv-pypi
source .venv-pypi/bin/activate
python -m pip install --upgrade pip
python -m pip install auralisvoicekit
python -m auralis_voicekit.cli doctor
```

Desde el repositorio clonado, el quickstart de PyPI valida generacion WAV, segmentacion y transcripcion `null` sin dependencias opcionales:

```bash
python examples/pypi_quickstart.py --json
```

## Checklist antes de publicar

- `CHANGELOG.md` actualizado.
- `src/auralis_voicekit/_version.py` actualizado.
- `python -m unittest discover -s tests` pasa.
- `python examples/pypi_quickstart.py --json` pasa desde el repositorio clonado.
- Si hay cambios de audio comprimido: `AURALIS_RUN_FFMPEG_INTEGRATION=1 python -m unittest tests.test_ffmpeg_integration` pasa.
- `python -m build` genera wheel y sdist.
- `python -m twine check dist/*` pasa.
- GitHub CI pasa en Windows, Ubuntu/Linux y macOS.
- GitHub Release existe para el tag elegido.

## Referencias oficiales

- https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/
- https://docs.pypi.org/trusted-publishers/
- https://docs.pypi.org/trusted-publishers/using-a-publisher/
- https://docs.pypi.org/attestations/producing-attestations/
