// ANW-17: read-only, full public-sitemap coverage incl. all restaurant directory pages.
// Does not approve drafts, mutate site, post to social, or follow affiliate redirects.
import fs from 'node:fs';
const base='https://an-ngon-co-deal.bvthn-1903.chatgpt.site';
const report={checkedAt:new Date().toISOString(),site:base,readOnly:true,pages:[],errors:[],warnings:[],imageHosts:{},imagePaths:{},rightsEvidence:'not independently verified'};
const decode=s=>String(s||'').replace(/&amp;/g,'&').replace(/&#38;/g,'&').replace(/&quot;/g,'"');
const attr=(tag,key)=>{const m=tag.match(new RegExp('\\b'+key+'\\s*=\\s*["\\x27]([^"\\x27]*)["\\x27]','i'));return m?decode(m[1]):''};
async function fetchText(url,accept='text/html'){
 const r=await fetch(url,{headers:{accept,'User-Agent':'Food-SEO-ReadOnly/1.0'},redirect:'manual',signal:AbortSignal.timeout(22000)});
 if(r.status!==200)throw Error('HTTP '+r.status);
 return r.text();
}
const [siteMap,feed,robots]=await Promise.all([fetchText(base+'/sitemap.xml','application/xml'),fetchText(base+'/rss.xml','application/rss+xml'),fetchText(base+'/robots.txt','text/plain')]);
const sitemapUrls=[...siteMap.matchAll(/<loc>([^<]+)<\/loc>/gi)].map(x=>decode(x[1].trim()));
const rssUrls=[...feed.matchAll(/<item[\s>][\s\S]*?<link>([^<]+)<\/link>/gi)].map(x=>decode(x[1].trim()));
const urls=[...new Set(sitemapUrls)];
if(sitemapUrls.length!==urls.length)report.errors.push('Duplicate sitemap loc');
if(!rssUrls.length)report.errors.push('RSS empty');
if(rssUrls.length!==new Set(rssUrls).size)report.errors.push('Duplicate RSS items');
if(rssUrls.some(x=>!urls.includes(x)))report.errors.push('RSS URL missing from sitemap');
if(robots.includes('Disallow: /bai-viet/'))report.errors.push('robots.txt blocks published articles');
let index=0;
await Promise.all(Array.from({length:4},async()=>{
 while(index<urls.length){
  const url=urls[index++];
  if(!url.startsWith(base+'/') && url!==base) {report.errors.push('Off-origin sitemap URL');continue;}
  const path=url.slice(base.length)||'/';
  try{
   const html=await fetchText(url);
   const links=[...html.matchAll(/<link\b[^>]*>/gi)].map(x=>x[0]);
   const metas=[...html.matchAll(/<meta\b[^>]*>/gi)].map(x=>x[0]);
   const canonical=links.filter(x=>attr(x,'rel').toLowerCase()==='canonical').map(x=>attr(x,'href'));
   const robotsDirective=metas.filter(x=>attr(x,'name').toLowerCase()==='robots').map(x=>attr(x,'content')).join(';');
   const ogImg=metas.filter(x=>attr(x,'property').toLowerCase()==='og:image').map(x=>attr(x,'content'));
   const desc=metas.filter(x=>attr(x,'name').toLowerCase()==='description').map(x=>attr(x,'content'));
   const scripts=[...html.matchAll(/<script\b[^>]*type=["\x27]application\/ld\+json["\x27][^>]*>([\s\S]*?)<\/script>/gi)].map(x=>x[1]);
   const nodes=[];
   for(const content of scripts){try{
     const json=JSON.parse(content);
     const v=Array.isArray(json)?json:[json];
     for(const j of v){nodes.push(j);if(Array.isArray(j['@graph']))nodes.push(...j['@graph']);}
   }catch(e){report.errors.push(path+' invalid JSON-LD')}}
   const types=[...new Set(nodes.flatMap(j=>[].concat(j['@type']||[])))];
   const isArticle=path.startsWith('/bai-viet/');
   const isPlace=path.startsWith('/dia-diem/');
   if(canonical.length!==1||canonical[0]!==url)report.errors.push(path+' canonical mismatched');
   if(/noindex/i.test(robotsDirective))report.errors.push(path+' wrongly noindex');
   if(desc.length!==1||desc[0].trim().length<20)report.errors.push(path+' description missing/short');
   if(ogImg.length!==1||!ogImg[0])report.errors.push(path+' OG image missing');
   if(isArticle&&!types.some(t=>['Article','BlogPosting','NewsArticle'].includes(t)))report.errors.push(path+' Article JSON-LD missing');
   if(isPlace&&!types.some(t=>['Restaurant','LocalBusiness','FoodEstablishment'].includes(t)))report.errors.push(path+' Restaurant/LocalBusiness JSON-LD missing');
   let imageHost='',imagePath='';
   if(ogImg[0]){try{const u=new URL(ogImg[0],base);imageHost=u.hostname;imagePath=u.pathname;report.imageHosts[imageHost]=(report.imageHosts[imageHost]||0)+1;report.imagePaths[imagePath]=(report.imagePaths[imagePath]||0)+1;}catch{report.errors.push(path+' malformed OG image URL');}}
   report.pages.push({path,status:200,kind:isArticle?'article':isPlace?'place':'other',canonicalOK:canonical.length===1&&canonical[0]===url,descriptionOK:desc.length===1&&desc[0].trim().length>=20,ogImageHost:imageHost,ogImagePath:imagePath,jsonLdTypes:types,noindex:/noindex/i.test(robotsDirective)});
  }catch(err){report.errors.push(path+' '+String(err.message||err).slice(0,140));}
 }
}));
report.pages.sort((a,b)=>a.path.localeCompare(b.path));
report.counts={totalSitemap:urls.length,rss: rssUrls.length,articles:report.pages.filter(x=>x.kind==='article').length,places:report.pages.filter(x=>x.kind==='place').length,reviewed:report.pages.length};
report.unknownImageRights=Object.keys(report.imageHosts).filter(h=>h!==new URL(base).hostname);
if(report.unknownImageRights.length)report.warnings.push('OG image on external hosts: '+report.unknownImageRights.join(', '));
report.decision=report.errors.length?'FAIL':report.warnings.length?'REVIEW':'PASS_METADATA_ONLY';
fs.mkdirSync('reports',{recursive:true});
fs.writeFileSync('reports/food-anw17-full-seo.json',JSON.stringify(report,null,2)+'\n','utf8');
console.log(JSON.stringify({decision:report.decision,counts:report.counts,imageHosts:report.imageHosts,imagePaths:report.imagePaths,errors:report.errors.slice(0,25),warnings:report.warnings,rightsEvidence:report.rightsEvidence},null,2));
if(report.errors.length)process.exitCode=1;
