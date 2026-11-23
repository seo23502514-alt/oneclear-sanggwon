window.EQQ = window.__QS;
window.EQ = {done:0, part:0, buf:[], fail:[], running:true};
(async()=>{
 const dl=(name,obj)=>{const b=new Blob([JSON.stringify(obj)],{type:'application/json'});const a=document.createElement('a');a.href=URL.createObjectURL(b);a.download=name;document.body.appendChild(a);a.click();a.remove();};
 const dec=s=>s.replace(/&amp;/g,'&');
 async function one(i){
  const q=EQQ[i];
  const h=await fetch('/images/search?q='+encodeURIComponent(q)+'&first=1').then(r=>r.text());
  const ms=[...h.matchAll(/ m="(\{[^"]*?)"/g)].slice(0,4).map(x=>{try{return JSON.parse(x[1].replace(/&quot;/g,'"').replace(/&amp;/g,'&'))}catch(e){return null}}).filter(Boolean);
  for(const j of ms){
   try{
    const blob=await fetch(dec(j.turl)).then(r=>{if(!r.ok)throw 0;return r.blob()});
    const bm=await createImageBitmap(blob);
    const sc=Math.min(1,420/Math.max(bm.width,bm.height));
    const c=document.createElement('canvas');c.width=Math.round(bm.width*sc);c.height=Math.round(bm.height*sc);
    const x=c.getContext('2d');x.fillStyle='#fff';x.fillRect(0,0,c.width,c.height);x.drawImage(bm,0,0,c.width,c.height);
    return {i,q,d:c.toDataURL('image/jpeg',0.82),p:j.purl||'',mu:j.murl||'',t:j.t||''};
   }catch(e){}
  }
  throw 'noimg';
 }
 for(let i=0;i<EQQ.length;i++){
  if(!EQ.running)break;
  try{EQ.buf.push(await one(i))}catch(e){EQ.fail.push(i)}
  EQ.done=i+1;
  if(EQ.buf.length>=60){dl('eqphoto_part_'+(EQ.part++)+'.json',EQ.buf);EQ.buf=[];}
  await new Promise(r=>setTimeout(r,400));
 }
 if(EQ.buf.length){dl('eqphoto_part_'+(EQ.part++)+'.json',EQ.buf);EQ.buf=[];}
 dl('eqphoto_fail.json',EQ.fail);
 EQ.finished=true;
})();
'started'
