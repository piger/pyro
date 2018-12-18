from . import Component


class HealthComponent(Component):
    def __init__(self):
        super(HealthComponent, self).__init__()
        self.health = 0

    def config(self, values):
        self.health = int(values[0])
