import itertools
from antlr4.InputStream import InputStream
from antlr4 import CommonTokenStream
from bblocks.typesparser import BlockTypesLexer, BlockTypesParser
from bblocks.declaration import nodetype
from bblocks.declaration import attributes, datatypes
from antlr4.error.ErrorStrategy import *



class TypesParseError(Exception):
    def __init__(self, originalError):
        self.originalError = originalError


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

    def _handle_block_type(self, block_type_tree):
        complex_type_name = block_type_tree.children[0].getText().lower()
        typelist = [self._handle_block_type(item) for item in block_type_tree.children[2::2]]

        scalar_types = {
            "object": datatypes.ObjectType,
            "videostream": datatypes.VideoStreamType,
            "image": datatypes.ImageType,
            "string": datatypes.StringType,
            "rect": datatypes.RectType,
            "number": datatypes.NumberType,
            "int": datatypes.IntType,
            "boolean": datatypes.BooleanType,
            "tuple": datatypes.TupleType,
            "list": datatypes.ListType,
            "void": datatypes.VoidType
        }

        for name, tp in scalar_types.items():
            if complex_type_name == name:
                return tp(*typelist)
        raise RuntimeError("Type {type} not found".format(type=complex_type_name))

    def _handle_func_arguments(self, func_arguments_tree):
        arg_names = []
        arg_types = []
        for argument in func_arguments_tree.children[::2]:
            arg_names.append(argument.children[0].getText().lower())
            arg_types.append(self._handle_block_type(argument.children[2]))
        return datatypes.TupleType(arg_types, arg_names)


    def _handle_properties_section(self, tree):
        properties = list(filter(lambda x: isinstance(x, BlockTypesParser.BlockTypesParser.Properties_sectionContext), tree.children[3:]))
        properties = list(itertools.chain(*[prop.children[2].children for prop in properties]))
        return {prop.children[0].getText(): self._handle_block_type(prop.children[2]) for prop in properties}

    def _handle_all_event_sections(self, block_type_definition_tree):
        events_section_list = list(filter(lambda x: isinstance(x, BlockTypesParser.BlockTypesParser.Events_sectionContext), block_type_definition_tree.children[3:]))
        event_list = list(itertools.chain(*[prop.children[2].children for prop in events_section_list]))
        return {event.children[0].getText(): self._handle_func_arguments(event.children[2]) for event in event_list}

    def _handle_handler(self, handler_tree):
        name = handler_tree.children[0].children[0].getText()
        single = len(handler_tree.children[0].children) == 1
        tp = self._handle_func_arguments(handler_tree.children[2])
        return name, nodetype.HandlerInfo(tp, single)

    def _handle_all_handler_sections(self, block_type_definition_tree):
        result = {}
        handlers_section_list = list(filter(lambda x: isinstance(x, BlockTypesParser.BlockTypesParser.Handlers_sectionContext), block_type_definition_tree.children[3:]))
        handler_list = list(itertools.chain(*[item.children[2].children for item in handlers_section_list if not item.children[2].children is None]))
        return dict(self._handle_handler(handler) for handler in handler_list)

    def _handle_typenodes(self, types_tree):
        result = []
        for typenode_child in types_tree.getChildren():
            if not isinstance(typenode_child, BlockTypesParser.BlockTypesParser.Block_type_definitionContext):
                continue
            item = nodetype.NodeType()
            attrs = []
            if not typenode_child.children[0].children is None:
                for attr in typenode_child.children[0].children:
                    attribute = attributes.Attribute()
                    attribute.name = attr.children[1].getText()
                    for param in attr.children[3::2]:
                        param_name = param.children[0].getText()
                        param_value = param.children[2].children[0]
                        if isinstance(param_value, BlockTypesParser.BlockTypesParser.StringContext):
                            param_value = param_value.children[0].getText()[1:-1]
                        else:
                            param_value = int(param_value.children[0].getText())
                        attribute.values[param_name] = param_value
                    attrs.append(attribute)
            item._attributes = attrs
            item._name = typenode_child.children[2].getText()
            item._properties = self._handle_properties_section(typenode_child)
            item._events = self._handle_all_event_sections(typenode_child)
            item._handlers = self._handle_all_handler_sections(typenode_child)
            result.append(item)
        return result

    def parse(self, program):
        input_stream = InputStream(program)
        lexer = BlockTypesLexer.BlockTypesLexer(input_stream)
        stream = CommonTokenStream(lexer)
        parser = BlockTypesParser.BlockTypesParser(stream)
        parser._errHandler = MyErrorStrategy2()

        self.tree_ = parser.block_types()
        if parser._errHandler._has_errors:
            raise TypesParseError("Could not parse input grammar")
        return self._handle_typenodes(self.tree_)
