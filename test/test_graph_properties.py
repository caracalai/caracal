import unittest

from broutonblocks.declaration.projects import Project, SessionInfo
from broutonblocks.typesparser import TypesParser


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
            my_node_type = node_types["MyNode"]

            session = SessionInfo()
            project = Project()
            project.register_types([my_node_type])
            my_node = project.add_node(my_node_type, session)
            my_node.set_property("threshold", 0.5)
            project.serialize()
        except RuntimeError:
            self.fail("test_graph_properties01")
