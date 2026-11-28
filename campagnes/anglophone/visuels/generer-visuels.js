const {chromium}=require('playwright');
const W='https://www.wooplans.com';
const R={v4005:'/media/public/v4-005/1792274272178--TgaDkj7.webp',d4034:'/media/public/d4-034/1793182644175-gwCmfMaj.webp',v3017:'/media/public/v3-017/1793180527113-CjHuoX5p.webp',v4036:'/media/public/v4-036/1793197388472-724fEdhG.webp',d5012:'/media/public/d5-012/1793182645813-yoMRRalX.webp'};
const C={KE:{price:'KES 8,892',pay:'Pay with M-Pesa'},GH:{price:'GHS 796',pay:'Pay with MTN MoMo'}};
const css=`*{margin:0;box-sizing:border-box}body{width:1080px;height:1350px;font-family:Montserrat,"Segoe UI",Arial,sans-serif;background:#0F5B59;color:#fff;overflow:hidden;position:relative}
.img{position:absolute;left:0;right:0;overflow:hidden}.img img{width:100%;height:118%;object-fit:cover;object-position:top}
.top{position:absolute;top:0;left:0;right:0;padding:44px 56px 0}.eyebrow{font-size:30px;font-weight:800;letter-spacing:4px;color:#E7C36C;text-transform:uppercase}
h1{font-size:76px;line-height:1.02;font-weight:900;margin-top:10px;letter-spacing:-1.5px}
.bottom{position:absolute;left:0;right:0;bottom:0;padding:36px 56px 44px;background:linear-gradient(transparent,rgba(7,46,45,.92) 28%)}
.price{display:inline-block;background:#F08A2E;color:#fff;font-size:84px;font-weight:900;padding:6px 26px;border-radius:18px;letter-spacing:-1px}
.sub{font-size:34px;font-weight:700;margin-top:18px;max-width:600px}.pay{position:absolute;right:56px;bottom:52px;background:#fff;color:#0F5B59;font-weight:800;font-size:28px;padding:12px 20px;border-radius:999px}
.logo{position:absolute;right:56px;top:48px;font-weight:900;font-size:30px;letter-spacing:2px}
.grid{position:absolute;top:300px;left:40px;right:40px;display:grid;grid-template-columns:1fr 1fr;gap:16px}.grid div{height:330px;border-radius:18px;overflow:hidden}.grid img{width:100%;height:118%;object-fit:cover;object-position:top}
.phone{position:absolute;top:300px;left:50%;transform:translateX(-50%);width:520px;height:760px;border-radius:44px;border:14px solid #111;overflow:hidden;background:#fff}.phone img{width:100%}`;
function page(id,cc){const c=C[cc];
 if(id==='V1')return `<div class=img style="top:250px;height:820px"><img src="${W+R.v4005}?w=1600"></div><div class=top><div class=eyebrow>4 Bedroom Bungalow · 201 <span style="text-transform:none">m²</span></div><h1>100 house plans.<br>One price.</h1></div><div class=logo>WOOPLANS</div><div class=bottom><span class=price>${c.price}</span><div class=sub>3D renders · floor plans · cost calculator</div></div><div class=pay>${c.pay}</div>`;
 if(id==='V2')return `<div class=img style="top:250px;height:820px"><img src="${W+R.d4034}?w=1600"></div><div class=top><div class=eyebrow>Two-story · 4 bedrooms</div><h1>Built for a narrow plot:<br>12 × 17 m</h1></div><div class=logo>WOOPLANS</div><div class=bottom><span class=price>${c.price}</span><div class=sub>This house + 99 more house plans</div></div><div class=pay>${c.pay}</div>`;
 if(id==='V3')return `<div class=top><div class=eyebrow>Bungalows & two-story houses</div><h1>100 house plans for the price of one</h1></div><div class=grid>${[R.v3017,R.v4036,R.d5012,R.d4034].map(u=>`<div><img src="${W+u}?w=800"></div>`).join('')}</div><div class=bottom><span class=price>${c.price}</span><div class=sub>Instant access on your phone</div></div><div class=pay>${c.pay}</div>`;
 if(id==='V4')return `<div class=top><div class=eyebrow>Before you build</div><h1>Know your building budget</h1></div><div class=phone><img src="data:image/png;base64,${require('fs').readFileSync(__dirname+'/../prem-calc-'+cc+'.png').toString('base64')}"></div><div class=bottom><span class=price>${c.price}</span><div class=sub>Cost calculator for every house</div></div><div class=pay>${c.pay}</div>`;
}
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1080,height:1350},deviceScaleFactor:1});
for(const cc of ['KE','GH'])for(const id of ['V1','V2','V3','V4']){
 await p.setContent(`<html><head><style>${css}</style></head><body>${page(id,cc)}</body></html>`,{waitUntil:'networkidle'});await p.waitForTimeout(500);
 await p.screenshot({path:`EN-${id}-${cc}.png`});}
await b.close();})();
