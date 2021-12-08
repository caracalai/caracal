import logging
import string
import time
import unittest
import random

from caracal.execution import Property, Event, Node, handler, Session
from caracal.declaration import datatypes as caratypes


class IntGenerator(Node):
    def __init__(self, id_=None):
        super().__init__(id_)
        self.results = []
        self.batch_results = []

    generated_val = Event("generated_val", caratypes.Tuple(caratypes.Int()))
    generated_batch = Event("generated_batch", caratypes.List(caratypes.Int()))

    def run(self):
        value = 0
        batch = []
        while value < 100:
            timer_start = time.time()
            value += 1
            self.fire(self.generated_val, value)
            self.results.append(time.time() - timer_start)
            batch.append(value)
            if value % 10 == 1:
                self.fire(self.generated_batch, batch)
                timer_end = time.time()
                self.batch_results.append(timer_end - timer_start)
                batch = []

        value = 0
        self.fire(self.generated_val, value)
        logging.warning("serialization avg time:")
        logging.warning(sum(self.results) / len(self.results))
        logging.warning(len(self.results))
        logging.warning("batch serialization avg time:")
        logging.warning(sum(self.batch_results) / len(self.batch_results))
        logging.warning(len(self.batch_results))


class IntReceiver(Node):
    def __init__(self, id_=None):
        super().__init__(id_)
        self.timer_start = time.time()
        self.batch_timer_start = time.time()
        self.results = []
        self.batch_results = []

    @handler("receive", caratypes.Tuple(caratypes.Int()))
    def on_received_value(self, msg):
        if msg.value == 0:
            logging.warning("deserialization avg time:")
            logging.warning(sum(self.results) / len(self.results))
            logging.warning(len(self.results))
            logging.warning("batch deserialization avg time:")
            logging.warning(sum(self.batch_results) / len(self.batch_results))
            logging.warning(len(self.batch_results))
            self.terminate()
            return
        timer_end = time.time()
        self.results.append(timer_end - self.timer_start)
        self.timer_start = time.time()

    @handler("receive_batch", caratypes.List(caratypes.Int()))
    def on_received_batch(self, msg):
        timer_end = time.time()
        self.batch_results.append(timer_end - self.timer_start)
        self.timer_start = time.time()


class FloatGenerator(Node):
    def __init__(self, id_=None):
        super().__init__(id_)
        self.results = []
        self.batch_results = []

    generated_val = Event("generated_val", caratypes.Tuple(caratypes.Int()))
    generated_batch = Event("generated_batch", caratypes.List(caratypes.Int()))

    def run(self):
        value = 0
        batch = []
        for i in range(100):
            timer_start = time.time()
            value += 0.003
            self.fire(self.generated_val, value)
            self.results.append(time.time() - timer_start)
            batch.append(value)
            if (i + 1) % 10 == 1:
                self.fire(self.generated_batch, batch)
                timer_end = time.time()
                self.batch_results.append(timer_end - timer_start)
                batch = []

        value = 0
        self.fire(self.generated_val, value)
        logging.warning("serialization avg time:")
        logging.warning(sum(self.results) / len(self.results))
        logging.warning(len(self.results))
        logging.warning("batch serialization avg time:")
        logging.warning(sum(self.batch_results) / len(self.batch_results))
        logging.warning(len(self.batch_results))


class FloatReceiver(Node):
    def __init__(self, id_=None):
        super().__init__(id_)
        self.timer_start = time.time()
        self.batch_timer_start = time.time()
        self.results = []
        self.batch_results = []

    @handler("receive", caratypes.Tuple(caratypes.Int()))
    def on_received_value(self, msg):
        if msg.value == 0:
            logging.warning("deserialization avg time:")
            logging.warning(sum(self.results) / len(self.results))
            logging.warning(len(self.results))
            logging.warning("batch deserialization avg time:")
            logging.warning(sum(self.batch_results) / len(self.batch_results))
            logging.warning(len(self.batch_results))
            self.terminate()
            return
        timer_end = time.time()
        self.results.append(timer_end - self.timer_start)
        self.timer_start = time.time()

    @handler("receive_batch", caratypes.List(caratypes.Int()))
    def on_received_batch(self, msg):
        timer_end = time.time()
        self.batch_results.append(timer_end - self.timer_start)
        self.timer_start = time.time()


class StringGenerator(Node):
    def __init__(self, id_=None):
        super().__init__(id_)
        self.results = []
        self.batch_results = []

    generated_val = Event("generated_val", caratypes.Tuple(caratypes.Int()))
    generated_batch = Event("generated_batch", caratypes.List(caratypes.Int()))

    def run(self):
        batch = []
        for i in range(100):
            value = "".join(
                random.SystemRandom().choice(string.ascii_uppercase + string.digits)
                for _ in range(63)
            )
            timer_start = time.time()
            self.fire(self.generated_val, value)
            self.results.append(time.time() - timer_start)
            batch.append(value)
            if (i + 1) % 10 == 1:
                self.fire(self.generated_batch, batch)
                timer_end = time.time()
                self.batch_results.append(timer_end - timer_start)
                batch = []

        value = 0
        self.fire(self.generated_val, value)
        logging.warning("serialization avg time:")
        logging.warning(sum(self.results) / len(self.results))
        logging.warning(len(self.results))
        logging.warning("batch serialization avg time:")
        logging.warning(sum(self.batch_results) / len(self.batch_results))
        logging.warning(len(self.batch_results))


