import zmq, json
import threading
import logging
from bblocks.proto.protoserializer import *
from bblocks.proto.basictypes_pb2 import *
from bblocks.declaration import nodetype
import inspect
import uuid

from collections import namedtuple
_Event = namedtuple("_Event", ["source_id", "event"])
import bblocks.execution.session as session


class Handler:
    def __init__(self, name, type, receives_multiple, info, function):
        self.declaration = nodetype.HandlerDeclaration(name, type, receives_multiple, info)
        self.function = function
        self.connected_events = []
        self.parent = None

    def __call__(self, *args):
        self.function(self.parent, *args)

    def connect(self, event):
        self.connected_events.append(event)


def handler(name, type, receives_multiple=False, info=None, function=None):
    if function:
        return Handler(function)
    else:
        def wrapper(func):
            return Handler(name, type, receives_multiple, info, func)
        return wrapper


class Property:
    def __init__(self, type, optional, default_value=None):
        self.declaration = nodetype.PropertyDeclaration(type, optional, default_value)
        self.parent = None
        self.value = None


class Event:
    def __init__(self, name, type, info=None):
        self.declaration = nodetype.EventDeclaration(name, type, info)
        self.parent = None

    @property
    def node_id(self):
        return self.parent.id


class ExternalEvent(Event):
    def __init__(self, name, type, node_id):
        self.declaration = nodetype.EventDeclaration(name, type)
        self.parent = None
        self.node_id = node_id




class Message:
    def __init__(self, id=None, value=None):
        self.id = id
        self.value = value

