import time
from collections import deque
from bblocks.typesparser import typesparser
from bblocks.execution.nodebase import *
from bblocks.execution.nodecluster import *
from bblocks.declaration.graph import *

class GeneratorA(NodeBase):
    def __init__(self):
        super().__init__()
        self.register_event("value")

    def run(self):
        index = 0
        while not self.stopped():
            time.sleep(1)
            self.generate_event("value", index)
            index += 1

class GeneratorB(NodeBase):
    def __init__(self):
        super().__init__()
        self.register_event("value")

    def run(self):
        index = 0
        while not self.stopped():
            time.sleep(1)
            self.generate_event("value", index)
            index += 1

class Summator(NodeBase):
    def __init__(self):
        super().__init__()
        self.register_handler("first", self.on_first)
        self.register_handler("second", self.on_second)
        self._firstQueue = deque()
        self._secondQueue = deque()

    def on_first(self, msg):
        print("on_first: Received {value}".format(value=msg.value))
        self._firstQueue.append(msg.value)
        self._process_queues()

    def on_second(self, msg):
        print("on_second: Received {value}".format(value=msg.value))
        self._secondQueue.append(msg.value)
        self._process_queues()

    def _process_queues(self):
        while len(self._firstQueue) > 0 and len(self._secondQueue) > 0:
            first = self._firstQueue[0]
            self._firstQueue.popleft()

            second = self._secondQueue[0]
            self._secondQueue.popleft()

            print(first + second)


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


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    try:
        graph = create_graph()
        config = json.loads(graph.serializeForExecutor())

        server_endpoint = 'tcp://127.0.0.1:2000'
        server_port = 2000

        myFabric = MyNodeCluster("python-service", config)
        myFabric.start(server_endpoint, server_port)
        myFabric.wait()
    except typesparser.TypesParseError as e:
        print (e.originalError)
