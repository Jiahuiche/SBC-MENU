;;;============================================================================
;;; SISTEMA SIMPLIFICADO DE MATCHING DE RECETAS
;;; Solo usa recipe-fact (sin objetos COOL)
;;;============================================================================

;;;============================================================================
;;; DEFINICIÓN DE TEMPLATES
;;;============================================================================

;;; Template para restricciones del usuario
(deftemplate user-restrictions
    "Restricciones dietéticas y preferencias del usuario"
    (slot is-vegan (type SYMBOL) (allowed-symbols TRUE FALSE) (default FALSE))
    (slot is-vegetarian (type SYMBOL) (allowed-symbols TRUE FALSE) (default FALSE))
    (slot is-gluten-free (type SYMBOL) (allowed-symbols TRUE FALSE) (default FALSE))
    (slot is-dairy-free (type SYMBOL) (allowed-symbols TRUE FALSE) (default FALSE))
    (slot max-price (type NUMBER) (default 1000))
    (slot min-servings (type NUMBER) (default 1))
)

;;; Template para preferencias del menú
(deftemplate menu-preferences
    "Qué tipo de platos desea el usuario en su menú"
    (slot wants-appetizer (type SYMBOL) (allowed-symbols TRUE FALSE) (default FALSE))
    (slot wants-main-course (type SYMBOL) (allowed-symbols TRUE FALSE) (default TRUE))
    (slot wants-dessert (type SYMBOL) (allowed-symbols TRUE FALSE) (default FALSE))
    (slot wants-soup (type SYMBOL) (allowed-symbols TRUE FALSE) (default FALSE))
)

;;; Template para recetas candidatas (matching exitoso)
(deftemplate candidate-recipe
    "Recetas que cumplen con las restricciones del usuario"
    (slot recipe-id (type SYMBOL))
    (slot recipe-name (type STRING))
    (slot category (type SYMBOL) (allowed-symbols appetizer main-course soup dessert side-dish unknown))
    (slot match-score (type NUMBER) (default 0))
    (slot price (type NUMBER))
    (slot servings (type NUMBER))
)

;;; Template para items del menú final
(deftemplate menu-item
    "Items seleccionados para el menú final"
    (slot position (type SYMBOL) (allowed-symbols appetizer main-course soup dessert))
    (slot recipe-id (type SYMBOL))
    (slot recipe-name (type STRING))
    (slot price (type NUMBER))
)

;;; Template para hechos de recetas
(deftemplate recipe-fact
    "Hecho de receta para matching"
    (slot id (type SYMBOL))
    (slot name (type STRING))
    (slot category (type SYMBOL) (allowed-symbols appetizer main-course soup dessert side-dish))
    (slot price (type NUMBER))
    (slot servings (type NUMBER))
    (slot is-vegan (type SYMBOL) (allowed-symbols TRUE FALSE) (default FALSE))
    (slot is-vegetarian (type SYMBOL) (allowed-symbols TRUE FALSE) (default FALSE))
    (slot is-gluten-free (type SYMBOL) (allowed-symbols TRUE FALSE) (default FALSE))
    (slot is-dairy-free (type SYMBOL) (allowed-symbols TRUE FALSE) (default FALSE))
)

;;;============================================================================
;;; MÓDULO PRINCIPAL
;;;============================================================================

(defrule initialize
    "Mensaje inicial del sistema"
    (declare (salience 100))
    =>
    (printout t crlf)
    (printout t "==========================================" crlf)
    (printout t "   SISTEMA DE MATCHING DE RECETAS" crlf)
    (printout t "==========================================" crlf)
    (printout t crlf)
)

;;;============================================================================
;;; REGLAS: RECIPE-MATCHING
;;;============================================================================

