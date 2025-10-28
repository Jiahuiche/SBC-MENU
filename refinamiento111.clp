(defmodule REFINAMIENTO
    (import ONTOLOGY ?ALL)
    (import MATCH ?ALL)
    (import DATA ?ALL)
    (import input ?ALL)
    (export ?ALL))

(deftemplate REFINAMIENTO::menu-candidate
    (slot tier (type SYMBOL) (default unknown))
    (slot index (type INTEGER) (default 0))
    (slot coverage-count (type INTEGER) (default 0))
    (multislot restrictions-covered (type SYMBOL))
    (multislot requested (type SYMBOL))
    (slot starter (type INSTANCE))
    (slot main (type INSTANCE))
    (slot dessert (type INSTANCE))
    (slot total-price (type FLOAT)))

(deftemplate REFINAMIENTO::menu-pointer
    (slot tier (type SYMBOL))
    (slot position (type INTEGER))
    (slot max (type INTEGER)))

(deftemplate REFINAMIENTO::menu-component
    (slot category (type SYMBOL))
    (slot recipe (type INSTANCE))
    (multislot restrictions (type SYMBOL))
    (slot price (type FLOAT)))

(deftemplate REFINAMIENTO::tier-summary
    (slot tier (type SYMBOL))
    (slot count (type INTEGER)))

(deftemplate REFINAMIENTO::session
    (slot phase (type SYMBOL))
    (slot tier (type SYMBOL) (default none))
    (slot best-coverage (type INTEGER) (default 0))
    (slot requested-total (type INTEGER) (default 0))
    (slot menu-count (type INTEGER) (default 0))
    (multislot requested (type SYMBOL)))

;;;============================================================================
;;; Reglas y funciones para el refinamiento de menús
;;;============================================================================

(deffunction REFINAMIENTO::dish-fits (?recipe ?category)
    (bind ?types (send ?recipe get-meal_types))
    (if (eq ?category starter) then
        (if (or (member$ starter ?types)
                (member$ appetizer ?types)
                (member$ side-dish ?types)) then
            (return TRUE)
        else
            (return FALSE)))
    (if (eq ?category main) then
        (if (or (member$ main-course ?types)
                (member$ main-dish ?types)
                (member$ lunch ?types)) then
            (return TRUE)
        else
            (return FALSE)))
    (if (eq ?category dessert) then
        (if (member$ dessert ?types) then
            (return TRUE)
        else
            (return FALSE)))
    (return FALSE))

(deffunction REFINAMIENTO::union-restrictions (?current ?extra)
    (bind ?result ?current)
    (foreach ?item ?extra
        (if (not (member$ ?item ?result)) then
            (bind ?result (create$ ?result ?item))))
    (return ?result))

(deffunction REFINAMIENTO::missing-restrictions (?requested ?covered)
    (bind ?missing (create$))
    (foreach ?item ?requested
        (if (not (member$ ?item ?covered)) then
            (bind ?missing (create$ ?missing ?item))))
    (return ?missing))

(deffunction REFINAMIENTO::find-min-price (?facts)
    (if (= (length$ ?facts) 0) then (return FALSE))
    (bind ?best (nth$ 1 ?facts))
    (bind ?best-price (fact-slot-value ?best total-price))
    (foreach ?fact ?facts
        (bind ?price (fact-slot-value ?fact total-price))
        (if (< ?price ?best-price) then
            (bind ?best ?fact)
            (bind ?best-price ?price)))
    (return ?best))

(deffunction REFINAMIENTO::remove-fact (?facts ?target)
    (bind ?result (create$))
    (foreach ?fact ?facts
        (if (neq ?fact ?target) then
            (bind ?result (create$ ?result ?fact))))
    (return ?result))

(deffunction REFINAMIENTO::order-by-price (?facts)
    (bind ?ordered (create$))
    (bind ?remaining ?facts)
    (while (> (length$ ?remaining) 0)
        (bind ?next (find-min-price ?remaining))
        (if (eq ?next FALSE) then
            (bind ?remaining (create$))
        else
            (bind ?ordered (create$ ?ordered ?next))
            (bind ?remaining (remove-fact ?remaining ?next))))
    (return ?ordered))

