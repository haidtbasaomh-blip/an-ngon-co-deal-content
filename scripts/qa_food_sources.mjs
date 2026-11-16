// Verify staged editorial citations, without publishing or copying source content.
// Read-only, no site, Facebook, or API writes.
import fs from 'node:fs';
const articles=JSON.parse(fs.readFileSync('ready.json','utf8')).articles||[];
const report={checkedAt:new Date().toISOString(),total:articles.length,missing:[],invalid:[],unreachable:[],verified:[],needsReview:[]};
const jobs=articles.map(a=>({id:a.id,title:a.title,url:String(a.source||''),status:String(a.sourceStatus||'')}));
for(const a of jobs){
 if(!a.url||a.status!=='topic_matched'){report.missing.push(a.id);continue}
 let url;try{url=new URL(a.url)}catch{report.invalid.push(a.id);continue}
 if(url.protocol!=='https:'||!['vnexpress.net','vietnam.travel','antoanthucpham.hanoi.gov.vn','tienphong.vn','dulich.quangninh.gov.vn','csdl.vietnamtourism.gov.vn','dantri.com.vn','beta-v2.vietnam.travel','ankhanh.haiphong.gov.vn','vietnamtourism.vn','www.vietnamairlines.com'].includes(url.hostname)){
  report.invalid.push(a.id+' '+url.hostname);continue
 }
}
let index=0;
await Promise.all(Array.from({length:5},async()=>{
 while(index<jobs.length){
  const a=jobs[index++];
  if(report.missing.includes(a.id)||report.invalid.some(x=>x.startsWith(a.id)))continue;
  try{
   let res=await fetch(a.url,{headers:{'user-agent':'Mozilla/5.0 (compatible; EditorialSourceQA/1.0)','accept':'text/html,*/*'},redirect:'follow',signal:AbortSignal.timeout(18000)});
   if(res.ok){
    const final=new URL(res.url);
    if(!['vnexpress.net','vietnam.travel','antoanthucpham.hanoi.gov.vn','tienphong.vn','dulich.quangninh.gov.vn','csdl.vietnamtourism.gov.vn','dantri.com.vn','beta-v2.vietnam.travel','ankhanh.haiphong.gov.vn','vietnamtourism.vn','www.vietnamairlines.com'].includes(final.hostname)){
      report.invalid.push(a.id+' unexpected redirected hostname '+final.hostname);continue
    }
    let html=(await res.text()).slice(0,250000).toLowerCase();
    const bad=/<title[^>]*>(404|403|page not found|not found|không tìm thấy trang)/i.test(html);
    if(bad)report.unreachable.push({id:a.id,status:res.status,url:res.url,reason:'404 or not-found page title'});
    else report.verified.push({id:a.id,status:res.status,url:res.url});
   }else if([401,403,429].includes(res.status))report.needsReview.push({id:a.id,status:res.status,reason:'bot or rate limit, manual verification required'});
   else report.unreachable.push({id:a.id,status:res.status});
  }catch(e){report.needsReview.push({id:a.id,reason:String(e).slice(0,120)})}
 }
}));
report.status=report.missing.length||report.invalid.length||report.unreachable.length?'FAIL':report.needsReview.length?'REVIEW':'PASS';
fs.mkdirSync('out',{recursive:true});
fs.writeFileSync('out/source_link_qa.json',JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report,null,2));
if(report.status==='FAIL')process.exitCode=1;
