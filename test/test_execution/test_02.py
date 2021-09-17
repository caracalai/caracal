from bblocks.execution.node import *
from bblocks.execution.nodecluster import *
from bblocks.declaration.graph import *
from collections import deque

import unittest
from bblocks.typesparser import typesparser
import logging, time
from test.test_execution.resultreceiver import ResultReceiver

localhost = "tcp://127.0.0.1"
delay = 0.0
test_count = 10
list_size = 5

class InitialList(Node):
    def __init__(self):
        super().__init__()
        self.register_event("values")

    def run(self):
        for i in range(test_count):
            self.generate_event("values", [i+k for k in range(list_size)])


class Exp(Node):
    def __init__(self):
        super().__init__()
        self.register_handler("value", self.on_value)
        self.register_event("result")

    def on_value(self, msg):
        self.generate_event("result", msg.value**2, msg_id=msg.id)


class Map(Node):
    def __init__(self):
        super().__init__()
        self.register_handler("initial_values", self.on_initial_values)
        self.register_handler("processed_value", self.on_processed_value)
        self.register_event("map_value")
        self.register_event("result")
        self._requests = {}
        self._results = []
        self.counter = 0


    def on_initial_values(self, msg):
        self._requests[msg.id] = {"result": [], "size": len(msg.value)}
        for item in msg.value:
            self.generate_event("map_value", item, msg_id=msg.id)

    def on_processed_value(self, msg):
        self._requests[msg.id]["result"].append(msg.value)
        if len(self._requests[msg.id]["result"]) == self._requests[msg.id]["size"]:
            self.counter += 1
            self._results.append(self._requests[msg.id]["result"])

            self._result = []
            self._list_size = 0
            del self._requests[msg.id]

            if self.counter == test_count:
                sock = self.context.socket(zmq.REQ)
                sock.connect(result_receiver.endpoint)
                sock.send_string(json.dumps({"results": self._results}))
                sock.close()



class MyNodeCluster(NodeCluster):
    def create_node(self, name):
        if name == "InitialList":
            return InitialList()
        if name == "Exp":
            return Exp()
        if name == "Map":
            return Map()
        raise RuntimeError("Undefined type {type}".format(type=name))


types = \
    """
    node InitialList:
        events:
            values(arg1:list(int))

    node Exp:
        handlers:
            value(arg1:int)
        events:
            result(arg1:int)

    node Map:
        handlers:
            initial_values(arg1:list(object))
            processed_value(arg1:object)
        events:
            map_value(arg1:object)
            result(arg1:list(object))
    """



def create_graph():
    parser = typesparser.TypesParser()
    node_types = parser.parse(types)
    node_types = {node.name: node for node in node_types}

    graph = Graph()
    InitialList = graph.addNode(node_types["InitialList"])
    Exp = graph.addNode(node_types["Exp"])
    Map = graph.addNode(node_types["Map"])

    graph.connect(InitialList, "values", Map, "initial_values")
    graph.connect(Map, "map_value", Exp, "value")
    graph.connect(Exp, "result", Map, "processed_value")
    graph.server_fabric = "python-service"
    for k, v in graph.nodes.items():
        v.fabric = "python-service"
    return graph


class CheckGraphExecution(unittest.TestCase):
    def test_first(self):
        global result_receiver

        result_receiver = ResultReceiver(localhost)
        logging.basicConfig(level=logging.CRITICAL)

        graph = create_graph()
        config = json.loads(graph.serializeForExecutor())

        server_endpoint = 'tcp://127.0.0.1:2000'
        myFabric = MyNodeCluster("python-service", config)
        myFabric.start(server_endpoint)

        msg = result_receiver.wait_results()
        self.assertTrue("results" in msg)
        for i in range(test_count):
            for k in range(list_size):
                self.assertEqual(msg["results"][i][k], (i + k)**2)
        myFabric.wait_for_finished()