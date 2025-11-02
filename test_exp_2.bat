(clear)
(load "onto.clp")
(load "recipes_clips.clp") 
(load "input.clp")
(load "match_max.clp")
(load "refinamiento.clp")
(focus input)
(reset)
EXPERIMENTO 8: Wedding - Presupuesto alto
(run)

wedding
yes
150
any-season
exit
60
150


(clear)
(load "onto.clp")
(load "recipes_clips.clp") 
(load "input.clp")
(load "match_max.clp")
(load "refinamiento.clp")
(focus input)
(reset)
EXPERIMENTO 9: Presupuesto muy ajustado
(run)

congress
80
any-season
exit
10
22

(clear)
(load "onto.clp")
(load "recipes_clips.clp") 
(load "input.clp")
(load "match_max.clp")
(load "refinamiento.clp")
(focus input)
(reset)
EXPERIMENTO 10: Presupuesto muy amplio
(run)

family
yes
70
winter
exit
10
150

(clear)
(load "onto.clp")
(load "recipes_clips.clp") 
(load "input.clp")
(load "match_max.clp")
(load "refinamiento.clp")
(focus input)
(reset)
EXPERIMENTO 11: Evento pequeño - Permite recetas complejas
(run)

congress
50
spring
exit
10
80

(clear)
(load "onto.clp")
(load "recipes_clips.clp") 
(load "input.clp")
(load "match_max.clp")
(load "refinamiento.clp")
(focus input)
(reset)
EXPERIMENTO 12: Evento grande - Sin recetas complejas
(run)

congress
200
summer
exit
15
90

(clear)
(load "onto.clp")
(load "recipes_clips.clp") 
(load "input.clp")
(load "match_max.clp")
(load "refinamiento.clp")
(focus input)
(reset)
EXPERIMENTO 13: Estacionalidad - Spring
(run)

family
no
90
spring
exit
15
100

(clear)
(load "onto.clp")
(load "recipes_clips.clp") 
(load "input.clp")
(load "match_max.clp")
(load "refinamiento.clp")
(focus input)
(reset)
EXPERIMENTO 14: Estacionalidad - Summer
(run)

family
no
90
summer
exit
15
100

