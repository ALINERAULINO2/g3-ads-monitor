#!/usr/bin/env python3
"""
G3 Ads Monitor — Dashboard Online
Streamlit + Plotly · Meta Ads API
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import requests
import os
from datetime import datetime, timedelta, date
from pathlib import Path

# ─── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="G3 Ads Monitor",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "G3 Ads Monitor — Dashboard Meta Ads · G3 Veículos"},
)

# ─── Credentials ─────────────────────────────────────────────────────────────
try:
    TOKEN   = st.secrets["META_ACCESS_TOKEN"]
    ACCOUNT = st.secrets["META_AD_ACCOUNT_ID"]
except Exception:
    TOKEN   = os.getenv("META_ACCESS_TOKEN", "")
    ACCOUNT = os.getenv("META_AD_ACCOUNT_ID", "")

BASE   = "https://graph.facebook.com/v20.0"
ORANGE = "#F7931E"
DARK   = "#111111"

# ─── CSS ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1rem !important; padding-bottom: 0.5rem !important; }

/* ── Cabeçalho ── */
.g3-header {
    background: #111111;
    border-radius: 12px;
    padding: 18px 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 22px;
}
.g3-title  { color: #fff; font-size: 24px; font-weight: 900; letter-spacing: -0.5px; }
.g3-title span { color: #F7931E; }
.g3-sub    { color: #9ca3af; font-size: 11px; margin-top: 3px; }
.g3-badge  { background: #F7931E; color: #111; font-size: 10px; font-weight: 800;
              padding: 5px 14px; border-radius: 6px; white-space: nowrap; }

/* ── KPI cards ── */
.kpi-wrap  { display: flex; gap: 12px; margin-bottom: 20px; flex-wrap: wrap; }
.kpi-card  {
    flex: 1; min-width: 130px;
    background: #fff;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    padding: 14px 16px;
    border-top: 4px solid #F7931E;
    box-shadow: 0 1px 3px rgba(0,0,0,.06);
}
.kpi-lbl   { font-size: 9px; color: #6b7280; text-transform: uppercase;
              letter-spacing: .6px; font-weight: 700; margin-bottom: 5px; }
.kpi-val   { font-size: 24px; font-weight: 900; color: #111; line-height: 1; }
.kpi-delta { font-size: 11px; margin-top: 5px; }
.kpi-sub   { font-size: 10px; color: #9ca3af; margin-top: 3px; }
.up   { color: #15803d; } .dn { color: #b91c1c; } .neu { color: #6b7280; }

/* ── Seção ── */
.sec-hd {
    font-size: 13px; font-weight: 800; color: #111;
    border-left: 4px solid #F7931E;
    padding-left: 10px; margin: 18px 0 10px;
    text-transform: uppercase; letter-spacing: .4px;
}

/* ── Alertas ── */
.al { padding: 9px 14px 9px 14px; border-left: 4px solid;
       border-radius: 0 6px 6px 0; margin-bottom: 7px;
       font-size: 12px; line-height: 1.5; }
.al-red { background:#fef2f2; border-color:#dc2626; color:#7f1d1d; }
.al-yel { background:#fefce8; border-color:#ca8a04; color:#713f12; }
.al-grn { background:#f0fdf4; border-color:#16a34a; color:#14532d; }

/* ── Frequência gauge pill ── */
.freq-ok  { color:#15803d; font-weight:800; }
.freq-med { color:#d97706; font-weight:800; }
.freq-bad { color:#b91c1c; font-weight:800; }

/* ── Sidebar ── */
[data-testid="stSidebar"] { background: #fafafa !important; }
.sb-sec { font-size:10px; font-weight:800; color:#F7931E;
           text-transform:uppercase; letter-spacing:.6px; margin: 14px 0 5px; }

/* ── Print ── */
@media print {
    [data-testid="stSidebar"],
    [data-testid="stHeader"],
    .stButton, .stMultiSelect, .element-container:has(.stButton) { display:none !important; }
    .g3-header, .kpi-card { -webkit-print-color-adjust:exact; print-color-adjust:exact; }
    .block-container { padding: 0 !important; }
    body { font-size: 10px; }
}
</style>
""", unsafe_allow_html=True)


# ─── API ─────────────────────────────────────────────────────────────────────

def _api(endpoint, params=None):
    p = {"access_token": TOKEN}
    if params:
        p.update(params)
    try:
        r = requests.get(f"{BASE}/{endpoint}", params=p, timeout=25)
        return r.json()
    except Exception as e:
        return {"error": str(e)}


