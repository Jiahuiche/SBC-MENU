(clear)
(load "onto.clp")
(load "recipes_clips.clp") 
(load "input.clp")
(load "match_max.clp")
(load "refinamiento.clp")
(focus input)
(reset)

EXPERIMENTO 1: Sin restricciones - Presupuesto moderado

(run)

congress
100
any-season
exit
20
80

(clear)
(load "onto.clp")
(load "recipes_clips.clp") 
(load "input.clp")
(load "match_max.clp")
(load "refinamiento.clp")
(focus input)
(reset)

EXPERIMENTO 2: Una restricción - Vegetarian

(run)

family
yes
80
summer
vegetarian
exit
25
100

(clear)
(load "onto.clp")
(load "recipes_clips.clp") 
(load "input.clp")
(load "match_max.clp")
(load "refinamiento.clp")
(focus input)
(reset)
EXPERIMENTO 3: Dos restricciones - Vegan + Gluten-free
(run)

congress
150
spring
vegan
gluten-free
exit
10
100

(clear)
(load "onto.clp")
(load "recipes_clips.clp") 
(load "input.clp")
(load "match_max.clp")
(load "refinamiento.clp")
(focus input)
(reset)
EXPERIMENTO 4: Tres restricciones - Vegan + Gluten-free + Nut-free
(run)

family
no
90
autumn
vegan
gluten-free
nut-free
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
EXPERIMENTO 5: Cuatro restricciones - Muy restrictivo
(run)

congress
120
winter
vegan
gluten-free
soy-free
nut-free
exit
20
90

(clear)
(load "onto.clp")
(load "recipes_clips.clp") 
(load "input.clp")
(load "match_max.clp")
(load "refinamiento.clp")
(focus input)
(reset)
EXPERIMENTO 6: Wedding - Presupuesto muy bajo
(run)

wedding
yes
100
spring
exit
10
20

(clear)
(load "onto.clp")
(load "recipes_clips.clp") 
(load "input.clp")
(load "match_max.clp")
(load "refinamiento.clp")
(focus input)
(reset)
EXPERIMENTO 7: Wedding - Presupuesto medio
(run)

wedding
yes
120
summer
vegetarian
exit
20
80



