import pyblocks.proto.basictypes_pb2 as basictypes_pb2
import pyblocks.basictypes as basictypes
from google.protobuf.any_pb2 import Any
import numpy as np

class ProtobufSerializer:
    def ProtobufSerializer(self):
        pass

    def deserialize_value(self, value):
        if isinstance(value, Any):
            for t in [basictypes_pb2.StringValue,
                      basictypes_pb2.ImageValue,
                      basictypes_pb2.BooleanValue,
                      basictypes_pb2.IntValue,
                      basictypes_pb2.CameraValue,
                      basictypes_pb2.TupleValue,
                      basictypes_pb2.ListValue]:
                if value.type_url == 'type.googleapis.com/%s' % t.DESCRIPTOR.full_name:
                    unpacked_message = t()
                    if value.Unpack(unpacked_message):
                        return self.deserialize_value(unpacked_message)
                    raise RuntimeError("Couldn't deserialize {value}".format(value=value))

        if isinstance(value, basictypes_pb2.IntValue):
            return value.value
        if isinstance(value, basictypes_pb2.FloatValue):
            return value.value
        if isinstance(value, basictypes_pb2.StringValue):
            return value.value
        # if isinstance(value, basictypes.Image):
        #     result = basictypes_pb2.ImageValue()
        #     result.data = cv2.imencode('.jpg', value.value)[1].tobytes()
        #     height, width, channels = value.value.shape
        #     result.width = width
        #     result.height = height
        #     return result
        if isinstance(value, basictypes_pb2.ImageValue):
            image = np.frombuffer(value.data, dtype=np.uint8)
            image = np.reshape(image, (value.width, value.height, 3))
            return basictypes.Image(image=image)
        if isinstance(value, basictypes_pb2.CameraValue):
            return basictypes.Camera(url=value.url)
        if isinstance(value, (basictypes_pb2.TupleValue, basictypes_pb2.ListValue)):
            items = [self.deserialize_value(item) for item in value.items]
            if isinstance(value, basictypes_pb2.TupleValue):
                items = tuple(items)
            return items
        raise RuntimeError("Undefined value: {value}".format(value=value))

    def serialize_value(self, value):
        if isinstance(value, str):
            result = basictypes_pb2.StringValue()
            result.value = value
            return result
        if not isinstance(value, bool):
            if isinstance(value, int):
                result = basictypes_pb2.IntValue()
                result.value = value
                return result
            if isinstance(value, np.int32):
                result = basictypes_pb2.IntValue()
                result.value = value
                return result
            if isinstance(value, float):
                result = basictypes_pb2.FloatValue()
                result.value = value
                return result
        if isinstance(value, bool):
            result = basictypes_pb2.BooleanValue()
            result.value = value
            return result
        if isinstance(value, basictypes.Image):
            result = basictypes_pb2.ImageValue()
            result.data = np.ndarray.tobytes(value.image)
            height, width, _ = value.image.shape
            result.width = width
            result.height = height
            return result
        if isinstance(value, tuple):
            result = basictypes_pb2.TupleValue()
            for item in value:
                obj = result.items.add()
                obj.Pack(self.serialize_value(item))
            return result
        if isinstance(value, list):
            result = basictypes_pb2.ListValue()
            for item in value:
                obj = result.items.add()
                obj.Pack(self.serialize_value(item))
            return result
        if isinstance(value, basictypes.Camera):
            result = basictypes_pb2.CameraValue()
            result.url = value.url
            return result
        if isinstance(value, basictypes.Image):
            result = basictypes_pb2.ImageValue()
            result.width = value.width
            result.height = value.height
            result.data = value.image
            return result
        raise RuntimeError("Undefined value")

    def serialize_message(self, id, value):
        message = basictypes_pb2.Message()
        message.id = id
        message.value.Pack(self.serialize_value(value))
        return message

    def deserialize_message(self, msg):
        id = msg.id
        value = self.deserialize_value(msg.value)
        return id, value
