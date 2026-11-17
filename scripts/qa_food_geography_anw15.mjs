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
    options:e.tagName==='SELECT'?[...e.options].slice(0,100).map(o=>({value:o.value,text:o.text})):undefined
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

 // Check all province options, not a truncated 30-item DOM excerpt.
 // Source: 202/2025/QH15, government article 10 Aug 2026.
 // Coverage is a diagnostic only: missing province options keep ANW-15 OPEN.
 const official = ['Cao Bằng','Điện Biên','Hà Tĩnh','Lai Châu','Lạng Sơn','Nghệ An','Quảng Ninh','Thanh Hóa','Sơn La','Hà Nội','Huế','Tuyên Quang','Lào Cai','Thái Nguyên','Phú Thọ','Bắc Ninh','Hưng Yên','Hải Phòng','Ninh Bình','Quảng Trị','Đà Nẵng','Quảng Ngãi','Gia Lai','Khánh Hòa','Lâm Đồng','Đắk Lắk','Thành phố Hồ Chí Minh','Đồng Nai','Tây Ninh','Cần Thơ','Vĩnh Long','Đồng Tháp','Cà Mau','An Giang'];
 const canonical = s=>String(s||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/^tp\.\s*/i,'Thanh pho ').replace(/[^a-zA-Z0-9]+/g,' ').trim().toLowerCase();
 const chosen = all.filter(c=>c.id==='geo-province'&&c.tag==='select').flatMap(c=>(c.options||[]).map(o=>o.text).filter(t=>t&&t!=='Tất cả'));
 const known = new Set(chosen.map(canonical));
 const wanted = new Set(official.map(canonical));
 const missingProvinces = official.filter(x=>!known.has(canonical(x)));
 const unknownOptions = chosen.filter(x=>!wanted.has(canonical(x)));
 const duplicates = chosen.filter((x,i)=>chosen.findIndex(y=>canonical(x)===canonical(y))!==i);
 result.provinceCoverage={officialSource:'https://xaydungchinhsach.chinhphu.vn/chi-tiet-34-don-vi-hanh-chinh-cap-tinh-tu-12-6-2025-119250612141845533.htm', expected:34,rendered:chosen.length, missing:missingProvinces,unknown:unknownOptions,duplicates};
 if(missingProvinces.length)result.missing.push('Missing province choices: '+missingProvinces.join(', '));
 if(unknownOptions.length)result.errors.push('Unrecognized province choices: '+unknownOptions.join(', '));

 for (const level of ['province','district','ward']) if(selectors[level]===0)result.missing.push(level+' select+nondefault option not proved in public rendered UI');
 // Interact with the ACTUAL production search (province + locality text), not just static labels.
 // The public catalog explicitly describes 3 Hanoi reference listings, not a full VN directory.
 result.filterTrials=[];
 const testCtx=await browser.newContext({viewport:{width:1280,height:900}});
 try {
  const p=await testCtx.newPage();
  const response=await p.goto(site+'/#/directory',{waitUntil:'domcontentloaded',timeout:35000});
  await p.waitForTimeout(900);
  if(response?.status()!==200)throw new Error('Live directory HTTP '+response?.status());
  const province=p.locator('#geo-province');
  const local=p.locator('#geo-local');
  const submit=p.getByRole('button',{name:'Tìm địa điểm',exact:true});
  if(await province.count()!==1||await local.count()!==1||await submit.count()!==1)
   throw new Error('Live geographic form selector not unique');
  const visibleSlugs=async()=>p.locator('a[href^="/dia-diem/"]').evaluateAll(
   anchors=>[...new Set(anchors.filter(a=>a.getClientRects().length>0).map(a=>a.getAttribute('href')).filter(Boolean))].sort());
  const trial=async(label,provinceValue,locality,expected)=>{
   await province.selectOption(provinceValue);
   await local.fill(locality);
   await submit.click();
   await p.waitForTimeout(350);
   const found=await visibleSlugs();
   const pass=JSON.stringify(found)===JSON.stringify([...expected].sort());
   result.filterTrials.push({label,province:provinceValue,search:locality,found,expected,pass});
   if(!pass)result.errors.push('Live filter failure: '+label+' expected '+expected.join('|')+' got '+found.join('|'));
  };
  await trial('All provinces, no search','Tất cả','',['/dia-diem/giang/','/dia-diem/pho-khoi/','/dia-diem/cha-ca/']);
  await trial('Only Hanoi','Hà Nội','',['/dia-diem/giang/','/dia-diem/pho-khoi/','/dia-diem/cha-ca/']);
  await trial('Cao Bang (empty)','Cao Bằng','',[]);
  await trial('Hanoi cafe title','Hà Nội','Giảng',['/dia-diem/giang/']);
  await trial('Cao Bang excludes Hanoi cafe','Cao Bằng','Giảng',[]);
  await trial('Hanoi unknown place','Hà Nội','_unlisted_test_20261117_',[]);
  await trial('All provinces cafe search','Tất cả','Giảng',['/dia-diem/giang/']);
  await trial('Hanoi district Hoan Kiem','Hà Nội','Hoàn Kiếm',['/dia-diem/giang/','/dia-diem/pho-khoi/','/dia-diem/cha-ca/']);
  await trial('Hanoi different district Ba Dinh','Hà Nội','Ba Đình',[]);
  await trial('Hanoi street Nguyen Huu Huan','Hà Nội','Nguyễn Hữu Huân',['/dia-diem/giang/']);
 }catch(e){result.errors.push('Live geography interaction test: '+String(e?.message||e).slice(0,350));}
 finally{await testCtx.close();}

 // Additional public read-only search form evidence; do NOT infer province accuracy from a static label.
 result.searchControls=all.filter(c=>c.tag==='input'&&c.type!=='file').map(c=>({route:c.route,id:c.id,placeholder:c.placeholder}));
 if(result.filterTrials?.length===10&&result.filterTrials.every(t=>t.pass)&&result.provinceCoverage.missing.length===0&&result.errors.length===0) {
  result.acceptance='PASS_VISIBLE_3_PLACES';
  result.missing=[];
 } else if(result.missing.length===0) {
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
console.log('PROVINCE_COVERAGE '+JSON.stringify(result.provinceCoverage));
if(process.env.GITHUB_STEP_SUMMARY)fs.appendFileSync(process.env.GITHUB_STEP_SUMMARY,summary);
if(result.acceptance!=='PASS_VISIBLE_3_PLACES')process.exitCode=1;