class StringReceiver(Node):
    def __init__(self, id_=None):
        super().__init__(id_)
        self.timer_start = time.time()
        self.batch_timer_start = time.time()
        self.results = []
        self.batch_results = []

    @handler("receive", caratypes.Tuple(caratypes.Int()))
    def on_received_value(self, msg):
        if msg.value == 0:
            logging.warning("deserialization avg time:")
            logging.warning(sum(self.results) / len(self.results))
            logging.warning(len(self.results))
            logging.warning("batch deserialization avg time:")
            logging.warning(sum(self.batch_results) / len(self.batch_results))
            logging.warning(len(self.batch_results))
            self.terminate()
            return
        timer_end = time.time()
        self.results.append(timer_end - self.timer_start)
        self.timer_start = time.time()

    @handler("receive_batch", caratypes.List(caratypes.Int()))
    def on_received_batch(self, msg):
        timer_end = time.time()
        self.batch_results.append(timer_end - self.timer_start)
        self.timer_start = time.time()


class BoolGenerator(Node):
    def __init__(self, id_=None):
        super().__init__(id_)
        self.results = []
        self.batch_results = []

    generated_val = Event("generated_val", caratypes.Tuple(caratypes.Int()))
    generated_batch = Event("generated_batch", caratypes.List(caratypes.Int()))

    def run(self):
        batch = []
        for i in range(100):
            value = bool(random.randint(0, 1))
            timer_start = time.time()
            self.fire(self.generated_val, value)
            self.results.append(time.time() - timer_start)
            batch.append(value)
            if (i + 1) % 10 == 1:
                self.fire(self.generated_batch, batch)
                timer_end = time.time()
                self.batch_results.append(timer_end - timer_start)
                batch = []

        value = "end"
        self.fire(self.generated_val, value)
        logging.warning("serialization avg time:")
        logging.warning(sum(self.results) / len(self.results))
        logging.warning(len(self.results))
        logging.warning("batch serialization avg time:")
        logging.warning(sum(self.batch_results) / len(self.batch_results))
        logging.warning(len(self.batch_results))


class BoolReceiver(Node):
    def __init__(self, id_=None):
        super().__init__(id_)
        self.timer_start = time.time()
        self.batch_timer_start = time.time()
        self.results = []
        self.batch_results = []

    @handler("receive", caratypes.Tuple(caratypes.Int()))
    def on_received_value(self, msg):
        timer_end = time.time()
        self.results.append(timer_end - self.timer_start)
        self.timer_start = time.time()
        if msg.value == "end":
            logging.warning("deserialization avg time:")
            logging.warning(sum(self.results) / len(self.results))
            logging.warning(len(self.results))
            logging.warning("batch deserialization avg time:")
            logging.warning(sum(self.batch_results) / len(self.batch_results))
            logging.warning(len(self.batch_results))
            self.terminate()
            return

    @handler("receive_batch", caratypes.List(caratypes.Int()))
    def on_received_batch(self, msg):
        timer_end = time.time()
        self.batch_results.append(timer_end - self.timer_start)
        self.timer_start = time.time()


class DeserializationTypesTest(unittest.TestCase):
    def test_integers(self):
        with Session() as session:
            logging.basicConfig(level=logging.WARNING)
            receiver = IntReceiver()
            generator = IntGenerator()
            receiver.on_received_value.connect(generator.generated_val)
            receiver.on_received_batch.connect(generator.generated_batch)
            session.run()
            self.assertLess(
                sum(receiver.results) / len(receiver.results),
                0.05,
                "Too long deserialization",
            )

    def test_floats(self):
        with Session() as session:
            logging.basicConfig(level=logging.WARNING)
            receiver = FloatReceiver()
            generator = FloatGenerator()
            receiver.on_received_value.connect(generator.generated_val)
            receiver.on_received_batch.connect(generator.generated_batch)
            session.run()
            self.assertLess(
                sum(receiver.results) / len(receiver.results),
                0.05,
                "Too long deserialization",
            )

    def test_strings(self):
        with Session() as session:
            logging.basicConfig(level=logging.WARNING)
            receiver = StringReceiver()
            generator = StringGenerator()
            receiver.on_received_value.connect(generator.generated_val)
            receiver.on_received_batch.connect(generator.generated_batch)
            session.run()
            # TODO have some questions about deserialization time of strings
            # on my hard there is 0.5s deserialization of 64 symbols string
            self.assertLess(
                sum(receiver.results) / len(receiver.results),
                1,
                "Too long deserialization",
            )

    def test_bools(self):
        with Session() as session:
            logging.basicConfig(level=logging.WARNING)
            receiver = BoolReceiver()
            generator = BoolGenerator()
            receiver.on_received_value.connect(generator.generated_val)
            receiver.on_received_batch.connect(generator.generated_batch)
            session.run()
            self.assertLess(
                sum(receiver.results) / len(receiver.results),
                0.05,
                "Too long deserialization",
            )


if __name__ == "__main__":
    unittest.main()
