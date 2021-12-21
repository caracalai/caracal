import logging
import unittest

from caracal.declaration import MetaInfo
import caracal.declaration.datatypes as caratypes
from caracal.execution import Event, handler, Node, Property, Session

sent_array = [54, -21, 54, 43, 34, 5, 43, 2, -6, 2]
threshold = 23
result = list(filter(lambda x: x >= threshold, sent_array))


class Generator(Node):
    processed_batch = Event("processedBatch", caratypes.Tuple(caratypes.Int()))

    def run(self):
        self.fire(self.processed_batch, sent_array)


class Processor(Node):
    threshold = Property(caratypes.Int(), default_value=0.7)
    result = Event("result", caratypes.Tuple(caratypes.Object()))

    @handler("onProcessBatch", caratypes.Tuple(caratypes.Int()), False, MetaInfo())
    def on_process_batch(self, msg):
        self.fire(self.result, list(filter(lambda x: x >= self.threshold, msg.value)))


class TestNode(Node):
    @handler("receive_result", caratypes.Tuple(caratypes.Object()))
    def receive_result(self, msg):
        self.result = msg.value
        self.terminate()


class CheckGraphExecution_03(unittest.TestCase):
    def test(self):
        with Session() as session:
            logging.basicConfig(level=logging.DEBUG)
            generator = Generator()
            generator.id = "generator"
            processor = Processor()
            processor.id = "processor"
            test_node = TestNode("test-node")

            processor.threshold = threshold
            processor.on_process_batch.connect(generator.processed_batch)
            test_node.receive_result.connect(processor.result)
            session.run()
            self.assertEqual(result, test_node.result)
