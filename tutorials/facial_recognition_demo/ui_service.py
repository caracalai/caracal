import logging
from bblocks.execution.node import *
from bblocks.execution.basictypes import *
from bblocks.execution.nodecluster import *
from bblocks.declaration import *
import cv2

class DragAndDropImageWebView(Node):
    def __init__(self):
        super().__init__()
        self.register_event("image_dropped")

    def run(self):
        image = cv2.imread('./Bezos.jpg')
        self.fire("image_dropped", Image(image))


class ShowDetectedFaceWebView(Node):
    def __init__(self):
        super().__init__()
        self.register_handler("processed_image", self.on_processed_image)

    def on_processed_image(self, msg):
        cv2.imshow("Result", msg.value[0].image)
        cv2.waitKey(0)


class UICluster(NodeCluster):
    def create_node(self, name):
        if name == "DragAndDropImageWebView":
            return DragAndDropImageWebView()
        if name == "ShowDetectedFaceWebView":
            return ShowDetectedFaceWebView()
        raise RuntimeError("Undefined type {type}".format(type=name))


if __name__ == "__main__":
    logging.basicConfig(level=logging.CRITICAL)

    with open("./graph.json") as f:
        config = json.load(f)

    server_endpoint = 'tcp://127.0.0.1:2000'
    cluster = UICluster("ui-service", config)
    cluster.start(server_endpoint)
    cluster.wait()
