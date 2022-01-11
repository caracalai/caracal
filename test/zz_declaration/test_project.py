import unittest

from caracal.declaration.projects import ProjectInfo

type_decl = """
                   @namespace(name="foo")
                   node MyNode:
                       properties:
                           myProp1: int(8)
                           myProp2: string("test")
                           myProp3: float(1.1)
                       handlers:
                           myHndl(myVal1:int, myVal2:string, myVal3:list(int))
                           myScndHndl+(myVal4: int)
                       events:
                           myEvt(myVal1:int)

                   @namespace(name="bar")
                   node MySecondNode:
                       properties:
                           myProp1: ndarray
                           myProp2: string("test")
                           myProp3: float(1.1)
                       handlers:
                           myHndl(myVal1:int, myVal2:string, myVal3:list(int))
                           myScndHndl+(myVal4: int)
                       events:
                           myEvt(myVal1:string)

                   @namespace(name="baz")
                   node MyThirdNode:
                       properties:
                           myProp1: ndarray
                           myProp2: boolean
                           myProp3: float(1.6)
                       handlers:
                           myHndl(myVal1:int, myVal2:string, myVal3:list(int))
                       events:
                           myEvt(myVal1:string)
                   """


class TestProject(unittest.TestCase):
    def __init__(self, method_name="runTest"):
        super(TestProject, self).__init__(method_name)

    def test_node_type(self):
        try:
            project = ProjectInfo()
            foo_type, bar_type, baz_type = project.parse_node_types_from_declaration(
                type_decl
            )
            self.assertTrue(
                project.contains_node_type(foo_type)
                and project.contains_node_type(bar_type)
                and project.contains_node_type(baz_type)
                and foo_type.project_info.uid == project.uid
                and foo_type.project_info.uid == project.uid
                and baz_type.project_info.uid == project.uid,
                "Wrong type creation in project",
            )

            project.remove_node_type(foo_type)
            self.assertTrue(
                project.contains_node_type(bar_type)
                and project.contains_node_type(baz_type)
                and not project.contains_node_type(foo_type),
                "Wrong type deletion from project",
            )
            self.assertRaises(RuntimeError, project.remove_node_type, foo_type)

        except RuntimeError:
            self.fail("Node type test has unexpected error")

    def test_session(self):
        try:
            project = ProjectInfo()
            session = project.create_session("test_session")
            session_2 = project.create_session("test_session2")
            self.assertTrue(
                project.contains_session(session) and project.contains_session(session_2),
                "Wrong session declaration",
            )
            self.assertEqual(
                project.sessions[session.uid].name,
                session.name,
                "Wrong session declaration",
            )
            self.assertEqual(
                project.sessions[session_2.uid].name,
                session_2.name,
                "Wrong session declaration",
            )

            project.remove_session(session)
            self.assertTrue(
                not project.contains_session(session)
                and project.contains_session(session_2),
                "Wrong session deletion",
            )

            self.assertRaises(RuntimeError, project.remove_session, session)
            self.assertRaises(RuntimeError, project.create_session, "test_session2")
            project.serialize()
        except RuntimeError:
            self.fail("Session test has unexpected error")

    def test_node(self):
        try:
            project = ProjectInfo()
            foo_type, bar_type, baz_type = project.parse_node_types_from_declaration(
                type_decl
            )

            session = project.create_session("default")
            session_2 = project.create_session("session_2")

            my_node = project.create_node(foo_type, session)
            my_node.set_uid("my_node")

            self.assertTrue(
                project.contains_node(my_node),
                "Wrong node declaration (node didn't related to project)",
            )
            self.assertEqual(
                project.sessions[session.uid].name,
                session.name,
                "Wrong node declaration (node didn't related to session)",
            )

            project.move_node(my_node, session_2)
            self.assertTrue(
                project.contains_node(my_node) and len(project.nodes) == 1,
                "Wrong node moving between sessions "
                "(node moved out of project or removed)",
            )
            self.assertEqual(
                project.sessions[session_2.uid].name,
                session_2.name,
                "Wrong node moving between sessions (unexpected session mutation)",
            )
            self.assertEqual(
                my_node.session,
                session_2,
                "Wrong node moving between sessions (unexpected session mutation)",
            )
            self.assertNotEqual(
                my_node.session,
                session,
                "Wrong node moving between sessions (session link didn't equals)",
            )

            project.remove_node(my_node)
            self.assertFalse(
                project.nodes, "Wrong node deletion (node is still in project)"
            )
            self.assertFalse(
                project.contains_node(my_node),
                "Wrong node deletion (node is still in project)",
            )

            project.serialize()
        except RuntimeError:
            self.fail("Node test has unexpected error")

    def test_properties(self):
        try:
            project = ProjectInfo()
            foo_type, bar_type, baz_type = project.parse_node_types_from_declaration(
                type_decl
            )

            session = project.create_session("default")
            my_node = project.create_node(foo_type, session)

            self.assertTrue(
                my_node.property_values["myProp1"] == 8,
                "Wrong prop declaration (prop with default value is not defined)",
            )

            my_node.set_property("myProp1", 10)
            self.assertTrue(
                my_node.property_values["myProp1"] == 10,
                "Wrong prop mutation (values didn't equals)",
            )

            self.assertRaises(
                RuntimeError,
                my_node.set_property,
                ("myProp10", 10),
                "Wrong prop mutation (can mutate non existing prop)",
            )

            self.assertRaises(
                RuntimeError,
                my_node.set_property,
                ("myProp1", "not valid value"),
                "Wrong prop mutation (types didn't match)",
            )

            project.serialize()
        except RuntimeError:
            self.fail("Node props test has unexpected error")

    def test_node_connection(self):
        try:
            project = ProjectInfo()
            foo_type, bar_type, baz_type = project.parse_node_types_from_declaration(
                type_decl
            )

            session = project.create_session("default")

            first_node = project.create_node(foo_type, session)
            second_node = project.create_node(bar_type, session)

            edge = project.connect(first_node, "myEvt", second_node, "myScndHndl")
            self.assertTrue(
                project.contains_connection(edge),
                "Wrong connection definition (connection is not in project)",
            )

            project.remove_connection(edge)
            self.assertTrue(
                not project.contains_connection(edge) and len(project.edges) == 0,
                "Wrong connection deletion (connection is not deleted from project)",
            )

            self.assertRaises(
                RuntimeError, project.remove_connection, edge
            )  # can delete non existing connection
        except RuntimeError:
            self.fail("Node connections test has unexpected error")
