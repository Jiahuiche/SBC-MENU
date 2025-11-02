(clear)
(load "onto.clp")
(load "recipes_clips.clp") 
(load "input.clp")
(load "match_max.clp")
(load "refinamiento.clp")
(focus input)
(reset)
EXPERIMENTO 15: Estacionalidad - Autumn
(run)

family
no
90
autumn
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
EXPERIMENTO 16: Estacionalidad - Winter
(run)

family
no
90
winter
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
EXPERIMENTO 17: Presupuesto min = max (caso límite)
(run)

congress
100
any-season
exit
35
35

(clear)
(load "onto.clp")
(load "recipes_clips.clp") 
(load "input.clp")
(load "match_max.clp")
(load "refinamiento.clp")
(focus input)
(reset)
EXPERIMENTO 18: Todas las restricciones (caso extremo)
(run)

congress
200
any-season
gluten-free
vegetarian
vegan
dairy-free
kosher
halal
shellfish-free
soy-free
nut-free
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
EXPERIMENTO 19: Wedding sin tarta
(run)

wedding
no
100
summer
vegetarian
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
EXPERIMENTO 20: Family con tarta
(run)

family
yes
60
autumn
exit
10
70

(clear)
(load "onto.clp")
(load "recipes_clips.clp") 
(load "input.clp")
(load "match_max.clp")
(load "refinamiento.clp")
(focus input)
(reset)
EXPERIMENTO 21: Todas las restricciones + wedding (caso extremo con wedding)
(run)

wedding
yes
200
any-season
gluten-free
vegetarian
vegan
dairy-free
kosher
halal
shellfish-free
soy-free
nut-free
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
EXPERIMENTO 22: Wedding - Presupuesto bajo
(run)

wedding
yes
100
spring
exit
10
25
