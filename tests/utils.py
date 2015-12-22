from bson import DBRef
import pytest
from rest_framework.exceptions import ValidationError
from mongoengine.errors import DoesNotExist


def dedent(blocktext):
    return '\n'.join([line[12:] for line in blocktext.splitlines()[1:-1]])


class BadType(object):
    """
    When used as a lookup with a `MockQueryset`, these objects
    will raise a `TypeError`, as occurs in Django when making
    queryset lookups with an incorrect type for the lookup value.
    """
    def __eq__(self):
        raise TypeError()


def get_items(mapping_or_list_of_two_tuples):
    # Tests accept either lists of two tuples, or dictionaries.
    if isinstance(mapping_or_list_of_two_tuples, dict):
        # {value: expected}
        return mapping_or_list_of_two_tuples.items()
    # [(value, expected), ...]
    return mapping_or_list_of_two_tuples


class FieldValues():
    """
    Base class for testing valid and invalid input values.
    """
    def test_valid_inputs(self):
        """
        Ensure that valid values return the expected validated data.
        """
        for input_value, expected_output in get_items(self.valid_inputs):
            assert self.field.run_validation(input_value) == expected_output

    def test_invalid_inputs(self):
        """
        Ensure that invalid values raise the expected validation error.
        """
        for input_value, expected_failure in get_items(self.invalid_inputs):
            with pytest.raises(ValidationError) as exc_info:
                self.field.run_validation(input_value)
            assert expected_failure in exc_info.value.detail[0]

    def test_outputs(self):
        for output_value, expected_output in get_items(self.outputs):
            assert self.field.to_representation(output_value) == expected_output
