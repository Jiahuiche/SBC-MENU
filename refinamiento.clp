(defmodule REFINAMIENTO (import ONTOLOGY ?ALL) 
                        (import MATCH ?ALL ) ;hacer module match 
                        (import DATA ?ALL)
                        (import input ?ALL) (export ?ALL))

(defrule MAIN::auto-focus-refinamiento
    =>
    (focus REFINAMIENTO))

(deftemplate REFINAMIENTO::menu
    (slot categoria (type SYMBOL)) ;;; barato, medio, caro
   (slot entrante (type INSTANCE))
   (slot principal (type INSTANCE))
   (slot postre (type INSTANCE))
   (slot precio-total (type FLOAT)))

;; Template para restricciones del usuario
; (deftemplate REFINAMIENTO::user-restrictions
;     (slot is-vegan (type SYMBOL) (allowed-symbols TRUE FALSE) (default FALSE))
;     (slot is-vegetarian (type SYMBOL) (allowed-symbols TRUE FALSE) (default FALSE))
;     (slot is-gluten-free (type SYMBOL) (allowed-symbols TRUE FALSE) (default FALSE))
;     (slot is-dairy-free (type SYMBOL) (allowed-symbols TRUE FALSE) (default FALSE))
;     (slot max-price (type NUMBER) (default 10000))
;     (slot min-price (type NUMBER) (default 0))
;     (slot min-servings (type NUMBER) (default 1)))

; ;; Template para candidatos
; (deftemplate REFINAMIENTO::candidate-set
;     (slot recipe-instance (type INSTANCE))
;     (multislot restrictions-met (type SYMBOL))
;     (slot restriction-count (type NUMBER) (default 0)))

(deftemplate limites-calculados
    (slot min-price (type FLOAT))
    (slot limite-barato (type FLOAT))
    (slot limite-medio (type FLOAT))
    (slot max-price (type FLOAT)))

; (deftemplate match-control
;     (slot phase (type SYMBOL)))


; (deffacts user-example (user-restrictions (is-vegan FALSE) (is-vegetarian TRUE) (is-gluten-free FALSE) (is-dairy-free FALSE) (max-price 300) (min-price 10) (min-servings 1)))

; (deffacts candidate-set-test-facts
;   (candidate-set
;     (recipe-instance [Recipe_644094])
;     (restrictions-met vegetarian)
;     (restriction-count 1))

;    (candidate-set
;     (recipe-instance [Recipe_647875])
;     (restrictions-met vegetarian)
;     (restriction-count 1))

;     (candidate-set
;     (recipe-instance [Recipe_715595])
;     (restrictions-met vegetarian)
;     (restriction-count 1))

;     (candidate-set
;     (recipe-instance [Recipe_649560])
;     (restrictions-met vegetarian)
;     (restriction-count 1))

;     (candidate-set
;     (recipe-instance [Recipe_716431])
;     (restrictions-met vegetarian)
;     (restriction-count 1))

;     (candidate-set
;     (recipe-instance [Recipe_661121])
;     (restrictions-met vegetarian)
;     (restriction-count 1))
;     (candidate-set
;     (recipe-instance [Recipe_716433])
;     (restrictions-met vegetarian)
;     (restriction-count 1))
;     (candidate-set
;     (recipe-instance [Recipe_665203])
;     (restrictions-met vegetarian)
;     (restriction-count 1))
;     (candidate-set
;     (recipe-instance [Recipe_991625])
;     (restrictions-met vegetarian)
;     (restriction-count 1))
;     (candidate-set
;     (recipe-instance [Recipe_1098351])
;     (restrictions-met vegetarian)
;     (restriction-count 1))
;     (candidate-set
;     (recipe-instance [Recipe_632527])
;     (restrictions-met vegetarian)
;     (restriction-count 1))
;     (candidate-set
;     (recipe-instance [Recipe_641445])
;     (restrictions-met vegetarian)
;     (restriction-count 1))
; )

(deffacts sistema-inicio
    (match-control (phase complete))
)
    
;;; Calcula rangos de precio de los menus

