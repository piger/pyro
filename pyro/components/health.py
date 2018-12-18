from . import Component, ComponentType


class HealthComponent(Component):

    NAME = 'health'
    kind = ComponentType.HEALTH

    def __init__(self):
        super(HealthComponent, self).__init__()
        self.health = 0

    def config(self, values):
        self.health = int(values[0])
