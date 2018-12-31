from . import Component


class PotionComponent(Component):
    """Potions

    - they can be on the map or in the inventory (just delete from cell.entities? and store
      somewhere?)
    - the player can drink or throw them
    - they must have a random mapped color
    """

    def __init__(self, potion_type):
        super(PotionComponent, self).__init__()
        self.potion_type = potion_type

    def setup(self, config):
        return
