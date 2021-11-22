import json
import logging
import unittest
import pickle
import codecs

from broutonblocks.declaration import MetaInfo
from broutonblocks.declaration.projects import ProjectInfo
import broutonblocks.declaration.datatypes as bbtypes
from broutonblocks.execution import Event, handler, Node, Property, Session
from broutonblocks.utils.types_tools import upload_node_types

sent_array = [54, -21, 54, 43, 34, 5, 43, 2, -6, 2]
threshold = 23
result = list(filter(lambda x: x >= threshold, sent_array))


class Generator(Node):
    processed_batch = Event("processedBatch", bbtypes.Int())

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
        file = open('project', 'rb')
        project = pickle.loads(file.read())
        file.close()
        with Session() as session:
            session.register_types([Generator, Processor, TestNode])
            session.run_project(project)
            self.assertEqual(result, session.nodes[])