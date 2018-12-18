from . import Component


class DoorComponent(Component):
    def __init__(self, initial_state=True):
        super(DoorComponent, self).__init__()
        self.state = initial_state

    def config(self, values):
        pass
