import json
from jsonschema import Draft202012Validator
# from jsonschema import Draft201909Validator


def validate_schema(schema: dict)-> tuple[bool, str]:
    #TODO: validate by draft $schema
    
    # json_object = json.dumps(schema, indent = 4)     

    try:
        # Draft201909Validator.check_schema(schema)
        # Draft202012Validator.check_schema(json_object)
        Draft202012Validator.check_schema(schema)
        return True, "Schema is Valid"

    except Exception as e:
        raise ValueError(e.message)