(deffunction REFINAMIENTO::calc-intervalo () ;REFINAMIENTO::
    (bind ?facts (find-fact ((?f user-restrictions)) TRUE))
   
   (if (neq ?facts FALSE) then

      ;;; Precios min-max user
      (bind ?fact (nth$ 1 ?facts))
      (bind ?minPrice_us (fact-slot-value ?fact min-price))
      (bind ?maxPrice_us (fact-slot-value ?fact max-price))

      ;;; Precios min-max recetas
      (bind ?minPrice_candidatos 1000000) ;;; Valor muy alto inicial
      (bind ?maxPrice_candidatos 0)
      (bind ?candidatos-encontrados FALSE)
      (bind ?candidate-facts (find-all-facts ((?c candidate-set)) TRUE))
      
      (if (or (eq ?candidate-facts FALSE) 
                (and (neq ?candidate-facts FALSE) (= (length$ ?candidate-facts) 0))) then
            (printout t "ERROR: No hay candidatos disponibles (en verificar)" crlf)
            (return FALSE)
      )
        
      (printout t "Debug: Encontrados " (length$ ?candidate-facts) " candidatos" crlf)
            
      (foreach ?cf ?candidate-facts
         (bind ?inst (fact-slot-value ?cf recipe-instance))
         (bind ?precio (send ?inst get-price))
         
         (if (< ?precio ?minPrice_candidatos) then
            (bind ?minPrice_candidatos ?precio))
            
         (if (> ?precio ?maxPrice_candidatos) then
            (bind ?maxPrice_candidatos ?precio)))

      ;;; Def limites

      (bind ?minPrice_final (max ?minPrice_us ?minPrice_candidatos))
      (bind ?maxPrice_final ?maxPrice_us)

      ;;; Verificar limites correcto 

      (if (>= ?minPrice_final ?maxPrice_final) then
            (printout t "ERROR: No hay solapamiento en los rangos de precio" crlf)
            (printout t "   Usuario: " ?minPrice_us "-" ?maxPrice_us "€" crlf)
            (printout t "   Candidatos: " ?minPrice_candidatos "-" ?maxPrice_candidatos "€" crlf)
            (return FALSE))
      
      ;;; Calc interv

      (bind ?rango (- ?maxPrice_final ?minPrice_final))
      (bind ?tercio (/ ?rango 3.0))
      (bind ?limite1 (+ ?minPrice_final ?tercio))
      (bind ?limite2 (+ ?limite1 ?tercio))

      ;;;Imprimir los limites e intervalos

      (printout t "CÁLCULO DE LÍMITES:" crlf)
      (printout t "   Usuario: " ?minPrice_us " - " ?maxPrice_us "€" crlf)
      (printout t "   Candidatos: " ?minPrice_candidatos " - " ?maxPrice_candidatos "€" crlf)
      (printout t "   Final: " ?minPrice_final " - " ?maxPrice_final "€" crlf)
      (printout t "   Límites: " ?minPrice_final " | " ?limite1 " | " ?limite2 " | " ?maxPrice_final "€" crlf)
      
      ;;; Retornar lista con los dos límites: 
      
      (return (create$ ?minPrice_final ?limite1 ?limite2 ?maxPrice_final))
   else
      (printout t "ERROR: No se encontró user-restrictions" crlf)
      (return FALSE)
   )
)

;;;Verifica platos usados

(deffunction REFINAMIENTO::plato-ya-usado (?e ?p ?po)
    (do-for-all-facts ((?m menu)) TRUE
        (if (or (eq ?m:entrante ?e) 
                (eq ?m:principal ?p) 
                (eq ?m:postre ?po)) then
            (return TRUE)))
    (return FALSE)
)

;;;Verifica combinacion platos es valida

(deffunction REFINAMIENTO::combinacion-es-valida (?entrante ?principal ?postre)
    ;;; Verificar que no sean la misma receta
    (if (or (eq ?entrante ?principal) 
            (eq ?entrante ?postre) 
            (eq ?principal ?postre)) then
        (return FALSE)
    )
    
    ;;; Verificar que no estén ya en otro menú
    (if (plato-ya-usado ?entrante ?principal ?postre) then
        (return FALSE)
    )
    
    (return TRUE)
)

;;; Busca combinacion de platos valida para el menu