@st.cache_data(ttl=3600, show_spinner=False)
def check_token():
    return "error" not in _api("me", {"fields": "id"})


@st.cache_data(ttl=1800, show_spinner=False)
def get_conta(since, until):
    fields = "impressions,reach,clicks,spend,ctr,cpc,cpm,frequency,actions"
    d = _api(f"{ACCOUNT}/insights", {
        "fields": fields,
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
    return sorted(d.get("data", []), key=lambda x: x.get("date_start", ""))


@st.cache_data(ttl=1800, show_spinner=False)
def get_campanhas(since, until):
    fields = "campaign_name,impressions,reach,clicks,spend,ctr,cpc,cpm,frequency,actions"
    d = _api(f"{ACCOUNT}/insights", {
        "fields": fields,
        "time_range": f'{{"since":"{since}","until":"{until}"}}',
        "level": "campaign", "limit": 50,
    })
    return sorted(d.get("data", []), key=lambda x: float(x.get("spend", 0)), reverse=True)


@st.cache_data(ttl=1800, show_spinner=False)
def get_ads(since, until):
    fields = "ad_id,ad_name,campaign_name,adset_name,impressions,clicks,spend,ctr,cpc,cpm,frequency,actions"
    d = _api(f"{ACCOUNT}/insights", {
        "fields": fields,
        "time_range": f'{{"since":"{since}","until":"{until}"}}',
        "level": "ad", "limit": 100,
    })
    return sorted(d.get("data", []), key=lambda x: float(x.get("spend", 0)), reverse=True)


# ─── Helpers ─────────────────────────────────────────────────────────────────

def leads_de(actions):
    TIPOS = [
        "onsite_conversion.messaging_conversation_started_7d",
        "lead", "offsite_conversion.fb_pixel_lead", "omni_complete_registration",
    ]
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
    except:
        return "R$ 0,00"


def pct(v):
    try:
        return f"{float(v):.2f}%"
    except:
        return "—"


def delta_html(a, b, inv=False):
    if not b:
        return '<span class="neu">—</span>'
    v = (float(a) - float(b)) / float(b) * 100
    sobe = v >= 0
    if inv:
        sobe = not sobe
    cls   = "up" if sobe else "dn"
    arrow = "▲" if v >= 0 else "▼"
    return f'<span class="{cls}">{arrow} {abs(v):.1f}% vs ant.</span>'


def kpi(lbl, val, dh="", sub=""):
    return f"""<div class="kpi-card">
      <div class="kpi-lbl">{lbl}</div>
      <div class="kpi-val">{val}</div>
      <div class="kpi-delta">{dh}</div>
      {"" if not sub else f'<div class="kpi-sub">{sub}</div>'}
    </div>"""


def rec(spend, ctr_, freq_, media_ctr):
    if float(freq_) > 3.5 or (float(spend) > 30 and float(ctr_) < float(media_ctr) * 0.5):
        return "🔴 PAUSAR"
    if float(ctr_) >= float(media_ctr) * 1.25 and float(spend) >= 30:
        return "🟢 ESCALAR"
    if float(spend) < 10:
        return "⏳ AGUARDAR"
    return "🔵 MONITORAR"


# ─── Presets de data ──────────────────────────────────────────────────────────

def _last_month():
    today = date.today()
    fim   = today.replace(day=1) - timedelta(1)
    return fim.replace(day=1), fim


PRESETS = {
    "Hoje":            (date.today(), date.today()),
    "Ontem":           (date.today()-timedelta(1), date.today()-timedelta(1)),
    "Últimos 7 dias":  (date.today()-timedelta(7), date.today()-timedelta(1)),
    "Últimos 14 dias": (date.today()-timedelta(14), date.today()-timedelta(1)),
    "Últimos 30 dias": (date.today()-timedelta(30), date.today()-timedelta(1)),
    "Este mês":        (date.today().replace(day=1), date.today()),
    "Mês anterior":    _last_month(),
    "Personalizado":   (date.today()-timedelta(30), date.today()-timedelta(1)),
}

# ─── Sidebar ─────────────────────────────────────────────────────────────────

with st.sidebar:
    logo_p = Path(__file__).parent / "logo.png"
    if logo_p.exists():
        st.image(str(logo_p), width=190)
    else:
        st.markdown("### 🚗 G3 Ads Monitor")

    st.markdown("---")
    st.markdown('<div class="sb-sec">📅 Período</div>', unsafe_allow_html=True)

    preset = st.selectbox("Período", list(PRESETS.keys()), index=5, label_visibility="collapsed")

    if preset == "Personalizado":
        c1, c2 = st.columns(2)
        ini = c1.date_input("De",  value=date.today()-timedelta(30))
        fim = c2.date_input("Até", value=date.today()-timedelta(1))
    else:
        ini, fim = PRESETS[preset]

    since = ini.strftime("%Y-%m-%d")
    until = fim.strftime("%Y-%m-%d")

    # Período anterior (mesma duração)
    n_dias   = max((fim - ini).days, 0)
    prev_ini = ini - timedelta(days=n_dias + 1)
    prev_fim = ini - timedelta(days=1)
    psince   = prev_ini.strftime("%Y-%m-%d")
    puntil   = prev_fim.strftime("%Y-%m-%d")

    st.markdown('<div class="sb-sec">⚙️ Ações</div>', unsafe_allow_html=True)

    if st.button("↺  Atualizar dados", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    if st.button("🖨️  Imprimir / Salvar PDF", use_container_width=True):
        st.components.v1.html("<script>window.print();</script>", height=0)

    st.markdown("---")
    st.caption(f"Conta: `{ACCOUNT}`")
    st.caption(f"{ini.strftime('%d/%m/%Y')} → {fim.strftime('%d/%m/%Y')}")
    st.caption(f"Comparando com: {prev_ini.strftime('%d/%m')} → {prev_fim.strftime('%d/%m/%Y')}")


# ─── Verificações ────────────────────────────────────────────────────────────

if not TOKEN or not ACCOUNT:
    st.error("⚙️ Configure META_ACCESS_TOKEN e META_AD_ACCOUNT_ID em `.streamlit/secrets.toml`")
    st.stop()

with st.spinner("Verificando credenciais Meta Ads…"):
    if not check_token():
        st.error("""
        **🔴 Token Meta Ads expirado.**

        Renove em [developers.facebook.com](https://developers.facebook.com) → **Graph API Explorer**
        Gere novo token com permissões `ads_read` e `ads_management`, depois atualize em **Secrets** no Streamlit Cloud.
        """)
        st.stop()


# ─── Carregar dados ───────────────────────────────────────────────────────────

with st.spinner("Carregando dados da Meta Ads API…"):
    conta     = get_conta(since, until)
    conta_ant = get_conta(psince, puntil)
    serie     = get_serie(since, until)
    campanhas = get_campanhas(since, until)
    ads_data  = get_ads(since, until)


# ─── Métricas ────────────────────────────────────────────────────────────────

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
cpl    = spend / leads  if leads  else 0
a_cpl  = a_spend / a_leads if a_leads else 0
media_ctr = ctr


# ─── HEADER ──────────────────────────────────────────────────────────────────

freq_cls = "freq-bad" if freq > 3.5 else ("freq-med" if freq > 2.5 else "freq-ok")
periodo_txt = f"{ini.strftime('%d/%m')} – {fim.strftime('%d/%m/%Y')}"

st.markdown(f"""
<div class="g3-header">
  <div>
    <div class="g3-title">G3 <span>Ads Monitor</span></div>
    <div class="g3-sub">Meta Ads · {periodo_txt} &nbsp;·&nbsp; Conta {ACCOUNT}</div>
  </div>
  <div class="g3-badge">⟳ {datetime.now().strftime('%d/%m/%Y %H:%M')}</div>
</div>
""", unsafe_allow_html=True)


# ─── KPI CARDS ───────────────────────────────────────────────────────────────

cols = st.columns(6)
kpis = [
    ("💰 Investimento",      brl(spend),    delta_html(spend, a_spend),       f"Ant: {brl(a_spend)}"),
    ("🎯 Leads / Resultados", str(leads),   delta_html(leads, a_leads),       f"CPL: {brl(cpl)}"),
    ("📊 CTR",               pct(ctr),      delta_html(ctr, a_ctr),           "Bench: 1,5%–3,0%"),
    ("💵 CPL",               brl(cpl),      delta_html(cpl, a_cpl, inv=True), f"Ant: {brl(a_cpl)}"),
    ("🖱️ CPC",               brl(cpc),      delta_html(cpc, a_cpc, inv=True), f"CPM: {brl(cpm)}"),
    ("🔁 Frequência",        f'<span class="{freq_cls}">{freq:.1f}x</span>',
                             delta_html(cpm, a_cpm, inv=True),                "Ideal: < 3,0x"),
]
for col, (lbl, val, dh, sub) in zip(cols, kpis):
    col.markdown(kpi(lbl, val, dh, sub), unsafe_allow_html=True)

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)


# ─── LINHA 2: Alcance + Impressões + Cliques ─────────────────────────────────

c1, c2, c3, c4 = st.columns(4)
c1.metric("Impressões",  f"{imp:,}".replace(",","."),  help="Total de impressões no período")
c2.metric("Alcance",     f"{reach:,}".replace(",","."), help="Pessoas únicas alcançadas")
c3.metric("Cliques",     f"{clicks:,}".replace(",","."), help="Cliques totais no link")
c4.metric("CPM",         brl(cpm), delta=f"{((cpm-a_cpm)/a_cpm*100):+.1f}% vs ant." if a_cpm else None,
          delta_color="inverse")

st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)


# ─── GRÁFICO DIÁRIO + DONUT ───────────────────────────────────────────────────

st.markdown('<div class="sec-hd">📈 Evolução Diária</div>', unsafe_allow_html=True)
col_trend, col_donut = st.columns([62, 38])

with col_trend:
    if serie:
        df_s = pd.DataFrame(serie)
        df_s["spend"]     = pd.to_numeric(df_s["spend"], errors="coerce").fillna(0)
        df_s["ctr"]       = pd.to_numeric(df_s.get("ctr", 0), errors="coerce").fillna(0)
        df_s["leads_dia"] = df_s["actions"].apply(leads_de) if "actions" in df_s.columns else 0
        df_s["label"]     = pd.to_datetime(df_s["date_start"]).dt.strftime("%d/%m")

        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Bar(
            x=df_s["label"], y=df_s["spend"], name="Investimento (R$)",
            marker_color=DARK, opacity=0.85,
            hovertemplate="<b>%{x}</b><br>R$ %{y:,.2f}<extra></extra>",
        ), secondary_y=False)
        fig.add_trace(go.Scatter(
            x=df_s["label"], y=df_s["ctr"], name="CTR (%)",
            line=dict(color=ORANGE, width=2.5), mode="lines+markers",
            marker=dict(size=6, color=ORANGE),
            hovertemplate="<b>%{x}</b><br>CTR: %{y:.2f}%<extra></extra>",
        ), secondary_y=True)
        if df_s["leads_dia"].sum() > 0:
            fig.add_trace(go.Scatter(
                x=df_s["label"], y=df_s["leads_dia"], name="Leads",
                line=dict(color="#7c3aed", width=2, dash="dot"),
                mode="lines+markers", marker=dict(size=5),
                hovertemplate="<b>%{x}</b><br>Leads: %{y}<extra></extra>",
            ), secondary_y=True)

        # Linha de média de gasto
        med = df_s["spend"].mean()
        fig.add_hline(y=med, line_dash="dash", line_color=ORANGE,
                      annotation_text=f"Média: R${med:.0f}",
                      annotation_position="top right", secondary_y=False)

        fig.update_layout(
            height=320, margin=dict(l=0, r=10, t=20, b=0),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font_size=11),
            plot_bgcolor="#fafafa", paper_bgcolor="#fff",
            font=dict(family="Inter, sans-serif", color=DARK),
            bargap=0.25,
        )
        fig.update_yaxes(title_text="Investimento (R$)", secondary_y=False,
                         gridcolor="#f0f0f0", tickprefix="R$")
        fig.update_yaxes(title_text="CTR / Leads", secondary_y=True,
                         gridcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Sem dados diários para o período selecionado.")

with col_donut:
    df_c = pd.DataFrame(campanhas)
    if not df_c.empty:
        df_c["spend"] = pd.to_numeric(df_c["spend"], errors="coerce").fillna(0)
        df_c = df_c[df_c["spend"] > 0]
        CORES = [DARK, ORANGE, "#374151", "#fb923c", "#6b7280",
                 "#fcd34d", "#9ca3af", "#fde68a", "#1d4ed8", "#60a5fa"]
        fig2 = go.Figure(go.Pie(
            labels=df_c["campaign_name"].str[:22],
            values=df_c["spend"], hole=.58,
            marker=dict(colors=CORES[:len(df_c)], line=dict(color="#fff", width=2)),
            textinfo="percent",
            hovertemplate="<b>%{label}</b><br>%{value:,.2f}<br>%{percent}<extra></extra>",
        ))
        fig2.add_annotation(
            text=f"<b>{brl(spend)}</b><br><span style='font-size:10px'>total</span>",
            x=0.5, y=0.5, showarrow=False, font_size=13, font_color=DARK, align="center",
        )
        fig2.update_layout(
            title=dict(text="Budget por Campanha", font_size=13, font_color=DARK, x=0),
            height=320, margin=dict(l=0, r=0, t=36, b=0),
            showlegend=True, paper_bgcolor="#fff",
            legend=dict(font_size=9, orientation="v", x=1, y=0.5),
            font=dict(family="Inter, sans-serif"),
        )
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})


