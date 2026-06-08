"""Dominio Senku via unified-planning (estilo Practica 4)."""

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
    dominio = Problem("dominio_senku")

    Casilla = UserType("Casilla")
    dominio.user_types.append(Casilla)

    ocupada = Fluent("ocupada", BoolType(), c=Casilla)
    vacia = Fluent("vacia", BoolType(), c=Casilla)
    salto = Fluent(
        "salto", BoolType(), desde=Casilla, sobre=Casilla, hasta=Casilla
    )
    for fluente in (ocupada, vacia, salto):
        dominio.add_fluent(fluente, default_initial_value=False)

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
    problema = construye_dominio_up().clone()
    problema.name = tablero.nombre

    Casilla = problema.user_type("Casilla")
    ocupada = problema.fluent("ocupada")
    vacia = problema.fluent("vacia")
    salto = problema.fluent("salto")

    objetos_por_coord = {}
    for coord in sorted(tablero.casillas):
        obj = Object(nombre_casilla(coord), Casilla)
        problema.add_object(obj)
        objetos_por_coord[coord] = obj

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

    for coord in tablero.meta_ocupadas:
        problema.add_goal(ocupada(objetos_por_coord[coord]))
    for coord in tablero.meta_vacias:
        problema.add_goal(vacia(objetos_por_coord[coord]))
    return problema
