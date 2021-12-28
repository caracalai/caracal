import logging
import multiprocessing
import unittest

from caracal import caratypes, Event, ExternalEvent, handler, Node, Property, Session


class TicksGen(Node):
    tick = Event("tick", caratypes.Tuple(caratypes.Int()))

    def run(self):
        for i in range(1, 5):
            self.fire(self.tick, i)


class DoSmth(Node):
    output = Event("output", caratypes.Tuple(caratypes.Int()))

    @handler("input_numbers", caratypes.Tuple(caratypes.Int()))
    def input_numbers(self, msg):
        self.fire(self.output, msg.value, msg.id)


class DoSmthWithErr(Node):
    output = Event("output", caratypes.Tuple(caratypes.Int()))

    @handler("input_numbers", caratypes.Tuple(caratypes.Int()))
    def input_numbers(self, msg):
        if msg.value not in [2, 3]:
            self.fire(self.output, msg.value, msg.id)


class Summat(Node):
    result = Property(
        caratypes.Int(),
        default_value=0,
    )

    @handler("input_numbers", caratypes.Tuple(caratypes.Object()), True)
    def input_numbers(self, msgs):
        logging.critical(f"{self.__class__.__name__} received")
        self.result += sum((msg.value for msg in msgs.value))
        if self.result == 15:
            logging.critical(self.result)
            self.terminate()


port = 2001


def first_worker():
    with Session(
        name="first", server_port=port, external_nodes=["Summator", "action3"]
    ) as session:
        # logging.basicConfig(level=logging.WARNING)
        gen = TicksGen(id_="Gen")
        action1 = DoSmth(id_="action1")
        action2 = DoSmthWithErr(id_="action2")

        action1.input_numbers.connect(gen.tick)
        action2.input_numbers.connect(gen.tick)

        session.run()


def second_worker(return_dict):
    with Session(name="second", server_port=2001, serves_server=False) as session:
        # logging.basicConfig(level=logging.DEBUG)
        action3 = DoSmthWithErr(id_="action3")
        summat = Summat(id_="Summator")

        gen_evt = ExternalEvent("tick", caratypes.Tuple(caratypes.Int()), node_id="Gen")
        act1_evt = ExternalEvent(
            "output", caratypes.Tuple(caratypes.Int()), node_id="action1"
        )
        act2_evt = ExternalEvent(
            "output", caratypes.Tuple(caratypes.Int()), node_id="action2"
        )

        action3.input_numbers.connect(gen_evt)
        summat.input_numbers.connect(act1_evt, act2_evt, action3.output)

        session.run()

    return_dict["result"] = summat.result


class MultipleHandlers(unittest.TestCase):
    def test_multihandler_without_evt_id(self):
        manager = multiprocessing.Manager()
        return_dict = manager.dict()
        worker1 = multiprocessing.Process(target=first_worker)
        worker1.start()

        worker2 = multiprocessing.Process(target=second_worker, args=(return_dict,))
        worker2.start()

        worker1.join()
        worker2.join()
