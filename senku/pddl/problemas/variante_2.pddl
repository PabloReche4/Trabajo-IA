(define
  (problem variante_2_cuadrado_5x5)
  (:domain senku)
  (:objects
    p_0_0
    p_0_1
    p_0_2
    p_0_3
    p_0_4
    p_1_0
    p_1_1
    p_1_2
    p_1_3
    p_1_4
    p_2_0
    p_2_1
    p_2_2
    p_2_3
    p_2_4
    p_3_0
    p_3_1
    p_3_2
    p_3_3
    p_3_4
    p_4_0
    p_4_1
    p_4_2
    p_4_3
    p_4_4
  )
  (:init
    (ocupada p_0_0)
    (ocupada p_0_1)
    (ocupada p_0_2)
    (ocupada p_0_3)
    (ocupada p_0_4)
    (ocupada p_1_0)
    (ocupada p_1_1)
    (ocupada p_1_2)
    (ocupada p_1_3)
    (ocupada p_1_4)
    (ocupada p_2_0)
    (ocupada p_2_1)
    (ocupada p_2_3)
    (ocupada p_2_4)
    (ocupada p_3_0)
    (ocupada p_3_1)
    (ocupada p_3_2)
    (ocupada p_3_3)
    (ocupada p_3_4)
    (ocupada p_4_0)
    (ocupada p_4_1)
    (ocupada p_4_2)
    (ocupada p_4_3)
    (ocupada p_4_4)
    (vacia p_2_2)
    (salto p_0_1 p_0_2 p_0_3)
    (salto p_0_1 p_1_1 p_2_1)
    (salto p_2_4 p_2_3 p_2_2)
    (salto p_2_4 p_3_4 p_4_4)
    (salto p_2_4 p_1_4 p_0_4)
    (salto p_4_0 p_4_1 p_4_2)
    (salto p_4_0 p_3_0 p_2_0)
    (salto p_1_2 p_1_3 p_1_4)
    (salto p_1_2 p_1_1 p_1_0)
    (salto p_1_2 p_2_2 p_3_2)
    (salto p_3_4 p_3_3 p_3_2)
    (salto p_3_4 p_2_4 p_1_4)
    (salto p_0_4 p_0_3 p_0_2)
    (salto p_0_4 p_1_4 p_2_4)
    (salto p_4_3 p_4_2 p_4_1)
    (salto p_4_3 p_3_3 p_2_3)
    (salto p_3_1 p_3_2 p_3_3)
    (salto p_3_1 p_2_1 p_1_1)
    (salto p_2_1 p_2_2 p_2_3)
    (salto p_2_1 p_3_1 p_4_1)
    (salto p_2_1 p_1_1 p_0_1)
    (salto p_0_2 p_0_3 p_0_4)
    (salto p_0_2 p_0_1 p_0_0)
    (salto p_0_2 p_1_2 p_2_2)
    (salto p_2_2 p_2_3 p_2_4)
    (salto p_2_2 p_2_1 p_2_0)
    (salto p_2_2 p_3_2 p_4_2)
    (salto p_2_2 p_1_2 p_0_2)
    (salto p_1_0 p_1_1 p_1_2)
    (salto p_1_0 p_2_0 p_3_0)
    (salto p_3_2 p_3_3 p_3_4)
    (salto p_3_2 p_3_1 p_3_0)
    (salto p_3_2 p_2_2 p_1_2)
    (salto p_1_3 p_1_2 p_1_1)
    (salto p_1_3 p_2_3 p_3_3)
    (salto p_4_1 p_4_2 p_4_3)
    (salto p_4_1 p_3_1 p_2_1)
    (salto p_4_4 p_4_3 p_4_2)
    (salto p_4_4 p_3_4 p_2_4)
    (salto p_0_0 p_0_1 p_0_2)
    (salto p_0_0 p_1_0 p_2_0)
    (salto p_1_1 p_1_2 p_1_3)
    (salto p_1_1 p_2_1 p_3_1)
    (salto p_0_3 p_0_2 p_0_1)
    (salto p_0_3 p_1_3 p_2_3)
    (salto p_2_0 p_2_1 p_2_2)
    (salto p_2_0 p_3_0 p_4_0)
    (salto p_2_0 p_1_0 p_0_0)
    (salto p_4_2 p_4_3 p_4_4)
    (salto p_4_2 p_4_1 p_4_0)
    (salto p_4_2 p_3_2 p_2_2)
    (salto p_3_0 p_3_1 p_3_2)
    (salto p_3_0 p_2_0 p_1_0)
    (salto p_1_4 p_1_3 p_1_2)
    (salto p_1_4 p_2_4 p_3_4)
    (salto p_2_3 p_2_2 p_2_1)
    (salto p_2_3 p_3_3 p_4_3)
    (salto p_2_3 p_1_3 p_0_3)
    (salto p_3_3 p_3_2 p_3_1)
    (salto p_3_3 p_2_3 p_1_3)
  )
  (:goal (and
      (ocupada p_2_2)
      (vacia p_0_0)
      (vacia p_0_1)
      (vacia p_0_2)
      (vacia p_0_3)
      (vacia p_0_4)
      (vacia p_1_0)
      (vacia p_1_1)
      (vacia p_1_2)
      (vacia p_1_3)
      (vacia p_1_4)
      (vacia p_2_0)
      (vacia p_2_1)
      (vacia p_2_3)
      (vacia p_2_4)
      (vacia p_3_0)
      (vacia p_3_1)
      (vacia p_3_2)
      (vacia p_3_3)
      (vacia p_3_4)
      (vacia p_4_0)
      (vacia p_4_1)
      (vacia p_4_2)
      (vacia p_4_3)
      (vacia p_4_4)
    )
  )
)