# ─── TABELA POR CAMPANHA ──────────────────────────────────────────────────────

st.markdown('<div class="sec-hd">🗂️ Desempenho por Campanha</div>', unsafe_allow_html=True)

if campanhas:
    total_sp = sum(float(c.get("spend", 0)) for c in campanhas)
    rows = []
    for c in campanhas:
        s  = float(c.get("spend", 0))
        ld = leads_de(c.get("actions", []))
        rows.append({
            "Campanha":   c.get("campaign_name", "?"),
            "Gasto":      brl(s),
            "% Budget":   f"{s/total_sp*100:.0f}%" if total_sp else "—",
            "Impressões": f"{int(float(c.get('impressions',0))):,}".replace(",","."),
            "Alcance":    f"{int(float(c.get('reach',0))):,}".replace(",","."),
            "Cliques":    f"{int(float(c.get('clicks',0))):,}".replace(",","."),
            "CTR":        pct(c.get("ctr", 0)),
            "CPC":        brl(c.get("cpc", 0)),
            "CPM":        brl(c.get("cpm", 0)),
            "Freq.":      f"{float(c.get('frequency',0)):.1f}x",
            "Leads":      str(ld) if ld else "—",
            "CPL":        brl(s/ld) if ld else "—",
        })
    df_camp = pd.DataFrame(rows)
    st.dataframe(df_camp, use_container_width=True, hide_index=True,
                 height=min(420, (len(rows)+1)*38))

    # Gráfico barras horizontal por campanha
    with st.expander("📊 Ver gráfico de campanhas"):
        df_bar = pd.DataFrame([{
            "Campanha": c.get("campaign_name","?")[:30],
            "Gasto":    float(c.get("spend",0)),
            "Leads":    leads_de(c.get("actions",[])),
        } for c in campanhas if float(c.get("spend",0))>0])
        if not df_bar.empty:
            fig3 = px.bar(df_bar.sort_values("Gasto"), x="Gasto", y="Campanha",
                          orientation="h", color_discrete_sequence=[ORANGE],
                          text=df_bar.sort_values("Gasto")["Gasto"].apply(lambda v: f"R${v:,.0f}"),
                          height=max(250, len(df_bar)*42))
            fig3.update_layout(plot_bgcolor="#fafafa", paper_bgcolor="#fff",
                               font_family="Inter", margin=dict(l=0,r=60,t=10,b=0),
                               xaxis_title="Investimento (R$)", yaxis_title="")
            fig3.update_traces(textposition="outside")
            st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})


