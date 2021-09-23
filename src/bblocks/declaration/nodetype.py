class Handler:
    def __init__(self, name, type, receives_multiple, info, function):
        self.name = name
        self.type = type
        self.receives_multiple = receives_multiple
        self.info = info
        self.function = function
        self.connected_events = []
        self.parent = None

    def __call__(self, *args):
        self.function(self.parent, *args)

    def connect(self, event):
        self.connected_events.append(event)


def handler(name, type, receives_multiple=False, info=None, function=None):
    if function:
        return Handler(function)
    else:
        def wrapper(func):
            return Handler(name, type, receives_multiple, info, func)
        return wrapper


# def handler(node, name, type, receives_multiple=False, info=None):
#     class HandlerInstance:
#         def __init__(self, func):
#     @functools.wraps
#     def handler_instance(func):
#         def wrapper(self, msg):
#             self.func(msg)
#         return wrapper
#     return handler_instance


# def handler(node, name, type, receives_multiple=False, info=None):
#     @functools.wraps
#     def handler_instance(func):
#         def wrapper(self, msg):
#             self.func(msg)
#         return wrapper
#     return handler_instance


class Property:
    def __init__(self, tp, optional, default_value=None):
        self._type = tp
        self._is_optional = optional
        self._default_value = default_value
        self.value = default_value
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
    def __init__(self, name, tp, info=None):
        self.name = name
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

    @property
    def node_id(self):
        return self.parent.id


class ExternalEvent(Event):
    def __init__(self, name, tp, node_id):
        super(ExternalEvent, self).__init__(name, tp)
        self._parent_node_id = node_id

    @property
    def node_id(self):
        return self._parent_node_id


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
