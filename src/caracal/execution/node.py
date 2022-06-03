import collections
import copy
import json
import logging
import queue
import threading
import typing
import uuid

import caracal.declaration.datatypes as cara_types
import caracal.declaration.nodetype as node_type
import caracal.execution.session as session
import caracal.proto.basictypes_pb2 as basic_types_pb2
import caracal.proto.protoserializer as proto_serializer
import zmq

_Event = collections.namedtuple("_Event", ["source_id", "event"])
_Parent = collections.namedtuple("_Parent", ["uid"])


class Handler:
    def __init__(
        self,
        name: str,
        data_type: typing.List[cara_types.Object],
        receives_multiple: bool,
        info: typing.Union[node_type.MetaInfo, None],
        function: typing.Callable,
    ):
        self.declaration = node_type.HandlerDeclaration(
            name, data_type, receives_multiple, info
        )
        self.function = function
        self.connected_events = set()
        self.parent = None
        self.events_queues = collections.OrderedDict()

    def __call__(self, msg):
        if self.declaration.receives_multiple:
            if not self.events_queues:
                for event in self.connected_events:
                    self.events_queues[
                        _Event(source_id=event.node_id, event=event.declaration.name)
                    ] = collections.deque()

            self.events_queues[_Event(source_id=msg.source_uid, event=msg.event)].append(
                msg
            )

            while all(self.events_queues.values()):
                msgs = [elem.popleft() for elem in self.events_queues.values()]
                ids = [msg.id for msg in msgs]
                if len(set(ids)) == 1:
                    self.function(self.parent, Message(id_=set(ids), value=msgs))
                else:
                    for msg in [msg for msg in msgs if msg.id == max(ids)]:
                        self.events_queues[
                            _Event(source_id=msg.source_uid, event=msg.event)
                        ].appendleft(msg)
        else:
            self.function(self.parent, msg)

    def connect(self, *events):
        for event in events:
            if event.declaration.data_type.intersect(self.declaration.data_type) is None:
                raise TypeError
            self.connected_events.add(event)


def handler(
    name: str,
    data_type,
    receives_multiple: bool = False,
    info: node_type.MetaInfo = None,
    function: typing.Callable = None,
):
    if function:
        return Handler(name, data_type, receives_multiple, info, function)
    else:

        def wrapper(func):
            return Handler(name, data_type, receives_multiple, info, func)

        return wrapper


class Property:
    def __init__(self, data_type, default_value=None):
        self.declaration = node_type.PropertyDeclaration(data_type, None, default_value)
        self.parent = None
        self.value = default_value

    @property
    def node_id(self):
        return self.parent.id


class Event:
    def __init__(self, name, data_type, info=None):
        self.declaration: node_type.EventDeclaration = node_type.EventDeclaration(
            name, data_type, info
        )
        self.parent: typing.Union[Node, None] = None

    @property
    def node_id(self):
        return self.parent.id


class ExternalHandler:
    def __init__(self, name, data_type, node_id):
        self.name = name
        self.data_type = data_type
        self.node_id = node_id


class ExternalEvent(Event):
    def __init__(self, name, data_type, node_id):
        super(ExternalEvent, self).__init__(name, data_type)
        self.declaration = node_type.EventDeclaration(name, data_type)
        self.parent = _Parent(uid=node_id)

    @property
    def node_id(self):
        return self.parent.uid


class Message:
    def __init__(self, id_=None, source_uid=None, event=None, value=None):
        self.id = id_
        self.source_uid = source_uid
        self.event = event
        self.value = value


