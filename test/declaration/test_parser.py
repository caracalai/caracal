from typing import Dict
import unittest

from caracal.declaration.nodetype import NodeTypeDeclaration
from caracal.typesparser import TypesParseError, TypesParser


class TestParse(unittest.TestCase):
    def __init__(self, method_name="runTest"):
        super(TestParse, self).__init__(method_name)

    def test_first(self):
        parser = TypesParser()
        node_types: Dict[str, NodeTypeDeclaration] = parser.parse(
            """
            node NodeType:
                handlers:
                    value(val:int)
                    processFile(file:string)
                    value2(a: tuple(int, int))
                events:
                    event1(a: int, b: float)
            """
        )
        node_type_uid = [
            node_type.uid
            for node_type in node_types.values()
            if node_type.name == "NodeType"
        ][0]
        self.assertTrue(node_type_uid in node_types)
        handler = node_types[node_type_uid].handlers["value"]
        self.assertTrue(len(handler.argument_names) == 1, "Handler contains value")
        self.assertTrue(len(handler.argument_names) == len(handler.argument_types))
        self.assertTrue(handler.argument_names[0] == "val")

        event = node_types[node_type_uid].events["event1"]
        self.assertTrue(len(event.argument_names) == 2, "Event contains value")
        self.assertTrue(len(event.argument_names) == len(event.argument_types))
        self.assertTrue(event.argument_names[0] == "a")
        self.assertTrue(event.argument_names[1] == "b")

    def test_second(self):
        parser = TypesParser()
        self.assertRaises(TypesParseError, parser.parse, "wrong program")

    # TODO this test do nothing
    # def test_complex_types(self):
    #     try:
    #         parser = TypesParser()
    #         node_types = parser.parse(
    #             """
    #             node FirstNode:
    #                 properties:
    #                     threshold?: float(0.8) // default value
    #                     border_width: int(10)
    #
    #             @namespace(value="abc")
    #             node FirstNode:
    #                 properties:
    #                     threshold?: float(0.8) // default value
    #                     border_width: int(10)
    #             """
    #         )
    #         # node_types["FirstNode"]
    #     except RuntimeError:
    #         self.fail("test_complex_types")