# ─── TABELA DE ANÚNCIOS ───────────────────────────────────────────────────────

st.markdown('<div class="sec-hd">🎨 Análise de Criativos</div>', unsafe_allow_html=True)

ads_filtrados = [a for a in ads_data if float(a.get("spend", 0)) > 0]

# Filtros
col_f1, col_f2 = st.columns([1, 1])
with col_f1:
    camp_opts = sorted(set(a.get("campaign_name","?") for a in ads_filtrados))
    sel_camps = st.multiselect("Filtrar campanha:", camp_opts, placeholder="Todas")
with col_f2:
    ordem = st.selectbox("Ordenar por:", ["Gasto ↓", "CTR ↓", "Leads ↓", "Frequência ↓"],
                         label_visibility="visible")

if sel_camps:
    ads_filtrados = [a for a in ads_filtrados if a.get("campaign_name") in sel_camps]

ORDEM_MAP = {
    "Gasto ↓":       lambda a: -float(a.get("spend", 0)),
    "CTR ↓":         lambda a: -float(a.get("ctr", 0)),
    "Leads ↓":       lambda a: -leads_de(a.get("actions", [])),
    "Frequência ↓":  lambda a: -float(a.get("frequency", 0)),
}
ads_filtrados.sort(key=ORDEM_MAP[ordem])

