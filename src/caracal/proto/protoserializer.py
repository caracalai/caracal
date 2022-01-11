from caracal.execution import basictypes
from caracal.proto import basictypes_pb2
from google.protobuf.any_pb2 import Any
import numpy as np


class ProtoSerializer:
    def ProtobufSerializer(self):
        pass

    def deserialize_value(self, value):
        if isinstance(value, Any):
            for t in [
                basictypes_pb2.StringValue,
                basictypes_pb2.NdarrayValue,
                basictypes_pb2.BooleanValue,
                basictypes_pb2.IntValue,
                basictypes_pb2.FloatValue,
                basictypes_pb2.TupleValue,
                basictypes_pb2.ListValue,
            ]:
                if value.type_url == f"type.googleapis.com/{t.DESCRIPTOR.full_name}":
                    unpacked_message = t()
                    if value.Unpack(unpacked_message):
                        return self.deserialize_value(unpacked_message)
                    raise RuntimeError(f"Couldn't deserialize {value}")

        if isinstance(value, basictypes_pb2.IntValue):
            return value.value
        if isinstance(value, basictypes_pb2.FloatValue):
            return value.value
        if isinstance(value, basictypes_pb2.StringValue):
            return value.value
        if isinstance(value, basictypes_pb2.BooleanValue):
            return value.value
        if isinstance(value, basictypes_pb2.NdarrayValue):
            shape = [self.deserialize_value(item) for item in value.shape]
            image = np.frombuffer(value.data, np.__dict__[value.data_type])
            image = np.reshape(image, shape)
            return basictypes.Ndarray(image=image)
        if isinstance(value, (basictypes_pb2.TupleValue, basictypes_pb2.ListValue)):
            items = [self.deserialize_value(item) for item in value.items]
            if isinstance(value, basictypes_pb2.TupleValue):
                items = tuple(items)
            return items
        raise RuntimeError(f"Undefined value: {value}")

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
        if isinstance(value, basictypes.Ndarray):
            result = basictypes_pb2.NdarrayValue()
            result.data = np.ndarray.tobytes(value.image)
            result.data_type = value.data_type
            for val in value.shape:
                obj = result.shape.add()
                obj.Pack(self.serialize_value(val))
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
        raise RuntimeError("Undefined value")

    def serialize_message(self, id_, value):
        message = basictypes_pb2.Message()
        message.id = id_
        message.value.Pack(self.serialize_value(value))
        return message

    def deserialize_message(self, msg):
        id_ = msg.id
        value = self.deserialize_value(msg.value)
        return id_, value
