import json
from benedict import benedict
from jsf import JSF

from jadnjson.constants.generator_constants import DEFINITIONS, DOL_REF, ORIG_REF, PATH_TO_VAL, POUND_SLASH_DEFINITIONS, PROPERTIES, SLASH_DOL_REF, UPDATED_REF
from jadnjson.utils.general_utils import get_last_instance
from jadnjson.validators.schema_validator import validate_schema


def move_def_to_prop(schema: benedict) -> benedict:
    
    """
    Moves and overwrites properties (refs) with definitions (actuals) to assist with reference resolution.

    Args:
        schema (benedict): schema to be updated

    Returns:
        benedict: updated schema
    """
    
    if isinstance(schema, dict):
        schema = benedict(schema, keypath_separator="/")
        
    schema_orig = schema.clone()
    defs_at_root = schema_orig.get(DEFINITIONS)
    properties_at_root = schema_orig.get(PROPERTIES)
    
    if defs_at_root and properties_at_root:
        schema.move(DEFINITIONS, PROPERTIES)
    else:
        print("unable to move definitions under properties")
        
    print(schema.dump())
        
    return schema


def find_refs(data: dict | benedict, replaceDefAndPropKeys: bool = True) -> benedict:
    """
    Searches json data for inner $refs. 

    Args:
        data (dict | benedict): json data to be searched
        flipDefsAndProps (bool, optional): Replaces properties (refs) with definitions (actuals). Defaults to True.

    Returns:
        benedict: {ref, path_to_value}
    """
    
    refs_found = benedict()
    keys_list = data.keypaths(indexes=False)
    for key in keys_list:
        if DOL_REF in key:
            path = data.get(key)
            
            if replaceDefAndPropKeys:
                path_updated = path.replace(POUND_SLASH_DEFINITIONS, PROPERTIES)
                
            ref_updated = key.replace(SLASH_DOL_REF, "")
            
            ref_data = benedict()
            ref_data[ORIG_REF] = key
            ref_data[UPDATED_REF] = ref_updated
            ref_data[PATH_TO_VAL] = path_updated
            
            refs_found[ref_updated] = ref_data
            
    print("$refs found: ", refs_found.dump())
                                     
    return refs_found


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
        
    resolved_schema = move_def_to_prop(resolved_schema)        
    
    refs_found = find_refs(resolved_schema)
    
    for ref_found in refs_found:
        
        ref_data = refs_found[ref_found]
        
        orig_ref = ref_data[ORIG_REF]
        updated_ref = ref_data[UPDATED_REF]
        path_to_val = ref_data[PATH_TO_VAL]
        
        actual_val = resolved_schema.get(path_to_val)
     
        if path_to_val and actual_val:
            
            # actual_key_val_data = benedict()
            
            # new_val_key = get_last_instance(path_to_val, "/")
            # actual_key_val_data[new_val_key] = actual_val
            
            resolved_schema[updated_ref] = actual_val
            print("+ found and updated: ", path_to_val)
            
            remove_ref = resolved_schema.get(orig_ref)
            if remove_ref:
                del resolved_schema[orig_ref]
                print("- removed ref: ", orig_ref)
                
        else:
            print("*** unable to locate: ", path_to_val)            
    
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