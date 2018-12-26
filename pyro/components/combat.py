from . import Component


class CombatComponent(Component):
    def __init__(self, damage=0, defense=0, accuracy=0):
        super(CombatComponent, self).__init__()
        self.damage = damage
        self.defense = defense
        self.accuracy = accuracy

    def config(self, values):
        m = {"DAMAGE": "damage", "DEFENSE": "defense", "ACCURACY": "accuracy"}
        for i in range(0, len(values), 2):
            name = values[i]
            value = values[i + 1]
            setattr(self, m[name], int(value))
