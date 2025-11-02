;;═══════════════════════════════════════════════════════════════════════════
;;  🌟✨ MÓDULO DE EXPERIENCIA GASTRONÓMICA DE ÉLITE ✨🌟
;;═══════════════════════════════════════════════════════════════════════════
;;
;;     Bienvenido al sistema de reservas del restaurante más exclusivo
;;          donde cada detalle cuenta una historia culinaria
;;
;;═══════════════════════════════════════════════════════════════════════════

(defmodule input
   (export ?ALL) ; exporta todas las reglas, funciones y templates
)

(defrule MAIN::start-input
   =>
   (focus input))

;;═══════════════════════════════════════════════════════════════════════════
;; 📋 PLANTILLAS DE DATOS EXCLUSIVOS
;;═══════════════════════════════════════════════════════════════════════════

(deftemplate input::user-restrictions
   (multislot requested (type SYMBOL) (default-dynamic (create$)))
   (slot max-people (type NUMBER) (default 100))
   (slot max-price (type NUMBER) (default 1000))
   (slot min-price (type NUMBER) (default 0))
   (slot event-type (type SYMBOL) (default unknown-event))
   (slot season (type SYMBOL) (default any-season))
   (slot quiere-tarta (type SYMBOL) (default FALSE))
)

;;═══════════════════════════════════════════════════════════════════════════
;; 🎯 FUNCIÓN DE SOLICITUD NUMÉRICA ELEGANTE
;;═══════════════════════════════════════════════════════════════════════════

(deffunction input::prompt-number (?prompt ?minimum)
   (printout t "    " ?prompt)
   (bind ?value (read))
   (while (or (not (numberp ?value)) (< ?value ?minimum))
      (printout t "    ⚠️  Por favor, ingrese un valor numérico ≥ " ?minimum crlf crlf)
      (printout t "    " ?prompt)
      (bind ?value (read)))
   (return ?value))

;;═══════════════════════════════════════════════════════════════════════════
;; 🎭 EXPERIENCIA INTERACTIVA DE RESERVA PREMIUM
;;═══════════════════════════════════════════════════════════════════════════

