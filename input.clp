(deftemplate event-info
   "Información general del evento"
   (slot event-type (type SYMBOL) (allowed-symbols boda congreso familiar))
   (slot guests (type NUMBER))
   (slot season (type SYMBOL) (allowed-symbols primavera verano otoño invierno))
   (slot style (type SYMBOL) (allowed-symbols clasico moderno regional sibarita)))
   
(deftemplate user-restrictions
   "Restricciones dietéticas y preferencias del usuario"
   (slot is-vegan (type SYMBOL) (allowed-symbols TRUE FALSE) (default FALSE))
   (slot is-vegetarian (type SYMBOL) (allowed-symbols TRUE FALSE) (default FALSE))
   (slot is-gluten-free (type SYMBOL) (allowed-symbols TRUE FALSE) (default FALSE))
   (slot is-dairy-free (type SYMBOL) (allowed-symbols TRUE FALSE) (default FALSE))
   (slot max-price (type NUMBER) (default 1000))
   (slot min-servings (type NUMBER) (default 1)))


(defrule request-data
   (initial-fact)
   =>
   (printout t "Event type (wedding/congress/family): ")
   (bind ?type (read))
   (printout t "Number of guests: ")
   (bind ?numGuests (read))
   (printout t "Season (spring/summer/autumn/winter): ")
   (bind ?season (read))
   (printout t "Cuisine style (classic/modern/regional/gourmet): ")
   (bind ?style (read))

   (printout t "Maximum budget per person: ")
   (bind ?maxPrice (read))
   (printout t "Minimum budget per person: ")
   (bind ?minPrice (read))

   (printout t "Vegan? (TRUE/FALSE): ")
   (bind ?vegan (read))
   (printout t "Vegetarian? (TRUE/FALSE): ")
   (bind ?vegetarian (read))
   (printout t "Gluten-free? (TRUE/FALSE): ")
   (bind ?glutenFree (read))
   (printout t "Dairy-free? (TRUE/FALSE): ")
   (bind ?dairyFree (read))

   (assert (event-info
               (event-type ?type)
               (guests ?numGuests)
               (season ?season)
               (style ?style)))

   (assert (user-restrictions
               (is-vegan ?vegan)
               (is-vegetarian ?vegetarian)
               (is-gluten-free ?glutenFree)
               (is-dairy-free ?dairyFree)
               (max-price ?maxPrice)
               (min-servings ?minPrice)))

   (printout t crlf "Data successfully recorded." crlf))

