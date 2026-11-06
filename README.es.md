# cortex9-git-safe-directory-discovery-model

[English](README.md) · [Guía práctica](PRACTICE.md)

Modelo en Python, en memoria, de cómo git descubre un repositorio subiendo
desde el directorio actual, y del chequeo de propiedad (`safe.directory`)
agregado por CVE-2022-24765. Compara tres modos: antes del fix, el fix del
commit 8959555 y el valor `*` del commit 0f85c4a.

**Es un modelo, no git, ni una reproducción de CVE-2022-24765.** Nunca
ejecuta git, nunca toca el sistema de archivos real y nunca ejecuta ni evalúa
valores de configuración. De la config de un repo solo se leen los *nombres*
de claves documentadas cuyo valor es un comando, como dato. Ver
[LIMITATIONS.md](LIMITATIONS.md).

## Qué se modela y de dónde

| Elemento | Fuente | Código |
|---|---|---|
| Subida: `<dir>/.git` (dir o archivo `gitdir:`), luego `<dir>` como bare; corte por techo y punto de montaje | git v2.35.2 `setup.c` | `discover` |
| Techo = ancestro *propio* más largo; el techo no se revisa; el cwd siempre | misma función | `longest_ancestor_length` |
| `GIT_DIR` → `GIT_DIR_EXPLICIT` sin chequeo | misma función | `Env.git_dir` |
| `ensure_valid_ownership`: dueño = uid actual → OK; si no, solo config system + global | commit 8959555; `read_very_early_config` en v2.35.2 | `ensure_valid_ownership` |
| Valor vacío resetea; coincidencia exacta tras interpolar marca seguro | commit 8959555 | idem |
| Solo se revisa el directorio de nivel superior | commit 8959555 | escenario 14 |
| `*` marca todo seguro; un vacío posterior lo anula | commit 0f85c4a | modo `fix_0f85c4a` |
| Amenaza: `C:\.git` de otro usuario, unidad montada, espacio temporal | notas de git 2.30.3 | escenario 02 |

## Ejecutar

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 -m git_safedir_model fixtures/scenarios/02_foreign_parent_repo.json
python3 scripts/gen_results.py /tmp/out && diff -r results /tmp/out
```

Resultados y detalles en [README.md](README.md). Guía en
[PRACTICE.md](PRACTICE.md). Licencia: Apache-2.0.
