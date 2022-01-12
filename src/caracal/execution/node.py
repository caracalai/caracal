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
            if isinstance(event, Event) or isinstance(event, ExternalEvent):
                handler_data_type = self.declaration.data_type
                event_data_type = event.declaration.data_type

                handler_data_type = (
                    handler_data_type
                    if not isinstance(handler_data_type, cara_types.Tuple)
                    else cara_types.Tuple(handler_data_type)
                )

                event_data_type = (
                    event_data_type
                    if not isinstance(event_data_type, cara_types.Tuple)
                    else cara_types.Tuple(event_data_type)
                )

                if event_data_type.intersect(handler_data_type) is None:
                    raise TypeError
                self.connected_events.add(event)
            else:
                raise TypeError


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
        self.__context__ = zmq.Context()
        self.__sub_socket__ = None
        self.__pub_socket__ = None
        self.__service_socket__ = None
        self.__event2handler__ = []
        self.__port__ = ""
        self.handlers = {}
        self.events = {}
        self.properties = {}
        self.id = id_ if id_ is not None else str(uuid.uuid1())

        self.session = session.current_session
        self.session.add(self)

        self.__pub_port__ = None
        self.__service_port__ = None
        self.__terminated__ = False

        self.__events_list__ = queue.Queue()
        self.__message_to_handlers__ = queue.Queue()

        self.__events_processor__ = None
        self.__events_from_server_processor__ = None
        self.__run_processor__ = None
        self.__node_type__ = Node.get_declaration(self.__class__)
        self.__init_attrs__()

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
    def __pub_endpoint__(self):
        return "tcp://127.0.0.1:{port}".format(port=self.__pub_port__)

    @property
    def __service_endpoint__(self):
        return "tcp://127.0.0.1:{port}".format(port=self.__service_port__)

    def __setattr__(self, key, value):
        if key in self.__class__.__dict__ and isinstance(
            self.__class__.__dict__[key], Property
        ):
            self.properties[key] = copy.copy(self.__class__.__dict__[key])
            self.__dict__[key] = value
            self.properties[key].value = value
        else:
            object.__setattr__(self, key, value)

    def __init_attrs__(self):
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

    def __set_server_endpoint__(self, server_endpoint):
        self.__port__ = server_endpoint

    def __start__(self):
        self.__initialize_processor__ = threading.Thread(target=self.__execute__)
        self.__initialize_processor__.start()

    def initialize(self):
        pass

    def run(self):
        pass

    def stop(self):
        self.stopped = True

    def __wait__(self):
        for processor in [
            self.__initialize_processor__,
            self.__events_processor__,
            self.__events_from_server_processor__,
            self.__run_processor__,
        ]:
            if processor is not None:
                processor.join()

    def __close_all_sockets__(self):
        self.__context__.destroy()

    @property
    def __server_endpoint__(self):
        return "tcp://127.0.0.1:{port}".format(port=self.session.server_port)

    def __message_id__(self):
        sock = self.__context__.socket(zmq.REQ)
        sock.connect(self.__server_endpoint__)
        sock.send(json.dumps({"command": "generate-next-message-index"}).encode("utf8"))
        msg = json.loads(sock.recv())
        sock.close()
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
                msg_id = self.__message_id__()
            self.__events_list__.put((event, value, msg_id))
        except Exception as e:
            logging.warning(
                "Node {type}_{id}:could not send message \n{e}".format(
                    type=type(self), id=self.id, e=e
                )
            )

    def terminate(self):
        if not self.__terminated__:
            logging.debug("Node terminated")
            sock = self.__context__.socket(zmq.REQ)

            sock.connect(self.__server_endpoint__)
            sock.send(json.dumps({"command": "terminate"}).encode("utf8"))
            json.loads(sock.recv())
            sock.close()

    def __wait_answer_from_server__(self):
        msg = self.__service_socket__.recv()

        config = json.loads(msg)
        self.__service_socket__.send(json.dumps({"success": True}).encode("utf8"))
        return config

    def __initialize_listener__(self, config):
        self.__sub_socket__ = self.__context__.socket(zmq.SUB)

        input_node_ids = set()
        for handler_val in self.handlers.values():
            for event in handler_val.connected_events:
                input_node_ids.add(event.node_id)

        for input_node_id in input_node_ids:
            if input_node_id not in config:
                continue
            addr = config[input_node_id]["publisher_endpoint"]
            self.__sub_socket__.connect(addr)

            for handler_val in self.handlers.values():
                for event in handler_val.connected_events:
                    if event.node_id != input_node_id:
                        continue
                    self.__event2handler__.append(
                        (
                            _Event(event=event.declaration.name, source_id=event.node_id),
                            handler_val.declaration.name,
                        )
                    )
                    topic = "{source_id}|{event}".format(
                        source_id=event.node_id, event=event.declaration.name
                    )
                    self.__sub_socket__.set(zmq.SUBSCRIBE, topic.encode("utf8"))
                    logging.debug(
                        "Node {id} subscriber addr={addr}, topic={topic}".format(
                            id=self.id, addr=addr, topic=topic
                        )
                    )

    def __send_command__(self, request):
        sock = self.__context__.socket(zmq.REQ)
        sock.connect(self.__server_endpoint__)
        sock.send(request.encode("utf8"))
        sock.close()

    def __process_events_from_server__(self):
        while not self.stopped and not self.__terminated__:
            msg = self.__service_socket__.recv()
            json.loads(msg)
            self.__service_socket__.send(json.dumps({"success": True}).encode("utf8"))
            self.stopped = True
            self.__close_all_sockets__()
            self.__run_processor__.join()
            break
        logging.debug(
            "Node {type}_{id}:process_events_from_server finished".format(
                type=type(self), id=self.id
            )
        )

    def __process_events__(self):
        logging.debug(
            "Node {type}_{id}:process_events started".format(type=type(self), id=self.id)
        )
        if len(self.__event2handler__) == 0:
            logging.debug(
                "Node {type}_{id}:process_events finished".format(
                    type=type(self), id=self.id
                )
            )
            return
        while not self.__terminated__:
            try:
                logging.debug(
                    "Node {type}_{id}: waiting for the next event...".format(
                        type=type(self), id=self.id
                    )
                )
                while not self.__message_to_handlers__.empty():
                    handler_name, message = self.__message_to_handlers__.get()
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

    def __initialize_sockets__(self):
        # step1: initialize publisher socket
        self.__pub_socket__ = self.__context__.socket(zmq.PUB)
        self.__pub_port__ = self.__pub_socket__.bind_to_random_port("tcp://127.0.0.1")
        logging.debug(
            "Node {type}_{id}. Publisher connected to port={port}".format(
                type=type(self), id=self.id, port=self.__pub_port__
            )
        )

        # step2: initialize service socket
        self.__service_socket__ = self.__context__.socket(zmq.REP)
        self.__service_port__ = self.__service_socket__.bind_to_random_port(
            "tcp://127.0.0.1"
        )
        logging.debug(
            "Node {type}_{id}. Service connected to port={port}".format(
                type=type(self), id=self.id, port=self.__service_port__
            )
        )

    def __register_socket__(self):
        self.__send_command__(
            json.dumps(
                {
                    "command": "register",
                    "id": self.id,
                    "publisher_endpoint": "tcp://127.0.0.1:{port}".format(
                        port=self.__pub_port__
                    ),
                    "service_endpoint": "tcp://127.0.0.1:{port}".format(
                        port=self.__service_port__
                    ),
                },
                sort_keys=True,
            )
        )

    def __execute__(self):
        # step1: initialize service socket
        self.__initialize_sockets__()

        # step2: initialize node
        self.initialize()

        # step3: register socket on the server
        self.__register_socket__()
        answer = self.__wait_answer_from_server__()

        # step4: initialize listener
        self.__initialize_listener__(answer)
        self.__send_command__(json.dumps({"command": "ready-to-work", "id": self.id}))

        self.__wait_answer_from_server__()

        logging.debug("Node {type}_{id}. initialized".format(type=type(self), id=self.id))

        self.__events_processor__ = threading.Thread(target=self.__process_events__)
        self.__events_processor__.start()

        self.__run_processor__ = threading.Thread(target=self.run)
        self.__run_processor__.start()

        while not self.__terminated__:
            try:
                msg = self.__service_socket__.recv(zmq.NOBLOCK)
                json.loads(msg)
                self.__service_socket__.send(json.dumps({"success": True}).encode("utf8"))
                self.__terminated__ = True
                self.__close_all_sockets__()
            except Exception:
                ...
            while True:
                try:
                    msg = self.__sub_socket__.recv(zmq.NOBLOCK)
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
                        for event_name, hand_name in self.__event2handler__
                        if _Event(source_id=source_id, event=event) == event_name
                    ]
                    logging.debug(
                        "Node {type}_{id}: received event {event}".format(
                            type=type(self), id=self.id, event=event
                        )
                    )
                    for hand_name in handler_names:
                        self.__message_to_handlers__.put((hand_name, message))
                except Exception:
                    break
            while not self.__events_list__.empty():
                event, value, msg_id = self.__events_list__.get()
                msg = proto_serializer.ProtoSerializer().serialize_message(msg_id, value)
                prefix = "{id}|{event} ".format(id=self.id, event=event).encode("utf8")
                logging.debug(
                    "Node {type}_{id}: fire event {event}".format(
                        type=type(self), id=self.id, event=str(prefix[:-1])
                    )
                )
                self.__pub_socket__.send(prefix + msg.SerializeToString(), zmq.DONTWAIT)

        logging.debug(
            "Node {type}_{id}. Execution started".format(type=type(self), id=self.id)
        )

    def __del__(self):
        if not self.__context__.closed:
            self.__context__.destroy()
        del self
