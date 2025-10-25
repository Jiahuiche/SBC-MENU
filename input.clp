;; ===========================
;; Módulo input
;; ===========================
(defmodule input
   (export ?ALL) ; exporta todas las reglas, funciones y templates
)

(defrule MAIN::start-input
   =>
   (focus input))

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

(deftemplate input::user-restrictions
   (multislot requested (type SYMBOL) (default-dynamic (create$)))
   (slot max-price (type NUMBER) (default 1000))
   (slot min-price (type NUMBER) (default 0))
   (slot min-servings (type NUMBER) (default 1))
)

(deffunction input::prompt-number (?prompt ?minimum)
   (printout t ?prompt)
   (bind ?value (read))
   (while (or (not (numberp ?value)) (< ?value ?minimum))
      (printout t "Please enter a numeric value greater or equal to " ?minimum "." crlf)
      (printout t ?prompt)
      (bind ?value (read)))
   (return ?value))

;; ===========================
;; Regla principal de entrada de datos
;; ===========================
(defrule input::request-data
   =>
   ;; === Solicitar tipo de evento ===
   (printout t "Event type (wedding/congress/family): ")
   (bind ?type (lowcase (read)))

   ;; === Solicitar estación ===
   (printout t "Season (spring/summer/autumn/winter): ")
   (bind ?season (lowcase (read)))

   ;; Crear hecho del evento
   (assert (event (type ?type) (season ?season)))

   ;; === Solicitar restricciones dietéticas ===
   (printout t "What diet restrictions do you have? (type 'exit' or press Enter to finish)" crlf)

   (bind ?restrictions (create$))
   (bind ?continue TRUE)
   (while ?continue
      (printout t "> ")
      (bind ?raw (readline))
      (bind ?entry (lowcase ?raw))
      (if (or (eq ?entry "exit") (eq ?entry ""))
         then
            (bind ?continue FALSE)
         else
            (bind ?symbol (string-to-field ?entry))
            (if (not (member$ ?symbol ?restrictions)) then
               (bind ?restrictions (create$ ?restrictions ?symbol)))
            (if (not (any-factp ((?f restriction)) (eq ?f:name ?symbol)))
               then (assert (restriction (name ?symbol))))))

   ;; === Solicitar presupuestos ===
   (bind ?min-price (prompt-number "Minimum price per menu (>= 0): " 0))
   (bind ?max-price (prompt-number "Maximum price per menu (>= minimum): " ?min-price))

   ;; === Solicitar porciones mínimas ===
   (bind ?min-servings (round (prompt-number "Minimum servings required (>= 1): " 1)))

   ;; Crear hecho de preferencias del usuario
   (assert (user-restrictions
              (requested ?restrictions)
              (max-price ?max-price)
              (min-price ?min-price)
              (min-servings ?min-servings)))

   (printout t crlf "Data successfully recorded." crlf)
   (focus MATCH)
)