(deffunction REFINAMIENTO::assign-tier-metadata ()
    (do-for-all-facts ((?summary tier-summary)) TRUE (retract ?summary))
    (do-for-all-facts ((?pointer menu-pointer)) TRUE (retract ?pointer))
    (bind ?menus (find-all-facts ((?m menu-candidate)) TRUE))
    (if (eq ?menus FALSE) then
        (bind ?menus (create$)))
    (if (= (length$ ?menus) 0) then (return 0))
    (bind ?min-price (fact-slot-value (nth$ 1 ?menus) total-price))
    (bind ?max-price ?min-price)
    (foreach ?menu ?menus
        (bind ?price (fact-slot-value ?menu total-price))
        (if (< ?price ?min-price) then (bind ?min-price ?price))
        (if (> ?price ?max-price) then (bind ?max-price ?price)))
    (bind ?range (- ?max-price ?min-price))
    (if (<= ?range 0.0) then
        (bind ?cheap-limit ?max-price)
        (bind ?medium-limit ?max-price)
    else
        (bind ?step (/ ?range 3.0))
        (bind ?cheap-limit (+ ?min-price ?step))
        (bind ?medium-limit (+ ?min-price (* 2 ?step))))
    (do-for-all-facts ((?menu menu-candidate)) TRUE
        (bind ?price (fact-slot-value ?menu total-price))
        (if (<= ?price ?cheap-limit) then
            (modify ?menu (tier cheap))
        else
            (if (<= ?price ?medium-limit) then
                (modify ?menu (tier medium))
            else
                (modify ?menu (tier expensive)))))
    (bind ?total 0)
    (bind ?tiers (create$ cheap medium expensive))
    (foreach ?tier ?tiers
        (bind ?facts (find-all-facts ((?m menu-candidate)) (eq ?m:tier ?tier)))
        (if (eq ?facts FALSE) then
            (bind ?facts (create$)))
        (if (> (length$ ?facts) 0) then
            (bind ?ordered (order-by-price ?facts))
            (bind ?position 0)
            (foreach ?menu ?ordered
                (bind ?position (+ ?position 1))
                (modify ?menu (index ?position)))
            (assert (tier-summary (tier ?tier) (count ?position)))
            (assert (menu-pointer (tier ?tier) (position 0) (max ?position)))
            (bind ?total (+ ?total ?position))))
    (return ?total))

(deffunction REFINAMIENTO::find-menu (?tier ?index)
    (bind ?result FALSE)
    (do-for-all-facts ((?m menu-candidate)) (and (eq ?m:tier ?tier) (= ?m:index ?index))
        (bind ?result ?m))
    (return ?result))

(deffunction REFINAMIENTO::print-menu (?menu)
    (bind ?tier (fact-slot-value ?menu tier))
    (bind ?index (fact-slot-value ?menu index))
    (bind ?total (fact-slot-value ?menu total-price))
    (bind ?coverage (fact-slot-value ?menu coverage-count))
    (bind ?requested (fact-slot-value ?menu requested))
    (bind ?covered (fact-slot-value ?menu restrictions-covered))
    (bind ?missing (missing-restrictions ?requested ?covered))
    (bind ?requested-count (length$ ?requested))
    (printout t crlf "[" ?tier "] opción " ?index crlf)
    (printout t "Cobertura: " ?coverage " de " ?requested-count " restricciones" crlf)
    (if (> (length$ ?covered) 0) then
        (printout t "Cumple: " (implode$ ?covered) crlf)
    else
        (printout t "Cumple: ninguna restricción solicitada" crlf))
    (if (> (length$ ?missing) 0) then
        (printout t "Pendiente: " (implode$ ?missing) crlf))
    (format t "Precio total: %.2f euros%n" ?total)
    (bind ?starter (fact-slot-value ?menu starter))
    (bind ?main (fact-slot-value ?menu main))
    (bind ?dessert (fact-slot-value ?menu dessert))
    (format t " Entrante: %s (%.2f euros)%n" (send ?starter get-title) (send ?starter get-price))
    (format t " Principal: %s (%.2f euros)%n" (send ?main get-title) (send ?main get-price))
    (format t " Postre: %s (%.2f euros)%n" (send ?dessert get-title) (send ?dessert get-price)))

