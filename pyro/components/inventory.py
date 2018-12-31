from . import Component


class InventoryComponent(Component):
    def __init__(self):
        super(InventoryComponent, self).__init__()
        self.max_items = 10
        self.items = []

    def setup(self, config):
        self.max_items = int(config["SIZE"])

    def take_item(self, entity):
        self.items.append(entity.eid)

    def use_item(self, slot):
        item = self.items[slot]
        print(item)
