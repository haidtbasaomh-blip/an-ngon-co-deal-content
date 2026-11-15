// Private GitHub Issues notification for changed food-site QA problems. No publishing.
import fs from 'node:fs';
const repo=process.env.GITHUB_REPOSITORY||'';
const token=process.env.GITHUB_TOKEN||'';
const runId=process.env.GITHUB_RUN_ID||'';
if(!/^[-\w.]+\/[-\w.]+$/.test(repo)||!token||!runId)throw Error('Missing GitHub Actions environment');
const report=JSON.parse(fs.readFileSync('reports/food-live-qa.json','utf8'));
if(report.status==='healthy'){console.log('Food site QA healthy: no failure notification.');process.exit(0)}
const arr=report.articles||{};
const fields=[
 report.status||'failed',
 (arr.broken||[]).length,
 (arr.missingCanon||[]).length,
 (arr.missingOG||[]).length,
 (arr.missingStructuredData||[]).length,
 (arr.noindexArticles||[]).length,
 (report.errors||[]).length
];
const fingerprint=fields.join('-');
const marker='<!-- FOOD-QA-ALERT signature='+fingerprint+' -->';
const url='https://api.github.com/repos/'+repo+'/issues/1/comments';
const headers={'Accept':'application/vnd.github+json','Authorization':'Bearer '+token,'X-GitHub-Api-Version':'2022-11-28','Content-Type':'application/json','User-Agent':'Food-QA-Actions'};
const response=await fetch(url+'?per_page=100',{headers});
if(!response.ok)throw Error('Cannot read issue alerts: HTTP '+response.status);
const comments=await response.json();
const previous=[...comments].reverse().find(x=>String(x.body||'').includes('FOOD-QA-ALERT signature='));
if(previous&&String(previous.body||'').includes(marker)){console.log('Failure state unchanged; notification deduplicated.');process.exit(0)}
const log='https://github.com/'+repo+'/actions/runs/'+runId;
const body=[
 marker,
 '### ĂN NGON CÓ DEAL — QA nội dung công khai cần xử lý',
 '',
 '- Trạng thái: **'+(report.status||'failed')+'**',
 '- URL bài lỗi: '+(arr.broken||[]).length,
 '- Thiếu canonical: '+(arr.missingCanon||[]).length,
 '- Thiếu OG image: '+(arr.missingOG||[]).length,
 '- Thiếu dữ liệu cấu trúc JSON-LD: '+(arr.missingStructuredData||[]).length,
 '- Bị noindex sai: '+(arr.noindexArticles||[]).length,
 '',
 'Kiểm tra và log: '+log,
 '',
 'Đây là cảnh báo nội bộ, không tự xuất bản bài, không đăng Facebook và không truy cập nháp.'
].join('\n');
const posted=await fetch(url,{method:'POST',headers,body:JSON.stringify({body})});
if(!posted.ok)throw Error('Cannot post issue alert: HTTP '+posted.status);
console.log('Food QA alert created at '+(await posted.json()).html_url);
