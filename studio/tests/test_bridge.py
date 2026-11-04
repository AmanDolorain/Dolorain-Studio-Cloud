import json, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from server import build_prompt
class BridgeTests(unittest.TestCase):
    def test_named_widget_and_link(self):
        workflow={'nodes':[{'id':1,'type':'Source','mode':0,'inputs':[],'widgets_values_named':{'value':12}},{'id':2,'type':'Sink','mode':0,'inputs':[{'name':'x','link':5}]}],'links':[[5,1,0,2,0,'INT']]}
        schema={'Source':{'input':{'required':{'value':['INT',{}]}}},'Sink':{'input':{'required':{'x':['INT',{}]}}}}
        prompt, errors=build_prompt(workflow,schema)
        self.assertEqual(errors,[])
        self.assertEqual(prompt['2']['inputs']['x'],['1',0])
        self.assertEqual(prompt['1']['inputs']['value'],12)
    def test_h3_controller_widget_edit_and_wired_target_override(self):
        # Input socket links are authoritative even if a target has obsolete saved widget values.
        workflow={'nodes':[
          {'id':20,'type':'H3VideoController','mode':0,'inputs':[],
           'widgets_values_named':{'width':567,'height':768,'duration_seconds':3}},
          {'id':15,'type':'MiniMaxH3ReferenceToVideo','mode':0,
           'inputs':[{'name':'width','widget':{'name':'width'}},{'name':'height','widget':{'name':'height'}}],
           'widgets_values_named':{'width':1344,'height':768}}],
          'links':[[18,20,5,15,0,'INT'],[19,20,6,15,1,'INT']]}
        schemas={
          'H3VideoController':{'input':{'required':{'width':['INT',{}],'height':['INT',{}],'duration_seconds':['FLOAT',{}]}}},
          'MiniMaxH3ReferenceToVideo':{'input':{'required':{'width':['INT',{}],'height':['INT',{}]}}}}
        prompt,errors=build_prompt(workflow,schemas)
        self.assertEqual(errors,[])
        self.assertEqual(prompt['20']['inputs']['width'],567)
        self.assertEqual(prompt['15']['inputs']['width'],['20',5])
        self.assertEqual(prompt['15']['inputs']['height'],['20',6])
    def test_required_muted_source_is_reported(self):
        graph={'nodes':[{'id':1,'type':'Source','mode':4},{'id':2,'type':'Sink','inputs':[{'name':'width','link':2}]}],
               'links':[[2,1,0,2,0,'INT']]}
        schema={'Sink':{'input':{'required':{'width':['INT',{}]}}}}
        _,errors=build_prompt(graph,schema)
        self.assertTrue(any('muted source' in error for error in errors))
    def test_missing_node_type(self):
        _,errors=build_prompt({'nodes':[{'id':1,'type':'NotInstalled'}],'links':[]},{})
        self.assertIn('not installed',errors[0])
    def test_optional_muted_source_omitted(self):
        workflow={'nodes':[{'id':1,'type':'Source','mode':4},{'id':2,'type':'Sink','mode':0,'inputs':[{'name':'optional','link':2}]}],'links':[[2,1,0,2,0,'INT']]}
        schema={'Sink':{'input':{'optional':{'optional':['INT',{}]}}}}
        prompt,errors=build_prompt(workflow,schema)
        self.assertEqual(errors,[])
        self.assertEqual(prompt['2']['inputs'],{})
if __name__=='__main__':unittest.main()
