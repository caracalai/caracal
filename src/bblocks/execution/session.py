from bblocks.declaration.project import *
from bblocks.execution.nodeserver import NodeServer

current_session = None


class Session:
    def __init__(self, serves_server=True, server_port=None):
        self.serves_server = serves_server
        self.server_port = server_port
        self.external_nodes = []
        self.nodes = []
        self.subgraph = Project()
        self.server = None


    def initialize(self, project_file, node_type_impls):
        project = Project.deserialize(project_file)

        reprs = {impl().type : impl  for impl in node_type_impls}

        # for node in project.nodes:
        #     for node_type_impl in node_type_impls:
        #         if node.type == node_type_impl.type:
        #             found = True
        #             node_type_impl()


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
        for _, node in self.subgraph.nodes.items():
            if node.type_id == value:
                return node
        return None


