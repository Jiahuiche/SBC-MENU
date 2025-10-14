;;; ---------------------------------------------------------
;;; ontologia_menu.clp
;;; Translated by owl2clips
;;; Translated to CLIPS from ontology ontologia_menu.ttl
;;; :Date 07/10/2025 13:43:47

(defclass Drink
    (is-a USER)
    (role concrete)
    (pattern-match reactive)
    (multislot CompatibleWith
        (type INSTANCE)
        (create-accessor read-write))
    (multislot DrinkOF
        (type INSTANCE)
        (create-accessor read-write))
)

(defclass Alcohol
    (is-a Drink)
    (role concrete)
    (pattern-match reactive)
)

(defclass Soft
    (is-a Drink)
    (role concrete)
    (pattern-match reactive)
)

(defclass Constraint
    (is-a USER)
    (role concrete)
    (pattern-match reactive)
    (multislot ApplyOn
        (type INSTANCE)
        (create-accessor read-write))
)

(defclass DairyFree
    (is-a Constraint)
    (role concrete)
    (pattern-match reactive)
)

(defclass GlutenFree
    (is-a Constraint)
    (role concrete)
    (pattern-match reactive)
)

(defclass Halal
    (is-a Constraint)
    (role concrete)
    (pattern-match reactive)
)

(defclass Kosher
    (is-a Constraint)
    (role concrete)
    (pattern-match reactive)
)

(defclass NutFree
    (is-a Constraint)
    (role concrete)
    (pattern-match reactive)
)

(defclass ShellfishFree
    (is-a Constraint)
    (role concrete)
    (pattern-match reactive)
)

(defclass Vegan
    (is-a Constraint)
    (role concrete)
    (pattern-match reactive)
)

(defclass Vegetarian
    (is-a Constraint)
    (role concrete)
    (pattern-match reactive)
)

(defclass Dish
    (is-a USER)
    (role concrete)
    (pattern-match reactive)
    (multislot CompatibleWith
        (type INSTANCE)
        (create-accessor read-write))
    (multislot MainCourseOf
        (type INSTANCE)
        (create-accessor read-write))
    (multislot SarterOf
        (type INSTANCE)
        (create-accessor read-write))
)

(defclass Dessert
    (is-a Dish)
    (role concrete)
    (pattern-match reactive)
)

(defclass Main
    (is-a Dish)
    (role concrete)
    (pattern-match reactive)
)

(defclass Starter
    (is-a Dish)
    (role concrete)
    (pattern-match reactive)
)

(defclass Ingredient
    (is-a USER)
    (role concrete)
    (pattern-match reactive)
    (multislot IngredientOf
        (type INSTANCE)
        (create-accessor read-write))
)

(defclass Aromatics_&_Herbs
    (is-a Ingredient)
    (role concrete)
    (pattern-match reactive)
)

(defclass Aromatics
    (is-a Aromatics_&_Herbs)
    (role concrete)
    (pattern-match reactive)
)

(defclass DryHerbs
    (is-a Aromatics_&_Herbs)
    (role concrete)
    (pattern-match reactive)
)

(defclass FreshHerbs
    (is-a Aromatics_&_Herbs)
    (role concrete)
    (pattern-match reactive)
)

(defclass Spices_&_Condiments
    (is-a Ingredient)
    (role concrete)
    (pattern-match reactive)
)

(defclass Dairy
    (is-a Ingredient)
    (role concrete)
    (pattern-match reactive)
)

(defclass Butter
    (is-a Dairy)
    (role concrete)
    (pattern-match reactive)
)

(defclass Cheese
    (is-a Dairy)
    (role concrete)
    (pattern-match reactive)
)

(defclass Cream
    (is-a Dairy)
    (role concrete)
    (pattern-match reactive)
)

(defclass Milk
    (is-a Dairy)
    (role concrete)
    (pattern-match reactive)
)

(defclass Yoghurt
    (is-a Dairy)
    (role concrete)
    (pattern-match reactive)
)

(defclass Fat
    (is-a Ingredient)
    (role concrete)
    (pattern-match reactive)
)

(defclass AnimalFat
    (is-a Fat)
    (role concrete)
    (pattern-match reactive)
)

(defclass VegetalFat
    (is-a Fat)
    (role concrete)
    (pattern-match reactive)
)

(defclass Nuts
    (is-a VegetalFat)
    (role concrete)
    (pattern-match reactive)
)

(defclass Oil
    (is-a VegetalFat)
    (role concrete)
    (pattern-match reactive)
)

