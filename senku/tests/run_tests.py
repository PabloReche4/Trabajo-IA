"""Lanzador de tests sin pytest."""

import sys
import traceback
from pathlib import Path

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
