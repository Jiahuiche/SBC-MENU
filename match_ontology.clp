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

;;; Template para restricciones del usuario
(deftemplate user-restrictions
    (slot is-vegan (type SYMBOL) (allowed-symbols TRUE FALSE) (default FALSE))
    (slot is-vegetarian (type SYMBOL) (allowed-symbols TRUE FALSE) (default FALSE))
    (slot is-gluten-free (type SYMBOL) (allowed-symbols TRUE FALSE) (default FALSE))
    (slot is-dairy-free (type SYMBOL) (allowed-symbols TRUE FALSE) (default FALSE))
    (slot max-price (type NUMBER) (default 10000))
    ;;;(slot min-price (type NUMBER) (default 0))
    (slot min-servings (type NUMBER) (default 1)))

;;; Template para candidatos
(deftemplate candidate-set
    (slot recipe-instance (type INSTANCE))
    (multislot restrictions-met (type SYMBOL))
    (slot restriction-count (type NUMBER) (default 0)))

;;; Control de fases
(deftemplate match-control
    (slot phase (type SYMBOL) (allowed-symbols init single pairs triples complete)))

;;; DATOS DE EJEMPLO: Usuario vegano sin gluten
(deffacts user-example
    (user-restrictions 
        (is-vegan TRUE) 
        (is-gluten-free TRUE) 
        (is-vegetarian FALSE) 
        (is-dairy-free FALSE)
        (max-price 500)
        (min-servings 4)))

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
;;; FASE 1: RESTRICCIONES INDIVIDUALES
;;;----------------------------------------------------------------------------

(defrule start-phase-1
    ?ctrl <- (match-control (phase init))
    =>
    (modify ?ctrl (phase single))
    (printout t crlf "📋 FASE 1: Restricciones individuales" crlf crlf))

;;; VEGAN
(defrule match-vegan
    (match-control (phase single))
    (user-restrictions (is-vegan TRUE) (max-price ?max-p) (min-servings ?min-s))
    ?inst <- (object (is-a Recipe) (title ?title) (price ?price) (servings ?servings) 
                     (restrictions $? vegan $?))
    (test (<= ?price ?max-p))
    (test (>= ?servings ?min-s))
    =>
    (assert (candidate-set (recipe-instance ?inst) (restrictions-met vegan) (restriction-count 1)))
    (printout t "[✓ VEGAN] " ?title crlf))

;;; VEGETARIAN
(defrule match-vegetarian
    (match-control (phase single))
    (user-restrictions (is-vegetarian TRUE) (max-price ?max-p) (min-servings ?min-s))
    ?inst <- (object (is-a Recipe) (title ?title) (price ?price) (servings ?servings)
                     (restrictions $? vegetarian $?))
    (test (<= ?price ?max-p))
    (test (>= ?servings ?min-s))
    =>
    (assert (candidate-set (recipe-instance ?inst) (restrictions-met vegetarian) (restriction-count 1)))
    (printout t "[✓ VEGETARIAN] " ?title crlf))

;;; GLUTEN-FREE
(defrule match-gluten-free
    (match-control (phase single))
    (user-restrictions (is-gluten-free TRUE) (max-price ?max-p) (min-servings ?min-s))
    ?inst <- (object (is-a Recipe) (title ?title) (price ?price) (servings ?servings)
                     (restrictions $? gluten-free $?))
    (test (<= ?price ?max-p))
    (test (>= ?servings ?min-s))
    =>
    (assert (candidate-set (recipe-instance ?inst) (restrictions-met gluten-free) (restriction-count 1)))
    (printout t "[✓ GLUTEN-FREE] " ?title crlf))

;;; DAIRY-FREE
(defrule match-dairy-free
    (match-control (phase single))
    (user-restrictions (is-dairy-free TRUE) (max-price ?max-p) (min-servings ?min-s))
    ?inst <- (object (is-a Recipe) (title ?title) (price ?price) (servings ?servings)
                     (restrictions $? dairy-free $?))
    (test (<= ?price ?max-p))
    (test (>= ?servings ?min-s))
    =>
    (assert (candidate-set (recipe-instance ?inst) (restrictions-met dairy-free) (restriction-count 1)))
    (printout t "[✓ DAIRY-FREE] " ?title crlf))

;;;----------------------------------------------------------------------------
;;; FASE 2: PARES DE RESTRICCIONES
;;;----------------------------------------------------------------------------

