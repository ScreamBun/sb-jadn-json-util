import json
from random import randrange
import time
from tracemalloc import start
from xml.etree.ElementTree import tostring
from benedict import benedict
from jsf import JSF
from faker import Faker
import jsonpointer

from jadnjson.constants import generator_constants
from jadnjson.constants.generator_constants import ADDITIONAL_PROPS, BASE_16, BASE_32, BASE_64, CONTENT_ENCODING, DATETIME_TIMEZONE_ORIG, DATETIME_TIMEZONE_REVISED, DEFINITIONS, DOL_REF, MAX_ITEMS, MIN_ITEMS, NCNAME_ORIG, NCNAME_REVISED, OBJECT, POUND, POUND_SLASH, PROPERTIES, REQUIRED, RES_WORD_TYPE, RES_WORD_TYPE_ALT, SLASH_DOL_REF, TYPE
from jadnjson.utils.general_utils import get_keys, get_last_occurance, remove_chars
from jadnjson.validators.schema_validator import validate_schema


class ReturnVal: 
    def __init__(self): 
        self.gen_data = None
        self.err_msg = None


def find_choices(bene_schema: benedict) -> dict:
    choices_found_dict = {}
    keys = bene_schema.keypaths(True)
    
    for k in keys:
        
        value = bene_schema.get(k)
        if isinstance(value, benedict):
            
            min_prop_val = value.get('minProperties')
            max_prop_val = value.get('maxProperties')
            
            if min_prop_val == 1 and max_prop_val == 1:
                # print("choice found, capturing for later")
                
                if "definitions/" in k:
                   k = k.replace("definitions/", "")
                   
                if "properties/" in k:
                   k = k.replace("properties/", "")
                        
                choices_found_dict[k] = value
            elif max_prop_val == 1:
                # print("choice found, capturing for later")
                
                if "definitions/" in k:
                   k = k.replace("definitions/", "")
                   
                if "properties/" in k:
                   k = k.replace("properties/", "")
                        
                choices_found_dict[k] = value                
                
            
    return choices_found_dict


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
    
    keys_list = data.keypaths(indexes=True)
    for key in keys_list:
        
        value = data.get(key)
        if isinstance(value, benedict):
            find_fix_encoding(value)            
            
        elif CONTENT_ENCODING in key:
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
    
    if pointer_data == None:
        print('pointer_data == None')
    elif not isinstance(pointer_data, benedict):
        print('not isinstance(pointer_data, benedict)')        
    else:
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


def resolve_inner_refs(schema: str | dict | benedict) -> {benedict, dict}:
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
    schema_reserved_words_updated = replace_reserved_words(schema)
    schema_unique_items_updated = update_unique_items(schema_reserved_words_updated)
    schema_patterns_adjusted = adjust_patterns(schema_unique_items_updated)
    schema_fixed_props = fix_root_ref(schema_patterns_adjusted)
    schema_reqs_added = add_required_root_items(schema_fixed_props)
    schema_limited = limit_max_items(schema_reqs_added, limit)
    schema_encoding_fixed = find_fix_encoding(schema_limited)
    resolved_schema = find_update_refs(schema_encoding_fixed) 
    
    choices_found_dict = find_choices(resolved_schema)   
    
    return resolved_schema, choices_found_dict


def get_all_keys(d):
    for key, value in d.items():
        yield key
        if isinstance(value, dict):
            yield from get_all_keys(value)
        else:
            if isinstance(value, str) and "base64url" in value:
                print(key)
    
                
