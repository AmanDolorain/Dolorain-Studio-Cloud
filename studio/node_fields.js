// The workflow stores widget values separately from its connection sockets.
let graphSchemas={};
const h3PresetNames=['Custom', 'Square 128 x 128', 'Square 256 x 256', 'Square 512 x 512', 'Square 640 x 640', 'Square 768 x 768', 'Square 1024 x 1024', 'Landscape 640 x 352', 'Landscape 864 x 480', 'Portrait 480 x 864', 'Landscape 1344 x 768', 'Portrait 768 x 1344', '1080p request 1920 x 1080', 'UHD 4K request 3840 x 2160', 'Portrait 4K request 2160 x 3840', 'DCI 4K request 4096 x 2160'];
// Offline definitions mirror the INPUT_TYPES contracts of Aman Dolorain's H3 repositories.
// Backend schemas always take priority. Missing-node values are never discarded.
const dolorainOfflineSchemas={
 H3VideoController:{input:{required:{
  duration_seconds:['FLOAT',{default:5,min:.01,max:149.66,step:.1}],
  fps:['FLOAT',{default:24,min:24,max:24,step:1}],
  width:['INT',{default:512,min:1,max:16384}],
  height:['INT',{default:512,min:1,max:16384}],
  resolution_preset:[h3PresetNames,{default:'Custom'}]
 }}},
 H3AudioController:{input:{required:{
  duration:['FLOAT',{forceInput:true,default:5}],
  audio_file:[[''],{default:''}],
  start_seconds:['FLOAT',{default:0,min:0,max:1e12,step:.01}]
 }}},
 AmanSimplePrompt:{input:{required:{
  text:['STRING',{default:'',multiline:true,dynamicPrompts:false}]
 }}}
};
let templateFieldNames;
function graphFields(n){
 const spec=(graphSchemas[n.type]||dolorainOfflineSchemas[n.type])?.input||{}, declared={...spec.required,...spec.optional};
 const named=n.widgets_values_named||{}, values=Array.isArray(n.widgets_values)?n.widgets_values:[];
 if(!templateFieldNames){
  templateFieldNames=new Map(JSON.parse(document.getElementById('source').textContent).nodes.map(node=>[node.type,Object.keys(node.widgets_values_named||{})]));
 }
 const schemaKeys=Object.keys(declared).filter(k=>{
  const [type,options]=declared[k];
  return !options?.forceInput&&(Array.isArray(type)||['INT','FLOAT','STRING','COMBO','BOOLEAN'].includes(type));
 });
 const saved=Object.keys(named), example=templateFieldNames.get(n.type)||[];
 let order=example.length===values.length&&example.length?example:schemaKeys;
 if(n.type==='H3AudioController'&&values.length===3)order=['audio_file','start_seconds','audio_player'];
 if(saved.length===values.length&&saved.length&&(!order.length||!order.every(k=>saved.includes(k))))order=saved;
 if(order.length!==values.length&&values.length){
  const expanded=schemaKeys.flatMap(k=>declared[k][1]?.control_after_generate?[k,'control_after_generate']:[k]);
  order=expanded.length===values.length?expanded:values.map((_,i)=>null);
 }
 const fields=values.map((v,i)=>({key:order[i],i,value:v}));
 for(const key of [...new Set([...saved,...schemaKeys])]){
  if(!fields.some(f=>f.key===key)&&(Object.hasOwn(named,key)||!values.length))fields.push({key,i:null});
 }
 const wiredNames=new Set();
 for(const link of wf.links){
  if(link[3]!==n.id)continue;
  const port=n.inputs?.[link[4]];
  if(port){wiredNames.add(port.name);if(port.widget?.name)wiredNames.add(port.widget.name)}
 }
 return fields.filter(f=>!['upload','choose video to upload','audio_player'].includes(f.key)).map(f=>{
  const [type,opts={}]=declared[f.key]||[];
  const choices=!type&&n.type==='H3VideoController'&&f.key==='resolution_preset'?h3PresetNames:Array.isArray(type)?type:Array.isArray(opts.options)&&opts.options.every(v=>['string','number','boolean'].includes(typeof v))?opts.options:null;
  const value=Object.hasOwn(named,f.key)?named[f.key]:f.value??opts.default??choices?.[0]??'';
  return {...f,type,opts,choices,value,label:f.key||'Setting '+(f.i+1),linked:wiredNames.has(f.key)};
 });
}
function multilineField(f){return f.opts.multiline||f.key==='text'&&f.value?.length>100||typeof f.value==='string'&&f.value.includes('\n')}
function fieldHeight(n){return graphFields(n).filter(f=>!f.linked).reduce((h,f)=>h+(multilineField(f)?60:31),0)}
function mountGraphFields(card,n){
 const fields=graphFields(n);if(fields.every(f=>f.linked))return;
 const box=document.createElement('div');box.className='nodeFields';
 const editors=new Map();
 function write(f,value){
  if(f.i!=null)n.widgets_values[f.i]=value;
  if(f.key){n.widgets_values_named??={};n.widgets_values_named[f.key]=value}
  f.value=value;
 }
 function set(key,value){
  const field=fields.find(f=>f.key===key);if(!field)return;
  write(field,value);editors.get(key)?.(value);
 }
 for(const f of fields){
  if(f.linked)continue;
  const label=document.createElement('label'),title=document.createElement('span');
  title.textContent=f.label.replaceAll('_',' ');title.title=f.label;label.append(title);
  let control=document.createElement('input'),read;
  if(f.choices?.length){
   control=document.createElement('select');const list=[...f.choices];
   if(!list.includes(f.value))list.unshift(f.value);
   list.forEach((v,i)=>control.add(new Option(String(v),String(i),false,Object.is(v,f.value))));
   read=()=>list[control.selectedIndex];editors.set(f.key,v=>{control.selectedIndex=list.indexOf(v)});
  }else if(f.type==='BOOLEAN'||typeof f.value==='boolean'){
   control.type='checkbox';control.checked=!!f.value;read=()=>control.checked;
  }else if(['FLOAT','INT'].includes(f.type)||typeof f.value==='number'){
   control.type='number';control.step=f.type==='INT'?'1':'any';
   for(const k of ['min','max'])if(Number.isFinite(f.opts[k]))control[k]=f.opts[k];
   control.value=f.value;read=()=>control.valueAsNumber;
  }else{
   if(multilineField(f)){control=document.createElement('textarea');label.className='longField'}
   const complex=f.value!==null&&typeof f.value==='object';
   control.value=complex?JSON.stringify(f.value):f.value;
   read=()=>complex?JSON.parse(control.value):control.value;
  }
  control.setAttribute('aria-label',f.label);if(!editors.has(f.key))editors.set(f.key,v=>{if(control.type==='checkbox')control.checked=!!v;else control.value=v});
  control.onchange=()=>{
   let v;try{v=read();if(typeof v==='number'&&!Number.isFinite(v)||!control.checkValidity())throw Error('Check the value for '+f.label)}catch(err){info(err.message,true);return}
   const previous=f.value;
   write(f,v);
   if(n.type==='H3VideoController'){
    const dims=['width','height'],size=dims.map(k=>fields.find(field=>field.key===k)?.value);
    n.properties??={};
    if(dims.includes(f.key)){
     set('resolution_preset','Custom');
     n.properties.h3_custom_size=size;
    }else if(f.key==='resolution_preset'){
     if(previous==='Custom')n.properties.h3_custom_size=size;
     const match=String(v).match(/(\d+)\s*[x×]\s*(\d+)\s*$/i);
     const target=match?match.slice(1).map(Number):v==='Custom'?n.properties.h3_custom_size:null;
     if(Array.isArray(target)&&target.length===2&&target.every(x=>Number.isInteger(x)&&x>0&&x<=16384))
      dims.forEach((key,i)=>set(key,target[i]));
    }
   }
   scheduleEdit();renderStudio();
  };
  label.append(control);box.append(label);
 }
 card.append(box);
}

/* Missing nodes are snapshots, not editable substitutes for an uninstalled pack.
   Never invent widget names or controls: show only saved workflow data. */
function mountMissingSnapshot(card,n){
 const named=n.widgets_values_named&&typeof n.widgets_values_named==='object'?n.widgets_values_named:{};
 const values=Array.isArray(n.widgets_values)?n.widgets_values:[];
 const entries=Object.entries(named).length?Object.entries(named):values.map((value,i)=>['Value '+(i+1),value]);
 if(!entries.length)return;
 const box=document.createElement('div');box.className='missingSnapshot';
 box.setAttribute('aria-label','Saved workflow values (read only)');
 for(const [name,value] of entries){
  const row=document.createElement('div');row.className='missingSnapshotRow';
  const label=document.createElement('span');label.className='missingSnapshotName';label.textContent=name.replaceAll('_',' ');
  const display=document.createElement('span');display.className='missingSnapshotValue';
  const rendered=value===null?'—':typeof value==='object'?JSON.stringify(value):String(value);
  display.textContent=rendered.length>140?rendered.slice(0,137)+'…':rendered;
  display.title=rendered;
  row.append(label,display);box.append(row);
 }
 card.append(box);
}
