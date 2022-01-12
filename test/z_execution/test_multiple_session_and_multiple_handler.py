import logging
import multiprocessing
import unittest

from caracal import cara_types, Event, ExternalEvent, handler, Node, Property, Session


class TicksGen(Node):
    tick = Event("tick", cara_types.Tuple(cara_types.Int()))

    def run(self):
        for i in range(1, 5):
            self.fire(self.tick, i)


class DoSmth(Node):
    output = Event("output", cara_types.Tuple(cara_types.Int()))

    @handler("input_numbers", cara_types.Tuple(cara_types.Int()))
    def input_numbers(self, msg):
        self.fire(self.output, msg.value, msg.id)


class DoSmthWithErr(Node):
    output = Event("output", cara_types.Tuple(cara_types.Int()))

    @handler("input_numbers", cara_types.Tuple(cara_types.Int()))
    def input_numbers(self, msg):
        if msg.value not in [2, 3]:
            self.fire(self.output, msg.value, msg.id)


class Summat(Node):
    result = Property(
        cara_types.Int(),
        default_value=0,
    )

    @handler("input_numbers", cara_types.Tuple(cara_types.Object()), True)
    def input_numbers(self, msgs):
        print(f"{self.__class__.__name__} received")
        self.result += sum((msg.value for msg in msgs.value))
        if self.result == 15:
            print(self.result)
            self.terminate()


port = 2001


def first_worker():
    with Session(
        name="first", server_port=port, external_nodes=["Summator", "action3"]
    ) as session:
        gen = TicksGen(id_="Gen")
        action1 = DoSmth(id_="action1")
        action2 = DoSmthWithErr(id_="action2")

        action1.input_numbers.connect(gen.tick)
        action2.input_numbers.connect(gen.tick)

        session.run()


def second_worker(return_dict):
    with Session(name="second", server_port=2001, serves_server=False) as session:
        action3 = DoSmthWithErr(id_="action3")
        summat = Summat(id_="Summator")

        gen_evt = ExternalEvent("tick", cara_types.Tuple(cara_types.Int()), node_id="Gen")
        act1_evt = ExternalEvent(
            "output", cara_types.Tuple(cara_types.Int()), node_id="action1"
        )
        act2_evt = ExternalEvent(
            "output", cara_types.Tuple(cara_types.Int()), node_id="action2"
        )

        action3.input_numbers.connect(gen_evt)
        summat.input_numbers.connect(act1_evt, act2_evt, action3.output)

        session.run()

    return_dict["result"] = summat.result


class MultipleHandlers(unittest.TestCase):
    def test_multiple_handler_without_evt_id(self):
        # logging.basicConfig(level=logging.DEBUG)
        manager = multiprocessing.Manager()
        return_dict = manager.dict()
        worker1 = multiprocessing.Process(target=first_worker)
        worker1.start()

        worker2 = multiprocessing.Process(target=second_worker, args=(return_dict,))
        worker2.start()

        worker1.join()
        worker2.join()

        self.assertEqual(return_dict["result"], 15)
