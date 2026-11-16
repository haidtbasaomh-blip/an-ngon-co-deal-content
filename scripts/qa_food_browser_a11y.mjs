// Read-only browser accessibility/mobile/admin & geographic-filter discovery
// for ĂN NGON CÓ DEAL existing live site.
import fs from 'node:fs';
import {chromium} from 'playwright';
import AxeBuilder from '@axe-core/playwright';
const base='https://an-ngon-co-deal.bvthn-1903.chatgpt.site';
const report={site:base,checkedAt:new Date().toISOString(),views:[],errors:[],warnings:[],geoControls:[],navigation:[],admin:{},counts:{},screenshots:[]};
const browser=await chromium.launch({channel:'chrome',headless:true,args:['--disable-dev-shm-usage','--no-sandbox']});
try {
 const site=await fetch(base+'/sitemap.xml',{signal:AbortSignal.timeout(18000)}).then(r=>r.text());
 const all=[...site.matchAll(/<loc>\s*([^<]+?)\s*<\/loc>/gi)].map(m=>m[1].replace(/&amp;/g,'&'));
 const articleUrls=all.filter(x=>x.startsWith(base+'/bai-viet/'));
 const navPaths=['/',...articleUrls.slice(0,2).map(u=>u.slice(base.length))];
 report.counts={sitemap:all.length,articles:articleUrls.length};
 for(const device of [
  {name:'phone375',width:375,height:812,mobile:true},
  {name:'phone390',width:390,height:844,mobile:true},
  {name:'desktop',width:1440,height:900,mobile:false}
 ]) {
  const context=await browser.newContext({viewport:{width:device.width,height:device.height},isMobile:device.mobile});
  const page=await context.newPage();
  const jsErrors=[];page.on('pageerror',err=>jsErrors.push(err.message));
  for(const path of navPaths){
   const res=await page.goto(base+path,{waitUntil:'domcontentloaded',timeout:35000});
   await page.waitForTimeout(200);
   const view=await page.evaluate(()=>({
    vw:document.documentElement.clientWidth,scrollW:document.documentElement.scrollWidth,
    textLength:(document.body?.innerText||'').length,headings:[...document.querySelectorAll('h1')].map(x=>x.innerText).slice(0,3),
    brokenImages:[...document.images].filter(x=>x.complete&&x.naturalWidth===0&&getComputedStyle(x).display!=='none').map(x=>x.src.slice(0,100)).slice(0,5)
   }));
   report.views.push({device:device.name,path,status:res?.status(),...view});
   if(res?.status()!==200)report.errors.push(device.name+' '+path+' HTTP '+res?.status());
   if(view.scrollW>view.vw+7)report.errors.push(device.name+' '+path+' overflow '+view.scrollW+'/'+view.vw);
   if(view.textLength<120)report.errors.push(device.name+' '+path+' suspiciously empty');
   if(view.brokenImages.length)report.warnings.push(device.name+' '+path+' '+view.brokenImages.length+' broken images');
   if(device.name==='phone375'&&path==='/'){
    await page.screenshot({path:'reports/food-browser-home375.png',fullPage:false});report.screenshots.push('reports/food-browser-home375.png');
   }
   if(device.name==='desktop'&&path==='/'){
    await page.screenshot({path:'reports/food-browser-home1440.png',fullPage:false});report.screenshots.push('reports/food-browser-home1440.png');
   }
   if(device.name==='desktop'&&path==='/'){
    report.navigation=await page.evaluate(()=>[...document.querySelectorAll('a[href]')].map(a=>({title:(a.innerText||'').trim().slice(0,60),href:a.getAttribute('href')})).filter(x=>/quan|tinh|dia|tim|kham|am thuc|xa|huyen|thanh/i.test(x.title+' '+x.href)).slice(0,70));
    report.geoControls=await page.evaluate(()=>({
      select:[...document.querySelectorAll('select')].map(e=>({name:e.name,id:e.id,aria:e.getAttribute('aria-label'),options:[...e.options].slice(0,15).map(o=>({text:o.text,value:o.value}))})),
      input:[...document.querySelectorAll('input')].map(e=>({type:e.type,name:e.name,id:e.id,placeholder:e.placeholder})),
      buttons:[...document.querySelectorAll('button')].map(e=>({text:(e.innerText||'').trim().slice(0,60),aria:e.getAttribute('aria-label')})).slice(0,35)
    }));
    try {
      const axe=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21a','wcag21aa']).analyze();
      report.accessibility={criticalOrSerious:axe.violations.filter(x=>['critical','serious'].includes(x.impact)).map(x=>({id:x.id,impact:x.impact,help:x.help,affected:x.nodes.length})),other:axe.violations.filter(x=>!['critical','serious'].includes(x.impact)).map(x=>({id:x.id,impact:x.impact,affected:x.nodes.length})),passes:axe.passes.length};
    }catch(e){report.warnings.push('Axe failed: '+String(e))}
   }
  }
  if(jsErrors.length)report.warnings.push(device.name+' JS errors '+jsErrors.slice(0,4).join('; '));
  await context.close();
 }
 const adminContext=await browser.newContext({viewport:{width:1440,height:900}}),adminPage=await adminContext.newPage();
 for(const path of ['/admin','/admin/']){
  const res=await adminPage.goto(base+path,{waitUntil:'domcontentloaded',timeout:30000});
  report.admin[path]={status:res?.status(),title:await adminPage.title()};
 }
 await adminContext.close();
 if((report.accessibility?.criticalOrSerious||[]).length)report.errors.push('WCAG critical/serious violations: '+report.accessibility.criticalOrSerious.length);
 report.status=report.errors.length?'FAIL':report.warnings.length?'NEEDS_REVIEW':'PASS';
}catch(e){report.errors.push('Browser error '+String(e));report.status='FAIL'}
finally{await browser.close()}
fs.mkdirSync('reports',{recursive:true});
fs.writeFileSync('reports/food-browser-a11y.json',JSON.stringify(report,null,2)+'\n');
const markdown=['# Food site Chrome mobile/accessibility audit','',
 '| Item | Result |','|---|---:|',
 '| Responsive/document pages checked | '+report.views.length+' |',
 '| Public article links in sitemap | '+report.counts.articles+' |',
 '| Serious accessibility violations | '+(report.accessibility?.criticalOrSerious.length??'not tested')+' |',
 '| Admin HTTP status | '+JSON.stringify(report.admin)+' |',
 '| Browser errors | '+report.errors.length+' |',
 '| Warnings | '+report.warnings.length+' |','',
 '**Result:** '+report.status,'',
 ...report.errors.map(x=>'- ERROR: '+x),...report.warnings.map(x=>'- WARNING: '+x),
 '',
 'No content publishing, no admin login, no Facebook activity.'];
fs.writeFileSync('reports/food-browser-a11y.md',markdown.join('\n')+'\n');
console.log(markdown.join('\n'));
console.log('GEO_DIAGNOSTICS '+JSON.stringify({geoControls:report.geoControls,navigation:report.navigation}));
console.log('ACCESSIBILITY '+JSON.stringify(report.accessibility));
if(process.env.GITHUB_STEP_SUMMARY)fs.appendFileSync(process.env.GITHUB_STEP_SUMMARY,markdown.join('\n'));
if(report.errors.length)process.exitCode=1;
