(define
  (problem problema_mundo_bloques)
  (:domain dominio_mundo_bloques)
  (:objects
    A B C
  )
  (:init
    (sobre A C)
    (sobre_la_mesa B)
    (sobre_la_mesa C)
    (despejado A)
    (despejado B)
    (brazo_libre)
  )
  (:goal (and
      (sobre_la_mesa A)
      (sobre B A)
      (sobre C B)
    )
  )
)