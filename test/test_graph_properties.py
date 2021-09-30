import unittest
from bblocks.typesparser import typesparser
from bblocks.declaration.project import *

class CheckGraphProperties(unittest.TestCase):
    def __init__(self, methodName='runTest'):
        super(CheckGraphProperties, self).__init__(methodName)
        self._program = """
                node MyNode:
                    properties:
                        threshold?: float(0.8) // default value
                        border_width: int(10)
                """
    def test_graph_properties01(self):
        try:
            parser = typesparser.TypesParser()
            node_types = parser.parse(self._program)
            node_types = dict({t.name: t for t in node_types})
            MyNodeType = node_types["MyNode"]

            graph = Project()
            myNode = graph.add_node(MyNodeType)
            myNode.set_property("threshold", 0.5)
            graph.serialize()
        except RuntimeError:
            self.fail("test_graph_properties01")
