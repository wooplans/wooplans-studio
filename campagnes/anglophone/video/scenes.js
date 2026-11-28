const {chromium}=require('playwright');const fs=require('fs');
const W='https://www.wooplans.com';
const R={v4005:'/media/public/v4-005/1792274272178--TgaDkj7.webp',d4034:'/media/public/d4-034/1793182644175-gwCmfMaj.webp',v3017:'/media/public/v3-017/1793180527113-CjHuoX5p.webp',v4036:'/media/public/v4-036/1793197388472-724fEdhG.webp',d5012:'/media/public/d5-012/1793182645813-yoMRRalX.webp'};
const C={KE:{price:'KES 8,892',pay:'Pay with M-Pesa'},GH:{price:'GHS 796',pay:'Pay with MTN MoMo'}};
const b64=f=>'data:image/png;base64,'+fs.readFileSync(f).toString('base64');
const css=`*{margin:0;box-sizing:border-box}body{width:1080px;height:1920px;overflow:hidden;font-family:Montserrat,"Segoe UI",Arial,sans-serif;background:#0F5B59;color:#fff;position:relative}
.bg{position:absolute;inset:0}.bg img{width:100%;height:112%;object-fit:cover;object-position:center top}
.shade{position:absolute;inset:0;background:linear-gradient(rgba(7,46,45,.55),transparent 30%,transparent 62%,rgba(7,46,45,.9))}
.cap{position:absolute;left:60px;right:60px;bottom:330px;text-align:center;font-size:76px;font-weight:900;line-height:1.08;text-shadow:0 4px 18px rgba(0,0,0,.6)}
.cap em{font-style:normal;color:#E7C36C}.top{position:absolute;top:150px;left:60px;right:60px;text-align:center;font-size:44px;font-weight:800;color:#E7C36C;letter-spacing:3px;text-transform:uppercase;text-shadow:0 3px 12px rgba(0,0,0,.6)}
.card{position:absolute;left:90px;right:90px;top:400px;bottom:680px;background:#fff;border-radius:40px;overflow:hidden;box-shadow:0 30px 80px rgba(0,0,0,.4)}.card img{width:100%;height:100%;object-fit:contain;background:#fff}
.grid{position:absolute;top:300px;left:50px;right:50px;display:grid;grid-template-columns:1fr 1fr;gap:20px}.grid div{height:470px;border-radius:26px;overflow:hidden}.grid img{width:100%;height:118%;object-fit:cover;object-position:top}
.price{display:inline-block;background:#F08A2E;padding:16px 44px;border-radius:30px;font-size:150px;font-weight:900;letter-spacing:-3px}
.mid{position:absolute;left:0;right:0;top:640px;text-align:center}.pay{display:inline-block;margin-top:40px;background:#fff;color:#0F5B59;font-size:56px;font-weight:900;padding:18px 40px;border-radius:999px}
.big{font-size:96px;font-weight:900;line-height:1.05}.site{position:absolute;bottom:300px;left:0;right:0;text-align:center;font-size:64px;font-weight:900}`;
const scenes=(cc)=>{const c=C[cc];return {
s1:`<div class=bg><img src="${W+R.v4005}?w=1600"></div><div class=shade></div><div class=cap>Planning to build your house?<br><em>Don't pay an architect yet.</em></div>`,
s2:`<div class=top>Inside the catalogue</div><div class=grid>${[R.v3017,R.d5012,R.v4036,R.d4034].map(u=>`<div><img src="${W+u}?w=800"></div>`).join('')}</div><div class=cap style="bottom:300px"><em>100 house plans</em><br>Bungalows & two-story houses<br>3 to 5 bedrooms</div>`,
s3:`<div class=top>For each house</div><div class=card><img src="${W}/api/apercu/plan/1"></div><div class=cap style="bottom:300px">3D renders &<br><em>floor plans with dimensions</em></div>`,
s4:`<div class=top>For each house</div><div class=card><img src="${b64('../prem-calc-'+cc+'.png')}" style="object-fit:cover;object-position:top"></div><div class=cap style="bottom:300px">A calculator:<br><em>what it will cost to build</em></div>`,
s5:`<div class=bg><img src="${W+R.d5012}?w=1600"></div><div class=shade></div><div class=cap><em>12 years</em> of experience<br><em>250+</em> building projects</div>`,
s6:`<div class=top>One price for the whole catalogue</div><div class=mid><span class=price>${c.price}</span></div>`,
s7:`<div class=top>One price for the whole catalogue</div><div class=mid><span class=price>${c.price}</span><br><span class=pay>${c.pay}</span><div class=big style="margin-top:60px">Instant access<br>on your phone</div></div>`,
s8:`<div class=mid style="top:560px"><div class=big>7-day<br><em style="font-style:normal;color:#E7C36C">money-back</em><br>guarantee</div></div>`,
s9:`<div class=bg><img src="${W+R.d4034}?w=1600"></div><div class=shade></div><div class=cap style="bottom:460px">Choose your house today</div><div class=site>wooplans.com</div>`}};
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1080,height:1920}});
for(const cc of ['KE','GH']){const S=scenes(cc);for(const k in S){await p.setContent(`<html><head><style>${css}</style></head><body>${S[k]}</body></html>`,{waitUntil:'networkidle'});await p.waitForTimeout(300);await p.screenshot({path:`${cc}-${k}.png`});}}
await b.close();})();
