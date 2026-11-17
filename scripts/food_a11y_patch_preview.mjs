// Browser-only safe preview of two precise Food WCAG fixes.
// Injecting into Playwright tab NEVER changes live website, database or user account.
// If this passes, translate selectors into the existing ChatGPT Site stylesheet/editor.
import fs from "node:fs";
import {chromium} from "playwright";
import AxeBuilder from "@axe-core/playwright";

const url="https://an-ngon-co-deal.bvthn-1903.chatgpt.site/";
const patchCss=[
".wrap > .section-head > div > p { color: #445144 !important; }",
".feature-content > p { color: #445144 !important; }",
".card-bottom > .badge { color: #65410d !important; }",
].join("\n");
const r={url,readOnly:true,sourceChanged:false,pre:[],post:[],patchCss,patchDom:"Remove misleading aria-label='Trang chủ' from home logo anchor, retaining visible brand text as accessible name."};
const browser=await chromium.launch({channel:"chrome",headless:true,args:["--no-sandbox","--disable-dev-shm-usage"]});
try{
 const page=await browser.newPage({viewport:{width:1440,height:900}});
 const resp=await page.goto(url,{waitUntil:"domcontentloaded",timeout:30000});
 if(resp?.status()!==200)throw Error("Home HTTP "+resp?.status());
 await page.waitForTimeout(400);
 const baseline=await new AxeBuilder({page}).withTags(["wcag2a","wcag2aa","wcag21a","wcag21aa"]).analyze();
 r.pre=baseline.violations.map(v=>({id:v.id,impact:v.impact,nodes:v.nodes.length}));
 await page.addStyleTag({content:patchCss});
 await page.evaluate(()=>{
    const home=document.querySelector('a[aria-label="Trang chủ"]');
    if(home)home.removeAttribute("aria-label");
 });
 await page.waitForTimeout(100);
 const result=await new AxeBuilder({page}).withTags(["wcag2a","wcag2aa","wcag21a","wcag21aa"]).analyze();
 r.post=result.violations.map(v=>({id:v.id,impact:v.impact,nodes:v.nodes.length,targets:v.nodes.slice(0,5).map(n=>n.target)}));
 r.outcome=!r.post.some(v=>v.impact==="critical"||v.impact==="serious")?"BROWSER_ONLY_FIX_PASS":"PATCH_PREVIEW_FAILED";
 await page.close();
}catch(e){r.outcome="ERROR";r.error=String(e).slice(0,450)}
finally{await browser.close()}
fs.mkdirSync("reports",{recursive:true});
fs.writeFileSync("reports/food-a11y-patch-preview.json",JSON.stringify(r,null,2)+"\n");
console.log(JSON.stringify({outcome:r.outcome,error:r.error||null,before:r.pre,after:r.post,productionChanged:false}));
if(r.outcome!=="BROWSER_ONLY_FIX_PASS")process.exitCode=1;
