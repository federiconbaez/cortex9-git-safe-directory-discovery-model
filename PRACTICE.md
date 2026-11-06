# Guía práctica / Practice guide

Ejercicios **offline y locales**: todo ocurre en un sistema de archivos en
memoria. No se ejecuta git ni se toca ningún repo real. *English summary at
the end.*

## Objetivos

1. Recorrer a mano el algoritmo de descubrimiento de git (v2.35.2).
2. Entender por qué un `.git` de otro usuario en un directorio padre era un
   problema (CVE-2022-24765) y qué cambia el fix.
3. Dominar la semántica de `safe.directory`: alcances, orden, reset, `*`.
4. Aplicar el patrón "verificar propiedad antes de confiar en config" en
   herramientas propias.

## Prerrequisitos

Python 3.10+. Lectura: notas de git 2.30.3, diffs de 8959555 y 0f85c4a,
`setup_git_directory_gently_1` en `setup.c` (ver [SOURCES.md](SOURCES.md)).

## Comandos locales

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 -m git_safedir_model fixtures/scenarios/02_foreign_parent_repo.json --mode pre_fix
python3 scripts/gen_results.py /tmp/out && diff -r results /tmp/out
```

## Ejercicios graduados

**Nivel 1 — subir.** Para 01, 02 y 11 escribe a mano la lista `visited` y
el resultado. Compara con `results/scenarios.json`.

**Nivel 2 — techo y montaje.** ¿Por qué en 11 el techo `/tmp` no se revisa
pero un cwd igual al techo sí? (test `test_cwd_is_checked_even_if_ceiling`).
Relaciónalo con el bucle `while (--offset > ceil_offset ...)`.

**Nivel 3 — alcances.** Explica 03, 04 y 05 citando `read_very_early_config`.
En 04, ¿por qué el modelo no puede decir que "leyó e ignoró" el
`safe.directory` del repo? Mira el test con spy `NoConfigReadWhenRejected`.
¿Por qué tendría sentido que la config del propio repo no pueda declararse
segura a sí misma?

**Nivel 4 — orden.** Predice 06 y 08 antes de ejecutarlos. Escribe una
secuencia system/global que termine segura tras un `*` y un reset.

**Nivel 5 — bordes.** 10 (barra final) y 14 (directorio intermedio ajeno):
¿son fallas del fix o decisiones? Argumenta con el código citado.

**Nivel 6 — código.** Agrega un modo `strict_gitdir` (tu propio diseño,
etiquetado como tal) que también exija que el directorio `.git` sea del
usuario. Añade escenarios, expectativas y tests; verifica que 01 y 03 no
cambian.

**Nivel 7 — defensa propia.** Escribe una función para una herramienta tuya
que lea un archivo de config de proyecto solo si el directorio es del
usuario o está en una lista permitida, reutilizando `ensure_valid_ownership`
como referencia. Incluye tests de vacío/reset.

## Vínculo modelo ↔ CVE

| Caso real | En el código |
|---|---|
| Prompt que ejecuta `git status` en un dir sin repo propio | `discover(..., cwd)` en escenario 02 |
| `C:\.git` / espacio temporal de otro usuario | `/tmp/.git` de Bob |
| Config ajena que define comandos | `command_valued_keys_in_repo_config` (solo nombres) |
| Fix 8959555 / 0f85c4a | modos `fix_8959555`, `fix_0f85c4a` |

---

## English summary

Offline, in-memory exercises only; git is never run. Levels: (1) trace the
discovery walk by hand; (2) ceiling and mount-point rules; (3) which config
scopes count and why; (4) value order, reset and `*`; (5) the trailing-slash
and intermediate-directory edges; (6) implement a self-designed stricter
mode with tests; (7) apply the ownership-before-config pattern in your own
tool.