(defclass Fruit
    (is-a Ingredient)
    (role concrete)
    (pattern-match reactive)
)

(defclass Protein
    (is-a Ingredient)
    (role concrete)
    (pattern-match reactive)
)

(defclass AnimalProtein
    (is-a Protein)
    (role concrete)
    (pattern-match reactive)
)

(defclass BlueFish
    (is-a AnimalProtein)
    (role concrete)
    (pattern-match reactive)
)

(defclass CuredMeat
    (is-a AnimalProtein)
    (role concrete)
    (pattern-match reactive)
)

(defclass Egg
    (is-a AnimalProtein)
    (role concrete)
    (pattern-match reactive)
)

(defclass RedMeat
    (is-a AnimalProtein)
    (role concrete)
    (pattern-match reactive)
)

(defclass Shellfish
    (is-a AnimalProtein)
    (role concrete)
    (pattern-match reactive)
)

(defclass WhiteFish
    (is-a AnimalProtein)
    (role concrete)
    (pattern-match reactive)
)

(defclass WhiteMeat
    (is-a AnimalProtein)
    (role concrete)
    (pattern-match reactive)
)

(defclass PlantProtein
    (is-a Protein)
    (role concrete)
    (pattern-match reactive)
)

(defclass Legumes
    (is-a PlantProtein)
    (role concrete)
    (pattern-match reactive)
)

(defclass Starch
    (is-a Ingredient)
    (role concrete)
    (pattern-match reactive)
)

(defclass Flour
    (is-a Starch)
    (role concrete)
    (pattern-match reactive)
)

(defclass GlutenFlour
    (is-a Flour)
    (role concrete)
    (pattern-match reactive)
)

(defclass GlutenFreeFlour
    (is-a Flour)
    (role concrete)
    (pattern-match reactive)
)

(defclass Grains
    (is-a Starch)
    (role concrete)
    (pattern-match reactive)
)

(defclass GlutenFreeGrain
    (is-a Grains)
    (role concrete)
    (pattern-match reactive)
)

(defclass GlutenGrain
    (is-a Grains)
    (role concrete)
    (pattern-match reactive)
)

(defclass Tubers
    (is-a Starch)
    (role concrete)
    (pattern-match reactive)
)

(defclass Sugar
    (is-a Ingredient)
    (role concrete)
    (pattern-match reactive)
)

(defclass ArtificialSugar
    (is-a Sugar)
    (role concrete)
    (pattern-match reactive)
)

(defclass NaturalSugar
    (is-a Sugar)
    (role concrete)
    (pattern-match reactive)
)

(defclass Vegetable
    (is-a Ingredient)
    (role concrete)
    (pattern-match reactive)
)

(defclass Event
    (is-a USER)
    (role concrete)
    (pattern-match reactive)
    (multislot hasConstraint
        (type INSTANCE)
        (create-accessor read-write))
    (multislot NumberOfPeople
        (type SYMBOL)
        (create-accessor read-write))
)

(defclass Conference
    (is-a Event)
    (role concrete)
    (pattern-match reactive)
)

(defclass FamilyEvent
    (is-a Event)
    (role concrete)
    (pattern-match reactive)
)

(defclass Baptism
    (is-a FamilyEvent)
    (role concrete)
    (pattern-match reactive)
)

(defclass Communion
    (is-a FamilyEvent)
    (role concrete)
    (pattern-match reactive)
)

(defclass Wedding
    (is-a FamilyEvent)
    (role concrete)
    (pattern-match reactive)
)

(defclass Client
    (is-a USER)
    (role concrete)
    (pattern-match reactive)
    (multislot Organize
        (type INSTANCE)
        (create-accessor read-write))
    (multislot hasConstraint
        (type INSTANCE)
        (create-accessor read-write))
    (multislot Email
        (type STRING)
        (create-accessor read-write))
    (multislot Name
        (type STRING)
        (create-accessor read-write))
    (multislot PhoneNumber
        (type STRING)
        (create-accessor read-write))
)

(defclass CousineStyle
    (is-a USER)
    (role concrete)
    (pattern-match reactive)
    (multislot hasCousineStyle
        (type INSTANCE)
        (create-accessor read-write))
)

(defclass Menu
    (is-a USER)
    (role concrete)
    (pattern-match reactive)
    (multislot ProposedMenu
        (type INSTANCE)
        (create-accessor read-write))
    (multislot Price
        (type SYMBOL)
        (create-accessor read-write))
)

(definstances instances
)
