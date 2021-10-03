import broutonblocks.declaration.datatypes as bbtypes
from broutonblocks.declaration import *
from broutonblocks.execution import *

import unittest, logging

sent_array = [54, -21, 54, 43, 34, 5, 43, 2, -6, 2]
threshold = 23
result = list(filter(lambda x: x >= threshold, sent_array))


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
        self.fire(self.result, list(filter(lambda x: x >= self.threshold.value, msg.value)))

class TestNode(Node):
    @handler("receive_result", bbtypes.Object())
    def receive_result(self, msg):
        self.result = msg.value
        self.terminate()


class CheckGraphExecution_03(unittest.TestCase):
    def test(self):
        with Session() as session:
            logging.basicConfig(level=logging.CRITICAL)
            processor = Generator()
            detector = Processor()
            test_node = TestNode("test-node")

            detector.threshold.value = threshold
            detector.on_process_batch.connect(processor.processed_batch)
            test_node.receive_result.connect(detector.result)
            session.run()
            self.assertEqual(result, test_node.result)




# # Everything is served under several sessions
# def usecase_second():
#     serves = True
#     port = 2000
#     if serves:
#         with bblocks.execution.session.Session(server_port=port) as session:
#             processor = Generator()
#             processor.id = "my-processor"
#             session.external_nodes = ["my-detector"]
#             session.run()
#     else:
#         with bblocks.execution.session.Session(server_port=port, serves_server=False) as session:
#             detector = Processor()
#             detector.id = "my-detector"
#             detector.threshold = 0.7
#             processor_processed_batch = ExternalEvent("generatedBatch", bbtypes.Image(), node_id="my-processor")
#             detector.processBatch.connect(processor_processed_batch)
#             session.run()
