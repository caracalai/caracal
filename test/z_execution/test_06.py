import json
import logging
import unittest
import  pickle

from broutonblocks.declaration import MetaInfo
from broutonblocks.declaration.projects import ProjectInfo
import broutonblocks.declaration.datatypes as bbtypes
from broutonblocks.execution import Event, handler, Node, Property, Session
from broutonblocks.utils.types_tools import upload_node_types

sent_array = [54, -21, 54, 43, 34, 5, 43, 2, -6, 2]
threshold = 23
result = list(filter(lambda x: x >= threshold, sent_array))


class Generator(Node):
    processed_batch = Event("processedBatch", bbtypes.Tuple(bbtypes.Int()))

    def run(self):
        self.fire(self.processed_batch, sent_array)


class Processor(Node):
    threshold = Property(bbtypes.Int(), default_value=0.7, optional=True)
    result = Event("result", bbtypes.Tuple(bbtypes.Object()))

    @handler("onProcessBatch", bbtypes.Tuple(bbtypes.Int()), False, MetaInfo())
    def on_process_batch(self, msg):
        self.fire(self.result, list(filter(lambda x: x >= self.threshold, msg.value)))


class TestNode(Node):
    @handler("receive_result", bbtypes.Tuple(bbtypes.Object()))
    def receive_result(self, msg):
        self.result = msg.value
        self.terminate()


class CheckGraphExecution_06(unittest.TestCase):
    def test(self):
        upload_node_types("type.txt", Generator, Processor, TestNode)
        project = ProjectInfo().deserialize(open('project.json').read())
        # with Session() as session:
        #     logging.basicConfig(level=logging.DEBUG)
        #     processor = Generator()
        #     processor.id = "processor"
        #     detector = Processor()
        #     detector.id = "detector"
        #     test_node = TestNode("test-node")
        #
        #     detector.threshold = threshold
        #     detector.on_process_batch.connect(processor.processed_batch)
        #     test_node.receive_result.connect(detector.result)
        #     session.run()
        #     self.assertEqual(result, test_node.result)