(deffunction REFINAMIENTO::buscar-combinacion-valida (?precio-min ?precio-max)
    (bind ?entrantes (create$))
    (bind ?principales (create$))
    (bind ?postres (create$))
    
    ;;; Separar candidatos por tipo de plato
    (do-for-all-facts ((?c candidate-set)) TRUE
        (bind ?inst (fact-slot-value ?c recipe-instance))
        (bind ?meal-types (send ?inst get-meal_types))
        
        (if (and (not (member$ main-course ?meal-types))
         (not (member$ dessert ?meal-types))
         (or (member$ starter ?meal-types)
             (member$ appetizer ?meal-types)
             (member$ side-dish ?meal-types))) then
            (bind ?entrantes (create$ ?entrantes ?inst)))
        
        (if (and (not (member$ starter ?meal-types))
         (not (member$ dessert ?meal-types))
         (not (member$ appetizer ?meal-types))
         (not (member$ side-dish ?meal-types))
         (or (member$ main-course ?meal-types)
             (member$ main-dish ?meal-types)))then
            (bind ?principales (create$ ?principales ?inst)))
            
        (if (and (not (member$ starter ?meal-types))
         (not (member$ main-course ?meal-types))
         (not (member$ appetizer ?meal-types))
         (not (member$ side-dish ?meal-types))
         (not (member$ brunch ?meal-types))
         (member$ dessert ?meal-types)) then
            (bind ?postres (create$ ?postres ?inst))))
    
    ;;; Buscar combinación que cumpla con el rango de precio
    (foreach ?e ?entrantes
        (foreach ?p ?principales
            (foreach ?po ?postres
                (if (combinacion-es-valida ?e ?p ?po) then
                    (bind ?precio-total (+ (send ?e get-price) 
                                         (send ?p get-price) 
                                         (send ?po get-price)))
                    (if (and (>= ?precio-total ?precio-min) 
                             (<= ?precio-total ?precio-max)) then
                        (return (create$ ?e ?p ?po ?precio-total)))))))
    
    (return FALSE)
)

;;; Mostrar detalles menu


(deffunction REFINAMIENTO::mostrar-detalles-menu (?m)
    (printout t "   💰 Precio total: " (fact-slot-value ?m precio-total) "€" crlf)
    (printout t "   🥗 Entrante: " (send (fact-slot-value ?m entrante) get-title) 
             " (" (send (fact-slot-value ?m entrante) get-price) "€)" crlf)
    (printout t "   🍖 Principal: " (send (fact-slot-value ?m principal) get-title) 
             " (" (send (fact-slot-value ?m principal) get-price) "€)" crlf)
    (printout t "   🍰 Postre: " (send (fact-slot-value ?m postre) get-title) 
             " (" (send (fact-slot-value ?m postre) get-price) "€)" crlf crlf)
)



;;; REGLAS PARA CREAR MENUS

(defrule REFINAMIENTO::iniciar-creacion-menus
    (declare (salience 100))
    ; ?ctrl <- (match-control (phase match-complete))
    =>
    ; (retract ?ctrl)
    (printout t "INICIANDO CREACIÓN DE MENÚS" crlf)
    
    
    (bind ?limites (calc-intervalo))
    
    (if (neq ?limites FALSE) then
        (assert (limites-calculados
            (min-price (nth$ 1 ?limites))
            (limite-barato (nth$ 2 ?limites))
            (limite-medio (nth$ 3 ?limites))
            (max-price (nth$ 4 ?limites))))
    else
        (printout t "No se pudieron calcular los límites" crlf)
    )
)


(defrule REFINAMIENTO::crear-menu-barato
    (declare (salience 90))
    ?limites <- (limites-calculados 
        (min-price ?min) 
        (limite-barato ?limBarato)
        (limite-medio ?limMedio) 
        (max-price ?max))
    (not (menu (categoria barato)))
    =>
    (printout t crlf " BUSCANDO MENÚ BARATO (≤ " ?limBarato "€)..." crlf)
    (bind ?menu-barato (buscar-combinacion-valida ?min ?limBarato))
    
    (if (neq ?menu-barato FALSE) then
        (assert (menu 
            (categoria barato)
            (entrante (nth$ 1 ?menu-barato))
            (principal (nth$ 2 ?menu-barato))
            (postre (nth$ 3 ?menu-barato))
            (precio-total (nth$ 4 ?menu-barato))))
        (printout t "     MENÚ BARATO CREADO: " (nth$ 4 ?menu-barato) "€" crlf)
    else
        (printout t "       No se pudo crear menú barato" crlf)
    )
)