if ads_filtrados:
    rows_ads = []
    for a in ads_filtrados:
        s    = float(a.get("spend", 0))
        ctr_ = float(a.get("ctr", 0))
        freq_= float(a.get("frequency", 0))
        cpc_ = float(a.get("cpc", 0))
        cpm_ = float(a.get("cpm", 0))
        ld   = leads_de(a.get("actions", []))
        rows_ads.append({
            "Anúncio":    a.get("ad_name", "?"),
            "Campanha":   a.get("campaign_name", "?"),
            "Conjunto":   a.get("adset_name", "?"),
            "Gasto":      brl(s),
            "CTR":        pct(ctr_),
            "CPC":        brl(cpc_),
            "CPM":        brl(cpm_),
            "Freq.":      f"{freq_:.1f}x",
            "Cliques":    f"{int(float(a.get('clicks',0))):,}".replace(",","."),
            "Impressões": f"{int(float(a.get('impressions',0))):,}".replace(",","."),
            "Leads":      str(ld) if ld else "—",
            "CPL":        brl(s/ld) if ld else "—",
            "Ação":       rec(s, ctr_, freq_, media_ctr),
        })

    df_ads = pd.DataFrame(rows_ads)

    def _style_acao(v):
        c = {"🟢 ESCALAR":"background:#dcfce7;color:#15803d;font-weight:700",
             "🔴 PAUSAR": "background:#fee2e2;color:#b91c1c;font-weight:700",
             "🔵 MONITORAR":"background:#eff6ff;color:#1d4ed8;font-weight:700",
             "⏳ AGUARDAR":"background:#f1f5f9;color:#64748b;font-weight:700"}
        return c.get(v, "")

    def _style_freq(v):
        try:
            f = float(str(v).replace("x",""))
            if f > 3.5: return "color:#b91c1c;font-weight:700"
            if f > 2.5: return "color:#d97706;font-weight:700"
            return "color:#15803d"
        except: return ""

    styled = df_ads.style \
        .applymap(_style_acao,  subset=["Ação"]) \
        .applymap(_style_freq,  subset=["Freq."])

    st.dataframe(styled, use_container_width=True, hide_index=True,
                 height=min(600, (len(rows_ads)+1)*38))