(defrule start-phase-2
    ?ctrl <- (match-control (phase single))
    =>
    (modify ?ctrl (phase pairs))
    (printout t crlf "📋 FASE 2: Pares de restricciones" crlf crlf))

;;; VEGAN + GLUTEN-FREE
(defrule match-vegan-gluten-free
    (match-control (phase pairs))
    (user-restrictions (is-vegan TRUE) (is-gluten-free TRUE) (max-price ?max-p) (min-servings ?min-s))
    ?inst <- (object (is-a Recipe) (title ?title) (price ?price) (servings ?servings)
                     (restrictions $? vegan $? gluten-free $?))
    (test (<= ?price ?max-p))
    (test (>= ?servings ?min-s))
    =>
    (assert (candidate-set (recipe-instance ?inst) (restrictions-met vegan gluten-free) (restriction-count 2)))
    (printout t "[✓✓ VEGAN + GLUTEN-FREE] " ?title crlf))

;;; VEGAN + DAIRY-FREE
(defrule match-vegan-dairy-free
    (match-control (phase pairs))
    (user-restrictions (is-vegan TRUE) (is-dairy-free TRUE) (max-price ?max-p) (min-servings ?min-s))
    ?inst <- (object (is-a Recipe) (title ?title) (price ?price) (servings ?servings)
                     (restrictions $? vegan $? dairy-free $?))
    (test (<= ?price ?max-p))
    (test (>= ?servings ?min-s))
    =>
    (assert (candidate-set (recipe-instance ?inst) (restrictions-met vegan dairy-free) (restriction-count 2)))
    (printout t "[✓✓ VEGAN + DAIRY-FREE] " ?title crlf))

;;; VEGETARIAN + GLUTEN-FREE
(defrule match-vegetarian-gluten-free
    (match-control (phase pairs))
    (user-restrictions (is-vegetarian TRUE) (is-gluten-free TRUE) (max-price ?max-p) (min-servings ?min-s))
    ?inst <- (object (is-a Recipe) (title ?title) (price ?price) (servings ?servings)
                     (restrictions $? vegetarian $? gluten-free $?))
    (test (<= ?price ?max-p))
    (test (>= ?servings ?min-s))
    =>
    (assert (candidate-set (recipe-instance ?inst) (restrictions-met vegetarian gluten-free) (restriction-count 2)))
    (printout t "[✓✓ VEGETARIAN + GLUTEN-FREE] " ?title crlf))

;;; VEGETARIAN + DAIRY-FREE
(defrule match-vegetarian-dairy-free
    (match-control (phase pairs))
    (user-restrictions (is-vegetarian TRUE) (is-dairy-free TRUE) (max-price ?max-p) (min-servings ?min-s))
    ?inst <- (object (is-a Recipe) (title ?title) (price ?price) (servings ?servings)
                     (restrictions $? vegetarian $? dairy-free $?))
    (test (<= ?price ?max-p))
    (test (>= ?servings ?min-s))
    =>
    (assert (candidate-set (recipe-instance ?inst) (restrictions-met vegetarian dairy-free) (restriction-count 2)))
    (printout t "[✓✓ VEGETARIAN + DAIRY-FREE] " ?title crlf))

;;; GLUTEN-FREE + DAIRY-FREE
(defrule match-gluten-free-dairy-free
    (match-control (phase pairs))
    (user-restrictions (is-gluten-free TRUE) (is-dairy-free TRUE) (max-price ?max-p) (min-servings ?min-s))
    ?inst <- (object (is-a Recipe) (title ?title) (price ?price) (servings ?servings)
                     (restrictions $? gluten-free $? dairy-free $?))
    (test (<= ?price ?max-p))
    (test (>= ?servings ?min-s))
    =>
    (assert (candidate-set (recipe-instance ?inst) (restrictions-met gluten-free dairy-free) (restriction-count 2)))
    (printout t "[✓✓ GLUTEN-FREE + DAIRY-FREE] " ?title crlf))

;;;----------------------------------------------------------------------------
;;; FASE 3: TRIPLETAS DE RESTRICCIONES
;;;----------------------------------------------------------------------------

(defrule start-phase-3
    ?ctrl <- (match-control (phase pairs))
    =>
    (modify ?ctrl (phase triples))
    (printout t crlf "📋 FASE 3: Tripletas de restricciones" crlf crlf))

