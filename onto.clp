(defmodule ONTOLOGY
  (export ?ALL))

(defclass ONTOLOGY::Recipe
  (is-a USER)
  (role concrete)
  (pattern-match reactive)

  (slot title            (type STRING))
  (slot price            (type NUMBER) (default 0.0))
  (slot wine_pairing     (type STRING)   (default ""))
  (multislot meal-types
    (type SYMBOL))
    

  (multislot restrictions
    (type SYMBOL)
    )

  (multislot ingredients (type SYMBOL))
  (slot seasons          (type SYMBOL)
                         (allowed-symbols any-season spring summer autumn winter)
                         (default any-season)))