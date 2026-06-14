"""Dominio y problemas del Senku con la API Python de unified-planning.

En la Practica 4 se vieron dos formas de definir un problema:
  (a) leer ficheros PDDL con PDDLReader.parse_problem;
  (b) construirlo en codigo con Problem, Fluent, UserType e
      InstantaneousAction (y volcarlo a PDDL con PDDLWriter).

Aqui implementamos (b). La ventaja frente a escribir el PDDL a mano es
que tenemos validacion sintactica al construirlo y podemos pasarselo
directamente a Fast Downward (via OneshotPlanner) sin pasar por fichero.

construye_problema_up(tablero) devuelve un Problem listo para resolver.
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
    """Devuelve un Problem con el dominio Senku (predicados + accion).

    No incluye objetos, estado inicial ni meta: es el equivalente al
    fichero PDDL de dominio, solo la parte comun."""
    dominio = Problem("dominio_senku")

    # Un solo tipo de objeto: Casilla.
    Casilla = UserType("Casilla")
    dominio.user_types.append(Casilla)

    # ocupada/vacia: estado dinamico de cada casilla.
    # salto: codifica la geometria como hechos estaticos del :init.
    ocupada = Fluent("ocupada", BoolType(), c=Casilla)
    vacia = Fluent("vacia", BoolType(), c=Casilla)
    salto = Fluent(
        "salto", BoolType(), desde=Casilla, sobre=Casilla, hasta=Casilla
    )
    for fluente in (ocupada, vacia, salto):
        dominio.add_fluent(fluente, default_initial_value=False)

    # Accion `mover`: la misma del PDDL hecho a mano.
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
    """Problem completo (dominio + objetos + init + meta) para un Tablero.

    Lo usamos para lanzar Fast Downward directamente sin escribir el
    PDDL a un fichero."""
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
