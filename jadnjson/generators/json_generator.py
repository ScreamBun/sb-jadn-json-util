import json
from benedict import benedict
from jsf import JSF
import jsonpointer

from jadnjson.constants import generator_constants
from jadnjson.constants.generator_constants import BASE_16, BASE_32, BASE_64, CONTENT_ENCODING, DATETIME_TIMEZONE_ORIG, DATETIME_TIMEZONE_REVISED, DOL_REF, POUND, POUND_SLASH, SLASH_DOL_REF
from jadnjson.utils.general_utils import get_last_occurance, remove_chars
from jadnjson.validators.schema_validator import validate_schema


def find_fix_encoding(data: benedict) -> benedict:
    """
    Some JADN specific encoding does not get converted to a JSON Schema equivalent during JSON Schema translation. 
    This logic attempts to map JADN encoding to JSON Schema valid encoding.  Eventually this needs to be fixed 
    in the JADN to JSON Schema Translation logic.  

    Args:
        data (benedict): JSON Schema

    Returns:
        benedict: Updated JSON Schema
    """
    
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
                case generator_constants.BASE_64:
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


def is_recursion_found(data: benedict, key: str, pointer: str) -> bool:  
    """
    Attempts to detect recursion within inner ref data.  The logic looks at parent keys,
    child keys and child ref keys.  More detection maybe needed, or renaming...

    Args:
        data (benedict): JSON Schema
        key (str): key (ref)
        pointer (str): path to the ref data

    Returns:
        bool: returns true if recursion found
    """
        
    recursion_found = False        
        
    key = remove_chars(key, "/", 1)  
    pointer = remove_chars(pointer, "/", 1)             
    pointer_name = get_last_occurance(pointer, '/', True)
    pointer_data = data.get(pointer)
    print('*** pointer: ', pointer)   
    pointer_keys = pointer_data.keypaths(indexes=False)        
    inner_refs = [i for i in pointer_keys if DOL_REF in i]
    
    parent_keys = key.split('/')
    parent_keys = list(map(str.lower, parent_keys))

    # Must be more than one, because the pointer resolve could contian the pointer name    
    if parent_keys.count(pointer_name) > 1:
        recursion_found = True
        
    elif pointer_keys.count(pointer_name) >= 1:
        recursion_found = True        
        
    elif inner_refs:
        
        for inner_ref in inner_refs:
            inner_pointer_path = pointer_data.get(inner_ref)
            innner_pointer_name = get_last_occurance(inner_pointer_path, '/', True)
            if innner_pointer_name in parent_keys:
                recursion_found = True
                break        
        
    return recursion_found


def find_update_refs(data: dict | benedict) -> benedict:
    """
    Searches json data for inner $refs and updates them with their actual values. 
    Attempts to detect recursion in refs.  If recursion is found, then that item is removed
    from the JSON Schema used for data generation.  Otherwise the data generation hits an endless loop.  

    Args:
        data (dict | benedict): json data to be searched

    Returns:
        benedict: {ref, pointer_to_value}
    """
    
    keys_list = data.keypaths(indexes=False)
    ref_key_list = [i for i in keys_list if i.endswith(DOL_REF)]
    for ref_key in ref_key_list:
        pointer = data.get(ref_key)
        
        if isinstance(pointer, str) and POUND in pointer:
            path_updated = pointer.replace(POUND, "")                
            ref_updated = ref_key.replace(SLASH_DOL_REF, "")
            
            recursion_found = is_recursion_found(data, ref_updated, path_updated)
            
            if recursion_found:
                print("warning: recursion found, removing for generation: ", ref_updated)
                del data[ref_updated]                 
            else:
                resolved_data = jsonpointer.JsonPointer(path_updated).resolve(data)

                try:
                    print("* ", ref_updated)
                    if ref_updated == "definitions/related-response/properties/related-tasks":
                        test = ""
                        
                    data[ref_updated] = resolved_data
                except RecursionError as err:
                    del data[ref_updated]
                    print("Recurrion error, ref removed from data gen -> ", ref_updated, resolved_data)
                
    keys_list_recheck = data.keypaths(indexes=False)
    ref_key_list = [i for i in keys_list_recheck if DOL_REF in i]
    if ref_key_list:
        find_update_refs(data)
                                     
    return data


