from enum import Enum

class TypeOccurence(str, Enum):
    uneFois = "une fois"
    chaqueJour = "chaque jour"
    chaqueSemaine = "chaque semaine"
    mensuel = "mensuel"
    bimestriel = "bimestriel"
    trimestriel = "trimestriel"
    annuel = "annuel"
