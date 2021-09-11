from bblocks.declaration import *
from bblocks.declaration.nodetype import *

import uuid
import json

class Node:
    def __init__(self, node_type, values):
        self._type = node_type
        self._values = values
        self._id = "{t}_{id}".format(t=node_type.name, id=str(uuid.uuid4()))
        self._graph = None
        self._location = (-1, -1)
        self._property_values = {}
        self._fabric = ""

    @property
    def property_values(self):
        return self._property_values


    @property
    def type(self):
        return self._type

    @property
    def fabric(self):
        return self._fabric

    @fabric.setter
    def fabric(self, value):
        self._fabric = value

    @property
    def id(self):
        return self._id

    @property
    def location(self):
        return self._location

    @location.setter
    def location(self, value):
        assert type(value) == tuple and len(value) == 2
        self._location = value

    @property
    def graph(self):
        return self._graph


    @graph.setter
    def graph(self, value):
        self._graph = value

    def setProperty(self, name, value):
        if not name in self._type.properties.keys():
            raise RuntimeError("Couldn't set property")

        prop_type = self._type._properties[name]
        if not prop_type.contains_value(value):
            raise RuntimeError("Couldn't set property")

        if isinstance(prop_type, DataSourceType):
            if not self.graph.contains_node(value):
                raise RuntimeError("Couldn't set property")

            if not isinstance(self.graph.node(value).type, TableDataSourceNode):
                raise RuntimeError("Couldn't set property")


            # TableDataSourceNode
            sourceBasicType = self.graph.node(value).type.basicType
            destBasicType = prop_type.basicType
            if not destBasicType.contains(sourceBasicType):
                raise RuntimeError("Couldn't set property")

        self._property_values[name] = value


class Edge:
    def __init__(self, source_node_id, event_name, dest_node_id, handler_name):
        self.id = str(uuid.uuid4())
        self.source_node_id = source_node_id
        self.event_name = event_name
        self.dest_node_id = dest_node_id
        self.handler_name = handler_name

class Graph:
    def __init__(self):
        self._nodes = {}
        self._edges = []
        self.server_fabric = ""


    def serializeForExecutor(self):
        result = {}

        result["server-fabric"] = self.server_fabric
        result["nodes"] = {}
        result["edges"] = []

        for n in self.nodes.values():
            result["nodes"][n.id] = {
                "type": {
                    "name": n.type.name,
                    "fabric": n.fabric
                }
            }

        for e in self.edges:
            result["edges"].append({
                "source": e.source_node_id,
                "event": e.event_name,
                "destination": e.dest_node_id,
                "handler": e.handler_name
            })


        return json.dumps(result, indent=2)

    @property
    def nodes(self):
        return self._nodes

    @property
    def edges(self):
        return self._edges

    def node(self, id):
        return self._nodes[id]

    def contains_node(self, id):
        return id in self._nodes


    def can_connect(self, source_node, event_name: str, dest_node: NodeType, handler_name: str):
        source_node_id = source_node.id
        dest_node_id = dest_node.id

        edge = Edge(source_node_id, event_name, dest_node_id, handler_name)
        all_edges = self._edges + [edge]

        if event_name not in self.node(edge.source_node_id).type.events:
            return False, "Node {node} doesn't have event {event}".format(node=self.node(edge.source_node_id).type.name, event=event_name)

        if handler_name not in self.node(edge.dest_node_id).type.handlers:
            return False, "Node {node} doesn't have handler {handler}".format(node=self.node(edge.dest_node_id).type.name, handler=handler_name)

        types_info = {}
        for _, node in self._nodes.items():
            types_info[node.id] = {}
            types_info[node.id]["events"] = copy.deepcopy(node.type.events)

            types_info[node.id]["handlers"] = {}
            for h, t in node.type.handlers.items():
                types_info[node.id]["handlers"][h] = copy.deepcopy(t.type)

        if dest_node.type.handlers[handler_name].single == True:
            if len(list(filter(lambda e: e.handler_name == handler_name and e.dest_node_id == dest_node_id, all_edges))) > 1:
                return False, "Handler {handler} of node {node} can't have multiple inputs".format(handler=handler_name, node=dest_node_id)

        while True:
            specialized = False
            for edge in all_edges:
                source_type = types_info[edge.source_node_id]["events"][edge.event_name]
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
                    if not self._nodes[edge.dest_node_id].type.handlers[edge.handler_name].single:
                        continue

                    if type(intersected_type) != type(types_info[node_id][connector_type][connector_name]):
                        types_info[node_id][connector_type][connector_name] = intersected_type
                        try:
                            updated, refined_types = self._nodes[node_id].type.specializeTypes(types_info[node_id], self.node(node_id)._property_values)
                            if updated == True:
                                types_info[node_id] = refined_types
                        except RuntimeError as e:
                            return False, str(e)

            if specialized == False:
                break
        return True, "Success"

    def connect(self, source_node: Node, event_name: str, dest_node: Node, handler_name: str):
        result, msg = self.can_connect(source_node, event_name, dest_node, handler_name)
        if not result:
            raise RuntimeError(msg)

        edge = Edge(source_node.id, event_name, dest_node.id, handler_name)
        self._edges.append(edge)
        return edge

    def addNode(self, node_type):
        node = Node(node_type, None)

        node.graph = self
        self._nodes[node.id] = node
        return node


    def removeNode(self, node_id):
        if node_id in self._nodes:
            del self._nodes[node_id]
            self._edges = list(filter(lambda e: e.source_node_id != node_id and e.dest_node_id != node_id, self.edges))

    def removeEdge(self, edge_id):
        self._edges = list(filter(lambda e: e.id != edge_id, self.edges))

