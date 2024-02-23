import json
from unittest import TestCase
import unittest
from jadnjson.constants.generator_constants import TESTS_PATH

from jadnjson.generators.json_generator import gen_data_from_schema
from jadnjson.utils.general_utils import get_file


class Generators(TestCase):
  
    faker_schema = {}
    sm_schema = {}
    alt_schmea = {}
    music_schema = {}
    full_schema = {}
    oc2ls1_0_1_schema = {}
    oc2ls1_1_0_schema = {}
    
    def setUp(self):
        faker_doc = get_file('faker_schema.json', TESTS_PATH)
        self.faker_schema = json.loads(faker_doc)
        
        sm_schema_doc = get_file('sm_schema.json', TESTS_PATH)
        self.sm_schema = json.loads(sm_schema_doc)
        
        alt_schema_doc = get_file('alt_schema.json', TESTS_PATH)
        self.alt_schema = json.loads(alt_schema_doc)
        
        music_schema_doc = get_file('music_schema.json', TESTS_PATH)
        self.music_schema = json.loads(music_schema_doc)               
        
        full_schema_doc = get_file('full_schema.json', TESTS_PATH)
        self.full_schema = json.loads(full_schema_doc)
        
        oc2ls_schema_1_0_1_doc = get_file('oc2ls_1.0.1_schema.json', TESTS_PATH)
        self.oc2ls1_0_1_schema = json.loads(oc2ls_schema_1_0_1_doc)
        
        oc2ls_schema_1_1_0_doc = get_file('oc2ls_1.1.0_schema.json', TESTS_PATH)
        self.oc2ls1_1_0_schema = json.loads(oc2ls_schema_1_1_0_doc)                    
        
    def test_gen_data_faker(self):
        g_data = gen_data_from_schema(self.faker_schema)
        
        print("----test gen data----")
        print(json.dumps(g_data, indent=4))
        assert g_data != None        
        
    def test_gen_data_sm(self):
        g_data = gen_data_from_schema(self.sm_schema)
        
        print("----test gen data----")
        print(json.dumps(g_data, indent=4))
        assert g_data != None
        
    def test_gen_data_music(self):
        g_data = gen_data_from_schema(self.music_schema)
        
        print("----test gen data----")
        print(json.dumps(g_data, indent=4))
        assert g_data != None        
        
    def test_gen_data_full(self):
        g_data = gen_data_from_schema(self.full_schema)
        
        print("----test gen data----")
        print(json.dumps(g_data, indent=4))        
        assert g_data != None
        
    def test_gen_data_alt(self):
        g_data = gen_data_from_schema(self.alt_schema)
        
        print("----test gen data----")
        print(json.dumps(g_data, indent=4))        
        assert g_data != None        
        
    def test_gen_data_oc2ls_1_0_1(self):
      
        g_data = gen_data_from_schema(self.oc2ls1_0_1_schema)
        
        print("----test gen data----")
        print(json.dumps(g_data, indent=4))        
        assert g_data != None           
        
    def test_gen_data_oc2ls_1_1_0(self):
      
        # Note: Process object has $ref called Process, which creates an infinite loop.
        # Removing recursion items for now, until a better approach can be established.
      
        g_data = gen_data_from_schema(self.oc2ls1_1_0_schema)
        
        print("----test gen data----")
        print(json.dumps(g_data, indent=4))        
        assert g_data != None            
        
        
if __name__ == '__main__':
    unittest.main()
        