from typing import Any, List

from multiversx_sdk.abi.codec import Codec
from multiversx_sdk.abi.parts import PartsHolder
from multiversx_sdk.abi.values_multi import (InputMultiValue,
                                             InputOptionalValue,
                                             InputVariadicValues,
                                             OutputMultiValue,
                                             OutputOptionalValue,
                                             OutputVariadicValues)


class Serializer:
    """
    The serializer follows the rules of the MultiversX Serialization format:
    https://docs.multiversx.com/developers/data/serialization-overview
    """

    def __init__(self, parts_separator: str, pub_key_length: int):
        if not parts_separator:
            raise ValueError("cannot create serializer: parts separator must not be empty")

        self.parts_separator = parts_separator
        self.codec = Codec(pub_key_length)

    def serialize(self, input_values: List[Any]) -> str:
        parts = self.serialize_to_parts(input_values)
        return self._encode_parts(parts)

    def serialize_to_parts(self, input_values: List[Any]) -> List[bytes]:
        parts_holder = PartsHolder([])
        self._do_serialize(parts_holder, input_values)
        return parts_holder.get_parts()

    def _do_serialize(self, parts_holder: PartsHolder, input_values: List[Any]):
        for i, value in enumerate(input_values):
            if value is None:
                raise ValueError("cannot serialize nil value")

            if isinstance(value, InputOptionalValue):
                if i != len(input_values) - 1:
                    # Usage of multiple optional values is not recommended:
                    # https://docs.multiversx.com/developers/data/multi-values
                    # Thus, here, we disallow them.
                    raise ValueError("an optional value must be last among input values")

                self._serialize_input_optional_value(parts_holder, value)
            elif isinstance(value, InputMultiValue):
                self._serialize_input_multi_value(parts_holder, value)
            elif isinstance(value, InputVariadicValues):
                if i != len(input_values) - 1:
                    raise ValueError("variadic values must be last among input values")

                self._serialize_input_variadic_values(parts_holder, value)
            else:
                parts_holder.append_empty_part()
                self._serialize_directly_encodable_value(parts_holder, value)

    def _serialize_input_optional_value(self, parts_holder: PartsHolder, value: InputOptionalValue):
        if value.value is None:
            return

        self._do_serialize(parts_holder, [value.value])

    def _serialize_input_multi_value(self, parts_holder: PartsHolder, value: InputMultiValue):
        for item in value.items:
            self._do_serialize(parts_holder, [item])

    def _serialize_input_variadic_values(self, parts_holder: PartsHolder, value: InputVariadicValues):
        for item in value.items:
            self._do_serialize(parts_holder, [item])

    def _serialize_directly_encodable_value(self, parts_holder: PartsHolder, value: Any):
        data = self.codec.encode_top_level(value)
        parts_holder.append_to_last_part(data)

    def deserialize(self, data: str, output_values: List[Any]):
        parts = self._decode_into_parts(data)
        self.deserialize_parts(parts, output_values)

    def deserialize_parts(self, parts: List[bytes], output_values: List[Any]):
        parts_holder = PartsHolder(parts)
        self._do_deserialize(parts_holder, output_values)

    def _do_deserialize(self, parts_holder: PartsHolder, output_values: List[Any]):
        for i, value in enumerate(output_values):
            if value is None:
                raise ValueError("cannot deserialize into nil value")

            if isinstance(value, OutputOptionalValue):
                if i != len(output_values) - 1:
                    # Usage of multiple optional values is not recommended:
                    # https://docs.multiversx.com/developers/data/multi-values
                    # Thus, here, we disallow them.
                    raise ValueError("an optional value must be last among output values")

                self._deserialize_output_optional_value(parts_holder, value)
            elif isinstance(value, OutputMultiValue):
                self._deserialize_output_multi_value(parts_holder, value)
            elif isinstance(value, OutputVariadicValues):
                if i != len(output_values) - 1:
                    raise ValueError("variadic values must be last among output values")

                self._deserialize_output_variadic_values(parts_holder, value)
            else:
                self._deserialize_directly_encodable_value(parts_holder, value)

    def _deserialize_output_optional_value(self, parts_holder: PartsHolder, value: OutputOptionalValue):
        if parts_holder.is_focused_beyond_last_part():
            value.value = None
            return

        self._do_deserialize(parts_holder, [value.value])

    def _deserialize_output_multi_value(self, parts_holder: PartsHolder, value: OutputMultiValue):
        for item in value.items:
            self._do_deserialize(parts_holder, [item])

    def _deserialize_output_variadic_values(self, parts_holder: PartsHolder, value: OutputVariadicValues):
        while not parts_holder.is_focused_beyond_last_part():
            new_item = value.item_creator()

            self._do_deserialize(parts_holder, [new_item])

            value.items.append(new_item)

    def _deserialize_directly_encodable_value(self, parts_holder: PartsHolder, value: Any):
        part = parts_holder.read_whole_focused_part()
        self.codec.decode_top_level(part, value)
        parts_holder.focus_on_next_part()

    def _encode_parts(self, parts: List[bytes]) -> str:
        parts_hex = [part.hex() for part in parts]
        return self.parts_separator.join(parts_hex)

    def _decode_into_parts(self, encoded: str) -> List[bytes]:
        parts_hex = encoded.split(self.parts_separator)
        parts = [bytes.fromhex(part_hex) for part_hex in parts_hex]
        return parts
