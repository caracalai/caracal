from collections import namedtuple
import json
import logging
import queue
import threading
from typing import Callable
import uuid


from broutonblocks.declaration import nodetype
from broutonblocks.execution import session
from broutonblocks.proto import basictypes_pb2
from broutonblocks.proto.protoserializer import ProtoSerializer
import zmq

_Event = namedtuple("_Event", ["source_id", "event"])


class Handler:
    def __init__(
        self,
        name: str,
        type_: list,
        receives_multiple: bool,
        info: nodetype.MetaInfo,
        function: Callable,
    ):
        self.declaration = nodetype.HandlerDeclaration(
            name, type_, receives_multiple, info
        )
        self.function = function
        self.connected_events = []
        self.parent = None

    def __call__(self, *args):
        self.function(self.parent, *args)

    def connect(self, event):
        if self.connected_events and not self.receives_multiple:
            raise Exception()
        self.connected_events.append(event)
        #


def handler(name: str, type_, receives_multiple=False, info=None, function=None):
    if function:
        return Handler(name, type_, receives_multiple, info, function)
    else:

        def wrapper(func):
            return Handler(name, type_, receives_multiple, info, func)

        return wrapper


class Property:
    def __init__(self, type_, optional, default_value=None):
        self.declaration = nodetype.PropertyDeclaration(type_, optional, default_value)
        self.parent = None
        self.value = default_value

    @property
    def node_id(self):
        return self.parent.id


class Event:
    def __init__(self, name, type_, info=None):
        self.declaration: nodetype.EventDeclaration = nodetype.EventDeclaration(
            name, type_, info
        )
        self.parent: Node = None

    @property
    def node_id(self):
        return self.parent.id


class ExternalHandler:
    def __init__(self, name, type_, node_id):
        self.name = name
        self.type = type_
        self.node_id = node_id


class ExternalEvent(Event):
    def __init__(self, name, type_, node_id):
        super(ExternalEvent, self).__init__(name, type_)
        self.declaration = nodetype.EventDeclaration(name, type_)
        self.parent = None
        self._node_id = node_id

    @property
    def node_id(self):
        return self._node_id


class Message:
    def __init__(self, id_=None, value=None):
        self.id = id_
        self.value = value


