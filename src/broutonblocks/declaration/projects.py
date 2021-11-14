from __future__ import annotations

import base64
import copy
import pickle
import uuid

from broutonblocks.declaration.nodetype import NodeTypeDeclaration
from broutonblocks.typesparser import TypesParser


class SessionInfo:
    def __init__(self, project, name: str):
        self.name = name
        self.project = project

    @property
    def uid(self) -> str:
        return self.name


class NodeInfo:
    def __init__(self, node_type: NodeTypeDeclaration, session: SessionInfo):
        self.node_type = node_type
        self.property_values = {
            prop: val.default_value for prop, val in self.node_type.properties.items()
        }
        self.session = session
        self.uid = "{type_name}_{uuid}".format(
            type_name=self.node_type.name, uuid=str(uuid.uuid4())
        )

    def set_property(self, name: str, value) -> None:
        if name not in self.node_type.properties.keys():
            raise RuntimeError("Couldn't set property")

        prop_type = self.node_type.properties[name].data_type
        if not prop_type.contains_value(value):
            raise RuntimeError("Couldn't set property")

        self.property_values[name] = value

    def serialize(self) -> dict:
        result = {
            "type_id": self.node_type.uid,
            "session_id": self.session.uid,
            "property_values": 1 / 0,
            "id": self.uid,
        }
        return result


class EdgeInfo:
    def __init__(
        self,
        source_node: NodeInfo,
        event_name: str,
        dest_node: NodeInfo,
        handler_name: str,
    ):
        self.uid = str(uuid.uuid4())
        self.source_node = source_node
        self.event_name = event_name
        self.dest_node = dest_node
        self.handler_name = handler_name


class ProjectInfo:
    def __init__(self):
        self.sessions = {}  # session-uid(name) -> SessionInfo
        self.node_types = {}  # type-uid -> NodeTypeDeclaration
        self.nodes = {}  # node-uid -> NodeInfo
        self.edges = {}  # Edges

    def parse_node_types_from_declaration(self, declaration: str) -> list:
        parser = TypesParser()
        types = parser.parse(declaration)
        for node_type in types.values():
            if not self.contains_node_type(node_type):
                self.node_types[node_type.uid] = node_type
            else:
                raise RuntimeError()
        return list(types.values())

    def remove_node_type(self, node_type: NodeTypeDeclaration) -> None:
        if self.contains_node_type(node_type):
            del self.node_types[node_type.uid]
        else:
            raise RuntimeError()

    def contains_node_type(self, node_type: NodeTypeDeclaration) -> bool:
        return node_type.uid in self.node_types

    def can_connect(
        self,
        source_node: NodeInfo,
        event_name: str,
        dest_node: NodeInfo,
        handler_name: str,
    ) -> bool:

        edge = EdgeInfo(source_node, event_name, dest_node, handler_name)
        all_edges = self.edges.copy()
        all_edges[edge.uid] = edge

        # a = self.node(edge.source_node_id).type
        if event_name not in self.nodes[edge.source_node.uid].node_type.events:
            return False

        if handler_name not in self.nodes[edge.dest_node.uid].node_type.handlers:
            return False

        types_info = {}
        for _, node in self.nodes.items():
            types_info[node.uid] = {}
            types_info[node.uid]["events"] = copy.deepcopy(node.node_type.events)

            types_info[node.uid]["handlers"] = {}
            for h, t in node.node_type.handlers.items():
                types_info[node.uid]["handlers"][h] = copy.deepcopy(t.data_type)

        if (
            not self.node_types[self.nodes[dest_node.uid].node_type.uid]
            .handlers[handler_name]
            .receives_multiple
        ):
            if (
                len(
                    [
                        edg
                        for edg in all_edges.values()
                        if edg.handler_name == handler_name
                        and edg.dest_node.uid == dest_node.uid
                    ]
                )
                > 1
            ):
                return False

        while True:
            specialized = False
            for edge in all_edges.values():
                source_type = types_info[edge.source_node.uid]["events"][
                    edge.event_name
                ].data_type
                dest_type = types_info[edge.dest_node.uid]["handlers"][edge.handler_name]
                intersected_type = source_type.intersect(dest_type)
                if intersected_type is None:
                    return False

                for _node_uid, _connector_type, _connector_name in [
                    (edge.source_node.uid, "events", edge.event_name),
                    (edge.dest_node.uid, "handlers", edge.handler_name),
                ]:
                    if (
                        self.nodes[edge.dest_node.uid]
                        .node_type.handlers[edge.handler_name]
                        .receives_multiple
                    ):
                        continue

            if not specialized:
                break
        return True

    def connect(
        self,
        source_node: NodeInfo,
        event_name: str,
        dest_node: NodeInfo,
        handler_name: str,
    ) -> EdgeInfo:
        result = self.can_connect(source_node, event_name, dest_node, handler_name)
        if not result:
            raise RuntimeError()

        edge = EdgeInfo(source_node, event_name, dest_node, handler_name)
        self.edges[edge.uid] = edge
        return edge

    def remove_connection(self, edge: EdgeInfo) -> None:
        if self.contains_connection(edge):
            del self.edges[edge.uid]
        else:
            raise RuntimeError()

    def contains_connection(self, edge: EdgeInfo) -> bool:
        return edge.uid in self.edges

    def create_session(self, name: str) -> SessionInfo:
        session = SessionInfo(self, name)
        if not self.contains_session(session):
            self.sessions[session.uid] = session
            return session
        else:
            raise RuntimeError()

    def remove_session(self, session: SessionInfo) -> None:
        if self.contains_session(session):
            for node_uid in list(self.nodes):
                if self.nodes[node_uid].session.uid == self.sessions[session.uid]:
                    self.remove_node(self.nodes[node_uid])
            del self.sessions[session.uid]
        else:
            raise RuntimeError()

    def contains_session(self, session: SessionInfo) -> bool:
        return session.uid in self.sessions

    def create_node(
        self, node_type: NodeTypeDeclaration, session: SessionInfo
    ) -> NodeInfo:
        if self.contains_session(session):
            node = NodeInfo(node_type, session)
            self.nodes[node.uid] = node
            return node
        else:
            raise RuntimeError()

    def contains_node(self, node: NodeInfo) -> bool:
        return node.uid in self.nodes

    def move_node(self, node: NodeInfo, dest_session: SessionInfo) -> None:
        if self.contains_node(node) and self.contains_session(dest_session):
            node.session = dest_session
        else:
            raise RuntimeError()

    def remove_node(self, node: NodeInfo) -> None:
        if self.contains_node(node):
            for edge in list(self.edges.values()):
                if node.uid == edge.dest_node or node.uid == edge.source_node:
                    self.remove_connection(self.edges[edge.uid])
            del self.nodes[node.uid]
        else:
            raise RuntimeError()

    @staticmethod
    def deserialize(text: str) -> ProjectInfo:
        return pickle.loads(base64.b64decode(text))

    def serialize(self) -> str:
        return base64.b64encode(pickle.dumps(self)).decode("ascii")
