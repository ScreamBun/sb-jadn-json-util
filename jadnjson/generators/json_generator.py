import json
from random import randrange
import time
from benedict import benedict
from jsf import JSF
import jsonpointer

from jadnjson.constants import generator_constants
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
                
                if "definitions/" in k:
                   k = k.replace("definitions/", "")
                   
                if "properties/" in k:
                   k = k.replace("properties/", "")
                        
                choices_found_dict[k] = value
            elif max_prop_val == 1:
                
                if "definitions/" in k:
                   k = k.replace("definitions/", "")
                   
                if "properties/" in k:
                   k = k.replace("properties/", "")
                        
                choices_found_dict[k] = value                
                
            
    return choices_found_dict


def find_fix_encoding(key: str, schema: benedict) -> benedict:
    """
    Some JADN specific encoding does not get converted to a JSON Schema equivalent during JSON Schema translation. 
    This logic attempts to map JADN encoding to JSON Schema valid encoding.  Eventually this needs to be fixed 
    in the JADN to JSON Schema Translation logic.  
    """
        
    encoding_type = schema.get(key)
    if isinstance(encoding_type, benedict):       
        return schema
        
    elif generator_constants.CONTENT_ENCODING in key:
        new_encoding_type = None
        
        match encoding_type:
            case generator_constants.BASE_64_URL:
                new_encoding_type = generator_constants.BASE_64
            case generator_constants.BASE64:
                new_encoding_type = generator_constants.BASE_64
            case generator_constants.BASE_64:
                new_encoding_type = generator_constants.BASE_64                    
            case generator_constants.BASE32:
                new_encoding_type = generator_constants.BASE_32
            case generator_constants.BASE16:
                new_encoding_type = generator_constants.BASE_16
            case _:
                print(f"encoding type not known {encoding_type}")
                
        if new_encoding_type:
            schema[key] = new_encoding_type
    
    return schema