;;; VEGAN + GLUTEN-FREE + DAIRY-FREE
(defrule match-vegan-gluten-free-dairy-free
    (match-control (phase triples))
    (user-restrictions (is-vegan TRUE) (is-gluten-free TRUE) (is-dairy-free TRUE) 
                      (max-price ?max-p) (min-servings ?min-s))
    ?inst <- (object (is-a Recipe) (title ?title) (price ?price) (servings ?servings)
                     (restrictions $? vegan $? gluten-free $? dairy-free $?))
    (test (<= ?price ?max-p))
    (test (>= ?servings ?min-s))
    =>
    (assert (candidate-set (recipe-instance ?inst) 
            (restrictions-met vegan gluten-free dairy-free) (restriction-count 3)))
    (printout t "[✓✓✓ VEGAN + GLUTEN-FREE + DAIRY-FREE] " ?title crlf))

;;; VEGETARIAN + GLUTEN-FREE + DAIRY-FREE
(defrule match-vegetarian-gluten-free-dairy-free
    (match-control (phase triples))
    (user-restrictions (is-vegetarian TRUE) (is-gluten-free TRUE) (is-dairy-free TRUE)
                      (max-price ?max-p) (min-servings ?min-s))
    ?inst <- (object (is-a Recipe) (title ?title) (price ?price) (servings ?servings)
                     (restrictions $? vegetarian $? gluten-free $? dairy-free $?))
    (test (<= ?price ?max-p))
    (test (>= ?servings ?min-s))
    =>
    (assert (candidate-set (recipe-instance ?inst) 
            (restrictions-met vegetarian gluten-free dairy-free) (restriction-count 3)))
    (printout t "[✓✓✓ VEGETARIAN + GLUTEN-FREE + DAIRY-FREE] " ?title crlf))

;;;----------------------------------------------------------------------------
;;; FASE 4: TODAS LAS RESTRICCIONES
;;;----------------------------------------------------------------------------

(defrule start-phase-4
    ?ctrl <- (match-control (phase triples))
    =>
    (modify ?ctrl (phase complete))
    (printout t crlf "📋 FASE 4: Todas las restricciones" crlf crlf))

;;; TODAS: VEGAN + VEGETARIAN + GLUTEN-FREE + DAIRY-FREE
(defrule match-all-restrictions
    (match-control (phase complete))
    (user-restrictions (is-vegan TRUE) (is-vegetarian TRUE) 
                      (is-gluten-free TRUE) (is-dairy-free TRUE)
                      (max-price ?max-p) (min-servings ?min-s))
    ?inst <- (object (is-a Recipe) (title ?title) (price ?price) (servings ?servings)
                     (restrictions $? vegan $? vegetarian $? gluten-free $? dairy-free $?))
    (test (<= ?price ?max-p))
    (test (>= ?servings ?min-s))
    =>
    (assert (candidate-set (recipe-instance ?inst) 
            (restrictions-met vegan vegetarian gluten-free dairy-free) (restriction-count 4)))
    (printout t "[✓✓✓✓ TODAS] " ?title crlf))

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
    (bind ?count-1 0)
    (bind ?count-2 0)
    (bind ?count-3 0)
    (bind ?count-4 0)
    
    (do-for-all-facts ((?c candidate-set)) TRUE
        (switch ?c:restriction-count
            (case 1 then (bind ?count-1 (+ ?count-1 1)))
            (case 2 then (bind ?count-2 (+ ?count-2 1)))
            (case 3 then (bind ?count-3 (+ ?count-3 1)))
            (case 4 then (bind ?count-4 (+ ?count-4 1)))))
    
    (printout t crlf "Recetas con 1 restricción: " ?count-1 crlf)
    (printout t "Recetas con 2 restricciones: " ?count-2 crlf)
    (printout t "Recetas con 3 restricciones: " ?count-3 crlf)
    (printout t "Recetas con 4 restricciones: " ?count-4 crlf)
    (printout t "TOTAL de candidatos: " (+ ?count-1 ?count-2 ?count-3 ?count-4) crlf))

(defrule show-best-candidates
    (declare (salience -20))
    (not (match-control))
    =>
    (bind ?max-count 0)
    
    ;; Encontrar máximo nivel de restricciones
    (do-for-all-facts ((?c candidate-set)) TRUE
        (if (> ?c:restriction-count ?max-count) then
            (bind ?max-count ?c:restriction-count)))
    
    (if (> ?max-count 0) then
        (printout t crlf "========================================" crlf)
        (printout t "🏆 MEJORES CANDIDATOS (" ?max-count " restricciones)" crlf)
        (printout t "========================================" crlf)
        
        (do-for-all-facts ((?c candidate-set)) (= ?c:restriction-count ?max-count)
            (bind ?inst ?c:recipe-instance)
            (printout t "• " (send ?inst get-title) crlf)
            (printout t "  Precio: " (send ?inst get-price) " | Porciones: " (send ?inst get-servings) crlf)
            (printout t "  Restricciones: " (implode$ ?c:restrictions-met) crlf crlf))))

