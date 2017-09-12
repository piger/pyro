import json
import pkg_resources


class Gamedata(object):
    def __init__(self):
        self._data = {}
        self.features = {}
        self.entities = {}
        self.potions = {}
        self.weapons = {}
        self.scrolls = {}
        self.potion = {}

    def load(self):
        self._data = json.load(pkg_resources.resource_stream('pyro', 'data/gamedata.json'))

        for feature in self._data['features']:
            self.features[feature['name']] = feature

        for entity in self._data['entities']:
            self.entities[entity['name']] = entity

        for entity in self._data['weapons']:
            self.weapons[entity['name']] = entity

        for entity in self._data['scrolls']:
            self.scrolls[entity['name']] = entity

    def get(self, name):
        return self._data[name]

    def get_feature(self, name):
        return self.features[name]

    def get_entity(self, name):
        return self.entities[name]

    def get_weapon(self, name):
        return self.weapons[name]

    def get_scroll(self, name):
        return self.scrolls[name]


gamedata = Gamedata()
