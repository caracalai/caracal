from bblocks.declaration.project import *
from bblocks.typesparser import typesparser
import unittest
import bblocks.execution.session
import bblocks.declaration.datatypes as bbtypes
from bblocks.declaration.nodetype import *
from bblocks.execution.node import *


class Sender(Node):
    def __init__(self):
        super(Sender, self).__init__()
        self.send = Event("send", bbtypes.Int)

    def run(self):
        self.fire(self.send, 0)


class Receiver(Node):
    def __init__(self):
        super(Receiver, self).__init__()

    @handler("receive", bbtypes.Int)
    def receive(self, msg):
        print(msg.value)



class CheckGraphExecution2(unittest.TestCase):
    def __init__(self, methodName='runTest'):
        super(CheckGraphExecution2, self).__init__(methodName)
        self.my_type = """
                node Sender:
                    events:
                        send(value: int)
                node Receiver:
                    handlers:
                        receive(value: int)
                """

    def test_04(self):
        try:
            parser = typesparser.TypesParser()
            node_types = parser.parse(self.my_type)
            sender_type = node_types["Sender"]
            receiver_type = node_types["Receiver"]

            project = Project()
            project.register_type(sender_type)
            project.register_type(receiver_type)

            sessionInfo = SessionInfo()
            sender = project.add_node(sender_type, sessionInfo)
            receiver = project.add_node(receiver_type, sessionInfo)
            project_file = project.serialize()
            with bblocks.execution.session.Session() as session:
                session.initialize(project_file, [Receiver, Sender])
                session.run()

        except RuntimeError:
            self.fail("test_graph_properties01")
