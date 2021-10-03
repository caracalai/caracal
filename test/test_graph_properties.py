import unittest
from broutonblocks.typesparser import *
from broutonblocks.declaration.projects import *

class CheckGraphProperties(unittest.TestCase):
    def test(self):
        self._program = """
                    node MyNode:
                        properties:
                            threshold?: float(0.8) // default value
                            border_width: int(10)
                    """

        try:
            parser = TypesParser()
            node_types = parser.parse(self._program)
            MyNodeType = node_types["MyNode"]

            session = SessionInfo()
            project = Project()
            project.register_types([MyNodeType])
            myNode = project.add_node(MyNodeType, session)
            myNode.set_property("threshold", 0.5)
            project.serialize()
        except RuntimeError:
            self.fail("test_graph_properties01")
