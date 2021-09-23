from bblocks.declaration.graph import *
from bblocks.execution.nodeserver import NodeServer

current_session = None

class Session:
    def __init__(self, serves_server=True, server_port=None):
        self.serves_server = serves_server
        self.server_port = server_port
        self.external_nodes = []
        self.nodes = []
        self.subgraph = Graph()
        self.server = None

    def run(self):
        if self.serves_server:
            all_nodes = self.external_nodes
            for node in self.nodes:
                all_nodes.append(node.id)
            all_nodes = list(set(all_nodes))
            self.server = NodeServer(all_nodes, self.server_port)
            self.server_port = self.server.port
            self.server.start()

        for node in self.nodes:
            node.server_port = self.server_port
            node.start()

    def add(self, node):
        self.nodes.append(node)

    def __enter__(self):
        global current_session
        current_session = self
        return self

    def __exit__(self, type, value, tb):
        global current_session
        current_session = None

    def find_node_by_value(self, value):
        for id, node in self.subgraph.nodes.items():
            if node.node_value == value:
                return node
        return None

    #
    # def connect(self, event, handler):
    #     first_node = self.find_node_by_value(event.parent)
    #     second_port = self.find_node_by_value(handler.parent)
    #     self.subgraph.connect(first_node, event.name, second_port, handler.name)


