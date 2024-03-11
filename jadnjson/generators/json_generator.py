import json
from benedict import benedict
from jsf import JSF
import jsonpointer

from jadnjson.constants import generator_constants
from jadnjson.constants.generator_constants import ADDITIONAL_PROPS, BASE_16, BASE_32, BASE_64, CONTENT_ENCODING, DATETIME_TIMEZONE_ORIG, DATETIME_TIMEZONE_REVISED, DEFINITIONS, DOL_REF, MAX_ITEMS, MIN_ITEMS, NCNAME_ORIG, NCNAME_REVISED, OBJECT, POUND, POUND_SLASH, PROPERTIES, REQUIRED, RES_WORD_TYPE, RES_WORD_TYPE_ALT, SLASH_DOL_REF, TYPE
from jadnjson.utils.general_utils import get_keys, get_last_occurance, remove_chars
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


def find_update_refs(schema: dict | benedict) -> benedict:
    """
    Searches the json schema for inner $refs and updates them with their actual values. 
    Attempts to detect recursion in refs.  If recursion is found, then that item is removed
    from the JSON Schema used for data generation.  Otherwise the data generation hits an endless loop.  

    Args:
        data (dict | benedict): json data to be searched

    Returns:
        benedict: {ref, pointer_to_value}
    """
    
    keys_list = schema.keypaths(indexes=False)
    ref_key_list = [i for i in keys_list if i.endswith(DOL_REF)]
    for ref_key in ref_key_list:
        pointer = schema.get(ref_key)
        
        if isinstance(pointer, str) and POUND in pointer:
            pointer_updated = pointer.replace(POUND, "")                
            ref_key_updated = ref_key.replace(SLASH_DOL_REF, "")
            
            recursion_found = is_recursion_found(schema, ref_key_updated, pointer_updated)
            
            if recursion_found:
                print("warning: recursion found, removing for generation: ", ref_key_updated)
                del schema[ref_key_updated]                 
            else:
                resolved_data = jsonpointer.JsonPointer(pointer_updated).resolve(schema)
                schema[ref_key_updated] = resolved_data
                
    keys_list_recheck = schema.keypaths(indexes=False)
    ref_key_list = [i for i in keys_list_recheck if DOL_REF in i]
    if ref_key_list:
        find_update_refs(schema)
                                     
    return schema


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
    
    max_items_key_list = get_keys(schema, False, MAX_ITEMS)
    for max_item_key in max_items_key_list:
        max_val = schema.get(max_item_key)
        if max_val > limit:
            schema[max_item_key] = limit
            print("maxItems updated, was ", max_val)
            
    min_items_key_list = get_keys(schema, False, MIN_ITEMS)
    for min_item_key in min_items_key_list:
        min_val = schema.get(min_item_key)
        if min_val > limit:
            schema[min_item_key] = limit
            print("minItems updated, was ", min_val)
    
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

    if not schema.get(REQUIRED):

        properties = schema.get(PROPERTIES)
        definitions = schema.get(DEFINITIONS)
        reqs = []
        
        if properties:
            prop_list = properties.keypaths(indexes=False)
            
            for prop in prop_list:
                if "/" not in prop:
                    reqs.append(prop)         
            
            required = schema.get(REQUIRED)
            if not required:
                schema[REQUIRED] = reqs
                
        elif definitions:
            defi = definitions.keypaths(indexes=False)[0]
            reqs.append(defi)              
            
            required = schema.get(REQUIRED)
            if not required:
               schema[REQUIRED] = reqs        
            
                
    return schema


def fix_root_ref(schema: benedict) -> benedict:
    """
    Some JSON Schemas contain a single root level $ref, no properties and definitions.
    The data generator has trouble with these, so to be consistant, this function
    creates the missing properties object based on the single root $ref.

    Args:
        schema (benedict): JSON Schema

    Returns:
        benedict: JSON Schema updated to contain a properties object
    """
    
    root_ref = schema.get(DOL_REF)
    properties = schema.get(PROPERTIES)
    type = schema.get(TYPE)
    additionalProperties = schema.get(ADDITIONAL_PROPS)
     
    if root_ref and not properties:
        root_name = get_last_occurance(root_ref, "/", False)
        new_props_path = PROPERTIES + "/" + root_name + "/" + DOL_REF
        
        schema[new_props_path] = root_ref
        del schema[DOL_REF]

        if not type:
            schema[TYPE] = OBJECT
            
        if not additionalProperties:
            schema[ADDITIONAL_PROPS] = False
    
    return schema

