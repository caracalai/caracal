import base64
import copy
import pickle
import uuid


class SessionInfo:
    def __init__(self, name="default"):
        self.name = name

    @property
    def uid(self):
        return self.name


class Node:
    def __init__(self, project, type_uid, session_uid):
        self.type_uid = type_uid
        self.property_values = {}
        self.session_uid = session_uid
        self.project = project
        self.uid = "{type_name}_{uuid}".format(
            type_name=self.node_type.name, uuid=str(uuid.uuid4())
        )

    @property
    def node_type(self):
        return self.project.node_types[self.type_uid]

    @property
    def session(self):
        return self.project.sessions[self.session_uid]

    def set_property(self, name, value):
        if name not in self.node_type.properties.keys():
            raise RuntimeError("Couldn't set property")

        prop_type = self.node_type.properties[name].data_type
        if not prop_type.contains_value(value):
            raise RuntimeError("Couldn't set property")

        self.property_values[name] = value

    def serialize(self):
        result = {
            "type_id": self.type_uid,
            "session_id": self.session_uid,
            "property_values": 1 / 0,
            "id": self.uid,
        }
        return result


class Edge:
    def __init__(self, source_node_uid, event_name, dest_node_uid, handler_name):
        self.uid = str(uuid.uuid4())
        self.source_node_uid = source_node_uid
        self.event_name = event_name
        self.dest_node_uid = dest_node_uid
        self.handler_name = handler_name


class Project:
    def __init__(self):
        self.sessions = {}  # session-id -> SessionInfo
        self.node_types = {}  # type-id -> NodeTypeDeclaration
        self.nodes = {}  # node-id -> NodeInfo
        self.edges = []  # Edges

    def add_node_type(self, node_type):
        self.node_types[node_type.uid] = node_type

    def remove_node_type(self, node_type):
        del self.node_types[node_type.uid]

    def node_type(self, uid_):
        if uid_ in self.node_types:
            return self.node_types[uid_]
        else:
            raise RuntimeError()

    def contains_node_type(self, uid_):
        return uid_ in self.node_types

    @staticmethod
    def deserialize(text):
        return pickle.loads(base64.b64decode(text))

    def serialize(self):
        return base64.b64encode(pickle.dumps(self)).decode("ascii")

    def node(self, uid_):
        if uid_ in self.nodes:
            return self.nodes[uid_]
        else:
            raise RuntimeError()

    def contains_node(self, uid_):
        return uid_ in self.nodes

    def can_connect(
        self,
        source_node: Node,
        event_name: str,
        dest_node: Node,
        handler_name: str,
    ):
        source_node_uid = source_node.uid
        dest_node_uid = dest_node.uid

        edge = Edge(source_node_uid, event_name, dest_node_uid, handler_name)
        all_edges = self.edges + [edge]

        # a = self.node(edge.source_node_id).type
        if event_name not in self.node(edge.source_node_uid).node_type.events:
            return False, "Node {node} doesn't have event {event}".format(
                node=self.node(edge.source_node_uid).node_type.name, event=event_name
            )

        if handler_name not in self.node(edge.dest_node_uid).node_type.handlers:
            return False, "Node {node} doesn't have handler {handler}".format(
                node=self.node(edge.dest_node_uid).node_type.name, handler=handler_name
            )

        types_info = {}
        for _, node in self.nodes.items():
            types_info[node.uid] = {}
            types_info[node.uid]["events"] = copy.deepcopy(node.node_type.events)

            types_info[node.uid]["handlers"] = {}
            for h, t in node.node_type.handlers.items():
                types_info[node.uid]["handlers"][h] = copy.deepcopy(t.node_type)

        if not self.node_types[dest_node.type_uid].handlers[handler_name].receives_multiple:
            if (
                len(
                    list(
                        filter(
                            lambda e: e.handler_name == handler_name
                                      and e.dest_node_uid == dest_node_uid,
                            all_edges,
                        )
                    )
                )
                > 1
            ):
                return (
                    False,
                    "Handler {handler} of node {node} "
                    "can't have multiple inputs".format(
                        handler=handler_name, node=dest_node_uid
                    ),
                )

        while True:
            specialized = False
            for edge in all_edges:
                source_type = types_info[edge.source_node_uid]["events"][
                    edge.event_name
                ].node_type
                dest_type = types_info[edge.dest_node_uid]["handlers"][edge.handler_name]
                intersected_type = source_type.intersect(dest_type)
                if intersected_type is None:
                    return (
                        False,
                        "Couldn't match types of {source_node}.{event} "
                        "('{source_class}') and "
                        "{dest_node}.{handler} ('{dest_class}')".format(
                            source_node=self.node(edge.source_node_uid).node_type.name,
                            event=edge.event_name,
                            dest_node=self.node(edge.dest_node_uid).node_type.name,
                            handler=edge.handler_name,
                            source_class=source_type.name,
                            dest_class=dest_type.name,
                        ),
                    )

                for _node_uid, _connector_type, _connector_name in [
                    (edge.source_node_uid, "events", edge.event_name),
                    (edge.dest_node_uid, "handlers", edge.handler_name),
                ]:
                    if (
                        self.nodes[edge.dest_node_uid]
                        .node_type.handlers[edge.handler_name]
                        .receives_multiple
                    ):
                        continue

            if not specialized:
                break
        return True, "Success"

    def connect(
        self, source_node_uid: str, event_name: str, dest_node_uid: str, handler_name: str
    ):
        source_node = self.node(source_node_uid)
        dest_node = self.node(dest_node_uid)
        result, msg = self.can_connect(source_node, event_name, dest_node, handler_name)
        if not result:
            raise RuntimeError(msg)

        edge = Edge(source_node.uid, event_name, dest_node.uid, handler_name)
        self.edges.append(edge)
        return edge

    def remove_connection(self, edge_uid):
        self.edges = list(filter(lambda e: e.uid != edge_uid, self.edges))

    def connection(self, uid_):
        if uid_ in self.edges:
            return self.edges[uid_]
        else:
            raise RuntimeError()

    def contains_node(self, uid_):
        return uid_ in self.edges

    def create_session(self, name):
        session = SessionInfo(name)
        self.sessions[session.uid] = session
        return session.uid

    def remove_session(self, session_uid):
        if session_uid in self.sessions:
            for node_uid in [node_uid for node_uid in self.nodes]:
                if self.nodes[node_uid].session_uid == self.sessions[session_uid]:
                    self.remove_node(node_uid)
            del self.sessions[session_uid]

    def session(self, uid_):
        if uid_ in self.sessions:
            return self.sessions[uid_]
        else:
            raise RuntimeError()

    def contains_session(self, uid_):
        return uid_ in self.sessions

    def add_node(self, type_, session_uid):
        if session_uid in self.sessions:
            node = Node(self, type_.uid, session_uid)
            self.nodes[node.uid] = node
            return node.uid
        else:
            raise RuntimeError()

    def remove_node(self, node_uid):
        if node_uid in self.nodes:
            del self.nodes[node_uid]
            self.edges = list(
                filter(
                    lambda e: e.source_node_uid != node_uid and e.dest_node_uid != node_uid,
                    self.edges,
                )
            )