;;; Regla: Matching VEGANO
(defrule match-vegan
    "Encuentra recipe-facts veganas"
    (declare (salience 55))
    (user-restrictions (is-vegan TRUE))
    (recipe-fact 
        (id ?id)
        (name ?name)
        (is-vegan TRUE)
        (category ?category)
        (price ?price)
        (servings ?servings))
    =>
    (assert (candidate-recipe
        (recipe-id ?id)
        (recipe-name ?name)
        (category ?category)
        (match-score 100)
        (price ?price)
        (servings ?servings)))
    (printout t ">> Recipe VEGANA: " ?name " [" ?category "]" crlf)
)

;;; Regla: Matching VEGETARIANO
(defrule match-vegetarian
    "Encuentra recipe-facts vegetarianas"
    (declare (salience 50))
    (user-restrictions (is-vegetarian TRUE) (is-vegan FALSE))
    (recipe-fact 
        (id ?id)
        (name ?name)
        (is-vegetarian TRUE)
        (category ?category)
        (price ?price)
        (servings ?servings))
    =>
    (assert (candidate-recipe
        (recipe-id ?id)
        (recipe-name ?name)
        (category ?category)
        (match-score 90)
        (price ?price)
        (servings ?servings)))
    (printout t ">> Recipe VEGETARIANA: " ?name " [" ?category "]" crlf)
)

;;; Regla: Matching GLUTEN-FREE
(defrule match-gluten-free
    "Encuentra recipe-facts sin gluten"
    (declare (salience 50))
    (user-restrictions (is-gluten-free TRUE))
    (recipe-fact 
        (id ?id)
        (name ?name)
        (is-gluten-free TRUE)
        (category ?category)
        (price ?price)
        (servings ?servings))
    =>
    (assert (candidate-recipe
        (recipe-id ?id)
        (recipe-name ?name)
        (category ?category)
        (match-score 95)
        (price ?price)
        (servings ?servings)))
    (printout t ">> Recipe GLUTEN-FREE: " ?name " [" ?category "]" crlf)
)

;;; Regla: Matching DAIRY-FREE
(defrule match-dairy-free
    "Encuentra recipe-facts sin lácteos"
    (declare (salience 50))
    (user-restrictions (is-dairy-free TRUE))
    (recipe-fact 
        (id ?id)
        (name ?name)
        (is-dairy-free TRUE)
        (category ?category)
        (price ?price)
        (servings ?servings))
    =>
    (assert (candidate-recipe
        (recipe-id ?id)
        (recipe-name ?name)
        (category ?category)
        (match-score 95)
        (price ?price)
        (servings ?servings)))
    (printout t ">> Recipe DAIRY-FREE: " ?name " [" ?category "]" crlf)
)

;;; Regla: Matching combinado VEGETARIANO + GLUTEN-FREE
(defrule match-veg-gf
    "Encuentra recipe-facts vegetarianas Y sin gluten"
    (declare (salience 65))
    (user-restrictions (is-vegetarian TRUE) (is-gluten-free TRUE))
    (recipe-fact 
        (id ?id)
        (name ?name)
        (is-vegetarian TRUE)
        (is-gluten-free TRUE)
        (category ?category)
        (price ?price)
        (servings ?servings))
    =>
    (assert (candidate-recipe
        (recipe-id ?id)
        (recipe-name ?name)
        (category ?category)
        (match-score 110)
        (price ?price)
        (servings ?servings)))
    (printout t ">>> Recipe VEGETARIANA+GLUTEN-FREE: " ?name " [" ?category "]" crlf)
)

;;;============================================================================
;;; REGLAS: MENU-CONSTRUCTION
;;;============================================================================

;;; Regla: Seleccionar APERITIVO
(defrule select-appetizer
    "Selecciona el mejor aperitivo"
    (declare (salience 70))
    (menu-preferences (wants-appetizer TRUE))
    ?best <- (candidate-recipe 
                (category appetizer)
                (recipe-id ?id)
                (recipe-name ?name)
                (price ?price)
                (match-score ?score))
    (not (candidate-recipe 
            (category appetizer)
            (match-score ?s&:(> ?s ?score))))
    (not (menu-item (position appetizer)))
    =>
    (assert (menu-item
        (position appetizer)
        (recipe-id ?id)
        (recipe-name ?name)
        (price ?price)))
    (printout t crlf "==> APERITIVO SELECCIONADO: " ?name " (Score: " ?score ")" crlf)
)

