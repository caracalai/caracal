import bblocks.execution.session

from bblocks.execution.node import Node
from bblocks.declaration.metainfo import MetaInfo
import bblocks.declaration.datatypes as bbtypes
from bblocks.declaration.nodetype import *
import logging


class VideoProcessor(Node):
    def __init__(self):
        super().__init__()
        self.processed_frame = Event("processedFrame", bbtypes.Image, MetaInfo(description="Description"))
        self.processed_batch = Event("processedBatch", bbtypes.List(bbtypes.Int()))

    def run(self):
        for i in range(10):
            self.generate_event(self.processed_batch, [1, 2, 3])


class FaceDetector(Node):
    def __init__(self):
        super().__init__()
        self.threshold = Property(bbtypes.Int(), default_value=0.7, optional=True)

    @handler("onProcessFrame", bbtypes.Image(), False, MetaInfo())
    def on_process_frame(self, msg):
        pass

    @handler("onProcessBatch", bbtypes.List(bbtypes.Int()), False, MetaInfo())
    def on_process_batch(self, msg):
        print(msg.value)


# Everything is served under one session
def usecase_first():
    with bblocks.execution.session.Session() as session:
        logging.basicConfig(level=logging.DEBUG)
        processor = VideoProcessor()
        detector = FaceDetector()

        detector.threshold.value = 1
        detector.on_process_batch.connect(processor.processed_batch)
        session.run()


# Everything is served under several sessions
def usecase_second():
    serves = True
    port = 2000
    if serves:
        with bblocks.execution.session.Session(server_port=port) as session:
            processor = VideoProcessor()
            processor.id = "my-processor"
            session.external_nodes = ["my-detector"]
            session.run()
    else:
        with bblocks.execution.session.Session(server_port=port, serves_server=False) as session:
            detector = FaceDetector()
            detector.id = "my-detector"
            detector.threshold = 0.7
            processor_processed_batch = ExternalEvent("generatedBatch", bbtypes.Image(), node_id="my-processor")
            detector.processBatch.connect(processor_processed_batch)
            session.run()


if __name__ == "__main__":
    usecase_first()
