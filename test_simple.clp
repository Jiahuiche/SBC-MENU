;;;============================================================================
;;; ARCHIVO DE PRUEBA DEL SISTEMA SIMPLIFICADO
;;;============================================================================

;;; 1. Cargar el sistema de matching simplificado
(load "match_simple.clp")

;;; 2. Imprimir mensaje de inicio
(printout t crlf)
(printout t "==========================================" crlf)
(printout t "   PRUEBA DEL SISTEMA DE MATCHING" crlf)
(printout t "==========================================" crlf)
(printout t crlf)

;;; 3. Resetear el sistema
(reset)

;;; 4. Crear recetas de prueba
(printout t "[INFO] Creando recetas de prueba..." crlf)

(assert (recipe-fact
    (id Recipe_001)
    (name "Ensalada de Quinoa")
    (category main-course)
    (price 250)
    (servings 4)
    (is-vegan TRUE)
    (is-vegetarian TRUE)
    (is-gluten-free TRUE)
    (is-dairy-free TRUE)))

(assert (recipe-fact
    (id Recipe_002)
    (name "Pastel Sin Gluten")
    (category dessert)
    (price 180)
    (servings 8)
    (is-vegan FALSE)
    (is-vegetarian TRUE)
    (is-gluten-free TRUE)
    (is-dairy-free FALSE)))

(assert (recipe-fact
    (id Recipe_003)
    (name "Sopa de Lentejas")
    (category soup)
    (price 120)
    (servings 6)
    (is-vegan TRUE)
    (is-vegetarian TRUE)
    (is-gluten-free TRUE)
    (is-dairy-free TRUE)))

(assert (recipe-fact
    (id Recipe_004)
    (name "Huevos al Horno")
    (category appetizer)
    (price 145)
    (servings 4)
    (is-vegan FALSE)
    (is-vegetarian TRUE)
    (is-gluten-free TRUE)
    (is-dairy-free TRUE)))

(printout t "[OK] 4 recetas creadas" crlf crlf)

;;; 5. Definir restricciones del usuario
(printout t "[INFO] Configurando restricciones del usuario:" crlf)
(printout t "  - Vegetariano: SI" crlf)
(printout t "  - Sin Gluten: SI" crlf)
(printout t "  - Precio maximo: $500" crlf crlf)

(assert (user-restrictions
    (is-vegan FALSE)
    (is-vegetarian TRUE)
    (is-gluten-free TRUE)
    (is-dairy-free FALSE)
    (max-price 500)
    (min-servings 2)))

;;; 6. Definir preferencias del menú
(printout t "[INFO] Configurando preferencias del menu:" crlf)
(printout t "  - Aperitivo: SI" crlf)
(printout t "  - Plato principal: SI" crlf)
(printout t "  - Postre: SI" crlf)
(printout t "  - Sopa: NO" crlf crlf)

(assert (menu-preferences
    (wants-appetizer TRUE)
    (wants-main-course TRUE)
    (wants-dessert TRUE)
    (wants-soup FALSE)))

;;; 7. Ejecutar el sistema
(printout t "[INFO] Ejecutando sistema de matching..." crlf)
(printout t "==========================================" crlf crlf)

(run)

;;; 8. Mostrar resultados manualmente si es necesario
(printout t crlf)
(printout t "==========================================" crlf)
(printout t "   RESULTADOS DEL MATCHING" crlf)
(printout t "==========================================" crlf crlf)

(printout t "[CANDIDATOS] Recetas que cumplen restricciones:" crlf)
(facts candidate-recipe)

(printout t crlf)
(printout t "[MENU] Items del menu seleccionado:" crlf)
(facts menu-item)

(printout t crlf)
(printout t "==========================================" crlf)
(printout t "   PRUEBA COMPLETADA" crlf)
(printout t "==========================================" crlf)
(printout t crlf)

;;; Salir
(exit)
