import json
import pkg_resources


class Gamedata(object):
    def __init__(self):
        self._data = {}
        self.features = {}
        self.entities = {}

    def load(self):
        self._data = json.load(pkg_resources.resource_stream('pyro', 'data/gamedata.json'))

        for feature in self._data['features']:
            self.features[feature['name']] = feature

        for entity in self._data['entities']:
            entity.setdefault('health', 0)
            entity.setdefault('damage', 0)
            entity.setdefault('armor', 0)
            self.entities[entity['name']] = entity

    def get(self, name):
        return self._data[name]

    def get_feature(self, name):
        return self.features[name]

    def get_entity(self, name):
        return self.entities[name]


gamedata = Gamedata()
