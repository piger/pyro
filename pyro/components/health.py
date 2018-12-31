from . import Component


class HealthComponent(Component):
    def __init__(self):
        super(HealthComponent, self).__init__()
        self.health = 0

    def setup(self, config):
        self.health = int(config["HP"])
