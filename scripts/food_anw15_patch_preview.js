// ANW-15: disposable, browser-only proof of an address-aware geography fix.
// NEVER deploy this preview directly. Requires window.__FOOD_GEO_PATCH_PREVIEW__ === true.
// The existing ChatGPT Site and its 2,000 drafts are not changed by this file.
// The three public addresses are independently identified by their canonical path.
// Sources: cafegiang.vn/pages/about-us ; guide.michelin.com Pho Khoi Hoi;
// chacathanglong.com.vn ; Hanoi 2025 administrative resolution 1656/NQ-UBTVQH15.
(function(){
  'use strict';
  if(window.__FOOD_GEO_PATCH_PREVIEW__ !== true)return;
  const metadata={
    '/dia-diem/giang/':{province:'Hà Nội',districtLegacy:'Hoàn Kiếm',wardCurrent:'Hoàn Kiếm',wardLegacy:'Lý Thái Tổ',street:'Nguyễn Hữu Huân'},
    '/dia-diem/pho-khoi/':{province:'Hà Nội',districtLegacy:'Hoàn Kiếm',wardCurrent:'Hoàn Kiếm',wardLegacy:'Hàng Vải',street:'Hàng Vải'},
    '/dia-diem/cha-ca/':{province:'Hà Nội',districtLegacy:'Hoàn Kiếm',wardCurrent:'Hoàn Kiếm',wardLegacy:'Cửa Đông',street:'Đường Thành'}
  };
  const fold=s=>String(s||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/đ/gi,'d').toLowerCase().replace(/\s+/g,' ').trim();
  const findCards=()=>[...document.querySelectorAll('a[href^="/dia-diem/"]')].map(a=>{
    const card=a.closest('article,.card,li,[class*="place"],[class*="listing"]')||a.parentElement;
    return {path:a.getAttribute('href'),node:card,link:a};
  }).filter((x,i,arr)=>x.path&&x.node&&arr.findIndex(y=>y.path===x.path)===i);
  const option=(value,text)=>{const o=document.createElement('option');o.value=value;o.textContent=text;return o;};
  const element=(tag,attrs,txt)=>{
    const e=document.createElement(tag);
    Object.entries(attrs).forEach(([key,value])=>e.setAttribute(key,value));
    if(txt!==undefined)e.textContent=txt;
    return e;
  };
  let installed=false;
  function install(){
    if(installed || !location.hash.includes('/directory'))return false;
    const province=document.querySelector('#geo-province');
    const local=document.querySelector('#geo-local');
    const submit=[...document.querySelectorAll('button')].find(b=>fold(b.textContent).includes('tim dia diem'));
    if(!province||!local||!submit)return false;
    const parent=province.parentElement||province;
    const wrapper=element('div',{'data-food-geo-preview':'true','style':'display:flex;gap:12px;flex-wrap:wrap;margin:8px 0;'});
    const makeSelect=(id,labelText)=>{
      const label=element('label',{'for':id,'style':'display:block;min-width:190px;font-size:14px;'},labelText);
      const select=element('select',{'id':id,'aria-label':labelText,'style':'display:block;width:100%;padding:8px;border:1px solid #bbb;border-radius:8px;'});
      select.appendChild(option('Tất cả','Tất cả'));
      select.appendChild(option('Hoàn Kiếm','Hoàn Kiếm'));
      label.appendChild(select);
      wrapper.appendChild(label);
      return select;
    };
    const district=makeSelect('geo-district-legacy','Quận/huyện trước 2025 (tham chiếu)');
    const ward=makeSelect('geo-ward-current','Phường/xã hiện hành');
    parent.insertAdjacentElement('afterend',wrapper);
    const status=element('div',{'role':'status','aria-live':'polite','data-food-geo-count':'true','style':'margin:6px 0;font-size:14px;'});
    submit.insertAdjacentElement('afterend',status);
    const render=()=>{
      const provinceValue=province.value;
      const districtValue=district.value;
      const wardValue=ward.value;
      const query=fold(local.value);
      const cards=findCards();
      let count=0;
      for(const item of cards){
        const data=metadata[item.path];
        // Unknown future listings stay visible only on completely unfiltered directory.
        const known=Boolean(data);
        const provinceOK=provinceValue==='Tất cả'||(known && fold(data.province)===fold(provinceValue));
        const districtOK=districtValue==='Tất cả'||(known && fold(data.districtLegacy)===fold(districtValue));
        const wardOK=wardValue==='Tất cả'||(known && fold(data.wardCurrent)===fold(wardValue));
        const haystack=fold([item.node.textContent,known?data.province:'',known?data.districtLegacy:'',known?data.wardCurrent:'',known?data.wardLegacy:'',known?data.street:''].join(' '));
        const queryOK=!query || haystack.includes(query);
        const show=provinceOK&&districtOK&&wardOK&&queryOK;
        item.node.style.display=show?'':'none';
        if(show)count++;
      }
      status.textContent=count+' địa điểm phù hợp trong '+cards.length+' địa điểm đã xuất bản';
      return count;
    };
    const refresh=()=>{
      const active=fold(province.value)===fold('Hà Nội')||province.value==='Tất cả';
      district.disabled=!active;ward.disabled=!active;
      if(!active){district.value='Tất cả';ward.value='Tất cả';}
      render();
    };
    submit.addEventListener('click',evt=>{
      evt.preventDefault();
      evt.stopImmediatePropagation();
      refresh();
    },true);
    // Capture before framework delegated listeners: preview does not overwrite app state.
    document.addEventListener('click',evt=>{
      if(evt.target===submit||submit.contains(evt.target)){
        evt.preventDefault();evt.stopImmediatePropagation();
        refresh();
      }
    },true);
    province.addEventListener('change',refresh);
    district.addEventListener('change',render);
    ward.addEventListener('change',render);
    local.addEventListener('input',render);
    window.__FOOD_GEO_PATCH_PROOF__={render,getResults:()=>findCards().filter(x=>x.node.getClientRects().length>0&&x.node.style.display!=='none').map(x=>x.path).sort(),count:()=>findCards().length};
    installed=true;
    refresh();
    return true;
  }
  // Nothing mutates the live production application: Playwright alone can set the guard.
  install();
})();
