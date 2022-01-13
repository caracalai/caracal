import typing
import uuid

import caracal.declaration.datatypes as caratypes


class ProgrammingLanguage:
    Python = (0,)
    Cpp = (1,)
    NodeJs = (2,)


class Attribute:
    def __init__(self):
        self.name: str = ""
        self.values: dict = {}


class MetaInfo:
    def __init__(self, **kwargs):
        pass


class PropertyDeclaration:
    def __init__(
        self,
        data_type: type,
        name: str = None,
        default_value: object = None,
    ):
        self.name: str = name
        self.data_type = data_type
        self.default_value: object = default_value

    @property
    def uid(self) -> str:
        return "property"

    def __str__(self):
        if self.default_value is None:
            return f"{self.name}: {self.data_type}"
        else:
            value = (
                self.default_value
                if not isinstance(self.default_value, str)
                else f'"{self.default_value}"'
            )
            return f"{self.name}: {self.data_type}({value})"


class MethodDeclaration:
    def __init__(
        self, name: str, data_type: tuple, info: typing.Union[MetaInfo, None] = None
    ):
        self.name: str = name
        self.info: typing.Union[MetaInfo, None] = info
        self.data_type = (
            caratypes.Tuple(*data_type)
            if not isinstance(data_type, caratypes.Tuple)
            else data_type
        )
        if not self.data_type.arg_names:
            self.data_type.arg_names = [
                data_type.name for data_type in self.data_type.item_types
            ]

    @property
    def argument_names(self):
        if all(self.data_type.arg_names):
            return self.data_type.arg_names
        else:
            return [f"value_{idx}" for idx in range(len(self.data_type.item_types))]

    @property
    def argument_types(self):
        return self.data_type.item_types


class HandlerDeclaration(MethodDeclaration):
    def __init__(self, name: str, data_type, receives_multiple: bool, info: str = None):
        super(HandlerDeclaration, self).__init__(name, data_type, info)
        self.receives_multiple = receives_multiple
        self.uid = str(uuid.uuid4())

    def __str__(self):
        result = f"{self.name}+" if self.receives_multiple else f"{self.name}"
        result += str(
            tuple(
                f"value{idx}: {arg_type}"
                for idx, arg_type in enumerate(self.argument_types, start=1)
            )
        )
        return result.replace("'", "").replace(",)", ")")


class EventDeclaration(MethodDeclaration):
    @property
    def uid(self) -> str:
        return self.name

    def __str__(self):
        result = f"{self.name}"
        result += str(
            tuple(
                f"value{idx}: {arg_type}"
                for idx, arg_type in enumerate(self.argument_types, start=1)
            )
        )
        return result.replace("'", "").replace(",)", ")")


class NodeTypeDeclaration:
    NAMESPACE_ATTRIBUTE = "namespace"
    GLOBAL_NAMESPACE_NAME = "global"

    def __init__(self):
        self.handlers: dict = {}
        self.events: dict = {}
        self.properties: dict = {}
        self.name: typing.Union[str, None] = None
        self.attributes: dict = {}
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
        result = '@namespace(name="{namespace}")\nnode {name}:\n'.format(
            namespace=self.namespace, name=self.name
        )
        properties = "\tproperties:\n"
        for value in self.properties.values():
            properties += "\t\t{prop}\n".format(prop=str(value))
        if properties != "\tproperties:\n":
            result += properties
        handlers = "\thandlers:\n"
        for value in self.handlers.values():
            handlers += "\t\t{handler}\n".format(handler=str(value))
        if handlers != "\thandlers:\n":
            result += handlers
        events = "\tevents:\n"
        for value in self.events.values():
            events += "\t\t{event}\n".format(event=str(value))
        if events != "\tevents:\n":
            result += events
        return result
