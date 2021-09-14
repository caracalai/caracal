import json

import zmq,  threading
import logging

class NodeServer:
    def __init__(self, config, port = None):
        self._context = zmq.Context()
        self._socket = self._context.socket(zmq.REP)
        if port is not None:
            self._socket.bind("tcp://127.0.0.1:{port}".format(port=port))
            self._socket_port = port
        else:
            self._socket_port = self._socket.bind_to_random_port("tcp://127.0.0.1")
        self._config = config
        self._stopped = False
        self._initialized_nodes = set()
        self._next_msg_index = 0
        self._worker = None

    def start(self):
        self._worker = threading.Thread(target=self._execute)
        self._worker.start()

    def stop(self):
        self._stopped = True

    def wait(self):
        self._worker.join()

    def wait_for_finished(self):
        self.stop()
        self._context.destroy()
        self._worker.join()
        self._stopped = False

    def stopped(self):
        return self._stopped

    def endpoint(self):
        return "tcp://127.0.0.1:{port}".format(port=self._socket_port)

    def _all_nodes_are_registered(self):
        for item in self._config["nodes"].values():
            for param in ["publisher_endpoint", "service_endpoint"]:
                if not (param in item and item[param] != ""):
                    return False
        return True

    def _find_edges(self, source_id="", destination_id=""):
        result = list(self._config["edges"])
        if source_id != "":
            result = list(filter(lambda x: x["source"] == source_id, result))
        if destination_id != "":
            result = list(filter(lambda x: x["destination"] == destination_id, result))
        return result

    def _find_source_nodes(self, destination_id=""):
        return list(set(map(lambda x: x["source"], self._find_edges(destination_id=destination_id))))

    def _initialize_nodes(self):
        for id, node in self._config["nodes"].items():
            sock = self._context.socket(zmq.REQ)
            sock.connect(node["service_endpoint"])

            node_config = {}
            node_config["id"] = id
            node_config["input_nodes"] = []

            input_node_ids = self._find_source_nodes(id)
            for input_node_id in input_node_ids:
                input_node = {"id": input_node_id,
                              "publisher_endpoint": self._config["nodes"][input_node_id]["publisher_endpoint"],
                              "edges": list(map(lambda x: {"event": x["event"], "handler": x["handler"]},
                                                self._find_edges(source_id=input_node_id, destination_id=id)))}
                node_config["input_nodes"].append(input_node)
            sock.send(json.dumps(node_config).encode("utf8"))
            sock.close()

    def _finish_nodes(self):
        for id, node in self._config["nodes"].items():
            sock = self._context.socket(zmq.REQ)
            sock.connect(node["service_endpoint"])
            sock.send(json.dumps({"id": id, "finish": "true"}).encode("utf8"))
            sock.close()

    def _start_nodes(self):
        for id, node in self._config["nodes"].items():
            sock = self._context.socket(zmq.REQ)
            sock.connect(node["service_endpoint"])
            sock.send(json.dumps({"id": id, "start": "true"}).encode("utf8"))

    def _execute(self):
        logging.debug("NodeServer: starting execution...")
        while not self.stopped():
            try:
                msg = self._socket.recv()
                if self.stopped():
                    break

                request = json.loads(msg)
                if not "command" in request:
                    logging.debug("NodeServer: Failed request")
                    self._socket.send(json.dumps({"success": "false"}).encode("utf8"))
                    continue

                cmd = request["command"]
                if cmd == "register":
                    id = request["id"]
                    logging.debug("NodeServer: Registration of {}".format(id))

                    self._config["nodes"][id]["publisher_endpoint"] = request["publisher_endpoint"]
                    self._config["nodes"][id]["service_endpoint"] = request["service_endpoint"]
                    self._socket.send(json.dumps({"success": "true"}).encode("utf8"))

                    if self._all_nodes_are_registered():
                        self._initialize_nodes()
                    continue

                if cmd == "ready-to-work":
                    logging.debug("NodeServer: Node {} is ready to work".format(id))

                    self._socket.send(json.dumps({"success": "true"}).encode("utf8"))
                    self._initialized_nodes.add(request["id"])
                    graph_node_ids = set(self._config["nodes"].keys())
                    if graph_node_ids.issubset(self._initialized_nodes):
                        logging.debug("NodeServer: all nodes are ready. Starting nodes")
                        self._finish_nodes()
                    continue

                if cmd == "generate-next-message-index":
                    self._socket.send(json.dumps({"index": self._next_msg_index}).encode("utf8"))
                    self._next_msg_index += 1
                    continue
                if cmd == "finish":
                    self._finish_nodes()
                    continue
                logging.warning("NodeServer: undefined command {cmd}".format(cmd=cmd))
            except:
                logging.debug("Socked is closed")
        logging.debug("NodeServer: Finished execution...")
