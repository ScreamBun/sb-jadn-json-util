import json
from unittest import TestCase
import unittest
from jadnjson.constants.generator_constants import TESTS_PATH

from jadnjson.generators.json_generator import find_refs, gen_data_from_schema, move_def_to_prop, resolve_inner_refs
from jadnjson.utils.general_utils import get_file


class Generators(TestCase):
  
    faker_test_schema = {}
    full_schema = {}
    sm_schema = {}
    alt_schmea = {}
    
    def setUp(self):
        faker_doc = get_file('faker_schema.json', TESTS_PATH)
        self.faker_test_schema = json.loads(faker_doc)
        
        full_schema_doc = get_file('full_schema.json', TESTS_PATH)
        self.full_schema = json.loads(full_schema_doc)
        
        sm_schema_doc = get_file('sm_schema.json', TESTS_PATH)
        self.sm_schema = json.loads(sm_schema_doc)
        
        alt_schema_doc = get_file('alt_schema.json', TESTS_PATH)
        self.alt_schema = json.loads(alt_schema_doc)        
        
    def test_gen_data_faker(self):
        g_data = gen_data_from_schema(self.faker_test_schema)
        
        print("----test gen data----")
        print(json.dumps(g_data, indent=4))
        assert g_data != None        
        
    def test_gen_data_sm(self):
        g_data = gen_data_from_schema(self.sm_schema)
        
        print("----test gen data----")
        print(json.dumps(g_data, indent=4))
        assert g_data != None
        
    def test_gen_data_full(self):
        g_data = gen_data_from_schema(self.alt_schema)
        
        print("----test gen data----")
        print(json.dumps(g_data, indent=4))        
        assert g_data != None        
        
    def test_resolve_inner_refs(self):
        resolved_1 = resolve_inner_refs(self.sm_schema)
        print("-- sm_schema --")
        print(resolved_1.dump())
        remaining_refs_1 = find_refs(resolved_1, False)
        
        resolved_2 = resolve_inner_refs(self.sm_schema_2)
        print("-- sm_schema_2 --")
        print(resolved_2.dump())
        remaining_refs_2 = find_refs(resolved_2, False)
        
        resolved_3 = resolve_inner_refs(self.sm_sample_schema)
        print("-- sm_sample_schema --")
        print(resolved_3.dump())
        remaining_refs_3 = find_refs(resolved_3, False)    
        
        resolved_4 = resolve_inner_refs(self.full_schmea)
        remaining_refs_4 = find_refs(resolved_4, False)
        print("-- full_schmea --")
        print(resolved_4.dump())        
        
        assert resolved_1 != None 
        assert len(remaining_refs_1) == 0
        assert resolved_2 != None 
        assert len(remaining_refs_2) == 0
        assert resolved_3 != None 
        assert len(remaining_refs_3) == 0
        assert resolved_4 != None 
        assert len(remaining_refs_4) == 0
        
        
    def test_move_def_to_prop(self):
      updated_schema = move_def_to_prop(self.full_schmea)
      print(updated_schema.dump())
      
      assert updated_schema != None 
      
    # def test_rand_gen_data(self):
    #   gen_data = gen_rand_data_from_schema(self.sm_sample_schema)
      
    #   print(json.dumps(gen_data))
    #   assert gen_data != None 
        
        
if __name__ == '__main__':
    unittest.main()
        