def replace_reserved_words(schema: benedict) -> benedict:
    """
    Looks for revered words and sets them to an alternate name.

    Args:
        schema (benedict): JSON Schema

    Returns:
        benedict: JSON Schema with updated reserve words.
    """

    res_type_key_list = get_keys(schema, False, RES_WORD_TYPE)
    removed_keys = []
    
    # Update keys
    for type_key in res_type_key_list:
        copy_obj = schema.get(type_key)
        copy_obj_key = type_key.replace(RES_WORD_TYPE, RES_WORD_TYPE_ALT) 
        schema[copy_obj_key] = copy_obj
        del schema[type_key]
        removed_keys.append(type_key)
        print("Reserved word found in keys and updated", type_key) 
        
    # Update ref pointers
    ref_key_list = get_keys(schema, False, DOL_REF)
    for ref_key in ref_key_list:
        pointer = schema.get(ref_key)
        if isinstance(pointer, str):
            
            pointer_filtered = pointer.replace(POUND_SLASH, "") 
            if pointer_filtered in removed_keys:
                
                pointer_updated = pointer.replace(RES_WORD_TYPE, RES_WORD_TYPE_ALT) 
                schema[ref_key] = pointer_updated
                print("Reserved word found in ref and updated", pointer)  
            
    # Update required fields
    req_key_list = get_keys(schema, False, REQUIRED)
    for req_key in req_key_list:
        req_array = schema.get(req_key)
        if RES_WORD_TYPE in req_array:
            
            for index, req in enumerate(req_array):
                if req == RES_WORD_TYPE:
                    req_array[index] = RES_WORD_TYPE_ALT
                    schema[req_key] = req_array           
                    print("Reserved word found in required fields and updated", req_key) 
    
    return schema


def update_unique_items(schema: benedict, set_to: bool = False) -> benedict:
    """
    Looks for uniqueItems and updates them to the set_to bool provided. 

    Args:
        schema (benedict): JSON Schema

    Returns:
        benedict: JSON Schema with uniqueItems updated
    """

    keys_list = schema.keypaths(indexes=False)
    unique_items_key_list = [i for i in keys_list if i.endswith("uniqueItems")]
    
    for unique_items_key in unique_items_key_list:
        schema[unique_items_key] = set_to
    
    return schema


def adjust_patterns(schema: benedict) -> benedict:
    """
    Looks for regex patterns that don't jive with the data generator and 
    updates them with comparable patterns that the data generator is happy with. 

    Args:
        schema (benedict): JSON Schema

    Returns:
        benedict: JSON Schema with data gen safe patterns
    """

    keys_list = schema.keypaths(indexes=False)
    pattern_key_list = [i for i in keys_list if i.endswith("pattern")]
    
    for pattern_key in pattern_key_list:
        pattern = schema.get(pattern_key)    
        
        if pattern == DATETIME_TIMEZONE_ORIG:
            schema[pattern_key] = DATETIME_TIMEZONE_REVISED
            print("* datetime timezone pattern revised")
            
        if pattern == NCNAME_ORIG:
            schema[pattern_key] = NCNAME_REVISED
            print("* ncname pattern revised")
    
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
    schmea_reserved_words_updated = replace_reserved_words(schema)
    schmea_unique_items_updated = update_unique_items(schmea_reserved_words_updated)
    schmea_patterns_adjusted = adjust_patterns(schmea_unique_items_updated)
    schema_fixed_props = fix_root_ref(schmea_patterns_adjusted)
    schema_reqs_added = add_required_root_items(schema_fixed_props)
    schema_limited = limit_max_items(schema_reqs_added, limit)
    schema_encoding_fixed = find_fix_encoding(schema_limited)
    resolved_schema = find_update_refs(schema_encoding_fixed)    
    
    return resolved_schema

def validate_schema(schema: dict) -> str:
    result = "VALID"
    
    try:
        validate_schema(schema)
    except Exception as err:
        raise Exception(err)
    
    return result  
    

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