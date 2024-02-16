import json
from benedict import benedict
from jsf import JSF
from jadnjson.constants import generator_constants

from jadnjson.constants.generator_constants import ACTUAL_VAL, BASE_16, BASE_32, BASE_64, CONTENT_ENCODING, DOL_REF, ORIG_REF, PATH_TO_VAL, POUND_SLASH, SLASH_DOL_REF, UPDATED_REF
from jadnjson.validators.schema_validator import validate_schema


def find_fix_encoding(data: benedict) -> benedict:
    
    keys_list = data.keypaths(indexes=False)
    for key in keys_list:
        if CONTENT_ENCODING in key:
            encoding_type = data.get(key)
            new_encoding_type = None
            
            match encoding_type:
                case generator_constants.BASE_64_URL:
                    new_encoding_type = BASE_64
                case generator_constants.BASE64:
                    new_encoding_type = BASE_64
                case generator_constants.BASE32:
                    new_encoding_type = BASE_32
                case generator_constants.BASE16:
                    new_encoding_type = BASE_16
                case _:
                    print("encoding type not known")
                    
            if new_encoding_type:
                data[key] = new_encoding_type
    
    return data


def find_update_refs(data: dict | benedict, replaceDefAndPropKeys: bool = True) -> benedict:
    """
    Searches json data for inner $refs and updates them with their actual values. 

    Args:
        data (dict | benedict): json data to be searched
        flipDefsAndProps (bool, optional): Replaces properties (refs) with definitions (actuals). Defaults to True.

    Returns:
        benedict: {ref, path_to_value}
    """
    resolved_schema = data.clone()
    
    keys_list = data.keypaths(indexes=False)
    for key in keys_list:
        if DOL_REF in key:
            path = data.get(key)
                
            path_updated = path.replace(POUND_SLASH, "")                
            ref_updated = key.replace(SLASH_DOL_REF, "")
            
            resolved_schema[ref_updated] = data.get(path_updated)
                                     
    return resolved_schema


def resolve_inner_refs(schema: str | dict | benedict) -> benedict:
    """
    Searches the json schema for inner refs ($ref) and replaces them with their actual values.  
    In other words, resovling the references. 

    Args:
        schema (str| dict | benedict): JSON Scheam to be searched for inner $refs. 
        Will convert a str to JSON and JSON to a Benedict, if given those types.

    Returns:
        benedict: An updated JSON Schema with its referenences resolved.
    """
    
    if isinstance(schema, str):
        schema = json.loads(schema)
    
    if isinstance(schema, dict):
        resolved_schema = benedict(schema, keypath_separator="/")
    else:
        resolved_schema = schema
    
    resolved_schema = find_fix_encoding(resolved_schema)
    resolved_schema = find_update_refs(resolved_schema)
    
    print(resolved_schema.dump())         
    
    return resolved_schema


def gen_data_from_schema(schema: str) -> str:
    """
    Generates fake data based on the schema

    Args:
        schema (str): JSON Schema

    Returns:
        str: Fake generated data based on the JSON Schema
    """
    
    schema_bene = resolve_inner_refs(schema)
    
    try:
        validate_schema(schema_bene)
    except Exception as err:
        raise Exception(err)    
    
    print(schema_bene.dump())
    
    fake_json = {}
    try:   
        faker = JSF(schema_bene)
        fake_json = faker.generate()
    except Exception as err:
        raise Exception(err)
    
    return fake_json