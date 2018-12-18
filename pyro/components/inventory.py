from . import Component


class InventoryComponent(Component):
    def __init__(self):
        super(InventoryComponent, self).__init__()
        self.max_items = 10
        self.items = []

    def config(self, values):
        self.max_items = int(values[0])

    def take_item(self, entity):
        self.items.append(entity.eid)

    def use_item(self, slot):
        item = self.items[slot]
        print(item)