(defrule finish-system
    (declare (salience -30))
    (not (match-control))
    =>
    (printout t "========================================" crlf)
    (printout t "✅ SISTEMA FINALIZADO" crlf)
    (printout t "========================================" crlf))

;;;----------------------------------------------------------------------------
;;; FASE 1: RESTRICCIONES INDIVIDUALES
;;;----------------------------------------------------------------------------

(defrule start-phase-1
    ?ctrl <- (match-control (phase init))
    =>
    (modify ?ctrl (phase single))
    (printout t crlf "📋 FASE 1: Restricciones individuales" crlf crlf))

;;; VEGAN
(defrule match-vegan
    (match-control (phase single))
    (user-restrictions (is-vegan TRUE) (max-price ?max-p) (min-servings ?min-s))
    ?inst <- (object (is-a ONTOLOGY::Recipe) (title ?title) (price ?price) (servings ?servings) 
                     (restrictions $? vegan $?))
    (test (<= ?price ?max-p))
    (test (>= ?servings ?min-s))
    =>
    (assert (candidate-set (recipe-instance ?inst) (restrictions-met vegan) (restriction-count 1)))
    (printout t "[✓ VEGAN] " ?title crlf))

;;; VEGETARIAN
(defrule match-vegetarian
    (match-control (phase single))
    (user-restrictions (is-vegetarian TRUE) (max-price ?max-p) (min-servings ?min-s))
    ?inst <- (object (is-a ONTOLOGY::Recipe) (title ?title) (price ?price) (servings ?servings)
                     (restrictions $? vegetarian $?))
    (test (<= ?price ?max-p))
    (test (>= ?servings ?min-s))
    =>
    (assert (candidate-set (recipe-instance ?inst) (restrictions-met vegetarian) (restriction-count 1)))
    (printout t "[✓ VEGETARIAN] " ?title crlf))

;;; GLUTEN-FREE
(defrule match-gluten-free
    (match-control (phase single))
    (user-restrictions (is-gluten-free TRUE) (max-price ?max-p) (min-servings ?min-s))
    ?inst <- (object (is-a ONTOLOGY::Recipe) (title ?title) (price ?price) (servings ?servings)
                     (restrictions $? gluten-free $?))
    (test (<= ?price ?max-p))
    (test (>= ?servings ?min-s))
    =>
    (assert (candidate-set (recipe-instance ?inst) (restrictions-met gluten-free) (restriction-count 1)))
    (printout t "[✓ GLUTEN-FREE] " ?title crlf))

;;; DAIRY-FREE
(defrule match-dairy-free
    (match-control (phase single))
    (user-restrictions (is-dairy-free TRUE) (max-price ?max-p) (min-servings ?min-s))
    ?inst <- (object (is-a ONTOLOGY::Recipe) (title ?title) (price ?price) (servings ?servings)
                     (restrictions $? dairy-free $?))
    (test (<= ?price ?max-p))
    (test (>= ?servings ?min-s))
    =>
    (assert (candidate-set (recipe-instance ?inst) (restrictions-met dairy-free) (restriction-count 1)))
    (printout t "[✓ DAIRY-FREE] " ?title crlf))

;;;----------------------------------------------------------------------------
;;; FASE 2: PARES DE RESTRICCIONES
;;;----------------------------------------------------------------------------

(defrule start-phase-2
    ?ctrl <- (match-control (phase single))
    =>
    (modify ?ctrl (phase pairs))
    (printout t crlf "📋 FASE 2: Pares de restricciones" crlf crlf))

;;; VEGAN + GLUTEN-FREE
(defrule match-vegan-gluten-free
    (match-control (phase pairs))
    (user-restrictions (is-vegan TRUE) (is-gluten-free TRUE) (max-price ?max-p) (min-servings ?min-s))
    ?inst <- (object (is-a ONTOLOGY::Recipe) (title ?title) (price ?price) (servings ?servings)
                     (restrictions $? vegan $? gluten-free $?))
    (test (<= ?price ?max-p))
    (test (>= ?servings ?min-s))
    =>
    (assert (candidate-set (recipe-instance ?inst) (restrictions-met vegan gluten-free) (restriction-count 2)))
    (printout t "[✓✓ VEGAN + GLUTEN-FREE] " ?title crlf))

