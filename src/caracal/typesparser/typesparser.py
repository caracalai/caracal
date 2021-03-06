import itertools
from antlr4.InputStream import InputStream
from antlr4 import CommonTokenStream
from caracal.typesparser import CaracalTypesLexer, CaracalTypesParser
from caracal.declaration import datatypes, nodetype
from antlr4.error.ErrorStrategy import *


class TypesParseError(Exception):
    def __init__(self, original_error):
        self.originalError = original_error


class MyErrorStrategy2(DefaultErrorStrategy):
    def __init__(self):
        super().__init__()
        self._has_errors = False

    def beginErrorCondition(self, recognizer):
        super(MyErrorStrategy2, self).beginErrorCondition(recognizer)
        self._has_errors = True


class MyErrorStrategy(DefaultErrorStrategy):
    def recover(self, recognizer, e):
        context = recognizer._ctx
        while context is not None:
            context.exception = e
            context = context.parentCtx
        raise TypesParseError(e)

    def recoverInline(self, recognizer):
        self.recover(recognizer, InputMismatchException(recognizer))

    def sync(self, recognizer):
        pass


class TypesParser:
    def __init__(self):
        self.tree_ = None

    def _handle_caracal_type(self, caracal_type_tree):
        complex_type_name = caracal_type_tree.children[0].getText().lower()
        typelist = [self._handle_caracal_type(item) for item in caracal_type_tree.children[2::2]]

        scalar_types = {
            "object": datatypes.Object,

            # basic types
            "int": datatypes.Int,
            "float": datatypes.Float,
            "boolean": datatypes.Boolean,
            "string": datatypes.String,

            # collections
            "tuple": datatypes.Tuple,
            "list": datatypes.List,

            "ndarray": datatypes.Ndarray,
            "void": datatypes.Void
        }

        for name, tp in scalar_types.items():
            if complex_type_name == name:
                return tp(*typelist)
        raise RuntimeError(f"Type {complex_type_name} not found")

    def _handle_func_arguments(self, func_arguments_tree):
        arg_names = []
        arg_types = []
        for argument in func_arguments_tree.children[::2]:
            arg_names.append(argument.children[0].getText().lower())
            arg_types.append(self._handle_caracal_type(argument.children[2]))
        result = datatypes.Tuple(*arg_types)
        result.arg_names = arg_names
        for arg, name in zip(result.item_types, result.arg_names):
            arg.name = name
        return result

    def _handle_literal(self, literal_tree):
        if literal_tree.symbol.type == CaracalTypesParser.CaracalTypesParser.STRING_LITERAL:
            return literal_tree.getText()[1:-1]
        if literal_tree.symbol.type == CaracalTypesParser.CaracalTypesParser.FLOAT:
            return float(literal_tree.getText())
        if literal_tree.symbol.type == CaracalTypesParser.CaracalTypesParser.INTEGER:
            return int(literal_tree.getText())
        raise TypesParseError("Could not parse literal")

    def _handle_property(self, property_tree):
        name_subtree = property_tree.children[0].children
        name = name_subtree[0].getText()

        property_type = self._handle_caracal_type(property_tree.children[2])
        if len(property_tree.children) > 3:
            prop_initialization_tree = property_tree.children[3]
            prop_initialization_value_tree = prop_initialization_tree.children[1]
            value = self._handle_literal(prop_initialization_value_tree)
        else:
            value = None
        return name, nodetype.PropertyDeclaration(property_type, name, value)

    def _handle_all_properties_section(self, tree):
        result = {}
        properties_section_list = list(filter(lambda x: isinstance(x, CaracalTypesParser.CaracalTypesParser.Properties_sectionContext), tree.children[3:]))
        property_list = list(itertools.chain(*[item.children[2].children for item in properties_section_list if not item.children[2].children is None]))
        return dict(self._handle_property(property) for property in property_list)

    def _handle_all_event_sections(self, caracal_type_definition_tree):
        events_section_list = list(filter(lambda x: isinstance(x, CaracalTypesParser.CaracalTypesParser.Events_sectionContext), caracal_type_definition_tree.children[3:]))
        event_list = list(itertools.chain(*[prop.children[2].children for prop in events_section_list]))
        return dict(self._handle_event(event) for event in event_list)

    def _handle_all_handler_sections(self, caracal_type_definition_tree):
        result = {}
        handlers_section_list = list(filter(lambda x: isinstance(x, CaracalTypesParser.CaracalTypesParser.Handlers_sectionContext), caracal_type_definition_tree.children[3:]))
        handler_list = list(itertools.chain(*[item.children[2].children for item in handlers_section_list if not item.children[2].children is None]))
        return dict(self._handle_handler(handler) for handler in handler_list)

    def _handle_event(self, event_tree):
        #return {event.children[0].getText(): self._handle_func_arguments(event.children[2]) for event in event_list}

        name = event_tree.children[0].children[0].getText()
        type = self._handle_func_arguments(event_tree.children[2])
        return name, nodetype.EventDeclaration(name, type)

    def _handle_handler(self, handler_tree):
        name = handler_tree.children[0].children[0].getText()
        single = len(handler_tree.children[0].children) == 1
        tp = self._handle_func_arguments(handler_tree.children[2])
        return name, nodetype.HandlerDeclaration(name, tp, not single)


    def _handle_typenodes(self, types_tree):
        result = []
        for typenode_child in types_tree.getChildren():
            if not isinstance(typenode_child, CaracalTypesParser.CaracalTypesParser.Caracal_type_definitionContext):
                continue
            item = nodetype.NodeTypeDeclaration()
            attrs = {}
            if not typenode_child.children[0].children is None:
                for attr in typenode_child.children[0].children:
                    attribute = nodetype.Attribute()
                    attribute.name = attr.children[1].getText()
                    for param in attr.children[3::2]:
                        param_name = param.children[0].getText()
                        param_value = param.children[2].children[0]
                        if isinstance(param_value, CaracalTypesParser.CaracalTypesParser.StringContext):
                            param_value = param_value.children[0].getText()[1:-1]
                        else:
                            param_value = int(param_value.children[0].getText())
                        attribute.values[param_name] = param_value
                    attrs[attribute.name] = attribute
            item.attributes = attrs
            item.name = typenode_child.children[2].getText()
            item.properties = self._handle_all_properties_section(typenode_child)
            item.events = self._handle_all_event_sections(typenode_child)
            item.handlers = self._handle_all_handler_sections(typenode_child)
            result.append(item)
        return result

    def parse(self, program):
        input_stream = InputStream(program)
        lexer = CaracalTypesLexer.CaracalTypesLexer(input_stream)
        stream = CommonTokenStream(lexer)
        parser = CaracalTypesParser.CaracalTypesParser(stream)
        parser._errHandler = MyErrorStrategy2()

        self.tree_ = parser.caracal_types()
        if parser._errHandler._has_errors:
            raise TypesParseError("Could not parse input grammar")

        result = self._handle_typenodes(self.tree_)
        return dict({t.uid: t for t in result})


