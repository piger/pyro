from . import Component


class DoorComponent(Component):
    def __init__(self, initial_state=False):
        super(DoorComponent, self).__init__()
        self.state = initial_state

    def config(self, values):
        pass

    @property
    def is_open(self):
        return self.state

    def toggle(self):
        self.state = not self.state

    def open(self):
        self.state = True

    def close(self):
        self.state = False
