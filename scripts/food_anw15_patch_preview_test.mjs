// Prove address-aware search behavior in a disposable Chrome page only.
import fs from 'node:fs';
import {chromium} from 'playwright';
const site='https://an-ngon-co-deal.bvthn-1903.chatgpt.site/#/directory';
const patch=fs.readFileSync('scripts/food_anw15_patch_preview.js','utf8');
const all=['/dia-diem/cha-ca/','/dia-diem/giang/','/dia-diem/pho-khoi/'];
const tests=[],errors=[];
const browser=await chromium.launch({channel:'chrome',headless:true,args:['--no-sandbox','--disable-dev-shm-usage']});
const ctx=await browser.newContext({viewport:{width:1280,height:900}});
try{
 const page=await ctx.newPage();
 const r=await page.goto(site,{waitUntil:'domcontentloaded',timeout:35000});
 if(r?.status()!==200)throw Error('Live directory HTTP '+r?.status());
 await page.waitForTimeout(900);
 const baseline=await page.locator('a[href^="/dia-diem/"]').evaluateAll(a=>[...new Set(a.filter(x=>x.getClientRects().length>0).map(x=>x.getAttribute('href')))].sort());
 if(JSON.stringify(baseline)!==JSON.stringify([...all].sort()))throw Error('Unexpected baseline: '+JSON.stringify(baseline));
 await page.addScriptTag({content:'window.__FOOD_GEO_PATCH_PREVIEW__=true;\n'+patch});
 const controls=await page.evaluate(()=>({district:!!document.querySelector('#geo-district-legacy'),ward:!!document.querySelector('#geo-ward-current'),count:window.__FOOD_GEO_PATCH_PROOF__?.count()}));
 if(!controls.district||!controls.ward||controls.count!==3)throw Error('Preview controls not mounted: '+JSON.stringify(controls));
 const test=async(label,{province,query,district,ward},expected)=>{
   if(province!==undefined)await page.locator('#geo-province').selectOption(province);
   if(query!==undefined)await page.locator('#geo-local').fill(query);
   if(district!==undefined)await page.locator('#geo-district-legacy').selectOption(district);
   if(ward!==undefined)await page.locator('#geo-ward-current').selectOption(ward);
   await page.getByRole('button',{name:'Tìm địa điểm',exact:true}).click();
   await page.waitForTimeout(130);
   const observed=await page.evaluate(()=>window.__FOOD_GEO_PATCH_PROOF__.getResults());
   const sorted=[...expected].sort();
   const pass=JSON.stringify(observed)===JSON.stringify(sorted);
   tests.push({label,observed,expected:sorted,pass});
   if(!pass)errors.push(label+' expected '+JSON.stringify(sorted)+' got '+JSON.stringify(observed));
 };
 await test('default 3',{},all);
 await test('Hanoi only',{province:'Hà Nội'},all);
 await test('Hoan Kiem free text',{query:'Hoàn Kiếm'},all);
 await test('Hoan Kiem without accents',{query:'hoan kiem'},all);
 await test('Hanoi district selector',{query:'',district:'Hoàn Kiếm'},all);
 await test('Hanoi current ward selector',{ward:'Hoàn Kiếm'},all);
 await test('Hanoi Giang title',{district:'Tất cả',ward:'Tất cả',query:'Giảng'},['/dia-diem/giang/']);
 await test('Hanoi Nguyen Huu Huan street',{query:'Nguyễn Hữu Huân'},['/dia-diem/giang/']);
 await test('Hanoi Ba Dinh no matching place',{query:'Ba Đình'},[]);
 await test('Hanoi unknown name',{query:'__not_a_real_place__'},[]);
 await test('Cao Bang no published place',{province:'Cao Bằng',query:''},[]);
 await test('all province returns 3',{province:'Tất cả',query:''},all);
 await page.reload({waitUntil:'domcontentloaded',timeout:35000});
 await page.waitForTimeout(900);
 const restored=await page.evaluate(()=>!document.querySelector('#geo-district-legacy')&&!document.querySelector('#geo-ward-current')&&!window.__FOOD_GEO_PATCH_PROOF__);
 if(!restored)errors.push('Preview injection persisted unexpectedly after reload');
 const report={checkedAt:new Date().toISOString(),site,previewOnly:true,changesToProduction:0,publishedCards:baseline.length,controls,tests,restoredAfterReload:restored,errors,
   outcome:errors.length?'FAILED':'BROWSER_ONLY_PASS',
   unresolved:'MUST apply equivalent model/filter changes via native ChatGPT Sites editor then retest live ANW-15; this preview did not deploy'};
 fs.mkdirSync('reports',{recursive:true});
 fs.writeFileSync('reports/food-anw15-locality-patch-preview.json',JSON.stringify(report,null,2)+'\n');
 console.log(JSON.stringify({outcome:report.outcome,tests:tests.length,passed:tests.filter(x=>x.pass).length,errors,restoredAfterReload:restored,changesToProduction:0}));
 if(errors.length)process.exitCode=1;
}catch(err){console.error('PREVIEW_ERROR',String(err).slice(0,500));process.exitCode=1;}
finally{await ctx.close();await browser.close();}
