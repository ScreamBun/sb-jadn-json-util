import json
from unittest import TestCase

from jadnjson.constants.generator_constants import TESTS_PATH
from jadnjson.utils.general_utils import get_file
from jadnjson.validators.schema_validator import validate_schema


class Test_SchemaValidator(TestCase):

    alt_schema = {}
    mapOf_strings_schema = {}
    mapOf_nonstrings_schema = {}
    
    def setUp(self):
        alt_schema = get_file('alt_schema.json', TESTS_PATH)
        self.alt_schema = json.loads(alt_schema)
        
        mapOf_strings_schema = get_file('mapOf_strings_schema.json', TESTS_PATH)
        self.mapOf_strings_schema = json.loads(mapOf_strings_schema) 
        
        mapOf_nonstrings_schema = get_file('mapOf_nonstrings_schema.json', TESTS_PATH)
        self.mapOf_nonstrings_schema = json.loads(mapOf_nonstrings_schema)                     


    def test_validate_alt_schema(self):
        result = validate_schema(self.alt_schema)
        
        test_result = None
        if isinstance(result, tuple):
            assert result[0] == True
            test_result = True
            
        assert test_result == True
        
        
    def test_validate_mapOf_strings_schema(self):
        result = validate_schema(self.mapOf_strings_schema)
        
        test_result = None
        if isinstance(result, tuple):
            assert result[0] == True
            test_result = True
            
        assert test_result == True   
        
        
    def test_validate_mapOf_nonstrings_schema(self):
        result = validate_schema(self.mapOf_nonstrings_schema)
        
        test_result = None
        if isinstance(result, tuple):
            assert result[0] == True
            test_result = True
            
        assert test_result == True                

        