(defmodule REFINAMIENTO (import ONTOLOGY ?ALL) 
                        ;(import MAIN ?ALL ) ;hacer module match 
                         (import DATA ?ALL) (export ?ALL))

(deftemplate REFINAMIENTO::menu
    (slot categoria (type SYMBOL)) ;;; barato, medio, caro
   (slot entrante (type INSTANCE))
   (slot principal (type INSTANCE))
   (slot postre (type INSTANCE))
   (slot precio-total (type FLOAT)))

;;; Template para restricciones del usuario
(deftemplate REFINAMIENTO::user-restrictions
    (slot is-vegan (type SYMBOL) (allowed-symbols TRUE FALSE) (default FALSE))
    (slot is-vegetarian (type SYMBOL) (allowed-symbols TRUE FALSE) (default FALSE))
    (slot is-gluten-free (type SYMBOL) (allowed-symbols TRUE FALSE) (default FALSE))
    (slot is-dairy-free (type SYMBOL) (allowed-symbols TRUE FALSE) (default FALSE))
    (slot max-price (type NUMBER) (default 10000))
    ;;;(slot min-price (type NUMBER) (default 0))
    (slot min-servings (type NUMBER) (default 1)))

;;; Template para candidatos
(deftemplate REFINAMIENTO::candidate-set
    (slot recipe-instance (type INSTANCE))
    (multislot restrictions-met (type SYMBOL))
    (slot restriction-count (type NUMBER) (default 0)))


(deffacts user-example (user-restrictions (is-vegan FALSE) (is-vegetarian FALSE) (is-gluten-free FALSE) (is-dairy-free FALSE) (max-price 500) (min-price 10) (min-servings 1)))

(deffacts candidate-set-test-facts
  (candidate-set
    (recipe-instance [Recipe_644094])
    (restrictions-met vegetarian)
    (restriction-count 1))

   (candidate-set
    (recipe-instance [Recipe_647875])
    (restrictions-met vegetarian)
    (restriction-count 1))

    (candidate-set
    (recipe-instance [Recipe_715595])
    (restrictions-met vegetarian)
    (restriction-count 1))

    (candidate-set
    (recipe-instance [Recipe_649560])
    (restrictions-met vegetarian)
    (restriction-count 1))

    (candidate-set
    (recipe-instance [Recipe_716431])
    (restrictions-met vegetarian)
    (restriction-count 1))

    (candidate-set
    (recipe-instance [Recipe_661121])
    (restrictions-met vegetarian)
    (restriction-count 1))
    (candidate-set
    (recipe-instance [Recipe_716433])
    (restrictions-met vegetarian)
    (restriction-count 1))
    (candidate-set
    (recipe-instance [Recipe_665203])
    (restrictions-met vegetarian)
    (restriction-count 1))
    (candidate-set
    (recipe-instance [Recipe_991625])
    (restrictions-met vegetarian)
    (restriction-count 1))
    (candidate-set
    (recipe-instance [Recipe_1098351])
    (restrictions-met vegetarian)
    (restriction-count 1))
    (candidate-set
    (recipe-instance [Recipe_632527])
    (restrictions-met vegetarian)
    (restriction-count 1))
)
    


(deffunction REFINAMIENTO::calc-intervalo () ;REFINAMIENTO::
    (bind ?fact (find-fact ((?f user-restrictions)) TRUE))
   
   (if (neq ?fact FALSE) then

      ;;; Precios min-max user
      (bind ?minPrice_us (fact-slot-value (nth$ 1 ?fact) min-price))
      (bind ?maxPrice_us (fact-slot-value (nth$ 1 ?fact) max-price))

      ;;; Precios min-max recetas
      (bind ?minPrice_candidatos 1000000) ;;; Valor muy alto inicial
        (bind ?maxPrice_candidatos 0)
        
        (bind ?candidatos (find-all-instances ((?c candidate-set)) TRUE))
        
        (foreach ?c ?candidatos
            (bind ?inst (send ?c get-recipe-instance))
            (bind ?precio (send ?inst get-price))
            
            (if (< ?precio ?minPrice_candidatos) then
                (bind ?minPrice_candidatos ?precio))
                
            (if (> ?precio ?maxPrice_candidatos) then
                (bind ?maxPrice_candidatos ?precio)))
      ;;; Def limites

      (bind ?minPrice_final (max ?minPrice_us ?minPrice_candidatos))
      (bind ?maxPrice_final (min ?maxPrice_us ?maxPrice_candidatos))

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

      (printout t "💰 CÁLCULO DE LÍMITES:" crlf)
      (printout t "   Usuario: " ?minPrice_us " - " ?maxPrice_us "€" crlf)
      (printout t "   Candidatos: " ?minPrice_candidatos " - " ?maxPrice_candidatos "€" crlf)
      (printout t "   Final: " ?minPrice_final " - " ?maxPrice_final "€" crlf)
      (printout t "   Límites: " ?minPrice_final " | " ?limite1 " | " ?limite2 " | " ?maxPrice_final "€" crlf)
      
      ;;; Retornar lista con los dos límites: 
      
      (return (create$ ?minPrice ?limite1 ?limite2 ?maxPrice))
   else
      (printout t "ERROR: No se encontró user-restrictions" crlf)
      (return FALSE)
   )
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