#!/usr/bin/env python3
"""G3 Ads Monitor — Dashboard Online · Tema Escuro · Meta Ads API"""
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import pandas as pd
import requests
import os
import base64
from datetime import datetime, timedelta, date
from pathlib import Path

# ─── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="G3 Ads Monitor",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "G3 Ads Monitor · G3 Veiculos · Trafego Pago"},
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

def logo_b64():
    if _LOGO.exists():
        return base64.b64encode(_LOGO.read_bytes()).decode()
    return None

_logo_data = logo_b64()

def logo_img(width=160):
    if _logo_data:
        return f'<img src="data:image/png;base64,{_logo_data}" style="width:{width}px;height:auto;">'
    return '<div style="color:#F7931E;font-size:20px;font-weight:900;letter-spacing:-1px;">G3 VEÍCULOS</div>'

# ─── CSS Tema Escuro ──────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

/* ── Base escura ── */
html, body, .stApp, [data-testid="stAppViewContainer"],
[data-testid="stMain"] {{
    background-color: {DARK} !important;
    color: {TEXT} !important;
    font-family: 'Inter', sans-serif !important;
}}
[data-testid="stHeader"] {{ background: {DARK} !important; }}
#MainMenu, footer {{ visibility: hidden; }}
.block-container {{ padding-top: 1rem !important; padding-bottom: 0.5rem !important; }}

/* ── Sidebar ── */
[data-testid="stSidebar"] {{
    background: #0a0a0a !important;
    border-right: 1px solid {BORDER} !important;
}}
[data-testid="stSidebar"] * {{ color: {TEXT} !important; }}
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stDateInput label {{ color: {MUTED} !important; font-size: 11px !important; }}
[data-testid="stSidebar"] select,
[data-testid="stSidebar"] input {{
    background: #1a1a1a !important;
    color: {TEXT} !important;
    border: 1px solid {BORDER} !important;
}}

/* ── Botoes sidebar ── */
[data-testid="stSidebar"] .stButton button {{
    background: {CARD} !important;
    color: {TEXT} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 6px;
    font-size: 12px;
    transition: all .2s;
}}
[data-testid="stSidebar"] .stButton button:hover {{
    border-color: {ORANGE} !important;
    color: {ORANGE} !important;
}}

/* ── st.metric escuro ── */
[data-testid="metric-container"] {{
    background: {CARD};
    border: 1px solid {BORDER};
    border-top: 3px solid {ORANGE};
    border-radius: 10px;
    padding: 14px 16px;
}}
[data-testid="metric-container"] label {{ color: {MUTED} !important; font-size: 10px !important; text-transform: uppercase; letter-spacing: .5px; }}
[data-testid="metric-container"] [data-testid="stMetricValue"] {{ color: {TEXT} !important; font-weight: 800; }}
[data-testid="metric-container"] [data-testid="stMetricDelta"] {{ font-size: 11px !important; }}

/* ── Dataframe escuro ── */
[data-testid="stDataFrame"] {{
    background: {CARD} !important;
    border-radius: 8px !important;
}}
.dvn-scroller {{ background: {CARD} !important; }}

/* ── Expander ── */
[data-testid="stExpander"] {{
    background: {CARD} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 8px !important;
}}
[data-testid="stExpander"] summary {{ color: {TEXT} !important; }}

/* ── Alerta/info ── */
[data-testid="stAlert"] {{
    background: #1a1a1a !important;
    border-color: {ORANGE} !important;
    color: {TEXT} !important;
}}

/* ── Spinner ── */
[data-testid="stSpinner"] {{ color: {ORANGE} !important; }}

/* ── KPI cards custom ── */
.kpi-wrap {{ display: flex; gap: 12px; margin-bottom: 16px; flex-wrap: wrap; }}
.kpi-card {{
    flex: 1; min-width: 130px;
    background: {CARD};
    border: 1px solid {BORDER};
    border-radius: 10px;
    padding: 14px 16px;
    border-top: 4px solid {ORANGE};
}}
.kpi-lbl  {{ font-size: 9px; color: {MUTED}; text-transform: uppercase;
              letter-spacing: .7px; font-weight: 700; margin-bottom: 6px; }}
