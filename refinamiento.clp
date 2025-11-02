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

(deffunction REFINAMIENTO::calc-intervalo () 
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




;;; Busca combinaciones válidas de platos (verifica duplicados entre menús)
(deffunction REFINAMIENTO::buscar-combinacion-valida (?precio-min ?precio-max ?aperitivos-extra)
    
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
    (bind ?categoria (fact-slot-value ?m categoria))
    (bind ?precio-base (fact-slot-value ?m precio-base))
    (bind ?precio-total (fact-slot-value ?m precio-total))
    
    ;;; ═══════════════════════════════════════════════════════════════════════
    ;;; CABECERA ARTÍSTICA DEL MENÚ
    ;;; ═══════════════════════════════════════════════════════════════════════
    (printout t "    " crlf)
    (printout t "    ╔══════════════════════════════════════════════════════════════╗" crlf)
    (printout t "    ║                                                              ║" crlf)
    (printout t "    ║           ✨ 🍽️  M E N Ú   G O U R M E T  🍽️ ✨            ║" crlf)
    (printout t "    ║                                                              ║" crlf)
    (printout t "    ╠══════════════════════════════════════════════════════════════╣" crlf)
    
    ;;; Categoría del menú con iconos específicos
    (if (eq ?categoria barato) then
        (printout t "    ║  💰 Categoría: MENÚ ECONÓMICO                               ║" crlf)
    )
    (if (eq ?categoria medio) then
        (printout t "    ║  🌟 Categoría: MENÚ SELECTO                                 ║" crlf)
    )
    (if (eq ?categoria caro) then
        (printout t "    ║  👑 Categoría: MENÚ PREMIUM EXCLUSIVO                       ║" crlf)
    )
    
    ;;; Tipo de evento con emojis temáticos
    (printout t "    ║                                                              ║" crlf)
    (if (eq ?event-type wedding) then
        (printout t "    ║  💐💍 Ocasión: CELEBRACIÓN DE BODA 💍💐                     ║" crlf)
    )
    (if (eq ?event-type family) then
        (printout t "    ║  👨‍👩‍👧‍👦 Ocasión: REUNIÓN FAMILIAR 🏠                          ║" crlf)
    )
    (if (eq ?event-type friends) then
        (printout t "    ║  🎉🥳 Ocasión: ENCUENTRO ENTRE AMIGOS 🎊                    ║" crlf)
    )
    
    (printout t "    ║                                                              ║" crlf)
    (printout t "    ╠══════════════════════════════════════════════════════════════╣" crlf)
    (printout t "    ║                                                              ║" crlf)
    (format t "      ║  💵 Precio base del menú  : %8.2f €                          ║%n" ?precio-base)
    (format t "      ║  💎 PRECIO TOTAL          : %8.2f €                          ║%n" ?precio-total)
    (printout t "    ║                                                              ║" crlf)
    (printout t "    ╚══════════════════════════════════════════════════════════════╝" crlf)
    (printout t crlf)

    ;;; ═══════════════════════════════════════════════════════════════════════
    ;;; APERITIVOS EXTRA (SOLO PARA BODAS)
    ;;; ═══════════════════════════════════════════════════════════════════════
    (bind ?aperitivos-extra (fact-slot-value ?m aperitivos-extra))
    (if (and (eq ?event-type wedding) (> (length$ ?aperitivos-extra) 0)) then
        (printout t "    ┌──────────────────────────────────────────────────────────────┐" crlf)
        (printout t "    │                                                              │" crlf)
        (printout t "    │          🍢  A P E R I T I V O S   E X T R A  🍢            │" crlf)
        (printout t "    │              ～ Para comenzar con estilo ～                  │" crlf)
        (printout t "    │                                                              │" crlf)
        (printout t "    └──────────────────────────────────────────────────────────────┘" crlf)
        (printout t crlf)
        (foreach ?a ?aperitivos-extra
            (printout t "         🔸 " (send ?a get-title) crlf)
            (format t "            💰 %.2f €%n" (send ?a get-price))
            (printout t crlf))
        (printout t "    ～ ～ ～ ～ ～ ～ ～ ～ ～ ～ ～ ～ ～ ～ ～ ～ ～ ～ ～ ～" crlf)
        (printout t crlf)
    )

    ;;; ═══════════════════════════════════════════════════════════════════════
    ;;; ENTRANTE / PRIMER PLATO
    ;;; ═══════════════════════════════════════════════════════════════════════
    (bind ?entrante-inst (fact-slot-value ?m entrante))
    (printout t "    ┌──────────────────────────────────────────────────────────────┐" crlf)
    (printout t "    │                                                              │" crlf)
    (printout t "    │            🥗  P R I M E R   P L A T O  🥗                  │" crlf)
    (printout t "    │                                                              │" crlf)
    (printout t "    └──────────────────────────────────────────────────────────────┘" crlf)
    (printout t crlf)
    (printout t "         ✦ " (send ?entrante-inst get-title) crlf)
    (format t "            💰 %.2f €%n" (send ?entrante-inst get-price))
    (printout t crlf)
    (printout t "         ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" crlf)
    (printout t "         📝 Descripción:" crlf)
    (printout t "            " (send ?entrante-inst get-explanation) crlf)
    (printout t "         ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" crlf)
    (printout t crlf)
    (printout t "    ～ ～ ～ ～ ～ ～ ～ ～ ～ ～ ～ ～ ～ ～ ～ ～ ～ ～ ～ ～" crlf)
    (printout t crlf)

    ;;; ═══════════════════════════════════════════════════════════════════════
    ;;; PLATO PRINCIPAL
    ;;; ═══════════════════════════════════════════════════════════════════════
    (bind ?principal-inst (fact-slot-value ?m principal))
    (printout t "    ┌──────────────────────────────────────────────────────────────┐" crlf)
    (printout t "    │                                                              │" crlf)
    (printout t "    │         🍽️  P L A T O   P R I N C I P A L  🍽️               │" crlf)
    (printout t "    │              ～ El corazón del menú ～                       │" crlf)
    (printout t "    │                                                              │" crlf)
    (printout t "    └──────────────────────────────────────────────────────────────┘" crlf)
    (printout t crlf)
    (printout t "         ✦ " (send ?principal-inst get-title) crlf)
    (format t "            💰 %.2f €%n" (send ?principal-inst get-price))
    (printout t crlf)
    (printout t "         ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" crlf)
    (printout t "         📝 Descripción:" crlf)
    (printout t "            " (send ?principal-inst get-explanation) crlf)
    (printout t "         ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" crlf)
    (printout t crlf)
    
    ;;; Vino recomendado con copa decorativa
    (bind ?vino-principal (send ?principal-inst get-wine_pairing))
    (printout t "         🍷 ══════════════════════════════════════════════" crlf)
    (if (and (neq ?vino-principal "") (neq ?vino-principal "No wine pairing")) then
        (printout t "            🍇 Maridaje sugerido: " ?vino-principal crlf)
    else
        (printout t "            🍇 Maridaje: A su elección, todos armonizan" crlf)
    )
    (printout t "         ══════════════════════════════════════════════════" crlf)
    (printout t crlf)
    (printout t "    ～ ～ ～ ～ ～ ～ ～ ～ ～ ～ ～ ～ ～ ～ ～ ～ ～ ～ ～ ～" crlf)
    (printout t crlf)

    ;;; ═══════════════════════════════════════════════════════════════════════
    ;;; POSTRE / DULCE FINAL
    ;;; ═══════════════════════════════════════════════════════════════════════
    (bind ?postre-inst (fact-slot-value ?m postre))
    (printout t "    ┌──────────────────────────────────────────────────────────────┐" crlf)
    (printout t "    │                                                              │" crlf)
    (printout t "    │              🍰  D U L C E   F I N A L  🍰                  │" crlf)
    (printout t "    │              ～ El broche perfecto ～                        │" crlf)
    (printout t "    │                                                              │" crlf)
    (printout t "    └──────────────────────────────────────────────────────────────┘" crlf)
    (printout t crlf)
    (printout t "         ✦ " (send ?postre-inst get-title) crlf)
    (format t "            💰 %.2f €%n" (send ?postre-inst get-price))
    (printout t crlf)
    (printout t "         ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" crlf)
    (printout t "         📝 Descripción:" crlf)
    (printout t "            " (send ?postre-inst get-explanation) crlf)
    (printout t "         ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" crlf)
    (printout t crlf)
    (printout t "    ～ ～ ～ ～ ～ ～ ～ ～ ～ ～ ～ ～ ～ ～ ～ ～ ～ ～ ～ ～" crlf)
    (printout t crlf)

    ;;; ═══════════════════════════════════════════════════════════════════════
    ;;; PLUS OPCIONAL: TARTA ESPECIAL
    ;;; ═══════════════════════════════════════════════════════════════════════
    (if (eq ?quiere-tarta TRUE) then 
        (printout t "    ┌──────────────────────────────────────────────────────────────┐" crlf)
        (printout t "    │                                                              │" crlf)
        (printout t "    │           🎂  P L U S   E S P E C I A L  🎂                 │" crlf)
        (printout t "    │                                                              │" crlf)
        (printout t "    └──────────────────────────────────────────────────────────────┘" crlf)
        (printout t crlf)
        (if (eq ?event-type wedding) then
            (printout t "         🌸 Tarta de boda personalizada disponible" crlf)
            (printout t "            ✨ Diseño exclusivo para su día especial" crlf)
            (printout t "            💰 +200.00 € (no incluido en el precio base)" crlf)
        else 
            (if (eq ?event-type family) then
                (printout t "         🎈 Tarta familiar especial disponible" crlf)
                (printout t "            ✨ Perfecta para celebraciones íntimas" crlf)
                (printout t "            💰 +50.00 € (no incluido en el precio base)" crlf)
            else
                (printout t "         🎁 Tarta disponible bajo consulta" crlf)
                (printout t "            ✨ Precio según especificaciones" crlf)
            )
        )
        (printout t crlf)
        (printout t "    ～ ～ ～ ～ ～ ～ ～ ～ ～ ～ ～ ～ ～ ～ ～ ～ ～ ～ ～ ～" crlf)
        (printout t crlf)
    )

    ;;; ═══════════════════════════════════════════════════════════════════════
    ;;; BEBIDAS INCLUIDAS
    ;;; ═══════════════════════════════════════════════════════════════════════
    (bind ?bebidas-sugeridas (sugerir-bebidas ?m))
    (printout t "    ┌──────────────────────────────────────────────────────────────┐" crlf)
    (printout t "    │                                                              │" crlf)
    (printout t "    │          🥤  B E B I D A S   I N C L U I D A S  🥤          │" crlf)
    (printout t "    │                                                              │" crlf)
    (printout t "    └──────────────────────────────────────────────────────────────┘" crlf)
    (printout t crlf)
    (printout t "         💧 Selección disponible:" crlf)
    (printout t "            " (implode$ ?bebidas-sugeridas) crlf)
    (printout t crlf)
    (printout t "    ════════════════════════════════════════════════════════════" crlf)
    (printout t crlf)
    
    ;;; ═══════════════════════════════════════════════════════════════════════
    ;;; PIE DE MENÚ CON PRECIO TOTAL DESTACADO
    ;;; ═══════════════════════════════════════════════════════════════════════
    (printout t "    ╔══════════════════════════════════════════════════════════════╗" crlf)
    (printout t "    ║                                                              ║" crlf)
    (format t "      ║          💎 PRECIO TOTAL DEL MENÚ: %8.2f €                   ║%n" ?precio-total)
    (printout t "    ║                                                              ║" crlf)
    (printout t "    ║         ✨ IVA incluido | Servicio de calidad ✨            ║" crlf)
    (printout t "    ║                                                              ║" crlf)
    (printout t "    ╚══════════════════════════════════════════════════════════════╝" crlf)
    (printout t crlf)
    (printout t "    ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★" crlf)
    (printout t crlf)
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
        
    )
)


