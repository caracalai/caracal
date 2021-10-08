import logging
import threading
import unittest

from broutonblocks.declaration import MetaInfo
import broutonblocks.declaration.datatypes as bbtypes
from broutonblocks.execution import (
    Event,
    ExternalEvent,
    handler,
    Node,
    Property,
    Session,
)

port = 2001
sent_array = [54, -21, 54, 43, 34, 5, 43, 2, -6, 2]
threshold = 23
result = list(filter(lambda x: x >= threshold, sent_array))
test_node_result = None


class Generator(Node):
    def __init__(self):
        super().__init__()
        self.processed_batch = Event("processedBatch", bbtypes.List(bbtypes.Int()))

    def run(self):
        self.fire(self.processed_batch, sent_array)


class Processor(Node):
    def __init__(self):
        super().__init__()
        self.threshold = Property(bbtypes.Int(), default_value=0.7, optional=True)
        self.result = Event("result", bbtypes.Object())

    @handler("onProcessBatch", bbtypes.List(bbtypes.Int()), False, MetaInfo())
    def on_process_batch(self, msg):
        self.fire(
            self.result, list(filter(lambda x: x >= self.threshold.value, msg.value))
        )


class TestNode(Node):
    @handler("receive_result", bbtypes.Object())
    def receive_result(self, msg):
        self.result = msg.value
        self.terminate()


def first_worker():
    with Session(server_port=port, external_nodes=["detector", "test-node"]) as session:
        processor = Generator()
        processor.id = "generator"
        session.run()


def second_worker():
    with Session(serves_server=False, server_port=port) as session:
        detector = Processor()
        detector.id = "detector"
        test_node = TestNode("test-node")

        detector.threshold.value = threshold
        processed_batch = ExternalEvent(
            "processedBatch", bbtypes.List(bbtypes.Int()), node_id="generator"
        )
        detector.on_process_batch.connect(processed_batch)
        test_node.receive_result.connect(detector.result)
        session.run()

        global test_node_result
        test_node_result = test_node.result


class CheckGraphExecution_05(unittest.TestCase):
    def test(self):
        logging.basicConfig(level=logging.CRITICAL)

        worker = threading.Thread(target=first_worker)
        worker.start()

        worker2 = threading.Thread(target=second_worker)
        worker2.start()

        worker.join()
        worker2.join()
        self.assertEqual(result, test_node_result)
