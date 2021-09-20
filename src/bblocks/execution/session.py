from bblocks.declaration.graph import *
from bblocks.execution.nodeserver import NodeServer

current_session = None

class Session:
    def __init__(self, serves_server=True, server_port=None):
        self.serves_server = serves_server
        self.port = server_port
        self.graph = Graph()

    def run(self):
        if self.serves_server:
            self._server_node = NodeServer(self.graph, self.port)
            self._server_node.start()
            self.port = self._server_node.port

        for id, node in self.graph.nodes.items():
            node.node_value.set_id(id)
            node.node_value.port = self.port
            node.node_value.start()

    def add(self, node):
        self.graph.addNode(node)

    def __enter__(self):
        global current_session
        current_session = self
        return self

    def __exit__(self, type, value, tb):
        global current_session
        current_session = None

    def find_node_by_value(self, value):
        for id, node in self.graph.nodes.items():
            if node.node_value == value:
                return node
        return None


    def connect(self, event, handler):
        first_node = self.find_node_by_value(event.parent)
        second_port = self.find_node_by_value(handler.parent)
        self.graph.connect(first_node, event.name, second_port, handler.name)


