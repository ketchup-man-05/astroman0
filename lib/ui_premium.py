"""Premium theme for Astroman AI. Hides every trace of default Streamlit chrome."""
import os, base64
import streamlit as st
import streamlit.components.v1 as components
from . import icons

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GOLD = "#c9a227"

# ---------------------------------------------------------------- logo ---
def logo_data_uri():
    for name in ("logo.png", "logo.jpg", "logo.webp", "logo.svg"):
        p = os.path.join(ROOT, "assets", name)
        if os.path.exists(p):
            with open(p, "rb") as f:
                ext = "svg+xml" if name.endswith("svg") else name.rsplit(".", 1)[1]
                return f"data:image/{ext};base64," + base64.b64encode(f.read()).decode()
    return None

def logo_mark(size=40):
    """Real logo if assets/logo.* exists, else a celestial SVG wordmark (no emoji)."""
    uri = logo_data_uri()
    if uri:
        return f"<img src='{uri}' height='{size}' style='border-radius:50%;vertical-align:middle'>"
    return (
        f"<svg width='{size}' height='{size}' viewBox='0 0 48 48' style='vertical-align:middle'>"
        "<circle cx='24' cy='24' r='21' fill='none' stroke='#c9a227' stroke-width='2'/>"
        "<ellipse cx='24' cy='24' rx='21' ry='8' fill='none' stroke='#c9a227' stroke-width='1' opacity='.55' transform='rotate(-24 24 24)'/>"
        "<path d='M24 10 L33 34 L27.5 34 L24 24 L20.5 34 L15 34 Z' fill='#c9a227'/>"
        "<circle cx='35' cy='13' r='2.2' fill='#f5f0e6'/></svg>"
    )

# --------------------------------------------------------------- css ----
def inject():
    st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Marcellus&family=Manrope:wght@300;400;500;600;700&display=swap');

/* ---- kill default chrome ---- */
header[data-testid="stHeader"], #MainMenu, footer,
div[data-testid="stToolbar"], .stAppDeployButton,
div[data-testid="stDecoration"], div[data-testid="stStatusWidget"] {display:none !important;}
section[data-testid="stSidebar"] {display:none !important;}

/* ---- full bleed canvas ---- */
.block-container {max-width:100% !important; padding:0 !important; margin:0 !important;}
div[data-testid="stVerticalBlock"] > div {padding-top:0;}

body, .stApp {background:#0a0d1a !important; color:#f5f0e6;
  font-family:'Manrope',system-ui,sans-serif !important;}
h1,h2,h3,.serif {font-family:'Marcellus',serif !important; letter-spacing:.02em;}