(defrule input::request-data
   =>
   
   ;;═══════════════════════════════════════════════════════════════════════════
   ;; 🎨 BANNER DE BIENVENIDA EXCLUSIVO
   ;;═══════════════════════════════════════════════════════════════════════════
   (printout t crlf crlf)
   (printout t "╔═══════════════════════════════════════════════════════════════════════════╗" crlf)
   (printout t "║                                                                           ║" crlf)
   (printout t "║    ✨🍽️✨  ══════════════════════════════════════════  ✨🍽️✨         ║" crlf)
   (printout t "║                                                                           ║" crlf)
   (printout t "║           🌟  B I E N V E N I D O   A   L A   É L I T E  🌟             ║" crlf)
   (printout t "║                                                                           ║" crlf)
   (printout t "║              Sistema de Menús Gastronómicos de Alta Cocina               ║" crlf)
   (printout t "║                                                                           ║" crlf)
   (printout t "║    ✨🍽️✨  ══════════════════════════════════════════  ✨🍽️✨         ║" crlf)
   (printout t "║                                                                           ║" crlf)
   (printout t "╚═══════════════════════════════════════════════════════════════════════════╝" crlf)
   (printout t crlf)
   (printout t "    Permítanos conocer sus preferencias para crear una experiencia" crlf)
   (printout t "    culinaria inolvidable, diseñada exclusivamente para usted." crlf)
   (printout t crlf)
   (printout t "    ═══════════════════════════════════════════════════════════════════════" crlf)
   (printout t crlf crlf)
   
   ;;═══════════════════════════════════════════════════════════════════════════
   ;; 🎊 PASO 1: TIPO DE CELEBRACIÓN
   ;;═══════════════════════════════════════════════════════════════════════════
   (printout t "    ╔═══════════════════════════════════════════════════════════════════╗" crlf)
   (printout t "    ║                                                                   ║" crlf)
   (printout t "    ║         🎊  PASO 1: Su Ocasión Especial  🎊                      ║" crlf)
   (printout t "    ║                                                                   ║" crlf)
   (printout t "    ╚═══════════════════════════════════════════════════════════════════╝" crlf)
   (printout t crlf)
   (printout t "    ¿Qué tipo de evento desea celebrar?" crlf)
   (printout t "    " crlf)
   (printout t "        💍  wedding  → Boda inolvidable" crlf)
   (printout t "        🎤  congress → Evento corporativo de prestigio" crlf)
   (printout t "        👨‍👩‍👧‍👦  family   → Reunión familiar íntima" crlf)
   (printout t crlf)
   (printout t "    📝 Ingrese su elección: ")
   (bind ?type-token (read))
   (bind ?event-type (string-to-field (lowcase (str-cat ?type-token))))
   
   ;;═══════════════════════════════════════════════════════════════════════════
   ;; 🎂 TARTA ESPECIAL (si aplica)
   ;;═══════════════════════════════════════════════════════════════════════════
   (if (or(eq ?event-type wedding) (eq ?event-type family)) then
      (printout t crlf)
      (printout t "    ┌─────────────────────────────────────────────────────────────────┐" crlf)
      (printout t "    │  🎂 ¿Desea incluir una tarta especial para la ocasión?         │" crlf)
      (printout t "    └─────────────────────────────────────────────────────────────────┘" crlf)
      (printout t crlf)
      (printout t "    📝 (yes/no): ")
      (bind ?cake-token (read))
      (bind ?cake-response (lowcase (str-cat ?cake-token)))
      (if (eq ?cake-response "yes") then
         (bind ?quiere-tarta TRUE)
         (printout t "    ✅ ¡Excelente elección! Incluiremos una tarta artesanal." crlf)
         else
         (bind ?quiere-tarta FALSE)
         (printout t "    ℹ️  De acuerdo, sin tarta adicional." crlf))
      else 
      (bind ?quiere-tarta FALSE))
   
   (printout t crlf)
   (printout t "    ═══════════════════════════════════════════════════════════════════════" crlf)
   (printout t crlf crlf)
   
   ;;═══════════════════════════════════════════════════════════════════════════
   ;; 👥 PASO 2: NÚMERO DE COMENSALES
   ;;═══════════════════════════════════════════════════════════════════════════
   (printout t "    ╔═══════════════════════════════════════════════════════════════════╗" crlf)
   (printout t "    ║                                                                   ║" crlf)
   (printout t "    ║         👥  PASO 2: Número de Invitados  👥                      ║" crlf)
   (printout t "    ║                                                                   ║" crlf)
   (printout t "    ╚═══════════════════════════════════════════════════════════════════╝" crlf)
   (printout t crlf)
   (bind ?max-people (prompt-number "📝 Cantidad máxima de personas (≥1): " 1))
   (printout t "    ✅ Perfecto, prepararemos todo para " ?max-people " invitados." crlf)
   (printout t crlf)
   (printout t "    ═══════════════════════════════════════════════════════════════════════" crlf)
   (printout t crlf crlf)

   ;;═══════════════════════════════════════════════════════════════════════════
   ;; 🌸 PASO 3: TEMPORADA DEL AÑO
   ;;═══════════════════════════════════════════════════════════════════════════
   (printout t "    ╔═══════════════════════════════════════════════════════════════════╗" crlf)
   (printout t "    ║                                                                   ║" crlf)
   (printout t "    ║         🌸  PASO 3: Estación del Año  🌸                         ║" crlf)
   (printout t "    ║                                                                   ║" crlf)
   (printout t "    ╚═══════════════════════════════════════════════════════════════════╝" crlf)
   (printout t crlf)
   (printout t "    Nuestros menús se adaptan a la temporada para garantizar" crlf)
   (printout t "    ingredientes frescos y de la más alta calidad." crlf)
   (printout t crlf)
   (printout t "        🌷  spring  → Primavera (ingredientes frescos y ligeros)" crlf)
   (printout t "        ☀️  summer  → Verano (platos refrescantes)" crlf)
   (printout t "        🍂  autumn  → Otoño (sabores cálidos y terrosos)" crlf)
   (printout t "        ❄️  winter  → Invierno (cocina reconfortante)" crlf)
   (printout t "        🌍  any     → Cualquier temporada (sin preferencia)" crlf)
   (printout t crlf)
   (printout t "    📝 Estación preferida: ")
   (bind ?season-token (read))
   (bind ?season-string (lowcase (str-cat ?season-token)))
   (if (or (eq ?season-string "") (eq ?season-string "any")) then
      (bind ?season-string "any-season")
      (printout t "    ℹ️  Sin preferencia estacional, perfecto." crlf)
      else
      (printout t "    ✅ Excelente, adaptaremos el menú a la temporada " ?season-string "." crlf))
   (bind ?season (string-to-field ?season-string))
   (printout t crlf)
   (printout t "    ═══════════════════════════════════════════════════════════════════════" crlf)
   (printout t crlf crlf)

   ;;═══════════════════════════════════════════════════════════════════════════
   ;; 🥗 PASO 4: RESTRICCIONES DIETÉTICAS
   ;;═══════════════════════════════════════════════════════════════════════════
   (printout t "    ╔═══════════════════════════════════════════════════════════════════╗" crlf)
   (printout t "    ║                                                                   ║" crlf)
   (printout t "    ║      🥗  PASO 4: Preferencias y Restricciones Dietéticas  🥗     ║" crlf)
   (printout t "    ║                                                                   ║" crlf)
   (printout t "    ╚═══════════════════════════════════════════════════════════════════╝" crlf)
   (printout t crlf)
   (printout t "    Su bienestar es nuestra prioridad. Por favor, indique cualquier" crlf)
   (printout t "    restricción alimentaria que debamos considerar." crlf)
   (printout t crlf)
   (printout t "    ┌─────────────────────────────────────────────────────────────────┐" crlf)
   (printout t "    │  Opciones disponibles:                                          │" crlf)
   (printout t "    │                                                                 │" crlf)
   (printout t "    │    🌾  gluten-free    →  Sin gluten                            │" crlf)
   (printout t "    │    🥬  vegetarian     →  Vegetariano                           │" crlf)
   (printout t "    │    🌱  vegan          →  Vegano                                │" crlf)
   (printout t "    │    🥛  dairy-free     →  Sin lácteos                           │" crlf)
   (printout t "    │    ✡️  kosher         →  Kosher                                │" crlf)
   (printout t "    │    ☪️  halal          →  Halal                                 │" crlf)
   (printout t "    │    🦐  shellfish-free →  Sin mariscos                          │" crlf)
   (printout t "    │    🌰  soy-free       →  Sin soja                              │" crlf)
   (printout t "    │    🥜  nut-free       →  Sin frutos secos                      │" crlf)
   (printout t "    │                                                                 │" crlf)
   (printout t "    └─────────────────────────────────────────────────────────────────┘" crlf)
   (printout t crlf)
   (printout t "    📝 Ingrese una restricción por línea." crlf)
   (printout t "    📝 Escriba 'exit' o presione Enter para finalizar." crlf)
   (printout t crlf)
   (bind ?restrictions (create$))
   (bind ?continue TRUE)
   (while ?continue
      (printout t "       → ")
      (bind ?raw (readline))
      (bind ?entry (lowcase ?raw))
      (if (or (eq ?entry "exit") (eq ?entry ""))
         then
            (bind ?continue FALSE)
            (if (= (length$ ?restrictions) 0) then
               (printout t "    ℹ️  Sin restricciones dietéticas, excelente." crlf)
            else
               (printout t "    ✅ Restricciones registradas correctamente." crlf))
         else
            (bind ?symbol (string-to-field ?entry))
            (if (not (member$ ?symbol ?restrictions)) then
               (bind ?restrictions (create$ ?restrictions ?symbol))
               (printout t "       ✓ Agregado: " ?entry crlf))))
   
   (printout t crlf)
   (printout t "    ═══════════════════════════════════════════════════════════════════════" crlf)
   (printout t crlf crlf)

   ;;═══════════════════════════════════════════════════════════════════════════
   ;; 💰 PASO 5: PRESUPUESTO POR PERSONA
   ;;═══════════════════════════════════════════════════════════════════════════
   (printout t "    ╔═══════════════════════════════════════════════════════════════════╗" crlf)
   (printout t "    ║                                                                   ║" crlf)
   (printout t "    ║         💰  PASO 5: Inversión por Comensal  💰                   ║" crlf)
   (printout t "    ║                                                                   ║" crlf)
   (printout t "    ╚═══════════════════════════════════════════════════════════════════╝" crlf)
   (printout t crlf)
   (printout t "    Diseñaremos opciones dentro de su rango presupuestario," crlf)
   (printout t "    desde propuestas económicas hasta experiencias premium." crlf)
   (printout t crlf)
   (bind ?min-price (prompt-number "📝 Precio mínimo por persona (€, ≥0): " 0))
   (bind ?max-price (prompt-number "📝 Precio máximo por persona (€, ≥mínimo): " ?min-price))
   (printout t crlf)
   (printout t "    ✅ Rango presupuestario establecido: " ?min-price "€ - " ?max-price "€ por persona." crlf)
   (printout t crlf)
   (printout t "    ═══════════════════════════════════════════════════════════════════════" crlf)
   (printout t crlf crlf)

   ;;═══════════════════════════════════════════════════════════════════════════
   ;; 💾 GUARDAR PREFERENCIAS DEL USUARIO
   ;;═══════════════════════════════════════════════════════════════════════════
   (assert (user-restrictions
            (event-type ?event-type)
             (season ?season)
              (requested ?restrictions)
               (max-people ?max-people)
              (max-price ?max-price)
              (min-price ?min-price)
              (quiere-tarta ?quiere-tarta)))

   ;;═══════════════════════════════════════════════════════════════════════════
   ;; ✅ CONFIRMACIÓN FINAL ELEGANTE
   ;;═══════════════════════════════════════════════════════════════════════════
   (printout t "    ╔═══════════════════════════════════════════════════════════════════╗" crlf)
   (printout t "    ║                                                                   ║" crlf)
   (printout t "    ║              ✨  Preferencias Registradas con Éxito  ✨          ║" crlf)
   (printout t "    ║                                                                   ║" crlf)
   (printout t "    ╚═══════════════════════════════════════════════════════════════════╝" crlf)
   (printout t crlf)
   (printout t "    📋 Resumen de su solicitud:" crlf)
   (printout t "       • Tipo de evento     : " ?event-type crlf)
   (printout t "       • Número de personas : " ?max-people crlf)
   (printout t "       • Temporada          : " ?season crlf)
   (printout t "       • Presupuesto        : " ?min-price "€ - " ?max-price "€ por persona" crlf)
   (printout t "       • Tarta especial     : " (if (eq ?quiere-tarta TRUE) then "Sí" else "No") crlf)
   (if (> (length$ ?restrictions) 0) then
      (printout t "       • Restricciones      : " (implode$ ?restrictions) crlf)
   else
      (printout t "       • Restricciones      : Ninguna" crlf))
   (printout t crlf)
   (printout t "    ┌─────────────────────────────────────────────────────────────────┐" crlf)
   (printout t "    │                                                                 │" crlf)
   (printout t "    │  🔍 Buscando las mejores opciones gastronómicas para usted...  │" crlf)
   (printout t "    │                                                                 │" crlf)
   (printout t "    │  ⏳ Por favor espere mientras nuestro sistema de inteligencia  │" crlf)
   (printout t "    │     artificial selecciona los platos perfectos...              │" crlf)
   (printout t "    │                                                                 │" crlf)
   (printout t "    └─────────────────────────────────────────────────────────────────┘" crlf)
   (printout t crlf)
   (printout t "    ═══════════════════════════════════════════════════════════════════════" crlf)
   (printout t crlf crlf)
   
   (focus MATCH)
)

