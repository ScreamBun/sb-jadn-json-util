import json
from unittest import TestCase
import unittest
from jadnjson.constants.generator_constants import TESTS_PATH

from jadnjson.generators.json_generator import gen_data_from_schema, resolve_inner_refs
from jadnjson.utils.general_utils import get_file, write_to_file


class Test_Generators(unittest.TestCase):
  
    faker_schema = {}
    sm_schema = {}
    alt_schmea = {}
    music_schema = {}
    full_schema = {}
    oc2ls1_0_1_schema = {}
    oc2ls1_1_0_schema = {}
    oscal_ap_schema = {}
    oscal_ar_schema = {}
    oscal_catalog_schema = {}
    oscal_component_schema = {}
    oscal_poam_schema = {}
    oscal_profile_schema = {}
    oscal_ssp_schema = {}
    
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

        oscal_ap_schema_doc = get_file('oscal_ap_schema.json', TESTS_PATH)
        self.oscal_ap_schema = json.loads(oscal_ap_schema_doc)
        
        oscal_ar_schema_doc = get_file('oscal_ar_schema.json', TESTS_PATH)
        self.oscal_ar_schema = json.loads(oscal_ar_schema_doc)        
        
        oscal_catalog_schema_doc = get_file('oscal_catalog_schema.json', TESTS_PATH)
        self.oscal_catalog_schema = json.loads(oscal_catalog_schema_doc) 
        
        oscal_component_schema_doc = get_file('oscal_component_definition_schema.json', TESTS_PATH)
        self.oscal_component_schema = json.loads(oscal_component_schema_doc)
        
        oscal_poam_schema_doc = get_file('oscal_poam_schema.json', TESTS_PATH)
        self.oscal_poam_schema = json.loads(oscal_poam_schema_doc)
        
        oscal_profile_schema_doc = get_file('oscal_profile_schema.json', TESTS_PATH)
        self.oscal_profile_schema = json.loads(oscal_profile_schema_doc)
        
        oscal_ssp_schema_doc = get_file('oscal_ssp_schema.json', TESTS_PATH)
        self.oscal_ssp_schema = json.loads(oscal_ssp_schema_doc)                
        
    def test_gen_data_faker(self):
        g_data = gen_data_from_schema(self.faker_schema)
        
        print("----test faker gen data----")
        print(json.dumps(g_data, indent=4))
        assert g_data != None        
        
    def test_gen_data_sm(self):
        g_data = gen_data_from_schema(self.sm_schema)
        
        print("----test oc2 sm gen data----")
        print(json.dumps(g_data, indent=4))
        assert g_data != None
        
    def test_gen_data_music(self):
        g_data = gen_data_from_schema(self.music_schema)
        
        print("----test music gen data----")
        print(json.dumps(g_data, indent=4))
        assert g_data != None        
        
    def test_gen_data_full(self):
        g_data = gen_data_from_schema(self.full_schema)
        
        print("----test oc2 full gen data----")
        print(json.dumps(g_data, indent=4))        
        assert g_data != None
        
    def test_gen_data_alt(self):
        g_data = gen_data_from_schema(self.alt_schema)
        
        print("----test alt gen data----")
        print(json.dumps(g_data, indent=4))        
        assert g_data != None                 
        
    def test_gen_data_oc2ls_1_0_1(self):
        g_data = gen_data_from_schema(self.oc2ls1_0_1_schema)
        
        print("----test oc2ls_1_0_1 gen data----")
        print(json.dumps(g_data, indent=4))        
        assert g_data != None           
        
    def test_gen_data_oc2ls_1_1_0(self):
        g_data = gen_data_from_schema(self.oc2ls1_1_0_schema)
        
        # write_filename = "mock_data.json"
        # write_to_file(g_data, write_filename)         
        
        print("----test gen data----")
        print(json.dumps(g_data, indent=4))        
        assert g_data != None
        
    def test_gen_data_oscal_ap(self):
        g_data = gen_data_from_schema(self.oscal_ap_schema)
        
        print("----test gen data----")
        print(json.dumps(g_data, indent=4))        
        assert g_data != None 
        
    def test_gen_data_oscal_ar(self):
        g_data = gen_data_from_schema(self.oscal_ar_schema)
        
        write_filename = "mock_data.json"
        write_to_file(g_data, write_filename)            
        
        print("----test gen data----")
        print(json.dumps(g_data, indent=4))        
        assert g_data != None
        
    def test_gen_data_oscal_catalog(self):
        g_data = gen_data_from_schema(self.oscal_catalog_schema)
        
        print("----test catalog gen data----")
        print(json.dumps(g_data, indent=4))        
        assert g_data != None         
        
    def test_gen_data_oscal_component(self):
        g_data = gen_data_from_schema(self.oscal_component_schema)
        
        print("----test component gen data----")
        print(json.dumps(g_data, indent=4))        
        assert g_data != None
        
    def test_gen_data_oscal_poam(self):
        g_data = gen_data_from_schema(self.oscal_poam_schema)
        
        print("----test poam gen data----")
        print(json.dumps(g_data, indent=4))        
        assert g_data != None
        
    def test_gen_data_oscal_profile(self):
        g_data = gen_data_from_schema(self.oscal_profile_schema)
        
        print("----test profile gen data----")
        print(json.dumps(g_data, indent=4))        
        assert g_data != None
        
    def test_gen_data_oscal_ssp(self):
        g_data = gen_data_from_schema(self.oscal_ssp_schema)
        
        print("----test ssp gen data----")
        print(json.dumps(g_data, indent=4))        
        assert g_data != None
        
    def test_resolve_inner_refs(self):
        resolved_schema = resolve_inner_refs(self.oc2ls1_1_0_schema)
        
        write_filename = "resolved_schema.json"
        write_to_file(resolved_schema, write_filename) 
        
        assert resolved_schema != None                  
        
if __name__ == '__main__':
    unittest.main()
        