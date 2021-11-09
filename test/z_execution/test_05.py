import logging
import multiprocessing
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
threshold = 23.0
result = list(filter(lambda x: x >= threshold, sent_array))
test_node_result = None


class Generator(Node):
    threshold = Property(bbtypes.Int(), default_value=0.7, optional=True)
    processed_batch = Event("processedBatch", bbtypes.List(bbtypes.Int()))

    def run(self):
        self.fire(self.processed_batch, sent_array)


class Processor(Node):
    threshold = Property(bbtypes.Int(), default_value=0.7, optional=True)
    result = Event("result", bbtypes.Object())

    @handler("onProcessBatch", bbtypes.List(bbtypes.Int()), False, MetaInfo())
    def on_process_batch(self, msg):
        self.fire(self.result, list(filter(lambda x: x >= self.threshold, msg.value)))


class TestNode(Node):
    result = None

    @handler("receive_result", bbtypes.Object())
    def receive_result(self, msg):
        self.result = msg.value
        logging.debug(msg.value)
        self.terminate()


def first_worker():
    with Session(server_port=port, external_nodes=["processor", "test-node"]) as session:
        generator = Generator()
        generator.id = "generator"
        session.run()


def second_worker(return_dict):
    with Session(name="second", serves_server=False, server_port=port) as session:
        processor = Processor()
        processor.threshold = 0.9
        processor.id = "processor"
        test_node = TestNode("test-node")

        processor.threshold = threshold
        processed_batch = ExternalEvent(
            "processedBatch", bbtypes.List(bbtypes.Int()), node_id="generator"
        )
        processor.on_process_batch.connect(processed_batch)
        test_node.receive_result.connect(processor.result)
        session.run()

    return_dict["result"] = test_node.result


class CheckGraphExecution_05(unittest.TestCase):
    def test(self):
        logging.basicConfig(level=logging.DEBUG)

        manager = multiprocessing.Manager()
        return_dict = manager.dict()
        worker = multiprocessing.Process(target=first_worker)
        worker.start()

        worker2 = multiprocessing.Process(target=second_worker, args=(return_dict,))
        worker2.start()

        worker.join()
        worker2.join()
        self.assertEqual(result, return_dict["result"])
