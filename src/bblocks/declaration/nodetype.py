from bblocks.declaration.datatypes import *

class HandlerInfo:
    def __init__(self, tp, single):
        self._type = tp
        self._single = single

    @property
    def type(self):
        return self._type

    @property
    def single(self):
        return self._single

    def __str__(self):
        result = "{type}".format(type=self.type)
        if self.single == False:
            result += " [can be multiple]"
        return result


class NodeType:
    def __init__(self):
        self._handlers = {}
        self._events = {}
        self._properties = {}
        self._name = None
        self._attributes = []

    @property
    def attributes(self):
        return self._attributes

    @property
    def handlers(self):
        return self._handlers

    @property
    def events(self):
        return self._events

    @property
    def properties(self):
        return self._properties

    def specializeTypes(self, types, propertyValues):
        return False, None


    @property
    def name(self):
        return self._name

    def __str__(self):
        result = 'node {name}\n'.format(name=self.name)
        result += '\tproperties:\n'
        for key, value in self.properties.items():
            result += "\t\t{name}: {type}\n".format(name=key, type=value)
        result += '\thandlers:\n'
        for key, value in self.handlers.items():
            result += "\t\t{name}: {type}\n".format(name=key, type=value)
        result += '\tevents:\n'
        for key, value in self.events.items():
            result += "\t\t{name}: {type}\n".format(name=key, type=value)
        return result