(defrule REFINAMIENTO::crear-menu-medio
    (declare (salience 80))
    ?limites <- (limites-calculados 
        (min-price ?min) 
        (limite-barato ?limBarato)
        (limite-medio ?limMedio) 
        (max-price ?max))
    (not (menu (categoria medio)))
    =>
    (printout t crlf "BUSCANDO MENÚ MEDIO (" ?limBarato "€ - " ?limMedio "€)..." crlf)
    (bind ?menu-medio (buscar-combinacion-valida ?limBarato ?limMedio))
    
    (if (neq ?menu-medio FALSE) then
        (assert (menu 
            (categoria medio)
            (entrante (nth$ 1 ?menu-medio))
            (principal (nth$ 2 ?menu-medio))
            (postre (nth$ 3 ?menu-medio))
            (precio-total (nth$ 4 ?menu-medio))))
        (printout t "     MENÚ MEDIO CREADO: " (nth$ 4 ?menu-medio) "€" crlf)
    else
        (printout t "       No se pudo crear menú medio" crlf)
    )
)

(defrule REFINAMIENTO::crear-menu-caro
    (declare (salience 70))
    ?limites <- (limites-calculados 
        (min-price ?min) 
        (limite-barato ?limBarato)
        (limite-medio ?limMedio) 
        (max-price ?max))
    (not (menu (categoria caro)))
    =>
    (printout t crlf "BUSCANDO MENÚ CARO (≥ " ?limMedio "€)..." crlf)
    (bind ?menu-caro (buscar-combinacion-valida ?limMedio ?max))
    
    (if (neq ?menu-caro FALSE) then
        (assert (menu 
            (categoria caro)
            (entrante (nth$ 1 ?menu-caro))
            (principal (nth$ 2 ?menu-caro))
            (postre (nth$ 3 ?menu-caro))
            (precio-total (nth$ 4 ?menu-caro))))
        (printout t "     MENÚ CARO CREADO: " (nth$ 4 ?menu-caro) "€" crlf)
    else
        (printout t "       No se pudo crear menú caro" crlf)
    )
)

;;; Reintentar con otro metodo si es necesario

(defrule REFINAMIENTO::reintentar-con-metodo-alternativo
    (declare (salience 50))
    ?limites <- (limites-calculados (min-price ?min) (limite-barato ?lb) 
                                   (limite-medio ?lm) (max-price ?max))
    (or (not (menu (categoria barato)))
        (not (menu (categoria medio)))
        (not (menu (categoria caro))))
    =>
    (printout t crlf "Algunos menús no se pudieron crear, intentando ajustar..." crlf)
    
    ;;; Aquí puedes implementar una estrategia alternativa
    ;;; Por ejemplo, ampliar los rangos de precio o permitir reutilizar platos
    (printout t "  Estrategia de reintento no implementada" crlf)
)


;;; Mostrar resultados finales

(defrule REFINAMIENTO::mostrar-resultados-finales
    (declare (salience -100))
    =>
    (printout t crlf "========================================" crlf)
    (printout t "📊 RESUMEN FINAL DE MENÚS" crlf)
    (printout t "========================================" crlf)
    
    (bind ?barato (if (> (length$ (find-all-facts ((?m menu)) (eq ?m:categoria barato))) 0) 
                     then "✅" else "❌"))
    (bind ?medio (if (> (length$ (find-all-facts ((?m menu)) (eq ?m:categoria medio))) 0) 
                    then "✅" else "❌"))
    (bind ?caro (if (> (length$ (find-all-facts ((?m menu)) (eq ?m:categoria caro))) 0) 
                   then "✅" else "❌"))
    
    (printout t "Barato: " ?barato " | Medio: " ?medio " | Caro: " ?caro crlf crlf)
    
    ;;; Mostrar detalles de cada menú creado
    (bind ?menus-baratos (find-all-facts ((?m menu)) (eq ?m:categoria barato)))
    (if (> (length$ ?menus-baratos) 0) then
        (printout t "🍽️  MENÚ BARATO:" crlf)
        (foreach ?m ?menus-baratos
            (mostrar-detalles-menu ?m)))
            
    (bind ?menus-medios (find-all-facts ((?m menu)) (eq ?m:categoria medio)))
    (if (> (length$ ?menus-medios) 0) then
        (printout t "🍽️  MENÚ MEDIO:" crlf)
        (foreach ?m ?menus-medios
            (mostrar-detalles-menu ?m)))
            
    (bind ?menus-caros (find-all-facts ((?m menu)) (eq ?m:categoria caro)))
    (if (> (length$ ?menus-caros) 0) then
        (printout t "🍽️  MENÚ CARO:" crlf)
        (foreach ?m ?menus-caros
            (mostrar-detalles-menu ?m)))
            
    (if (and (= (length$ ?menus-baratos) 0) 
             (= (length$ ?menus-medios) 0) 
             (= (length$ ?menus-caros) 0)) then
        (printout t "❌ No se pudo crear ningún menú" crlf))
)



