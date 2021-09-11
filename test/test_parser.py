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
            """)
        node_types = {node.name: node for node in node_types}
        self.assertTrue("NodeType" in node_types)

    def test_second(self):
        parser = typesparser.TypesParser()
        self.assertRaises(typesparser.TypesParseError, parser.parse, "abc")
    

