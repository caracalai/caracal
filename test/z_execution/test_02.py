import logging
import unittest

import caracal.declaration.datatypes as caratypes
from caracal.execution import Event, handler, Node, Session


def map_func(value):
    return value ** 2


sent_array = [54, 23]
result = list(map(lambda x: map_func(x), sent_array))


class InitialList(Node):
    values = Event("values", caratypes.List(caratypes.Int()))

    def run(self):
        self.fire(self.values, sent_array)


class Exp(Node):
    result = Event("result", caratypes.List(caratypes.Int()))

    @handler("value", caratypes.List(caratypes.Int()))
    def on_process_value(self, msg):
        self.fire(self.result, map_func(msg.value), msg.id)


class Map(Node):
    map_value = Event("map_value", caratypes.Object())
    result = Event("result", caratypes.List(caratypes.Object()))
    requests = {}

    @handler("initial_values", caratypes.List(caratypes.Int()))
    def set_initial_values(self, msg):
        self.requests[msg.id] = {"result": [], "size": len(msg.value)}
        for item in msg.value:
            self.fire(self.map_value, item, msg_id=msg.id)

    @handler("processed_value", caratypes.Object())
    def process_value(self, msg):
        self.requests[msg.id]["result"].append(msg.value)
        if len(self.requests[msg.id]["result"]) == self.requests[msg.id]["size"]:
            res = self.requests[msg.id]["result"]
            self.fire(self.result, res)
            del self.requests[msg.id]


class TestNode(Node):
    @handler("receive_result", caratypes.Object())
    def receive_result(self, msg):
        self.result = msg.value
        self.terminate()


class CheckGraphExecution_02(unittest.TestCase):
    def setUp(self) -> None:
        with Session() as session:
            logging.basicConfig(level=logging.DEBUG)
            self.listNode = InitialList("initial-list")
            self.mapNode = Map("map")
            self.expNode = Exp("exp")
            self.test_node = TestNode("test-node")

            self.mapNode.set_initial_values.connect(self.listNode.values)
            self.mapNode.process_value.connect(self.expNode.result)
            self.expNode.on_process_value.connect(self.mapNode.map_value)
            self.test_node.receive_result.connect(self.mapNode.result)
            session.run()

    def test(self):

        self.assertEqual(result, self.test_node.result)

    def tearDown(self) -> None:
        del self.mapNode
        del self.expNode
        del self.listNode
        del self.test_node
        del self