;;; VEGAN + DAIRY-FREE
(defrule match-vegan-dairy-free
    (match-control (phase pairs))
    (user-restrictions (is-vegan TRUE) (is-dairy-free TRUE) (max-price ?max-p) (min-servings ?min-s))
    ?inst <- (object (is-a ONTOLOGY::Recipe) (title ?title) (price ?price) (servings ?servings)
                     (restrictions $? vegan $? dairy-free $?))
    (test (<= ?price ?max-p))
    (test (>= ?servings ?min-s))
    =>
    (assert (candidate-set (recipe-instance ?inst) (restrictions-met vegan dairy-free) (restriction-count 2)))
    (printout t "[✓✓ VEGAN + DAIRY-FREE] " ?title crlf))

;;; VEGETARIAN + GLUTEN-FREE
(defrule match-vegetarian-gluten-free
    (match-control (phase pairs))
    (user-restrictions (is-vegetarian TRUE) (is-gluten-free TRUE) (max-price ?max-p) (min-servings ?min-s))
    ?inst <- (object (is-a ONTOLOGY::Recipe) (title ?title) (price ?price) (servings ?servings)
                     (restrictions $? vegetarian $? gluten-free $?))
    (test (<= ?price ?max-p))
    (test (>= ?servings ?min-s))
    =>
    (assert (candidate-set (recipe-instance ?inst) (restrictions-met vegetarian gluten-free) (restriction-count 2)))
    (printout t "[✓✓ VEGETARIAN + GLUTEN-FREE] " ?title crlf))

;;; VEGETARIAN + DAIRY-FREE
(defrule match-vegetarian-dairy-free
    (match-control (phase pairs))
    (user-restrictions (is-vegetarian TRUE) (is-dairy-free TRUE) (max-price ?max-p) (min-servings ?min-s))
    ?inst <- (object (is-a ONTOLOGY::Recipe) (title ?title) (price ?price) (servings ?servings)
                     (restrictions $? vegetarian $? dairy-free $?))
    (test (<= ?price ?max-p))
    (test (>= ?servings ?min-s))
    =>
    (assert (candidate-set (recipe-instance ?inst) (restrictions-met vegetarian dairy-free) (restriction-count 2)))
    (printout t "[✓✓ VEGETARIAN + DAIRY-FREE] " ?title crlf))

;;; GLUTEN-FREE + DAIRY-FREE
(defrule match-gluten-free-dairy-free
    (match-control (phase pairs))
    (user-restrictions (is-gluten-free TRUE) (is-dairy-free TRUE) (max-price ?max-p) (min-servings ?min-s))
    ?inst <- (object (is-a ONTOLOGY::Recipe) (title ?title) (price ?price) (servings ?servings)
                     (restrictions $? gluten-free $? dairy-free $?))
    (test (<= ?price ?max-p))
    (test (>= ?servings ?min-s))
    =>
    (assert (candidate-set (recipe-instance ?inst) (restrictions-met gluten-free dairy-free) (restriction-count 2)))
    (printout t "[✓✓ GLUTEN-FREE + DAIRY-FREE] " ?title crlf))

;;;----------------------------------------------------------------------------
;;; FASE 3: TRIPLETAS DE RESTRICCIONES
;;;----------------------------------------------------------------------------

(defrule start-phase-3
    ?ctrl <- (match-control (phase pairs))
    =>
    (modify ?ctrl (phase triples))
    (printout t crlf "📋 FASE 3: Tripletas de restricciones" crlf crlf))

;;; VEGAN + GLUTEN-FREE + DAIRY-FREE
(defrule match-vegan-gluten-free-dairy-free
    (match-control (phase triples))
    (user-restrictions (is-vegan TRUE) (is-gluten-free TRUE) (is-dairy-free TRUE) 
                      (max-price ?max-p) (min-servings ?min-s))
    ?inst <- (object (is-a ONTOLOGY::Recipe) (title ?title) (price ?price) (servings ?servings)
                     (restrictions $? vegan $? gluten-free $? dairy-free $?))
    (test (<= ?price ?max-p))
    (test (>= ?servings ?min-s))
    =>
    (assert (candidate-set (recipe-instance ?inst) 
            (restrictions-met vegan gluten-free dairy-free) (restriction-count 3)))
    (printout t "[✓✓✓ VEGAN + GLUTEN-FREE + DAIRY-FREE] " ?title crlf))

