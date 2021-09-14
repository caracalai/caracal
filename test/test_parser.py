import unittest
from bblocks.typesparser import typesparser

class CheckGraphExecution(unittest.TestCase):
    def test_first(self):
        parser = typesparser.TypesParser()
        node_types = parser.parse(
            """
            node NodeType:
                handlers:
                    value(val:int)
                    value2(a: tuple(int, int))
                events:                       
                    event1(a: int, b: float)
            """)
        node_types = {node.name: node for node in node_types}

        self.assertTrue("NodeType" in node_types)
        handler = node_types["NodeType"].handlers["value"]
        self.assertTrue(len(handler.argument_names) == 1, "Handler contains value")
        self.assertTrue(len(handler.argument_names) == len(handler.argument_types))
        self.assertTrue(handler.argument_names[0] == "val")

        event = node_types["NodeType"].events["event1"]
        self.assertTrue(len(event.argument_names) == 2, "Event contains value")
        self.assertTrue(len(event.argument_names) == len(event.argument_types))
        self.assertTrue(event.argument_names[0] == "a")
        self.assertTrue(event.argument_names[1] == "b")

    def test_second(self):
        parser = typesparser.TypesParser()
        self.assertRaises(typesparser.TypesParseError, parser.parse, "wrong program")



