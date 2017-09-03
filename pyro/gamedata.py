import json
import pkg_resources


class Gamedata(object):
    def __init__(self):
        self._data = {}
        self._features = {}
        self._entities = {}

    def load(self):
        self._data = json.load(pkg_resources.resource_stream('pyro', 'data/gamedata.json'))
        for feature in self._data['features']:
            self._features[feature['name']] = feature
        for entity in self._data['entities']:
            self._entities[entity['name']] = entity

    def get(self, name):
        return self._data[name]

    def get_feature(self, name):
        return self._features[name]

    def get_entity(self, name):
        return self._entities[name]


gamedata = Gamedata()
