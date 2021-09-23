import json
import zmq, threading
import logging


class NodeServer:
    def __init__(self, all_nodes_list, port=None):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        if port is not None:
            self.socket.bind("tcp://127.0.0.1:{port}".format(port=port))
            self.port = port
        else:
            self.port = self.socket.bind_to_random_port("tcp://127.0.0.1")
        self.all_nodes_list = all_nodes_list
        self.stopped = False
        self.initialized_nodes = set()
        self.next_msg_index = 0
        self.worker = None
        self.nodes_info = {}

    def start(self):
        self.worker = threading.Thread(target=self._execute)
        self.worker.start()

    def stop(self):
        self.stopped = True

    def wait(self):
        self.worker.join()

    def wait_for_finished(self):
        self.stop()
        for socket in [self.socket]:
            try:
                socket.close()
            except Exception as e:
                print('Trying to close down socket: {} resulted in error: {}'.format(socket, e))

        self.context.term()
        self.worker.join()
        self.stopped = False

    def endpoint(self):
        return "tcp://127.0.0.1:{port}".format(port=self.port)

    def _initialize_nodes(self):
        for node in self.nodes_info.values():
            sock = self.context.socket(zmq.REQ)
            sock.connect(node["service_endpoint"])

            sock.send(json.dumps(self.nodes_info).encode("utf8"))
            sock.close()

    def _finish_nodes(self):
        for node in self.nodes_info.values():
            sock = self.context.socket(zmq.REQ)
            sock.connect(node["service_endpoint"])
            sock.send(json.dumps({"id": id, "finish": "true"}).encode("utf8"))
            sock.close()

    def _start_nodes(self):
        for id, node in self.nodes_info.items():
            sock = self.context.socket(zmq.REQ)
            sock.connect(node["service_endpoint"])
            sock.send(json.dumps({"id": id, "start": "true"}).encode("utf8"))
            sock.close()

    def _all_nodes_are_registered(self):
        for id in self.all_nodes_list:
            if id not in self.nodes_info:
                return False
            for param in ["publisher_endpoint", "service_endpoint"]:
                if not (param in self.nodes_info[id] and self.nodes_info[id] != ""):
                    return False
        return True

    def _execute(self):
        logging.debug("NodeServer: starting execution...")
        while not self.stopped:
            try:
                msg = self.socket.recv()
                if self.stopped:
                    break

                request = json.loads(msg)
                if not "command" in request:
                    logging.debug("NodeServer: Failed request")
                    self.socket.send(json.dumps({"success": "false"}).encode("utf8"))
                    continue

                cmd = request["command"]
                if cmd == "register":
                    id = request["id"]
                    logging.debug("NodeServer: Registration of {}".format(id))

                    self.nodes_info[id] = {
                        "publisher_endpoint": request["publisher_endpoint"],
                        "service_endpoint": request["service_endpoint"]
                    }
                    self.socket.send(json.dumps({"success": "true"}).encode("utf8"))

                    if self._all_nodes_are_registered():
                        self._initialize_nodes()
                    continue

                if cmd == "ready-to-work":
                    logging.debug("NodeServer: Node {} is ready to work".format(id))

                    self.socket.send(json.dumps({"success": "true"}).encode("utf8"))
                    self.initialized_nodes.add(request["id"])
                    graph_node_ids = set(self.all_nodes_list)

                    if graph_node_ids.issubset(self.initialized_nodes):
                        logging.debug("NodeServer: all nodes are ready. Starting nodes")
                        self._start_nodes()
                    continue

                if cmd == "generate-next-message-index":
                    self.socket.send(json.dumps({"index": self.next_msg_index}).encode("utf8"))
                    self.next_msg_index += 1
                    continue
                logging.warning("NodeServer: undefined command {cmd}".format(cmd=cmd))
            except Exception as e:
                logging.debug("Socked is closed")
                break
        logging.debug("NodeServer: Finished execution...")
