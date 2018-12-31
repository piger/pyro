from . import Component


class CombatComponent(Component):
    def __init__(self, damage=0, defense=0, accuracy=0):
        super(CombatComponent, self).__init__()
        self.damage = damage
        self.defense = defense
        self.accuracy = accuracy

    def setup(self, config):
        if "DAMAGE" in config:
            self.damage = int(config["DAMAGE"])
        if "DEFENSE" in config:
            self.defense = int(config["DEFENSE"])
        if "ACCURACY" in config:
            self.accuracy = int(config["ACCURACY"])
