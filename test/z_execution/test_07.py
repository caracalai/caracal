import logging
import unittest

from caracal.declaration import MetaInfo
import caracal.declaration.datatypes as caratypes
from caracal.execution import Event, handler, Node, Property, Session


class Generator1(Node):
    threshold = Property(caratypes.Int(), default_value=5)
    value = Event("value", caratypes.Int())

    def run(self):
        self.fire(self.value, self.threshold)


class Generator2(Node):
    threshold = Property(caratypes.Int(), default_value=2)
    value = Event("value", caratypes.Int())

    def run(self):
        self.fire(self.value, self.threshold)


class Summat(Node):
    result = Event("result", caratypes.Int())

    summa = 0

    a_queue = []
    b_queue = []

    @handler("a", caratypes.Int(), False, MetaInfo())
    def a(self, msg):
        self.a_queue.append(msg.value)
        self.run()

    @handler("b", caratypes.Int(), False, MetaInfo())
    def b(self, msg):
        self.b_queue.append(msg.value)
        self.run()

    def run(self):
        if bool(self.a_queue) and bool(self.b_queue):
            a, *self.a_queue = self.a_queue
            b, *self.b_queue = self.b_queue
            self.summa = a + b
            logging.warning(f"a + b = {a} + {b} = { self.summa }")
            self.terminate()


class TestDownloadedProject(unittest.TestCase):
    def __init__(self, methodName="runTest"):
        super(TestDownloadedProject, self).__init__(methodName)

    def test_case(self):
        with Session() as session:
            # logging.basicConfig(level=logging.DEBUG)

            generator_first = Generator1()
            generator_second = Generator1()
            generator_second.threshold = 2
            summat = Summat()

            summat.a.connect(generator_second.value)
            summat.b.connect(generator_first.value)
            session.run()

            self.assertEqual(summat.summa, 7)
