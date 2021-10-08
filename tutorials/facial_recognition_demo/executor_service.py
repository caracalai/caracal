from bblocks.execution.node import *
from bblocks.execution.nodecluster import *
from bblocks.execution.basictypes import *
from bblocks.declaration import *
import cv2


class FaceDetection(Node):
    def __init__(self):
        super().__init__()
        self.register_handler("image", self.on_image)
        self.register_event("result")
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

    def on_image(self, msg):
        image = msg.value.image

        faces = self.face_cascade.detectMultiScale(image, 1.1, 4)
        # Draw the rectangle around each face
        bboxes = []
        for (x, y, w, h) in faces:
            cv2.rectangle(image, (x, y), (x + w, y + h), (255, 0, 0), 2)
            bboxes.append((int(x), int(y), int(x + w), int(y + h)))
        self.fire("result", (Image(image), bboxes))


class ExecutorCluster(NodeCluster):
    def create_node(self, name):
        if name == "FaceDetection":
            return FaceDetection()
        raise RuntimeError("Undefined type {type}".format(type=name))


if __name__ == "__main__":
    logging.basicConfig(level=logging.NOTSET)

    with open("./graph.json") as f:
        config = json.load(f)

    server_port = 2000
    cluster = ExecutorCluster("executor-service", config)
    cluster.start(server_port=server_port)
    cluster.wait()
