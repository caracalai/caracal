import unittest

from broutonblocks.typesparser import typesparser


class CheckProperties(unittest.TestCase):
    def __init__(self, methodName="runTest"):
        super(CheckProperties, self).__init__(methodName)
        self._program = """
                @section(name="abc", count=12)
                node MyNode:
                    properties:
                        threshold?: float(0.8) // optional property with default value
                        border_width: int(10)
                        opt_param?: int  // optional parameter without default value
                        string_param: string
                        image_param: image
                        list_param: list(string)
                    handlers:
                        value(val:int)
                        value2(a: tuple(int, int))
                    events:
                        event1(a: int, b: float)
                """

    def test_properties_parsing(self):
        try:
            parser = typesparser.TypesParser()
            parser.parse(self._program)
        except typesparser.TypesParseError:
            self.fail("test_properties_parsing")

    def test_properties_saving(self):
        try:
            parser = typesparser.TypesParser()
            node_types = parser.parse(self._program)
            self.assertTrue(len(node_types) == 1, "Incorrect number of node types")
            myNode = node_types["MyNode"]
            self.assertTrue(
                len(myNode.properties) == 6, "Incorrect number of properties"
            )
            self.assertTrue(
                myNode.properties["threshold"].optional, "Threshold should be optional"
            )
            self.assertTrue(
                myNode.properties["threshold"].default_value is not None,
                "threshold should contain default value",
            )
            self.assertTrue(
                not myNode.properties["border_width"].optional,
                "border_width should not be optional",
            )
            self.assertTrue(
                myNode.properties["string_param"].default_value is None,
                "string_param should not contain default value",
            )

        except typesparser.TypesParseError:
            self.fail("test_properties_parsing")
