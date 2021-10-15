import unittest

from broutonblocks.typesparser import TypesParseError, TypesParser


class CheckGraphExecution(unittest.TestCase):
    def test_first(self):
        parser = TypesParser()
        node_types = parser.parse(
            """
            node NodeType:
                handlers:
                    value(val:int)
                    processFile(file:BinaryFile)
                    value2(a: tuple(int, int))
                events:
                    event1(a: int, b: float)
            """
        )

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
        parser = TypesParser()
        self.assertRaises(TypesParseError, parser.parse, "wrong program")

    def test_complex_types(self):
        try:
            parser = TypesParser()
            node_types = parser.parse(
                """
                node FirstNode:
                    properties:
                        threshold?: float(0.8) // default value
                        border_width: int(10)

                @namespace(value="abc")
                node FirstNode:
                    properties:
                        threshold?: float(0.8) // default value
                        border_width: int(10)
                """
            )
            node_types["FirstNode"]
        except RuntimeError:
            self.fail("test_complex_types")
