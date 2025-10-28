(defmodule REFINAMIENTO (import ONTOLOGY ?ALL) 
                        (import MATCH ?ALL )
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


(deftemplate limites-calculados
    (slot min-price (type FLOAT))
    (slot limite-barato (type FLOAT))
    (slot limite-medio (type FLOAT))
    (slot max-price (type FLOAT)))



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
      (bind ?candidate-facts (find-all-facts ((?c combinationMAX)) TRUE))
      
      (if (or (eq ?candidate-facts FALSE) 
                (and (neq ?candidate-facts FALSE) (= (length$ ?candidate-facts) 0))) then
            (printout t "ERROR: No hay candidatos disponibles (en verificar)" crlf)
            (return FALSE)
      )
        
      (printout t "Debug: Encontrados " (length$ ?candidate-facts) " candidatos" crlf)
            
      (foreach ?cf ?candidate-facts
         (bind ?inst (fact-slot-value ?cf recipes))
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
    (do-for-all-facts ((?c combinationMAX)) TRUE
        (bind ?inst (fact-slot-value ?c recipes))
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

;;; Sugerir bebidas basado en los platos del menú
(deffunction REFINAMIENTO::sugerir-bebidas (?m)
    (bind ?entrante (fact-slot-value ?m entrante))
    (bind ?principal (fact-slot-value ?m principal))
    (bind ?postre (fact-slot-value ?m postre))
    
    (bind ?bebidas (create$))
    
    ;;; Bebidas basadas en el plato principal
    (bind ?tipos-principal (send ?principal get-meal_types))
    (bind ?ingredientes-principal (send ?principal get-ingredients))
    
    ;;; Agua siempre incluida
    (bind ?bebidas (create$ ?bebidas "agua"))
    
    ;;; Sugerencias basadas en el tipo de plato principal
    (if (or (member$ fish ?ingredientes-principal)
            (member$ salmon ?ingredientes-principal)
            (member$ tuna ?ingredientes-principal)
            (member$ cod ?ingredientes-principal)
            (member$ shrimp ?ingredientes-principal)
            (member$ lobster ?ingredientes-principal)
            (member$ crab ?ingredientes-principal)
            (member$ octopus ?ingredientes-principal)
            (member$ scallop ?ingredientes-principal)
            (member$ seafood ?ingredientes-principal)) then
        (bind ?bebidas (create$ ?bebidas "vino-blanco" "cerveza-lager"))
    )
    
    (if (or (member$ beef ?ingredientes-principal)
            (member$ steak ?ingredientes-principal)
            (member$ lamb ?ingredientes-principal)
            (member$ pork ?ingredientes-principal)) then
        (bind ?bebidas (create$ ?bebidas "vino-tinto" "cerveza-ambar"))
    )
    
    (if (or (member$ chicken ?ingredientes-principal)
            (member$ turkey ?ingredientes-principal)
            (member$ duck ?ingredientes-principal)
            (member$ poultry ?ingredientes-principal)) then
        (bind ?bebidas (create$ ?bebidas "vino-rosado" "cerveza-rubia"))
    )

    (if (or (member$ pasta ?ingredientes-principal)
            (member$ spaghetti ?ingredientes-principal)
            (member$ noodle ?ingredientes-principal)
            (member$ macaroni ?ingredientes-principal)
            (member$ fettuccine ?ingredientes-principal)
            (member$ ravioli ?ingredientes-principal)) then
        (bind ?bebidas (create$ ?bebidas "vino-tinto" "vino-blanco"))
    )

    (if (or (member$ tofu ?ingredientes-principal)
            (member$ bean ?ingredientes-principal)
            (member$ lentil ?ingredientes-principal)
            (member$ vegetable ?ingredientes-principal)
            (member$ chickpea ?ingredientes-principal)) then
        (bind ?bebidas (create$ ?bebidas "vino-rosado" "vino-blanco"))
    )
    
    (if (member$ spicy ?ingredientes-principal) then
        (bind ?bebidas (create$ ?bebidas "cerveza" "limonada"))
    )
    
    ;;; Refrescos para postres dulces
    (bind ?tipos-postre (send ?postre get-meal_types))
    (if (member$ dessert ?tipos-postre) then
        (bind ?bebidas (create$ ?bebidas "café" "té"))
    )
    
    ;;; Bebidas universales
    (bind ?bebidas (create$ ?bebidas "refrescos"))
    
    ;;; Eliminar duplicados
    (bind ?bebidas-unicas (create$))
    (foreach ?b ?bebidas
        (if (not (member$ ?b ?bebidas-unicas)) then
            (bind ?bebidas-unicas (create$ ?bebidas-unicas ?b))))
    
    (return ?bebidas-unicas)
)

;;; Mostrar detalles menu


(deffunction REFINAMIENTO::mostrar-detalles-menu (?m)
    (printout t " Precio total: " (fact-slot-value ?m precio-total) "€" crlf)
    (printout t "Entrante: " (send (fact-slot-value ?m entrante) get-title) 
             " (" (send (fact-slot-value ?m entrante) get-price) "€)" crlf)
    (printout t "Principal: " (send (fact-slot-value ?m principal) get-title) 
             " (" (send (fact-slot-value ?m principal) get-price) "€)" crlf)
    
    ;;; MOSTRAR VINO RECOMENDADO PARA EL PLATO PRINCIPAL
    (bind ?vino-principal (send (fact-slot-value ?m principal) get-wine_pairing))
    (if (and (neq ?vino-principal "") (neq ?vino-principal "No wine pairing")) then
        (printout t "Vino recomendado: " ?vino-principal crlf)
    else
        (printout t "Vino recomendado: Cualquier Vino" crlf)
    )
    
    (printout t "Postre: " (send (fact-slot-value ?m postre) get-title) 
             " (" (send (fact-slot-value ?m postre) get-price) "€)" crlf)
    
    ;;; SUGERIR BEBIDAS/REFRESCOS BASADO EN LOS PLATOS
    (printout t "Bebidas sugeridas: ")
    (bind ?bebidas-sugeridas (sugerir-bebidas ?m))
    (printout t (implode$ ?bebidas-sugeridas) crlf crlf)
)

;;; Versión relajada de búsqueda (no verifica platos usados)

(deffunction REFINAMIENTO::buscar-combinacion-valida-relajada (?precio-min ?precio-max)
    ;;; Versión relajada que no verifica platos usados
    (bind ?entrantes (create$))
    (bind ?principales (create$))
    (bind ?postres (create$))
    
    ;;; Separar candidatos por tipo de plato
    (do-for-all-facts ((?c combinationMAX)) TRUE
        (bind ?inst (fact-slot-value ?c recipes))
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
                     (member$ main-dish ?meal-types))) then
            (bind ?principales (create$ ?principales ?inst)))
            
        (if (and (not (member$ starter ?meal-types))
                 (not (member$ main-course ?meal-types))
                 (not (member$ appetizer ?meal-types))
                 (not (member$ side-dish ?meal-types))
                 (not (member$ brunch ?meal-types))
                 (member$ dessert ?meal-types)) then
            (bind ?postres (create$ ?postres ?inst))))
    
    ;;; DEBUG: Mostrar cantidades
    (printout t "        [DEBUG] Entrantes: " (length$ ?entrantes) 
             " | Principales: " (length$ ?principales) 
             " | Postres: " (length$ ?postres) crlf)
    
    ;;; Buscar combinación (solo verifica que no sean la misma receta)
    (foreach ?e ?entrantes
        (foreach ?p ?principales
            (foreach ?po ?postres
                ;;; SOLO verificar que no sean la misma receta (no verificar uso previo)
                (if (and (neq ?e ?p) (neq ?e ?po) (neq ?p ?po)) then
                    (bind ?precio-total (+ (send ?e get-price) 
                                         (send ?p get-price) 
                                         (send ?po get-price)))
                    (if (and (>= ?precio-total ?precio-min) 
                             (<= ?precio-total ?precio-max)) then
                        (printout t "        [DEBUG] Combinación encontrada: " ?precio-total "€" crlf)
                        (return (create$ ?e ?p ?po ?precio-total)))))))
    
    (printout t "        [DEBUG] No se encontró combinación en rango " ?precio-min "-" ?precio-max "€" crlf)
    (return FALSE)
)

