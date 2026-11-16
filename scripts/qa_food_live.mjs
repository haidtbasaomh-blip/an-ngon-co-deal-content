// Read-only monitoring of the existing Ăn Ngon Có Deal site. Never publishes content.
import fs from 'node:fs';
const base='https://an-ngon-co-deal.bvthn-1903.chatgpt.site';
const errors=[],warnings=[];
async function get(path){
 const response=await fetch(base+path,{headers:{accept:'text/html,application/rss+xml,application/xml'},redirect:'manual',signal:AbortSignal.timeout(20000)});
 if(!response.ok)throw Error(path+' HTTP '+response.status);
 return response.text();
}
function tag(xml,name){const m=xml.match(new RegExp('<'+name+'(?:\\s[^>]*)?>([\\s\\S]*?)<\\/'+name+'>','i'));return m?m[1].trim():''}
function htmlEntity(s){return s.replace(/&amp;/g,'&').replace(/&#38;/g,'&')}
async function run(){
 const [home,rss,sitemap]=await Promise.all([get('/'),get('/rss.xml'),get('/sitemap.xml')]);
 if(!/<rss\b/i.test(rss)||!/<channel\b/i.test(rss))errors.push('RSS is not valid channel XML');
 if(!/rel=['"]canonical['"]/i.test(home))errors.push('Homepage missing canonical');
 if(/<meta\b[^>]*name=['"]robots['"][^>]*noindex/i.test(home))errors.push('Public homepage is noindex');
 if(!/property=['"]og:image['"]/i.test(home))warnings.push('Homepage OG image not detected');
 const itemXml=[...rss.matchAll(/<item(?:\s[^>]*)?>([\s\S]*?)<\/item>/gi)].map(m=>m[1]);
 const articleLinks=itemXml.map(x=>htmlEntity(tag(x,'link'))).filter(Boolean);
 const urlSet=new Set(articleLinks);
 const duplicateRSS=articleLinks.length-urlSet.size;
 if(!articleLinks.length)errors.push('RSS contains zero published article links');
 if(duplicateRSS)errors.push('RSS duplicate links: '+duplicateRSS);
 const sitemapUrls=[...sitemap.matchAll(/<loc>([^<]+)<\/loc>/gi)].map(m=>htmlEntity(m[1].trim()));
 if(sitemapUrls.length<10)errors.push('Sitemap missing expected public articles');
 const sitemapSet=new Set(sitemapUrls);
 const missingFromSitemap=articleLinks.filter(link=>!sitemapSet.has(link));
 if(missingFromSitemap.length)warnings.push('RSS article URLs not present in sitemap: '+missingFromSitemap.length);
 const foreign=articleLinks.filter(link=>!link.startsWith(base+'/bai-viet/'));
 if(foreign.length)errors.push('RSS contains unexpected external or non-article links: '+foreign.length);
 // Check a representative fixed sample, do not hammer hosting or connected apps.
 const sample=articleLinks; // Audit every RSS-published article, not a 12-article sample.
 let index=0;const failures=[],missingCanon=[],missingOG=[],missingDescription=[],missingTitle=[],missingStructuredData=[],noindexArticles=[];
 await Promise.all(Array.from({length:4},async()=>{
  while(index<sample.length){
   const url=sample[index++],path=url.slice(base.length);
   try{
    const html=await get(path);
    if(!/rel=['"]canonical['"]/i.test(html))missingCanon.push(path);
    if(!/property=['"]og:image['"]/i.test(html))missingOG.push(path);
    if(!/<title\b[^>]*>[^<]+<\/title>/i.test(html))missingTitle.push(path);
    if(!/<meta\b[^>]*name=['"]description['"]/i.test(html))missingDescription.push(path);
    const jsonScripts=[...html.matchAll(/<script\b[^>]*type=['"]application\/ld\+json['"][^>]*>([\s\S]*?)<\/script>/gi)];
    try {
      const nodes=jsonScripts.flatMap(m=>{const j=JSON.parse(m[1]);return Array.isArray(j['@graph'])?j['@graph']:[j]});
      const article=nodes.find(j=>['Article','BlogPosting','NewsArticle'].includes(j['@type']));
      if(!article || article.url!==url || !article.headline || !article.image || !nodes.some(j=>j['@type']==='BreadcrumbList'))missingStructuredData.push(path);
    } catch {missingStructuredData.push(path)}
    if(/<meta\b[^>]*name=['"]robots['"][^>]*noindex/i.test(html))noindexArticles.push(path);
   }catch(e){failures.push(path+': '+String(e.message||e))}
  }
 }));
 if(failures.length)errors.push('Published article URLs failed: '+failures.length);
 if(missingCanon.length)errors.push('Published articles without canonical: '+missingCanon.length);
 if(missingOG.length)warnings.push('Published articles without OG image: '+missingOG.length);
 if(missingDescription.length)warnings.push('Published articles without meta description: '+missingDescription.length);
 if(missingStructuredData.length)errors.push('Published articles without JSON-LD: '+missingStructuredData.length);
 if(missingTitle.length)errors.push('Published articles without title: '+missingTitle.length);
 if(noindexArticles.length)errors.push('Published articles incorrectly noindex: '+noindexArticles.length);
 const privatePaths=['/draft-index.json','/draft-batches/0.json','/editorial-review.json','/api/admin/editorial','/api/admin/backups','/admin/backups/'];
 const privateAccess=[];
 for(const path of privatePaths){const r=await fetch(base+path,{redirect:'manual',signal:AbortSignal.timeout(20000)});privateAccess.push({path,status:r.status});if(r.status!==403)errors.push('Private resource exposed or unexpected response: '+path+' HTTP '+r.status)}
 const publicEditorial=JSON.parse(await get('/api/editorial'));
 const publicOnly=Array.isArray(publicEditorial.articles)&&publicEditorial.articles.every(a=>a.approved===true&&a.publicationStatus==='published'&&!a.id.startsWith('nhap-'));
 if(!publicOnly)errors.push('Public editorial API contains non-published content');
 if(publicEditorial.articles?.length!==articleLinks.length)errors.push('Public API count differs from RSS');
 if(/draft-batches|draft-index|\/admin\//i.test(rss+sitemap))errors.push('Private draft/admin URL in RSS or sitemap');
 const report={checkedAt:new Date().toISOString(),site:base,readOnly:true,privateAccess,publicOnly,homepage:{canonical:true},rss:{itemCount:itemXml.length,validLinks:articleLinks.length,duplicateLinks:duplicateRSS},sitemap:{urls:sitemapUrls.length,missingRSSArticles:missingFromSitemap.length},articles:{sampled:sample.length,totalPublished:articleLinks.length,broken:failures,missingCanon,missingOG,missingTitle,missingDescription,missingStructuredData,noindexArticles},status:errors.length?'failed':warnings.length?'needs_review':'healthy',errors,warnings};
 fs.mkdirSync('reports',{recursive:true});
 fs.writeFileSync('reports/food-live-qa.json',JSON.stringify(report,null,2)+'\n');
 const summary=['# Ăn Ngon Có Deal – kiểm tra website thật',
  '| Hạng mục | Kết quả |','|---|---:|',
  '| Bài trong RSS | '+itemXml.length+' |','| URL sitemap | '+sitemapUrls.length+' |',
  '| Bài được kiểm tra thực tế | '+sample.length+' |',
  '| Bài lỗi truy cập | '+failures.length+' |',
  '| Tài nguyên riêng chặn khách 403 | '+privateAccess.filter(x=>x.status===403).length+'/'+privatePaths.length+' |',
  '| API chỉ chứa bài đã xuất bản | '+publicOnly+' |',
  '| Bài thiếu canonical | '+missingCanon.length+' |',
  '| Bài thiếu ảnh OG | '+missingOG.length+' |',
  '| Bài thiếu meta description | '+missingDescription.length+' |',
  '| Bài thiếu JSON-LD | '+missingStructuredData.length+' |',
  '| Bài bị noindex sai | '+noindexArticles.length+' |',
  '| Bài từ RSS chưa có trong sitemap | '+missingFromSitemap.length+' |','',
  '**Trạng thái:** '+report.status.toUpperCase(),'',
  'Kiểm tra bài công khai và xác minh khách chưa đăng nhập bị chặn ở tài nguyên riêng. Không đăng nhập admin, không xuất bản nháp, không gửi Facebook.',
  ...errors.map(e=>'LỖI: '+e),...warnings.map(e=>'CẦN RÀ SOÁT: '+e),''].join('\n');
 fs.writeFileSync('reports/food-live-qa.md',summary);
 if(process.env.GITHUB_STEP_SUMMARY)fs.appendFileSync(process.env.GITHUB_STEP_SUMMARY,summary+'\n');
 console.log(summary);
 if(errors.length)process.exitCode=1;
}
try{await run()}catch(err){
 fs.mkdirSync('reports',{recursive:true});
 const msg=String(err?.message||err);
 fs.writeFileSync('reports/food-live-qa.json',JSON.stringify({readOnly:true,status:'failed',error:msg,checkedAt:new Date().toISOString()},null,2));
 console.error(msg);process.exitCode=1;
}