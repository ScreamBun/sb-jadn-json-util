import json
from unittest import TestCase
import unittest
from jadnjson.constants.generator_constants import TESTS_PATH

from jadnjson.generators.json_generator import find_update_refs, gen_data_from_schema, resolve_inner_refs
from jadnjson.utils.general_utils import get_file


class Generators(TestCase):
  
    faker_schema = {}
    sm_schema = {}
    alt_schmea = {}
    full_schema = {}
    oc2ls_schema = {}
    
    def setUp(self):
        faker_doc = get_file('faker_schema.json', TESTS_PATH)
        self.faker_schema = json.loads(faker_doc)
        
        sm_schema_doc = get_file('sm_schema.json', TESTS_PATH)
        self.sm_schema = json.loads(sm_schema_doc)
        
        alt_schema_doc = get_file('alt_schema.json', TESTS_PATH)
        self.alt_schema = json.loads(alt_schema_doc)        
        
        full_schema_doc = get_file('full_schema.json', TESTS_PATH)
        self.full_schema = json.loads(full_schema_doc)
        
        oc2ls_schema_doc = get_file('oc2ls_1.0.1_schema.json', TESTS_PATH)
        self.oc2ls_schema = json.loads(oc2ls_schema_doc)                
        
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
        
    def test_gen_data_full(self):
        g_data = gen_data_from_schema(self.full_schema)
        
        print("----test gen data----")
        print(json.dumps(g_data, indent=4))        
        assert g_data != None
        
    def test_gen_data_oc2ls(self):
      
        # TODO: Leftoff here, recurrision issues in ocs2l schemas.
        # Process object has $ref called Process, which creates an infinite loop.
        # May need to check for this and remove/ignore/warn where the parent name 
        # equals an inner $ref definition/value  
        # ocs2ls copy still has the looping issue
      
        g_data = gen_data_from_schema(self.oc2ls_schema)
        
        print("----test gen data----")
        print(json.dumps(g_data, indent=4))        
        assert g_data != None            
        
    def test_resolve_inner_refs(self):
        resolved_1 = resolve_inner_refs(self.faker_schema)
        print("-- sm_schema --")
        print(resolved_1.dump())
        remaining_refs_1 = find_update_refs(resolved_1, False)
        
        resolved_2 = resolve_inner_refs(self.sm_schema)
        print("-- sm_schema_2 --")
        print(resolved_2.dump())
        remaining_refs_2 = find_update_refs(resolved_2, False)
        
        resolved_3 = resolve_inner_refs(self.alt_schema)
        print("-- sm_sample_schema --")
        print(resolved_3.dump())
        remaining_refs_3 = find_update_refs(resolved_3, False)    
        
        resolved_4 = resolve_inner_refs(self.full_schema)
        remaining_refs_4 = find_update_refs(resolved_4, False)
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
        
        
if __name__ == '__main__':
    unittest.main()
        