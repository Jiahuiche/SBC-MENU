;;;============================================================================
;;; SISTEMA DE MATCHING INCREMENTAL DE RECETAS CON ONTOLOGÍA
;;; Trabaja con instancias de ONTOLOGY::Recipe
;;; Autor: Sistema experto en CLIPS
;;; Fecha: Octubre 2025
;;;============================================================================
;;; IMPORTANTE: Cargar en este orden:
;;; 1. (load "onto.clp")
;;; 2. (load "recipes_clips.clp")
;;; 3. (load "match_ontology.clp")
;;; 4. (reset)
;;; 5. (run)
;;;============================================================================

(defmodule MATCH
    (import ONTOLOGY ?ALL)
    (import DATA ?ALL))

(in-module MATCH)

;;; Template para restricciones del usuario
(deftemplate user-restrictions
    (multislot requested (type SYMBOL) (default-dynamic (create$)))
    (slot max-price (type NUMBER) (default 10000))
    (slot min-servings (type NUMBER) (default 1)))

;;; Template para candidatos
(deftemplate candidate-set
    (slot recipe-instance (type INSTANCE))
    (multislot restrictions-met (type SYMBOL))
    (slot restriction-count (type NUMBER) (default 0)))

;;; Control de fases
(deftemplate match-control
    (slot phase (type SYMBOL) (allowed-symbols init complete)))

;;; DATOS DE EJEMPLO: Usuario vegano sin gluten
(deffacts user-example  
    (user-restrictions 
        (requested vegan gluten-free)
        (max-price 500)
        (min-servings 4)))

;;;------------------------------------------------------------------------
;;; Funciones auxiliares (adaptadas de combinatoria.clp)
;;;------------------------------------------------------------------------

(deffunction combinaciones (?lista)
    "Combinaciones de tamaño >= 2 a partir de una lista"
    (if (<= (length$ ?lista) 1) then
        (return (create$)))
    (bind ?primero (nth$ 1 ?lista))
    (bind ?resto (rest$ ?lista))
    (bind ?subcombs (combinaciones ?resto))
    (bind ?resultado ?subcombs)
    (foreach ?c ?subcombs
        (bind ?resultado (create$ ?resultado (create$ ?primero ?c))))
    (loop-for-count (?i 1 (length$ ?resto))
        (bind ?elem (nth$ ?i ?resto))
        (bind ?resultado (create$ ?resultado (create$ ?primero ?elem))))
    (return ?resultado))

(deffunction all-restriction-combinations (?reqs)
    "Devuelve todas las combinaciones desde 1 hasta N restricciones"
    (bind ?total (length$ ?reqs))
    (if (= ?total 0) then
        (return (create$ (create$))))
    (bind ?resultado (create$))
    (loop-for-count (?i 1 ?total)
        (bind ?resultado (create$ ?resultado (create$ (nth$ ?i ?reqs)))))
    (bind ?resultado (create$ ?resultado (combinaciones ?reqs)))
    (return ?resultado))

(deffunction recipe-satisfies (?recipe ?combo ?max-price ?min-servings)
    "Comprueba si una receta cumple la combinación y los umbrales"
    (bind ?price (send ?recipe get-price))
    (if (> ?price ?max-price) then (return FALSE))
    (bind ?servings (send ?recipe get-servings))
    (if (< ?servings ?min-servings) then (return FALSE))
    (bind ?restrictions (send ?recipe get-restrictions))
    (loop-for-count (?i 1 (length$ ?combo))
        (bind ?needed (nth$ ?i ?combo))
        (if (not (member$ ?needed ?restrictions)) then (return FALSE)))
    (return TRUE))

;;;----------------------------------------------------------------------------
;;; INICIALIZACIÓN
;;;----------------------------------------------------------------------------

(defrule init-system
    (declare (salience 100))
    =>
    (printout t "========================================" crlf)
    (printout t "🔍 SISTEMA DE MATCHING DE RECETAS" crlf)
    (printout t "========================================" crlf)
    (assert (match-control (phase init))))

;;;----------------------------------------------------------------------------
;;; GENERACIÓN DINÁMICA DE CANDIDATOS
;;;----------------------------------------------------------------------------