def is_recursion_found(data: benedict, key: str, pointer: str) -> bool:  
    """
    Attempts to detect recursion within inner ref data.  The logic looks at parent keys,
    child keys and child ref keys.  More detection maybe needed, or renaming...
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
        pointer_keys = pointer_data.keypaths(indexes=True)
        inner_refs = [i for i in pointer_keys if generator_constants.DOL_REF in i]
        
        parent_keys = key.split('/')
        parent_keys = list(map(str.lower, parent_keys))

        # Must be more than one, because the pointer resolve could contian the pointer name    
        if parent_keys.count(pointer_name) > 1:
            recursion_found = True
            
        # elif pointer_keys.count(pointer_name) >= 1:
        #     recursion_found = True        
            
        elif inner_refs:
            
            for inner_ref in inner_refs:
                inner_pointer_path = pointer_data.get(inner_ref)
                innner_pointer_name = get_last_occurance(inner_pointer_path, '/', True)
                if innner_pointer_name in parent_keys:
                    recursion_found = True
                    break        
        
    return recursion_found


def update_inner_refs(schema: dict | benedict) -> benedict:
    """
    Searches the json schema for inner $refs and updates them with their actual values. 
    Attempts to detect recursion in refs.  If recursion is found, then that item is removed
    from the JSON Schema used for data generation.  Otherwise the data generation hits an endless loop.  
    """
    
    keys_list = schema.keypaths(indexes=True)
    ref_key_list = [i for i in keys_list if i.endswith(generator_constants.DOL_REF)]
    for ref_key in ref_key_list:
        pointer = schema.get(ref_key)
        
        if isinstance(pointer, str) and generator_constants.POUND in pointer:
            pointer_updated = pointer.replace(generator_constants.POUND, "")                
            ref_key_updated = ref_key.replace(generator_constants.SLASH_DOL_REF, "")
            
            recursion_found = is_recursion_found(schema, ref_key_updated, pointer_updated)
            if recursion_found:
                print("warning: recursion found, removing for generation: ", ref_key_updated)
                del schema[ref_key_updated]                 
            else:
                resolved_data = jsonpointer.JsonPointer(pointer_updated).resolve(schema)
                schema[ref_key_updated] = resolved_data
                                     
    return schema


def limit_max_items(key: str, schema: benedict, max_items: int = 3, max_length: int = 25) -> benedict:
    """
    Searches for type Array and then, adds a limit (default 3) to help 
    reduce the amount of mock data generated.  If nothing is provided then
    the data generated has no limit and takes awhile to generate data. 
    """
        
    if key.endswith(generator_constants.MAX_ITEMS):          
        max_val = schema.get(key)      
        if max_val > max_items:
            schema[key] = max_items
            print(f"{key} maxItems updated, {max_val} => {max_items}")
            
    if key.endswith(generator_constants.MAX_LENGTH):          
        max_val = schema.get(key)
        if max_val > max_length:
            schema[key] = max_length
            print(f"{key} maxLength updated, {max_val} => {max_length}")            
    
    if key.endswith(generator_constants.MIN_ITEMS):        
        min_val = schema.get(key)
        if min_val > max_items:
            schema[key] = max_items
            print(f"{key} minItems updated, was {max_val} => {max_items}")
            
    if key.endswith(generator_constants.MIN_LENGTH):        
        min_val = schema.get(key)
        if min_val > max_length:
            schema[key] = max_length
            print(f"{key} minLength updated, was {max_val} => {max_length}")         
    
    return schema

def add_required_root_items(schema: benedict) -> benedict:
    """
    Adds a required item to root if one does not exist.  Otherwise the 
    data generator may return nothing. 
    """

    if not schema.get(generator_constants.REQUIRED):

        properties = schema.get(generator_constants.PROPERTIES)
        definitions = schema.get(generator_constants.DEFINITIONS)
        reqs = []
        
        if properties:
            prop_list = properties.keypaths(indexes=False)
            
            for prop in prop_list:
                if "/" not in prop:
                    reqs.append(prop)         
            
            required = schema.get(generator_constants.REQUIRED)
            if not required:
                schema[generator_constants.REQUIRED] = reqs
                
        elif definitions:
            defi = definitions.keypaths(indexes=False)[0]
            reqs.append(defi)              
            
            required = schema.get(generator_constants.REQUIRED)
            if not required:
               schema[generator_constants.REQUIRED] = reqs        
            
                
    return schema


def fix_root_ref(schema: benedict) -> benedict:
    """
    Some JSON Schemas contain a single root level $ref, no properties and definitions.
    The data generator has trouble with these, so to be consistant, this function
    creates the missing properties object based on the single root $ref.
    """
    
    root_ref = schema.get(generator_constants.DOL_REF)
    properties = schema.get(generator_constants.PROPERTIES)
    type = schema.get(generator_constants.TYPE)
    additionalProperties = schema.get(generator_constants.ADDITIONAL_PROPS)
    
    # May need to move to its own function and update url based on draft version
    schema[generator_constants.SCHEMA_KEY] = generator_constants.SCHEMA_URL
     
    if root_ref and not properties:
        root_name = get_last_occurance(root_ref, "/", False)
        new_props_path = generator_constants.PROPERTIES + "/" + root_name + "/" + generator_constants.DOL_REF
        
        schema[new_props_path] = root_ref
        del schema[generator_constants.DOL_REF]

        if not type:
            schema[generator_constants.TYPE] = generator_constants.OBJECT
            
        if not additionalProperties:
            schema[generator_constants.ADDITIONAL_PROPS] = False
    
    return schema

def replace_reserved_words(key: str, schema: benedict) -> benedict:
    """
    Looks for revered words and sets them to an alternate name.
    """

    # Update Keys
    removed_keys = []
    if get_last_occurance(key, '/') == generator_constants.RES_WORD_TYPE:
        copy_obj = schema.get(key)
        copy_obj_key = key.replace(generator_constants.RES_WORD_TYPE, generator_constants.RES_WORD_TYPE_ALT)
        schema[copy_obj_key] = copy_obj
        del schema[key]
        removed_keys.append(key)
        print(f"{key} Reserved word replaced {generator_constants.RES_WORD_TYPE} => {generator_constants.RES_WORD_TYPE_ALT}")
        
    if removed_keys:
        # Update ref pointers
        ref_key_list = get_keys(schema, False, generator_constants.DOL_REF)
        for ref_key in ref_key_list:
            pointer = schema.get(ref_key)
            if isinstance(pointer, str):
                
                pointer_filtered = pointer.replace(generator_constants.POUND_SLASH, "") 
                if pointer_filtered in removed_keys:
                    
                    pointer_updated = pointer.replace(generator_constants.RES_WORD_TYPE, generator_constants.RES_WORD_TYPE_ALT) 
                    schema[ref_key] = pointer_updated
                    print("Reserved word found in ref and updated", pointer)  
                
        # Update required fields
        req_key_list = get_keys(schema, False, generator_constants.REQUIRED)
        for req_key in req_key_list:
            req_array = schema.get(req_key)
            if generator_constants.RES_WORD_TYPE in req_array:
                
                for index, req in enumerate(req_array):
                    if req == generator_constants.RES_WORD_TYPE:
                        req_array[index] = generator_constants.RES_WORD_TYPE_ALT
                        schema[req_key] = req_array           
                        print("Reserved word found in required fields and updated", req_key)         
        
    return schema


def update_unique_items(key: str, schema: benedict, set_to: bool = False) -> benedict:
    """
    Looks for uniqueItems and updates them to the set_to bool provided. 
    """
    
    if key.endswith("uniqueItems"):
        schema[key] = set_to
    
    return schema


def adjust_patterns(key: str, schema: benedict) -> benedict:
    """
    Looks for regex patterns that don't jive with the data generator and 
    updates them with comparable patterns that the data generator is happy with. 
    """
    
    if key.endswith("pattern"):  
       
        pattern = schema.get(key)    
        
        if pattern == generator_constants.DATETIME_TIMEZONE_ORIG:
            schema[key] = generator_constants.DATETIME_TIMEZONE_REVISED
            print(f"{key} pattern revised {pattern} => {generator_constants.DATETIME_TIMEZONE_REVISED}")
            
        if pattern == generator_constants.NCNAME_ORIG:
            schema[key] = generator_constants.NCNAME_REVISED
            print(f"{key} pattern revised {pattern} => {generator_constants.NCNAME_REVISED}")
    
    return schema

def determine_max_items(num_of_keys: int) -> int:
    # Note, the numbers below may need to be adjusted or smarter....
    # They significantly impact the size of the data generated.
    max = 1
    
    if num_of_keys < 10000 and num_of_keys >= 5000:
        max = 2
    elif num_of_keys < 5000 and num_of_keys >= 1000:
        max = 3
    elif num_of_keys < 1000:
        max = 4
    
    return max


def cleanup_schema_for_data_gen(schema: str | dict | benedict) -> {benedict, dict}:
    """
    Searches the json schema for inner refs ($ref) and replaces them with their actual values.  
    In other words, resovling the references.  Attempts to detect recursion and skips it if found.
    """
    
    if isinstance(schema, str):
        schema = json.loads(schema)
    
    if isinstance(schema, dict):
        schema = benedict(schema, keypath_separator="/")
    
    fix_root_ref(schema)
    add_required_root_items(schema)
    # update_inner_refs(schema)
    # replace_reserved_words(schema) # May need to be optimized
    
    keys_list = schema.keypaths(indexes=False)
    num_of_keys = len(keys_list)
    print(f'Number of keys to process: {str(num_of_keys)}')
    proposed_max_items = determine_max_items(num_of_keys)
    print(f'Proposed max items: {str(proposed_max_items)}')
    
    for key in keys_list:
        # print(f'{key}')
        
        if key.startswith("definitions/"):
                
            val = schema.get(key) 
            if key is None:
                print(f"NoneType found!!! {key}")
            elif val is None:
                print(f"NoneType val found!!! {key}")
            else:
                try:
                    # TODO: Temporarily disbled, poor peroforance with larger schemas 
                    # replace_reserved_words(key, schema)
                    update_unique_items(key, schema)
                    adjust_patterns(key, schema)
                    limit_max_items(key, schema, max_items=proposed_max_items)
                    find_fix_encoding(key, schema)
                except Exception as err:
                    print(f'key: {key}')                
                    print("error cleaning up json schema: ", err)
                    raise Exception(err)

    # TODO: Temporarily disbled, poor peroforance with larger schemas 
    # choices_found_dict = find_choices(resolved_schema)
    choices_found_dict = None
    
    update_inner_refs(schema)
    
    return schema, choices_found_dict
    

def gen_fake_data(schema: dict) -> json:
    print("gen_fake_data")
    
    fake_data_json = {}
    
    i = 0
    lim = 6
    while i < lim:
          
        try:   
            faker = JSF(schema)                
            fake_data_json = faker.generate()
            
            if not fake_data_json:
                i += 1
                time_to_wait = i * .3
                time.sleep(time_to_wait)                
                print("no data, trying again....")
            else:
                for value in fake_data_json.values():
                    if not value:
                        i += 1
                        time_to_wait = i * .3
                        time.sleep(time_to_wait)
                    else:
                        print("data generated")
                        i = lim
                        break                        
                
        except Exception as err:
            i = lim
            # print('--------------------')
            # print('schema:')
            # print(schema)
            # print('--------------------')
            print("error attempting to gen fake data: ", err)
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
                    randomized_key = randrange(0, len(choice_list))
                    select_choice_opt_key = choice_list[randomized_key]
                    select_choice_opt_data = choice_data.get(select_choice_opt_key)
                    
                    # Clear out all choice options
                    for choice_opt_key in choice_data.copy():
                        del choice_data[choice_opt_key]
                        
                    # Reset choice with 1st choice option only
                    choice_data[select_choice_opt_key] = select_choice_opt_data
                    
    return fake_data_bene
    

def gen_data_from_schema(schema: dict) -> ReturnVal:
    """
    Generates fake data based on the schema
    """
    
    ret_val = ReturnVal()

    # Validate before changes
    # try:
    #     validate_schema(schema)
    # except Exception as err:
    #     ret_val.err_msg = err
    #     return ret_val
    
    schema_bene, choices_found = cleanup_schema_for_data_gen(schema)
    
    schema_json = schema_bene.to_json()
    schema_dict = json.loads(schema_json)
    
    # write_filename = "test_schema.json"
    # write_file('./', write_filename, schema_json)
    # print(f"schema writtern to file {write_filename}")
    
    # Validate after changes
    try:
        validate_schema(schema)
    except Exception as err:
        ret_val.err_msg = err
        return ret_val    
    
    fake_data = gen_fake_data(schema)
    # fake_data = cleanup_choices(fake_data, choices_found)
    ret_val.gen_data = fake_data

    return ret_val