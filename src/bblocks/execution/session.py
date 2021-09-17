from bblocks.declaration.graph import *
from bblocks.execution.nodeserver import NodeServer

current_session = None

class Session:
    def __init__(self, serves_server=True, server_port=2000):
        self._serves_server = serves_server
        self._server_port = server_port
        self._graph = Graph()

    def run(self):
        if self._serves_server:
            self._server_node = NodeServer(self._graph, self._server_port)
            self._server_node.start()
            self._server_port = self._server_node.port

        for id, node in self._config["nodes"].items():
            node.set_id(id)
            node.set_port(self._server_port)
            node.start()

    def add(self, node):
        self._graph.addNode(node)

    def __enter__(self):
        global current_session
        current_session = self
        return self

    def __exit__(self, type, value, tb):
        global current_session
        current_session = None

    def find_node_by_value(self, value):
        for id, node in self._graph._nodes.items():
            if node.node_value == value:
                return node
        return None


    def connect(self, event, handler):
        n1 = self.find_node_by_value(event.parent)
        n2 = self.find_node_by_value(handler.parent)
        self._graph.connect(n1, event.name, n2, handler.name)


