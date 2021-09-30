import pickle


class ProgrammingLanguage:
    Python = 0,
    Cpp = 1,
    NodeJs = 2

class Attribute:
    def __init__(self):
        self.name = ""
        self.values = {}

    def serialize(self):
        return {
            "name": self.name
        }

class MetaInfo:
    def __init__(self, **kwargs):
        pass

    def serialize(self):
        return {}

class PropertyDeclaration:
    def __init__(self, data_type, optional, default_value=None):
        self.data_type = data_type
        self.is_optional = optional
        self.default_value = default_value

    def serialize(self):
        return {
            "data_type": self.data_type,
            "is_optional": self.is_optional,
            "default_value": self.default_value
        }



class MethodDeclaration:
    def __init__(self, name, data_type, info=None):
        self.name = name
        self.data_type = data_type

    @property
    def argument_names(self):
        return self.data_type.names

    @property
    def argument_types(self):
        return self.data_type.types

    def serialize(self):
        return {
            "name": self.name,
            "data_type": self.data_type
        }


class HandlerDeclaration(MethodDeclaration):
    def __init__(self, name, data_type, receives_multiple, info=None):
        super(HandlerDeclaration, self).__init__(name, data_type, info)
        self.receives_multiple = receives_multiple

    def __str__(self):
        result = "{type}".format(type=self.data_type)
        if self.single == False:
            result += " [can be multiple]"
        return result


class EventDeclaration(MethodDeclaration):
    def __str__(self):
        result = "{type}".format(type=self.data_type)
        return result

    @property
    def id(self):
        return "property_{id}"


class NodeTypeDeclaration:
    def __init__(self):
        self.handlers = {}
        self.events = {}
        self.properties = {}
        self.name = None
        self.attributes = []

    @property
    def id(self):
        return self.name

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


    def serialize(self):
        result = {}
        result["name"] = self.name

        handlers = {}
        for item in self.handlers.values():
            handlers[item.id] = item.serialize()
        result["handlers"] = handlers

        events = {}
        for item in self.events.values():
            events[item.id] = item.serialize()
        result["handlers"] = events

        properties = {}
        for item in self.properties.values():
            properties[item.id] = item.serialize()
        result["handlers"] = properties

        return result

        # for n in self.nodes.values():
        #     properties = {}
        #     for prop_name, info in n.type.properties.items():
        #         prop_value = info.default_value
        #         if prop_name in n.property_values:
        #             prop_value = n.property_values[prop_name]
        #         if prop_value != None:
        #             properties[prop_name] = base64.b64encode(
        #                 ProtoSerializer().serialize_message(0, prop_value).SerializeToString()
        #             ).decode('ascii')
        #     result["nodes"][n.id] = {
        #         "type": {
        #             "name": n.type.name,
        #             "properties": properties
        #         }
        #     }
