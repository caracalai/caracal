import logging

from broutonblocks.declaration.projects import ProjectInfo
from broutonblocks.execution.nodeserver import NodeServer


current_session = None


class Session:
    def __init__(self, serves_server=True, server_port=None, external_nodes=None):
        if external_nodes is None:
            external_nodes = []
        self.serves_server = serves_server
        self.server_port = server_port
        self.external_nodes = external_nodes
        self.nodes = []
        self.project = ProjectInfo()
        self.server = None

    def initialize(self, project_file, node_type_impls):
        self.project = ProjectInfo.deserialize(project_file)

        # reprs = {impl().type: impl for impl in node_type_impls}

        # for node in project.nodes:
        #     for node_type_impl in node_type_impls:
        #         if node.type == node_type_impl.type:
        #             found = True
        #             node_type_impl()

    def run(self):
        try:
            if self.serves_server:
                logging.debug(
                    "session external nodes = {nodes}".format(nodes=self.external_nodes)
                )
                all_nodes = self.external_nodes
                for node in self.nodes:
                    all_nodes.append(node.id)
                all_nodes = list(set(all_nodes))
                # logging.debug("session all nodes = {nodes}"
                # .format(nodes=self.all_nodes))
                self.server = NodeServer(all_nodes, self.server_port)
                self.server_port = self.server.port
                self.server.start()

            for node in self.nodes:
                node.server_port = self.server_port
                node.start()

            for node in self.nodes:
                node.wait()
            if self.server is not None:
                self.server.wait()
        except Exception as e:
            logging.critical("Session exception " + str(e))

    def add(self, node):
        self.nodes.append(node)
        logging.debug(
            "session add node. Node count = {count}".format(count=len(self.nodes))
        )

    def __enter__(self):
        global current_session
        current_session = self
        return self

    def __exit__(self, type_, value, tb):
        global current_session
        del self.server
        del self
        current_session = None

    def find_node_by_value(self, value):
        for _, node in self.project.nodes.items():
            if node.type_id == value:
                return node
        return None
