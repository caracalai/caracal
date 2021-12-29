import logging

import caracal.declaration.projects as project
import caracal.execution.node as node_py
import caracal.execution.nodeserver as node_server


current_session = None


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
        self.project = project.ProjectInfo()
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

    # def initialize(self, project_file, node_type_impls):
    #     self.project = projects.ProjectInfo.deserialize(project_file)

    def run_project(self, project_info: project.ProjectInfo):
        for node in project_info.nodes.values():
            if node.session.name == self.name:
                if node.node_type.name in self.node_type_impls:
                    self.node_type_impls[node.node_type.name](node.uid)
                else:
                    raise NotImplementedError()
        for edge in project_info.edges.values():
            if edge.dest_node.session.name == self.name:
                if edge.source_node.session.name == self.name:
                    source_node = self.nodes[edge.source_node.uid]
                    event = source_node.events[edge.event_name]
                else:
                    event = node_py.ExternalEvent(
                        edge.event_name,
                        edge.source_node.node_type.events[edge.event_name].data_type,
                        edge.source_node.uid,
                    )
                dest_node = self.nodes[edge.dest_node.uid]
                handler = dest_node.handlers[edge.handler_name]
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
                self.server = node_server.NodeServer(all_nodes, self.server_port)
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
