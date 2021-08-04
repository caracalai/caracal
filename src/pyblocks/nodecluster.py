from pyblocks.nodeserver import NodeServer

class NodeCluster:
    def __init__(self, name, config):
        self._name = name
        self._config = config
        self._server_node = None
        self._nodes = []

    def start(self, server_endpoint, server_port):
        if self._name == self._config["server-fabric"]:
            self._server_node = NodeServer(self._config, server_port)
            self._server_node.start()
            server_endpoint = self._server_node.endpoint()

        for id, node_info in self._config["nodes"].items():
            if node_info['type']["fabric"] != self._name:
                continue

            node = self.create_node(node_info["type"]['name'])
            node.set_id(id)
            node.set_server_endpoint(server_endpoint)
            node.start()
            self._nodes.append(node)

    def wait(self):
        self._server_node.wait()
        for node in self._nodes:
            node.wait()

    def wait_for_finished(self):
        self._server_node.wait_for_finished()
        for node in self._nodes:
            node.wait_for_finished()

    def create_node(self, name):
        raise RuntimeError("Undefined method")