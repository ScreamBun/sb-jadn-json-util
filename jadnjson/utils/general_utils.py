import json
import os

import benedict


def get_last_occurance(val: str, split_on: chr, lower: bool = False) -> str: 
    
    return_val = val
    if val and split_on in val:
        return_val = val.split(split_on)[-1]
    
        if lower:
            return_val = return_val.lower()
    
    return return_val

def get_file(file_name: str, relative_path: str) -> str:
    file_dir = os.path.dirname(os.path.realpath('__file__'))
    # print(file_dir)
    join_file_path = os.path.join(file_dir, '.' + relative_path + file_name)
    abs_file_path = os.path.abspath(os.path.realpath(join_file_path))  

    doc = None
    with open(abs_file_path, 'r') as f:
        doc = f.read()

    return doc

def get_last_instance(val: str, delimit: str) -> str:
    return_val = None
    if val:
        return_val = val.split(delimit)[-1]
    return return_val

def get_keys(schema: benedict, include_indexes: bool = False, ends_with: str = None) -> list:
    keys_list = schema.keypaths(indexes=include_indexes)
    filtered_key_list = [i for i in keys_list if i.endswith(ends_with)]    
    return filtered_key_list

def remove_chars(val_str: str, to_be_removed: str, num_of_chars: int) -> str:
    """
    Removes characters from a string

    Args:
        val_str (str): string to have characters removed
        to_be_removed (str): characters to be removed
        num_of_chars (int): number of charaters to be removed

    Returns:
        return (str): updated string with characters removed 
    """
    return_val = val_str
    if val_str and len(val_str) > 1 and to_be_removed == val_str[:num_of_chars]:
        return_val = val_str[num_of_chars:]
        
    return return_val

def write_to_file(json_data: dict, filename: str):
    
    data = None
    if isinstance(json_data, dict):
        data = json.dumps(json_data, indent=4)
    elif isinstance(json_data, benedict):
        data = json_data.dump()
    
    if data:
        file_dir = os.path.dirname(os.path.realpath('__file__'))
        join_file_path = os.path.join(file_dir, '_out/' + filename)
        abs_file_path = os.path.abspath(os.path.realpath(join_file_path))      
        
        with open(abs_file_path, "w") as json_file:
            json_file.write(data)
    else:
        raise "no data found"