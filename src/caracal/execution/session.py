import io
import logging
import sys
import time
import traceback

from caracal.declaration.projects import ProjectInfo
from caracal.execution.nodeserver import NodeServer

current_session = None

old_stdout = sys.stdout
new_stdout = io.StringIO()
sys.stdout = new_stdout


class Session:
    def __init__(
        self, name="global", serves_server=True, server_port=None, external_nodes=None
    ):
        if external_nodes is None:
            external_nodes = []
        self.serves_server = serves_server
        self.server_port = server_port
        self.external_nodes = external_nodes
        self.name = name
        self.node_type_impls = {}
        self.nodes = {}
        self.project = ProjectInfo()
        self.server = None

    @staticmethod
    def convert_used_node_types_to_text_declaration(session):
        result = ""
        for node in session.nodes.values():
            result += str(node.node_type) + "\n"
        return result

    def register_types(self, node_type_impls):
        for t_ in node_type_impls:
            self.node_type_impls[t_.__name__] = t_

    def initialize(self, project_file, node_type_impls):
        self.project = ProjectInfo.deserialize(project_file)

    def run_project(self, project: ProjectInfo):
        for node in project.nodes.values():
            if node.session.name == self.name:
                if node.node_type.name in self.node_type_impls:
                    self.node_type_impls[node.node_type.name](node.uid)
                else:
                    raise NotImplementedError()
        for edge in project.edges.values():
            source_node = self.nodes[edge.source_node.uid]
            dest_node = self.nodes[edge.dest_node.uid]
            handler = dest_node.handlers[edge.handler_name]
            event = source_node.events[edge.event_name]
            handler.connect(event)
        self.run()

    def run(self):
        try:
            if self.serves_server:
                logging.debug(
                    "session external nodes = {nodes}".format(nodes=self.external_nodes)
                )
                all_nodes = self.external_nodes
                for node in self.nodes.values():
                    all_nodes.append(node.id)
                all_nodes = list(set(all_nodes))
                self.server = NodeServer(all_nodes, self.server_port)
                self.server_port = self.server.port
                self.server.start()
            logging.debug("Len of nodes values {}".format(len(self.nodes.values())))
            for key in self.nodes:
                logging.warning(self.nodes[key].session.name)
                self.nodes[key].server_port = self.server_port
                self.nodes[key].start()

            for node in self.nodes.values():
                node.wait()
            if self.server is not None:
                self.server.wait()
        except Exception as e:
            traceback.print_exc()
            output = new_stdout.getvalue()
            logging.debug(output)
            logging.critical("Session exception " + str(e))

    def add(self, node):
        self.nodes[node.id] = node

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
