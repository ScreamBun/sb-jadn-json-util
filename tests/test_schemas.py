import json
from unittest import TestCase

from jadnjson.constants.generator_constants import TESTS_PATH
from jadnjson.utils.general_utils import get_file
from jadnjson.validators.schema_validator import validate_schema


class SchemaValidator(TestCase):

    resolved_hunt_schema = {}
    
    def setUp(self):
        resolved_hunt_doc = get_file('resolved_hunt_20240314.json', TESTS_PATH)
        self.resolved_hunt_schema = json.loads(resolved_hunt_doc)    

    def test_validate_schema(self):
        result = validate_schema(self.resolved_hunt_schema)
        
        test_result = None
        if isinstance(result, tuple):
            assert result[0] == True
            test_result = True
            
        assert test_result == True

        