import uuid


class ProgrammingLanguage:
    Python = (0,)
    Cpp = (1,)
    NodeJs = (2,)


class Attribute:
    def __init__(self):
        self.name = ""
        self.values = {}


class MetaInfo:
    def __init__(self, **kwargs):
        pass


class PropertyDeclaration:
    def __init__(self, data_type, optional, default_value=None):
        self.data_type = data_type
        self.optional = optional
        self.default_value = default_value


class MethodDeclaration:
    def __init__(self, name, data_type, info=None):
        self.name = name
        self.data_type = data_type

    @property
    def argument_names(self):
        return self.data_type.names

    @property
    def argument_types(self):
        return self.data_type.item_types


class HandlerDeclaration(MethodDeclaration):
    def __init__(self, name, data_type, receives_multiple, info=None):
        super(HandlerDeclaration, self).__init__(name, data_type, info)
        self.receives_multiple = receives_multiple
        self.uid = str(uuid.uuid4())

    def __str__(self):
        result = f"{self.name}: {self.data_type}"
        if self.receives_multiple:
            result += " [can be multiple]"
        return result


class EventDeclaration(MethodDeclaration):
    def __init__(self, name, data_type):
        super().__init__(name, data_type)
        self.uid = str(uuid.uuid4())

    def __str__(self):
        result = f"{self.name}: {self.data_type}"
        return result


class NodeTypeDeclaration:
    NAMESPACE_ATTRIBUTE = "namespace"
    GLOBAL_NAMESPACE_NAME = "global"

    def __init__(self):
        self.handlers = {}
        self.events = {}
        self.properties = {}
        self.name = None
        self.attributes = {}
        self.project_info = None
        self.uid: str = str(uuid.uuid4())

    @property
    def namespace(self):
        if self.NAMESPACE_ATTRIBUTE in self.attributes:
            return self.attributes[self.NAMESPACE_ATTRIBUTE].values["name"]
        return self.GLOBAL_NAMESPACE_NAME

    @namespace.setter
    def namespace(self, val):
        old_node_type_key = self.uid

        if self.NAMESPACE_ATTRIBUTE not in self.attributes:
            self.attributes[self.NAMESPACE_ATTRIBUTE] = Attribute()
        self.attributes[self.NAMESPACE_ATTRIBUTE].values["name"] = val

        if (
            self.project_info is not None
        ):  # if the object is used outside of a ProjectInfo object
            self.project_info.node_types[self.uid] = self.project_info.node_types.pop(
                old_node_type_key
            )

    @namespace.deleter
    def namespace(self):
        if self.NAMESPACE_ATTRIBUTE in self.attributes:
            del self.attributes[self.NAMESPACE_ATTRIBUTE]

    def __str__(self):
        result = "node {name}\n".format(name=self.name)
        result += "\tdeclaration:\n"
        for key, value in self.properties.items():
            result += "\t\t{name}: {type}\n".format(name=key, type=value)
        result += "\thandlers:\n"
        for key, value in self.handlers.items():
            result += "\t\t{name}: {type}\n".format(name=key, type=value)
        result += "\tevents:\n"
        for key, value in self.events.items():
            result += "\t\t{name}: {type}\n".format(name=key, type=value)
        return result

    # def serialize(self):
    #     result = {"name": self.name}
    #
    #     handlers = {}
    #     for item in self.handlers.values():
    #         handlers[item.id] = item.serialize()
    #     result["handlers"] = handlers
    #
    #     events = {}
    #     for item in self.events.values():
    #         events[item.id] = item.serialize()
    #     result["events"] = events
    #
    #     declaration = {}
    #     for item in self.declaration.values():
    #         declaration[item.id] = item.serialize()
    #     result["declaration"] = declaration
    #
    #     return result
    #
    #     # for n in self.nodes.values():
    #     #     declaration = {}
    #     #     for prop_name, info in n.type.declaration.items():
    #     #         prop_value = info.default_value
    #     #         if prop_name in n.property_values:
    #     #             prop_value = n.property_values[prop_name]
    #     #         if prop_value != None:
    #     #             declaration[prop_name] = base64.b64encode(
    #     #                 ProtoSerializer().serialize_message(0, prop_value)
    #     #                 .SerializeToString()
    #     #             ).decode('ascii')
    #     #     result["nodes"][n.id] = {
    #     #         "type": {
    #     #             "name": n.type.name,
    #     #             "declaration": declaration
    #     #         }
    #     #     }
