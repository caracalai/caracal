import broutonblocks.declaration.datatypes as bbtypes
from broutonblocks.execution import *
import unittest, time, collections, logging

item_count = 20
delay = 0.0

class GeneratorFirst(Node):
    def __init__(self, id=None):
        super().__init__(id)
        self.value = Event("value", bbtypes.Int())

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
    def __init__(self, id=None):
        super().__init__(id)
        self.value = Event("value", bbtypes.Int())

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
    def __init__(self, id=None):
        super().__init__(id)
        self.result = Event("result", bbtypes.Int())
        self.first_queue = collections.deque()
        self.second_queue = collections.deque()

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
    def __init__(self):
        super(TestNode, self).__init__()
        self.result = []

    @handler("receive_result", bbtypes.Int())
    def receive_result(self, msg):
        self.result.append(msg.value)
        if len(self.result) == item_count:
            self.terminate()


class CheckGraphExecution_01(unittest.TestCase):
    def test(self):
        with Session() as session:
            logging.basicConfig(level=logging.CRITICAL)

            generator_first = GeneratorFirst()
            generator_second = GeneratorSecond()
            summator = Summator()
            test_node = TestNode()

            summator.on_first.connect(generator_first.value)
            summator.on_second.connect(generator_second.value)
            test_node.receive_result.connect(summator.result)
            session.run()


            self.assertEqual([0, 3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36, 39, 42, 45, 48, 51, 54, 57],
                             test_node.result)