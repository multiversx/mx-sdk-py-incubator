from copy import deepcopy
from typing import Any, Dict, List, cast

from multiversx_sdk.abi.abi_definition import (AbiDefinition,
                                               EndpointDefinition,
                                               EnumDefinition,
                                               ParameterDefinition,
                                               StructDefinition)
from multiversx_sdk.abi.address_value import AddressValue
from multiversx_sdk.abi.biguint_value import BigUIntValue
from multiversx_sdk.abi.bool_value import BoolValue
from multiversx_sdk.abi.bytes_value import BytesValue
from multiversx_sdk.abi.enum_value import EnumValue
from multiversx_sdk.abi.field import Field
from multiversx_sdk.abi.interface import NativeObjectHolder
from multiversx_sdk.abi.list_value import ListValue
from multiversx_sdk.abi.option_value import OptionValue
from multiversx_sdk.abi.serializer import Serializer
from multiversx_sdk.abi.small_int_values import *
from multiversx_sdk.abi.struct_value import StructValue
from multiversx_sdk.abi.tuple_value import TupleValue
from multiversx_sdk.abi.type_formula import TypeFormula
from multiversx_sdk.abi.type_formula_parser import TypeFormulaParser
from multiversx_sdk.abi.values_multi import OptionalValue, VariadicValues
from multiversx_sdk.core.constants import ARGS_SEPARATOR


class Abi:
    def __init__(self, definition: AbiDefinition) -> None:
        self.definition = definition
        self.type_formula_parser = TypeFormulaParser()
        self.serializer = Serializer(parts_separator=ARGS_SEPARATOR)
        self.custom_types_prototypes_by_name: Dict[str, Any] = {}
        self.endpoints_prototypes_by_name: Dict[str, EndpointPrototype] = {}

        # for name in definition.types.enums:
        #     self.custom_types_prototypes_by_name[name] = self._create_custom_type_prototype(name)

        for struct_type in definition.types.structs:
            self.custom_types_prototypes_by_name[struct_type] = self._create_custom_type_prototype(struct_type)

        for endpoint in definition.endpoints:
            input_prototype = self._create_endpoint_input_prototypes(endpoint)
            output_prototype = self._create_endpoint_output_prototypes(endpoint)

            endpoint_prototype = EndpointPrototype(
                name=endpoint.name,
                input_parameters=input_prototype,
                output_parameters=output_prototype
            )

            self.endpoints_prototypes_by_name[endpoint.name] = endpoint_prototype

    def _create_custom_type_prototype(self, name: str) -> Any:
        if name in self.definition.types.enums:
            definition = self.definition.types.enums[name]
            return self._create_enum_prototype(definition)
        if name in self.definition.types.structs:
            definition = self.definition.types.structs[name]
            return self._create_struct_prototype(definition)

        raise ValueError(f"cannot create prototype for custom type {name} not found")

    def _create_enum_prototype(self, enum_definition: EnumDefinition) -> Any:
        # TODO create fields provider.
        return EnumValue()

    def _create_struct_prototype(self, struct_definition: StructDefinition) -> Any:
        fields_prototypes: List[Field] = []

        for field_definition in struct_definition.fields:
            type_formula = self.type_formula_parser.parse_expression(field_definition.type)
            field_prototype = self._create_prototype(type_formula)
            fields_prototypes.append(field_prototype)

        return StructValue(fields_prototypes)

    def _create_endpoint_input_prototypes(self, endpoint: EndpointDefinition) -> List[Any]:
        prototypes: List[Any] = []

        for parameter in endpoint.inputs:
            parameter_prototype = self._create_parameter_prototype(parameter)
            prototypes.append(parameter_prototype)

        return prototypes

    def _create_endpoint_output_prototypes(self, endpoint: EndpointDefinition) -> List[Any]:
        prototypes: List[Any] = []

        for parameter in endpoint.outputs:
            parameter_prototype = self._create_parameter_prototype(parameter)
            prototypes.append(parameter_prototype)

        return prototypes

    def _create_parameter_prototype(self, parameter: ParameterDefinition) -> Any:
        type_formula = self.type_formula_parser.parse_expression(parameter.type)
        return self._create_prototype(type_formula)

    def encode_endpoint_input_parameters(self, endpoint_name: str, values: List[Any]) -> List[bytes]:
        endpoint_prototype = self._get_endpoint_prototype(endpoint_name)

        if len(values) != len(endpoint_prototype.input_parameters):
            raise ValueError(f"invalid value length: expected {len(endpoint_prototype.input_parameters)}, got {len(values)}")

        input_values = deepcopy(endpoint_prototype.input_parameters)
        input_values_as_native_object_holders = cast(List[NativeObjectHolder], input_values)

        # Populate the input values with the provided arguments
        # TODO: SKIP IF ALREADY TYPED, thus not needed to call set_native_object(arg)
        for i, arg in enumerate(values):
            input_values_as_native_object_holders[i].set_native_object(arg)

        input_values_encoded = self.serializer.serialize_to_parts(input_values)
        return input_values_encoded

    def decode_endpoint_output_parameters(self, endpoint_name: str, encoded_values: List[bytes]) -> List[Any]:
        endpoint_prototype = self._get_endpoint_prototype(endpoint_name)
        output_values = deepcopy(endpoint_prototype.output_parameters)
        self.serializer.deserialize_parts(encoded_values, output_values)

        output_values_as_native_object_holders = cast(List[NativeObjectHolder], output_values)
        output_native_values = [value.get_native_object() for value in output_values_as_native_object_holders]
        return output_native_values

    def _get_endpoint_prototype(self, endpoint_name: str) -> 'EndpointPrototype':
        endpoint_prototype = self.endpoints_prototypes_by_name.get(endpoint_name)

        if not endpoint_prototype:
            raise ValueError(f"endpoint {endpoint_name} not found")

        return endpoint_prototype

    def _create_prototype(self, type_formula: TypeFormula) -> Any:
        name = type_formula.name

        if name == "bool":
            return BoolValue()
        if name == "u32":
            return U32Value()
        if name == "u64":
            return U64Value()
        if name == "BigUint":
            return BigUIntValue()
        if name == "bytes":
            return BytesValue()
        if name == "Address":
            return AddressValue()
        if name == "CodeMetadata":
            return BytesValue()
        if name == "tuple":
            return TupleValue([self._create_prototype(type_parameter) for type_parameter in type_formula.type_parameters])
        if name == "Option":
            type_parameter = type_formula.type_parameters[0]
            return OptionValue(self._create_prototype(type_parameter))
        if name == "List":
            type_parameter = type_formula.type_parameters[0]
            return ListValue([], item_creator=lambda: self._create_prototype(type_parameter))
        if name == "optional":
            # The prototype of an optional is provided a value.
            type_parameter = type_formula.type_parameters[0]
            return OptionalValue(self._create_prototype(type_parameter))
        if name == "variadic":
            type_parameter = type_formula.type_parameters[0]
            return VariadicValues([], item_creator=lambda: self._create_prototype(type_parameter))

        # Handle custom types
        if name in self.custom_types_prototypes_by_name:
            return deepcopy(self.custom_types_prototypes_by_name[name])

        raise ValueError(f"cannot create prototype for type: {name}")


class EndpointPrototype:
    def __init__(self, name: str, input_parameters: List[Any], output_parameters: List[Any]) -> None:
        self.name = name
        self.input_parameters = input_parameters
        self.output_parameters = output_parameters
