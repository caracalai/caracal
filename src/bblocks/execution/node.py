import zmq, json
import threading
import logging
from bblocks.proto.protoserializer import *
from bblocks.proto.basictypes_pb2 import *
from bblocks.declaration.nodetype import *
import inspect

from collections import namedtuple
_Event = namedtuple("_Event", ["source_id", "event"])
from bblocks.declaration.nodetype import Handler, Event
import bblocks.execution.session as session

class Message:
    def __init__(self, id=None, value=None):
        self.id = id
        self.value = value

class Node:
    def __init__(self):
        self._worker = None
        self._stopped = False
        self.context = zmq.Context()
        self._sub_socket = None
        self._pub_socket = None
        self._service_socket = None
        self._event2handler = {}
        self.port = ""
        self.handlers = {}
        self.events = {}
        self._session = session.current_session
        self._session.add(self)

    @property
    def name(self):
        return self.__class__.__name__

    def __setattr__(self, name, value):
        if isinstance(value, Property):
            value.parent = self
        if isinstance(value, Event):
            value.parent = self
            self.events[value.name] = value
        super().__setattr__(name, value)


    def __getattribute__(self, item):
        result = super().__getattribute__(item)
        if isinstance(result, Handler):
            self.handlers[result.name] = result
            result.parent = self
        # if isinstance(result, Event):
        #     result.parent = self
        return result

    def set_id(self, id):
        self._id = id

    def id(self):
        return self._id

    def set_server_endpoint(self, server_endpoint):
        self.port = server_endpoint

    def start(self):
        self._worker = threading.Thread(target=self._execute)
        self._worker.start()

    def initialize(self):
        pass

    def run(self):
        pass

    def stop(self):
        self._stopped = True

    def stopped(self):
        return self._stopped

    def wait(self):
        self._worker.join()

    def wait_for_finished(self):
        for socket in [self._sub_socket, self._pub_socket, self._service_socket]:
            try:
                socket.close()
            except Exception as e:
                print('Trying to close down socket: {} resulted in error: {}'.format(socket, e))

        self.context.term()
        if self._worker is not None:
            self._worker.join()

    def register_event(self, name):
        raise Exception("register_event")

    def register_handler(self, name, func):
        self.handlers[name] = func

    @property
    def server_endpoint(self):
        return "tcp://127.0.0.1:{port}".format(port=self.port)

    def _message_id(self):
        sock = self.context.socket(zmq.REQ)
        sock.connect(self.server_endpoint)
        sock.send(json.dumps({"command": "generate-next-message-index"}).encode("utf8"))
        msg = json.loads(sock.recv())
        sock.close()
        return int(msg["index"])

    def generate_event(self, event, value, msg_id=None):
        if not event in self.events.keys():
            logging.warning("Node {name}: Couldn't generate event. Error: undefined event '{event}'".format(name=self.id(), event=event))
            return
        if msg_id is None:
            msg_id = self._message_id()
        msg = ProtoSerializer().serialize_message(msg_id, value)
        logging.debug("Node {name}:send event".format(name=self.id()))
        prefix = "{id}|{event} ".format(id=self.id(), event=event).encode("utf8")
        self._pub_socket.send(prefix + msg.SerializeToString(), zmq.DONTWAIT)

    def _wait_answer_from_server(self):
        msg = self._service_socket.recv()

        config = json.loads(msg)
        self._service_socket.send(json.dumps({"success": True}).encode("utf8"))
        return config

    def _initialize_listener(self, config):
        self._sub_socket = self.context.socket(zmq.SUB)
        for input_node in config["input_nodes"]:
            self._sub_socket.connect(input_node["publisher_endpoint"])
            logging.debug("Node {id} subscriber listens: {addr}".format(
                id=self.id(), addr=input_node["publisher_endpoint"]))

            for edge in input_node["edges"]:
                self._event2handler[_Event(event=edge["event"], source_id=input_node["id"])] = edge["handler"]
                topic = "{source_id}|{event}".format(
                    source_id=input_node["id"], event=edge["event"])
                self._sub_socket.set(zmq.SUBSCRIBE, topic.encode("utf8"))
                logging.debug("Node {id}: topic={topic}".format(
                    id=self.id(), topic=topic))

    def _send_command(self, request):
        sock = self.context.socket(zmq.REQ)
        sock.connect(self.server_endpoint)
        sock.send(request.encode("utf8"))
        sock.close()

    def _process_events_from_server(self):
        while True:
            msg = self._service_socket.recv()
            config = json.loads(msg)
            self._service_socket.send(json.dumps({"success": True}).encode("utf8"))

    def _process_events(self):
        if len(self._event2handler) == 0:
            return
        while not self.stopped():
            try:
                logging.debug("Node {name}: waiting for the next event...".format(name=self.id()))
                msg = self._sub_socket.recv()
                index = msg.find(b" ")
                source_id, event = msg[:index].decode("utf8").split("|")
                binary_msg = basictypes_pb2.Message()
                binary_msg.ParseFromString(msg[index+1:])

                msg_id, msg_value = ProtoSerializer().deserialize_message(binary_msg)
                message = Message(msg_id, msg_value)
                handler_name = self._event2handler[_Event(source_id=source_id, event=event)]
                self.handlers[handler_name](message)
            except Exception as e:
                break

        logging.debug("Node {name}: Finished processing events".format(name=self.id()))

    def _execute(self):
        logging.debug("Execute started")

        # step0: publisher
        self._pub_socket = self.context.socket(zmq.PUB)
        pub_port = self._pub_socket.bind_to_random_port("tcp://127.0.0.1")
        logging.debug("Node {id}. Publisher connected to port={port}".format(id=self.id(), port=pub_port))

        # step1: initialize node
        self.initialize()

        # step2: initialize service socket
        self._service_socket = self.context.socket(zmq.REP)
        service_port = self._service_socket.bind_to_random_port("tcp://127.0.0.1")
        logging.debug("Node {id}. Service connected to port={port}".format(id=self.id(), port=service_port))

        # step3: register socket on the server
        self._send_command(json.dumps({
            "command": "register",
            "id": self.id(),
            "publisher_endpoint": "tcp://127.0.0.1:{port}".format(port=pub_port),
            "service_endpoint": "tcp://127.0.0.1:{port}".format(port=service_port)}, sort_keys=True))
        answer = self._wait_answer_from_server()

        self._initialize_listener(answer)
        self._send_command(json.dumps({
            "command": "ready-to-work",
            "id": self.id()
        }))
        answer = self._wait_answer_from_server()
        self._events_processor = threading.Thread(target=self._process_events)
        self._events_processor.start()

        self.run()