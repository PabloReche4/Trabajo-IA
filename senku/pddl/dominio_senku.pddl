(define
  (domain senku)
  (:requirements :strips)
  (:predicates
    ; (ocupada ?p) indica que la posicion ?p contiene una pieza
    (ocupada ?p)
    ; (vacia ?p) indica que la posicion ?p no contiene pieza (hueco)
    (vacia ?p)
    ; (salto ?desde ?sobre ?hasta) describe que las tres posiciones
    ; estan alineadas, consecutivas y permiten un salto valido
    ; desde ?desde, pasando por ?sobre, hasta ?hasta.
    (salto ?desde ?sobre ?hasta)
  )
  (:action mover
    :parameters (?desde ?sobre ?hasta)
    :precondition (and
      (salto ?desde ?sobre ?hasta)
      (ocupada ?desde)
      (ocupada ?sobre)
      (vacia ?hasta)
    )
    :effect (and
      (not (ocupada ?desde))
      (vacia ?desde)
      (not (ocupada ?sobre))
      (vacia ?sobre)
      (not (vacia ?hasta))
      (ocupada ?hasta)
    )
  )
)
