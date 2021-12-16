import unittest

from caracal.declaration import datatypes
from caracal.execution import Node, Event, handler, Session

result = 0


class TicksGen(Node):
    tick = Event("tick", datatypes.Tuple(datatypes.Int()))

    def run(self):
        for i in range(1, 5):
            self.fire(self.tick, i)


class DoSmth(Node):
    output = Event("output", datatypes.Tuple(datatypes.Int()))

    @handler("input", datatypes.Tuple(datatypes.Int()))
    def input(self, msg):
        self.fire(self.output, msg.value, msg.id)


class DoSmth1(Node):
    output = Event("output", datatypes.Tuple(datatypes.Int()))

    @handler("input", datatypes.Tuple(datatypes.Int()))
    def input(self, msg):
        self.fire(self.output, msg.value, msg.id)


class DoSmthWithErr(Node):
    output = Event("output", datatypes.Tuple(datatypes.Int()))

    @handler("input", datatypes.Tuple(datatypes.Int()))
    def input(self, msg):
        if msg.value not in [2, 3]:
            self.fire(self.output, msg.value, msg.id)


class Summator(Node):
    @handler("input", datatypes.Tuple(datatypes.Object()), True)
    def input(self, msgs):
        global result
        result += sum([msg.value for msg in msgs.value])
        if result == 15:
            print(result)
            self.terminate()


class MultiplaHandlers(unittest.TestCase):
    def test_something(self):
        with Session() as session:
            gen = TicksGen()
            action1 = DoSmth()
            action2 = DoSmthWithErr()
            action3 = DoSmth()
            sum = Summator()

            action1.input.connect(gen.tick)
            action2.input.connect(gen.tick)
            action3.input.connect(gen.tick)

            sum.input.connect(action1.output)
            sum.input.connect(action2.output)
            sum.input.connect(action3.output)

            session.run()
        global result
        self.assertEqual(result, 15)