;;; Reintentar creando menus permitiendo platos repetidos

;;; Reintentar creando menus permitiendo platos repetidos
(deffunction REFINAMIENTO::reintentar-con-platos-repetidos (?limites)
    (bind ?min (fact-slot-value ?limites min-price))
    (bind ?limBarato (fact-slot-value ?limites limite-barato))
    (bind ?limMedio (fact-slot-value ?limites limite-medio))
    (bind ?max (fact-slot-value ?limites max-price))
    
    (printout t "      Permitiendo platos repetidos entre menús..." crlf)
    
    ;;; Limpiar menús existentes
    (do-for-all-facts ((?m menu)) TRUE (retract ?m))
    
    ;;; DEBUG: Mostrar rangos de precio
    (printout t "      Rangos: Barato(" ?min "-" ?limBarato 
             ") Medio(" ?limBarato "-" ?limMedio 
             ") Caro(" ?limMedio "-" ?max ")" crlf)
    
    ;;; Crear menús barato (sin verificar platos usados)
    (bind ?menu-barato (buscar-combinacion-valida-relajada ?min ?limBarato))
    (if (neq ?menu-barato FALSE) then
        (assert (menu (categoria barato)
                     (entrante (nth$ 1 ?menu-barato))
                     (principal (nth$ 2 ?menu-barato))
                     (postre (nth$ 3 ?menu-barato))
                     (precio-total (nth$ 4 ?menu-barato))))
        (printout t "      ✅ Menú barato creado: " (nth$ 4 ?menu-barato) "€" crlf)
    else
        (printout t "      ❌ No se pudo crear menú barato" crlf)
    )
    
    ;;; Crear menú medio (sin verificar platos usados)
    (bind ?menu-medio (buscar-combinacion-valida-relajada ?limBarato ?limMedio))
    (if (neq ?menu-medio FALSE) then
        (assert (menu (categoria medio)
                     (entrante (nth$ 1 ?menu-medio))
                     (principal (nth$ 2 ?menu-medio))
                     (postre (nth$ 3 ?menu-medio))
                     (precio-total (nth$ 4 ?menu-medio))))
        (printout t "      ✅ Menú medio creado: " (nth$ 4 ?menu-medio) "€" crlf)
    else
        (printout t "      ❌ No se pudo crear menú medio" crlf)
    )
    
    ;;; Crear menú caro (sin verificar platos usados)
    (bind ?menu-caro (buscar-combinacion-valida-relajada ?limMedio ?max))
    (if (neq ?menu-caro FALSE) then
        (assert (menu (categoria caro)
                     (entrante (nth$ 1 ?menu-caro))
                     (principal (nth$ 2 ?menu-caro))
                     (postre (nth$ 3 ?menu-caro))
                     (precio-total (nth$ 4 ?menu-caro))))
        (printout t "      ✅ Menú caro creado: " (nth$ 4 ?menu-caro) "€" crlf)
    else
        (printout t "      ❌ No se pudo crear menú caro" crlf)
    )
    
    ;;; DEBUG: Contar menús creados
    (bind ?count-barato (length$ (find-all-facts ((?m menu)) (eq ?m:categoria barato))))
    (bind ?count-medio (length$ (find-all-facts ((?m menu)) (eq ?m:categoria medio))))
    (bind ?count-caro (length$ (find-all-facts ((?m menu)) (eq ?m:categoria caro))))
    
    (printout t "      Menús creados: Barato(" ?count-barato 
             ") Medio(" ?count-medio ") Caro(" ?count-caro ")" crlf)
    
    ; Verificar si se crearon todos los menús
    (if (and (> ?count-barato 0) (> ?count-medio 0) (> ?count-caro 0)) then
        (printout t "      ✅ TODOS los menús creados exitosamente" crlf)
        (return TRUE)
    else
        ;Limpiar si no se completó
        (do-for-all-facts ((?m menu)) TRUE (retract ?m))
        (printout t "      ❌ No se pudieron crear todos los menús" crlf)
        (return FALSE)
    )
)



;;; REGLAS PARA CREAR MENUS

(defrule REFINAMIENTO::iniciar-creacion-menus
    (declare (salience 100))
    ; ?ctrl <- (match-control (phase complete))
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
    
    ;;;; Permitir repetir platos
    (printout t "  Estrategia 1: Permitir platos repetidos..." crlf)
    (bind ?exito-repetidos (reintentar-con-platos-repetidos ?limites))
    
    (if (eq ?exito-repetidos TRUE) then
        (printout t "  ✅ Éxito con platos repetidos" crlf)
    else
        (printout t "  ❌ Falló con platos repetidos" crlf)
        ;;; Aquí puedes añadir más estrategias...
    )
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