def limit_max_items(schema: benedict, limit: int = 3) -> benedict:
    """
    Searches for type Array and then, adds a limit (default 3) to help 
    reduce the amount of mock data generated.  If nothing is provided then
    the data generated has no limit and takes awhile to generate data. 

    Args:
        schema (benedict): JSON Schema
        limit (int): array items limit, defaulted to 3

    Returns:
        benedict: Updated JSON Schema with limits added
    """
    
    key_type = "type"
    val_array = "array"
    max_items_tag = "/maxItems"
    min_items_tag = "/minItems"
    path_delimiter = "/"
    
    keys_list = schema.keypaths(indexes=True)
    for key in keys_list:
        
        if path_delimiter in key:
            key_split = key.rsplit(path_delimiter, 1)
            parent_key = key_split[0]
            last_key = key_split[1]
        else:
            last_key = key
            parent_key = key
        
        if last_key == key_type:
            val = schema.get(key)
            
            if val == val_array:
                max_items_path = parent_key + max_items_tag
                schema[max_items_path] = limit
              
        min_items_path = parent_key + min_items_tag
        min_items = schema.get(min_items_path)
        if min_items and min_items > limit:
            schema[min_items_path] = limit
            
    
    # print(schema.dump())
    
    return schema

def add_required_root_items(schema: benedict) -> benedict:
    """
    Adds a required item to root if one does not exist.  Otherwise the 
    data generator may return nothing. 

    Args:
        schema (benedict): JSON Schema

    Returns:
        benedict: returns an updated JSON Schema with a required item
    """

    if not schema.get("required"):

        properties = schema.get("properties")
        definitions = schema.get("definitions")
        reqs = []
        
        if properties:
            prop_list = properties.keypaths(indexes=False)
            
            for prop in prop_list:
                if "/" not in prop:
                    reqs.append(prop)         
            
            required = schema.get("required")
            if not required:
                schema["required"] = reqs
                
        elif definitions:
            defi = definitions.keypaths(indexes=False)[0]
            reqs.append(defi)              
            
            required = schema.get("required")
            if not required:
               schema["required"] = reqs        
            
                
    return schema


def fix_root_ref(schema: benedict) -> benedict:
    
    root_ref = schema.get("$ref")
    properties = schema.get("properties")
    type = schema.get("type")
    additionalProperties = schema.get("additionalProperties")
     
    if root_ref and not properties:
        schema["properties/root/$ref"] = root_ref
        del schema["$ref"]

        if not type:
            schema["type"] = "object"
            
        if not additionalProperties:
            schema["additionalProperties"] = False
    
    return schema

def adjust_patterns(schema: benedict) -> benedict:

    keys_list = schema.keypaths(indexes=False)
    pattern_key_list = [i for i in keys_list if i.endswith("pattern")]
    
    for pattern_key in pattern_key_list:
        pattern = schema.get(pattern_key)    
        
        if pattern == DATETIME_TIMEZONE_ORIG:
            schema[pattern_key] = DATETIME_TIMEZONE_REVISED
    
    return schema


def resolve_inner_refs(schema: str | dict | benedict) -> benedict:
    """
    Searches the json schema for inner refs ($ref) and replaces them with their actual values.  
    In other words, resovling the references.  Attempts to detect recursion and skips it if found.

    Args:
        schema (str| dict | benedict): JSON Scheam to be searched for inner $refs. 
        Will convert a str to JSON and JSON to a Benedict, if given those types.

    Returns:
        benedict: An updated JSON Schema with its referenences resolved.
    """
    
    if isinstance(schema, str):
        schema = json.loads(schema)
    
    if isinstance(schema, dict):
        schema = benedict(schema, keypath_separator="/")
    
    # TODO: Configurable limit and per type, hardcoded for arrays and 3 max items
    limit = 3
    schmea_patterns_adjusted = adjust_patterns(schema)
    schema_fixed_props = fix_root_ref(schmea_patterns_adjusted)
    schema_reqs_added = add_required_root_items(schema_fixed_props)
    schema_limited = limit_max_items(schema_reqs_added, limit)
    schema_encoding_fixed = find_fix_encoding(schema_limited)
    resolved_schema = find_update_refs(schema_encoding_fixed)
    
    print(resolved_schema.dump())         
    
    return resolved_schema
    

def gen_data_from_schema(schema: dict) -> str:
    """
    Generates fake data based on the schema

    Args:
        schema (str): JSON Schema

    Returns:
        str: Fake generated data based on the JSON Schema
    """
    
    # Validate before changes
    try:
        validate_schema(schema)
    except Exception as err:
        raise Exception(err)  
    
    
    schema_bene = resolve_inner_refs(schema)
    
    # Validate agaion after changes
    try:
        validate_schema(schema_bene)
    except Exception as err:
        raise Exception(err)    
    
    fake_json = {}
    try:   
        faker = JSF(schema_bene)
        fake_json = faker.generate()    
    except Exception as err:
        raise Exception(err)
    
    return fake_json