class Node:
    def __init__(self, id=None):
        self.stopped = False
        self.context = zmq.Context()
        self.sub_socket = None
        self.pub_socket = None
        self.service_socket = None
        self.event2handler = {}
        self.port = ""
        self.handlers = {}
        self.events = {}
        self.session = session.current_session
        self.session.add(self)
        self.id = id if id != None else str(uuid.uuid1())
        self.pub_port = None
        self.service_port = None
        self.terminated = False

        self.events_processor = None
        self.events_from_server_processor = None
        self.run_processor = None

    @property
    def name(self):
        return self.__class__.__name__

    @property
    def type(self):
        result = nodetype.NodeTypeDeclaration()
        name = self.name
        for _, item in self.handlers:
            result.handlers[item.declaration.id] = item.declaration
        for _, item in self.properties:
            result.properties[item.declaration.id] = item.declaration
        return result

    @property
    def pub_endpoint(self):
        return "tcp://127.0.0.1:{port}".format(self.pub_port)

    @property
    def service_endpoint(self):
        return "tcp://127.0.0.1:{port}".format(self.service_port)

    def __setattr__(self, name, value):
        if isinstance(value, Property):
            value.parent = self
        if isinstance(value, Event):
            value.parent = self
            self.events[value.declaration.name] = value
        super().__setattr__(name, value)


    def __getattribute__(self, item):
        result = super().__getattribute__(item)
        if isinstance(result, Handler):
            self.handlers[result.declaration.name] = result
            result.parent = self
        # if isinstance(result, Event):
        #     result.parent = self
        return result

    def set_server_endpoint(self, server_endpoint):
        self.port = server_endpoint

    def start(self):
        worker = threading.Thread(target=self.execute)
        worker.start()

    def initialize(self):
        pass

    def run(self):
        pass

    def stop(self):
        self.stopped = True

    def wait(self):
        # self.stopped = True
        for processor in [self.events_processor, self.events_from_server_processor,
                          self.run_processor]:
            if processor != None:
                processor.join()

    def close_all_sockets(self):
        for socket in [self.sub_socket, self.pub_socket, self.service_socket]:
            try:
                socket.close()
            except Exception as e:
                print('Trying to close down socket: {} resulted in error: {}'.format(socket, e))
        self.context.term()

    def register_event(self, name):
        raise Exception("register_event")

    def register_handler(self, name, func):
        self.handlers[name] = func

    @property
    def server_endpoint(self):
        return "tcp://127.0.0.1:{port}".format(port=self.session.server_port)

    def message_id(self):
        sock = self.context.socket(zmq.REQ)
        sock.connect(self.server_endpoint)
        sock.send(json.dumps({"command": "generate-next-message-index"}).encode("utf8"))
        msg = json.loads(sock.recv())
        sock.close()
        return int(msg["index"])


    def fire(self, event, value, msg_id=None):
        try:
            event = event.declaration.name
            if not event in self.events.keys():
                logging.warning("Node {name}: Couldn't generate event. Error: undefined event '{event}'".format(name=self.id, event=event))
                return
            if msg_id is None:
                msg_id = self.message_id()
            msg = ProtoSerializer().serialize_message(msg_id, value)
            prefix = "{id}|{event} ".format(id=self.id, event=event).encode("utf8")
            self.pub_socket.send(prefix + msg.SerializeToString(), zmq.DONTWAIT)
        except:
            logging.warning("Node {name}:could not send message exception".format(name=self.id))


    def terminate(self):
        if self.terminated == False:
            self.terminated = True
            sock = self.context.socket(zmq.REQ)
            sock.connect(self.server_endpoint)
            sock.send(json.dumps({"command": "terminate"}).encode("utf8"))
            msg = json.loads(sock.recv())
            sock.close()

    def wait_answer_from_server(self):
        msg = self.service_socket.recv()

        config = json.loads(msg)
        self.service_socket.send(json.dumps({"success": True}).encode("utf8"))
        return config

    def initialize_listener(self, config):
        self.sub_socket = self.context.socket(zmq.SUB)

        input_node_ids = set()
        for handler in self.handlers.values():
            for event in handler.connected_events:
                input_node_ids.add(event.node_id)

        for input_node_id in input_node_ids:
            if not input_node_id in config:
                pass
            self.sub_socket.connect(config[input_node_id]["publisher_endpoint"])
            logging.debug("Node {id} subscriber listens: {addr}".format(
                id=self.id, addr=config[input_node_id]["publisher_endpoint"]))

            for handler in self.handlers.values():
                for event in handler.connected_events:
                    if event.node_id != input_node_id:
                        continue
                    self.event2handler[_Event(event=event.declaration.name, source_id=event.node_id)] = handler.declaration.name
                    topic = "{source_id}|{event}".format(
                        source_id=event.node_id, event=event.declaration.name)
                    self.sub_socket.set(zmq.SUBSCRIBE, topic.encode("utf8"))
                    logging.debug("Node {id}: topic={topic}".format(id=self.id, topic=topic))

    def send_command(self, request):
        sock = self.context.socket(zmq.REQ)
        sock.connect(self.server_endpoint)
        sock.send(request.encode("utf8"))
        sock.close()

    def process_events_from_server(self):
        logging.debug("Node {name}:process_events_from_server1".format(name=self.id))
        while not self.stopped:
            logging.debug("Node {name}:process_events_from_server2".format(name=self.id))
            msg = self.service_socket.recv()
            config = json.loads(msg)
            logging.debug("Node {name}:process_events_from_server3".format(name=self.id))
            self.service_socket.send(json.dumps({"success": True}).encode("utf8"))
            self.stopped = True
            self.close_all_sockets()

            logging.debug("Node {name}:process_events_from_server4".format(name=self.id))
            self.run_processor.join()
            logging.debug("Node {name}:process_events_from_server5".format(name=self.id))
            logging.debug("Node {name}:process_events_from_server6".format(name=self.id))
            break
        logging.debug("Node {name}:process_events_from_server finished".format(name=self.id))

    def _process_events(self):
        if len(self.event2handler) == 0:
            return
        while not self.stopped:
            try:
                logging.debug("Node {name}: waiting for the next event...".format(name=self.id))
                msg = self.sub_socket.recv()
                index = msg.find(b" ")
                source_id, event = msg[:index].decode("utf8").split("|")
                binary_msg = basictypes_pb2.Message()
                binary_msg.ParseFromString(msg[index+1:])

                msg_id, msg_value = ProtoSerializer().deserialize_message(binary_msg)
                message = Message(msg_id, msg_value)
                handler_name = self.event2handler[_Event(source_id=source_id, event=event)]
                self.handlers[handler_name](message)
            except Exception as e:
                logging.warning("Node {name}: Exception {e}".format(name=self.id, e=e))
                break

        logging.debug("Node {name}: Finished processing events".format(name=self.id))

    def execute(self):
        logging.debug("Execute started")

        # step0: publisher
        self.pub_socket = self.context.socket(zmq.PUB)
        self.pub_port = self.pub_socket.bind_to_random_port("tcp://127.0.0.1")
        logging.debug("Node {id}. Publisher connected to port={port}".format(id=self.id, port=self.pub_port))

        # step1: initialize node
        self.initialize()

        # step2: initialize service socket
        self.service_socket = self.context.socket(zmq.REP)
        self.service_port = self.service_socket.bind_to_random_port("tcp://127.0.0.1")
        logging.debug("Node {id}. Service connected to port={port}".format(id=self.id, port=self.service_port))

        # step3: register socket on the server
        self.send_command(json.dumps({
            "command": "register",
            "id": self.id,
            "publisher_endpoint": "tcp://127.0.0.1:{port}".format(port=self.pub_port),
            "service_endpoint": "tcp://127.0.0.1:{port}".format(port=self.service_port)}, sort_keys=True))
        answer = self.wait_answer_from_server()

        self.initialize_listener(answer)
        self.send_command(json.dumps({
            "command": "ready-to-work",
            "id": self.id
        }))
        answer = self.wait_answer_from_server()


        self.events_processor = threading.Thread(target=self._process_events)
        self.events_processor.start()

        self.events_from_server_processor = threading.Thread(target=self.process_events_from_server)
        self.events_from_server_processor.start()

        self.run_processor = threading.Thread(target=self.run)
        self.run_processor.start()