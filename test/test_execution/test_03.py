import bblocks.execution.session

from bblocks.execution.node import Node
from bblocks.declaration.metainfo import MetaInfo
import bblocks.declaration.datatypes as bbtypes
from bblocks.declaration.nodetype import *


class VideoProcessor(Node):
    def __init__(self):
        super().__init__()
        self.processed_frame = Event("processedFrame", bbtypes.Image, MetaInfo(description="Description"))
        self.processed_batch = Event("processedBatch", bbtypes.List(bbtypes.Int()))

    @handler("processFrame", bbtypes.Image())
    def process_frame(self, msg):
        pass

    @handler("processBatch", bbtypes.List(bbtypes.Image()))
    def process_batch(self, msg):
        pass

    def run(self):
        print("run")
        self.generate_event("processedBatch", [1, 2, 3])

    def info(self):
        return MetaInfo(category="Neural Networks", version="1.0", synopsis="", description="Description of Node")


class FaceDetector(Node):
    def __init__(self):
        super().__init__()
        self.threshold = Property(bbtypes.Int(), default_value=0.7, optional=True)

    @handler("onProcessFrame", bbtypes.Image(), False, MetaInfo())
    def on_process_frame(self, msg):
        pass

    @handler("onProcessBatch", bbtypes.List(bbtypes.Int()), False, MetaInfo())
    def on_process_batch(self, msg):
        pass

import logging
if __name__ == "__main__":
    with bblocks.execution.session.Session() as session:
        logging.basicConfig(level=logging.DEBUG)
        processor = VideoProcessor()
        detector = FaceDetector()

        detector.threshold.value = 1
        session.connect(processor.processed_batch, detector.on_process_batch)

        session.run()
#
# # Case when the graph is executed from different scripts
# if __name__ == "__main__":
#     port = 2000
#     with bb.Session(server_port=port) as session:
#         session.register_types([FaceDetector])
#         detector = session.add(FaceDetector())
#         detector.threshold = 0.7
#         processor_generatedBatch = bb.ExternalEvent("generatedBatch", bb.image, node_id="processor"))
#         bb.connect(processor_generatedBatch, detector.processBatch)
#         session.run()
#
#         # Construct graph with types from workspace:
#         from broutonblocks.canva import Canva
#
#         node_types = [
#         FaceDetector,
#         VideoProcessor
#     ]
#
#     # upload types to Canva
#     #if __name__ == "__main__":
#         client = Canva.login(username="misha", password="qwerty")
#     project = client.open_project("MyProject", create_if_not_exists=True)
#     project.import_types(node_types)
#
#     # load canva from
#     if __name__ == "__main__":
#         client = Canva.login(username="misha", password="qwerty")
#     project = client.open_project("MyProject")
#
#     port = 2000
#     with bb.Session(id="python-service", server_port=port) as session:
#         session.register_types(awesome_detectors_repo.node_types)
#     session.register_types(node_types)
#     session.load_graph(project.graph)
#     session.execute()
#
#     # blocks are in other repos
#     pip
#     install < external - git - repo >
#     with bb.Session(id="python-service", server_port=port) as session:
#         bb.register_nodes(awesome_detectors_repo.nodes)
