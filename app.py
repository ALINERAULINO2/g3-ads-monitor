#!/usr/bin/env python3
"""G3 Ads Monitor — Dashboard Online · Meta Ads API"""
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import requests
import os
import base64
from datetime import datetime, timedelta, date
from pathlib import Path

st.set_page_config(
    page_title="G3 Ads Monitor",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Credenciais ──────────────────────────────────────────────────────────────
try:
    TOKEN   = st.secrets["META_ACCESS_TOKEN"]
    ACCOUNT = st.secrets["META_AD_ACCOUNT_ID"]
except Exception:
    TOKEN   = os.getenv("META_ACCESS_TOKEN", "")
    ACCOUNT = os.getenv("META_AD_ACCOUNT_ID", "")

BASE   = "https://graph.facebook.com/v20.0"
ORANGE = "#F7931E"
DARK   = "#111111"
CARD   = "#1a1a1a"
BORDER = "#2a2a2a"
TEXT   = "#e5e7eb"
MUTED  = "#6b7280"

# ─── Logo ─────────────────────────────────────────────────────────────────────
_LOGO = Path(__file__).parent / "logo.png"
_logo_data = base64.b64encode(_LOGO.read_bytes()).decode() if _LOGO.exists() else None

def logo_img(w=160):
    if _logo_data:
        return f'<img src="data:image/png;base64,{_logo_data}" style="width:{w}px;height:auto;display:block;">'
    return '<span style="color:#F7931E;font-size:20px;font-weight:900;">G3 VEICULOS</span>'

# ─── CSS (apenas estilos G3 personalizados — tema base vem do config.toml) ────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
#MainMenu, footer { visibility: hidden; }
.block-container { padding-top: 0.8rem !important; }

/* ── Cabeçalho ── */
.g3-header {
    background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%);
    border: 1px solid #2a2a2a;
    border-left: 5px solid #F7931E;
    border-radius: 12px;
    padding: 16px 22px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 18px;
}
.g3-title { color: #fff; font-size: 22px; font-weight: 900; letter-spacing: -0.5px; }
.g3-title span { color: #F7931E; }
.g3-sub   { color: #6b7280; font-size: 11px; margin-top: 4px; }
.g3-badge { background: #F7931E; color: #000; font-size: 10px; font-weight: 800;
             padding: 5px 14px; border-radius: 6px; white-space: nowrap; }

/* ── KPI cards ── */
.kpi-wrap { display: flex; gap: 12px; margin-bottom: 16px; flex-wrap: wrap; }
.kpi-card {
    flex: 1; min-width: 130px;
    background: #1a1a1a;
    border: 1px solid #2a2a2a;
    border-radius: 10px;
    padding: 14px 16px;
    border-top: 4px solid #F7931E;
}
.kpi-lbl  { font-size: 9px; color: #6b7280; text-transform: uppercase;
             letter-spacing: .7px; font-weight: 700; margin-bottom: 6px; }
.kpi-val  { font-size: 23px; font-weight: 900; color: #fff; line-height: 1.1; }
.kpi-delta{ font-size: 11px; margin-top: 5px; }
.kpi-sub  { font-size: 10px; color: #6b7280; margin-top: 3px; }
.up  { color: #4ade80; } .dn { color: #f87171; } .neu { color: #6b7280; }

/* ── Seção ── */
.sec-hd {
    font-size: 11px; font-weight: 800; color: #e5e7eb;
    border-left: 4px solid #F7931E;
    padding-left: 10px; margin: 20px 0 12px;
    text-transform: uppercase; letter-spacing: .5px;
}

/* ── Alertas ── */
.al { padding: 10px 16px; border-left: 4px solid;
      border-radius: 0 8px 8px 0; margin-bottom: 8px; font-size: 12px; line-height: 1.6; }
.al-red { background: #2d0a0a; border-color: #f87171; color: #fca5a5; }
.al-yel { background: #2d2000; border-color: #fbbf24; color: #fde68a; }
.al-grn { background: #052d16; border-color: #4ade80; color: #86efac; }

/* ── Sidebar ── */
.sb-sec { font-size: 10px; font-weight: 800; color: #F7931E;
          text-transform: uppercase; letter-spacing: .6px; margin: 14px 0 5px; }

/* ── Freq badge ── */
.freq-ok  { color: #4ade80; font-weight: 800; }
.freq-med { color: #fbbf24; font-weight: 800; }
.freq-bad { color: #f87171; font-weight: 800; }

/* ── Tabela customizada ── */
.g3-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.g3-table th {
    background: #1a1a1a; color: #F7931E; font-weight: 700; font-size: 10px;
    text-transform: uppercase; letter-spacing: .5px;
    padding: 8px 10px; border-bottom: 2px solid #F7931E; text-align: left;
}
.g3-table td { padding: 8px 10px; border-bottom: 1px solid #2a2a2a; color: #e5e7eb; }
.g3-table tr:hover td { background: #222; }
.g3-table .num { text-align: right; font-variant-numeric: tabular-nums; }
.badge-escalar   { background:#052d16; color:#4ade80; padding:2px 8px; border-radius:4px; font-size:10px; font-weight:700; }
.badge-pausar    { background:#2d0a0a; color:#f87171; padding:2px 8px; border-radius:4px; font-size:10px; font-weight:700; }
.badge-monitorar { background:#172554; color:#93c5fd; padding:2px 8px; border-radius:4px; font-size:10px; font-weight:700; }
.badge-aguardar  { background:#1c1917; color:#a8a29e; padding:2px 8px; border-radius:4px; font-size:10px; font-weight:700; }
/* ── Status do anúncio ── */
.st-ativo       { background:#052d16; color:#4ade80; padding:2px 8px; border-radius:4px; font-size:10px; font-weight:700; }
.st-pausado     { background:#2d2000; color:#fbbf24; padding:2px 8px; border-radius:4px; font-size:10px; font-weight:700; }
.st-reprovado   { background:#2d0a0a; color:#f87171; padding:2px 8px; border-radius:4px; font-size:10px; font-weight:700; }
.st-arquivado   { background:#1c1917; color:#78716c; padding:2px 8px; border-radius:4px; font-size:10px; font-weight:700; }
.st-revisao     { background:#1e1b4b; color:#a5b4fc; padding:2px 8px; border-radius:4px; font-size:10px; font-weight:700; }
.st-problema    { background:#2d1500; color:#fb923c; padding:2px 8px; border-radius:4px; font-size:10px; font-weight:700; }
.st-desconhecido{ background:#111; color:#6b7280; padding:2px 8px; border-radius:4px; font-size:10px; font-weight:700; }

/* ── Mobile ── */
@media (max-width: 768px) {
    .block-container { padding: 0.4rem 0.4rem !important; }

    /* Header empilhado */
    .g3-header { flex-direction: column; align-items: flex-start; gap: 10px; padding: 12px 14px; }
    .g3-header > div:first-child { flex-direction: column; gap: 8px; }
    .g3-title { font-size: 18px; }
    .g3-sub   { font-size: 10px; }
    .g3-badge { font-size: 9px; padding: 4px 10px; align-self: flex-start; }

    /* KPI cards: 2 por linha */
    .kpi-wrap { gap: 8px; }
    .kpi-card { min-width: calc(50% - 4px) !important; flex: 1 1 calc(50% - 4px) !important;
                padding: 10px 12px; }
    .kpi-val  { font-size: 17px !important; }
    .kpi-lbl  { font-size: 8px !important; }
    .kpi-sub, .kpi-delta { font-size: 10px !important; }

    /* Colunas Streamlit empilham */
    [data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; }
    [data-testid="column"] { min-width: 100% !important; width: 100% !important; }

    /* Tabela menor */
    .g3-table { font-size: 11px; }
    .g3-table th { font-size: 9px; padding: 6px 8px; }
    .g3-table td { padding: 6px 8px; }

    /* Alertas */
    .al { font-size: 11px; padding: 8px 12px; }

    /* Seção */
    .sec-hd { font-size: 10px; margin: 14px 0 8px; }

    /* Glossario: 1 coluna */
    .gloss-grid { grid-template-columns: 1fr !important; }
}

/* ── Print ── */
@media print {
    [data-testid="stSidebar"], [data-testid="stHeader"],
    .stButton, .element-container:has(.stButton) { display: none !important; }
    .g3-header { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
    .block-container { padding: 0 !important; }
}
</style>
""", unsafe_allow_html=True)


# ─── API ─────────────────────────────────────────────────────────────────────
def _api(endpoint, params=None):
    p = {"access_token": TOKEN}
    if params:
        p.update(params)
    try:
        r = requests.get(f"{BASE}/{endpoint}", params=p, timeout=30)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

@st.cache_data(ttl=3600, show_spinner=False)
def check_token():
    return "error" not in _api("me", {"fields": "id"})

@st.cache_data(ttl=900, show_spinner=False)
def get_conta(since, until):
    d = _api(f"{ACCOUNT}/insights", {
        "fields": "impressions,reach,clicks,spend,ctr,cpc,cpm,frequency,actions",
        "time_range": f'{{"since":"{since}","until":"{until}"}}',
        "level": "account",
    })
    return (d.get("data") or [{}])[0]

@st.cache_data(ttl=900, show_spinner=False)
def get_serie(since, until):
    d = _api(f"{ACCOUNT}/insights", {
        "fields": "spend,ctr,impressions,clicks,actions",
        "time_range": f'{{"since":"{since}","until":"{until}"}}',
        "time_increment": 1, "level": "account",
    })
    return sorted(d.get("data", []), key=lambda x: x.get("date_start", ""))

@st.cache_data(ttl=900, show_spinner=False)
def get_campanhas(since, until):
    d = _api(f"{ACCOUNT}/insights", {
        "fields": "campaign_id,campaign_name,impressions,reach,clicks,spend,ctr,cpc,cpm,frequency,actions",
        "time_range": f'{{"since":"{since}","until":"{until}"}}',
        "level": "campaign", "limit": 50,
    })
    return sorted(d.get("data", []), key=lambda x: float(x.get("spend", 0)), reverse=True)

@st.cache_data(ttl=900, show_spinner=False)
def get_ads(since, until):
    d = _api(f"{ACCOUNT}/insights", {
        "fields": "ad_id,ad_name,campaign_name,adset_name,impressions,clicks,spend,ctr,cpc,cpm,frequency,actions",
        "time_range": f'{{"since":"{since}","until":"{until}"}}',
        "level": "ad", "limit": 200,
    })
    return sorted(d.get("data", []), key=lambda x: float(x.get("spend", 0)), reverse=True)

@st.cache_data(ttl=900, show_spinner=False)
def get_campaign_statuses():
    """Busca status atual de todas as campanhas."""
    result, after = {}, None
    for _ in range(5):
        params = {"fields": "id,status,effective_status", "limit": 200}
        if after:
            params["after"] = after
        d = _api(f"{ACCOUNT}/campaigns", params)
        for camp in d.get("data", []):
            result[camp["id"]] = camp.get("effective_status", "UNKNOWN")
        after = d.get("paging", {}).get("cursors", {}).get("after")
        if not after or not d.get("data"):
            break
    return result

@st.cache_data(ttl=900, show_spinner=False)
def get_ad_statuses():
    """Busca status atual de todos os anúncios (não vem no insights)."""
    result, after = {}, None
    for _ in range(10):  # máx 10 páginas
        params = {"fields": "id,status,effective_status,name", "limit": 200}
        if after:
            params["after"] = after
        d = _api(f"{ACCOUNT}/ads", params)
        for ad in d.get("data", []):
            result[ad["id"]] = {
                "status":           ad.get("status", "UNKNOWN"),
                "effective_status": ad.get("effective_status", "UNKNOWN"),
            }
        after = d.get("paging", {}).get("cursors", {}).get("after")
        if not after or not d.get("data"):
            break
    return result


# ─── Helpers ─────────────────────────────────────────────────────────────────
def leads_de(actions):
    TIPOS = {"onsite_conversion.messaging_conversation_started_7d",
             "lead", "offsite_conversion.fb_pixel_lead", "omni_complete_registration"}
    total, seen = 0, set()
    for a in (actions or []):
        t = a.get("action_type", "")
        if t in TIPOS and t not in seen:
            total += int(float(a.get("value", 0)))
            seen.add(t)
    return total

def brl(v):
    try:
        return f"R$ {float(v):,.2f}".replace(",","X").replace(".",",").replace("X",".")
    except Exception:
        return "R$ 0,00"

def pct(v):
    try: return f"{float(v):.2f}%"
    except Exception: return "—"

def delta_html(a, b, inv=False):
    try:
        if not b or float(b) == 0: return '<span class="neu">—</span>'
        v = (float(a) - float(b)) / float(b) * 100
        sobe = (v >= 0) if not inv else (v < 0)
        return f'<span class="{"up" if sobe else "dn"}">{"▲" if v>=0 else "▼"} {abs(v):.1f}% vs ant.</span>'
    except Exception:
        return '<span class="neu">—</span>'

def kpi_card(lbl, val, dh="", sub=""):
    s = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    return (f'<div class="kpi-card"><div class="kpi-lbl">{lbl}</div>'
            f'<div class="kpi-val">{val}</div><div class="kpi-delta">{dh}</div>{s}</div>')

def rec_badge(spend, ctr_, freq_, media_ctr):
    try:
        if float(freq_) > 3.5 or (float(spend) > 30 and float(ctr_) < float(media_ctr) * 0.5):
            return "PAUSAR"
        if float(ctr_) >= float(media_ctr) * 1.25 and float(spend) >= 30:
            return "ESCALAR"
        if float(spend) < 10:
            return "AGUARDAR"
        return "MONITORAR"
    except Exception:
        return "AGUARDAR"

def badge_html(b):
    m = {"ESCALAR":"escalar","PAUSAR":"pausar","MONITORAR":"monitorar","AGUARDAR":"aguardar"}
    return f'<span class="badge-{m[b]}">{b}</span>'

_STATUS_MAP = {
    # effective_status (prioridade — reflete estado real incluindo campanha/conjunto pai)
    "ACTIVE":           ("st-ativo",        "ATIVO"),
    "PAUSED":           ("st-pausado",      "PAUSADO"),
    "CAMPAIGN_PAUSED":  ("st-pausado",      "CAMPANHA PAUSADA"),
    "ADSET_PAUSED":     ("st-pausado",      "CONJUNTO PAUSADO"),
    "DISAPPROVED":      ("st-reprovado",    "REPROVADO"),
    "PENDING_REVIEW":   ("st-revisao",      "EM REVISAO"),
    "IN_PROCESS":       ("st-revisao",      "PROCESSANDO"),
    "WITH_ISSUES":      ("st-problema",     "COM PROBLEMA"),
    "ARCHIVED":         ("st-arquivado",    "ARQUIVADO"),
    "DELETED":          ("st-arquivado",    "DELETADO"),
}

def status_html(ad_id, statuses_dict):
    info = statuses_dict.get(str(ad_id), {})
    eff  = info.get("effective_status", "UNKNOWN")
    cls, label = _STATUS_MAP.get(eff, ("st-desconhecido", eff))
    return f'<span class="{cls}">{label}</span>'

def _chart_layout(fig, height=340):
    fig.update_layout(
        height=height, margin=dict(l=0, r=10, t=30, b=0),
        paper_bgcolor=CARD, plot_bgcolor="#141414",
        font=dict(family="Inter, sans-serif", color=TEXT, size=11),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
                    font_size=11, bgcolor="rgba(0,0,0,0)", borderwidth=0),
        bargap=0.28, hovermode="x unified",
        hoverlabel=dict(bgcolor="#222", font_color=TEXT, bordercolor=BORDER),
    )
    fig.update_xaxes(gridcolor="#222", tickcolor=MUTED, linecolor=BORDER, color=MUTED)
    fig.update_yaxes(gridcolor="#222", tickcolor=MUTED, linecolor=BORDER, color=MUTED)
    return fig

_HTML_COLS = {"Campanha","Anuncio","Conjunto","Acao","Status"}

def html_table(rows, cols):
    """Renderiza tabela HTML customizada com tema escuro."""
    ths = "".join(f"<th>{c}</th>" for c in cols)
    trs = ""
    for row in rows:
        tds = "".join(
            f'<td>{row.get(c,"—")}</td>' if c in _HTML_COLS
            else f'<td class="num">{row.get(c,"—")}</td>'
            for c in cols
        )
        trs += f"<tr>{tds}</tr>"
    return f'<div style="overflow-x:auto;"><table class="g3-table"><thead><tr>{ths}</tr></thead><tbody>{trs}</tbody></table></div>'


# ─── Presets de data ──────────────────────────────────────────────────────────
def _last_month():
    today = date.today()
    fim = today.replace(day=1) - timedelta(1)
    return fim.replace(day=1), fim

PRESETS = {
    "Hoje":            (date.today(), date.today()),
    "Ontem":           (date.today()-timedelta(1), date.today()-timedelta(1)),
    "Ultimos 7 dias":  (date.today()-timedelta(7), date.today()-timedelta(1)),
    "Ultimos 14 dias": (date.today()-timedelta(14), date.today()-timedelta(1)),
    "Ultimos 30 dias": (date.today()-timedelta(30), date.today()-timedelta(1)),
    "Este mes":        (date.today().replace(day=1), date.today()),
    "Mes anterior":    _last_month(),
    "Personalizado":   (date.today()-timedelta(30), date.today()-timedelta(1)),
}


# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        f'<div style="text-align:center;padding:10px 0 6px;">{logo_img(175)}</div>',
        unsafe_allow_html=True,
    )
    st.divider()
    st.markdown('<div class="sb-sec">Periodo</div>', unsafe_allow_html=True)
    preset = st.selectbox("Periodo", list(PRESETS.keys()), index=5, label_visibility="collapsed")

    if preset == "Personalizado":
        c1, c2 = st.columns(2)
        ini = c1.date_input("De",  value=date.today()-timedelta(30))
        fim = c2.date_input("Ate", value=date.today()-timedelta(1))
    else:
        ini, fim = PRESETS[preset]

    since = ini.strftime("%Y-%m-%d")
    until = fim.strftime("%Y-%m-%d")
    n_dias   = max((fim - ini).days, 0)
    prev_ini = ini - timedelta(days=n_dias + 1)
    prev_fim = ini - timedelta(days=1)
    psince   = prev_ini.strftime("%Y-%m-%d")
    puntil   = prev_fim.strftime("%Y-%m-%d")

    st.markdown('<div class="sb-sec">Acoes</div>', unsafe_allow_html=True)
    if st.button("Atualizar dados", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    if st.button("Imprimir / Salvar PDF", use_container_width=True):
        st.components.v1.html("<script>window.print();</script>", height=0)

    st.divider()
    st.caption(f"Conta: {ACCOUNT}")
    st.caption(f"{ini.strftime('%d/%m/%Y')} ate {fim.strftime('%d/%m/%Y')}")
    st.caption(f"vs. {prev_ini.strftime('%d/%m')} a {prev_fim.strftime('%d/%m/%Y')}")
    # Contador regressivo de auto-refresh
    st.markdown(
        '<div id="refresh-counter" style="font-size:10px;color:#6b7280;margin-top:8px;">'
        'Prox. atualizacao em <span id="rtimer" style="color:#F7931E;font-weight:700;">15:00</span>'
        '</div>',
        unsafe_allow_html=True,
    )

# Auto-refresh a cada 15 minutos (900 segundos)
st.components.v1.html("""
<script>
var secs = 900;
function tick() {
    secs--;
    if (secs <= 0) { window.parent.location.reload(); return; }
    var m = String(Math.floor(secs/60)).padStart(2,'0');
    var s = String(secs%60).padStart(2,'0');
    var el = window.parent.document.getElementById('rtimer');
    if (el) el.textContent = m+':'+s;
    setTimeout(tick, 1000);
}
setTimeout(tick, 1000);
</script>
""", height=0)


# ─── Validações ───────────────────────────────────────────────────────────────
if not TOKEN or not ACCOUNT:
    st.error("Configure META_ACCESS_TOKEN e META_AD_ACCOUNT_ID em .streamlit/secrets.toml")
    st.stop()

with st.spinner("Verificando acesso Meta Ads..."):
    if not check_token():
        st.error("Token Meta Ads expirado. Renove em developers.facebook.com e atualize os secrets.")
        st.stop()


# ─── Carregar dados ───────────────────────────────────────────────────────────
with st.spinner("Carregando dados..."):
    conta      = get_conta(since, until)
    conta_ant  = get_conta(psince, puntil)
    serie      = get_serie(since, until)
    campanhas  = get_campanhas(since, until)
    ads_data        = get_ads(since, until)
    ad_statuses     = get_ad_statuses()
    camp_statuses   = get_campaign_statuses()

# ─── Cálculos ────────────────────────────────────────────────────────────────
def _f(d, k): return float(d.get(k, 0) or 0)
def _i(d, k): return int(_f(d, k))

spend  = _f(conta,"spend");    a_spend  = _f(conta_ant,"spend")
imp    = _i(conta,"impressions")
reach  = _i(conta,"reach")
clicks = _i(conta,"clicks")
ctr    = _f(conta,"ctr");      a_ctr    = _f(conta_ant,"ctr")
cpc    = _f(conta,"cpc");      a_cpc    = _f(conta_ant,"cpc")
cpm    = _f(conta,"cpm");      a_cpm    = _f(conta_ant,"cpm")
freq   = _f(conta,"frequency")
leads  = leads_de(conta.get("actions",[])); a_leads = leads_de(conta_ant.get("actions",[]))
cpl    = spend/leads    if leads    else 0
a_cpl  = a_spend/a_leads if a_leads else 0
media_ctr = ctr if ctr > 0 else 1.5
freq_cls  = "freq-bad" if freq > 3.5 else ("freq-med" if freq > 2.5 else "freq-ok")


# ─── HEADER ──────────────────────────────────────────────────────────────────
periodo_txt = f"{ini.strftime('%d/%m')} - {fim.strftime('%d/%m/%Y')}"
st.markdown(f"""
<div class="g3-header">
  <div style="display:flex;align-items:center;gap:18px;">
    {logo_img(110)}
    <div>
      <div class="g3-title">G3 <span>Ads Monitor</span></div>
      <div class="g3-sub">Meta Ads &middot; {periodo_txt} &middot; Conta {ACCOUNT}</div>
    </div>
  </div>
  <div class="g3-badge">Atualizado {datetime.now().strftime('%d/%m/%Y %H:%M')}</div>
</div>
""", unsafe_allow_html=True)


# ─── KPI CARDS ───────────────────────────────────────────────────────────────
st.markdown(
    '<div class="kpi-wrap">'
    + kpi_card("Investimento",       brl(spend), delta_html(spend, a_spend),           f"Ant: {brl(a_spend)}")
    + kpi_card("Leads / Resultados", str(leads), delta_html(leads, a_leads),           f"CPL: {brl(cpl)}")
    + kpi_card("CTR",                pct(ctr),   delta_html(ctr, a_ctr),               "Bench: 1,5% - 3,0%")
    + kpi_card("CPL",                brl(cpl),   delta_html(cpl, a_cpl, inv=True),     f"Ant: {brl(a_cpl)}")
    + kpi_card("CPC",                brl(cpc),   delta_html(cpc, a_cpc, inv=True),     f"CPM: {brl(cpm)}")
    + kpi_card("Frequencia",
               f'<span class="{freq_cls}">{freq:.1f}x</span>',
               delta_html(freq, _f(conta_ant,"frequency"), inv=True),
               "Ideal: menor que 3,0x")
    + '</div>',
    unsafe_allow_html=True,
)

# ─── LINHA MÉTRICAS SECUNDÁRIAS ───────────────────────────────────────────────
st.markdown(
    f'<div style="display:flex;gap:12px;margin-bottom:18px;">'
    f'<div class="kpi-card" style="border-top-color:#6b7280;">'
    f'<div class="kpi-lbl">Impressoes</div>'
    f'<div class="kpi-val" style="font-size:18px;">{imp:,}'.replace(",",".")
    + f'</div></div>'
    f'<div class="kpi-card" style="border-top-color:#6b7280;">'
    f'<div class="kpi-lbl">Alcance</div>'
    f'<div class="kpi-val" style="font-size:18px;">{reach:,}'.replace(",",".")
    + f'</div></div>'
    f'<div class="kpi-card" style="border-top-color:#6b7280;">'
    f'<div class="kpi-lbl">Cliques</div>'
    f'<div class="kpi-val" style="font-size:18px;">{clicks:,}'.replace(",",".")
    + f'</div></div>'
    + kpi_card("CPM", brl(cpm), delta_html(cpm, a_cpm, inv=True), "")
    + '</div>',
    unsafe_allow_html=True,
)


# ─── EVOLUÇÃO DIÁRIA + DONUT ──────────────────────────────────────────────────
st.markdown('<div class="sec-hd">Evolucao Diaria</div>', unsafe_allow_html=True)
col_trend, col_donut = st.columns([62, 38])

with col_trend:
    if serie:
        rows_s = [{"data": r.get("date_start",""),
                   "spend": float(r.get("spend",0) or 0),
                   "ctr":   float(r.get("ctr",0) or 0),
                   "leads": leads_de(r.get("actions",[]))}
                  for r in serie]
        df_s = pd.DataFrame(rows_s)
        df_s["label"] = pd.to_datetime(df_s["data"]).dt.strftime("%d/%m")
        med = df_s["spend"].mean()

        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Bar(
            x=df_s["label"], y=df_s["spend"], name="Invest. (R$)",
            marker=dict(color=ORANGE, opacity=0.9, line=dict(width=0)),
            hovertemplate="<b>%{x}</b><br>R$ %{y:,.2f}<extra></extra>",
        ), secondary_y=False)
        if df_s["leads"].sum() > 0:
            fig.add_trace(go.Scatter(
                x=df_s["label"], y=df_s["leads"], name="Leads",
                line=dict(color="#a78bfa", width=2.5),
                mode="lines+markers", marker=dict(size=7, color="#a78bfa"),
                hovertemplate="<b>%{x}</b><br>Leads: %{y}<extra></extra>",
            ), secondary_y=True)
        # Linha de média como trace (evita bug add_hline em subplots)
        if len(df_s) > 1:
            fig.add_trace(go.Scatter(
                x=[df_s["label"].iloc[0], df_s["label"].iloc[-1]],
                y=[med, med], mode="lines",
                name=f"Media R${med:,.0f}",
                line=dict(color="#fff", width=1.2, dash="dash"),
                hoverinfo="skip",
            ), secondary_y=False)

        _chart_layout(fig)
        fig.update_yaxes(title_text="Invest. (R$)", secondary_y=False,
                         tickprefix="R$ ", gridcolor="#222")
        fig.update_yaxes(title_text="Leads", secondary_y=True,
                         gridcolor="rgba(0,0,0,0)", showgrid=False)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Sem dados diarios para o periodo selecionado.")

with col_donut:
    camp_spend = [(c.get("campaign_name","?"), float(c.get("spend",0)))
                  for c in campanhas if float(c.get("spend",0)) > 0]
    if camp_spend:
        nomes, vals = zip(*camp_spend)
        CORES_PIE = [ORANGE,"#fb923c","#374151","#6b7280","#fcd34d",
                     "#9ca3af","#d97706","#1d4ed8","#4ade80","#f87171"]
        fig2 = go.Figure(go.Pie(
            labels=[n[:22] for n in nomes], values=vals, hole=0.58,
            marker=dict(colors=CORES_PIE[:len(nomes)], line=dict(color=CARD, width=2)),
            textinfo="percent",
            hovertemplate="<b>%{label}</b><br>R$ %{value:,.2f}<br>%{percent}<extra></extra>",
        ))
        fig2.add_annotation(text=f"<b>{brl(spend)}</b><br>total",
                            x=0.5, y=0.5, showarrow=False,
                            font=dict(size=13, color="#fff"), align="center")
        fig2.update_layout(
            title=dict(text="Budget por Campanha", font_size=12, font_color=TEXT, x=0),
            height=340, margin=dict(l=0, r=0, t=36, b=0),
            paper_bgcolor=CARD, showlegend=True,
            legend=dict(font=dict(size=9, color=MUTED), x=1, y=0.5),
            font=dict(family="Inter, sans-serif"),
        )
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})


# ─── CAMPANHAS ────────────────────────────────────────────────────────────────
st.markdown('<div class="sec-hd">Desempenho por Campanha</div>', unsafe_allow_html=True)

if campanhas:
    total_sp = sum(float(c.get("spend",0)) for c in campanhas) or 1

    # Monta linhas com status e recomendação
    def _camp_status_html(c):
        eff = camp_statuses.get(str(c.get("campaign_id","")), "UNKNOWN")
        cls, label = _STATUS_MAP.get(eff, ("st-desconhecido", eff))
        return f'<span class="{cls}">{label}</span>', label

    all_rows_c = []
    for c in campanhas:
        s   = float(c.get("spend",0))
        ld  = leads_de(c.get("actions",[]))
        ctr_= float(c.get("ctr",0))
        fr_ = float(c.get("frequency",0))
        rec = rec_badge(s, ctr_, fr_, media_ctr)
        st_html, st_label = _camp_status_html(c)
        all_rows_c.append({
            "_rec":      rec,
            "_status":   st_label,
            "Status":    st_html,
            "Acao":      badge_html(rec),
            "Campanha":  c.get("campaign_name","?"),
            "Gasto":     brl(s),
            "% Budget":  f"{s/total_sp*100:.1f}%",
            "Leads":     str(ld) if ld else "—",
            "CPL":       brl(s/ld) if ld else "—",
            "CTR":       pct(ctr_),
            "CPC":       brl(c.get("cpc",0)),
            "CPM":       brl(c.get("cpm",0)),
            "Freq.":     f"{fr_:.1f}x",
            "Impressoes":f"{int(float(c.get('impressions',0))):,}".replace(",","."),
        })

    # Filtros
    cf1, cf2, cf3 = st.columns([3, 2, 2])
    with cf1:
        rec_opts  = sorted({r["_rec"] for r in all_rows_c})
        sel_rec_c = st.multiselect("Recomendacao:", rec_opts,
                                   placeholder="Todas", key="rec_camp")
    with cf2:
        st_opts   = sorted({r["_status"] for r in all_rows_c if r["_status"] != "UNKNOWN"})
        sel_st_c  = st.multiselect("Status:", st_opts,
                                   placeholder="Todos", key="st_camp")
    with cf3:
        ord_c = st.selectbox("Ordenar:", ["Gasto","Leads","CTR","Frequencia"], key="ord_camp")

    rows_c = all_rows_c
    if sel_rec_c: rows_c = [r for r in rows_c if r["_rec"] in sel_rec_c]
    if sel_st_c:  rows_c = [r for r in rows_c if r["_status"] in sel_st_c]
    ORD_C = {"Gasto": lambda r: -float(r["Gasto"].replace("R$","").replace(".","").replace(",",".").strip() or 0),
             "Leads": lambda r: -int(r["Leads"]) if r["Leads"].isdigit() else 0,
             "CTR":   lambda r: -float(r["CTR"].replace("%","") or 0),
             "Frequencia": lambda r: -float(r["Freq."].replace("x","") or 0)}
    rows_c.sort(key=ORD_C[ord_c])

    cols_c = ["Status","Acao","Campanha","Gasto","% Budget","Leads","CPL","CTR","CPC","CPM","Freq.","Impressoes"]
    st.markdown(html_table(rows_c, cols_c), unsafe_allow_html=True)

    with st.expander("Ver grafico de campanhas"):
        df_bar = [(r["Campanha"][:30], float(r["Gasto"].replace("R$","").replace(".","").replace(",",".").strip() or 0))
                  for r in rows_c if r["Gasto"] != "R$ 0,00"]
        if df_bar:
            nomes_b, vals_b = zip(*sorted(df_bar, key=lambda x: x[1]))
            fig3 = go.Figure(go.Bar(
                x=list(vals_b), y=list(nomes_b), orientation="h",
                marker_color=ORANGE,
                text=[f"R${v:,.0f}" for v in vals_b],
                textposition="outside", textfont=dict(color=TEXT, size=10),
                hovertemplate="<b>%{y}</b><br>R$ %{x:,.2f}<extra></extra>",
            ))
            _chart_layout(fig3, height=max(260, len(df_bar)*42))
            fig3.update_layout(xaxis_title="Investimento (R$)", yaxis_title="",
                               margin=dict(l=0, r=80, t=10, b=0))
            st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})


# ─── ANÁLISE DE CRIATIVOS ─────────────────────────────────────────────────────
st.markdown('<div class="sec-hd">Analise de Criativos</div>', unsafe_allow_html=True)

ads_validos = [a for a in ads_data if float(a.get("spend",0)) > 0]

def _rec(a):
    return rec_badge(a.get("spend",0), a.get("ctr",0), a.get("frequency",0), media_ctr)

def _ad_st_label(a):
    eff = ad_statuses.get(str(a.get("ad_id","")), {}).get("effective_status","UNKNOWN")
    return _STATUS_MAP.get(eff, ("","UNKNOWN"))[1]

# Filtros — linha 1
af1, af2, af3 = st.columns([3, 2, 2])
with af1:
    camp_opts = sorted({a.get("campaign_name","?") for a in ads_validos})
    sel_camps = st.multiselect("Campanha:", camp_opts, placeholder="Todas", key="camp_ad")
with af2:
    rec_opts_a = ["ESCALAR","PAUSAR","MONITORAR","AGUARDAR"]
    sel_rec_a  = st.multiselect("Recomendacao:", rec_opts_a, placeholder="Todas", key="rec_ad")
with af3:
    st_opts_a  = sorted({_ad_st_label(a) for a in ads_validos if _ad_st_label(a) != "UNKNOWN"})
    sel_st_a   = st.multiselect("Status:", st_opts_a, placeholder="Todos", key="st_ad")

# Filtro — linha 2 (ordem)
ordem = st.selectbox("Ordenar por:", ["Gasto","CTR","Leads","Frequencia"], key="ord_ad")

if sel_camps:  ads_validos = [a for a in ads_validos if a.get("campaign_name") in sel_camps]
if sel_rec_a:  ads_validos = [a for a in ads_validos if _rec(a) in sel_rec_a]
if sel_st_a:   ads_validos = [a for a in ads_validos if _ad_st_label(a) in sel_st_a]

ORDEM_MAP = {
    "Gasto":      lambda a: -float(a.get("spend",0)),
    "CTR":        lambda a: -float(a.get("ctr",0)),
    "Leads":      lambda a: -leads_de(a.get("actions",[])),
    "Frequencia": lambda a: -float(a.get("frequency",0)),
}
ads_validos.sort(key=ORDEM_MAP[ordem])

if ads_validos:
    n_e = sum(1 for a in ads_validos if _rec(a)=="ESCALAR")
    n_p = sum(1 for a in ads_validos if _rec(a)=="PAUSAR")
    n_m = sum(1 for a in ads_validos if _rec(a)=="MONITORAR")
    n_a = sum(1 for a in ads_validos if _rec(a)=="AGUARDAR")
    st.markdown(
        f'<div style="display:flex;gap:10px;margin:10px 0 14px;flex-wrap:wrap;">'
        f'<span class="badge-escalar" style="padding:6px 14px;font-size:12px;">ESCALAR: {n_e}</span>'
        f'<span class="badge-pausar"  style="padding:6px 14px;font-size:12px;">PAUSAR: {n_p}</span>'
        f'<span class="badge-monitorar" style="padding:6px 14px;font-size:12px;">MONITORAR: {n_m}</span>'
        f'<span class="badge-aguardar" style="padding:6px 14px;font-size:12px;">AGUARDAR: {n_a}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    rows_a = []
    for a in ads_validos:
        s    = float(a.get("spend",0))
        ctr_ = float(a.get("ctr",0))
        freq_= float(a.get("frequency",0))
        ld   = leads_de(a.get("actions",[]))
        badge = _rec(a)
        ad_id = a.get("ad_id","")
        rows_a.append({
            "Status":    status_html(ad_id, ad_statuses),
            "Acao":      badge_html(badge),
            "Anuncio":   a.get("ad_name","?")[:45],
            "Campanha":  a.get("campaign_name","?")[:30],
            "Gasto":     brl(s),
            "Leads":     str(ld) if ld else "—",
            "CPL":       brl(s/ld) if ld else "—",
            "CTR":       pct(ctr_),
            "CPC":       brl(a.get("cpc",0)),
            "CPM":       brl(a.get("cpm",0)),
            "Freq.":     f"{freq_:.1f}x",
            "Cliques":   f"{int(float(a.get('clicks',0))):,}".replace(",","."),
        })

    cols_a = ["Status","Acao","Anuncio","Campanha","Gasto","Leads","CPL","CTR","CPC","CPM","Freq.","Cliques"]
    st.markdown(html_table(rows_a, cols_a), unsafe_allow_html=True)

    with st.expander("Ver grafico: Top criativos por gasto"):
        top = ads_validos[:15]
        nomes_a = [a.get("ad_name","?")[:32] for a in top]
        gastos_a = [float(a.get("spend",0)) for a in top]
        CORE_MAP = {"ESCALAR":ORANGE,"PAUSAR":"#f87171","MONITORAR":"#38bdf8","AGUARDAR":MUTED}
        cores_a = [CORE_MAP[_rec(a)] for a in top]
        fig_a = go.Figure(go.Bar(
            x=gastos_a[::-1], y=nomes_a[::-1], orientation="h",
            marker_color=cores_a[::-1],
            text=[f"R${v:,.0f}" for v in gastos_a[::-1]],
            textposition="outside", textfont=dict(color=TEXT, size=10),
            hovertemplate="<b>%{y}</b><br>R$ %{x:,.2f}<extra></extra>",
        ))
        _chart_layout(fig_a, height=max(300, len(top)*40))
        fig_a.update_layout(
            title=dict(text="Laranja=Escalar  Vermelho=Pausar  Azul=Monitorar",
                       font_size=10, font_color=MUTED, x=0),
            xaxis_title="Investimento (R$)", yaxis_title="",
            margin=dict(l=0, r=90, t=30, b=0),
        )
        st.plotly_chart(fig_a, use_container_width=True, config={"displayModeBar": False})
else:
    st.info("Nenhum anuncio com gasto no periodo selecionado.")


# ─── GLOSSÁRIO ───────────────────────────────────────────────────────────────
with st.expander("O que significam essas siglas? (clique para ver)"):
    st.markdown(f"""
<div class="gloss-grid" style="display:grid;grid-template-columns:1fr 1fr;gap:10px 24px;padding:4px 0;">
  <div style="background:#1a1a1a;border-left:4px solid {ORANGE};border-radius:6px;padding:10px 14px;">
    <div style="color:{ORANGE};font-weight:800;font-size:11px;text-transform:uppercase;margin-bottom:4px;">CPL — Custo por Lead</div>
    <div style="color:{TEXT};font-size:12px;line-height:1.6;">Quanto voce paga por cada lead gerado. Se o CPL for R$ 4,00, cada pessoa interessada custou R$ 4,00. <b>Quanto menor, melhor.</b></div>
  </div>
  <div style="background:#1a1a1a;border-left:4px solid {ORANGE};border-radius:6px;padding:10px 14px;">
    <div style="color:{ORANGE};font-weight:800;font-size:11px;text-transform:uppercase;margin-bottom:4px;">CTR — Taxa de Cliques</div>
    <div style="color:{TEXT};font-size:12px;line-height:1.6;">De cada 100 pessoas que viram o anuncio, quantas clicaram. CTR de 2% = 2 em cada 100 clicaram. <b>Acima de 1,5% e considerado bom.</b></div>
  </div>
  <div style="background:#1a1a1a;border-left:4px solid {ORANGE};border-radius:6px;padding:10px 14px;">
    <div style="color:{ORANGE};font-weight:800;font-size:11px;text-transform:uppercase;margin-bottom:4px;">CPC — Custo por Clique</div>
    <div style="color:{TEXT};font-size:12px;line-height:1.6;">Quanto voce paga por cada clique no anuncio, independente de virar lead ou nao. <b>Quanto menor, mais eficiente.</b></div>
  </div>
  <div style="background:#1a1a1a;border-left:4px solid {ORANGE};border-radius:6px;padding:10px 14px;">
    <div style="color:{ORANGE};font-weight:800;font-size:11px;text-transform:uppercase;margin-bottom:4px;">CPM — Custo por Mil Impressoes</div>
    <div style="color:{TEXT};font-size:12px;line-height:1.6;">Quanto custa exibir o anuncio 1.000 vezes. Indica o custo de "aparecer" para as pessoas, antes mesmo do clique.</div>
  </div>
  <div style="background:#1a1a1a;border-left:4px solid {ORANGE};border-radius:6px;padding:10px 14px;">
    <div style="color:{ORANGE};font-weight:800;font-size:11px;text-transform:uppercase;margin-bottom:4px;">Frequencia</div>
    <div style="color:{TEXT};font-size:12px;line-height:1.6;">Quantas vezes em media a mesma pessoa viu seu anuncio. Frequencia 5,5x = a mesma pessoa viu o anuncio 5,5 vezes. <b>Acima de 3,5x o publico comeca a se cansar (saturacao).</b></div>
  </div>
  <div style="background:#1a1a1a;border-left:4px solid {ORANGE};border-radius:6px;padding:10px 14px;">
    <div style="color:{ORANGE};font-weight:800;font-size:11px;text-transform:uppercase;margin-bottom:4px;">Impressoes</div>
    <div style="color:{TEXT};font-size:12px;line-height:1.6;">Total de vezes que o anuncio foi exibido na tela de alguem. Uma mesma pessoa pode gerar varias impressoes. Diferente de Alcance, que conta pessoas unicas.</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ─── ALERTAS ─────────────────────────────────────────────────────────────────
st.markdown('<div class="sec-hd">Alertas e Recomendacoes</div>', unsafe_allow_html=True)

alertas = []
for c in campanhas:
    nome  = c.get("campaign_name","?")
    freq_ = float(c.get("frequency",0))
    ctr_c = float(c.get("ctr",0))
    sp    = float(c.get("spend",0))
    ld    = leads_de(c.get("actions",[]))
    if freq_ > 3.5:
        alertas.append(("red", f"<b>{nome}</b>: frequencia {freq_:.1f}x — publico saturando. Renovar criativos ou ampliar segmentacao."))
    elif freq_ > 2.5:
        alertas.append(("yel", f"<b>{nome}</b>: frequencia {freq_:.1f}x — atencao. Monitorar saturacao do publico."))
    if sp > 50 and ctr_c < media_ctr * 0.5:
        alertas.append(("yel", f"<b>{nome}</b>: CTR {pct(ctr_c)} abaixo da media ({pct(media_ctr)}). Revisar criativos e copy."))
    if sp > 100 and ld == 0:
        alertas.append(("yel", f"<b>{nome}</b>: {brl(sp)} gastos sem lead. Revisar segmentacao e oferta."))
    if ctr_c >= media_ctr * 1.3 and sp >= 50:
        alertas.append(("grn", f"<b>{nome}</b>: CTR {pct(ctr_c)} acima da media. Considere aumentar budget em 20-30%."))

if not alertas:
    alertas.append(("grn", "Conta com performance dentro do esperado. Nenhuma acao urgente identificada."))

a_col, _ = st.columns([3, 1])
with a_col:
    for tipo, msg in alertas[:12]:
        st.markdown(f'<div class="al al-{tipo}">{msg}</div>', unsafe_allow_html=True)


# ─── RODAPÉ ───────────────────────────────────────────────────────────────────
st.divider()
st.markdown(
    f'<div style="font-size:10px;color:{MUTED};text-align:center;padding:2px 0 12px;">'
    f'G3 Veiculos &middot; Trafego Pago G3 &middot; Meta Ads API &middot; '
    f'{ini.strftime("%d/%m/%Y")} ate {fim.strftime("%d/%m/%Y")} &middot; '
    f'Atualizado {datetime.now().strftime("%d/%m/%Y %H:%M")}'
    f'</div>',
    unsafe_allow_html=True,
)
