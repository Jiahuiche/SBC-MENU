(defrule pedir-datos
  (initial-fact)
  =>
  (printout t "Tipo de evento (boda/congreso): ")
  (bind ?tipo (read))
  (printout)
  (printout t "Presupuesto máximo por persona: ")
  (bind ?presu (read))
  (printout t "Restricciones: ")
  (bind ?lista (explode$ (readline)))



)

(defrule mostrar
  (Pedido (tipo_evento ?t) (presupuesto ?p))
  =>
  (printout t "Has creado un pedido de tipo " ?t " con presupuesto " ?p "€" crlf))
