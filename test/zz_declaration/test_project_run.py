import unittest

from broutonblocks.declaration import MetaInfo
from broutonblocks.declaration.projects import ProjectInfo
import broutonblocks.declaration.datatypes as bbtypes
from broutonblocks.execution import Event, handler, Node, Property, Session
from broutonblocks.typesparser import TypesParser


class Node1(Node):
    def __init__(self, uid=None):
        super().__init__(uid)
        self.threshold = Property(bbtypes.Int(), default_value=10, optional=True)
        self.value = Event("value", bbtypes.Int())
        self.session.add(self)

    def run(self):
        self.fire(self.value, 10)


result = -1


class Node2(Node):
    def __init__(self, id_=None):
        super().__init__(id_)
        self.result = Event("result", bbtypes.Int())
        self.session.add(self)

    @handler("handler1", bbtypes.Int(), False, MetaInfo())
    def handler1(self, msg):
        self.fire(self.result, msg.value + 10)


class ResultNode(Node):
    def __init__(self, id_=None):
        super().__init__(id_)

    @handler("result", bbtypes.Int(), False, MetaInfo())
    def result(self, msg):
        global result
        result = msg.value
        self.terminate()


class TestProject(unittest.TestCase):
    def __init__(self, methodName="runTest"):
        super(TestProject, self).__init__(methodName)

    def test_run_project(self):
        program = """
        node Node1:
            properties:
                threshold: int(10)
            events:
                value(value: int)
        node Node2:
            handlers:
                handler1(value: int)
            events:
                result(result: int)
       node ResultNode:
            handlers:
                result(result: int)


        """
        project = ProjectInfo()
        first_type, second_type, third_type = project.parse_node_types_from_declaration(program)
        session_info = project.create_session("default")
        node1 = project.create_node(first_type, session_info)
        node2 = project.create_node(second_type, session_info)
        node3 = project.create_node(third_type, session_info)
        project.connect(node1, "value", node2, "handler1")
        project.connect(node2, "result", node3, "result")

        with Session("default") as session:
            session.register_types([Node1, Node2, ResultNode])
            session.run_project(project)
        self.assertEqual(result, 20)
