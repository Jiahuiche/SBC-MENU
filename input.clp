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

(deftemplate input::user-restrictions
   (slot type (type SYMBOL) (default unknown-event))
   (slot season (type SYMBOL) (default any-season))
   (multislot requested (type SYMBOL) (default-dynamic (create$)))
   (slot max-price (type NUMBER) (default 1000))
   (slot min-price (type NUMBER) (default 0))
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
   (bind ?type-token (read))
   (bind ?type-string (if (symbolp ?type-token)
                          then (lowcase (symbol-name ?type-token))
                          else (lowcase ?type-token)))
   (bind ?type (string-to-field ?type-string))

   ;; === Solicitar estación ===
   (printout t "Season (spring/summer/autumn/winter): ")
   (bind ?season-token (read))
   (bind ?season-string (if (symbolp ?season-token)
                            then (lowcase (symbol-name ?season-token))
                            else (lowcase ?season-token)))
   (if (or (eq ?season-string "") (eq ?season-string "any")) then
       (bind ?season-string "any-season"))
   (bind ?season (string-to-field ?season-string))

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

   ;; Crear hecho de preferencias del usuario
   (assert (user-restrictions
             (type ?type)
             (season ?season)
              (requested ?restrictions)
              (max-price ?max-price)
              (min-price ?min-price)))

   (printout t crlf "Data successfully recorded." crlf)
   (focus MATCH)
)