(defrule build-candidates
    ?ctrl <- (match-control (phase init))
    ?prefs <- (user-restrictions (max-price ?max-p) (min-servings ?min-s))
    =>
    (do-for-all-facts ((?c candidate-set)) TRUE (retract ?c))
    (bind ?requested (fact-slot-value ?prefs requested))
    (bind ?combos (all-restriction-combinations ?requested))
    (bind ?combo-count 0)
    (foreach ?combo ?combos
        (bind ?combo-count (+ ?combo-count 1))
        (do-for-all-instances ((?recipe ONTOLOGY::Recipe)) TRUE
            (if (recipe-satisfies ?recipe ?combo ?max-p ?min-s) then
                (assert (candidate-set
                            (recipe-instance ?recipe)
                            (restrictions-met (expand$ ?combo))
                            (restriction-count (length$ ?combo)))))))
    (retract ?ctrl)
    (assert (match-control (phase complete)))
    (printout t crlf "📋 Evaluadas combinaciones de restricciones: " ?combo-count crlf))

;;;----------------------------------------------------------------------------
;;; REFINAMIENTO Y ESTADÍSTICAS
;;;----------------------------------------------------------------------------

(defrule finish-matching
    ?ctrl <- (match-control (phase complete))
    =>
    (retract ?ctrl)
    (printout t crlf "========================================" crlf)
    (printout t "📊 ESTADÍSTICAS DE CANDIDATOS" crlf)
    (printout t "========================================" crlf))

(defrule show-statistics
    (declare (salience -10))
    (not (match-control))
    =>
    (bind ?count-0 0)
    (bind ?count-1 0)
    (bind ?count-2 0)
    (bind ?count-3 0)
    (bind ?count-4 0)
    
    (do-for-all-facts ((?c candidate-set)) TRUE
        (switch ?c:restriction-count
            (case 0 then (bind ?count-0 (+ ?count-0 1)))
            (case 1 then (bind ?count-1 (+ ?count-1 1)))
            (case 2 then (bind ?count-2 (+ ?count-2 1)))
            (case 3 then (bind ?count-3 (+ ?count-3 1)))
            (case 4 then (bind ?count-4 (+ ?count-4 1)))))
    
    (printout t crlf "Recetas con 0 restricciones: " ?count-0 crlf)
    (printout t "Recetas con 1 restricción: " ?count-1 crlf)
    (printout t "Recetas con 2 restricciones: " ?count-2 crlf)
    (printout t "Recetas con 3 restricciones: " ?count-3 crlf)
    (printout t "Recetas con 4 restricciones: " ?count-4 crlf)
    (printout t "TOTAL de candidatos: " (+ ?count-0 ?count-1 ?count-2 ?count-3 ?count-4) crlf))

(defrule show-best-candidates
    (declare (salience -20))
    (not (match-control))
    =>
    (bind ?max-count -1)
    
    ;; Encontrar máximo nivel de restricciones
    (do-for-all-facts ((?c candidate-set)) TRUE
        (if (> ?c:restriction-count ?max-count) then
            (bind ?max-count ?c:restriction-count)))
    
    (if (>= ?max-count 0) then
        (printout t crlf "========================================" crlf)
        (printout t "🏆 MEJORES CANDIDATOS (" ?max-count " restricciones)" crlf)
        (printout t "========================================" crlf)
        
        (do-for-all-facts ((?c candidate-set)) (= ?c:restriction-count ?max-count)
            (bind ?inst ?c:recipe-instance)
            (printout t "• " (send ?inst get-title) crlf)
            (printout t "  Precio: " (send ?inst get-price) " | Porciones: " (send ?inst get-servings) crlf)
            (printout t "  Restricciones: "
                        (if (= ?max-count 0) then "sin requisitos" else (implode$ ?c:restrictions-met))
                        crlf crlf))))

(defrule finish-system
    (declare (salience -30))
    (not (match-control))
    =>
    (printout t "========================================" crlf)
    (printout t "✅ SISTEMA FINALIZADO" crlf)
    (printout t "========================================" crlf))
