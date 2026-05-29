"""Lanzador de tests sin dependencias.

Ejecuta todas las funciones `test_*` de `test_basico.py` y muestra un
resumen. Util cuando no se tiene instalado pytest.

Uso (desde la raiz del proyecto):
    python senku/tests/run_tests.py
"""

import sys
import traceback
from pathlib import Path

# Permite ejecutarlo desde cualquier sitio anadiendo la raiz al path
RAIZ = Path(__file__).resolve().parents[2]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from senku.tests import test_basico as m


def main() -> int:
    funciones = [
        getattr(m, nombre)
        for nombre in dir(m)
        if nombre.startswith("test_") and callable(getattr(m, nombre))
    ]
    fallos = 0
    for fn in funciones:
        try:
            fn()
            print(f"  OK   {fn.__name__}")
        except AssertionError as e:
            fallos += 1
            print(f"  FALLO {fn.__name__}: {e}")
        except Exception as e:  # noqa: BLE001
            fallos += 1
            print(f"  ERROR {fn.__name__}: {type(e).__name__}: {e}")
            traceback.print_exc()
    print()
    print(f"Resultado: {len(funciones) - fallos}/{len(funciones)} tests superados")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
