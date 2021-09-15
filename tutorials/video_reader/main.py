from bblocks.execution.nodebase import *
from bblocks.execution.nodecluster import *
from bblocks.declaration.graph import *
from collections import deque
import cv2

import unittest
from bblocks.typesparser import typesparser
import logging, time
from test.test_execution.resultreceiver import ResultReceiver

localhost = "tcp://127.0.0.1"
delay = 0.0
test_count = 10
list_size = 5
import time

class ReadVideoFile(NodeBase):
    def __init__(self):
        super().__init__()
        self.register_event("next_image")

    def run(self):
        cap = cv2.VideoCapture("tom.mp4")
        if cap.isOpened() == False:
            print("Video is not opened")


        start = time.time()
        while cap.isOpened():
            ret, frame = cap.read()
            if ret == True:
                self.generate_event("next_image",  frame)
            else:
                break
        cap.release()
        end = time.time()
        print(end - start)


class ProcessImage(NodeBase):
    def __init__(self):
        super().__init__()
        self.register_handler("process_image", self.process_image)

    def process_image(self, msg):
        pass


class MyNodeCluster(NodeCluster):
    def create_node(self, name):
        if name == "ReadVideoFile":
            return ReadVideoFile()
        if name == "ProcessImage":
            return ProcessImage()
        raise RuntimeError("Undefined type {type}".format(type=name))


types = \
    """
    node ReadVideoFile:
        events:
            next_image(img:image)

    node ProcessImage:
        handlers:
            process_image(img:Image)
        events:
            processed_image(img:Image)
    """



def create_graph():
    parser = typesparser.TypesParser()
    node_types = parser.parse(types)
    node_types = {node.name: node for node in node_types}

    graph = Graph()
    ReadVideoFile = graph.addNode(node_types["ReadVideoFile"])
    ProcessImage = graph.addNode(node_types["ProcessImage"])

    graph.connect(ReadVideoFile, "next_image", ProcessImage, "process_image")
    graph.server_fabric = "python-service"
    for k, v in graph.nodes.items():
        v.fabric = "python-service"
    return graph


class CheckGraphExecution(unittest.TestCase):
    def test_first(self):
        global result_receiver

        result_receiver = ResultReceiver(localhost)
        logging.basicConfig(level=logging.CRITICAL)

        graph = create_graph()
        config = json.loads(graph.serializeForExecutor())

        server_endpoint = 'tcp://127.0.0.1:2000'
        myFabric = MyNodeCluster("python-service", config)
        myFabric.start(server_endpoint)

        msg = result_receiver.wait_results()
        self.assertTrue("results" in msg)