def build_missing_data(data_schema: dict) -> benedict:
    fake = Faker()
    obj_name = None
    data_name = None
    data_val = None
    
    for data_k, data_val in data_schema.items():
        obj_name = data_k
        
        if data_k == "properties":
        
            for prop_k, prop_val in data_val.items():
                
                data_name = prop_k
                
                for inner_prop_k, inner_prop_val in prop_val.items():
            
                    if inner_prop_k == "type":
                        data_type = inner_prop_val
                        
                        if data_type == "string":
                            
                            data_max = None
                            if inner_prop_k == "maxLength":
                                data_max = inner_prop_val                
                            
                            data_val = fake.pystr(max_chars=data_max)
                        elif data_type == "number":
                            
                            data_min = 0
                            if inner_prop_k == "minimum":
                                data_min = inner_prop_val
                                
                            data_max = 9999
                            if inner_prop_k == "maximum":
                                data_max = inner_prop_val
                                
                            if inner_prop_k == "exclusiveMinimum":
                                data_min = inner_prop_val
                                
                            if inner_prop_k == "exclusiveMaximum":
                                data_max = inner_prop_val                                                                           
                            
                            data_val = fake.pyint(min_value=data_min, max_value=data_max)
                    
                    
    if data_name == None:
        ret_val = {}
    else:            
        ret_val = {data_name : data_val}
        
    return ret_val

def gen_fake_data(schema_dict: dict) -> json:

    # print(schema_dict)
    
    fake_data_json = {}
    
    i = 0
    lim = 6
    while i < lim:
          
        try:   
            # time.sleep(2.0)
            faker = JSF(schema_dict)
            
            # Attempt at threading...
            # faker = await JSF(schema_dict)
            # yield faker              
                
            fake_data_json = faker.generate()
            # print(str(fake_data_json))
            
            # Attempt at threading...
            # fake_data_json = await faker.generate()
            # yield fake_data_json
            
            if not fake_data_json:
                i += 1
                time_to_wait = i * .3
                time.sleep(time_to_wait)                
                print("data missing")
            else:
                for value in fake_data_json.values():
                    if not value:
                        i += 1
                        time_to_wait = i * .3
                        time.sleep(time_to_wait)
                    else:
                        print("value found")
                        i = lim
                        break                        
                
        except Exception as err:
            
            if i < lim:
                i += 1
                print("error attempting to gen fake data: ", err)
                print(f"data gen attempt {i}, trying again")
                time_to_wait = i * .3
                time.sleep(time_to_wait)           
            else:
                raise Exception(err)
            
    return fake_data_json 


def cleanup_choices(fake_data: dict, choices_found: dict) -> benedict:
    fake_data_bene = benedict(fake_data, keypath_separator="/")
    fake_data_bene.clean(strings=True, collections=True)
            
    if choices_found and len(choices_found) > 0:
        
        for choice_key in choices_found.copy():
            
            # Get choice data
            choice_data = fake_data_bene.get(choice_key)

            if choice_data != None:
                
                if len(choice_data) > 0:
                    # Remove 'extra' choices, to fix a jsf data gen bug
                
                    # Get a randomized choice option
                    choice_list = list(choice_data.keys())
                    # print(choice_list)
                    randomized_key = randrange(0, len(choice_list))
                    # print(randomized_key)
                    select_choice_opt_key = choice_list[randomized_key]
                    # print(choice_data)
                    select_choice_opt_data = choice_data.get(select_choice_opt_key)
                    # print("selected choice option at key "+ str(select_choice_opt_key))
                    
                    # Clear out all choice options
                    for choice_opt_key in choice_data.copy():
                        del choice_data[choice_opt_key]
                        
                    # Reset choice with 1st choice option only
                    choice_data[select_choice_opt_key] = select_choice_opt_data
                    
    return fake_data_bene
    

def gen_data_from_schema(schema: dict) -> ReturnVal:
    """
    Generates fake data based on the schema

    Args:
        schema (str): JSON Schema

    Returns:
        str: Fake generated data based on the JSON Schema
    """
    ret_val = ReturnVal()

    # Validate before changes
    try:
        validate_schema(schema)
    except Exception as err:
        ret_val.err_msg = err
        return ret_val
        # raise Exception(err) 
    
    schema_bene, choices_found = resolve_inner_refs(schema)
    
    schema_json = schema_bene.to_json()
    schema_dict = json.loads(schema_json)
    
    # Validate after adjustments for 3rd party acceptance
    try:
        validate_schema(schema_dict)
    except Exception as err:
        ret_val.err_msg = err
        return ret_val
        # raise Exception(err)
    
    fake_data = gen_fake_data(schema_dict)
    fake_data = cleanup_choices(fake_data, choices_found)
    ret_val.gen_data = fake_data

    return ret_val