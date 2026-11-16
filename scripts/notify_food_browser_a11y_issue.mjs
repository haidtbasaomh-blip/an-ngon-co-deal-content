// Report new WCAG issues to the existing internal GitHub QA issue.
// Never publishes posts, changes the website, or prints credentials.
import fs from 'node:fs';
import {createHash} from 'node:crypto';

const repo=process.env.GITHUB_REPOSITORY||'';
const token=process.env.GITHUB_TOKEN||'';
const run=process.env.GITHUB_RUN_ID||'';
if(!/^[-\w.]+\/[-\w.]+$/.test(repo)||!token||!/^\d+$/.test(run)) throw Error('Missing Actions context');
const path='reports/food-browser-a11y.json';
if(!fs.existsSync(path)){console.log('No audit report; see workflow logs.');process.exit(0)}
const report=JSON.parse(fs.readFileSync(path,'utf8'));
if(report.status!=='FAIL'){console.log('No WCAG failure.');process.exit(0)}
const violations=(report.accessibility?.criticalOrSerious||[]).map(x=>({
 id:String(x.id||'?'),impact:String(x.impact||'?'),count:Number(x.affected||0),
 targets:(x.targets||[]).flatMap(z=>z.target||[]).map(String).slice(0,6).sort()
})).sort((a,b)=>a.id.localeCompare(b.id));
const errors=(report.errors||[]).map(String).sort();
const sig=createHash('sha256').update(JSON.stringify({violations,errors})).digest('hex').slice(0,16);
const marker='<!-- FOOD-BROWSER-A11Y signature='+sig+' -->';
const api='https://api.github.com/repos/'+repo+'/issues/1/comments';
const headers={Accept:'application/vnd.github+json',Authorization:'Bearer '+token,
 'X-GitHub-Api-Version':'2022-11-28','Content-Type':'application/json','User-Agent':'Food-A11y-QA'};
const history=await fetch(api+'?per_page=100',{headers,signal:AbortSignal.timeout(20000)});
if(!history.ok)throw Error('Issue history HTTP '+history.status);
if((await history.json()).some(x=>String(x.body||'').includes(marker))){console.log('Same WCAG state: skip repeat.');process.exit(0)}
const lines=[marker,'### ĂN NGON CÓ DEAL — Accessibility QA cần khắc phục','',
 '- Trạng thái: **'+report.status+'**',
 '- Nhóm vi phạm WCAG nghiêm trọng: **'+violations.length+'**',
 '- Log: https://github.com/'+repo+'/actions/runs/'+run,'',
 ...violations.map(v=>'- **'+v.id+'** ('+v.impact+', '+v.count+' phần tử): '+v.targets.join(' | ').slice(0,500)),
 ...errors.map(e=>'- QA: '+e.slice(0,180)),'',
 'Chỉ sửa site sau khi đối chiếu bản production. Cảnh báo này không sửa web, không đăng Facebook.'];
const response=await fetch(api,{method:'POST',headers,body:JSON.stringify({body:lines.join('\n')}),signal:AbortSignal.timeout(20000)});
if(!response.ok)throw Error('Create alert HTTP '+response.status);
console.log('Created WCAG alert: '+(await response.json()).html_url);
