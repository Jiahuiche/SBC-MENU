(defmodule REFINAMIENTO (import ONTOLOGY ?ALL) 
                        (import MATCH ?ALL )
                        (import DATA ?ALL)
                        (import input ?ALL) )

; (defrule MAIN::auto-focus-refinamiento
;     =>
;     (focus REFINAMIENTO))

(deftemplate REFINAMIENTO::menu
    (slot categoria (type SYMBOL)) ;;; barato, medio, caro
   (slot entrante (type INSTANCE))
   (slot principal (type INSTANCE))
   (slot postre (type INSTANCE))
   (slot precio-total (type FLOAT)))

(deftemplate REFINAMIENTO::menu-completo
    (slot categoria (type SYMBOL)) ;;; barato, medio, caro
    (slot entrante (type INSTANCE))
    (slot principal (type INSTANCE))
    (slot postre (type INSTANCE))
    (multislot aperitivos-extra (type INSTANCE)) ;;; Aperitivos para bodas
    (slot precio-base (type FLOAT)) ;;; Precio sin aperitivos extra
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
         (bind ?inst (fact-slot-value ?cf recipe))
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


; (deffunction REFINAMIENTO::aperitivo-ya-usado-en-otros-menus (?aperitivo)
;     "Verifica si un aperitivo ya está usado en otros menús (platos principales o aperitivos)"
;     (bind ?titulo-aperitivo (send ?aperitivo get-title))
    
;     (do-for-all-facts ((?m menu-completo)) TRUE
;         ; Verificar si coincide con entrante, principal o postre de algún menú
;         (if (or (str-compare ?titulo-aperitivo (send ?m:entrante get-title))
;                 (str-compare ?titulo-aperitivo (send ?m:principal get-title))
;                 (str-compare ?titulo-aperitivo (send ?m:postre get-title))) then
;             (return TRUE))
        
;         ; Verificar si está en los aperitivos extra de algún menú
;         (foreach ?a ?m:aperitivos-extra
;             (if (str-compare ?titulo-aperitivo (send ?a get-title)) then
;                 (return TRUE)))
;     )
;     (return FALSE)
; )


(deffunction REFINAMIENTO::plato-ya-usado (?e ?p ?po ?aperitivos)
    (bind ?titulo-entrante (send ?e get-title))
    (bind ?titulo-principal (send ?p get-title))
    (bind ?titulo-postre (send ?po get-title))
    (bind ?titulos-aperitivos (create$))
    
    ;;; Obtener títulos de todos los aperitivos del menú actual
    (foreach ?a ?aperitivos
        (bind ?titulos-aperitivos (insert$ ?titulos-aperitivos (length$ ?titulos-aperitivos) (send ?a get-title)))
    )
    
    (do-for-all-facts ((?m menu-completo)) TRUE
        ;;; Verificar si los platos principales están duplicados
        (if (or (str-compare (send ?m:entrante get-title) ?titulo-entrante) 
                (str-compare (send ?m:principal get-title) ?titulo-principal) 
                (str-compare (send ?m:postre get-title) ?titulo-postre)) then
            (return TRUE))
        
        ;;; Verificar si los aperitivos están duplicados con platos principales de otros menús
        (foreach ?a-actual ?aperitivos
            (bind ?titulo-a-actual (send ?a-actual get-title))
            (if (or (str-compare ?titulo-a-actual (send ?m:entrante get-title))
                    (str-compare ?titulo-a-actual (send ?m:principal get-title))
                    (str-compare ?titulo-a-actual (send ?m:postre get-title))) then
                (return TRUE)
            )
        )
        
        ;;; Verificar si los aperitivos están duplicados con aperitivos de otros menús
        (foreach ?a-actual ?aperitivos
            (bind ?titulo-a-actual (send ?a-actual get-title))
            (foreach ?a-otro-menu ?m:aperitivos-extra
                (if (str-compare ?titulo-a-actual (send ?a-otro-menu get-title)) then
                    (return TRUE)
                )
            )
        )
    )
    (return FALSE)
)

; ;;; Verifica combinacion platos es valida

; (deffunction REFINAMIENTO::combinacion-es-valida (?entrante ?principal ?postre ?aperitivos-extra)
;     ;;; Verificar que no sean la misma receta (por título)
;     (bind ?titulo-entrante (send ?entrante get-title))
;     (bind ?titulo-principal (send ?principal get-title))
;     (bind ?titulo-postre (send ?postre get-title))
    
;     ; Verificar duplicados entre platos principales
;     (if (or (str-compare ?titulo-entrante ?titulo-principal) 
;             (str-compare ?titulo-entrante ?titulo-postre) 
;             (str-compare ?titulo-principal ?titulo-postre)) then
;         (return FALSE)
;     )
    
;     ; Verificar que aperitivos no dupliquen con platos principales
;     (foreach ?a ?aperitivos-extra
;         (bind ?titulo-aperitivo (send ?a get-title))
;         (if (or (str-compare ?titulo-aperitivo ?titulo-entrante)
;                 (str-compare ?titulo-aperitivo ?titulo-principal)
;                 (str-compare ?titulo-aperitivo ?titulo-postre)) then
;             (return FALSE))
;     )
    
;     ;;; Verificar que no estén ya en otro menú (por título)
;     (if (plato-ya-usado ?entrante ?principal ?postre ?aperitivos-extra) then
;         (return FALSE)
;     )
    
;     (return TRUE)
; )

;;; Busca combinaciones válidas de platos (verifica duplicados entre menús)
(deffunction REFINAMIENTO::buscar-combinacion-valida (?precio-min ?precio-max ?aperitivos-extra)
    ;;; Versión relajada que SÍ verifica duplicados entre menús
    (bind ?entrantes (create$))
    (bind ?principales (create$))
    (bind ?postres (create$))
    
    ;;; Separar candidatos por tipo de plato
    (do-for-all-facts ((?c combinationMAX)) TRUE
        (bind ?inst (fact-slot-value ?c recipe))
        (bind ?meal-types (send ?inst get-meal-types))
        
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

    ;;; DEBUG: Mostrar estadísticas
    (printout t "        [DEBUG] Recetas disponibles - " 
             "Entrantes: " (length$ ?entrantes) 
             " | Principales: " (length$ ?principales) 
             " | Postres: " (length$ ?postres) crlf)
    
    ;;; Si alguna lista está vacía, retornar FALSE
    (if (or (= (length$ ?entrantes) 0) 
            (= (length$ ?principales) 0) 
            (= (length$ ?postres) 0)) then
        (printout t "        [DEBUG] No hay suficientes recetas de algún tipo" crlf)
        (return FALSE)
    )
    
    ;;; Obtener títulos ya usados en otros menús para evitar duplicados
    (bind ?titulos-ya-usados (create$))
    (do-for-all-facts ((?m menu-completo)) TRUE
        (bind ?titulos-ya-usados (create$ ?titulos-ya-usados 
            (send ?m:entrante get-title)
            (send ?m:principal get-title) 
            (send ?m:postre get-title)))
        (foreach ?a ?m:aperitivos-extra
            (bind ?titulos-ya-usados (create$ ?titulos-ya-usados (send ?a get-title))))
    )
    
    ;;; Buscar combinación (verifica duplicados con otros menús)
    (foreach ?e ?entrantes
        (bind ?titulo-e (send ?e get-title))
        (foreach ?p ?principales
            (bind ?titulo-p (send ?p get-title))
            (foreach ?po ?postres
                (bind ?titulo-po (send ?po get-title))
                
                ;;; Verificar que no sean la misma receta y no estén en otros menús
                (if (and (str-compare ?titulo-e ?titulo-p)
                         (str-compare ?titulo-e ?titulo-po)
                         (str-compare ?titulo-p ?titulo-po)
                         (not (member$ ?titulo-e ?titulos-ya-usados))
                         (not (member$ ?titulo-p ?titulos-ya-usados))
                         (not (member$ ?titulo-po ?titulos-ya-usados))) then
                    (bind ?precio-total (+ (send ?e get-price) 
                                         (send ?p get-price) 
                                         (send ?po get-price)))
                    (if (and (>= ?precio-total ?precio-min) 
                             (<= ?precio-total ?precio-max)) then
                        (printout t "        [DEBUG] Combinación válida encontrada: " ?precio-total "€" crlf)
                        (printout t "        [DEBUG]   " ?titulo-e " | " ?titulo-p " | " ?titulo-po crlf)
                        (return (create$ ?e ?p ?po ?precio-total)))))))
    
    (printout t "        [DEBUG] No se encontró combinación sin duplicados en rango " ?precio-min "-" ?precio-max "€" crlf)
    (return FALSE)
)


;;; Versión relajada de búsqueda (no verifica platos usados)

(deffunction REFINAMIENTO::buscar-combinacion-valida-relajada (?precio-min ?precio-max ?aperitivos-extra)
    "Versión RELAJADA que PERMITE repetir platos entre menús"
    (bind ?entrantes (create$))
    (bind ?principales (create$))
    (bind ?postres (create$))
    
    ;;; Separar candidatos por tipo de plato
    (do-for-all-facts ((?c combinationMAX)) TRUE
        (bind ?inst (fact-slot-value ?c recipe))
        (bind ?meal-types (send ?inst get-meal-types))
        
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

    ;;; DEBUG: Mostrar estadísticas
    (printout t "        [DEBUG-RELAJADA] Recetas disponibles - " 
             "Entrantes: " (length$ ?entrantes) 
             " | Principales: " (length$ ?principales) 
             " | Postres: " (length$ ?postres) crlf)
    
    ;;; Si alguna lista está vacía, retornar FALSE
    (if (or (= (length$ ?entrantes) 0) 
            (= (length$ ?principales) 0) 
            (= (length$ ?postres) 0)) then
        (printout t "        [DEBUG-RELAJADA] No hay suficientes recetas de algún tipo" crlf)
        (return FALSE)
    )
    
    ;;; Buscar combinación SIN verificar duplicados con otros menús
    (foreach ?e ?entrantes
        (bind ?titulo-e (send ?e get-title))
        (foreach ?p ?principales
            (bind ?titulo-p (send ?p get-title))
            (foreach ?po ?postres
                (bind ?titulo-po (send ?po get-title))
                
                ;;; SOLO verificar que no sean la misma receta dentro del mismo menú
                ;;; NO verificar si ya están en otros menús
                (if (and (str-compare ?titulo-e ?titulo-p)
                         (str-compare ?titulo-e ?titulo-po)
                         (str-compare ?titulo-p ?titulo-po)) then
                    (bind ?precio-total (+ (send ?e get-price) 
                                         (send ?p get-price) 
                                         (send ?po get-price)))
                    (if (and (>= ?precio-total ?precio-min) 
                             (<= ?precio-total ?precio-max)) then
                        (printout t "        [DEBUG-RELAJADA] ✅ Combinación encontrada: " ?precio-total "€" crlf)
                        (printout t "        [DEBUG-RELAJADA]   " ?titulo-e " | " ?titulo-p " | " ?titulo-po crlf)
                        (return (create$ ?e ?p ?po ?precio-total)))))))
    
    (printout t "        [DEBUG-RELAJADA] ❌ No se encontró combinación en rango " ?precio-min "-" ?precio-max "€" crlf)
    (return FALSE)
)

;;; Sugerir bebidas basado en los platos del menú
(deffunction REFINAMIENTO::sugerir-bebidas (?m)
    (bind ?entrante (fact-slot-value ?m entrante))
    (bind ?principal (fact-slot-value ?m principal))
    (bind ?postre (fact-slot-value ?m postre))
    
    (bind ?bebidas (create$))
    
    ;;; Bebidas basadas en el plato principal
    (bind ?tipos-principal (send ?principal get-meal-types))
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
    (bind ?tipos-postre (send ?postre get-meal-types))
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

(deffunction REFINAMIENTO::buscar-aperitivos-extra-wedding-con-combinacion (?presupuesto-aperitivos ?e ?p ?po)
    "Busca aperitivos extra para bodas, evitando duplicados con la combinación dada y con otros menús"
    (bind ?todos-aperitivos (create$))

    ; Buscar TODOS los tipos de platos que puedan servir como aperitivos
    (do-for-all-facts ((?c combinationMAX)) TRUE
        (bind ?inst (fact-slot-value ?c recipe))
        (bind ?meal-types (send ?inst get-meal-types))
        (bind ?precio (send ?inst get-price))
        
        ; Incluir cualquier plato que sea apropiado como aperitivo
        (if (and (or (member$ starter ?meal-types)
                     (member$ appetizer ?meal-types) 
                     (member$ side-dish ?meal-types)
                     (member$ hor-doeuvre ?meal-types)
                     (member$ fingerfood ?meal-types)
                     (member$ snack ?meal-types)
                     (member$ brunch ?meal-types))
                 (< ?precio 25.0)  ; Límite de precio
                 (not (member$ main-course ?meal-types))
                 (not (member$ dessert ?meal-types))) then
            (bind ?todos-aperitivos (create$ ?todos-aperitivos ?inst))
        )
    )

    ; Obtener títulos ya usados en otros menús
    (bind ?titulos-ya-usados (create$))
    (do-for-all-facts ((?m menu-completo)) TRUE
        (bind ?titulos-ya-usados (create$ ?titulos-ya-usados 
            (send ?m:entrante get-title)
            (send ?m:principal get-title) 
            (send ?m:postre get-title)))
        (foreach ?a ?m:aperitivos-extra
            (bind ?titulos-ya-usados (create$ ?titulos-ya-usados (send ?a get-title))))
    )

    ; Añadir los platos principales actuales a la lista de títulos a evitar
    (bind ?titulos-ya-usados (create$ ?titulos-ya-usados 
        (send ?e get-title) (send ?p get-title) (send ?po get-title)))

    (bind ?resultado (create$))
    (bind ?presupuesto-restante ?presupuesto-aperitivos)
    (bind ?titulos-usados (create$))

    ; DEBUG: Mostrar información de búsqueda
    (printout t "      [APERITIVOS] Buscando entre " (length$ ?todos-aperitivos) 
             " opciones, presupuesto: " ?presupuesto-aperitivos "€" crlf)

    ; Seleccionar hasta 3 aperitivos que no estén duplicados
    (foreach ?a ?todos-aperitivos
        (bind ?titulo (send ?a get-title))
        (bind ?precio (send ?a get-price))
        
        (if (and (< (length$ ?resultado) 3)
                 (<= ?precio ?presupuesto-restante)
                 (not (member$ ?titulo ?titulos-usados))
                 (not (member$ ?titulo ?titulos-ya-usados))) then
            (bind ?resultado (create$ ?resultado ?a))
            (bind ?titulos-usados (create$ ?titulos-usados ?titulo))
            (bind ?presupuesto-restante (- ?presupuesto-restante ?precio))
            (printout t "      [APERITIVO] ✅ " ?titulo " (" ?precio "€)" crlf)
        )
    )
    
    (if (> (length$ ?resultado) 0) then
        (printout t "      ✅ " (length$ ?resultado) " aperitivos seleccionados" crlf)
    else
        (printout t "      ❌ No se pudieron encontrar aperitivos" crlf)
    )
    
    (return ?resultado)
)

;;; Mostrar detalles menu


(deffunction REFINAMIENTO::mostrar-detalles-menu (?m)

    (bind ?user-fact (nth$ 1 (find-all-facts ((?u user-restrictions)) TRUE)))
    (bind ?event-type (fact-slot-value ?user-fact event-type))
    (bind ?quiere-tarta (fact-slot-value ?user-fact quiere-tarta))
    
    (printout t " Precio base: " (fact-slot-value ?m precio-base) "€" crlf)

    ;;; MOSTRAR APERITIVOS EXTRA SOLO PARA BODAS
    (bind ?aperitivos-extra (fact-slot-value ?m aperitivos-extra))
    (if (and (eq ?event-type wedding) (> (length$ ?aperitivos-extra) 0)) then
        (printout t "Aperitivos extra incluidos:" crlf)
        (foreach ?a ?aperitivos-extra
            (printout t "  - " (send ?a get-title) " (" (send ?a get-price) "€)" crlf))
    )

    (printout t "Entrante: " (send (fact-slot-value ?m entrante) get-title) 
             " (" (send (fact-slot-value ?m entrante) get-price) "€)" crlf)
    (printout t "Principal: " (send (fact-slot-value ?m principal) get-title) 
             " (" (send (fact-slot-value ?m principal) get-price) "€)" crlf)
    
    ;;; MOSTRAR VINO RECOMENDADO
    (bind ?vino-principal (send (fact-slot-value ?m principal) get-wine_pairing))
    (if (and (neq ?vino-principal "") (neq ?vino-principal "No wine pairing")) then
        (printout t "Vino recomendado: " ?vino-principal crlf)
    else
        (printout t "Vino recomendado: Cualquier Vino" crlf)
    )
    
    (printout t "Postre: " (send (fact-slot-value ?m postre) get-title) 
             " (" (send (fact-slot-value ?m postre) get-price) "€)" crlf)
    
    ; Mostrar tarta como PLUS APARTE (solo informativo)
    (if (eq ?quiere-tarta TRUE) then 
        (if (eq ?event-type wedding) then
            (printout t "PLUS: Tarta de boda personalizada disponible (+200€)" crlf)
        else 
            (if (eq ?event-type family) then
                (printout t "PLUS: Tarta familiar especial disponible (+50€)" crlf)
            else
                (printout t "PLUS: Tarta disponible (consulte precio aparte)" crlf)
            )
        )
    )
    ;;; MOSTRAR PRECIO TOTAL
    (printout t "PRECIO TOTAL: " (fact-slot-value ?m precio-total) "€" crlf)
    
    ;;; SUGERIR BEBIDAS
    (printout t "Bebidas incluidas: ")
    (bind ?bebidas-sugeridas (sugerir-bebidas ?m))
    (printout t (implode$ ?bebidas-sugeridas) crlf crlf)
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
    ?user <- (user-restrictions (event-type ?event-type) (quiere-tarta ?quiere-tarta))
    (not (menu-completo (categoria barato)))
    =>
    (printout t crlf " BUSCANDO MENÚ BARATO (≤ " ?limBarato "€)..." crlf)
    
    (bind ?presupuesto-total ?limBarato)
    (bind ?presupuesto-menu ?limBarato)
    (bind ?aperitivos-extra (create$))
    (bind ?costo-aperitivos 0.0)
    
    ; PASO 1: Si es boda, reservar 20% para aperitivos extra
    (if (eq ?event-type wedding) then
        (printout t "      Reservando presupuesto para aperitivos extra..." crlf)
        (bind ?presupuesto-aperitivos (* ?presupuesto-total 0.2))
        (bind ?presupuesto-menu (- ?presupuesto-total ?presupuesto-aperitivos))

        ; VERIFICAR SI HAY PRESUPUESTO SUFICIENTE DESPUÉS DE APERITIVOS
        (if (> ?presupuesto-menu ?min) then
            (printout t "      ✅ Presupuesto suficiente, incluyendo aperitivos" crlf)
            
            (bind ?modo-boda? TRUE)
        else
            (printout t "      ⚠️  Presupuesto insuficiente para aperitivos, creando menú normal" crlf)
            (printout t "         Necesita: >" ?min "€ | Disponible: " ?presupuesto-menu "€" crlf)
            (bind ?presupuesto-menu ?presupuesto-total)
            (bind ?modo-boda? FALSE)
        )
    )
    
    ; PASO 2: Buscar combinación válida con el presupuesto restante, SIN aperitivos
    (bind ?menu-normal (buscar-combinacion-valida ?min ?presupuesto-menu (create$)))
    
    ; SI FALLA EL INTENTO NORMAL, INTENTAR VERSIÓN RELAJADA
    (if (eq ?menu-normal FALSE) then
        (printout t "      ⚠️  No se pudo crear menú con restricciones estrictas, intentando versión relajada..." crlf)
        (bind ?menu-normal (buscar-combinacion-valida-relajada ?min ?presupuesto-menu (create$)))
    )
    
    (if (neq ?menu-normal FALSE) then
        (bind ?entrante (nth$ 1 ?menu-normal))
        (bind ?principal (nth$ 2 ?menu-normal))
        (bind ?postre (nth$ 3 ?menu-normal))
        (bind ?precio-base (nth$ 4 ?menu-normal))
        
        ; PASO 3: Si es boda, buscar aperitivos que no dupliquen con la combinación encontrada (solo si se puede)
        (if (and (eq ?event-type wedding) (eq ?modo-boda? TRUE)) then
            (bind ?aperitivos-extra (buscar-aperitivos-extra-wedding-con-combinacion ?presupuesto-aperitivos ?entrante ?principal ?postre))
            ; Calcular costo real de los aperitivos
            (foreach ?a ?aperitivos-extra
                (bind ?costo-aperitivos (+ ?costo-aperitivos (send ?a get-price))))
            (printout t "      Aperitivos seleccionados: " (length$ ?aperitivos-extra) " (costo: " ?costo-aperitivos "€)" crlf)
        )
        
        (bind ?precio-total (+ ?precio-base ?costo-aperitivos))
        
        ; Crear menú completo
        (assert (menu-completo 
            (categoria barato)
            (entrante ?entrante)
            (principal ?principal)
            (postre ?postre)
            (aperitivos-extra ?aperitivos-extra)
            (precio-base ?precio-base)
            (precio-total ?precio-total)))
        
        (printout t "     ✅ MENÚ BARATO CREADO: " ?precio-total "€" 
                 (if (> ?costo-aperitivos 0) then (str-cat " (incluye " (length$ ?aperitivos-extra) " aperitivos extra)") else "") 
                    crlf)
    else
        (printout t "     ❌ No se pudo crear menú barato con las especificaciones actuales" crlf)
        ; Crear un menú vacío para evitar que la regla se reactive
        ;(assert (menu-completo (categoria barato)))
    )
)

(defrule REFINAMIENTO::crear-menu-medio
    (declare (salience 80))
    ?limites <- (limites-calculados 
        (min-price ?min) 
        (limite-barato ?limBarato)
        (limite-medio ?limMedio) 
        (max-price ?max))
    ?user <- (user-restrictions (event-type ?event-type) (quiere-tarta ?quiere-tarta))
    (not (menu-completo (categoria medio)))
    =>
    (printout t crlf "BUSCANDO MENÚ MEDIO (" ?limBarato "€ - " ?limMedio "€)..." crlf)
    
    (bind ?presupuesto-total ?limMedio)
    (bind ?presupuesto-menu ?limMedio)
    (bind ?aperitivos-extra (create$))
    (bind ?costo-aperitivos 0.0)
    
    ; PASO 1: Si es boda, reservar 20% para aperitivos extra
    (if (eq ?event-type wedding) then
        (printout t "      Reservando presupuesto para aperitivos extra..." crlf)
        (bind ?presupuesto-aperitivos (* ?presupuesto-total 0.2))
        (bind ?presupuesto-menu (- ?presupuesto-total ?presupuesto-aperitivos))

        (if (> ?presupuesto-menu ?limBarato) then
            (printout t "      ✅ Presupuesto suficiente, incluyendo aperitivos" crlf)
            
            (bind ?modo-boda? TRUE)
        else
            (printout t "      ⚠️  Presupuesto insuficiente para aperitivos, creando menú normal" crlf)
            (printout t "         Necesita: >" ?limBarato "€ | Disponible: " ?presupuesto-menu "€" crlf)
            (bind ?presupuesto-menu ?presupuesto-total)
            (bind ?modo-boda? FALSE)
        )
    )
    
    ; PASO 2: Buscar combinación válida con el presupuesto restante, SIN aperitivos
    (bind ?menu-normal (buscar-combinacion-valida ?limBarato ?presupuesto-menu (create$)))
    
    ; SI FALLA EL INTENTO NORMAL, INTENTAR VERSIÓN RELAJADA
    (if (eq ?menu-normal FALSE) then
        (printout t "      ⚠️  No se pudo crear menú con restricciones estrictas, intentando versión relajada..." crlf)
        (bind ?menu-normal (buscar-combinacion-valida-relajada ?limBarato ?presupuesto-menu (create$)))
    )
    
    (if (neq ?menu-normal FALSE) then
        (bind ?entrante (nth$ 1 ?menu-normal))
        (bind ?principal (nth$ 2 ?menu-normal))
        (bind ?postre (nth$ 3 ?menu-normal))
        (bind ?precio-base (nth$ 4 ?menu-normal))
        
        ; PASO 3: Si es boda, buscar aperitivos que no dupliquen con la combinación encontrada
        (if (and (eq ?event-type wedding) (eq ?modo-boda? TRUE)) then
            (bind ?aperitivos-extra (buscar-aperitivos-extra-wedding-con-combinacion ?presupuesto-aperitivos ?entrante ?principal ?postre))
            ; Calcular costo real de los aperitivos
            (foreach ?a ?aperitivos-extra
                (bind ?costo-aperitivos (+ ?costo-aperitivos (send ?a get-price))))
            (printout t "      Aperitivos seleccionados: " (length$ ?aperitivos-extra) " (costo: " ?costo-aperitivos "€)" crlf)
        )
        
        (bind ?precio-total (+ ?precio-base ?costo-aperitivos))
        
        ; Crear menú completo
        (assert (menu-completo 
            (categoria medio)
            (entrante ?entrante)
            (principal ?principal)
            (postre ?postre)
            (aperitivos-extra ?aperitivos-extra)
            (precio-base ?precio-base)
            (precio-total ?precio-total)))
        
        (printout t "     ✅ MENÚ MEDIO CREADO: " ?precio-total "€" 
                 (if (> ?costo-aperitivos 0) then (str-cat " (incluye " (length$ ?aperitivos-extra) " aperitivos extra)") else "") 
                crlf)
    else
        (printout t "     ❌ No se pudo crear menú medio con las especificaciones actuales" crlf)
        ; Crear un menú vacío para evitar que la regla se reactive
        ;(assert (menu-completo (categoria medio)))
    )
)

(defrule REFINAMIENTO::crear-menu-caro
    (declare (salience 70))
    ?limites <- (limites-calculados 
        (min-price ?min) 
        (limite-barato ?limBarato)
        (limite-medio ?limMedio) 
        (max-price ?max))
    ?user <- (user-restrictions (event-type ?event-type) (quiere-tarta ?quiere-tarta))
    (not (menu-completo (categoria caro)))
    =>
    (printout t crlf "BUSCANDO MENÚ CARO (≥ " ?limMedio "€)..." crlf)
    
    (bind ?presupuesto-total ?max)
    (bind ?presupuesto-menu ?max)
    (bind ?aperitivos-extra (create$))
    (bind ?costo-aperitivos 0.0)
    
    ; PASO 1: Si es boda, reservar 20% para aperitivos extra
    (if (eq ?event-type wedding) then
        (printout t "      Reservando presupuesto para aperitivos extra..." crlf)
        (bind ?presupuesto-aperitivos (* ?presupuesto-total 0.2))
        (bind ?presupuesto-menu (- ?presupuesto-total ?presupuesto-aperitivos))

        ; VERIFICAR SI HAY PRESUPUESTO SUFICIENTE DESPUÉS DE APERITIVOS
        (if (> ?presupuesto-menu ?limMedio) then
            (printout t "      ✅ Presupuesto suficiente, incluyendo aperitivos" crlf)
            
            (bind ?modo-boda? TRUE)
        else
            (printout t "      ⚠️  Presupuesto insuficiente para aperitivos, creando menú normal" crlf)
            (printout t "         Necesita: >" ?limMedio "€ | Disponible: " ?presupuesto-menu "€" crlf)
            (bind ?presupuesto-menu ?presupuesto-total)
            (bind ?modo-boda? FALSE)
        )
    )
    
    ; PASO 2: Buscar combinación válida con el presupuesto restante, SIN aperitivos
    (bind ?menu-normal (buscar-combinacion-valida ?limMedio ?presupuesto-menu (create$)))
    
    ; SI FALLA EL INTENTO NORMAL, INTENTAR VERSIÓN RELAJADA
    (if (eq ?menu-normal FALSE) then
        (printout t "      ⚠️  No se pudo crear menú con restricciones estrictas, intentando versión relajada..." crlf)
        (bind ?menu-normal (buscar-combinacion-valida-relajada ?limMedio ?presupuesto-menu (create$)))
    )
    
    (if (neq ?menu-normal FALSE) then
        (bind ?entrante (nth$ 1 ?menu-normal))
        (bind ?principal (nth$ 2 ?menu-normal))
        (bind ?postre (nth$ 3 ?menu-normal))
        (bind ?precio-base (nth$ 4 ?menu-normal))
        
        ; PASO 3: Si es boda, buscar aperitivos que no dupliquen con la combinación encontrada
        (if (and (eq ?event-type wedding) (eq ?modo-boda? TRUE)) then
            (bind ?aperitivos-extra (buscar-aperitivos-extra-wedding-con-combinacion ?presupuesto-aperitivos ?entrante ?principal ?postre))
            ; Calcular costo real de los aperitivos
            (foreach ?a ?aperitivos-extra
                (bind ?costo-aperitivos (+ ?costo-aperitivos (send ?a get-price))))
            (printout t "      Aperitivos seleccionados: " (length$ ?aperitivos-extra) " (costo: " ?costo-aperitivos "€)" crlf)
        )
        
        (bind ?precio-total (+ ?precio-base ?costo-aperitivos))
        
        ; Crear menú completo
        (assert (menu-completo 
            (categoria caro)
            (entrante ?entrante)
            (principal ?principal)
            (postre ?postre)
            (aperitivos-extra ?aperitivos-extra)
            (precio-base ?precio-base)
            (precio-total ?precio-total)))
        
        (printout t "     ✅ MENÚ CARO CREADO: " ?precio-total "€" 
                 (if (> ?costo-aperitivos 0) then (str-cat " (incluye " (length$ ?aperitivos-extra) " aperitivos extra)") else "") 
                crlf)
    else
        (printout t "     ❌ No se pudo crear menú caro con las especificaciones actuales" crlf)
        ; Crear un menú vacío para evitar que la regla se reactive
        ;(assert (menu-completo (categoria caro)))
    )
)


; ;;; Mostrar resultados finales

(defrule REFINAMIENTO::mostrar-resultados-finales
    (declare (salience -100))
    =>
    (printout t crlf "========================================" crlf)
    (printout t "📊 RESUMEN FINAL DE MENÚS" crlf)
    (printout t "========================================" crlf)
    
    (bind ?barato (if (> (length$ (find-all-facts ((?m menu-completo)) (eq ?m:categoria barato))) 0) 
                     then "✅" else "❌"))
    (bind ?medio (if (> (length$ (find-all-facts ((?m menu-completo)) (eq ?m:categoria medio))) 0)
                    then "✅" else "❌"))
    (bind ?caro (if (> (length$ (find-all-facts ((?m menu-completo)) (eq ?m:categoria caro))) 0)
                   then "✅" else "❌"))
    
    (printout t "Barato: " ?barato " | Medio: " ?medio " | Caro: " ?caro crlf crlf)
    
    ;;; Mostrar detalles de cada menú creado
    (bind ?menus-baratos (find-all-facts ((?m menu-completo)) (eq ?m:categoria barato)))
    (if (> (length$ ?menus-baratos) 0) then
        (printout t "🍽️  MENÚ BARATO:" crlf)
        (foreach ?m ?menus-baratos
            (mostrar-detalles-menu ?m)))

    (bind ?menus-medios (find-all-facts ((?m menu-completo)) (eq ?m:categoria medio)))
    (if (> (length$ ?menus-medios) 0) then
        (printout t "🍽️  MENÚ MEDIO:" crlf)
        (foreach ?m ?menus-medios
            (mostrar-detalles-menu ?m)))

    (bind ?menus-caros (find-all-facts ((?m menu-completo)) (eq ?m:categoria caro)))
    (if (> (length$ ?menus-caros) 0) then
        (printout t "🍽️  MENÚ CARO:" crlf)
        (foreach ?m ?menus-caros
            (mostrar-detalles-menu ?m)))
            
    (if (and (= (length$ ?menus-baratos) 0) 
             (= (length$ ?menus-medios) 0) 
             (= (length$ ?menus-caros) 0)) then
        (printout t "❌ No se pudo crear ningún menú" crlf))
)