else:
    st.info("Nenhum anúncio com gasto no período selecionado.")


# ─── ALERTAS ─────────────────────────────────────────────────────────────────

st.markdown('<div class="sec-hd">⚡ Alertas & Recomendações</div>', unsafe_allow_html=True)

alertas = []
for c in campanhas:
    nome  = c.get("campaign_name","?")
    freq_ = float(c.get("frequency", 0))
    ctr_  = float(c.get("ctr", 0))
    sp    = float(c.get("spend", 0))
    ld    = leads_de(c.get("actions", []))
    if freq_ > 3.5:
        alertas.append(("red", f"<b>{nome}</b>: frequência {freq_:.1f}x — público saturando. Renovar criativos ou ampliar segmentação."))
    elif freq_ > 2.5:
        alertas.append(("yel", f"<b>{nome}</b>: frequência {freq_:.1f}x — atenção. Monitorar saturação."))
    if sp > 50 and media_ctr > 0 and ctr_ < media_ctr * 0.5:
        alertas.append(("yel", f"<b>{nome}</b>: CTR {pct(ctr_)} — muito abaixo da média ({pct(media_ctr)}). Revisar criativos."))
    if sp > 100 and ld == 0:
        alertas.append(("yel", f"<b>{nome}</b>: {brl(sp)} gastos sem lead. Revisar segmentação e oferta."))
    if media_ctr > 0 and ctr_ >= media_ctr * 1.3 and sp >= 50:
        alertas.append(("grn", f"<b>{nome}</b>: CTR {pct(ctr_)} — ótima performance. Considere aumentar budget em 20–30%."))

if not alertas:
    alertas.append(("grn", "Conta com performance dentro do esperado. Nenhuma ação urgente identificada."))

a_col, _ = st.columns([3, 1])
with a_col:
    for tipo, msg in alertas[:10]:
        st.markdown(f'<div class="al al-{tipo}">{msg}</div>', unsafe_allow_html=True)


# ─── RODAPÉ ──────────────────────────────────────────────────────────────────

st.markdown("---")
st.markdown(
    f'<div style="font-size:10px;color:#9ca3af;text-align:center;padding:4px 0 12px">'
    f'G3 Veículos · G3 Ads Monitor · Meta Ads API · '
    f'{ini.strftime("%d/%m/%Y")} → {fim.strftime("%d/%m/%Y")} · '
    f'Atualizado em {datetime.now().strftime("%d/%m/%Y às %H:%M")}'
    f'</div>',
    unsafe_allow_html=True,
)
