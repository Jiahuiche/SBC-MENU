;; ============================================
;; Template para definir restricciones dietéticas
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
(deffacts datos-iniciales
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
;; Función para comprobar si un plato cumple todas las restricciones de una combinación
(deffunction cumple-todas (?plato ?restricciones)
   ;; Obtener el multislot "cumple" del plato
   (bind ?cumple (fact-slot-value ?plato cumple))
   
   ;; Obtener la cantidad de restricciones en la combinación
   (bind ?n (length$ ?restricciones))
   
   ;; Recorrer todas las restricciones de la combinación
   (loop-for-count (?i 1 ?n)
      (bind ?r (nth$ ?i ?restricciones))   ;; Tomar la restricción actual
      ;; Si el plato no cumple esta restricción, devolver FALSE
      (if (not (member$ ?r ?cumple)) then (return FALSE))
   )
   
   ;; Si pasó todas las restricciones, devolver TRUE
   (return TRUE)
)

;; ============================================
;; Función recursiva para generar todas las combinaciones posibles de una lista
;; Cada combinación se devuelve como un multifield
;; ============================================
;; Función recursiva para generar combinaciones de tamaño >= 2
(deffunction combinaciones (?lista)
   (if (<= (length$ ?lista) 1) then
      ;; Lista de tamaño 0 o 1 → no devuelve nada porque queremos >= 2
      (return (create$))
   )

   ;; Separar el primer elemento
   (bind ?primero (nth$ 1 ?lista))
   ;; Tomar el resto de la lista
   (bind ?resto (rest$ ?lista))
   ;; Combinaciones del resto
   (bind ?subcombs (combinaciones ?resto))

   ;; Inicializar resultado
   (bind ?resultado ?subcombs)

   ;; Para cada subcombinación, agregar el primer elemento
   (foreach ?c ?subcombs
      (bind ?resultado (create$ ?resultado (create$ ?primero ?c))))

   ;; Generar combinaciones de 2 elementos entre primero y el resto
   (loop-for-count (?i 1 (length$ ?resto))
      (bind ?elem (nth$ ?i ?resto))
      (bind ?resultado (create$ ?resultado (create$ ?primero ?elem)))
   )

   (return ?resultado)
)
;; ============================================
;; Función que comprueba que cada restricción tenga al menos un plato que la cumpla
(deffunction restricciones-individuales-validas ()
   (bind ?todas-validas TRUE)
   (do-for-all-facts ((?r restricciones)) TRUE
      (bind ?nombre ?r:nombre)
      (bind ?cumple-algun-plato FALSE)
      (do-for-all-facts ((?p plato)) TRUE
         (if (member$ ?nombre (fact-slot-value ?p cumple)) then
            (bind ?cumple-algun-plato TRUE)
         )
      )
      (if (not ?cumple-algun-plato) then
         (printout t "¡Aviso! No hay ningún plato que cumpla la restricción: " ?nombre crlf)
         (bind ?todas-validas FALSE)
      )
   )
   (return ?todas-validas)
)
;; ============================================
;; Regla principal que aplica las funciones en orden
(defrule ejecutar-verificacion
   =>
   ;; Primero comprobamos restricciones individuales
   (if (restricciones-individuales-validas) then
      ;; Crear una lista con todas las restricciones disponibles
      (bind ?todas (create$))
      (do-for-all-facts ((?r restricciones)) TRUE 
         (bind ?todas (create$ ?todas ?r:nombre)))

      ;; Si todas son válidas, comprobamos combinaciones de 2 o más
      (bind ?comb-list (combinaciones ?todas))
      (printout t "combinaciones:" comb-list)
      ;; Para cada combinación, comprobar si algún plato la cumple
      (foreach ?comb ?comb-list
         (bind ?ok FALSE)  ;; Flag para saber si algún plato cumple la combinación
         (do-for-all-facts ((?p plato)) TRUE
            (if (cumple-todas ?p ?comb) then (bind ?ok TRUE)))
         ;; Si algún plato cumple, imprimir la combinación
         (if ?ok then
            (printout t "Combinación válida: " ?comb crlf)))
   else
      (printout t "No se generaron combinaciones porque hay restricciones sin platos que las cumplan." crlf)
   )
)
