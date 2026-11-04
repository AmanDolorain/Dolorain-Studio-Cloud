function nodeWidth(id){
 const n=idmap().get(Number(id)),g=groupOf(Number(id));
 return n?.properties?.dolorainSize?.w || (g?.width?g.width-32:218);
}
function sizeBoxes(){
 return groups.map(g=>{
  const ids=g.ids.filter(id=>positions[id]);
  const x=Math.min(g.x,...ids.map(id=>positions[id].x-16));
  const y=Math.min(g.y,...ids.map(id=>positions[id].y-42));
  const right=Math.max(g.x+(g.width||250),...ids.map(id=>positions[id].x+nodeWidth(id)+16));
  const bottom=Math.max(g.y+(g.height||105),...ids.map(id=>positions[id].y+nodeHeight(id)+16));
  return {g,x,y,w:right-x,h:bottom-y};
 });
}
function fitMember(id,b){
 const n=idmap().get(id);
 if(n.properties?.dolorainSize)delete n.properties.dolorainSize.w;
 positions[id].x=b.x+16;
 positions[id].y=Math.max(b.y+42,positions[id].y);
}
function finishNodeDrop(ids,event,boxes){
 const world=$('world').getBoundingClientRect();
 const x=(event.clientX-world.left)/zoom,y=(event.clientY-world.top)/zoom;
 const target=[...boxes].reverse().find(b=>x>=b.x&&x<=b.x+b.w&&y>=b.y&&y<=b.y+b.h);
 if(!target)return;
 const g=target.g;
 for(const id of ids){
  const old=groupOf(id);
  if(old===g){
   if(!g.width)continue;
   positions[id].x=Math.min(Math.max(g.x+16,positions[id].x),g.x+g.width-16-nodeWidth(id));
   positions[id].y=Math.max(g.y+42,positions[id].y);continue;
  }
  if(old)old.ids=old.ids.filter(v=>v!==id);
  g.ids.push(id);g.width=target.w;g.x=target.x;fitMember(id,target);
 }
}
function resizeStart(e){
 const grip=e.target.closest('.sizeGrip');
 if(!grip||e.button!==0)return;
 e.stopImmediatePropagation();e.preventDefault();
 const v=$('viewport'),pid=e.pointerId,node=grip.closest('.node'),id=node&&Number(node.dataset.id);
 const n=node&&idmap().get(id),g=node?groupOf(id):groups[Number(grip.closest('.group').dataset.i)];
 const b=rects().find(b=>b.g===g),w=node?nodeWidth(id):b.w,h=node?node.offsetHeight:b.h;
 recordEdit();editHistory.held=true;v.setPointerCapture(pid);
 function move(ev){
  if(ev.pointerId!==pid)return;
  const width=Math.round(w+(ev.clientX-e.clientX)/zoom),height=Math.round(h+(ev.clientY-e.clientY)/zoom);
  if(node){
   n.properties??={};n.properties.dolorainSize={w:Math.max(136,width),h:Math.max(45,height)};
   if(g&&positions[id].x+n.properties.dolorainSize.w+16>b.x+b.w)g.width=positions[id].x+n.properties.dolorainSize.w+16-g.x;
  }else{
   g.x=b.x;g.y=b.y;g.width=Math.max(168,width);g.height=Math.max(105,height);
   for(const member of g.ids){
    const p=positions[member],size=idmap().get(member).properties?.dolorainSize;
    p.x=g.x+16;
    if(size?.w)size.w=Math.min(size.w,g.width-32);
   }
  }
  renderGraph();
 }
 function end(ev){
  if(ev.pointerId!==pid)return;
  v.removeEventListener('pointermove',move);
  for(const name of ['pointerup','pointercancel','lostpointercapture'])v.removeEventListener(name,end);
  if(v.hasPointerCapture(pid))v.releasePointerCapture(pid);
  editHistory.held=false;recordEdit();
 }
 v.addEventListener('pointermove',move);
 for(const name of ['pointerup','pointercancel','lostpointercapture'])v.addEventListener(name,end);
}