(deffunction REFINAMIENTO::generate-menus ()
    (do-for-all-facts ((?m menu-candidate)) TRUE (retract ?m))
    (do-for-all-facts ((?p menu-pointer)) TRUE (retract ?p))
    (do-for-all-facts ((?s tier-summary)) TRUE (retract ?s))
    (do-for-all-facts ((?sess session)) TRUE (retract ?sess))
    (do-for-all-facts ((?comp menu-component)) TRUE (retract ?comp))
    (bind ?user (find-fact ((?u user-restrictions)) TRUE))
    (if (eq ?user FALSE) then
        (printout t "No se encontraron preferencias del usuario." crlf)
        (return failure))
    (bind ?requested (fact-slot-value ?user requested))
    (bind ?requested-count (length$ ?requested))
    (bind ?min-budget (fact-slot-value ?user min-price))
    (bind ?max-budget (fact-slot-value ?user max-price))
    (bind ?modules (get-module-list))
    (if (not (member$ MATCH ?modules)) then
        (printout t "El módulo MATCH no está disponible. Cargue primero el módulo de matching." crlf)
        (return failure))
    (bind ?candidate-facts (get-fact-list MATCH))
    (foreach ?cand ?candidate-facts
        (if (eq (fact-relation ?cand) candidate-set) then
            (bind ?recipe (fact-slot-value ?cand recipe-instance))
            (bind ?restrictions (fact-slot-value ?cand restrictions-met))
            (bind ?price (send ?recipe get-price))
            (if (dish-fits ?recipe starter) then
                (assert (menu-component
                    (category starter)
                    (recipe ?recipe)
                    (restrictions ?restrictions)
                    (price ?price))))
            (if (dish-fits ?recipe main) then
                (assert (menu-component
                    (category main)
                    (recipe ?recipe)
                    (restrictions ?restrictions)
                    (price ?price))))
            (if (dish-fits ?recipe dessert) then
                (assert (menu-component
                    (category dessert)
                    (recipe ?recipe)
                    (restrictions ?restrictions)
                    (price ?price))))))
    (bind ?starters (find-all-facts ((?c menu-component)) (eq ?c:category starter)))
    (if (eq ?starters FALSE) then (bind ?starters (create$)))
    (bind ?mains (find-all-facts ((?c menu-component)) (eq ?c:category main)))
    (if (eq ?mains FALSE) then (bind ?mains (create$)))
    (bind ?desserts (find-all-facts ((?c menu-component)) (eq ?c:category dessert)))
    (if (eq ?desserts FALSE) then (bind ?desserts (create$)))
    (if (or (= (length$ ?starters) 0)
            (= (length$ ?mains) 0)
            (= (length$ ?desserts) 0)) then
        (printout t "No hay suficientes platos para formar un menú completo." crlf)
        (return failure))
    (bind ?starter-count (length$ ?starters))
    (bind ?main-count (length$ ?mains))
    (bind ?dessert-count (length$ ?desserts))
    (bind ?best-coverage -1)
    (bind ?attempted 0)
    (loop-for-count (?i 1 ?starter-count)
        (bind ?starter (nth$ ?i ?starters))
        (bind ?starter-recipe (fact-slot-value ?starter recipe))
        (bind ?starter-res (fact-slot-value ?starter restrictions))
        (bind ?starter-price (fact-slot-value ?starter price))
        (loop-for-count (?j 1 ?main-count)
            (bind ?main (nth$ ?j ?mains))
            (bind ?main-recipe (fact-slot-value ?main recipe))
            (if (neq ?starter-recipe ?main-recipe) then
                (bind ?main-res (fact-slot-value ?main restrictions))
                (bind ?main-price (fact-slot-value ?main price))
                (loop-for-count (?k 1 ?dessert-count)
                    (bind ?dessert (nth$ ?k ?desserts))
                    (bind ?dessert-recipe (fact-slot-value ?dessert recipe))
                    (if (and (neq ?dessert-recipe ?starter-recipe)
                             (neq ?dessert-recipe ?main-recipe)) then
                        (bind ?attempted (+ ?attempted 1))
                        (bind ?dessert-res (fact-slot-value ?dessert restrictions))
                        (bind ?dessert-price (fact-slot-value ?dessert price))
                        (bind ?total (+ ?starter-price ?main-price ?dessert-price))
                        (if (and (>= ?total ?min-budget) (<= ?total ?max-budget)) then
                            (bind ?coverage-list (create$))
                            (bind ?coverage-list (union-restrictions ?coverage-list ?starter-res))
                            (bind ?coverage-list (union-restrictions ?coverage-list ?main-res))
                            (bind ?coverage-list (union-restrictions ?coverage-list ?dessert-res))
                            (bind ?coverage (length$ ?coverage-list))
                            (if (> ?coverage ?best-coverage) then
                                (do-for-all-facts ((?old menu-candidate)) TRUE (retract ?old))
                                (bind ?best-coverage ?coverage))
                            (if (= ?coverage ?best-coverage) then
                                (assert (menu-candidate
                                    (coverage-count ?coverage)
                                    (restrictions-covered ?coverage-list)
                                    (requested ?requested)
                                    (starter ?starter-recipe)
                                    (main ?main-recipe)
                                    (dessert ?dessert-recipe)
                                    (total-price ?total))))))))))
    (if (= ?best-coverage -1) then
        (printout t "No se encontraron menús dentro del rango de precios especificado." crlf)
        (if (> ?attempted 0) then
            (printout t "Intente ampliar el presupuesto o reducir restricciones." crlf))
        (return failure))
    (bind ?total-menus (assign-tier-metadata))
    (if (= ?total-menus 0) then
        (printout t "No se pudieron organizar los menús por rangos de precio." crlf)
        (return failure))
    (assert (session
        (phase initial)
        (best-coverage ?best-coverage)
        (requested-total ?requested-count)
        (menu-count ?total-menus)
        (requested ?requested)))
    (printout t crlf "Generados " ?total-menus " menús con cobertura "
        ?best-coverage " de " ?requested-count " restricciones." crlf)
    (if (< ?best-coverage ?requested-count) then
        (printout t "Aviso: no se pudieron satisfacer todas las restricciones." crlf))
    (return success)
)

