import unittest

from broutonblocks.declaration.projects import ProjectInfo


class TestProject(unittest.TestCase):
    def __init__(self, method_name="runTest"):
        super(TestProject, self).__init__(method_name)

    def test_node_type(self):
        try:
            my_type = """
                    node MyType_1:
                        handlers:
                            handler(value: int)

                    @namespace(value="abc")
                    node MyType_2:
                        handlers:
                            handler(value: int)
                    """

            project = ProjectInfo()
            my_type, abc_my_type = project.parse_node_types_from_declaration(my_type)
            self.assertTrue(len(project.node_types) == 2)
            self.assertEqual(project.node_types[my_type.uid].name, "MyType_1")
            self.assertEqual(project.node_types[abc_my_type.uid].name, "MyType_2")

            project.remove_node_type(my_type)
            self.assertTrue(len(project.node_types) == 1)
        except RuntimeError:
            self.fail("test_graph_properties01")

    def test_session(self):
        try:
            project = ProjectInfo()
            session = project.create_session("test_session")
            self.assertTrue(len(project.sessions) == 1)
            self.assertEqual(project.sessions[session.name].name, session.name)
            project.remove_session(session)
            project.serialize()
        except RuntimeError:
            self.fail("test_graph_properties01")

    def test_node(self):
        program = """
                    node MyNode:
                        properties:
                            threshold?: float(0.8) // default value
                            border_width: int(10)
                    """

        try:
            project = ProjectInfo()
            (my_type,) = project.parse_node_types_from_declaration(program)

            session = project.create_session("default")
            session_2 = project.create_session("session_2")
            self.assertTrue(len(project.sessions) == 2)

            my_node = project.create_node(my_type, session)
            self.assertTrue(len(project.nodes) == 1)
            self.assertEqual(project.sessions[session.name].name, session.name)

            project.move_node(my_node, session_2)
            self.assertTrue(len(project.nodes) == 1)
            self.assertEqual(project.sessions[session_2.name].name, session_2.name)

            project.remove_node(my_node)
            self.assertTrue(not project.nodes)

            project.serialize()
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
            project = ProjectInfo()
            (my_type,) = project.parse_node_types_from_declaration(program)

            session = project.create_session("default")
            self.assertTrue(len(project.sessions) == 1)

            my_node = project.create_node(my_type, session)
            self.assertTrue(len(project.nodes) == 1)

            my_node.set_property("threshold", 0.5)
            self.assertTrue(my_node.property_values["threshold"] == 0.5)

            project.serialize()
        except RuntimeError:
            self.fail("test_graph_properties01")

    def test_node_connection(self):
        try:
            my_type = """
                    node MyType:
                        events:
                            event(value: int)

                    @namespace(value="abc")
                    node MyType:
                        handlers:
                            handler(value: int)
                    """

            project = ProjectInfo()
            first_type, second_type = project.parse_node_types_from_declaration(my_type)
            self.assertTrue(len(project.node_types) == 2)
            self.assertEqual(project.node_types[first_type.uid].name, "MyType")
            self.assertEqual(project.node_types[second_type.uid].name, "MyType")

            session = project.create_session("default")

            first_node = project.create_node(first_type, session)
            second_node = project.create_node(second_type, session)

            edge = project.connect(first_node, "event", second_node, "handler")
            self.assertTrue(len(project.edges) == 1)

            project.remove_connection(edge)
            self.assertTrue(len(project.edges) == 0)
        except RuntimeError:
            self.fail("test_graph_properties01")