.wrap {max-width:1080px; margin:0 auto; padding:0 28px;}
.wrap-narrow {max-width:760px; margin:0 auto; padding:0 24px;}
.gold-text {background:linear-gradient(120deg,#f0d060 10%,#c9a227 45%,#f7e7a8 70%,#c9a227 95%);
  -webkit-background-clip:text; background-clip:text; color:transparent;}
.muted {color:#9aa0b4;}
.eyebrow {text-transform:uppercase; letter-spacing:.32em; font-size:.72rem; color:#c9a227; font-weight:600;}

/* ---- top nav ---- */
.topnav {position:sticky; top:0; z-index:50; backdrop-filter:blur(14px);
  background:rgba(10,13,26,.78); border-bottom:1px solid rgba(201,162,39,.22);}
.topnav-inner {max-width:1080px; margin:0 auto; padding:14px 28px;
  display:flex; align-items:center; justify-content:space-between; gap:12px; flex-wrap:wrap;}
.brand {display:flex; align-items:center; gap:12px; text-decoration:none;}
.brand-name {font-family:'Marcellus',serif; font-size:1.25rem; color:#f5f0e6; letter-spacing:.06em;}
.brand-name b {color:#c9a227; font-weight:400;}
.navlinks {display:flex; gap:6px; flex-wrap:wrap;}
.navlinks a {color:#c9c9d4; text-decoration:none; font-size:.92rem; font-weight:500;
  padding:9px 16px; border-radius:999px; transition:all .25s;}
.navlinks a:hover {color:#f5f0e6; background:rgba(201,162,39,.12);}
.navlinks a.active {color:#0a0d1a; background:linear-gradient(135deg,#c9a227,#f0d060); font-weight:700;}

/* ---- premium cards ---- */
.pcard {background:linear-gradient(160deg,rgba(255,255,255,.055),rgba(255,255,255,.015));
  border:1px solid rgba(201,162,39,.28); border-radius:20px; padding:28px; margin:16px 0;
  box-shadow:0 18px 50px rgba(0,0,0,.35); transition:transform .35s, box-shadow .35s, border-color .35s;}
.pcard:hover {transform:translateY(-4px); border-color:rgba(201,162,39,.55);
  box-shadow:0 26px 60px rgba(0,0,0,.45), 0 0 40px rgba(201,162,39,.08);}
.pcard h3 {margin-top:.4rem;}

/* ---- buttons (override streamlit) ---- */
.stButton > button, .stDownloadButton > button {
  background:linear-gradient(135deg,#c9a227,#e8c84a) !important; color:#141428 !important;
  border:none !important; border-radius:999px !important; font-weight:700 !important;
  padding:.8rem 2.2rem !important; font-size:1rem !important; letter-spacing:.02em;
  box-shadow:0 10px 30px rgba(201,162,39,.35) !important; transition:all .3s !important;
  position:relative; overflow:hidden;}
.stButton > button:hover, .stDownloadButton > button:hover {
  transform:translateY(-2px) !important; box-shadow:0 16px 40px rgba(201,162,39,.5) !important;}
.stButton > button[kind="secondary"] {
  background:rgba(201,162,39,.08) !important; color:#f5f0e6 !important;
  border:1px solid rgba(201,162,39,.5) !important; box-shadow:none !important;}

/* ---- inputs ---- */
.stTextInput input, .stNumberInput input, .stSelectbox [data-baseweb="select"] {
  background:rgba(255,255,255,.05) !important; border:1px solid rgba(201,162,39,.35) !important;
  border-radius:14px !important; color:#f5f0e6 !important; padding:.7rem 1rem !important;}
.stTextInput input:focus, .stNumberInput input:focus {
  border-color:#c9a227 !important; box-shadow:0 0 0 3px rgba(201,162,39,.18) !important;}

/* ---- reveal on scroll ---- */
.reveal {opacity:0; transform:translateY(28px); transition:opacity .8s ease, transform .8s ease;}
.reveal.visible {opacity:1; transform:none;}

/* ---- footer ---- */
.site-footer {border-top:1px solid rgba(201,162,39,.2); margin-top:70px; padding:36px 28px;
  text-align:center; color:#9aa0b4; font-size:.88rem;}
.site-footer .brand-name {font-size:1.05rem;}

/* misc */
hr {border-color:rgba(201,162,39,.18) !important;}
a {color:#e8c84a;}
.stExpander {border:1px solid rgba(201,162,39,.25) !important; border-radius:14px !important;
  background:rgba(255,255,255,.03) !important;}
</style>
<script>
const io = new IntersectionObserver(es => es.forEach(e => {
  if (e.isIntersecting) { e.target.classList.add('visible'); io.unobserve(e.target); }
}), {threshold:.12});
function watchReveals(){ document.querySelectorAll('.reveal:not(.visible)').forEach(el => io.observe(el)); }
watchReveals();
new MutationObserver(watchReveals).observe(document.body, {childList:true, subtree:true});
</script>""", unsafe_allow_html=True)

# ---------------------------------------------------------------- nav ---
def nav(active="home"):
    links = [("home", "Home", "/"), ("ask", "Ask a Question", "/Astroman_AI"),
             ("help", "Help", "/Help"), ("reviews", "Reviews", "/Reviews")]
    items = "".join(
        f"<a href='{href}' class='{'active' if key == active else ''}'>{label}</a>"
        for key, label, href in links)
    st.markdown(f"""<div class="topnav"><div class="topnav-inner">
      <a class="brand" href="/" target="_self">{logo_mark(38)}
        <span class="brand-name">ASTROMAN <b>AI</b></span></a>
      <div class="navlinks">{items}</div></div></div>""", unsafe_allow_html=True)

# ---------------------------------------------------------------- hero --
_HERO = """<div id="hero" style="position:relative;height:600px;overflow:hidden;
  background:radial-gradient(1200px 600px at 50% -10%,#1b2348 0%,#0a0d1a 60%);">
<canvas id="stars" style="position:absolute;inset:0;width:100%;height:100%"></canvas>
<div id="zwrap" style="position:absolute;left:50%;top:46%;width:640px;height:640px;
  transform:translate(-50%,-50%);opacity:.16;pointer-events:none">
  <div id="zring" style="width:100%;height:100%;position:relative;animation:spin 140s linear infinite">
  @@GLYPHS@@
  <div style="position:absolute;inset:60px;border:1px solid #c9a227;border-radius:50%"></div>
  <div style="position:absolute;inset:110px;border:1px dashed #c9a227;border-radius:50%;opacity:.6"></div>
  </div></div>
<div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;
  justify-content:center;text-align:center;padding:0 24px">
  <div style="letter-spacing:.4em;font-size:.75rem;color:#c9a227;font-weight:600;margin-bottom:18px">
  KRISHNAMURTI PADDHATI &nbsp;·&nbsp; PRASHNA KUNDLI</div>
  <div style="font-family:Marcellus,serif;font-size:clamp(2.4rem,6vw,4.2rem);line-height:1.12;
    background:linear-gradient(120deg,#f7e7a8,#c9a227 55%,#f0d060);-webkit-background-clip:text;
    background-clip:text;color:transparent;max-width:900px">
    Ask the question.<br>The stars do the mathematics.</div>
  <p style="color:#c9c9d4;max-width:620px;font-size:1.06rem;margin:22px 0 30px;font-weight:300">
    A KP horary reading — cast for the exact moment you ask, decided by the sub-lord,
    scored from −8 to +8. Instant. Free. Honest.</p>
  <a href="/Astroman_AI" target="_top" id="cta">Ask Your Question
    <span style="margin-left:10px">→</span></a>
  <div style="margin-top:26px;color:#9aa0b4;font-size:.85rem;letter-spacing:.08em">
    Free forever &nbsp;·&nbsp; No account needed &nbsp;·&nbsp; Your question stays private</div>
</div>
<div style="position:absolute;bottom:18px;left:50%;transform:translateX(-50%);color:#c9a227;
  font-size:.7rem;letter-spacing:.35em;animation:bob 2.6s ease-in-out infinite">SCROLL</div>
</div>
<style>
#cta{position:relative;overflow:hidden;display:inline-block;background:linear-gradient(135deg,#c9a227,#f0d060);
  color:#141428 !important;font-weight:700;font-size:1.08rem;padding:1rem 3rem;border-radius:999px;
  text-decoration:none;box-shadow:0 14px 44px rgba(201,162,39,.4);transition:transform .3s,box-shadow .3s;}
#cta:hover{transform:translateY(-3px) scale(1.02);box-shadow:0 20px 60px rgba(201,162,39,.55);}
#cta::after{content:'';position:absolute;top:0;left:-80%;width:50%;height:100%;
  background:linear-gradient(100deg,transparent,rgba(255,255,255,.55),transparent);
  transform:skewX(-20deg);animation:shimmer 3.2s ease-in-out infinite;}
@keyframes shimmer{0%{left:-80%}55%,100%{left:160%}}
@keyframes spin{to{transform:rotate(360deg)}}
@keyframes bob{0%,100%{transform:translate(-50%,0);opacity:.5}50%{transform:translate(-50%,8px);opacity:1}}
</style>
<script>
(function(){
const cv=document.getElementById('stars'),ctx=cv.getContext('2d');let W,H,stars=[],shoots=[];
function size(){W=cv.width=cv.offsetWidth;H=cv.height=cv.offsetHeight;
  stars=Array.from({length:190},()=>({x:Math.random()*W,y:Math.random()*H,
    r:Math.random()*1.4+.3,p:Math.random()*6.28,s:.5+Math.random()*1.5}));}
size();window.addEventListener('resize',size);
function spawnShoot(){shoots.push({x:Math.random()*W*.8,y:Math.random()*H*.3,
  vx:-(6+Math.random()*4),vy:3+Math.random()*2,life:1});
  setTimeout(spawnShoot,3500+Math.random()*4500);}
setTimeout(spawnShoot,2000);
let t=0;(function loop(){t+=.016;ctx.clearRect(0,0,W,H);
for(const st of stars){st.p+=.02*st.s;
  ctx.globalAlpha=.25+.65*Math.abs(Math.sin(st.p));
  ctx.fillStyle='#f5f0e6';ctx.beginPath();ctx.arc(st.x,st.y,st.r,0,6.28);ctx.fill();}
ctx.globalAlpha=1;
for(let i=shoots.length-1;i>=0;i--){const s=shoots[i];s.x+=s.vx;s.y+=s.vy;s.life-=.016;
  if(s.life<=0){shoots.splice(i,1);continue;}
  const g=ctx.createLinearGradient(s.x,s.y,s.x-s.vx*10,s.y-s.vy*10);
  g.addColorStop(0,'rgba(240,208,96,'+(.9*s.life)+')');g.addColorStop(1,'rgba(240,208,96,0)');
  ctx.strokeStyle=g;ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(s.x,s.y);
  ctx.lineTo(s.x-s.vx*10,s.y-s.vy*10);ctx.stroke();}
requestAnimationFrame(loop);})();
</script>"""

def hero():
    glyphs = "♈♉♊♋♌♍♎♏♐♑♒♓"
    spans = "".join(
        f"<span style='position:absolute;left:50%;top:50%;color:#c9a227;font-size:26px;"
        f"transform:rotate({i*30}deg) translateY(-296px) rotate({-i*30}deg)'>{g}</span>"
        for i, g in enumerate(glyphs))
    html = _HERO.replace("@@GLYPHS@@", spans)
    components.html(html, height=600, scrolling=False)

# -------------------------------------------------------------- verdict -
_VERDICT = """<div style="font-family:Manrope,sans-serif;max-width:680px;margin:0 auto">
<div class="vstep" style="background:linear-gradient(135deg,rgba(201,162,39,.14),rgba(43,58,103,.35));
  border:1px solid #c9a227;border-radius:22px;padding:34px;text-align:center;
  box-shadow:0 24px 70px rgba(0,0,0,.5),0 0 60px rgba(201,162,39,.1)">
  <div style="letter-spacing:.35em;font-size:.72rem;color:#c9a227;font-weight:600">YOUR READING</div>
  <div style="font-family:Marcellus,serif;font-size:2rem;margin:14px 0;line-height:1.3">@@HEADLINE@@</div>
  <div style="display:flex;align-items:center;justify-content:center;gap:18px;margin:20px 0">
    <div style="width:120px;height:120px;border-radius:50%;border:3px solid #c9a227;
      display:flex;flex-direction:column;align-items:center;justify-content:center;
      background:radial-gradient(circle,rgba(201,162,39,.18),transparent 70%)">
      <div id="scoreNum" data-target="@@SCORE@@" style="font-size:2.4rem;font-weight:700;color:#f0d060">0</div>
      <div style="font-size:.68rem;color:#9aa0b4;letter-spacing:.15em">KP SCORE</div>
    </div></div>
  <p style="color:#d8d4c4;font-size:1.02rem;line-height:1.7;max-width:560px;margin:0 auto">@@STORY@@</p>
  <div style="margin-top:16px;color:#9aa0b4;font-size:.9rem">@@BAND@@</div>
</div></div>
<style>.vstep{opacity:0;transform:translateY(30px) scale(.98);animation:vin .9s ease forwards}
@keyframes vin{to{opacity:1;transform:none}}</style>
<script>(function(){const el=document.getElementById('scoreNum');
const target=parseInt(el.dataset.target,10);const t0=performance.now(),D=1400;
function f(t){const p=Math.min(1,(t-t0)/D),e=1-Math.pow(1-p,3);
  el.textContent=(target<0?'−':'+')+Math.round(Math.abs(target)*e);
  if(p<1)requestAnimationFrame(f);else el.textContent=(target<0?'−':'+')+Math.abs(target);}
requestAnimationFrame(f);})();</script>"""

def verdict_card(headline, story, score, band):
    html = (_VERDICT.replace("@@HEADLINE@@", headline).replace("@@STORY@@", story)
            .replace("@@SCORE@@", str(score)).replace("@@BAND@@", band))
    components.html(html, height=460, scrolling=False)

# --------------------------------------------------------------- footer -
def footer():
    st.markdown("""<div class="site-footer"><div class="wrap">""" +
        logo_mark(30) +
        """<div class="brand-name" style="margin:10px 0">ASTROMAN <b style="color:#c9a227">AI</b></div>
<div>KP Prashna Kundli · honest astrology, stated plainly.</div>
<div class="muted" style="margin-top:8px">For reflection and guidance — not a substitute for professional advice.</div>
</div></div>""", unsafe_allow_html=True)

def section_head(eyebrow, title, sub=""):
    st.markdown(f"""<div class="wrap" style="text-align:center;margin:56px auto 8px">
      <div class="eyebrow">{eyebrow}</div>
      <h2 style="font-size:2rem;margin:.6rem 0" class="serif">{title}</h2>
      <p class="muted" style="max-width:640px;margin:0 auto">{sub}</p></div>""",
                unsafe_allow_html=True)
