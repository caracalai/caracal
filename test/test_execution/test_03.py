import bblocks.execution.session

import bblocks.declaration.datatypes as bbtypes
from bblocks.execution.node import *
from bblocks.declaration.nodetype import *
import logging


class VideoProcessor(Node):
    def __init__(self):
        super().__init__()
        self.processed_frame = Event("processedFrame", bbtypes.Image, MetaInfo(description="Description"))
        self.processed_batch = Event("processedBatch", bbtypes.List(bbtypes.Int()))

    def run(self):
        for i in range(10):
            self.fire(self.processed_batch, [1, 2, 3])


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

"""
session.uploadProject(<user-name>, <pass>, <project>)
session.downloadProject(<user-name>, <pass>, <project>)

"""

# if __name__ == "__main__":
#     # usecase_first
#
#     bblocks.serialize_to_file("mytypes.txt",  [type_first, type_second, ...])
#
#     # canva.upload_types("<user-name>, <pass>, <project>", [type_first, type_second, ...])
#
#     canva_proj = canva.load_project("<user-name>, <pass>, <project>")
#     with bblocks.execution.session.SessionInfo("session_a") as session:
#         session.register_types([FaceDetector, VideoProcessor])
#         session.run(canva_proj)
#
#
# > broutonblocks-cli --run <project>  --user <user-name>, --pass <pass> --session="default"  --port 2000