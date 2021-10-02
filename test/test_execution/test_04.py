# from bblocks.declaration.project import *
# from bblocks.typesparser import typesparser
# import unittest
# import bblocks.execution.session
# import bblocks.declaration.datatypes as bbtypes
# from bblocks.execution.node import *
#
# sent_value = 10
#
# class Sender(Node):
#     def __init__(self):
#         super(Sender, self).__init__()
#         self.send = Event("send", bbtypes.Int)
#
#     def run(self):
#         self.fire(self.send, sent_value)
#
#
# class Receiver(Node):
#     def __init__(self):
#         super(Receiver, self).__init__()
#         self.result = Event("result", bbtypes.Object())
#
#     @handler("receive", bbtypes.Int)
#     def receive(self, msg):
#         self.fire(self.result, msg.value ** 2)
#
#
# class TestNode(Node):
#     def __init__(self, id=None):
#         super().__init__(id)
#         self.result = None
#
#     @handler("receive_result", bbtypes.Object())
#     def receive_result(self, msg):
#         self.result = msg.value
#         self.terminate()
#
# class CheckGraphExecution_04(unittest.TestCase):
#     def test(self):
#         try:
#             self.my_type = """
#                             node Sender:
#                                 events:
#                                     send(value: int)
#                             node Receiver:
#                                 handlers:
#                                     receive(value: int)
#                             node TestNode:
#                                 handlers:
#                                     receive_result(value: object)
#                             """
#
#             parser = typesparser.TypesParser()
#             node_types = parser.parse(self.my_type)
#             sender_type = node_types["Sender"]
#             receiver_type = node_types["Receiver"]
#             test_node_type = node_types["TestNode"]
#
#             project = Project()
#             project.register_types([sender_type, receiver_type, test_node_type])
#
#             sessionInfo = SessionInfo()
#             sender = project.add_node(sender_type, sessionInfo)
#             receiver = project.add_node(receiver_type, sessionInfo)
#             project_file = project.serialize()
#             with bblocks.execution.session.Session() as session:
#                 session.initialize(project_file, [Receiver, Sender, TestNode])
#                 session.run()
#
#
#         except RuntimeError:
#             self.fail("test_graph_properties01")
