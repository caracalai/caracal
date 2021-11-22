from broutonblocks.declaration import MetaInfo
import broutonblocks.declaration.datatypes as bbtypes
from broutonblocks.execution import (
    Event,
    handler,
    Node,
    Property,
    Session,
)

port = 2001


def upload_node_types(file, *args):
    with Session(name="second", serves_server=False, server_port=port):
        list_node = []
        for node in args:
            list_node.append(node())

        dump = open(file, "w+")

        for node in list_node:
            result = "node {name}:\n".format(name=node.name)
            result += "\tproperties:\n"
            for key, value in node.properties.items():
                result += "\t\t{name}: {type}\n".format(
                    name=key,
                    type=value.declaration.data_type.name.format(
                        name=key, type=str(value)
                    )
                    .replace("Integer", "int")
                    .replace("Binary", "binaryfile")
                    .lower(),
                )
                if value.declaration.default_value is not None:
                    result = result[:-1] + "({value})\n".format(
                        value=value.declaration.default_value
                    )
            result += "\thandlers:\n"
            for key, value in node.handlers.items():
                handler = "\t\t{name}({value_list})\n".format(
                    value_list=", ".join(
                        [
                            "value{index}: {arg_types}".format(
                                index=idx, arg_types=arg_types
                            )
                            for idx, arg_types in enumerate(
                                value.declaration.data_type.item_types, start=1
                            )
                        ]
                    )
                    .replace("Integer", "int")
                    .replace("Binary", "binaryfile")
                    .replace("(", "")
                    .replace(")", "")
                    .lower(),
                    name=key,
                )
                if value.declaration.receives_multiple:
                    result += (
                        handler[: handler.find("(")]
                        + "+"
                        + handler[handler.find("(") : -1]
                        + "\n"
                    )
                else:
                    result += handler

            result += "\tevents:\n"
            for key, value in node.node_type.events.items():
                result += "\t\t{name}(value: {type})\n".format(
                    name=key,
                    type=str(value)
                    .replace("Integer", "int")
                    .replace("Binary", "binaryfile")
                    .lower(),
                )
            dump.write(result)


if __name__ == "__main__":

    class Generator(Node):
        threshold = Property(bbtypes.Int(), default_value=0.7, optional=True)
        processed_batch = Event("processedBatch", bbtypes.List(bbtypes.BinaryArray()))

        def run(self):
            self.fire(self.processed_batch, [])

    class Processor(Node):
        threshold = Property(bbtypes.Int(), default_value=0.7, optional=True)
        result = Event("result", bbtypes.Object())

        @handler(
            "onProcessBatch",
            bbtypes.Tuple(bbtypes.Int(), bbtypes.Boolean()),
            False,
            MetaInfo(),
        )
        def on_process_batch(self, msg):
            self.fire(self.result, list(filter(lambda x: x >= self.threshold, msg.value)))

        # @handler("name")
        # def on_name(
        #         self,
        #         value: bbtypes.Type(),
        # ):

    class TestNode(Node):
        result = None

        @handler("receive_result", bbtypes.Tuple(bbtypes.Object()))
        def receive_result(self, msg):
            self.result = msg.value
            self.terminate()

    upload_node_types("a.txt", Generator, Processor, TestNode)