class Node:
    def __init__(self, id_=None):
        self.stopped = False
        self._context = zmq.Context()
        self._sub_socket = None
        self._pub_socket = None
        self._service_socket = None
        self._message_id_socket = None
        self._event2handler = []
        self._port = ""
        self.handlers = {}
        self.events = {}
        self.properties = {}
        self.id = id_ if id_ is not None else str(uuid.uuid4())

        self.session = session.current_session
        self.session.add(self)

        self._pub_port = None
        self._service_port = None
        self._terminated = False

        self._events_list = queue.Queue()
        self._message_to_handlers = queue.Queue()

        self._events_processor = None
        self._events_from_server_processor = None
        self._run_processor = None
        self._node_type = Node.get_declaration(self.__class__)
        self._init_attrs()

    @property
    def name(self):
        return self.__class__.__name__

    @staticmethod
    def get_declaration(node):
        result = node_type.NodeTypeDeclaration()
        result.name = node.__name__
        items = [
            it
            for it in node.__dict__.keys()
            if not it.startswith("__") and not callable(it)
        ]
        for item in items:
            if isinstance(node.__dict__[item], Handler):
                result.handlers[node.__dict__[item].declaration.name] = node.__dict__[
                    item
                ].declaration
            if isinstance(node.__dict__[item], Property):
                result.properties[node.__dict__[item].declaration.uid] = node.__dict__[
                    item
                ].declaration
                result.properties[node.__dict__[item].declaration.uid].name = item
            if isinstance(node.__dict__[item], Event):
                result.events[node.__dict__[item].declaration.uid] = node.__dict__[
                    item
                ].declaration
        return result

    @property
    def _pub_endpoint(self):
        return "tcp://127.0.0.1:{port}".format(port=self._pub_port)

    @property
    def _service_endpoint(self):
        return "tcp://127.0.0.1:{port}".format(port=self._service_port)

    def __setattr__(self, key, value):
        if key in self.__class__.__dict__ and isinstance(
            self.__class__.__dict__[key], Property
        ):
            self.properties[key] = copy.copy(self.__class__.__dict__[key])
            self.__dict__[key] = value
            self.properties[key].value = value
        else:
            object.__setattr__(self, key, value)

    def _init_attrs(self):
        for attr_name in [attr for attr in dir(self) if attr[:2] != "__"]:
            attr = self.__getattribute__(attr_name)
            if isinstance(attr, Handler):
                attr.parent = self
                self.handlers[attr.declaration.name] = copy.copy(attr)
                self.__dict__[attr_name] = self.handlers[attr.declaration.name]
            elif isinstance(attr, Event):
                attr.parent = self
                self.events[attr.declaration.name] = copy.copy(attr)
                self.__dict__[attr_name] = self.events[attr.declaration.name]
            elif attr_name in self.__class__.__dict__ and isinstance(
                self.__class__.__dict__[attr_name], Property
            ):
                self.properties[attr_name] = copy.copy(self.__class__.__dict__[attr_name])
                self.properties[attr_name].parent = self
                self.properties[attr_name].declaration.name = attr_name
                self.__dict__[attr_name] = self.properties[attr_name].value

    def _set_server_endpoint(self, server_endpoint):
        self._port = server_endpoint

    def _start(self):
        self.__initialize_processor = threading.Thread(target=self._execute)
        self.__initialize_processor.start()

    def initialize(self):
        pass

    def run(self):
        pass

    def finish(self):
        pass

    def stop(self):
        self.stopped = True

    def _wait(self):
        for processor in [
            self.__initialize_processor,
            self._events_processor,
            self._events_from_server_processor,
            self._run_processor,
        ]:
            if processor is not None:
                processor.join()

    def _close_all_sockets(self):
        self._context.destroy()

    @property
    def _server_endpoint(self):
        return "tcp://127.0.0.1:{port}".format(port=self.session.server_port)

    def _message_id(self):
        self._message_id_socket.connect(self._server_endpoint)
        self._message_id_socket.send(
            json.dumps({"command": "generate-next-message-index"}).encode("utf8")
        )
        msg = json.loads(self._message_id_socket.recv())
        return int(msg["index"])

    def fire(self, event, value, msg_id=None):
        try:
            event = event.declaration.name
            if event not in self.events.keys():
                logging.warning(
                    "Node {type}_{id}: Couldn't generate event. "
                    "Error: undefined event '{event}'".format(
                        type=type(self), id=self.id, event=event
                    )
                )
                return
            if msg_id is None:
                msg_id = self._message_id()
            self._events_list.put((event, value, msg_id))
        except Exception as e:
            logging.warning(
                "Node {type}_{id}:could not send message \n{e}".format(
                    type=type(self), id=self.id, e=e
                )
            )

    def terminate(self):
        if not self._terminated:
            logging.debug("Node terminated")
            sock = self._context.socket(zmq.REQ)

            sock.connect(self._server_endpoint)
            sock.send(json.dumps({"command": "terminate"}).encode("utf8"))
            json.loads(sock.recv())
            sock.close()

    def _wait_answer_from_server(self):
        msg = self._service_socket.recv()

        config = json.loads(msg)
        self._service_socket.send(json.dumps({"success": True}).encode("utf8"))
        return config

    def _initialize_listener(self, config):
        self._sub_socket = self._context.socket(zmq.SUB)

        input_node_ids = set()
        for handler_val in self.handlers.values():
            for event in handler_val.connected_events:
                input_node_ids.add(event.node_id)

        for input_node_id in input_node_ids:
            if input_node_id not in config:
                continue
            addr = config[input_node_id]["publisher_endpoint"]
            self._sub_socket.connect(addr)

            for handler_val in self.handlers.values():
                for event in handler_val.connected_events:
                    if event.node_id != input_node_id:
                        continue
                    self._event2handler.append(
                        (
                            _Event(event=event.declaration.name, source_id=event.node_id),
                            handler_val.declaration.name,
                        )
                    )
                    topic = "{source_id}|{event}".format(
                        source_id=event.node_id, event=event.declaration.name
                    )
                    self._sub_socket.set(zmq.SUBSCRIBE, topic.encode("utf8"))
                    logging.debug(
                        "Node {id} subscriber addr={addr}, topic={topic}".format(
                            id=self.id, addr=addr, topic=topic
                        )
                    )

    def _send_command(self, request):
        sock = self._context.socket(zmq.REQ)
        sock.connect(self._server_endpoint)
        sock.send(request.encode("utf8"))
        sock.close()

    def _process_events_from_server(self):
        while not self.stopped and not self._terminated:
            msg = self._service_socket.recv()
            json.loads(msg)
            self._service_socket.send(json.dumps({"success": True}).encode("utf8"))
            self.stopped = True
            self._close_all_sockets()
            self._run_processor.join()
            break
        logging.debug(
            "Node {type}_{id}:process_events_from_server finished".format(
                type=type(self), id=self.id
            )
        )

    def _process_events(self):
        logging.debug(
            "Node {type}_{id}:process_events started".format(type=type(self), id=self.id)
        )
        if len(self._event2handler) == 0:
            logging.debug(
                "Node {type}_{id}:process_events finished".format(
                    type=type(self), id=self.id
                )
            )
            return
        while not self._terminated:
            try:
                logging.debug(
                    "Node {type}_{id}: waiting for the next event...".format(
                        type=type(self), id=self.id
                    )
                )
                while not self._message_to_handlers.empty():
                    handler_name, message = self._message_to_handlers.get()
                    self.handlers[handler_name](message)

            except Exception as e:
                logging.warning(
                    "Node {type}_{id}: Exception {e}".format(
                        type=type(self), id=self.id, e=e
                    )
                )
                logging.warning(e.args)
                break

        logging.debug(
            "Node {type}_{id}:process_events finished".format(type=type(self), id=self.id)
        )

    def _initialize_sockets(self):
        # step0: initialize message_id socket
        self._message_id_socket = self._context.socket(zmq.REQ)

        # step1: initialize publisher socket
        self._pub_socket = self._context.socket(zmq.PUB)
        self._pub_port = self._pub_socket.bind_to_random_port("tcp://127.0.0.1")
        logging.debug(
            "Node {type}_{id}. Publisher connected to port={port}".format(
                type=type(self), id=self.id, port=self._pub_port
            )
        )

        # step2: initialize service socket
        self._service_socket = self._context.socket(zmq.REP)
        self._service_port = self._service_socket.bind_to_random_port("tcp://127.0.0.1")
        logging.debug(
            "Node {type}_{id}. Service connected to port={port}".format(
                type=type(self), id=self.id, port=self._service_port
            )
        )

    def _register_socket(self):
        self._send_command(
            json.dumps(
                {
                    "command": "register",
                    "id": self.id,
                    "publisher_endpoint": "tcp://127.0.0.1:{port}".format(
                        port=self._pub_port
                    ),
                    "service_endpoint": "tcp://127.0.0.1:{port}".format(
                        port=self._service_port
                    ),
                },
                sort_keys=True,
            )
        )

    def _check_properties(self):
        for prop in [
            prop
            for prop in self.properties.values()
            if prop.declaration.default_value is None
        ]:
            if prop.value is None:
                raise Exception(
                    f'{self.__class__} property "{prop.declaration.name}" \
is not set to a value'
                )

    def _execute(self):
        # step0: check properties
        self._check_properties()

        # step1: initialize service socket
        self._initialize_sockets()

        # step2: initialize node
        self.initialize()

        # step3: register socket on the server
        self._register_socket()
        answer = self._wait_answer_from_server()

        # step4: initialize listener
        self._initialize_listener(answer)
        self._send_command(json.dumps({"command": "ready-to-work", "id": self.id}))

        self._wait_answer_from_server()

        logging.debug("Node {type}_{id}. initialized".format(type=type(self), id=self.id))

        self._events_processor = threading.Thread(target=self._process_events)
        self._events_processor.start()

        self._run_processor = threading.Thread(target=self.run)
        self._run_processor.start()

        while not self._terminated:
            try:
                msg = self._service_socket.recv(zmq.NOBLOCK)
                json.loads(msg)
                self._service_socket.send(json.dumps({"success": True}).encode("utf8"))
                self._terminated = True
                self._close_all_sockets()
            except Exception:
                ...
            while True:
                try:
                    msg = self._sub_socket.recv(zmq.NOBLOCK)
                    logging.debug(
                        "Node {type}_{id}: received new event".format(
                            type=type(self), id=self.id
                        )
                    )
                    index = msg.find(b" ")
                    source_id, event = msg[:index].decode("utf8").split("|")
                    binary_msg = basic_types_pb2.Message()
                    binary_msg.ParseFromString(msg[index + 1 :])

                    (
                        msg_id,
                        msg_value,
                    ) = proto_serializer.ProtoSerializer().deserialize_message(binary_msg)
                    message = Message(msg_id, source_id, event, msg_value)
                    handler_names = [
                        hand_name
                        for event_name, hand_name in self._event2handler
                        if _Event(source_id=source_id, event=event) == event_name
                    ]
                    logging.debug(
                        "Node {type}_{id}: received event {event}".format(
                            type=type(self), id=self.id, event=event
                        )
                    )
                    for hand_name in handler_names:
                        self._message_to_handlers.put((hand_name, message))
                except Exception:
                    break
            while not self._events_list.empty():
                event, value, msg_id = self._events_list.get()
                msg = proto_serializer.ProtoSerializer().serialize_message(msg_id, value)
                prefix = "{id}|{event} ".format(id=self.id, event=event).encode("utf8")
                logging.debug(
                    "Node {type}_{id}: fire event {event}".format(
                        type=type(self), id=self.id, event=str(prefix[:-1])
                    )
                )
                self._pub_socket.send(prefix + msg.SerializeToString(), zmq.DONTWAIT)
        else:
            self.finish()
        logging.debug(
            "Node {type}_{id}. Execution started".format(type=type(self), id=self.id)
        )

    def __del__(self):
        if not self._context.closed:
            self._context.destroy()
        del self