; ;;; Mostrar resultados finales

(defrule REFINAMIENTO::mostrar-resultados-finales
    (declare (salience -100))
    =>
    (bind ?barato (if (> (length$ (find-all-facts ((?m menu-completo)) (eq ?m:categoria barato))) 0) 
                     then "✅" else "❌"))
    (bind ?medio (if (> (length$ (find-all-facts ((?m menu-completo)) (eq ?m:categoria medio))) 0)
                    then "✅" else "❌"))
    (bind ?caro (if (> (length$ (find-all-facts ((?m menu-completo)) (eq ?m:categoria caro))) 0)
                   then "✅" else "❌"))

    (printout t crlf crlf)
    (printout t "╔══════════════════════════════════════════════════════════════════════════╗" crlf)
    (printout t "║                                                                          ║" crlf)
    (printout t "║    ��🎉🎊  ═════════════════════════════════════════  🎊🎉🎊         ║" crlf)
    (printout t "║                                                                          ║" crlf)
    (printout t "║           ✨✨  R E S U M E N   F I N A L   D E   M E N Ú S  ✨✨      ║" crlf)
    (printout t "║                                                                          ║" crlf)
    (printout t "║    ��🎉🎊  ═════════════════════════════════════════  🎊🎉🎊         ║" crlf)
    (printout t "║                                                                          ║" crlf)
    (printout t "╠══════════════════════════════════════════════════════════════════════════╣" crlf)
    (printout t "║                                                                          ║" crlf)
    (format t   "║      📋 Estado de disponibilidad:                                        ║%n")
    (printout t "║                                                                          ║" crlf)
    (format t "  ║         💰 Menú Económico  : %-3s                                        ║%n" ?barato)
    (format t "  ║         🌟 Menú Selecto    : %-3s                                        ║%n" ?medio)
    (format t "  ║         👑 Menú Premium    : %-3s                                        ║%n" ?caro)
    (printout t "║                                                                          ║" crlf)
    (printout t "╚══════════════════════════════════════════════════════════════════════════╝" crlf)
    (printout t crlf crlf)
    
    ;;; Mostrar detalles de cada menú creado con separadores artísticos
    (bind ?menus-baratos (find-all-facts ((?m menu-completo)) (eq ?m:categoria barato)))
    (if (> (length$ ?menus-baratos) 0) then
        (printout t "╔═══════════════════════════════════════════════════════════════════════════╗" crlf)
        (printout t "║                                                                           ║" crlf)
        (printout t "║         💰💰  M E N Ú   E C O N Ó M I C O  💰💰                         ║" crlf)
        (printout t "║                 ～ Calidad excepcional, precio accesible ～               ║" crlf)
        (printout t "║                                                                           ║" crlf)
        (printout t "╚═══════════════════════════════════════════════════════════════════════════╝" crlf)
        (printout t crlf)
        (foreach ?m ?menus-baratos
            (mostrar-detalles-menu ?m)))

    (bind ?menus-medios (find-all-facts ((?m menu-completo)) (eq ?m:categoria medio)))
    (if (> (length$ ?menus-medios) 0) then
        (printout t "╔═══════════════════════════════════════════════════════════════════════════╗" crlf)
        (printout t "║                                                                           ║" crlf)
        (printout t "║            🌟🌟  M E N Ú   S E L E C T O  🌟🌟                          ║" crlf)
        (printout t "║                 ～ La elección perfecta para el disfrute ～               ║" crlf)
        (printout t "║                                                                           ║" crlf)
        (printout t "╚═══════════════════════════════════════════════════════════════════════════╝" crlf)
        (printout t crlf)
        (foreach ?m ?menus-medios
            (mostrar-detalles-menu ?m)))

    (bind ?menus-caros (find-all-facts ((?m menu-completo)) (eq ?m:categoria caro)))
    (if (> (length$ ?menus-caros) 0) then
        (printout t "╔═══════════════════════════════════════════════════════════════════════════╗" crlf)
        (printout t "║                                                                           ║" crlf)
        (printout t "║        👑👑  M E N Ú   P R E M I U M   E X C L U S I V O  👑👑          ║" crlf)
        (printout t "║              ～ La experiencia culinaria definitiva ～                    ║" crlf)
        (printout t "║                                                                           ║" crlf)
        (printout t "╚═══════════════════════════════════════════════════════════════════════════╝" crlf)
        (printout t crlf)
        (foreach ?m ?menus-caros
            (mostrar-detalles-menu ?m)))
            
    (if (and (= (length$ ?menus-baratos) 0) 
             (= (length$ ?menus-medios) 0) 
             (= (length$ ?menus-caros) 0)) then
        (printout t crlf)
        (printout t "    ╔══════════════════════════════════════════════════════════════╗" crlf)
        (printout t "    ║                                                              ║" crlf)
        (printout t "    ║    ❌  Lo sentimos, no se pudo generar ningún menú  ❌      ║" crlf)
        (printout t "    ║                                                              ║" crlf)
        (printout t "    ║         Por favor, revise los criterios de búsqueda          ║" crlf)
        (printout t "    ║                                                              ║" crlf)
        (printout t "    ╚══════════════════════════════════════════════════════════════╝" crlf)
        (printout t crlf))
    
    ;;; Banner de cierre final
    (printout t crlf)
    (printout t "╔═══════════════════════════════════════════════════════════════════════════╗" crlf)
    (printout t "║                                                                           ║" crlf)
    (printout t "║                  ✨ Gracias por utilizar nuestro servicio ✨             ║" crlf)
    (printout t "║                                                                           ║" crlf)
    (printout t "║              🍽️  ¡Que disfrute de su experiencia culinaria!  🍽️          ║" crlf)
    (printout t "║                                                                           ║" crlf)
    (printout t "╚═══════════════════════════════════════════════════════════════════════════╝" crlf)
    (printout t crlf)
    (printout t "    ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★ ★" crlf)
    (printout t crlf crlf)
)

