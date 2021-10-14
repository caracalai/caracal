import unittest

from broutonblocks.declaration import Project, SessionInfo
from broutonblocks.typesparser import TypesParser


class TestProject(unittest.TestCase):
    def __init__(self, methodName="runTest"):
        super(TestProject, self).__init__(methodName)

    def test_00(self):
        try:
            my_type = """
                    node MyType:
                        handlers:
                            handler(value: int)

                    @namespace(value="abc")
                    node MyType:
                        handlers:
                            handler(value: int)
                    """

            parser = TypesParser()
            types = parser.parse(my_type)
            first_type = types["MyType"]
            second_type = types["abc:MyType"]

            project = Project()
            project.add_node_type(first_type)
            project.add_node_type(second_type)
            self.assertTrue(len(project.node_types) == 2)
            self.assertEqual(project.node_types[first_type.uid].name, "MyType")
            self.assertEqual(project.node_types[second_type.uid].name, "MyType")

            project.remove_node_type(first_type)
            self.assertTrue(len(project.node_types) == 1)
        except RuntimeError:
            self.fail("test_graph_properties01")

    def test_properties(self):
        program = """
                    node MyNode:
                        properties:
                            threshold?: float(0.8) // default value
                            border_width: int(10)
                    """

        try:
            parser = TypesParser()
            node_types = parser.parse(program)
            my_node_type = node_types["MyNode"]

            session = SessionInfo()
            project = Project()
            project.add_node_type(my_node_type)
            my_node = project.add_node(my_node_type, session)
            my_node.set_property("threshold", 0.5)
            project.serialize()
        except RuntimeError:
            self.fail("test_graph_properties01")
