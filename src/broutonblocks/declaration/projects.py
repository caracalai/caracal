import base64
import copy
import json
import uuid

from broutonblocks.declaration.nodetype import *


class SessionInfo:
    def __init__(self, name="default"):
        self.name = name


class Node:
    def __init__(self, project, type_id, session_id, name="undefined_name"):
        self.type_id = type_id
        self.property_values = {}
        self.session_id = session_id
        self.project = project
        self.id = "{type_name}_{uuid}".format(type_name=self.type.name, uuid=str(uuid.uuid4()))

    @property
    def type(self):
        return self.project.types[self.type_id]

    @property
    def session(self):
        return self.project.sessions[self.session_id]

    def set_property(self, name, value):
        if not name in self.type.properties.keys():
            raise RuntimeError("Couldn't set property")

        prop_type = self.type.properties[name].data_type
        if not prop_type.contains_value(value):
            raise RuntimeError("Couldn't set property")

        self.property_values[name] = value

    def serialize(self):
        result = {}
        result["type_id"] = self.type_id
        result["session_id"] = self.session_id
        result["property_values"] = 1/0
        result["id"] = self.id
        return result


class Edge:
    def __init__(self, source_node_id, event_name, dest_node_id, handler_name):
        self.id = str(uuid.uuid4())
        self.source_node_id = source_node_id
        self.event_name = event_name
        self.dest_node_id = dest_node_id
        self.handler_name = handler_name


class Project:
    def __init__(self):
        self.sessions = {}  # session-id -> SessionInfo
        self.types = {}     # type-id -> TypeInfo
        self.nodes = {}     # node-id -> NodeInfo
        self.edges = []     # Edges

    def register_types(self, types):
        for type in types:
            self.types[type.id] = type

    def remove_type(self, type):
        raise NotImplemented()


    @staticmethod
    def deserialize(text):
        return pickle.loads(base64.b64decode(text))

    def serialize(self):
        return base64.b64encode(pickle.dumps(self)).decode('ascii')

        result = {}

        types = {}
        for type in self.types.values():
            types[type.id] = type.serialize()
        result["types"] = types

        sessions = {}
        for session in self.sessions.values():
            session[session.id] = session.serialize()
        result["sessions"] = sessions

        nodes = {}
        for node in self.nodes:
            nodes[node.id] = node.serialize()
        result["nodes"] = nodes

        edges = []
        for edge in self.edges:
            edges.append(node.serialize())
        result["edges"] = edges

        return json.dumps(result, indent=2)

    def node(self, id):
        return self.nodes[id]

    def contains_node(self, id):
        return id in self.nodes

    def can_connect(self, source_node, event_name: str, dest_node: NodeTypeDeclaration, handler_name: str):
        source_node_id = source_node.id
        dest_node_id = dest_node.id

        edge = Edge(source_node_id, event_name, dest_node_id, handler_name)
        all_edges = self.edges + [edge]

        a = self.node(edge.source_node_id).type
        if event_name not in self.node(edge.source_node_id).type.events:
            return False, "Node {node} doesn't have event {event}".format(
                node=self.node(edge.source_node_id).type.name, event=event_name)

        if handler_name not in self.node(edge.dest_node_id).type.handlers:
            return False, "Node {node} doesn't have handler {handler}".format(
                node=self.node(edge.dest_node_id).type.name, handler=handler_name)

        types_info = {}
        for _, node in self.nodes.items():
            types_info[node.id] = {}
            types_info[node.id]["events"] = copy.deepcopy(node.type.events)

            types_info[node.id]["handlers"] = {}
            for h, t in node.type.handlers.items():
                types_info[node.id]["handlers"][h] = copy.deepcopy(t.type)

        if not dest_node.node_value.handlers[handler_name].receives_multiple:
            if len(list(filter(lambda e: e.handler_name == handler_name and e.dest_node_id == dest_node_id,
                               all_edges))) > 1:
                return False, "Handler {handler} of node {node} can't have multiple inputs".format(handler=handler_name,
                                                                                                   node=dest_node_id)

        while True:
            specialized = False
            for edge in all_edges:
                source_type = types_info[edge.source_node_id]["events"][edge.event_name].type
                dest_type = types_info[edge.dest_node_id]["handlers"][edge.handler_name]
                intersected_type = source_type.intersect(dest_type)
                if intersected_type == None:
                    return False, "Couldn't match types of {source_node}.{event} ('{source_class}') and {dest_node}.{handler} ('{dest_class}')" \
                        .format(source_node=self.node(edge.source_node_id).type.name,
                                event=edge.event_name,
                                dest_node=self.node(edge.dest_node_id).type.name,
                                handler=edge.handler_name,
                                source_class=source_type.name,
                                dest_class=dest_type.name)

                for node_id, connector_type, connector_name in [
                    (edge.source_node_id, "events", edge.event_name),
                    (edge.dest_node_id, "handlers", edge.handler_name)]:
                    if self.nodes[edge.dest_node_id].type.handlers[edge.handler_name].receives_multiple:
                        continue

                    # if type(intersected_type) != type(types_info[node_id][connector_type][connector_name]):
                    #     types_info[node_id][connector_type][connector_name] = intersected_type
                    #     try:
                    #         updated, refined_types = self._nodes[node_id].node_value.type.specializeTypes(types_info[node_id], self.node(node_id)._property_values)
                    #         if updated == True:
                    #             types_info[node_id] = refined_types
                    #     except RuntimeError as e:
                    #         return False, str(e)

            if specialized == False:
                break
        return True, "Success"

    def connect(self, source_node: Node, event_name: str, dest_node: Node, handler_name: str):
        result, msg = self.can_connect(source_node, event_name, dest_node, handler_name)
        if not result:
            raise RuntimeError(msg)

        edge = Edge(source_node.id, event_name, dest_node.id, handler_name)
        self.edges.append(edge)
        return edge

    def remove_connection(self, edge_id):
        self.edges = list(filter(lambda e: e.id != edge_id, self.edges))

    def create_session(self, lang, name):
        session = SessionInfo(lang, name)
        self.sessions[session.id] = session

    def remove_session(self, name):
        raise NotImplemented()

    def add_node(self, type, session):
        node = Node(self, type.id, session)
        self.nodes[node.id] = node
        return node

    def remove_node(self, node_id):
        if node_id in self.nodes:
            del self.nodes[node_id]
            self.edges = list(filter(lambda e: e.source_node_id != node_id and e.dest_node_id != node_id, self.edges))
