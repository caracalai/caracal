import json
import logging
import threading

import zmq


class NodeServer:
    def __init__(self, all_nodes_list, port=None):
        self.context = zmq.Context()
        # self.context.setsockopt(zmq.LINGER, 100)
        self.socket = self.context.socket(zmq.REP)
        # self.socket.setsockopt(zmq.LINGER, 100)
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
        logging.debug("all_nodes_list: " + str(self.all_nodes_list))

    def start(self):
        self.worker = threading.Thread(target=self.execute)
        self.worker.start()

    def stop(self):
        self.stopped = True

    def wait(self):
        self.worker.join()

    def wait_for_finished(self):
        self.stop()
        for socket in [self.socket]:
            try:
                socket.close(linger=0)
            except Exception as e:
                print(
                    "Trying to close down socket: {} resulted in error: {}".format(
                        socket, e
                    )
                )

        self.context.term()
        self.worker.join()
        self.stopped = False

    def endpoint(self):
        return "tcp://127.0.0.1:{port}".format(port=self.port)

    def initialize_nodes(self):
        for node in self.nodes_info.values():
            sock = self.context.socket(zmq.REQ)
            # sock.setsockopt(zmq.LINGER, 100)
            sock.connect(node["service_endpoint"])

            sock.send(json.dumps(self.nodes_info).encode("utf8"))
            sock.close(linger=100)

    def finish_nodes(self):
        for id_, node in self.nodes_info.items():
            sock = self.context.socket(zmq.REQ)
            # sock.setsockopt(zmq.LINGER, 100)
            sock.connect(node["service_endpoint"])
            sock.send(json.dumps({"id": id_, "finish": "true"}).encode("utf8"))
            sock.close(linger=100)

    def start_nodes(self):
        for id_, node in self.nodes_info.items():
            sock = self.context.socket(zmq.REQ)
            # sock.setsockopt(zmq.LINGER, 100)
            sock.connect(node["service_endpoint"])
            sock.send(json.dumps({"id": id_, "start": "true"}).encode("utf8"))
            sock.close(linger=100)

    def all_nodes_are_registered(self):
        for id_ in self.all_nodes_list:
            if id_ not in self.nodes_info:
                return False
            for param in ["publisher_endpoint", "service_endpoint"]:
                if not (param in self.nodes_info[id_] and self.nodes_info[id_] != ""):
                    return False
        return True

    def execute(self):
        logging.debug("Server: starting execution...")
        while not self.stopped:
            try:
                msg = self.socket.recv()
                if self.stopped:
                    break

                request = json.loads(msg)
                if "command" not in request:
                    logging.debug("Server: Failed request")
                    self.socket.send(json.dumps({"success": "false"}).encode("utf8"))
                    continue

                cmd = request["command"]
                if cmd == "register":
                    id_ = request["id"]
                    logging.debug("Server: Registration of {}".format(id_))

                    self.nodes_info[id_] = {
                        "publisher_endpoint": request["publisher_endpoint"],
                        "service_endpoint": request["service_endpoint"],
                    }
                    self.socket.send(json.dumps({"success": "true"}).encode("utf8"))

                    if self.all_nodes_are_registered():
                        logging.debug(
                            "Server: all nodes are registered. Starting initialization..."
                        )
                        self.initialize_nodes()
                    continue

                if cmd == "terminate":
                    self.socket.send(json.dumps({"success": "true"}).encode("utf8"))
                    for id_, node in self.nodes_info.items():
                        sock = self.context.socket(zmq.REQ)
                        # sock.setsockopt(zmq.LINGER, 100)
                        sock.connect(node["service_endpoint"])
                        sock.send(
                            json.dumps({"id": id_, "terminate": "true"}).encode("utf8")
                        )
                        sock.close(linger=100)
                    break

                if cmd == "ready-to-work":
                    id_ = request["id"]
                    logging.debug("Server: Node {} is ready to work".format(id_))

                    self.socket.send(json.dumps({"success": "true"}).encode("utf8"))
                    self.initialized_nodes.add(request["id"])
                    graph_node_ids = set(self.all_nodes_list)

                    if graph_node_ids.issubset(self.initialized_nodes):
                        logging.debug("Server: all nodes are ready. Starting nodes")
                        self.start_nodes()
                    continue

                if cmd == "generate-next-message-index":
                    self.socket.send(
                        json.dumps({"index": self.next_msg_index}).encode("utf8")
                    )
                    self.next_msg_index += 1
                    continue
                logging.warning("Server: undefined command {cmd}".format(cmd=cmd))
            except Exception:
                logging.debug("Socket is closed")
                break
        logging.debug("Server: Finished execution...")

    def __del__(self):
        if not self.context.closed:
            self.context.destroy(linger=100)
        del self
