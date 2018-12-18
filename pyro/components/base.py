import re


class Component:
    def config(self, values):
        raise NotImplementedError

    @property
    def name(self):
        words = re.findall(r'[A-Z][^A-Z]*', self.__class__.__name__)
        return "_".join([word.lower() for word in words if word != "Component"])

    @property
    def class_name(self):
        return re.sub(r'Component$', '', self.__class__.__name__)

    def __repr__(self):
        return "Component(name: %s, class_name: %s)" % (
            self.name, self.class_name)
