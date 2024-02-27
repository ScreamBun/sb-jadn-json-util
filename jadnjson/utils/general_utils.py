import os


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