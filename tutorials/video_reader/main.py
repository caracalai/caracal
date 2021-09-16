from bblocks.execution.nodebase import *
from bblocks.execution.nodecluster import *
from bblocks.declaration.graph import *
from collections import deque
import cv2
import sys
import unittest
from bblocks.typesparser import typesparser
import logging, time
from test.test_execution.resultreceiver import ResultReceiver

localhost = "tcp://127.0.0.1"
delay = 0.0
test_count = 10
list_size = 5
import time, tqdm

class ReadVideoFile(NodeBase):
    def __init__(self):
        super().__init__()
        self.register_event("next_batch")
        self.register_event("frame_count")

    def run(self):

        cap = cv2.VideoCapture(video_filepath)
        if cap.isOpened() == False:
            print("Video is not opened")

        start = time.time()
        frame_cnt = 0

        batch_size = 100
        batch = []
        pbar = tqdm.tqdm()
        while cap.isOpened():
            ret, frame = cap.read()
            pbar.update(1)
            if ret == True:
                batch.append(basictypes.Image(frame))
                if len(batch) == batch_size:
                    self.generate_event("next_batch", batch)
                    frame_cnt += len(batch)
                    batch = []
                    if frame_cnt > 200:
                        break
            else:
                break
        if len(batch) == batch_size:
            self.generate_event("next_batch", batch)
            frame_cnt += len(batch)
            batch = []
        cap.release()
        end = time.time()
        self.generate_event("frame_count", frame_cnt)
        print(end - start)


class AddBorder(NodeBase):
    def __init__(self):
        super().__init__()
        self.register_handler("process_batch", self.process_batch)
        self.register_event("result_batch")

    def process_batch(self, msg):
        images = msg.value
        result = []
        for image in images:
            image = image.image
            row, col = image.shape[:2]
            bottom = image[row - 2:row, 0:col]
            mean = cv2.mean(bottom)[0]

            bordersize = 30
            border = cv2.copyMakeBorder(
                image,
                top=bordersize,
                bottom=bordersize,
                left=bordersize,
                right=bordersize,
                borderType=cv2.BORDER_CONSTANT,
                value=[165, 36, 34]
            )
            result.append(basictypes.Image(border))
        self.generate_event("result_batch", result, msg.id)


class CreateBundleFromStream(NodeBase):
    def __init__(self):
        super().__init__()
        self.register_handler("add_batch", self.add_batch)
        self.register_handler("add", self.add)
        self.register_handler("set_bundle_size", self.set_bundle_size)
        self.register_event("next_bundle")

        self._objects = []
        self._counters = []

    def add_batch(self, msg):
        self._objects.extend(msg.value)
        self._check()

    def add(self, msg):
        self._objects.append(msg.value)
        self._check()

    def set_bundle_size(self, msg):
        self._counters.append(msg.value)
        self._check()

    def _check(self):
        if len(self._counters) == 0:
            return
        counter = self._counters[0]
        if len(self._objects) >= counter:
            bundle = self._objects[:counter]
            self._counters.pop(0)
            self.generate_event("next_bundle", bundle)

class CreateVideoFile(NodeBase):
    def __init__(self):
        super().__init__()
        self.register_handler("process", self.process)

    def process(self, msg):
        frames = msg.value
        if len(frames) == 0:
            return
        frame_shape = frames[0].image.shape
        video = cv2.VideoWriter(output_filepath, -1, 25, (frame_shape[1], frame_shape[0]))
        for frame in frames:
            video.write(frame.image)

        video.release()
        print("saved video")


class MyNodeCluster(NodeCluster):
    def create_node(self, name):
        if name == "ReadVideoFile":
            return ReadVideoFile()
        if name == "AddBorder":
            return AddBorder()
        if name == "CreateBundleFromStream":
            return CreateBundleFromStream()
        if name == "CreateVideoFile":
            return CreateVideoFile()
        raise RuntimeError("Undefined type {type}".format(type=name))


types = \
    """
    node ReadVideoFile:
        events:
            next_batch(imgs: list(image))
            frame_count(cnt: int)

    node AddBorder:
        handlers:
            process_batch(imgs:list(Image))
        events:
            result_batch(imgs:list(Image))

    node CreateBundleFromStream:
        handlers:
            add_batch(items: list(object))
            add(item: object)
            set_bundle_size(count: int)
        events:
            next_bundle(items: list(object))
    
    node CreateVideoFile:
        handlers:
            process(frames: list(image))
        events:
            result(video: int)
    """


def create_graph():
    parser = typesparser.TypesParser()
    node_types = parser.parse(types)
    node_types = {node.name: node for node in node_types}

    graph = Graph()
    ReadVideoFile = graph.addNode(node_types["ReadVideoFile"])
    AddBorder = graph.addNode(node_types["AddBorder"])
    CreateBundleFromStream = graph.addNode(node_types["CreateBundleFromStream"])
    CreateVideoFile = graph.addNode(node_types["CreateVideoFile"])

    graph.connect(ReadVideoFile, "next_batch", AddBorder, "process_batch")
    graph.connect(ReadVideoFile, "frame_count", CreateBundleFromStream, "set_bundle_size")
    graph.connect(AddBorder, "result_batch", CreateBundleFromStream, "add_batch")
    graph.connect(CreateBundleFromStream, "next_bundle", CreateVideoFile, "process")
    graph.server_fabric = "python-service"
    for k, v in graph.nodes.items():
        v.fabric = "python-service"
    return graph


if __name__ == "__main__":
    global result_receiver
    global video_filepath
    global output_filepath

    video_filepath = sys.argv[1]
    output_filepath = sys.argv[2]
    result_receiver = ResultReceiver(localhost)
    logging.basicConfig(level=logging.CRITICAL)

    graph = create_graph()
    config = json.loads(graph.serializeForExecutor())

    server_endpoint = 'tcp://127.0.0.1:2000'
    myFabric = MyNodeCluster("python-service", config)
    myFabric.start(server_endpoint)
    myFabric.wait()
