;; ===========================
;; Módulo input
;; ===========================
(defmodule input
   (export ?ALL) ; exporta todas las reglas y globals si hubiera
)

;; ===========================
;; Plantillas (estructuras de hechos)
;; ===========================
(deftemplate input::restriction
   (slot name)
   ;;(slot num_people)
)

(deftemplate input::event
   (slot type)
   (slot season)
)

;; ===========================
;; Regla principal de entrada de datos
;; ===========================
(defrule input::request-data
   =>
   ;; === Solicitar tipo de evento ===
   (printout t "Event type (wedding/congress/family): ")
   (bind ?type (string-to-field (readline)))

   ;; === Solicitar estación ===
   (printout t "Season (spring/summer/autumn/winter): ")
   (bind ?season (string-to-field (readline)))

   ;; Crear hecho del evento
   (assert (event (type ?type) (season ?season)))

   ;; === Solicitar restricciones dietéticas ===
   (printout t "What diet restrictions do you have? (type 'exit' or press Enter to finish)" crlf)

   (bind ?r "NONE")
   (while (and (neq ?r "exit") (neq ?r ""))
      (printout t "> ")
      (bind ?r (readline))
      (if (and (neq ?r "exit") (neq ?r ""))
          then
             (if (not (any-factp ((?f restriction)) (eq ?f:name ?r)))
                 then (assert (restriction (name ?r))))))
   (printout t crlf "Data successfully recorded." crlf)
)
