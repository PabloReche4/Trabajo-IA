"""Construccion del dominio y los problemas del Senku usando la API
Python de unified-planning (estilo Practica 4).

En la Practica 4 se mostraron dos formas de definir un problema de
planificacion:

    a) Leer un par de ficheros PDDL con `PDDLReader.parse_problem`.
    b) Construir el problema en codigo Python con `Problem`, `Fluent`,
       `UserType` e `InstantaneousAction` y serializarlo con
       `PDDLWriter`.

Este modulo implementa (b) para el dominio Senku. La ventaja frente a
escribir el PDDL a mano es que se obtiene validacion sintactica
inmediata, soporte para escribir el .pddl resultante y la posibilidad de
pasarselo directamente a un planificador como Fast Downward a traves de
`OneshotPlanner`.

La funcion `construye_problema_up(tablero)` devuelve un objeto
`unified_planning.model.Problem` listo para resolver con Fast Downward
o cualquier otro planificador soportado por la biblioteca.
"""

from typing import TYPE_CHECKING

from unified_planning.shortcuts import (
    BoolType,
    Fluent,
    InstantaneousAction,
    Object,
    Problem,
    UserType,
)

from .tableros import Tablero, nombre_casilla


if TYPE_CHECKING:  # pragma: no cover
    from unified_planning.model import Problem as ProblemUP


def construye_dominio_up() -> "ProblemUP":
    """Crea un objeto Problem con la definicion del dominio Senku
    (predicados y esquema de accion) pero sin objetos, estado inicial
    ni meta. Es el equivalente al fichero PDDL de dominio."""
    dominio = Problem("dominio_senku")

    # Tipos de objetos: una unica clase para las casillas.
    Casilla = UserType("Casilla")
    dominio.user_types.append(Casilla)

    # Predicados: ocupada, vacia y salto (este ultimo describe la
    # geometria como hechos del estado inicial).
    ocupada = Fluent("ocupada", BoolType(), c=Casilla)
    vacia = Fluent("vacia", BoolType(), c=Casilla)
    salto = Fluent(
        "salto", BoolType(), desde=Casilla, sobre=Casilla, hasta=Casilla
    )
    for fluente in (ocupada, vacia, salto):
        dominio.add_fluent(fluente, default_initial_value=False)

    # Accion `mover`: misma estructura que en la version PDDL.
    mover = InstantaneousAction("mover", desde=Casilla, sobre=Casilla, hasta=Casilla)
    desde = mover.desde
    sobre = mover.sobre
    hasta = mover.hasta
    for precondicion in [
        salto(desde, sobre, hasta),
        ocupada(desde),
        ocupada(sobre),
        vacia(hasta),
    ]:
        mover.add_precondition(precondicion)
    mover.add_effect(ocupada(desde), False)
    mover.add_effect(vacia(desde), True)
    mover.add_effect(ocupada(sobre), False)
    mover.add_effect(vacia(sobre), True)
    mover.add_effect(vacia(hasta), False)
    mover.add_effect(ocupada(hasta), True)
    dominio.add_action(mover)
    return dominio


def construye_problema_up(tablero: Tablero) -> "ProblemUP":
    """Devuelve un objeto Problem completamente especificado a partir de
    la definicion interna del tablero. Util para invocar Fast Downward
    sin pasar por un fichero PDDL intermedio."""
    problema = construye_dominio_up().clone()
    problema.name = tablero.nombre

    Casilla = problema.user_type("Casilla")
    ocupada = problema.fluent("ocupada")
    vacia = problema.fluent("vacia")
    salto = problema.fluent("salto")

    # Objetos: una constante por casilla.
    objetos_por_coord = {}
    for coord in sorted(tablero.casillas):
        obj = Object(nombre_casilla(coord), Casilla)
        problema.add_object(obj)
        objetos_por_coord[coord] = obj

    # Estado inicial.
    for coord in tablero.inicial_ocupadas:
        problema.set_initial_value(ocupada(objetos_por_coord[coord]), True)
    for coord in tablero.inicial_vacias:
        problema.set_initial_value(vacia(objetos_por_coord[coord]), True)
    for desde, sobre, hasta in tablero.saltos():
        problema.set_initial_value(
            salto(
                objetos_por_coord[desde],
                objetos_por_coord[sobre],
                objetos_por_coord[hasta],
            ),
            True,
        )

    # Meta.
    for coord in tablero.meta_ocupadas:
        problema.add_goal(ocupada(objetos_por_coord[coord]))
    for coord in tablero.meta_vacias:
        problema.add_goal(vacia(objetos_por_coord[coord]))
    return problema
