;; ============================================
;; Template para definir restricciones dietéticas
;; ============================================
;; Cada restricción tiene un nombre único
(deftemplate restricciones
	(slot nombre)
)

;; Template para definir platos de comida
;; Cada plato tiene un nombre y un multislot "cumple" con las restricciones que satisface
(deftemplate plato
	(slot nombre)
	(multislot cumple)
)

;; ============================================
;; Hechos iniciales: restricciones y platos
;; ============================================
(deffacts datos-iniciales
	;; Creamos un hecho disparador
	(ejecutar-main)
	;; Restricciones disponibles
	(restricciones (nombre vegetariano))
	(restricciones (nombre sin-gluten))
	(restricciones (nombre vegano))
	(restricciones (nombre diabetico))

	;; Platos y las restricciones que cumplen
	(plato (nombre ensalada) (cumple vegetariano sin-gluten))
	(plato (nombre hamburguesa) (cumple sin-gluten))
	(plato (nombre tofu) (cumple vegano vegetariano sin-gluten))
	(plato (nombre sopa) (cumple vegetariano diabetico))
)

;; ============================================
;; Función recursiva para generar todas las combinaciones posibles de una lista
;; Cada combinación se devuelve como un multifield
;; ============================================
(deffunction combinaciones (?lista)
	(bind ?n (length$ ?lista))
	(bind ?resultado (create$))

	;; Si la lista tiene 1 o 0 elementos, no hay combinaciones válidas
	(if (<= ?n 0) then
		(return (create$))
	)
	;; Primero, añadimos las combinaciones de 1 elemento como strings
	(loop-for-count (?i 1 ?n)
		(bind ?resultado (create$ ?resultado (str-cat (nth$ ?i ?lista))))
	)
	;; Generar combinaciones de 2 en adelante
	(loop-for-count (?i 1 (- ?n 1))
		;; Para cada elemento, tomamos el resto
		(bind ?resto (subseq$ ?lista (+ ?i 1) ?n))

		;; Combinaciones del resto
		(bind ?subcombs (combinaciones ?resto))

		;; Añadimos combinaciones de 2 elementos (i + cada uno del resto)
		(foreach ?r ?resto
			(bind ?comb (str-cat (nth$ ?i ?lista) " " ?r))
			(bind ?resultado (create$ ?resultado ?comb))
		)

		;; Añadimos combinaciones más grandes (i + cada subcombinación)
		(foreach ?c ?subcombs
			(bind ?comb (str-cat (nth$ ?i ?lista) " " ?c))
			(bind ?resultado (create$ ?resultado ?comb))
		)
	)
	(return ?resultado)
)
;; ============================================
;; Función que comprueba si un plato cumple todas las restricciones de una combinación
;; ============================================
(deffunction cumple-todas (?plato ?restricciones)
	;; Obtenemos el multislot "cumple" del plato
	(bind ?cumple (fact-slot-value ?plato cumple))
	
	;; Recorremos cada restricción en la combinación
	(loop-for-count (?i 1 (length$ ?restricciones))
		;; Si el plato no cumple una restricción, devolvemos FALSE
		(if (not (member$ (nth$ ?i ?restricciones) ?cumple)) then
			(return FALSE)
		)
	)
	;; Si cumple todas, devolvemos TRUE
	(return TRUE)
)

;; ============================================
;; Función que comprueba si algún plato cumple una combinación de restricciones
;; ============================================
(deffunction algun-plato-cumple (?combinacion)
	(bind ?ok FALSE)
	
	;; Recorremos todos los hechos de plato
	(do-for-all-facts ((?p plato)) TRUE
		;; Si el plato cumple todas las restricciones, marcamos ok como TRUE
		(if (cumple-todas ?p ?combinacion) then
			(bind ?ok TRUE)
		)
	)
	;; Devolvemos TRUE si al menos un plato cumple la combinación
	(return ?ok)
)

;; ============================================ 
;; Regla principal que actúa como "main"
;; ============================================
(defrule main
	?f <- (ejecutar-main)
	=>
	(printout t "===== EJECUTANDO PROGRAMA =====" crlf)
	(bind ?todas (create$))
	(do-for-all-facts ((?r restricciones)) TRUE 
		(bind ?todas (create$ ?todas ?r:nombre))
	)
	(bind ?combs (combinaciones ?todas))

    ;; Descomentar si se quiere hacer un print de comprobacion
	;;(printout t "Combinaciones:" crlf)
	;;(foreach ?comb ?combs
    ;;	(printout t ?comb crlf)
	;;)

    ;; Recorremos las combinaciones como strings
    ;; Recorremos las combinaciones como strings
(foreach ?c ?combs
    ;; Convertimos la string en multifield de restricciones
    (bind ?restricciones (explode$ ?c))  ;; separa por espacios

    ;; Lista de platos que cumplen la combinación
    (bind ?platos-validos (create$))

    ;; Recorremos todos los platos y añadimos los que cumplen todas las restricciones
    (do-for-all-facts ((?p plato)) TRUE
        (if (cumple-todas ?p ?restricciones) then
            (bind ?platos-validos (create$ ?platos-validos ?p))
        )
    )

    ;; Imprimimos la combinación y los platos que la cumplen
    (if (> (length$ ?platos-validos) 0) then
        (printout t "Platos válida para: " ?c crlf)
        (foreach ?p ?platos-validos
            ;; Mostramos el nombre del plato y su multislot de restricciones
            (printout t "  Plato: " (fact-slot-value ?p nombre)
                     ", restricciones: " (fact-slot-value ?p cumple) crlf)
        )
    else
        (printout t "No hay plato que cumpla: " ?c crlf)
    )
)
	;; Eliminamos el hecho disparador para que no vuelva a ejecutarse
	(retract ?f)
)
