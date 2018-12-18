from . import Component, ComponentType


class DoorComponent(Component):

    NAME = 'door'
    kind = ComponentType.DOOR

    def __init__(self, initial_state=True):
        super(DoorComponent, self).__init__()
        self.state = initial_state

    def config(self, values):
        pass