;; (deffunction REFINAMIENTO::get-precios-recipe (instancias o classes de recipies)
;; ;;; igual no hay que hacerlo 

;; )

;(defrule REFINAMIENTO::make-menus (parametros) 
 ;;; coger las candidatos de recetas y coger un meal-type para cada menu 
 ;;;y calcular con los precios y separarlos en 3 menus 
 ;;; hay que calcular si estan todas las restricciones en un grupo de menus y sino hacer varios grupos

;()
;; ;=>
;; ()

;;  )

 ;(defrule REFINAMIENTO::seleccionar-mejor-menu-barato
   ; (user-restrictions (min-price ?minP) (max-price ?maxP))
   
    ;(candidate-set (recipe-instance ?e))
    ;(candidate-set (recipe-instance ?p))
 ;   (candidate-set (recipe-instance ?po))
  ;  
 ;   (test (member$ starter (send ?e get-meal_types)))
  ;  (test (member$ main-course (send ?p get-meal_types)))
   ; (test (member$ dessert (send ?po get-meal_types)))
   ; (test (and (neq ?e ?p) (neq ?e ?po) (neq ?p ?po)))
   
   ; No existe ya un menú barato
  ;  (not (menu (categoria barato)))
   ; =>
   ; (bind ?precio-total (+ (send ?e get-price) (send ?p get-price) (send ?po get-price)))
   ; (bind ?limites (crear-rangos-desde-restricciones))
    ;(bind ?limite1 (nth$ 1 ?limites))
   
   ; Solo si es barato
  ;  (if (<= ?precio-total ?limite1) then
   ;    (assert (menu (categoria barato) (entrante ?e) (principal ?p) (postre ?po) (precio-total ?precio-total)))
    ;   (printout t "✓ Menú BARATO: " ?precio-total "€" crlf)))

 ;(defrule REFINAMIENTO::seleccionar-mejor-menu-medio
   ; (user-restrictions (min-price ?minP) (max-price ?maxP))
   ; (candidate-set (recipe-instance ?e))
   ; (candidate-set (recipe-instance ?p))
   ; (candidate-set (recipe-instance ?po))
   
 ;  (test (member$ starter (send ?e get-meal_types)))
 ;  (test (member$ main-course (send ?p get-meal_types)))
 ;  (test (member$ dessert (send ?po get-meal_types)))
 ;  (test (and (neq ?e ?p) (neq ?e ?po) (neq ?p ?po)))
   
 ;  (not (menu (categoria medio)))
 ;  =>
 ;  (bind ?precio-total (+ (send ?e get-price) (send ?p get-price) (send ?po get-price)))
 ;  (bind ?limites (crear-rangos-desde-restricciones))
 ;  (bind ?limite1 (nth$ 1 ?limites))
 ;  (bind ?limite2 (nth$ 2 ?limites))
   
 ;  (if (and (> ?precio-total ?limite1) (<= ?precio-total ?limite2)) then
 ;     (assert (menu (categoria medio) (entrante ?e) (principal ?p) (postre ?po) (precio-total ?precio-total)))
 ;     (printout t "✓ Menú MEDIO: " ?precio-total "€" crlf)))

;(defrule REFINAMIENTO::seleccionar-mejor-menu-caro
;   (user-restrictions (min-price ?minP) (max-price ?maxP))
;   (candidate-set (recipe-instance ?e))
;   (candidate-set (recipe-instance ?p))
;   (candidate-set (recipe-instance ?po))
   
;   (test (member$ starter (send ?e get-meal_types)))
;   (test (member$ main-course (send ?p get-meal_types)))
;   (test (member$ dessert (send ?po get-meal_types)))
;   (test (and (neq ?e ?p) (neq ?e ?po) (neq ?p ?po)))
   
;   (not (menu (categoria caro)))
 ;  =>
 ;  (bind ?precio-total (+ (send ?e get-price) (send ?p get-price) (send ?po get-price)))
 ;  (bind ?limites (crear-rangos-desde-restricciones))
 ;  (bind ?limite2 (nth$ 2 ?limites))
   
  ; (if (and (> ?precio-total ?limite2) (<= ?precio-total ?maxP)) then
;      (assert (menu (categoria caro) (entrante ?e) (principal ?p) (postre ?po) (precio-total ?precio-total)))
;      (printout t "✓ Menú CARO: " ?precio-total "€" crlf)))