;;; Regla: Seleccionar SOPA
(defrule select-soup
    "Selecciona la mejor sopa"
    (declare (salience 70))
    (menu-preferences (wants-soup TRUE))
    ?best <- (candidate-recipe 
                (category soup)
                (recipe-id ?id)
                (recipe-name ?name)
                (price ?price)
                (match-score ?score))
    (not (candidate-recipe 
            (category soup)
            (match-score ?s&:(> ?s ?score))))
    (not (menu-item (position soup)))
    =>
    (assert (menu-item
        (position soup)
        (recipe-id ?id)
        (recipe-name ?name)
        (price ?price)))
    (printout t crlf "==> SOPA SELECCIONADA: " ?name " (Score: " ?score ")" crlf)
)

;;; Regla: Seleccionar PLATO PRINCIPAL
(defrule select-main-course
    "Selecciona el mejor plato principal"
    (declare (salience 75))
    (menu-preferences (wants-main-course TRUE))
    ?best <- (candidate-recipe 
                (category main-course)
                (recipe-id ?id)
                (recipe-name ?name)
                (price ?price)
                (match-score ?score))
    (not (candidate-recipe 
            (category main-course)
            (match-score ?s&:(> ?s ?score))))
    (not (menu-item (position main-course)))
    =>
    (assert (menu-item
        (position main-course)
        (recipe-id ?id)
        (recipe-name ?name)
        (price ?price)))
    (printout t crlf "==> PLATO PRINCIPAL SELECCIONADO: " ?name " (Score: " ?score ")" crlf)
)

;;; Regla: Seleccionar POSTRE
(defrule select-dessert
    "Selecciona el mejor postre"
    (declare (salience 70))
    (menu-preferences (wants-dessert TRUE))
    ?best <- (candidate-recipe 
                (category dessert)
                (recipe-id ?id)
                (recipe-name ?name)
                (price ?price)
                (match-score ?score))
    (not (candidate-recipe 
            (category dessert)
            (match-score ?s&:(> ?s ?score))))
    (not (menu-item (position dessert)))
    =>
    (assert (menu-item
        (position dessert)
        (recipe-id ?id)
        (recipe-name ?name)
        (price ?price)))
    (printout t crlf "==> POSTRE SELECCIONADO: " ?name " (Score: " ?score ")" crlf)
)

;;;============================================================================
;;; REGLAS: REPORTING
;;;============================================================================

;;; Regla: Mostrar resumen del menú
(defrule show-menu-summary
    "Muestra un resumen del menú generado"
    (declare (salience -100))
    =>
    (printout t crlf)
    (printout t "==========================================" crlf)
    (printout t "        MENU GENERADO" crlf)
    (printout t "==========================================" crlf)
    (bind ?total-price 0)
    (do-for-all-facts ((?m menu-item)) TRUE
        (printout t ?m:position " : " ?m:recipe-name " ($" ?m:price ")" crlf)
        (bind ?total-price (+ ?total-price ?m:price))
    )
    (printout t "------------------------------------------" crlf)
    (printout t "TOTAL: $" ?total-price crlf)
    (printout t "==========================================" crlf crlf)
)

;;; Regla: Mostrar estadísticas
(defrule show-statistics
    "Muestra estadísticas de las recetas"
    (declare (salience -90))
    =>
    (bind ?total-candidates (length$ (find-all-facts ((?c candidate-recipe)) TRUE)))
    (bind ?total-menu-items (length$ (find-all-facts ((?m menu-item)) TRUE)))
    
    (printout t crlf)
    (printout t "==========================================" crlf)
    (printout t "        ESTADISTICAS" crlf)
    (printout t "==========================================" crlf)
    (printout t "Recetas candidatas: " ?total-candidates crlf)
    (printout t "Items en el menu: " ?total-menu-items crlf)
    (printout t "==========================================" crlf crlf)
)
