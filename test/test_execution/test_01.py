from bblocks.execution.nodebase import *
from bblocks.execution.nodecluster import *
from bblocks.declaration.graph import *
from collections import deque

import unittest
from bblocks.typesparser import typesparser
import logging, time
from test.test_execution.resultreceiver import ResultReceiver

localhost = "tcp://127.0.0.1"
delay = 0.0

class GeneratorA(NodeBase):
    def __init__(self):
        super().__init__()
        self.register_event("value")

    def run(self):
        index = 0
        counter = 0
        while not self.stopped():
            time.sleep(delay)
            self.generate_event("value", index)
            index += 1
            counter += 1
            if counter == 100:
                break

class GeneratorB(NodeBase):
    def __init__(self):
        super().__init__()
        self.register_event("value")

    def run(self):
        index = 0
        counter = 0
        while not self.stopped():
            self.generate_event("value", index)
            index += 2
            counter += 1
            if counter == 100:
                break


class Summator(NodeBase):
    def __init__(self):
        super().__init__()
        self.counter = 0
        self.register_handler("first", self.on_first)
        self.register_handler("second", self.on_second)
        self._firstQueue = deque()
        self._secondQueue = deque()
        self.results = []

    def on_first(self, msg):
        self._firstQueue.append(msg.value)
        self._process_queues()

    def on_second(self, msg):
        self._secondQueue.append(msg.value)
        self._process_queues()

    def _process_queues(self):
        while len(self._firstQueue) > 0 and len(self._secondQueue) > 0:
            first = self._firstQueue[0]
            self._firstQueue.popleft()

            second = self._secondQueue[0]
            self._secondQueue.popleft()

            self.results.append(first * second)
            self.counter += 1
            if self.counter == 100:
                sock = self.context.socket(zmq.REQ)
                sock.connect(result_receiver.endpoint)
                sock.send_string(json.dumps({"results": self.results}))
                break


class MyNodeCluster(NodeCluster):
    def create_node(self, name):
        if name == "GeneratorA":
            return GeneratorA()
        if name == "GeneratorB":
            return GeneratorB()
        if name == "Summator":
            return Summator()
        raise RuntimeError("Undefined type {type}".format(type=name))


types = \
    """
    @section(name="abc")
    node GeneratorA:
        events:
            value(val:int)
            
   node GeneratorB:
        events:
            value(val:int)

    node Summator:
        handlers:
            first(val:int)
            second(val:int)
        events:
            result(val:int)                            
    """



def create_graph():
    parser = typesparser.TypesParser()

    node_types = parser.parse(types)
    node_types = {node.name: node for node in node_types}

    graph = Graph()
    GeneratorA = graph.addNode(node_types["GeneratorA"])
    GeneratorB = graph.addNode(node_types["GeneratorB"])
    Summator = graph.addNode(node_types["Summator"])

    graph.connect(GeneratorA, "value", Summator, "first")
    graph.connect(GeneratorB, "value", Summator, "second")
    graph.server_fabric = "python-service"
    for k, v in graph.nodes.items():
        v.fabric = "python-service"
    return graph
import logging


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
        for i in range(10):
            self.assertEqual(i * (i*2), msg["results"][i])
        myFabric.wait_for_finished()

