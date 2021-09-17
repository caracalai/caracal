from bblocks.execution.node import *
from bblocks.execution.nodecluster import *
from bblocks.declaration.graph import *

import unittest
from bblocks.typesparser import typesparser
import logging
from test.test_execution.resultreceiver import ResultReceiver

localhost = "tcp://127.0.0.1"

class Generator(Node):
    def __init__(self):
        super().__init__()
        self.register_event("value")

    def run(self):
        index = 0
        for i in range(10):
            self.generate_event("value", i)


class Receiver(Node):
    def __init__(self):
        super().__init__()
        self.counter = 0
        self.results = []
        self.register_handler("value", self.process_value)

    def process_value(self, message):
        self.counter += 1
        self.results.append(message.value)
        if self.counter == 10:
            sock = self.context.socket(zmq.REQ)
            sock.connect(result_receiver.endpoint)
            sock.send_string(json.dumps({"results": self.results}))
            sock.close()


class MyNodeCluster(NodeCluster):
    def create_node(self, name):
        if name == "Generator":
            return Generator()
        if name == "Receiver":
            return Receiver()
        raise RuntimeError("Undefined type {type}".format(type=name))

def create_graph():
    parser = typesparser.TypesParser()

    node_types = parser.parse(
        """
        node Generator:
            events:
                value(val:int)
        node Receiver:
            handlers:
                value(val:int)
        """)
    node_types = {node.name: node for node in node_types}

    graph = Graph()
    generator = graph.addNode(node_types["Generator"])
    receiver = graph.addNode(node_types["Receiver"])

    graph.connect(generator, "value", receiver, "value")
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
        for i in range(10):
            self.assertEqual(i, msg["results"][i])
        myFabric.wait_for_finished()
