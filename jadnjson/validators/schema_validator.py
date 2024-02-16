from jsonschema import Draft201909Validator


def validate_schema(schema: dict)-> tuple[bool, str]:
    #TODO: validate by draft $schema

    try:
        Draft201909Validator.check_schema(schema)
        return True, "Schema is Valid"

    except Exception as e:
        raise ValueError(e.message)