import jsonschema
from django.core.exceptions import ValidationError
from jsonschema.validators import validator_for


def validate_json_schema(value):
    """
    Validate json schema
    """
    try:
        if value:
            # check only if schema defined
            cls = validator_for(value)
            cls.check_schema(value)
    except jsonschema.exceptions.ValidationError as e:
        raise ValidationError(message=e.message)

    return value


def validate_json_schema_data(value, schema):
    """
    Validate data according json schema
    """
    try:
        # check result schema
        if value and schema:
            properties = schema.get('properties').keys()
            unexpected_properties = value.keys() - properties
            if unexpected_properties:
                # value key(s) not in expected properties
                raise ValidationError(message=f"{unexpected_properties} not in schema properties")
            jsonschema.validate(value, schema)
    except jsonschema.exceptions.ValidationError as e:
        raise ValidationError(message=e.message)

    return value
