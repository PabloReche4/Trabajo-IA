(define
  (problem variante_1_cruz_inglesa)
  (:domain senku)
  (:objects
    p_0_2
    p_0_3
    p_0_4
    p_1_2
    p_1_3
    p_1_4
    p_2_0
    p_2_1
    p_2_2
    p_2_3
    p_2_4
    p_2_5
    p_2_6
    p_3_0
    p_3_1
    p_3_2
    p_3_3
    p_3_4
    p_3_5
    p_3_6
    p_4_0
    p_4_1
    p_4_2
    p_4_3
    p_4_4
    p_4_5
    p_4_6
    p_5_2
    p_5_3
    p_5_4
    p_6_2
    p_6_3
    p_6_4
  )
  (:init
    (ocupada p_0_2)
    (ocupada p_0_3)
    (ocupada p_0_4)
    (ocupada p_1_2)
    (ocupada p_1_3)
    (ocupada p_1_4)
    (ocupada p_2_0)
    (ocupada p_2_1)
    (ocupada p_2_2)
    (ocupada p_2_3)
    (ocupada p_2_4)
    (ocupada p_2_5)
    (ocupada p_2_6)
    (ocupada p_3_0)
    (ocupada p_3_1)
    (ocupada p_3_2)
    (ocupada p_3_4)
    (ocupada p_3_5)
    (ocupada p_3_6)
    (ocupada p_4_0)
    (ocupada p_4_1)
    (ocupada p_4_2)
    (ocupada p_4_3)
    (ocupada p_4_4)
    (ocupada p_4_5)
    (ocupada p_4_6)
    (ocupada p_5_2)
    (ocupada p_5_3)
    (ocupada p_5_4)
    (ocupada p_6_2)
    (ocupada p_6_3)
    (ocupada p_6_4)
    (vacia p_3_3)
    (salto p_4_0 p_4_1 p_4_2)
    (salto p_4_0 p_3_0 p_2_0)
    (salto p_3_4 p_3_5 p_3_6)
    (salto p_3_4 p_3_3 p_3_2)
    (salto p_3_4 p_4_4 p_5_4)
    (salto p_3_4 p_2_4 p_1_4)
    (salto p_4_3 p_4_4 p_4_5)
    (salto p_4_3 p_4_2 p_4_1)
    (salto p_4_3 p_5_3 p_6_3)
    (salto p_4_3 p_3_3 p_2_3)
    (salto p_3_1 p_3_2 p_3_3)
    (salto p_5_4 p_5_3 p_5_2)
    (salto p_5_4 p_4_4 p_3_4)
    (salto p_4_6 p_4_5 p_4_4)
    (salto p_4_6 p_3_6 p_2_6)
    (salto p_0_2 p_0_3 p_0_4)
    (salto p_0_2 p_1_2 p_2_2)
    (salto p_2_2 p_2_3 p_2_4)
    (salto p_2_2 p_2_1 p_2_0)
    (salto p_2_2 p_3_2 p_4_2)
    (salto p_2_2 p_1_2 p_0_2)
    (salto p_2_5 p_2_4 p_2_3)
    (salto p_2_5 p_3_5 p_4_5)
    (salto p_1_3 p_2_3 p_3_3)
    (salto p_6_2 p_6_3 p_6_4)
    (salto p_6_2 p_5_2 p_4_2)
    (salto p_4_2 p_4_3 p_4_4)
    (salto p_4_2 p_4_1 p_4_0)
    (salto p_4_2 p_5_2 p_6_2)
    (salto p_4_2 p_3_2 p_2_2)
    (salto p_3_0 p_3_1 p_3_2)
    (salto p_4_5 p_4_4 p_4_3)
    (salto p_4_5 p_3_5 p_2_5)
    (salto p_3_3 p_3_4 p_3_5)
    (salto p_3_3 p_3_2 p_3_1)
    (salto p_3_3 p_4_3 p_5_3)
    (salto p_3_3 p_2_3 p_1_3)
    (salto p_3_6 p_3_5 p_3_4)
    (salto p_5_3 p_4_3 p_3_3)
    (salto p_2_4 p_2_5 p_2_6)
    (salto p_2_4 p_2_3 p_2_2)
    (salto p_2_4 p_3_4 p_4_4)
    (salto p_2_4 p_1_4 p_0_4)
    (salto p_1_2 p_1_3 p_1_4)
    (salto p_1_2 p_2_2 p_3_2)
    (salto p_0_4 p_0_3 p_0_2)
    (salto p_0_4 p_1_4 p_2_4)
    (salto p_2_1 p_2_2 p_2_3)
    (salto p_2_1 p_3_1 p_4_1)
    (salto p_6_4 p_6_3 p_6_2)
    (salto p_6_4 p_5_4 p_4_4)
    (salto p_3_2 p_3_3 p_3_4)
    (salto p_3_2 p_3_1 p_3_0)
    (salto p_3_2 p_4_2 p_5_2)
    (salto p_3_2 p_2_2 p_1_2)
    (salto p_4_1 p_4_2 p_4_3)
    (salto p_4_1 p_3_1 p_2_1)
    (salto p_3_5 p_3_4 p_3_3)
    (salto p_5_2 p_5_3 p_5_4)
    (salto p_5_2 p_4_2 p_3_2)
    (salto p_4_4 p_4_5 p_4_6)
    (salto p_4_4 p_4_3 p_4_2)
    (salto p_4_4 p_5_4 p_6_4)
    (salto p_4_4 p_3_4 p_2_4)
    (salto p_0_3 p_1_3 p_2_3)
    (salto p_2_0 p_2_1 p_2_2)
    (salto p_2_0 p_3_0 p_4_0)
    (salto p_1_4 p_1_3 p_1_2)
    (salto p_1_4 p_2_4 p_3_4)
    (salto p_2_3 p_2_4 p_2_5)
    (salto p_2_3 p_2_2 p_2_1)
    (salto p_2_3 p_3_3 p_4_3)
    (salto p_2_3 p_1_3 p_0_3)
    (salto p_2_6 p_2_5 p_2_4)
    (salto p_2_6 p_3_6 p_4_6)
    (salto p_6_3 p_5_3 p_4_3)
  )
  (:goal (and
      (ocupada p_3_3)
      (vacia p_0_2)
      (vacia p_0_3)
      (vacia p_0_4)
      (vacia p_1_2)
      (vacia p_1_3)
      (vacia p_1_4)
      (vacia p_2_0)
      (vacia p_2_1)
      (vacia p_2_2)
      (vacia p_2_3)
      (vacia p_2_4)
      (vacia p_2_5)
      (vacia p_2_6)
      (vacia p_3_0)
      (vacia p_3_1)
      (vacia p_3_2)
      (vacia p_3_4)
      (vacia p_3_5)
      (vacia p_3_6)
      (vacia p_4_0)
      (vacia p_4_1)
      (vacia p_4_2)
      (vacia p_4_3)
      (vacia p_4_4)
      (vacia p_4_5)
      (vacia p_4_6)
      (vacia p_5_2)
      (vacia p_5_3)
      (vacia p_5_4)
      (vacia p_6_2)
      (vacia p_6_3)
      (vacia p_6_4)
    )
  )
)