.kpi-val  {{ font-size: 23px; font-weight: 900; color: #fff; line-height: 1.1; }}
.kpi-delta{{ font-size: 11px; margin-top: 5px; }}
.kpi-sub  {{ font-size: 10px; color: {MUTED}; margin-top: 3px; }}
.up  {{ color: #4ade80; }} .dn {{ color: #f87171; }} .neu {{ color: {MUTED}; }}

/* ── Cabecalho ── */
.g3-header {{
    background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%);
    border: 1px solid {BORDER};
    border-left: 5px solid {ORANGE};
    border-radius: 12px;
    padding: 16px 22px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
}}
.g3-title {{ color: #fff; font-size: 22px; font-weight: 900; letter-spacing: -0.5px; }}
.g3-title span {{ color: {ORANGE}; }}
.g3-sub   {{ color: {MUTED}; font-size: 11px; margin-top: 4px; }}
.g3-badge {{
    background: {ORANGE}; color: #000; font-size: 10px; font-weight: 800;
    padding: 5px 14px; border-radius: 6px; white-space: nowrap;
}}

/* ── Secao header ── */
.sec-hd {{
    font-size: 11px; font-weight: 800; color: {TEXT};
    border-left: 4px solid {ORANGE};
    padding-left: 10px; margin: 22px 0 12px;
    text-transform: uppercase; letter-spacing: .5px;
    display: flex; align-items: center; gap: 8px;
}}

/* ── Alertas ── */
.al {{ padding: 10px 16px; border-left: 4px solid;
       border-radius: 0 8px 8px 0; margin-bottom: 8px;
       font-size: 12px; line-height: 1.6; }}
.al-red {{ background: #2d0a0a; border-color: #f87171; color: #fca5a5; }}
.al-yel {{ background: #2d2000; border-color: #fbbf24; color: #fde68a; }}
.al-grn {{ background: #052d16; border-color: #4ade80; color: #86efac; }}

/* ── Sidebar label ── */
.sb-sec {{ font-size: 10px; font-weight: 800; color: {ORANGE};
           text-transform: uppercase; letter-spacing: .6px; margin: 14px 0 5px; }}

/* ── Freq badge ── */
.freq-ok  {{ color: #4ade80; font-weight: 800; }}
.freq-med {{ color: #fbbf24; font-weight: 800; }}
.freq-bad {{ color: #f87171; font-weight: 800; }}

/* ── Print ── */
@media print {{
    [data-testid="stSidebar"], [data-testid="stHeader"],
    .stButton, .element-container:has(.stButton) {{ display: none !important; }}
    body, .stApp {{ background: #fff !important; color: #000 !important; }}
    .kpi-card {{ background: #f9fafb !important; border-top-color: {ORANGE} !important; }}
    .g3-header {{ background: {DARK} !important; -webkit-print-color-adjust: exact; }}
    .block-container {{ padding: 0 !important; }}
}}

/* ── HR ── */
hr {{ border-color: {BORDER} !important; margin: 8px 0 !important; }}

/* ── Tooltip ── */
[data-testid="stTooltipIcon"] {{ color: {MUTED} !important; }}
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


@st.cache_data(ttl=1800, show_spinner=False)
def get_conta(since, until):
    d = _api(f"{ACCOUNT}/insights", {
        "fields": "impressions,reach,clicks,spend,ctr,cpc,cpm,frequency,actions",
        "time_range": f'{{"since":"{since}","until":"{until}"}}',
        "level": "account",
    })
    return (d.get("data") or [{}])[0]


@st.cache_data(ttl=1800, show_spinner=False)
def get_serie(since, until):
    d = _api(f"{ACCOUNT}/insights", {
        "fields": "spend,ctr,impressions,clicks,actions",
        "time_range": f'{{"since":"{since}","until":"{until}"}}',
        "time_increment": 1, "level": "account",
    })
    rows = d.get("data", [])
    return sorted(rows, key=lambda x: x.get("date_start", ""))


@st.cache_data(ttl=1800, show_spinner=False)
def get_campanhas(since, until):
    d = _api(f"{ACCOUNT}/insights", {
        "fields": "campaign_name,impressions,reach,clicks,spend,ctr,cpc,cpm,frequency,actions",
        "time_range": f'{{"since":"{since}","until":"{until}"}}',
        "level": "campaign", "limit": 50,
    })
    return sorted(d.get("data", []), key=lambda x: float(x.get("spend", 0)), reverse=True)


@st.cache_data(ttl=1800, show_spinner=False)
def get_ads(since, until):
    d = _api(f"{ACCOUNT}/insights", {
        "fields": "ad_id,ad_name,campaign_name,adset_name,impressions,clicks,spend,ctr,cpc,cpm,frequency,actions",
        "time_range": f'{{"since":"{since}","until":"{until}"}}',
        "level": "ad", "limit": 200,
    })
    return sorted(d.get("data", []), key=lambda x: float(x.get("spend", 0)), reverse=True)


# ─── Helpers ─────────────────────────────────────────────────────────────────

def leads_de(actions):
    TIPOS = {
        "onsite_conversion.messaging_conversation_started_7d",
        "lead", "offsite_conversion.fb_pixel_lead", "omni_complete_registration",
    }
    total, seen = 0, set()
    for a in (actions or []):
        t = a.get("action_type", "")
        if t in TIPOS and t not in seen:
            total += int(float(a.get("value", 0)))
            seen.add(t)
    return total


def brl(v):
    try:
        return f"R$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


def pct(v):
    try:
        return f"{float(v):.2f}%"
    except Exception:
        return "—"


def delta_html(a, b, inv=False):
    try:
        if not b or float(b) == 0:
            return f'<span class="neu">—</span>'
        v = (float(a) - float(b)) / float(b) * 100
        sobe = (v >= 0) if not inv else (v < 0)
        cls  = "up" if sobe else "dn"
        arrow = "▲" if v >= 0 else "▼"
        return f'<span class="{cls}">{arrow} {abs(v):.1f}% vs ant.</span>'
    except Exception:
        return f'<span class="neu">—</span>'


def kpi_card(lbl, val, dh="", sub=""):
    return (
        f'<div class="kpi-card">'
        f'<div class="kpi-lbl">{lbl}</div>'
        f'<div class="kpi-val">{val}</div>'
        f'<div class="kpi-delta">{dh}</div>'
        f'{"" if not sub else f"<div class=kpi-sub>{sub}</div>"}'
        f'</div>'
    )


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


def _chart_layout(fig, height=340):
    fig.update_layout(
        height=height,
        margin=dict(l=0, r=10, t=30, b=0),
        paper_bgcolor=CARD,
        plot_bgcolor="#141414",
        font=dict(family="Inter, sans-serif", color=TEXT, size=11),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02,
            xanchor="left", x=0, font_size=11,
            bgcolor="rgba(0,0,0,0)", borderwidth=0,
        ),
        bargap=0.28,
    )
    fig.update_xaxes(gridcolor="#222", tickcolor=MUTED, linecolor=BORDER, color=MUTED)
    fig.update_yaxes(gridcolor="#222", tickcolor=MUTED, linecolor=BORDER, color=MUTED)
    return fig


# ─── Presets de data ──────────────────────────────────────────────────────────

def _last_month():
    today = date.today()
    fim   = today.replace(day=1) - timedelta(1)
    return fim.replace(day=1), fim


PRESETS = {
    "Hoje":             (date.today(), date.today()),
    "Ontem":            (date.today() - timedelta(1), date.today() - timedelta(1)),
    "Ultimos 7 dias":   (date.today() - timedelta(7),  date.today() - timedelta(1)),
    "Ultimos 14 dias":  (date.today() - timedelta(14), date.today() - timedelta(1)),
    "Ultimos 30 dias":  (date.today() - timedelta(30), date.today() - timedelta(1)),
    "Este mes":         (date.today().replace(day=1), date.today()),
    "Mes anterior":     _last_month(),
    "Personalizado":    (date.today() - timedelta(30), date.today() - timedelta(1)),
}


# ─── Sidebar ─────────────────────────────────────────────────────────────────

with st.sidebar:
    if _logo_data:
        st.markdown(
            f'<div style="text-align:center;padding:12px 0 8px;">'
            f'{logo_img(170)}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div style="text-align:center;padding:12px 0;color:#F7931E;'
            'font-size:22px;font-weight:900;">G3 VEICULOS</div>',
            unsafe_allow_html=True,
        )

    st.markdown('<hr style="border-color:#2a2a2a;margin:4px 0 10px;">', unsafe_allow_html=True)
    st.markdown('<div class="sb-sec">Periodo</div>', unsafe_allow_html=True)

    preset = st.selectbox("Periodo", list(PRESETS.keys()), index=5, label_visibility="collapsed")

    if preset == "Personalizado":
        c1, c2 = st.columns(2)
        ini = c1.date_input("De",  value=date.today() - timedelta(30))
        fim = c2.date_input("Ate", value=date.today() - timedelta(1))
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

    st.markdown('<hr style="border-color:#2a2a2a;margin:10px 0;">', unsafe_allow_html=True)
    st.markdown(
        f'<div style="font-size:10px;color:{MUTED};line-height:2;">'
        f'Conta: {ACCOUNT}<br>'
        f'{ini.strftime("%d/%m/%Y")} ate {fim.strftime("%d/%m/%Y")}<br>'
        f'vs. {prev_ini.strftime("%d/%m")} a {prev_fim.strftime("%d/%m/%Y")}'
        f'</div>',
        unsafe_allow_html=True,
    )


# ─── Validacoes ───────────────────────────────────────────────────────────────

if not TOKEN or not ACCOUNT:
    st.error("Configure META_ACCESS_TOKEN e META_AD_ACCOUNT_ID em .streamlit/secrets.toml")
    st.stop()

with st.spinner("Verificando acesso Meta Ads..."):
    if not check_token():
        st.error("Token Meta Ads expirado. Renove em developers.facebook.com e atualize os secrets.")
        st.stop()


# ─── Carregar dados ───────────────────────────────────────────────────────────

with st.spinner("Carregando dados..."):
    conta     = get_conta(since, until)
    conta_ant = get_conta(psince, puntil)
    serie     = get_serie(since, until)
    campanhas = get_campanhas(since, until)
    ads_data  = get_ads(since, until)


# ─── Calculos ────────────────────────────────────────────────────────────────

def _f(d, k):  return float(d.get(k, 0) or 0)
def _i(d, k):  return int(_f(d, k))

spend  = _f(conta, "spend");    a_spend  = _f(conta_ant, "spend")
imp    = _i(conta, "impressions")
reach  = _i(conta, "reach")
clicks = _i(conta, "clicks")
ctr    = _f(conta, "ctr");      a_ctr    = _f(conta_ant, "ctr")
cpc    = _f(conta, "cpc");      a_cpc    = _f(conta_ant, "cpc")
cpm    = _f(conta, "cpm");      a_cpm    = _f(conta_ant, "cpm")
freq   = _f(conta, "frequency")
leads  = leads_de(conta.get("actions", []));  a_leads = leads_de(conta_ant.get("actions", []))
cpl    = spend / leads   if leads   else 0
a_cpl  = a_spend / a_leads if a_leads else 0
media_ctr = ctr if ctr else 1.5


# ─── HEADER ──────────────────────────────────────────────────────────────────

periodo_txt = f"{ini.strftime('%d/%m')} - {fim.strftime('%d/%m/%Y')}"
freq_cls    = "freq-bad" if freq > 3.5 else ("freq-med" if freq > 2.5 else "freq-ok")

logo_html = logo_img(120) if _logo_data else ""

st.markdown(f"""
<div class="g3-header">
  <div style="display:flex;align-items:center;gap:18px;">
    {logo_html}
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
    + kpi_card("Investimento",       brl(spend),  delta_html(spend, a_spend),      f"Ant: {brl(a_spend)}")
    + kpi_card("Leads / Resultados", str(leads),  delta_html(leads, a_leads),      f"CPL: {brl(cpl)}")
    + kpi_card("CTR",                pct(ctr),    delta_html(ctr, a_ctr),          "Bench: 1,5% - 3,0%")
    + kpi_card("CPL",                brl(cpl),    delta_html(cpl, a_cpl, inv=True),f"Ant: {brl(a_cpl)}")
    + kpi_card("CPC",                brl(cpc),    delta_html(cpc, a_cpc, inv=True),f"CPM: {brl(cpm)}")
    + kpi_card("Frequencia",
               f'<span class="{freq_cls}">{freq:.1f}x</span>',
               delta_html(freq, _f(conta_ant, "frequency"), inv=True),
               "Ideal: menor que 3,0x")
    + '</div>',
    unsafe_allow_html=True,
)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Impressoes",  f"{imp:,}".replace(",", "."))
c2.metric("Alcance",     f"{reach:,}".replace(",", "."))
c3.metric("Cliques",     f"{clicks:,}".replace(",", "."))
c4.metric("CPM",         brl(cpm),
          delta=f"{(cpm - a_cpm) / a_cpm * 100:+.1f}% vs ant." if a_cpm else None,
          delta_color="inverse")


# ─── EVOLUCAO DIARIA + DONUT ──────────────────────────────────────────────────

st.markdown('<div class="sec-hd">Evolucao Diaria</div>', unsafe_allow_html=True)
col_trend, col_donut = st.columns([62, 38])

with col_trend:
    if serie:
        rows_s = []
        for row in serie:
            rows_s.append({
                "data":   row.get("date_start", ""),
                "spend":  float(row.get("spend", 0) or 0),
                "ctr":    float(row.get("ctr",   0) or 0),
                "leads":  leads_de(row.get("actions", [])),
                "clicks": int(float(row.get("clicks", 0) or 0)),
            })
        df_s = pd.DataFrame(rows_s)
        df_s["label"] = pd.to_datetime(df_s["data"]).dt.strftime("%d/%m")

        med_spend = df_s["spend"].mean()

        fig = make_subplots(specs=[[{"secondary_y": True}]])

        # Barras: Investimento
        fig.add_trace(go.Bar(
            x=df_s["label"], y=df_s["spend"], name="Investimento (R$)",
            marker=dict(color=ORANGE, opacity=0.9, line=dict(width=0)),
            hovertemplate="<b>%{x}</b><br>R$ %{y:,.2f}<extra></extra>",
        ), secondary_y=False)

        # Linha: Leads
        if df_s["leads"].sum() > 0:
            fig.add_trace(go.Scatter(
                x=df_s["label"], y=df_s["leads"], name="Leads",
                line=dict(color="#a78bfa", width=2.5),
                mode="lines+markers",
                marker=dict(size=7, color="#a78bfa", symbol="circle"),
                hovertemplate="<b>%{x}</b><br>Leads: %{y}<extra></extra>",
            ), secondary_y=True)

        # Linha: CTR
        fig.add_trace(go.Scatter(
            x=df_s["label"], y=df_s["ctr"], name="CTR (%)",
            line=dict(color="#38bdf8", width=2, dash="dot"),
            mode="lines+markers",
            marker=dict(size=5, color="#38bdf8"),
            hovertemplate="<b>%{x}</b><br>CTR: %{y:.2f}%<extra></extra>",
        ), secondary_y=True)

        # Linha de media (shape manual — evita bug do add_hline em subplots)
        if len(df_s) > 1:
            fig.add_trace(go.Scatter(
                x=[df_s["label"].iloc[0], df_s["label"].iloc[-1]],
                y=[med_spend, med_spend],
                mode="lines", name=f"Media R${med_spend:,.0f}",
                line=dict(color="#fff", width=1.2, dash="dash"),
                hoverinfo="skip",
                showlegend=True,
            ), secondary_y=False)

        _chart_layout(fig)
        fig.update_yaxes(title_text="Investimento (R$)", secondary_y=False,
                         tickprefix="R$ ", gridcolor="#222")
        fig.update_yaxes(title_text="Leads / CTR", secondary_y=True,
                         gridcolor="rgba(0,0,0,0)", showgrid=False)
        fig.update_layout(
            hovermode="x unified",
            hoverlabel=dict(bgcolor=CARD, font_color=TEXT, bordercolor=BORDER),
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Sem dados diarios para o periodo selecionado.")

with col_donut:
    camp_spend = [(c.get("campaign_name", "?"), float(c.get("spend", 0)))
                  for c in campanhas if float(c.get("spend", 0)) > 0]
    if camp_spend:
        nomes, vals = zip(*camp_spend)
        CORES_PIE = [ORANGE, "#fb923c", "#374151", "#6b7280", "#fcd34d",
                     "#9ca3af", "#d97706", "#1d4ed8", "#4ade80", "#f87171"]

        fig2 = go.Figure(go.Pie(
            labels=[n[:24] for n in nomes],
            values=vals, hole=0.58,
            marker=dict(colors=CORES_PIE[:len(nomes)],
                        line=dict(color=CARD, width=2)),
            textinfo="percent",
            hovertemplate="<b>%{label}</b><br>R$ %{value:,.2f}<br>%{percent}<extra></extra>",
        ))
        fig2.add_annotation(
            text=f"<b>{brl(spend)}</b><br>total",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=13, color="#fff"), align="center",
        )
        fig2.update_layout(
            title=dict(text="Budget por Campanha", font_size=13,
                       font_color=TEXT, x=0),
            height=340, margin=dict(l=0, r=0, t=36, b=0),
            paper_bgcolor=CARD,
            showlegend=True,
            legend=dict(font=dict(size=9, color=MUTED), x=1, y=0.5),
            font=dict(family="Inter, sans-serif"),
        )
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})


# ─── CAMPANHAS ────────────────────────────────────────────────────────────────

st.markdown('<div class="sec-hd">Desempenho por Campanha</div>', unsafe_allow_html=True)

if campanhas:
    total_sp = sum(float(c.get("spend", 0)) for c in campanhas) or 1
    rows_c = []
    for c in campanhas:
        s  = float(c.get("spend", 0))
        ld = leads_de(c.get("actions", []))
        rows_c.append({
            "Campanha":   c.get("campaign_name", "?"),
            "Gasto":      brl(s),
            "% Budget":   f"{s / total_sp * 100:.1f}%",
            "Leads":      str(ld) if ld else "—",
            "CPL":        brl(s / ld) if ld else "—",
            "CTR":        pct(c.get("ctr", 0)),
            "CPC":        brl(c.get("cpc", 0)),
            "CPM":        brl(c.get("cpm", 0)),
            "Freq.":      f"{float(c.get('frequency', 0)):.1f}x",
            "Impressoes": f"{int(float(c.get('impressions', 0))):,}".replace(",", "."),
            "Alcance":    f"{int(float(c.get('reach', 0))):,}".replace(",", "."),
        })
    df_c = pd.DataFrame(rows_c)
    st.dataframe(df_c, use_container_width=True, hide_index=True,
                 height=min(440, (len(rows_c) + 1) * 38))

    with st.expander("Ver grafico de campanhas"):
        bar_data = [(c.get("campaign_name", "?")[:32], float(c.get("spend", 0)),
                     leads_de(c.get("actions", [])))
                    for c in campanhas if float(c.get("spend", 0)) > 0]
        if bar_data:
            df_bar = pd.DataFrame(bar_data, columns=["Campanha", "Gasto", "Leads"])
            df_bar = df_bar.sort_values("Gasto")
            fig3 = go.Figure()
            fig3.add_trace(go.Bar(
                x=df_bar["Gasto"], y=df_bar["Campanha"],
                orientation="h",
                marker_color=ORANGE,
                text=[f"R${v:,.0f}" for v in df_bar["Gasto"]],
                textposition="outside",
                textfont=dict(color=TEXT, size=10),
                hovertemplate="<b>%{y}</b><br>R$ %{x:,.2f}<extra></extra>",
            ))
            _chart_layout(fig3, height=max(260, len(df_bar) * 42))
            fig3.update_layout(
                xaxis_title="Investimento (R$)", yaxis_title="",
                margin=dict(l=0, r=80, t=10, b=0),
            )
            st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})


# ─── ANALISE DE CRIATIVOS ─────────────────────────────────────────────────────

st.markdown('<div class="sec-hd">Analise de Criativos</div>', unsafe_allow_html=True)

ads_validos = [a for a in ads_data if float(a.get("spend", 0)) > 0]

col_f1, col_f2 = st.columns([3, 2])
with col_f1:
    camp_opts = sorted({a.get("campaign_name", "?") for a in ads_validos})
    sel_camps = st.multiselect("Filtrar por campanha:", camp_opts, placeholder="Todas as campanhas")
with col_f2:
    ordem = st.selectbox("Ordenar por:", ["Gasto", "CTR", "Leads", "Frequencia"])

if sel_camps:
    ads_validos = [a for a in ads_validos if a.get("campaign_name") in sel_camps]

ORDEM_MAP = {
    "Gasto":      lambda a: -float(a.get("spend", 0)),
    "CTR":        lambda a: -float(a.get("ctr", 0)),
    "Leads":      lambda a: -leads_de(a.get("actions", [])),
    "Frequencia": lambda a: -float(a.get("frequency", 0)),
}
ads_validos.sort(key=ORDEM_MAP[ordem])

# Resumo rapido por status
if ads_validos:
    n_escalar   = sum(1 for a in ads_validos if rec_badge(a.get("spend",0), a.get("ctr",0), a.get("frequency",0), media_ctr) == "ESCALAR")
    n_pausar    = sum(1 for a in ads_validos if rec_badge(a.get("spend",0), a.get("ctr",0), a.get("frequency",0), media_ctr) == "PAUSAR")
    n_monitorar = sum(1 for a in ads_validos if rec_badge(a.get("spend",0), a.get("ctr",0), a.get("frequency",0), media_ctr) == "MONITORAR")
    n_aguardar  = sum(1 for a in ads_validos if rec_badge(a.get("spend",0), a.get("ctr",0), a.get("frequency",0), media_ctr) == "AGUARDAR")

    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Escalar",   n_escalar,   help="CTR >= 125% da media com gasto relevante")
    r2.metric("Pausar",    n_pausar,    help="Frequencia alta ou CTR muito baixo")
    r3.metric("Monitorar", n_monitorar, help="Performance normal, acompanhar")
    r4.metric("Aguardar",  n_aguardar,  help="Gasto insuficiente para decisao")

    rows_a = []
    for a in ads_validos:
        s     = float(a.get("spend", 0))
        ctr_  = float(a.get("ctr", 0))
        freq_ = float(a.get("frequency", 0))
        cpc_  = float(a.get("cpc", 0))
        cpm_  = float(a.get("cpm", 0))
        imp_  = int(float(a.get("impressions", 0)))
        clk_  = int(float(a.get("clicks", 0)))
        ld    = leads_de(a.get("actions", []))
        badge = rec_badge(s, ctr_, freq_, media_ctr)

        BADGE_EMOJI = {
            "ESCALAR":   "🟢 ESCALAR",
            "PAUSAR":    "🔴 PAUSAR",
            "MONITORAR": "🔵 MONITORAR",
            "AGUARDAR":  "⏳ AGUARDAR",
        }

        rows_a.append({
            "Acao":       BADGE_EMOJI[badge],
            "Anuncio":    a.get("ad_name", "?"),
            "Campanha":   a.get("campaign_name", "?"),
            "Gasto":      brl(s),
            "Leads":      str(ld) if ld else "—",
            "CPL":        brl(s / ld) if ld else "—",
            "CTR":        pct(ctr_),
            "CPC":        brl(cpc_),
            "CPM":        brl(cpm_),
            "Freq.":      f"{freq_:.1f}x",
            "Cliques":    f"{clk_:,}".replace(",", "."),
            "Impressoes": f"{imp_:,}".replace(",", "."),
        })

    df_a = pd.DataFrame(rows_a)
    st.dataframe(
        df_a,
        use_container_width=True,
        hide_index=True,
        height=min(640, (len(rows_a) + 1) * 38),
        column_config={
            "Acao":    st.column_config.TextColumn("Acao",    width="medium"),
            "Anuncio": st.column_config.TextColumn("Anuncio", width="large"),
        },
    )

    # Mini-grafico top criativos por gasto
    with st.expander("Ver grafico: Top criativos por gasto"):
        top = ads_validos[:15]
        if top:
            nomes_a = [a.get("ad_name", "?")[:35] for a in top]
            gastos_a = [float(a.get("spend", 0)) for a in top]
            cores_a  = [
                ORANGE if rec_badge(a.get("spend",0), a.get("ctr",0), a.get("frequency",0), media_ctr) == "ESCALAR"
                else "#f87171" if rec_badge(a.get("spend",0), a.get("ctr",0), a.get("frequency",0), media_ctr) == "PAUSAR"
                else "#38bdf8" if rec_badge(a.get("spend",0), a.get("ctr",0), a.get("frequency",0), media_ctr) == "MONITORAR"
                else MUTED
                for a in top
            ]
            fig_a = go.Figure(go.Bar(
                x=gastos_a[::-1], y=nomes_a[::-1],
                orientation="h",
                marker_color=cores_a[::-1],
                text=[f"R${v:,.0f}" for v in gastos_a[::-1]],
                textposition="outside",
                textfont=dict(color=TEXT, size=10),
                hovertemplate="<b>%{y}</b><br>R$ %{x:,.2f}<extra></extra>",
            ))
            _chart_layout(fig_a, height=max(300, len(top) * 40))
            fig_a.update_layout(
                title=dict(text="Laranja=Escalar  Vermelho=Pausar  Azul=Monitorar",
                           font_size=10, font_color=MUTED, x=0),
                xaxis_title="Investimento (R$)", yaxis_title="",
                margin=dict(l=0, r=80, t=30, b=0),
            )
            st.plotly_chart(fig_a, use_container_width=True, config={"displayModeBar": False})
else:
    st.info("Nenhum anuncio com gasto no periodo selecionado.")


# ─── ALERTAS ─────────────────────────────────────────────────────────────────

st.markdown('<div class="sec-hd">Alertas e Recomendacoes</div>', unsafe_allow_html=True)

alertas = []
for c in campanhas:
    nome  = c.get("campaign_name", "?")
    freq_ = float(c.get("frequency", 0))
    ctr_c = float(c.get("ctr", 0))
    sp    = float(c.get("spend", 0))
    ld    = leads_de(c.get("actions", []))

    if freq_ > 3.5:
        alertas.append(("red", f"<b>{nome}</b>: frequencia {freq_:.1f}x — publico saturando. "
                                "Renovar criativos ou ampliar segmentacao."))
    elif freq_ > 2.5:
        alertas.append(("yel", f"<b>{nome}</b>: frequencia {freq_:.1f}x — atenção. "
                                "Monitorar saturacao do publico."))
    if sp > 50 and media_ctr > 0 and ctr_c < media_ctr * 0.5:
        alertas.append(("yel", f"<b>{nome}</b>: CTR {pct(ctr_c)} muito abaixo da media "
                                f"({pct(media_ctr)}). Revisar criativos e copy."))
    if sp > 100 and ld == 0:
        alertas.append(("yel", f"<b>{nome}</b>: {brl(sp)} gastos sem lead. "
                                "Revisar segmentacao e oferta."))
    if media_ctr > 0 and ctr_c >= media_ctr * 1.3 and sp >= 50:
        alertas.append(("grn", f"<b>{nome}</b>: CTR {pct(ctr_c)} — performance acima da media. "
                                "Considere aumentar budget em 20-30%."))

if not alertas:
    alertas.append(("grn", "Conta com performance dentro do esperado. Nenhuma acao urgente identificada."))

a_col, _ = st.columns([3, 1])
with a_col:
    for tipo, msg in alertas[:12]:
        st.markdown(f'<div class="al al-{tipo}">{msg}</div>', unsafe_allow_html=True)


# ─── RODAPE ───────────────────────────────────────────────────────────────────

st.markdown('<hr style="border-color:#2a2a2a;margin:20px 0 10px;">', unsafe_allow_html=True)
st.markdown(
    f'<div style="font-size:10px;color:{MUTED};text-align:center;padding:2px 0 12px;">'
    f'G3 Veiculos &middot; Trafego Pago &middot; Meta Ads API &middot; '
    f'{ini.strftime("%d/%m/%Y")} ate {fim.strftime("%d/%m/%Y")} &middot; '
    f'Atualizado em {datetime.now().strftime("%d/%m/%Y %H:%M")}'
    f'</div>',
    unsafe_allow_html=True,
)
