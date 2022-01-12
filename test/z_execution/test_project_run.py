import unittest

from caracal.declaration import MetaInfo
import caracal.declaration.datatypes as cara_types
from caracal.declaration.projects import ProjectInfo
from caracal.execution import Event, handler, Node, Property, Session


class Node1(Node):
    threshold = Property(cara_types.Int(), default_value=10)
    value = Event("value", cara_types.Int())

    def run(self):
        self.fire(self.value, 10)


result = -1


class Node2(Node):
    result = Event("result", cara_types.Int())

    @handler("handler1", cara_types.Int(), False, MetaInfo())
    def handler1(self, msg):
        self.fire(self.result, msg.value + 10)


class ResultNode(Node):
    @handler("result", cara_types.Int(), False, MetaInfo())
    def result(self, msg):
        global result
        result = msg.value
        self.terminate()


class TestProjectRun(unittest.TestCase):
    def __init__(self, methodName="runTest"):
        super(TestProjectRun, self).__init__(methodName)

    def test_project_run(self):
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
        first_type, second_type, third_type = project.parse_node_types_from_declaration(
            program
        )
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
