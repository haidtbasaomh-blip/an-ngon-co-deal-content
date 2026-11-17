// ANW-15: read-only three-level geography / search acceptance probe.
// Never logs in, edits, publishes, sends Facebook posts, or stores personal data.
import fs from 'node:fs';
import {chromium} from 'playwright';
const site='https://an-ngon-co-deal.bvthn-1903.chatgpt.site';
const routes=['/','/#/directory'];
const result={site,checkedAt:new Date().toISOString(),readOnly:true,views:[],actions:[],errors:[],missing:[],acceptance:'OPEN'};
fs.mkdirSync('reports',{recursive:true});
const browser=await chromium.launch({channel:'chrome',headless:true,args:['--no-sandbox','--disable-dev-shm-usage']});
try {
 for(const route of routes){
  const ctx=await browser.newContext({viewport:{width:1280,height:800}});
  const p=await ctx.newPage();
  const response=await p.goto(site+route,{waitUntil:'domcontentloaded',timeout:35000});
  await p.waitForTimeout(900);
  const state=await p.evaluate(()=>{
   const visible=e=>{const s=getComputedStyle(e);return s.display!=='none'&&s.visibility!=='hidden'&&e.getClientRects().length>0};
   const controls=[...document.querySelectorAll('select,input,button,[role="combobox"],[role="listbox"]')].filter(visible).map(e=>({
    tag:e.tagName.toLowerCase(),type:e.type||'',name:e.name||'',id:e.id||'',
    role:e.getAttribute('role')||'',aria:e.getAttribute('aria-label')||'',
    placeholder:e.placeholder||'',text:(e.textContent||'').trim().slice(0,80),
    options:e.tagName==='SELECT'?[...e.options].slice(0,30).map(o=>({value:o.value,text:o.text})):undefined
   })).slice(0,100);
   const links=[...document.querySelectorAll('a[href*="/dia-diem/"]')].filter(visible).map(x=>({href:x.getAttribute('href'),text:(x.textContent||'').trim().slice(0,120)})).slice(0,25);
   const headings=[...document.querySelectorAll('h1,h2,h3')].filter(visible).map(e=>(e.textContent||'').trim().slice(0,100)).slice(0,30);
   return {title:document.title,controls,links,headings,bodyText:(document.body?.innerText||'').slice(0,850),pageWidth:document.documentElement.scrollWidth,screenWidth:document.documentElement.clientWidth};
  });
  result.views.push({route,status:response?.status()||0,location:p.url(),...state});
  if(response?.status()!==200)result.errors.push(route+' HTTP '+response?.status());
  if(state.pageWidth>state.screenWidth+8)result.errors.push(route+' horizontal overflow');
  await ctx.close();
 }
 const all=result.views.flatMap(v=>v.controls.map(c=>({...c,route:v.route})));
 const combined=c=>([c.aria,c.name,c.id,c.placeholder,c.text].filter(Boolean).join(' ')).toLowerCase();
 const geo = {
  province:all.filter(c=>/(tỉnh|thành phố|province|city)/i.test(combined(c)) && !/(thành công|đăng nhập)/i.test(combined(c))),
  district:all.filter(c=>/(huyện|quận|district)/i.test(combined(c))),
  ward:all.filter(c=>/(phường|xã|ward|commune)/i.test(combined(c)))
 };
 const selectors=Object.fromEntries(Object.entries(geo).map(([k,v])=>[k,v.filter(c=>c.tag==='select'&&c.options?.some(o=>o.value&&o.value!=='Tất cả')).length]));
 result.geoSelectors=Object.fromEntries(Object.entries(geo).map(([k,v])=>[k,v.map(c=>({route:c.route,id:c.id,tag:c.tag,aria:c.aria,options:(c.options||[]).length}))]));
 for (const level of ['province','district','ward']) if(selectors[level]===0)result.missing.push(level+' select+nondefault option not proved in public rendered UI');
 // Additional public read-only search form evidence; do NOT infer province accuracy from a static label.
 result.searchControls=all.filter(c=>c.tag==='input'&&c.type!=='file').map(c=>({route:c.route,id:c.id,placeholder:c.placeholder}));
 if(result.missing.length===0) {
  result.acceptance='REVIEW_FILTER_OUTCOMES';
  result.errors.push('Three selectors detected, but field-level matching and returned place addresses still need live option-transition proof');
 } else result.acceptance='OPEN';
} catch (e) {
 result.errors.push(String(e?.message||e).slice(0,400));
 result.acceptance='OPEN';
} finally{await browser.close()}
fs.writeFileSync('reports/food-geography-anw15.json',JSON.stringify(result,null,2)+'\n');
const summary=[
 '# ANW-15 public geographic filter audit','',
 'Status: '+result.acceptance,
 'Views: '+result.views.length,
 'Missing proof: '+result.missing.join('; '),
 'Errors: '+result.errors.join('; '),'',
 'This is a discovery/preflight report, not an assertion of 100% acceptance.',
 'No live data, draft, page, ad, or social post was changed.'
].join('\n');
fs.writeFileSync('reports/food-geography-anw15.md',summary+'\n');
console.log(summary);
console.log('CONTROLS '+JSON.stringify(result.geoSelectors));
if(process.env.GITHUB_STEP_SUMMARY)fs.appendFileSync(process.env.GITHUB_STEP_SUMMARY,summary);