class Node:
    def __init__(self, id_=None):
        self.stopped = False
        self.context = zmq.Context()
        # self.context.setsockopt(zmq.LINGER, 100)
        self.sub_socket = None
        self.pub_socket = None
        self.service_socket = None
        self.event2handler = {}
        self.port = ""
        self.handlers = {}
        self.events = {}
        self.properties = {}
        self.id = id_ if id_ is not None else str(uuid.uuid1())

        self.session = session.current_session

        self.session.add(self)
        self.pub_port = None
        self.service_port = None
        self.terminated = False

        self.events_list = queue.Queue()
        self.message_to_handlers = queue.Queue()

        self.events_processor = None
        self.events_from_server_processor = None
        self.run_processor = None
        self.__init_attrs()

    @property
    def name(self):
        return self.__class__.__name__

    @property
    def node_type(self):
        result = nodetype.NodeTypeDeclaration()
        result.name = self.name
        for _, item in self.handlers.items():
            result.handlers[item.declaration.uid] = item.declaration
        for _, item in self.properties.items():
            result.properties[item.declaration.uid] = item.declaration
        for _, item in self.events.items():
            result.events[item.declaration.uid] = item.declaration
        return result

    @property
    def pub_endpoint(self):
        return "tcp://127.0.0.1:{port}".format(port=self.pub_port)

    @property
    def service_endpoint(self):
        return "tcp://127.0.0.1:{port}".format(port=self.service_port)

    # def __setattr__(self, name, value):
    #     if isinstance(value, Property):
    #         value.parent = self
    #     if isinstance(value, Event):
    #         value.parent = self
    #         self.events[value.declaration.name] = value
    #     if isinstance(value, Handler):
    #         value.parent = self
    #         self.handlers[value.declaration.name] = value
    #     super().__setattr__(name, value)

    def __setattr__(self, key, value):
        try:
            attr = object.__getattribute__(self, key)
            if isinstance(attr, Property):
                attr.value = value
            #             attr.parent = self
            #             self.properties[key] = attr
            else:
                object.__setattr__(self, key, value)
        except AttributeError:
            object.__setattr__(self, key, value)

    # def __getattribute__(self, item):
    #     result = super().__getattribute__(item)
    #     if isinstance(result, Handler):
    #         self.handlers[result.declaration.name] = result
    #         result.parent = self
    #     if isinstance(result, Property):
    #         return result.value
    #
    #     return result
    """ *** magic *** """

    def __getattribute__(self, item):
        attr = object.__getattribute__(self, item)
        if isinstance(attr, Property):
            return attr.valuу
        return attr

    def __init_attrs(self):
        for attr_name in [attr for attr in dir(self) if attr[:2] != "__"]:
            attr = self.__getattribute__(attr_name)
            if isinstance(attr, Handler):
                attr.parent = self
                self.handlers[attr.declaration.name] = attr
            elif isinstance(attr, Event):
                attr.parent = self
                self.events[attr.declaration.name] = attr
            elif isinstance(attr, Property):
                attr.parent = self
                self.properties[attr_name] = attr
                attr.declaration.name = attr_name

    def set_server_endpoint(self, server_endpoint):
        self.port = server_endpoint

    def start(self):
        self.initialize_processor = threading.Thread(target=self.execute)
        self.initialize_processor.start()

    def initialize(self):
        pass

    def run(self):
        pass

    def stop(self):
        self.stopped = True

    def wait(self):
        for processor in [
            self.initialize_processor,
            self.events_processor,
            self.events_from_server_processor,
            self.run_processor,
        ]:
            if processor is not None:
                processor.join()

    def close_all_sockets(self):
        # TODO check destroy
        # for socket in [self.sub_socket, self.pub_socket, self.service_socket]:
        #     try:
        #         #socket.close(linger=100)
        #         socket.close()
        #
        #     except Exception as e:
        #         logging.warning(
        #             "Trying to close down socket: "
        #             "{} resulted in error: {}".format(socket, e)
        #         )
        self.context.destroy()

    def register_event(self, name):
        raise Exception("register_event")

    def register_handler(self, name, func):
        self.handlers[name] = func

    @property
    def server_endpoint(self):
        return "tcp://127.0.0.1:{port}".format(port=self.session.server_port)

    def message_id(self):
        sock = self.context.socket(zmq.REQ)
        sock.setsockopt(zmq.LINGER, 100)
        sock.connect(self.server_endpoint)
        sock.send(json.dumps({"command": "generate-next-message-index"}).encode("utf8"))
        msg = json.loads(sock.recv())
        # sock.close(linger=100)
        sock.close()
        return int(msg["index"])

    def fire(self, event, value, msg_id=None):
        try:
            event = event.declaration.name
            if event not in self.events.keys():
                logging.warning(
                    "Node {name}: Couldn't generate event. "
                    "Error: undefined event '{event}'".format(name=self.id, event=event)
                )
                return
            if msg_id is None:
                msg_id = self.message_id()
            self.events_list.put((event, value, msg_id))
            # msg = ProtoSerializer().serialize_message(msg_id, value)
            # prefix = "{id}|{event} ".format(id=self.id, event=event).encode("utf8")
            # logging.debug(
            #     "Node {name}: fire event {event}".format(
            #         name=self.id, event=str(prefix[:-1])
            #     )
            # )
            # self.pub_socket.send(prefix + msg.SerializeToString(), zmq.DONTWAIT)
        except Exception:
            logging.warning(
                "Node {name}:could not send message exception".format(name=self.id)
            )

    def terminate(self):
        if not self.terminated:
            logging.debug("Node terminated")
            # self.terminated = True
            sock = self.context.socket(zmq.REQ)
            sock.setsockopt(zmq.LINGER, 100)

            sock.connect(self.server_endpoint)
            sock.send(json.dumps({"command": "terminate"}).encode("utf8"))
            json.loads(sock.recv())
            # sock.close(linger=100)
            sock.close()

    def wait_answer_from_server(self):
        msg = self.service_socket.recv()

        config = json.loads(msg)
        self.service_socket.send(json.dumps({"success": True}).encode("utf8"))
        return config

    def initialize_listener(self, config):
        self.sub_socket = self.context.socket(zmq.SUB)

        self.sub_socket.setsockopt(zmq.LINGER, 100)
        input_node_ids = set()
        for handler in self.handlers.values():
            for event in handler.connected_events:
                input_node_ids.add(event.node_id)

        for input_node_id in input_node_ids:
            if input_node_id not in config:
                continue
            addr = config[input_node_id]["publisher_endpoint"]
            self.sub_socket.connect(addr)

            for handler in self.handlers.values():
                for event in handler.connected_events:
                    if event.node_id != input_node_id:
                        continue
                    self.event2handler[
                        _Event(event=event.declaration.name, source_id=event.node_id)
                    ] = handler.declaration.name
                    topic = "{source_id}|{event}".format(
                        source_id=event.node_id, event=event.declaration.name
                    )
                    self.sub_socket.set(zmq.SUBSCRIBE, topic.encode("utf8"))
                    logging.debug(
                        "Node {id} subscriber addr={addr}, topic={topic}".format(
                            id=self.id, addr=addr, topic=topic
                        )
                    )

    def send_command(self, request):
        sock = self.context.socket(zmq.REQ)
        sock.setsockopt(zmq.LINGER, 100)
        sock.connect(self.server_endpoint)
        sock.send(request.encode("utf8"))
        # sock.close(linger=100)
        sock.close()

    def process_events_from_server(self):
        while not self.stopped and not self.terminated:
            msg = self.service_socket.recv()
            json.loads(msg)
            self.service_socket.send(json.dumps({"success": True}).encode("utf8"))
            self.stopped = True
            # self.events_processor.join()
            self.close_all_sockets()
            self.run_processor.join()
            break
        logging.debug(
            "Node {name}:process_events_from_server finished".format(name=self.id)
        )

    def process_events(self):
        logging.debug("Node {name}:process_events started".format(name=self.id))
        if len(self.event2handler) == 0:
            logging.debug("Node {name}:process_events finished".format(name=self.id))
            return
        while not self.terminated:
            # logging.debug("Node {name}: stopped {stopped}"
            # .format(name=self.id, stopped=self.stopped))
            try:
                logging.debug(
                    "Node {name}: waiting for the next event...".format(name=self.id)
                )
                while not self.message_to_handlers.empty():
                    handler_name, message = self.message_to_handlers.get()
                    self.handlers[handler_name](message)
                # msg = self.sub_socket.recv()
                # logging.debug("Node {name}: received new event".format(name=self.id))
                # index = msg.find(b" ")
                # source_id, event = msg[:index].decode("utf8").split("|")
                # binary_msg = basictypes_pb2.Message()
                # binary_msg.ParseFromString(msg[index + 1:])
                #
                # msg_id, msg_value = ProtoSerializer().deserialize_message(binary_msg)
                # message = Message(msg_id, msg_value)
                # handler_name = self.event2handler[
                #     _Event(source_id=source_id, event=event)
                # ]  # noqa
                # logging.debug(
                #     "Node {name}: received event {event}".format(
                #         name=self.id, event=event
                #     )
                # )

            except Exception as e:
                logging.warning("Node {name}: Exception {e}".format(name=self.id, e=e))
                logging.warning(e.args)
                break

        logging.debug("Node {name}:process_events finished".format(name=self.id))

    def execute(self):
        # step0: publisher
        self.pub_socket = self.context.socket(zmq.PUB)
        self.pub_socket.setsockopt(zmq.LINGER, 100)
        self.pub_port = self.pub_socket.bind_to_random_port("tcp://127.0.0.1")
        logging.debug(
            "Node {id}. Publisher connected to port={port}".format(
                id=self.id, port=self.pub_port
            )
        )

        # step1: initialize node
        self.initialize()

        # step2: initialize service socket
        self.service_socket = self.context.socket(zmq.REP)
        self.service_socket.setsockopt(zmq.LINGER, 100)
        self.service_port = self.service_socket.bind_to_random_port("tcp://127.0.0.1")
        logging.debug(
            "Node {id}. Service connected to port={port}".format(
                id=self.id, port=self.service_port
            )
        )

        # step3: register socket on the server
        self.send_command(
            json.dumps(
                {
                    "command": "register",
                    "id": self.id,
                    "publisher_endpoint": "tcp://127.0.0.1:{port}".format(
                        port=self.pub_port
                    ),
                    "service_endpoint": "tcp://127.0.0.1:{port}".format(
                        port=self.service_port
                    ),
                },
                sort_keys=True,
            )
        )
        answer = self.wait_answer_from_server()

        self.initialize_listener(answer)
        self.send_command(json.dumps({"command": "ready-to-work", "id": self.id}))

        self.wait_answer_from_server()

        logging.debug("Node {id}. initialized".format(id=self.id))

        self.events_processor = threading.Thread(target=self.process_events)
        self.events_processor.start()

        # self.events_from_server_processor = threading.Thread(
        #     target=self.process_events_from_server
        # )
        # self.events_from_server_processor.start()

        self.run_processor = threading.Thread(target=self.run)
        self.run_processor.start()

        while not self.terminated:
            try:
                msg = self.service_socket.recv(zmq.NOBLOCK)
                json.loads(msg)
                self.service_socket.send(json.dumps({"success": True}).encode("utf8"))
                self.terminated = True
                self.close_all_sockets()
            except Exception:
                ...
            while True:
                try:
                    msg = self.sub_socket.recv(zmq.NOBLOCK)
                    logging.debug("Node {name}: received new event".format(name=self.id))
                    index = msg.find(b" ")
                    source_id, event = msg[:index].decode("utf8").split("|")
                    binary_msg = basictypes_pb2.Message()
                    binary_msg.ParseFromString(msg[index + 1 :])

                    msg_id, msg_value = ProtoSerializer().deserialize_message(binary_msg)
                    message = Message(msg_id, msg_value)
                    handler_name = self.event2handler[
                        _Event(source_id=source_id, event=event)
                    ]  # noqa
                    logging.debug(
                        "Node {name}: received event {event}".format(
                            name=self.id, event=event
                        )
                    )
                    self.message_to_handlers.put((handler_name, message))
                except Exception:
                    break
            while not self.events_list.empty():
                event, value, msg_id = self.events_list.get()
                msg = ProtoSerializer().serialize_message(msg_id, value)
                prefix = "{id}|{event} ".format(id=self.id, event=event).encode("utf8")
                logging.debug(
                    "Node {name}: fire event {event}".format(
                        name=self.id, event=str(prefix[:-1])
                    )
                )
                self.pub_socket.send(prefix + msg.SerializeToString(), zmq.DONTWAIT)

        logging.debug("Node {id}. Execution started".format(id=self.id))

    def __del__(self):
        if not self.context.closed:
            # self.context.destroy(linger=100)
            self.context.destroy()
        del self
