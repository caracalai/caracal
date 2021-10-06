import logging
import unittest

import broutonblocks.declaration.datatypes as bbtypes
from broutonblocks.execution import Event, handler, Node, Session


def map_func(value):
    return value ** 2


sent_array = [54, 23]
result = list(map(lambda x: map_func(x), sent_array))


class InitialList(Node):
    def __init__(self, id_=None):
        super().__init__(id_)
        self.values = Event("values", bbtypes.List(bbtypes.Int()))

    def run(self):
        self.fire(self.values, sent_array)


class Exp(Node):
    def __init__(self, id_=None):
        super().__init__(id_)
        self.result = Event("result", bbtypes.List(bbtypes.Int()))

    @handler(name="value", type=bbtypes.List(bbtypes.Int()))
    def on_process_value(self, msg):
        self.fire(self.result, map_func(msg.value), msg.id)


class Map(Node):
    def __init__(self, id_=None):
        super().__init__(id_)
        self.map_value = Event("map_value", bbtypes.Object())
        self.result = Event("result", bbtypes.List(bbtypes.Object()))
        self.requests = {}

    @handler(name="initial_values", type=bbtypes.List(bbtypes.Int()))
    def set_initial_values(self, msg):
        self.requests[msg.id] = {"result": [], "size": len(msg.value)}
        for item in msg.value:
            self.fire(self.map_value, item, msg_id=msg.id)

    @handler(name="processed_value", type=bbtypes.Object())
    def process_value(self, msg):
        self.requests[msg.id]["result"].append(msg.value)
        if len(self.requests[msg.id]["result"]) == self.requests[msg.id]["size"]:
            res = self.requests[msg.id]["result"]
            self.fire(self.result, res)
            del self.requests[msg.id]


class TestNode(Node):
    @handler("receive_result", bbtypes.Object())
    def receive_result(self, msg):
        self.result = msg.value
        self.terminate()


class CheckGraphExecution_02(unittest.TestCase):
    def test(self):
        with Session() as session:
            logging.basicConfig(level=logging.CRITICAL)
            listNode = InitialList("initial-list")
            mapNode = Map("map")
            expNode = Exp("exp")
            test_node = TestNode("test-node")

            mapNode.set_initial_values.connect(listNode.values)
            mapNode.process_value.connect(expNode.result)
            expNode.on_process_value.connect(mapNode.map_value)
            test_node.receive_result.connect(mapNode.result)
            session.run()

            self.assertEqual(result, test_node.result)
