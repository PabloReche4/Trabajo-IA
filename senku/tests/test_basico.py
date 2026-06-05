"""Tests unitarios basicos del sistema Senku.

Cubre:
    - Generacion de tableros y casillas.
    - Validacion de la condicion pagoda en la asignacion clasica.
    - Funcionamiento de BFS en un caso trivial solucionable.
    - Generacion y relectura de un fichero PDDL produce el mismo
      problema (round-trip).
"""

from pathlib import Path
import tempfile

from senku.src.busqueda import busqueda_primero_anchura, beam_search
from senku.src.estado import ProblemaSenku
from senku.src.generador_pddl import escribe_problema, problema_a_pddl
from senku.src.heuristicas import (
    pagoda_clasica,
    pagoda_uniforme,
    valor_pagoda,
    heuristica_pagoda,
)
from senku.src.lector_pddl import carga_con_parser_ligero
from senku.src.tableros import TABLEROS, Tablero


# ---------------------------------------------------------------------------
# Generacion de tableros
# ---------------------------------------------------------------------------


def test_todas_las_variantes_definidas():
    assert set(TABLEROS.keys()) == {1, 2, 3, 4, 5}


def test_inicial_y_meta_son_subconjuntos_de_casillas():
    for tablero in TABLEROS.values():
        assert tablero.inicial_ocupadas <= tablero.casillas
        assert tablero.inicial_vacias <= tablero.casillas
        assert tablero.meta_ocupadas <= tablero.casillas


def test_inicial_es_complemento_de_vacias():
    for tablero in TABLEROS.values():
        assert tablero.inicial_ocupadas | tablero.inicial_vacias == tablero.casillas


def test_saltos_son_ternas_alineadas():
    """Cada salto (a, b, c) debe estar dentro del tablero, alineado y
    con b siendo el punto medio de a y c."""
    for tablero in TABLEROS.values():
        for desde, sobre, hasta in tablero.saltos():
            assert {desde, sobre, hasta} <= tablero.casillas
            r1, c1 = desde
            r2, c2 = sobre
            r3, c3 = hasta
            # Punto medio
            assert (r1 + r3, c1 + c3) == (2 * r2, 2 * c2)
            # Alineamiento (horizontal o vertical)
            assert r1 == r2 == r3 or c1 == c2 == c3


# ---------------------------------------------------------------------------
# Funcion pagoda
# ---------------------------------------------------------------------------


def test_pagoda_uniforme_es_valida():
    for tablero in TABLEROS.values():
        pesos = pagoda_uniforme(tablero)
        for a, b, c in tablero.saltos():
            assert pesos[a] + pesos[b] >= pesos[c]


def test_pagoda_clasica_es_valida():
    """Comprueba la condicion a + b >= c en todas las ternas de salto."""
    for tablero in TABLEROS.values():
        pesos = pagoda_clasica(tablero)
        for a, b, c in tablero.saltos():
            assert pesos[a] + pesos[b] >= pesos[c], (
                f"Violacion pagoda en {tablero.nombre}: {a}+{b} < {c}"
            )


def test_pagoda_decrece_con_cada_movimiento():
    """Para todo estado inicial y para cada sucesor: valor pagoda no
    aumenta."""
    for tablero in TABLEROS.values():
        problema = ProblemaSenku.desde_tablero(tablero)
        pesos = pagoda_clasica(tablero)
        v_inicial = valor_pagoda(problema.inicial, pesos)
        for _, sucesor in problema.sucesores(problema.inicial):
            assert valor_pagoda(sucesor, pesos) <= v_inicial


# ---------------------------------------------------------------------------
# BFS en caso trivial
# ---------------------------------------------------------------------------