(defrule REFINAMIENTO::start-refinement
    ?req <- (refinement-request (status pending))
    =>
    (retract ?req)
    (bind ?result (generate-menus))
    (if (eq ?result failure) then
        (assert (session (phase finished)))))

(defrule REFINAMIENTO::prompt-tier-list
    ?s <- (session (phase initial) (best-coverage ?coverage) (requested-total ?total) (menu-count ?count))
    =>
    (printout t crlf "Menús disponibles: " ?count crlf)
    (printout t "Cobertura máxima: " ?coverage " de " ?total " restricciones" crlf)
    (printout t "Categorías disponibles:" crlf)
    (do-for-all-facts ((?ts tier-summary)) TRUE
        (printout t " - " ?ts:tier " (" ?ts:count " opciones)" crlf))
    (printout t "Escriba la categoría deseada (cheap/medium/expensive) o 'exit' para terminar." crlf)
    (modify ?s (phase reading-tier) (tier none)))

(defrule REFINAMIENTO::read-tier-selection
    ?s <- (session (phase reading-tier))
    =>
    (printout t "> ")
    (bind ?input (lowcase (readline)))
    (if (or (eq ?input "exit") (eq ?input "quit")) then
        (modify ?s (phase finished))
    else
        (bind ?symbol (string-to-field ?input))
        (if (any-factp ((?ts tier-summary)) (eq ?ts:tier ?symbol)) then
            (modify ?s (phase showing) (tier ?symbol))
        else
            (printout t "Categoría no reconocida." crlf)
            (modify ?s (phase reading-tier)))))

(defrule REFINAMIENTO::show-next-menu
    ?s <- (session (phase showing) (tier ?tier) (requested-total ?total))
    ?pointer <- (menu-pointer (tier ?tier) (position ?pos) (max ?max))
    =>
    (if (= ?pos ?max) then
        (printout t "Ya se han mostrado todas las opciones de la categoría " ?tier "." crlf)
        (modify ?s (phase initial) (tier none))
    else
        (bind ?next (+ ?pos 1))
        (bind ?menu (find-menu ?tier ?next))
        (if (eq ?menu FALSE) then
            (printout t "No se pudo recuperar el menú solicitado." crlf)
            (modify ?s (phase finished))
        else
            (print-menu ?menu)
            (modify ?pointer (position ?next))
            (modify ?s (phase prompt-next)))))

(defrule REFINAMIENTO::prompt-next-step
    ?s <- (session (phase prompt-next) (tier ?tier))
    =>
    (printout t "Escriba 'next' para otra opción de " ?tier ", 'back' para elegir otra categoría o 'exit' para terminar." crlf)
    (modify ?s (phase waiting-next)))

(defrule REFINAMIENTO::handle-next-response
    ?s <- (session (phase waiting-next) (tier ?tier))
    =>
    (printout t "> ")
    (bind ?input (lowcase (readline)))
    (if (or (eq ?input "next") (eq ?input "n")) then
        (modify ?s (phase showing))
    else
        (if (or (eq ?input "back") (eq ?input "b") (eq ?input "tier")) then
            (modify ?s (phase initial) (tier none))
        else
            (if (or (eq ?input "exit") (eq ?input "quit")) then
                (modify ?s (phase finished))
            else
                (printout t "Entrada no reconocida." crlf)
                (modify ?s (phase prompt-next))))))

(defrule REFINAMIENTO::finish-session
    ?s <- (session (phase finished))
    =>
    (retract ?s)
    (printout t "Finalizando refinamiento de menús." crlf))