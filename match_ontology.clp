;;;============================================================================
;;; SISTEMA DE MATCHING INCREMENTAL DE RECETAS CON ONTOLOGÍA
;;; Trabaja con instancias de ONTOLOGY::Recipe
;;; Autor: Sistema experto en CLIPS
;;; Fecha: Octubre 2025
;;;============================================================================
;;; IMPORTANTE: Cargar en este orden:
;;; 1. (load "onto.clp")
;;; 2. (load "recipes_clips.clp")
;;; 3. (load "input.clp")
;;; 4. (load "match_ontology.clp")
;;; 5. (reset)
;;; 6. (run)
;;;============================================================================

(defmodule MATCH
    (import ONTOLOGY ?ALL)
    (import DATA ?ALL)
    (import input ?ALL)
    (export ?ALL))

;;; Template para candidatos
(deftemplate MATCH::candidate-set
    (slot recipe-instance (type INSTANCE))
    (multislot restrictions-met (type SYMBOL))
    (slot restriction-count (type NUMBER) (default 0)))

(deftemplate MATCH::match-control
    (slot phase (type SYMBOL) (allowed-symbols init complete)))

;;;------------------------------------------------------------------------
;;; Funciones auxiliares
;;;------------------------------------------------------------------------

(deffunction MATCH::passes-thresholds (?recipe ?min-price ?max-price ?preferred-season)
    "Verifica umbrales de precio y estación preferida"
    (bind ?price (send ?recipe get-price))
    (if (< ?price ?min-price) then (return FALSE))
    (if (> ?price ?max-price) then (return FALSE))
    (bind ?recipe-season (send ?recipe get-seasons))
    (if (and (neq ?preferred-season any-season) (neq ?preferred-season ?recipe-season)) then
        (return FALSE))
    (return TRUE))

(deffunction MATCH::matched-restrictions (?requested ?recipe)
    "Devuelve las restricciones solicitadas que la receta cumple"
    (bind ?result (create$))
    (bind ?available (send ?recipe get-restrictions))
    (loop-for-count (?i 1 (length$ ?requested))
        (bind ?item (nth$ ?i ?requested))
        (if (member$ ?item ?available) then
            (bind ?result (create$ ?result ?item))))
    (return ?result))

(deffunction MATCH::emit-subsets (?remaining ?current ?recipe)
    "Genera todas las combinaciones no vacías de ?remaining, acumulando en ?current"
    (bind ?total 0)
    (if (> (length$ ?remaining) 0) then
        (bind ?first (nth$ 1 ?remaining))
        (bind ?rest (rest$ ?remaining))
        (bind ?with-first (create$ ?current ?first))
        (assert (candidate-set
                    (recipe-instance ?recipe)
                    (restrictions-met ?with-first)
                    (restriction-count (length$ ?with-first))))
        (bind ?total (+ ?total 1))
        (bind ?total (+ ?total (emit-subsets ?rest ?with-first ?recipe)))
        (bind ?total (+ ?total (emit-subsets ?rest ?current ?recipe))))
    (return ?total))

(deffunction MATCH::generate-candidates-for-recipe (?recipe ?requested ?min-price ?max-price ?preferred-season)
    "Genera candidatos para una receta específica y devuelve cuántos se crearon"
    (if (not (passes-thresholds ?recipe ?min-price ?max-price ?preferred-season)) then
        (return 0))

    (bind ?requested-count (length$ ?requested))
    (if (= ?requested-count 0) then
        (assert (candidate-set
                    (recipe-instance ?recipe)
                    (restrictions-met (create$))
                    (restriction-count 0)))
        (return 1))

    (bind ?matched (matched-restrictions ?requested ?recipe))
    (if (> (length$ ?matched) 0) then
        (return (emit-subsets ?matched (create$) ?recipe))
     else
        (return 0)))

;;;----------------------------------------------------------------------------
;;; INICIALIZACIÓN
;;;----------------------------------------------------------------------------

(defrule MATCH::init-system
    (declare (salience 100))
    =>
    (printout t "========================================" crlf)
    (printout t "🔍 SISTEMA DE MATCHING DE RECETAS" crlf)
    (printout t "========================================" crlf)
    (assert (match-control (phase init))))

;;;----------------------------------------------------------------------------
;;; GENERACIÓN DINÁMICA DE CANDIDATOS
;;;----------------------------------------------------------------------------

(defrule MATCH::build-candidates
    ?ctrl <- (match-control (phase init))
    ?prefs <- (user-restrictions (min-price ?min-p) (max-price ?max-p) (season ?season-pref))
    =>
    (do-for-all-facts ((?c candidate-set)) TRUE (retract ?c))
    (bind ?requested (fact-slot-value ?prefs requested))
    (bind ?recipes (find-all-instances ((?recipe ONTOLOGY::Recipe)) TRUE))
    (bind ?combo-count 0)
    (foreach ?recipe ?recipes
        (bind ?combo-count
            (+ ?combo-count
               (generate-candidates-for-recipe
                    ?recipe
                    ?requested
                    ?min-p
                    ?max-p
                    ?season-pref))))
    (retract ?ctrl)
    (assert (match-control (phase complete)))
    (printout t crlf "📋 Evaluadas combinaciones de restricciones: " ?combo-count crlf))


;;;----------------------------------------------------------------------------
;;; REFINAMIENTO Y ESTADÍSTICAS
;;;----------------------------------------------------------------------------

(defrule MATCH::finish-matching
    ?ctrl <- (match-control (phase complete))
    =>
    (retract ?ctrl)
    (printout t crlf "========================================" crlf)
    (printout t "📊 ESTADÍSTICAS DE CANDIDATOS" crlf)
    (printout t "========================================" crlf))

(defrule MATCH::show-statistics
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

(defrule MATCH::show-best-candidates
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
            (printout t "  Precio: " (send ?inst get-price) crlf)
            (printout t "  Restricciones: "
                        (if (= ?max-count 0) then "sin requisitos" else (implode$ ?c:restrictions-met))
                        crlf crlf))))

(defrule MATCH::finish-system
    (declare (salience -30))
    (not (match-control))
    =>
    (printout t "========================================" crlf)
    (printout t "✅ SISTEMA FINALIZADO" crlf)
    (printout t "========================================" crlf))
