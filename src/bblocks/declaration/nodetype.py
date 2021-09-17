import functools

from bblocks.declaration.datatypes import *


def handler(name, type, receives_multiple=False, info=None):
    @functools.wraps
    def handler_instance(func):
        def wrapper(self, msg):
            func(msg)

    return handler_instance

class Property:
    def __init__(self, tp, optional, default_value=None):
        self._type = tp
        self._is_optional = optional
        self._default_value = default_value
        self.value = self.default_value
        self.parent = None

    def set_value(self, value):
        self.value = value

    @property
    def type(self):
        return self._type

    @property
    def default_value123(self):
        return self._default_value

    @property
    def is_optional(self):
        return self._is_optional

    def __str__(self):
        return str(self.value)

class MethodInfo:
    def __init__(self, tp, info=None):
        self._type = tp
        self.parent = None

    @property
    def type(self):
        return self._type

    @property
    def argument_names(self):
        return self._type.names

    @property
    def argument_types(self):
        return self._type.types


class Event(MethodInfo):
    def __str__(self):
        result = "{type}".format(type=self.type)
        return result

class HandlerInfo(MethodInfo):
    def __init__(self, tp, single):
        super(HandlerInfo, self).__init__(tp)
        self._single = single

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
