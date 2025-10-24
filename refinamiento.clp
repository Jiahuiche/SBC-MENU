(defmodule REFINAMIENTO (import ONTOLOGY ?ALL) 
                        ;(import MAIN ?ALL ) ;hacer module match 
                         (import DATA ?ALL) (export ?ALL))

(deftemplate REFINAMIENTO::menu
    (slot categoria (type SYMBOL)) ;;; barato, medio, caro
   (slot entrante (type INSTANCE))
   (slot principal (type INSTANCE))
   (slot postre (type INSTANCE))
   (slot precio-total (type FLOAT)))





;(assert (candidate-set (recipe-instance (create$))))

(deffacts user-example (user-restrictions (is-vegan FALSE) (is-vegetarian FALSE) (is-gluten-free FALSE) (is-dairy-free FALSE) (max-price 50) (min-price 10) (min-servings 1)))

(deffunction REFINAMIENTO::calc-intervalo-opc1 () ;REFINAMIENTO::
    (bind ?fact (find-fact ((?f user-restrictions)) TRUE))
   
   (if (neq ?fact FALSE) then
      (bind ?minPrice (fact-slot-value (nth$ 1 ?fact) min-price))
      (bind ?maxPrice (fact-slot-value (nth$ 1 ?fact) max-price))
      
      (bind ?rango (- ?maxPrice ?minPrice))
      (bind ?tercio (/ ?rango 3.0))
      (bind ?limite1 (+ ?minPrice ?tercio))
      (bind ?limite2 (+ ?limite1 ?tercio))
      
      ;;; Retornar lista con los dos límites: (limite_bajo-medio limite_medio-alto)
      (return (create$ ?minPrice ?limite1 ?limite2 ?maxPrice))
   else
      (printout t "ERROR: No se encontró user-restrictions" crlf)
      (return FALSE)))




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