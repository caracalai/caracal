from bblocks.typesparser import typesparser
from bblocks.declaration.project import *
import logging

if __name__ == "__main__":
    with open("types.txt", encoding="utf8") as f:
        types = f.read()
    logging.basicConfig(level=logging.DEBUG)

    parser = typesparser.TypesParser()
    node_types = parser.parse(types)
    node_types = {node.name: node for node in node_types}

    graph = Project()
    DragAndDropImageWebView = graph.add_node(node_types["DragAndDropImageWebView"])
    ShowDetectedFaceWebView = graph.add_node(node_types["ShowDetectedFaceWebView"])
    FaceDetection = graph.add_node(node_types["FaceDetection"])

    graph.connect(DragAndDropImageWebView, "image_dropped", FaceDetection, "image")
    graph.connect(FaceDetection, "result", ShowDetectedFaceWebView, "processed_image")

    graph.server_fabric = "executor-service"
    DragAndDropImageWebView.fabric = "ui-service"
    ShowDetectedFaceWebView.fabric = "ui-service"
    FaceDetection.fabric = "executor-service"

    with open("graph.json", "w") as f:
        f.write(graph.serialize())


