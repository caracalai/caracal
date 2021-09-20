from bblocks.declaration import *
from bblocks.declaration.nodetype import *
from bblocks.proto import protoserializer
import base64
import copy
import uuid
import json

from bblocks.proto.protoserializer import ProtoSerializer


class Node:
    def __init__(self, node_value, values):
        self.node_value = node_value
        self._values = values
        self.id = "{t}_{id}".format(t="<undefined_name>", id=str(uuid.uuid4()))
        self.graph = None
        self.location = (-1, -1)
        self.property_values = {}
        self.fabric = ""


    def setProperty(self, name, value):
        if not name in self.node_value.properties.keys():
            raise RuntimeError("Couldn't set property")

        prop_type = self.node_value._properties[name].type
        if not prop_type.contains_value(value):
            raise RuntimeError("Couldn't set property")

        # if isinstance(prop_type, DataSourceType):
        #     if not self.graph.contains_node(value):
        #         raise RuntimeError("Couldn't set property")
        #
        #     if not isinstance(self.graph.node(value).type, TableDataSourceNode):
        #         raise RuntimeError("Couldn't set property")
        #
        #
        #     # TableDataSourceNode
        #     sourceBasicType = self.graph.node(value).type.basicType
        #     destBasicType = prop_type.basicType
        #     if not destBasicType.contains(sourceBasicType):
        #         raise RuntimeError("Couldn't set property")

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
        self.nodes = {}
        self._edges = []
        self.server_fabric = ""


    def serializeForExecutor(self):
        result = {}

        result["server-fabric"] = self.server_fabric
        result["nodes"] = {}
        result["edges"] = []

        for n in self.nodes.values():
            properties = {}
            for prop_name, info in n.type.properties.items():
                prop_value = info.default_value
                if prop_name in n.property_values:
                    prop_value = n.property_values[prop_name]
                if prop_value != None:
                    properties[prop_name] = base64.b64encode(
                        ProtoSerializer().serialize_message(0, prop_value).SerializeToString()
                    ).decode('ascii')
            result["nodes"][n.id] = {
                "type": {
                    "name": n.type.name,
                    "properties": properties,
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

    def node(self, id):
        return self.nodes[id]

    def contains_node(self, id):
        return id in self.nodes


    def can_connect(self, source_node, event_name: str, dest_node: NodeType, handler_name: str):
        source_node_id = source_node.id
        dest_node_id = dest_node.id

        edge = Edge(source_node_id, event_name, dest_node_id, handler_name)
        all_edges = self._edges + [edge]


        a = self.node(edge.source_node_id).node_value
        if event_name not in self.node(edge.source_node_id).node_value.events:
            return False, "Node {node} doesn't have event {event}".format(node=self.node(edge.source_node_id).node_value.name, event=event_name)

        if handler_name not in self.node(edge.dest_node_id).node_value.handlers:
            return False, "Node {node} doesn't have handler {handler}".format(node=self.node(edge.dest_node_id).node_value.name, handler=handler_name)

        types_info = {}
        for _, node in self.nodes.items():
            types_info[node.id] = {}
            types_info[node.id]["events"] = copy.deepcopy(node.node_value.events)

            types_info[node.id]["handlers"] = {}
            for h, t in node.node_value.handlers.items():
                types_info[node.id]["handlers"][h] = copy.deepcopy(t.type)

        if not dest_node.node_value.handlers[handler_name].receives_multiple:
            if len(list(filter(lambda e: e.handler_name == handler_name and e.dest_node_id == dest_node_id, all_edges))) > 1:
                return False, "Handler {handler} of node {node} can't have multiple inputs".format(handler=handler_name, node=dest_node_id)

        while True:
            specialized = False
            for edge in all_edges:
                source_type = types_info[edge.source_node_id]["events"][edge.event_name].type
                dest_type = types_info[edge.dest_node_id]["handlers"][edge.handler_name]
                intersected_type = source_type.intersect(dest_type)
                if intersected_type == None:
                    return False, "Couldn't match types of {source_node}.{event} ('{source_class}') and {dest_node}.{handler} ('{dest_class}')" \
                            .format(source_node=self.node(edge.source_node_id).node_value.name,
                                    event=edge.event_name,
                                    dest_node=self.node(edge.dest_node_id).node_value.name,
                                    handler=edge.handler_name,
                                    source_class=source_type.name,
                                    dest_class=dest_type.name)


                for node_id, connector_type, connector_name in [
                    (edge.source_node_id, "events", edge.event_name),
                    (edge.dest_node_id, "handlers", edge.handler_name)]:
                    if self.nodes[edge.dest_node_id].node_value.handlers[edge.handler_name].receives_multiple:
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
        self._edges.append(edge)
        return edge

    def addNode(self, node_value):
        node = Node(node_value, None)

        node.graph = self
        self.nodes[node.id] = node
        return node

    def removeNode(self, node_id):
        if node_id in self.nodes:
            del self.nodes[node_id]
            self._edges = list(filter(lambda e: e.source_node_id != node_id and e.dest_node_id != node_id, self.edges))

    def removeEdge(self, edge_id):
        self._edges = list(filter(lambda e: e.id != edge_id, self.edges))

