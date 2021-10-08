# Generated from ./BlockTypes.g4 by ANTLR 4.9.2
from antlr4 import *

if __name__ is not None and "." in __name__:
    from .BlockTypesParser import BlockTypesParser
else:
    from BlockTypesParser import BlockTypesParser

# This class defines a complete listener for a parse tree produced by BlockTypesParser.
class BlockTypesListener(ParseTreeListener):

    # Enter a parse tree produced by BlockTypesParser#block_types.
    def enterBlock_types(self, ctx: BlockTypesParser.Block_typesContext):
        pass

    # Exit a parse tree produced by BlockTypesParser#block_types.
    def exitBlock_types(self, ctx: BlockTypesParser.Block_typesContext):
        pass

    # Enter a parse tree produced by BlockTypesParser#block_type_definition.
    def enterBlock_type_definition(
        self, ctx: BlockTypesParser.Block_type_definitionContext
    ):
        pass

    # Exit a parse tree produced by BlockTypesParser#block_type_definition.
    def exitBlock_type_definition(
        self, ctx: BlockTypesParser.Block_type_definitionContext
    ):
        pass

    # Enter a parse tree produced by BlockTypesParser#attributes.
    def enterAttributes(self, ctx: BlockTypesParser.AttributesContext):
        pass

    # Exit a parse tree produced by BlockTypesParser#attributes.
    def exitAttributes(self, ctx: BlockTypesParser.AttributesContext):
        pass

    # Enter a parse tree produced by BlockTypesParser#attribute.
    def enterAttribute(self, ctx: BlockTypesParser.AttributeContext):
        pass

    # Exit a parse tree produced by BlockTypesParser#attribute.
    def exitAttribute(self, ctx: BlockTypesParser.AttributeContext):
        pass

    # Enter a parse tree produced by BlockTypesParser#attr_param.
    def enterAttr_param(self, ctx: BlockTypesParser.Attr_paramContext):
        pass

    # Exit a parse tree produced by BlockTypesParser#attr_param.
    def exitAttr_param(self, ctx: BlockTypesParser.Attr_paramContext):
        pass

    # Enter a parse tree produced by BlockTypesParser#attr_param_value.
    def enterAttr_param_value(self, ctx: BlockTypesParser.Attr_param_valueContext):
        pass

    # Exit a parse tree produced by BlockTypesParser#attr_param_value.
    def exitAttr_param_value(self, ctx: BlockTypesParser.Attr_param_valueContext):
        pass

    # Enter a parse tree produced by BlockTypesParser#string.
    def enterString(self, ctx: BlockTypesParser.StringContext):
        pass

    # Exit a parse tree produced by BlockTypesParser#string.
    def exitString(self, ctx: BlockTypesParser.StringContext):
        pass

    # Enter a parse tree produced by BlockTypesParser#integer.
    def enterInteger(self, ctx: BlockTypesParser.IntegerContext):
        pass

    # Exit a parse tree produced by BlockTypesParser#integer.
    def exitInteger(self, ctx: BlockTypesParser.IntegerContext):
        pass

    # Enter a parse tree produced by BlockTypesParser#properties_section.
    def enterProperties_section(self, ctx: BlockTypesParser.Properties_sectionContext):
        pass

    # Exit a parse tree produced by BlockTypesParser#properties_section.
    def exitProperties_section(self, ctx: BlockTypesParser.Properties_sectionContext):
        pass

    # Enter a parse tree produced by BlockTypesParser#properties.
    def enterProperties(self, ctx: BlockTypesParser.PropertiesContext):
        pass

    # Exit a parse tree produced by BlockTypesParser#properties.
    def exitProperties(self, ctx: BlockTypesParser.PropertiesContext):
        pass

    # Enter a parse tree produced by BlockTypesParser#handlers_section.
    def enterHandlers_section(self, ctx: BlockTypesParser.Handlers_sectionContext):
        pass

    # Exit a parse tree produced by BlockTypesParser#handlers_section.
    def exitHandlers_section(self, ctx: BlockTypesParser.Handlers_sectionContext):
        pass

    # Enter a parse tree produced by BlockTypesParser#handlers.
    def enterHandlers(self, ctx: BlockTypesParser.HandlersContext):
        pass

    # Exit a parse tree produced by BlockTypesParser#handlers.
    def exitHandlers(self, ctx: BlockTypesParser.HandlersContext):
        pass

    # Enter a parse tree produced by BlockTypesParser#events_section.
    def enterEvents_section(self, ctx: BlockTypesParser.Events_sectionContext):
        pass

    # Exit a parse tree produced by BlockTypesParser#events_section.
    def exitEvents_section(self, ctx: BlockTypesParser.Events_sectionContext):
        pass

    # Enter a parse tree produced by BlockTypesParser#events.
    def enterEvents(self, ctx: BlockTypesParser.EventsContext):
        pass

    # Exit a parse tree produced by BlockTypesParser#events.
    def exitEvents(self, ctx: BlockTypesParser.EventsContext):
        pass

    # Enter a parse tree produced by BlockTypesParser#predicates_section.
    def enterPredicates_section(self, ctx: BlockTypesParser.Predicates_sectionContext):
        pass

    # Exit a parse tree produced by BlockTypesParser#predicates_section.
    def exitPredicates_section(self, ctx: BlockTypesParser.Predicates_sectionContext):
        pass

    # Enter a parse tree produced by BlockTypesParser#predicates.
    def enterPredicates(self, ctx: BlockTypesParser.PredicatesContext):
        pass

    # Exit a parse tree produced by BlockTypesParser#predicates.
    def exitPredicates(self, ctx: BlockTypesParser.PredicatesContext):
        pass

    # Enter a parse tree produced by BlockTypesParser#prop.
    def enterProp(self, ctx: BlockTypesParser.PropContext):
        pass

    # Exit a parse tree produced by BlockTypesParser#prop.
    def exitProp(self, ctx: BlockTypesParser.PropContext):
        pass

    # Enter a parse tree produced by BlockTypesParser#prop_initialization.
    def enterProp_initialization(self, ctx: BlockTypesParser.Prop_initializationContext):
        pass

    # Exit a parse tree produced by BlockTypesParser#prop_initialization.
    def exitProp_initialization(self, ctx: BlockTypesParser.Prop_initializationContext):
        pass

    # Enter a parse tree produced by BlockTypesParser#prop_name.
    def enterProp_name(self, ctx: BlockTypesParser.Prop_nameContext):
        pass

    # Exit a parse tree produced by BlockTypesParser#prop_name.
    def exitProp_name(self, ctx: BlockTypesParser.Prop_nameContext):
        pass

    # Enter a parse tree produced by BlockTypesParser#event.
    def enterEvent(self, ctx: BlockTypesParser.EventContext):
        pass

    # Exit a parse tree produced by BlockTypesParser#event.
    def exitEvent(self, ctx: BlockTypesParser.EventContext):
        pass

    # Enter a parse tree produced by BlockTypesParser#handler.
    def enterHandler(self, ctx: BlockTypesParser.HandlerContext):
        pass

    # Exit a parse tree produced by BlockTypesParser#handler.
    def exitHandler(self, ctx: BlockTypesParser.HandlerContext):
        pass

    # Enter a parse tree produced by BlockTypesParser#func_arguments.
    def enterFunc_arguments(self, ctx: BlockTypesParser.Func_argumentsContext):
        pass

    # Exit a parse tree produced by BlockTypesParser#func_arguments.
    def exitFunc_arguments(self, ctx: BlockTypesParser.Func_argumentsContext):
        pass

    # Enter a parse tree produced by BlockTypesParser#argument.
    def enterArgument(self, ctx: BlockTypesParser.ArgumentContext):
        pass

    # Exit a parse tree produced by BlockTypesParser#argument.
    def exitArgument(self, ctx: BlockTypesParser.ArgumentContext):
        pass

    # Enter a parse tree produced by BlockTypesParser#handler_name.
    def enterHandler_name(self, ctx: BlockTypesParser.Handler_nameContext):
        pass

    # Exit a parse tree produced by BlockTypesParser#handler_name.
    def exitHandler_name(self, ctx: BlockTypesParser.Handler_nameContext):
        pass

    # Enter a parse tree produced by BlockTypesParser#block_type.
    def enterBlock_type(self, ctx: BlockTypesParser.Block_typeContext):
        pass

    # Exit a parse tree produced by BlockTypesParser#block_type.
    def exitBlock_type(self, ctx: BlockTypesParser.Block_typeContext):
        pass

    # Enter a parse tree produced by BlockTypesParser#ident.
    def enterIdent(self, ctx: BlockTypesParser.IdentContext):
        pass

    # Exit a parse tree produced by BlockTypesParser#ident.
    def exitIdent(self, ctx: BlockTypesParser.IdentContext):
        pass

    # Enter a parse tree produced by BlockTypesParser#pred.
    def enterPred(self, ctx: BlockTypesParser.PredContext):
        pass

    # Exit a parse tree produced by BlockTypesParser#pred.
    def exitPred(self, ctx: BlockTypesParser.PredContext):
        pass

    # Enter a parse tree produced by BlockTypesParser#logical_expr.
    def enterLogical_expr(self, ctx: BlockTypesParser.Logical_exprContext):
        pass

    # Exit a parse tree produced by BlockTypesParser#logical_expr.
    def exitLogical_expr(self, ctx: BlockTypesParser.Logical_exprContext):
        pass

    # Enter a parse tree produced by BlockTypesParser#expr.
    def enterExpr(self, ctx: BlockTypesParser.ExprContext):
        pass

    # Exit a parse tree produced by BlockTypesParser#expr.
    def exitExpr(self, ctx: BlockTypesParser.ExprContext):
        pass


del BlockTypesParser