def _senku_3_en_linea() -> ProblemaSenku:
    """Tres casillas en linea con piezas en (0,0) y (0,1) y hueco en
    (0,2). La unica solucion es saltar (0,0) -> (0,2)."""
    casillas = frozenset({(0, 0), (0, 1), (0, 2)})
    tablero = Tablero(
        nombre="linea3",
        casillas=casillas,
        inicial_ocupadas=frozenset({(0, 0), (0, 1)}),
        inicial_vacias=frozenset({(0, 2)}),
        meta_ocupadas=frozenset({(0, 2)}),
        meta_vacias=frozenset({(0, 0), (0, 1)}),
    )
    return ProblemaSenku.desde_tablero(tablero)


def test_bfs_resuelve_caso_trivial():
    problema = _senku_3_en_linea()
    resultado = busqueda_primero_anchura(problema)
    assert resultado.exito
    assert len(resultado.movimientos) == 1
    assert resultado.movimientos[0] == ((0, 0), (0, 1), (0, 2))


def test_beam_resuelve_caso_trivial():
    problema = _senku_3_en_linea()
    pesos = pagoda_uniforme(problema.tablero)
    h = heuristica_pagoda(problema, pesos)
    resultado = beam_search(problema, h, beta=5, iteraciones_maximas=5)
    assert resultado.exito
    assert len(resultado.movimientos) == 1


def test_beam_conectividad_resuelve_cruz_inglesa():
    """La heuristica de conectividad permite a beam search resolver la
    cruz inglesa (variante 1), la mas representativa del Senku clasico.
    Es el resultado central del trabajo."""
    from senku.src.heuristicas import heuristica_conectividad
    from senku.src.busqueda import beam_search_con_reinicios

    problema = ProblemaSenku.desde_tablero(TABLEROS[1], modo_relajado=True)
    h = heuristica_conectividad(problema)
    resultado = beam_search_con_reinicios(
        problema, h, beta=300, intentos=6, iteraciones_maximas=80
    )
    assert resultado.exito
    # La cruz inglesa tiene 32 piezas; reducir a 1 requiere 31 saltos.
    assert len(resultado.movimientos) == 31


def test_beam_search_reporta_min_piezas():
    """beam_search debe rellenar min_piezas_alcanzadas, tanto en exito
    como en fallo, para conocer cuanto se aproximo a la meta."""
    problema = _senku_3_en_linea()
    pesos = pagoda_uniforme(problema.tablero)
    h = heuristica_pagoda(problema, pesos)
    r = beam_search(problema, h, beta=5, iteraciones_maximas=5)
    assert r.exito
    assert r.min_piezas_alcanzadas == 1


def test_beam_iterativo_resuelve_v1():
    """beam_search_iterativo, partiendo de un beta pequeno, debe acabar
    encontrando solucion a la cruz inglesa."""
    from senku.src.heuristicas import heuristica_conectividad
    from senku.src.busqueda import beam_search_iterativo

    problema = ProblemaSenku.desde_tablero(TABLEROS[1], modo_relajado=True)
    h = heuristica_conectividad(problema)
    resultado = beam_search_iterativo(
        problema, h, betas=[100, 300, 800], intentos_por_beta=3
    )
    assert resultado.exito
    assert len(resultado.movimientos) == 31
    assert "beta_exitoso" in resultado.parametros


def test_parche_fd_aplicable():
    """El parche de up-fast-downward se puede aplicar sin errores
    (idempotente). Verifica solo que la importacion y la llamada no
    fallan; no requiere ejecutar Fast Downward."""
    try:
        from senku.src.parche_fd import aplicar_parche
    except ImportError:
        return
    aplicar_parche()
    aplicar_parche()  # idempotente


def test_componentes_conexas():
    """Verifica el conteo de componentes conexas."""
    from senku.src.heuristicas import _componentes_conexas

    # Dos piezas adyacentes: 1 componente
    assert _componentes_conexas(frozenset({(0, 0), (0, 1)})) == 1
    # Dos piezas separadas: 2 componentes
    assert _componentes_conexas(frozenset({(0, 0), (0, 2)})) == 2
    # Conjunto vacio: 0 componentes
    assert _componentes_conexas(frozenset()) == 0
    # Una L conexa: 1 componente
    assert _componentes_conexas(frozenset({(0, 0), (0, 1), (1, 1)})) == 1