;;; VEGETARIAN + GLUTEN-FREE + DAIRY-FREE
(defrule match-vegetarian-gluten-free-dairy-free
    (match-control (phase triples))
    (user-restrictions (is-vegetarian TRUE) (is-gluten-free TRUE) (is-dairy-free TRUE)
                      (max-price ?max-p) (min-servings ?min-s))
    ?inst <- (object (is-a ONTOLOGY::Recipe) (title ?title) (price ?price) (servings ?servings)
                     (restrictions $? vegetarian $? gluten-free $? dairy-free $?))
    (test (<= ?price ?max-p))
    (test (>= ?servings ?min-s))
    =>
    (assert (candidate-set (recipe-instance ?inst) 
            (restrictions-met vegetarian gluten-free dairy-free) (restriction-count 3)))
    (printout t "[✓✓✓ VEGETARIAN + GLUTEN-FREE + DAIRY-FREE] " ?title crlf))

;;;----------------------------------------------------------------------------
;;; FASE 4: TODAS LAS RESTRICCIONES
;;;----------------------------------------------------------------------------

(defrule start-phase-4
    ?ctrl <- (match-control (phase triples))
    =>
    (modify ?ctrl (phase complete))
    (printout t crlf "📋 FASE 4: Todas las restricciones" crlf crlf))

;;; TODAS: VEGAN + VEGETARIAN + GLUTEN-FREE + DAIRY-FREE
(defrule match-all-restrictions
    (match-control (phase complete))
    (user-restrictions (is-vegan TRUE) (is-vegetarian TRUE) 
                      (is-gluten-free TRUE) (is-dairy-free TRUE)
                      (max-price ?max-p) (min-servings ?min-s))
    ?inst <- (object (is-a ONTOLOGY::Recipe) (title ?title) (price ?price) (servings ?servings)
                     (restrictions $? vegan $? vegetarian $? gluten-free $? dairy-free $?))
    (test (<= ?price ?max-p))
    (test (>= ?servings ?min-s))
    =>
    (assert (candidate-set (recipe-instance ?inst) 
            (restrictions-met vegan vegetarian gluten-free dairy-free) (restriction-count 4)))
    (printout t "[✓✓✓✓ TODAS] " ?title crlf))

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
    (bind ?count-1 0)
    (bind ?count-2 0)
    (bind ?count-3 0)
    (bind ?count-4 0)
    
    (do-for-all-facts ((?c candidate-set)) TRUE
        (switch ?c:restriction-count
            (case 1 then (bind ?count-1 (+ ?count-1 1)))
            (case 2 then (bind ?count-2 (+ ?count-2 1)))
            (case 3 then (bind ?count-3 (+ ?count-3 1)))
            (case 4 then (bind ?count-4 (+ ?count-4 1)))))
    
    (printout t crlf "Recetas con 1 restricción: " ?count-1 crlf)
    (printout t "Recetas con 2 restricciones: " ?count-2 crlf)
    (printout t "Recetas con 3 restricciones: " ?count-3 crlf)
    (printout t "Recetas con 4 restricciones: " ?count-4 crlf)
    (printout t "TOTAL de candidatos: " (+ ?count-1 ?count-2 ?count-3 ?count-4) crlf))

(defrule show-best-candidates
    (declare (salience -20))
    (not (match-control))
    =>
    (bind ?max-count 0)
    
    ;; Encontrar máximo nivel de restricciones
    (do-for-all-facts ((?c candidate-set)) TRUE
        (if (> ?c:restriction-count ?max-count) then
            (bind ?max-count ?c:restriction-count)))
    
    (if (> ?max-count 0) then
        (printout t crlf "========================================" crlf)
        (printout t "🏆 MEJORES CANDIDATOS (" ?max-count " restricciones)" crlf)
        (printout t "========================================" crlf)
        
        (do-for-all-facts ((?c candidate-set)) (= ?c:restriction-count ?max-count)
            (bind ?inst ?c:recipe-instance)
            (printout t "• " (send ?inst get-title) crlf)
            (printout t "  Precio: " (send ?inst get-price) " | Porciones: " (send ?inst get-servings) crlf)
            (printout t "  Restricciones: " (implode$ ?c:restrictions-met) crlf crlf))))

(defrule finish-system
    (declare (salience -30))
    (not (match-control))
    =>
    (printout t "========================================" crlf)
    (printout t "✅ SISTEMA FINALIZADO" crlf)
    (printout t "========================================" crlf))
