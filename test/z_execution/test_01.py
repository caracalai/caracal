import collections
import logging
import time
import unittest

import broutonblocks.declaration.datatypes as bbtypes
from broutonblocks.execution import Event, handler, Node, Session

item_count = 20
delay = 0.0


class GeneratorFirst(Node):
    value = Event("value", bbtypes.Int())

    def run(self):
        index = 0
        counter = 0
        while not self.stopped:
            time.sleep(delay)
            self.fire(self.value, index)
            index += 1
            counter += 1
            if counter == item_count:
                break


class GeneratorSecond(Node):
    value = Event("value", bbtypes.Int())

    def run(self):
        index = 0
        counter = 0
        while not self.stopped:
            time.sleep(delay)
            self.fire(self.value, index)
            index += 2
            counter += 1
            if counter == item_count:
                break


class Summator(Node):
    result = Event("result", bbtypes.Int())
    first_queue = collections.deque()
    second_queue = collections.deque()

    @handler("on_first", bbtypes.Int())
    def on_first(self, msg):
        self.first_queue.append(msg.value)
        self.process_queues()

    @handler("on_second", bbtypes.Int())
    def on_second(self, msg):
        self.second_queue.append(msg.value)
        self.process_queues()

    def process_queues(self):
        while len(self.first_queue) > 0 and len(self.second_queue) > 0:
            first = self.first_queue[0]
            self.first_queue.popleft()

            second = self.second_queue[0]
            self.second_queue.popleft()
            self.fire(self.result, first + second)


class TestNode(Node):
    result = []

    @handler("receive_result", bbtypes.Int())
    def receive_result(self, msg):
        self.result.append(msg.value)
        if len(self.result) == item_count:
            self.terminate()


class CheckGraphExecution_01(unittest.TestCase):
    def setUp(self) -> None:
        with Session() as session:
            logging.basicConfig(level=logging.DEBUG)

            self.generator_first = GeneratorFirst()
            self.generator_second = GeneratorSecond()
            self.summator = Summator()
            self.test_node = TestNode()

            self.summator.on_first.connect(self.generator_first.value)
            self.summator.on_second.connect(self.generator_second.value)
            self.test_node.receive_result.connect(self.summator.result)
            session.run()

    def test(self):
        self.assertEqual(
            [
                0,
                3,
                6,
                9,
                12,
                15,
                18,
                21,
                24,
                27,
                30,
                33,
                36,
                39,
                42,
                45,
                48,
                51,
                54,
                57,
            ],
            self.test_node.result,
        )

    def tearDown(self) -> None:
        del self.generator_first
        del self.generator_second
        del self.summator
        del self.test_node
        del self