def test_es_meta_modo_relajado():
    """En modo relajado, basta con que quede una sola pieza."""
    problema = _senku_3_en_linea()
    relajado = ProblemaSenku.desde_tablero(problema.tablero, modo_relajado=True)
    # Estado con una pieza fuera de la posicion objetivo: estricto = no, relajado = si
    estado = frozenset({(0, 0)})
    assert not problema.es_meta(estado)
    assert relajado.es_meta(estado)


# ---------------------------------------------------------------------------
# Round-trip PDDL: generar y leer un problema produce el mismo resultado.
# ---------------------------------------------------------------------------


def test_round_trip_pddl_parser_ligero():
    tablero_original = TABLEROS[2]  # cuadrado 5x5: pequeno y manejable
    with tempfile.TemporaryDirectory() as tmpdir:
        ruta = Path(tmpdir) / "problema.pddl"
        ruta_dom = Path(tmpdir) / "dominio.pddl"
        # Reescribimos un dominio minimo (no se usa, solo necesita existir)
        ruta_dom.write_text(
            "(define (domain senku) (:requirements :strips))",
            encoding="utf-8",
        )
        escribe_problema(tablero_original, ruta)
        problema = carga_con_parser_ligero(ruta_dom, ruta)
    assert problema.tablero.casillas == tablero_original.casillas
    assert problema.inicial == tablero_original.inicial_ocupadas
    assert problema.meta_ocupadas == tablero_original.meta_ocupadas
    assert problema.meta_vacias == tablero_original.meta_vacias
    # Numero de saltos debe coincidir
    assert len(problema.saltos) == sum(1 for _ in tablero_original.saltos())


def test_problema_a_pddl_contiene_secciones():
    pddl = problema_a_pddl(TABLEROS[1])
    for seccion in ["(define", "(:domain senku)", "(:objects", "(:init", "(:goal"]:
        assert seccion in pddl


# ---------------------------------------------------------------------------
# Integracion con unified-planning (estilo Practica 4)
# ---------------------------------------------------------------------------


def test_construye_problema_up_es_compatible():
    """Verifica que el problema construido con la API Python de
    unified-planning tiene el numero correcto de objetos y goals, y
    que se puede serializar con PDDLWriter."""
    try:
        from unified_planning.io import PDDLWriter
        from senku.src.dominio_up import construye_problema_up
    except ImportError:
        return  # entorno sin unified-planning: saltamos

    tablero = TABLEROS[2]
    problema_up = construye_problema_up(tablero)
    assert sum(1 for _ in problema_up.all_objects) == len(tablero.casillas)
    n_goals = len(list(problema_up.goals))
    assert n_goals == len(tablero.meta_ocupadas) + len(tablero.meta_vacias)
    # Serializacion (sin escribir a disco)
    PDDLWriter(problema_up).get_problem()
    PDDLWriter(problema_up).get_domain()


def test_lector_unified_planning_round_trip():
    """Carga un PDDL generado por el escritor manual usando el lector
    basado en unified-planning."""
    try:
        from senku.src.lector_pddl import carga_con_unified_planning
    except ImportError:
        return
    with tempfile.TemporaryDirectory() as tmpdir:
        ruta_dom = Path(tmpdir) / "dominio.pddl"
        ruta_prob = Path(tmpdir) / "problema.pddl"
        # Copia el dominio Senku real y genera el problema
        dom_origen = Path(__file__).resolve().parents[1] / "pddl" / "dominio_senku.pddl"
        ruta_dom.write_text(dom_origen.read_text(encoding="utf-8"), encoding="utf-8")
        from senku.src.generador_pddl import escribe_problema
        escribe_problema(TABLEROS[4], ruta_prob)
        problema = carga_con_unified_planning(ruta_dom, ruta_prob)
        assert len(problema.tablero.casillas) == len(TABLEROS[4].casillas)
        assert len(problema.saltos) == sum(1 for _ in TABLEROS[4].saltos())
