(define
  (domain dominio_mundo_bloques)
  (:requirements :strips)
  (:predicates
    (sobre_la_mesa ?b)
    (sobre ?b1 ?b2)
    (agarrado ?b)
    (brazo_libre)
    (despejado ?b)
  )
  (:action agarrar
    :parameters (?b)
    :precondition (and
      (sobre_la_mesa ?b)
      (despejado ?b)
      (brazo_libre)
    )
    :effect (and
      (not (sobre_la_mesa ?b))
      (not (despejado ?b))
      (not (brazo_libre))
      (agarrado ?b)
    )
  )
  (:action bajar
    :parameters (?b)
    :precondition (and
      (agarrado ?b)
    )
    :effect (and
      (not (agarrado ?b))
      (sobre_la_mesa ?b)
      (despejado ?b)
      (brazo_libre)
    )
  )
  (:action desapilar
    :parameters (?b1 ?b2)
    :precondition (and
      (sobre ?b1 ?b2)
      (despejado ?b1)
      (brazo_libre)
    )
    :effect (and
      (not (sobre ?b1 ?b2))
      (not (despejado ?b1))
      (not (brazo_libre))
      (agarrado ?b1)
      (despejado ?b2)
    )
  )
  (:action apilar
    :parameters (?b1 ?b2)
    :precondition (and
      (agarrado ?b1)
      (despejado ?b2)
    )
    :effect (and
      (not (agarrado ?b1))
      (not (despejado ?b2))
      (sobre ?b1 ?b2)
      (despejado ?b1)
      (brazo_libre)
    )
  )
)
