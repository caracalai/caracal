import time
from collections import deque
from bblocks.typesparser import typesparser
from bblocks.execution.nodebase import *
from bblocks.execution.nodecluster import *
from bblocks.declaration.graph import Graph
import logging


class InitialList(NodeBase):
    def __init__(self):
        super().__init__()
        self.register_event("values")

    def run(self):
        for i in range(10):
            self.generate_event("values", [i, i+1, i+2, i+3, i+4])


class Exp(NodeBase):
    def __init__(self):
        super().__init__()
        self.register_event("result")
        self.register_handler("value", self.on_value)

    def on_value(self, msg):
        time.sleep(0.1) # long operation
        self.generate_event("result", msg.value**2, msg_id=msg.id)


class Map(NodeBase):
    def __init__(self):
        super().__init__()
        self.register_handler("initial_values", self.on_initial_values)
        self.register_handler("processed_value", self.on_processed_value)
        self.register_event("map_value")
        self.register_event("result")
        self._requests = {}


    def on_initial_values(self, msg):
        self._requests[msg.id] = {"result": [], "size": len(msg.value)}
        for item in msg.value:
            self.generate_event("map_value", item, msg_id=msg.id)

    def on_processed_value(self, msg):
        self._requests[msg.id]["result"].append(msg.value)
        if len(self._requests[msg.id]["result"]) == self._requests[msg.id]["size"]:
            print(self._requests[msg.id]["result"])
            self._result = []
            self._list_size = 0
            del self._requests[msg.id]


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

if __name__ == "__main__":
    logging.basicConfig(level=logging.CRITICAL)

    graph = create_graph()
    config = json.loads(graph.serializeForExecutor())

    server_endpoint = 'tcp://127.0.0.1:2000'
    server_port = 2000

    myFabric = MyNodeCluster("python-service", config)
    myFabric.start(server_endpoint, server_port)
    myFabric.wait()
