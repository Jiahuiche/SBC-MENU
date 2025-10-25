;; ===========================
;; Módulo match
;; ===========================
(defmodule match
   (import input ?ALL)
   (export ?ALL)
)

;; ============================================
;; Template para definir platos de comida
;; ============================================
(deftemplate match::plato
   (slot nombre)
   (multislot cumple)
)

;; ============================================
;; Función recursiva para generar todas las combinaciones posibles de una lista
;; ============================================
(deffunction match::combinate (?lista)
   (bind ?n (length$ ?lista))
   (bind ?resultado (create$))

   (if (<= ?n 0) then
      (return (create$))
   )

   ;; Añadimos combinaciones de 1 elemento
   (loop-for-count (?i 1 ?n)
      (bind ?resultado (create$ ?resultado (str-cat (nth$ ?i ?lista))))
   )

   ;; Generar combinaciones de 2 o más elementos
   (loop-for-count (?i 1 (- ?n 1))
      (bind ?resto (subseq$ ?lista (+ ?i 1) ?n))
      (bind ?subcombs (combinate ?resto))

      ;; Combinaciones de 2 elementos
      (foreach ?r ?resto
         (bind ?comb (str-cat (nth$ ?i ?lista) " " ?r))
         (bind ?resultado (create$ ?resultado ?comb))
      )

      ;; Combinaciones más grandes
      (foreach ?c ?subcombs
         (bind ?comb (str-cat (nth$ ?i ?lista) " " ?c))
         (bind ?resultado (create$ ?resultado ?comb))
      )
   )

   (return ?resultado)
)

;; ============================================
;; Función que comprueba si un plato cumple todas las restricciones
;; ============================================
(deffunction match::cumple-todas (?plato ?restricciones)
   (bind ?cumple (fact-slot-value ?plato cumple))

   (loop-for-count (?i 1 (length$ ?restricciones))
      (if (not (member$ (nth$ ?i ?restricciones) ?cumple)) then
         (return FALSE)
      )
   )
   (return TRUE)
)

;; ============================================
;; Función que comprueba si algún plato cumple una combinación
;; ============================================
(deffunction match::algun-plato-cumple (?combinacion)
   (bind ?ok FALSE)
   (do-for-all-facts ((?p plato)) TRUE
      (if (cumple-todas ?p ?combinacion) then
         (bind ?ok TRUE)
      )
   )
   (return ?ok)
)

;; ============================================ 
;; Regla principal que actúa como "main"
;; ============================================
(defrule match::main
   (not (main-end))
   =>
   ;; Platos y las restricciones que cumplen
   (assert (plato (nombre ensalada) (cumple vegetariano sin-gluten)))
   (assert (plato (nombre hamburguesa) (cumple sin-gluten)))
   (assert (plato (nombre tofu) (cumple vegano vegetariano sin-gluten)))
   (assert (plato (nombre sopa) (cumple vegetariano diabetico)))

   (printout t "===== EJECUTANDO PROGRAMA =====" crlf)

   ;; Obtener restricciones del módulo input
   (bind ?list-restrictions (create$))
   (do-for-all-facts ((?r restriction)) TRUE 
      (bind ?list-restrictions (create$ ?list-restrictions ?r:name))
   )

   ;; Generar combinaciones
   (bind ?combs (combinate ?list-restrictions))

   ;; Recorremos las combinaciones
   (foreach ?c ?combs
      (bind ?restricciones (explode$ ?c))  ;; separa por espacios
      (bind ?platos-validos (create$))

      ;; Recorremos todos los platos y añadimos los que cumplen todas las restricciones
      (do-for-all-facts ((?p plato)) TRUE
         (if (cumple-todas ?p ?restricciones) then
            (bind ?platos-validos (create$ ?platos-validos ?p))
         )
      )

      ;; Imprimimos la combinación y los platos válidos
      (if (> (length$ ?platos-validos) 0) then
         (printout t "Platos válidos para: " ?c crlf)
         (foreach ?p ?platos-validos
            (printout t "  Plato: " (fact-slot-value ?p nombre)
                     ", restricciones: " (fact-slot-value ?p cumple) crlf)
         )
      else
         (printout t "No hay plato que cumpla: " ?c crlf)
      )
   )

   ;; Evitar que se vuelva a ejecutar
   (assert (main-end))
)
