import streamlit as st
import pandas as pd
import numpy as np
import unicodedata
import os
import sqlite3


# 1. Page Configuration
st.set_page_config(
    page_title="ULS Indicadores SNS - Painel de Controlo",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# 2. Theme Toggle State and Sorting State
if "theme" not in st.session_state:
    st.session_state.theme = "light"

# Sync with URL query parameters for click-to-sort AND filter preservation
params = st.query_params

# Page control ('matriz' or 'perfil')
page = params.get("page", "matriz")
st.session_state.page = page

# Selected Indicator for Profile Page (defaults to first indicator in list)
selected_ind = params.get("ind", "% 1ªs Cons. Tempo Adeq.").replace("_", " ").replace("pct", "%").replace("slash", "/")
st.session_state.selected_ind = selected_ind

# Selected ULS for Profile Page (defaults to 'Baixo Mondego' or first available)
selected_uls = params.get("uls", "ULS Região de Aveiro").replace("_", " ").replace("slash", "/")
st.session_state.selected_uls = selected_uls

# Toggle for Profile Page comparison mode ('indicadores' or 'comparacao')
profile_mode = params.get("pmode", "comparacao")
st.session_state.profile_mode = profile_mode

if "sort" in params:
    q_sort = params["sort"].replace("_", " ").replace("pct", "%").replace("slash", "/")
    st.session_state.sort_ind = q_sort
    st.session_state.sort_state = int(params.get("state", 0))
else:
    st.session_state.sort_ind = None
    st.session_state.sort_state = 0

# Restore filter values from URL params (set when sort/nav links are clicked)
_url_end_month  = params.get("end",   None)
_url_start_month= params.get("start", None)
_url_persp_idx  = params.get("persp", None)
_url_groups     = params.get("grps",  None)  # comma-separated group names
_url_dims       = params.get("dims",  None)  # comma-separated dimension names

if "prev_points" not in st.session_state:
    st.session_state.prev_points = []

def toggle_theme():
    st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"

IS_DARK = st.session_state.theme == "dark"

# 3. Inject Custom CSS for Premium Zinc Design
theme_css = f"""
<style>
:root {{
    --bg: { '#09090b' if IS_DARK else '#ffffff' };
    --bg-subtle: { '#0c0c0f' if IS_DARK else '#f9fafb' };
    --card: { '#0c0c0f' if IS_DARK else '#ffffff' };
    --card-hover: { '#131316' if IS_DARK else '#f4f4f5' };
    --border: { '#1e1e24' if IS_DARK else '#e4e4e7' };
    --border-subtle: { '#16161a' if IS_DARK else '#f0f0f2' };
    --text: { '#fafafa' if IS_DARK else '#09090b' };
    --text-muted: { '#d4d4d8' if IS_DARK else '#3f3f46' };
    --text-dim: { '#a1a1aa' if IS_DARK else '#71717a' };
    --accent: #2563eb;
    --accent-muted: #1d4ed8;
    --green: { '#22c55e' if IS_DARK else '#16a34a' };
    --green-muted: { 'rgba(34,197,94,0.12)' if IS_DARK else 'rgba(22,163,74,0.08)' };
    --red: { '#ef4444' if IS_DARK else '#dc2626' };
    --red-muted: { 'rgba(239,68,68,0.12)' if IS_DARK else 'rgba(220,38,38,0.08)' };
    --amber: { '#f59e0b' if IS_DARK else '#d97706' };
    --amber-muted: { 'rgba(245,158,11,0.12)' if IS_DARK else 'rgba(217,119,6,0.08)' };
    --shadow: { 'none' if IS_DARK else '0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.03)' };
    --radius: 10px;
}}

/* Hide Streamlit elements */
header[data-testid="stHeader"], #MainMenu, footer, [data-testid="stToolbar"],
[data-testid="stDecoration"], [data-testid="stStatusWidget"], .stDeployButton,
div[data-testid="stSidebarCollapsedControl"] {{
    display: none !important;
}}

/* Global app styling */
html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"], .main, .block-container, section[data-testid="stMain"] {{
    background-color: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'DM Sans', -apple-system, sans-serif !important;
}}
.block-container {{
    padding: 0 2rem 2rem !important;
    max-width: 1440px !important;
}}

/* Brand header */
.brand-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid var(--border);
    padding-bottom: 0.4rem;
    margin-bottom: 0.4rem;
}}
.brand-name {{
    font-size: 1.15rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: var(--text);
    display: flex;
    align-items: center;
    gap: 8px;
}}
.brand-symbol {{
    color: var(--accent);
    font-size: 1.25rem;
}}

/* Layout columns gaps */
[data-testid="stHorizontalBlock"] {{ gap: 1rem !important; }}

/* KPI Cards */
.metric-card {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1rem 1.2rem;
    box-shadow: var(--shadow);
}}
.metric-label {{
    font-size: 0.75rem;
    color: var(--text-muted);
    font-weight: 500;
}}
.metric-value {{
    font-size: 1.45rem;
    font-weight: 700;
    color: var(--text);
    letter-spacing: -0.02em;
    margin-top: 2px;
}}

/* Chart wraps */
.chart-wrap {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1rem 1.2rem 0.5rem;
    box-shadow: var(--shadow);
    margin-bottom: 1rem;
}}
.chart-header {{
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 0.6rem;
}}
.chart-title {{
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--text);
}}
.chart-subtitle {{
    font-size: 0.72rem;
    color: var(--text-dim);
}}

/* HTML data table */
.table-wrap {{
    margin-top: 1rem;
    border: 1px solid var(--border);
    border-radius: var(--radius);
    overflow: hidden;
    box-shadow: var(--shadow);
    background: var(--card);
}}
.data-table {{
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    font-size: 0.78rem;
}}
.data-table th {{
    text-align: left;
    padding: 0.65rem 0.8rem;
    color: var(--text-muted);
    font-weight: 600;
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    border-bottom: 1px solid var(--border);
    background: var(--bg-subtle);
}}
.data-table td {{
    padding: 0.6rem 0.8rem;
    color: var(--text);
    border-bottom: 1px solid var(--border-subtle);
}}
.data-table tr:last-child td {{
    border-bottom: none;
}}
.data-table tr:hover td {{
    background-color: var(--card-hover);
}}

/* Heatmap Table Styles */
.heatmap-table {{
    border-collapse: collapse;
    font-family: 'DM Sans', sans-serif;
    color: var(--text);
    width: 100%;
}}
.heatmap-table th {{
    font-size: 8.5px;
    font-weight: bold;
    text-align: center;
    vertical-align: bottom;
    border-bottom: 2px solid var(--border);
    padding: 4px 4px 8px 4px;
    min-width: 48px;
    position: sticky;
    top: 0;
    z-index: 10;
    background-color: var(--bg);
}}
.heatmap-table th .hdr-label {{
    word-break: break-word;
    line-height: 1.2;
    padding: 0 2px;
}}
.heatmap-table td.row-lbl {{
    font-size: 9.5px;
    font-weight: bold;
    text-align: right;
    padding: 3px 8px;
    border-right: 2px solid var(--border);
    min-width: 165px;
    max-width: 165px;
    width: 165px;
    white-space: nowrap;
    position: sticky;
    left: 0;
    z-index: 5;
    background-color: var(--bg);
}}
.heatmap-table td.cell {{
    text-align: center;
    font-weight: bold;
    font-size: 8px;
    min-width: 48px;
    height: 20px;
    border: 1px solid var(--border-subtle);
    cursor: pointer;
}}


/* Badges and Delta cells */
.badge {{
    display: inline-block;
    padding: 2px 7px;
    border-radius: 5px;
    font-size: 0.7rem;
    font-weight: 600;
}}
.badge-green {{ color: var(--green); background: var(--green-muted); }}
.badge-red {{ color: var(--red); background: var(--red-muted); }}
.badge-neutral {{ color: var(--text-muted); background: var(--border); }}

/* Selectboxes and components styling */
div[data-baseweb="select"] > div {{
    background-color: var(--card) !important;
    border-color: var(--border) !important;
    color: var(--text) !important;
    border-radius: 7px !important;
    font-size: 0.75rem !important;
    min-height: 28px !important;
    height: 28px !important;
    padding-top: 0px !important;
    padding-bottom: 0px !important;
    align-items: center !important;
}}
div[data-baseweb="select"] > div > div {{
    padding-top: 0px !important;
    padding-bottom: 0px !important;
}}
/* Compact multiselect tags */
div[role="button"] {{
    padding-top: 0px !important;
    padding-bottom: 0px !important;
    height: 20px !important;
    font-size: 0.7rem !important;
}}
/* Compact labels */
label[data-testid="stWidgetLabel"] {{
    margin-bottom: 4px !important;
    padding-bottom: 0px !important;
    font-size: 0.8rem !important;
    font-weight: 600 !important;
    color: var(--text-dim) !important;
}}
/* Reduce general spacing */
div[data-testid="stVerticalBlock"] > div {{
    gap: 0.2rem !important;
}}
div[data-baseweb="popover"] {{
    background-color: var(--card) !important;
    color: var(--text) !important;
}}

/* Page navigation pill tabs */
.nav-container {{
    display: flex;
    gap: 8px;
    margin-bottom: 0.8rem;
    border-bottom: 1px solid var(--border);
    padding-bottom: 0.5rem;
}}
.nav-tab {{
    padding: 0.35rem 0.8rem;
    font-size: 0.78rem;
    font-weight: 600;
    border-radius: 6px;
    text-decoration: none;
    transition: all 0.2s ease;
    border: 1px solid var(--border);
}}
.nav-tab-active {{
    background-color: var(--accent);
    color: #ffffff !important;
    border-color: var(--accent);
}}
.nav-tab-inactive {{
    background-color: var(--card);
    color: var(--text-muted) !important;
}}
.nav-tab-inactive:hover {{
    background-color: var(--card-hover);
    color: var(--text) !important;
}}

/* Profile themed grid layout */
.profile-grid {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1.25rem;
    margin-bottom: 1.25rem;
}}
@media (max-width: 1024px) {{
    .profile-grid {{ grid-template-columns: repeat(2, 1fr); }}
}}
@media (max-width: 640px) {{
    .profile-grid {{ grid-template-columns: 1fr; }}
}}

.profile-card {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1rem 1.1rem;
    box-shadow: var(--shadow);
    display: flex;
    flex-direction: column;
}}
.profile-card-header {{
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 0.82rem;
    font-weight: 700;
    color: var(--text);
    border-bottom: 1px solid var(--border-subtle);
    padding-bottom: 0.5rem;
    margin-bottom: 0.5rem;
}}
.profile-card-header-icon {{
    font-size: 0.95rem;
}}
.profile-ind-list {{
    max-height: 250px;
    overflow-y: auto;
    padding-right: 4px;
}}
/* Scrollbar styling for list */
.profile-ind-list::-webkit-scrollbar {{
    width: 4px;
}}
.profile-ind-list::-webkit-scrollbar-track {{
    background: transparent;
}}
.profile-ind-list::-webkit-scrollbar-thumb {{
    background: var(--border);
    border-radius: 4px;
}}

.profile-ind-item {{
    display: flex;
    flex-direction: column;
    padding: 0.5rem 0.6rem;
    border-radius: 6px;
    margin-bottom: 4px;
    border: 1px solid transparent;
    text-decoration: none !important;
    transition: all 0.15s ease;
}}
.profile-ind-item:hover {{
    background-color: var(--card-hover);
}}
.profile-ind-item-selected {{
    background-color: { 'rgba(37,99,235,0.08)' if not IS_DARK else 'rgba(37,99,235,0.15)' };
    border-color: var(--accent);
}}
.profile-ind-name-row {{
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
}}
.profile-ind-name {{
    font-size: 0.76rem;
    font-weight: 600;
    color: var(--text);
    max-width: 70%;
    line-height: 1.25;
}}
.profile-ind-val {{
    font-size: 0.8rem;
    font-weight: 700;
    color: var(--text);
}}
.profile-ind-sub-row {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 3px;
    font-size: 0.65rem;
    color: var(--text-dim);
}}
.profile-ind-devs {{
    display: flex;
    gap: 6px;
}}

/* Mini KPIs row */
.profile-kpis-grid {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1rem;
    margin-bottom: 1rem;
}}
.profile-kpi-card {{
    background: var(--bg-subtle);
    border: 1px solid var(--border-subtle);
    border-radius: 8px;
    padding: 0.6rem 0.9rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}}
.profile-kpi-lbl {{
    font-size: 0.68rem;
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.02em;
}}
.profile-kpi-val {{
    font-size: 1.15rem;
    font-weight: 700;
    color: var(--text);
}}
</style>
"""
st.markdown(theme_css, unsafe_allow_html=True)

# 4. Data Loading and Normalization (Cached)
@st.cache_data
def load_data():
    db_path = "sns_indicadores.db"
    conn = sqlite3.connect(db_path)
    
    # Load ULS metadata
    df_uls = pd.read_sql("SELECT * FROM uls_metadata", conn)
    
    # Load Indicators metadata
    df_ids = pd.read_sql("SELECT * FROM ind_metadata", conn)
    
    # Load periods
    df_periods = pd.read_sql("SELECT DISTINCT periodo FROM indicadores_sns ORDER BY periodo", conn)
    periods = [p for p in df_periods['periodo'].dropna().tolist() if p != 'None' and p != 'nan']
    
    conn.close()
    return df_uls, df_ids, periods

# Heatmap row metadata configuration
heatmap_indicators = [
    {"name": "Cons. Hospitalares", "id": "CH_F000", "type": "Mensal", "col": "no_de_consultas_medicas_total", "is_pct": False, "sentido": "+"},
    {"name": "1ªs Consultas", "id": "CH_F020", "type": "Mensal", "col": "no_de_primeiras_consultas", "is_pct": False, "sentido": "+"},
    {"name": "Acesso Cons. CSP", "id": "CSP_A030", "type": "Stock", "col": "taxa_de_utilizacao_global_de_consultas_medicas_1_ano", "is_pct": True, "sentido": "+"},
    {"name": "Total Urgência (Link)", "id": "URG_B000_L", "type": "Mensal", "col": "total_urgencias", "is_pct": False, "sentido": "-"},
    {"name": "Doentes Saídos", "id": "CH_G010", "type": "Mensal", "col": "doentes_saidos", "is_pct": False, "sentido": "+"},
    {"name": "Demora Média", "id": "CH_C000", "type": "Stock", "col": "demora_media_antes_da_cirurgia", "is_pct": False, "sentido": "-"},
    {"name": "% 1ªs Cons. Tempo Adeq.", "id": "CH_A000", "type": "Stock", "col": "1as_consultas_realizadas_em_tempo_adequado", "is_pct": True, "sentido": "+"},
    {"name": "Cir. Programadas", "id": "CH_D020", "type": "Mensal", "col": "no_intervencoes_cirurgicas_programadas", "is_pct": False, "sentido": "+"},
    {"name": "Nº Partos", "id": "CH_K010", "type": "Mensal", "col": "no_de_partos", "is_pct": False, "sentido": "+"},
    {"name": "% Cesarianas", "id": "CH_K000", "type": "Stock", "col": "no_de_cesarianas", "is_pct": True, "sentido": "-", "ratio_cols": ("no_de_cesarianas", "no_de_partos")},
    {"name": "Total RH", "id": "ULS_F110", "type": "Stock", "col": "total_geral", "is_pct": False, "sentido": "+"},
    {"name": "% Utentes c/ MdF", "id": "CSP_G030", "type": "Stock", "col": "total_utentes_com_mdf_atribuido0", "is_pct": True, "sentido": "+"},
    {"name": "Consultas CSP", "id": "CSP_B_TOT", "type": "Mensal", "col": None, "is_pct": False, "sentido": "+", "sum_cols": ["no_de_consultas_medicas_presencias_qt", "no_de_consultas_medicas_nao_presenciais_ou_inespecificas_qt", "no_de_consultas_medicas_ao_domicilio_qt"]},
    {"name": "Urgências", "id": "URG_B000", "type": "Mensal", "col": "total_urgencias", "is_pct": False, "sentido": "-"},
    {"name": "Dívida Vencida (M€)", "id": "ULS_B010", "type": "Stock", "col": "divida_vencida_fornecedores_externos", "is_pct": False, "sentido": "-"},
    {"name": "% Frat. Anca 48h", "id": "CH_J000", "type": "Stock", "col": "fraturas_anca_com_cirurgia_realizada_nas_primeiras_48_horas", "is_pct": True, "sentido": "+"},
    {"name": "% LIC TMRG", "id": "CH_A010", "type": "Stock", "col": "no_primeiras_ce_prestadas_dentro_do_tmrg", "is_pct": True, "sentido": "+", "ratio_cols": ("no_primeiras_ce_prestadas_dentro_do_tmrg", "no_primeiras_ce_realizadas_com_registo_no_cth")},
    {"name": "Cont. Enfermagem CSP", "id": "CSP_C_TOT", "type": "Mensal", "col": None, "is_pct": False, "sentido": "+", "sum_cols": ["no_de_contactos_de_enfermagem_presenciais_qt", "no_de_contactos_de_enfermagem_nao_presenciais_qt"]},
    {"name": "EBITDA (M€)", "id": "ULS_A000", "type": "Stock", "col": "ebitda", "is_pct": False, "sentido": "+"},
    {"name": "% Gastos TE/Suplementares", "id": "ULS_C020", "type": "Stock", "col": "gastos_com_te_e_suplementos_no_total_gastos_com_pessoal", "is_pct": True, "sentido": "-"},
    {"name": "Trab. por Vinculação", "id": "ULS_G_TOT", "type": "Stock", "col": "no_trabalhadores", "is_pct": False, "sentido": "+"},
    {"name": "Dias de Ausência", "id": "ULS_H_TOT", "type": "Mensal", "col": "valor", "is_pct": False, "sentido": "-", "source_filter": "RH - Dias de Ausencia por Motivo"},
    {"name": "Horas Trab. Extra", "id": "ULS_E_TOT", "type": "Mensal", "col": None, "is_pct": False, "sentido": "-", "sum_cols": ["trabalho_extraordinario_diurno", "trabalho_extraordinario_nocturno", "trabalho_em_dias_de_descanso_semanal_complementar", "trabalho_em_dias_de_descanso_semanal_obrigatorio"]},
    {"name": "Ausências Formação", "id": "ULS_D_TOT", "type": "Mensal", "col": None, "is_pct": False, "sentido": "+", "sum_cols": ["pessoal_de_enfermagem", "pessoal_em_formacao_pre_carreira", "pessoal_medico"]},
    {"name": "Taxa Ocup. Intern.", "id": "CH_H020", "type": "Stock", "col": "taxa_anual_de_ocupacao_em_internamento", "is_pct": True, "sentido": "+"},
    {"name": "Demora Pré-Cirurgia", "id": "CH_C_RAT", "type": "Stock", "col": "no_de_dias_ate_cirurgia_em_episodios_de_gdh_cirurgicos_programados", "is_pct": False, "sentido": "-", "ratio_cols": ("no_de_dias_ate_cirurgia_em_episodios_de_gdh_cirurgicos_programados", "no_de_episodios_em_gdh_cirurgicos_de_internamento_programados_com_exclusoes")},
    {"name": "Hemodiálise", "id": "IRC_A000", "type": "Stock", "col": "utentes_em_hemodialise", "is_pct": False, "sentido": "-"},
    {"name": "Cir. Ambulatório", "id": "CH_D010", "type": "Mensal", "col": "no_intervencoes_cirurgicas_de_ambulatorio", "is_pct": False, "sentido": "+"},
    {"name": "Mortalidade AVC", "id": "CH_I_TOT", "type": "Stock", "col": None, "is_pct": True, "sentido": "-", "sum_cols": ["mortalidade_avc_hemorragico_30_dias", "mortalidade_avc_isquemico_30_dias"]},
    {"name": "Controlo Diabetes", "id": "CSP_D020", "type": "Stock", "col": "proporcao_dm_c_ultima_hgba1c_8_0", "is_pct": True, "sentido": "+"},
    {"name": "Controlo Hipertensão", "id": "CSP_E010", "type": "Stock", "col": "proporcao_hipertensos_65_a_com_pa_150_90", "is_pct": True, "sentido": "+"},
    {"name": "Vig. Recém-Nascidos", "id": "CSP_F020", "type": "Stock", "col": "proporcao_rn_c_cons_med_vigil_ate_28_dias_vida", "is_pct": True, "sentido": "+"},
    {"name": "Consumo Antibióticos", "id": "CH_L_RAT", "type": "Stock", "col": "unidades_antibioticos", "is_pct": True, "sentido": "-", "ratio_cols": ("unidades_antibioticos", "unidades_totais")},
    {"name": "Mortalidade Hosp.", "id": "MOR_A000", "type": "Stock", "col": "taxa_mortalidade", "is_pct": True, "sentido": "-"}
]

thematic_categories = {
    "Acesso": {
        "title": "Acesso", "icon": "📁",
        "indicators": ["% 1ªs Cons. Tempo Adeq.", "% LIC TMRG", "Taxa Ocup. Intern.", "Acesso Cons. CSP", "Consultas CSP", "Cont. Enfermagem CSP", "Cons. Hospitalares", "1ªs Consultas", "Urgências", "Total Urgência (Link)", "Hemodiálise"]
    },
    "Qualidade": {
        "title": "Qualidade", "icon": "⭐",
        "indicators": ["Mortalidade AVC", "% Frat. Anca 48h", "% Cesarianas", "Consumo Antibióticos", "Mortalidade Hosp.", "Controlo Diabetes", "Controlo Hipertensão", "Vig. Recém-Nascidos"]
    },
    "Sustentabilidade": {
        "title": "Sustentabilidade e Eficiência", "icon": "📊",
        "indicators": ["Demora Pré-Cirurgia", "Cir. Ambulatório", "Demora Média", "EBITDA (M€)", "Dívida Vencida (M€)", "% Gastos TE/Suplementares", "Dias de Ausência"]
    },
    "Operacional": {
        "title": "Operacional e Recursos", "icon": "⚙️",
        "indicators": ["Cir. Programadas", "Doentes Saídos", "Nº Partos", "% Utentes c/ MdF", "Total RH", "Trab. por Vinculação", "Horas Trab. Extra", "Ausências Formação"]
    }
}

# Map indicators globally for scope visibility across all page conditions
ind_pct_map = {ind["name"]: ind["is_pct"] for ind in heatmap_indicators}
ind_sentido_map = {ind["name"]: ind["sentido"] for ind in heatmap_indicators}

# Load data once
df_uls, df_ids, periods = load_data()

# Dynamically detect the most recent period that has substantial data (>= 2000 records)
def detect_default_period(periods):
    try:
        conn = sqlite3.connect("sns_indicadores.db")
        for p in periods[::-1]:
            res = conn.execute("SELECT COUNT(*) FROM indicadores_sns WHERE periodo = ?", (p,)).fetchone()[0]
            if res >= 2000:
                conn.close()
                return p
        conn.close()
    except:
        pass
    return periods[-1] if periods else None

default_period = detect_default_period(periods)

# 5. Core Heatmap Calculation Engine
@st.cache_data
def calculate_metrics(df_uls, df_ids, start_month, end_month):
    # Get all distinct periods in range from db
    db_path = "sns_indicadores.db"
    conn = sqlite3.connect(db_path)
    df_p = pd.read_sql(
        "SELECT DISTINCT periodo FROM indicadores_sns WHERE periodo >= ? AND periodo <= ? ORDER BY periodo",
        conn, params=(start_month, end_month)
    )
    conn.close()
    
    periods_current = df_p['periodo'].dropna().tolist()
    if not periods_current:
        periods_current = [end_month]
        
    periods_homologous = []
    for p in periods_current:
        try:
            y = int(p[:4]) - 1
            periods_homologous.append(f"{y}{p[4:]}")
        except:
            pass
            
    periods_2024 = [f"2024{p[4:]}" for p in periods_current]
    
    latest_month_curr = end_month
    try:
        latest_month_hom = f"{int(end_month[:4])-1}{end_month[4:]}"
    except:
        latest_month_hom = end_month
    latest_month_2024 = f"2024{end_month[4:]}"
    
    # Select only required columns from SQLite to avoid loading 154 columns into memory
    cols_to_query = [
        "periodo", "mapped_uls", "_fonte",
        "no_de_consultas_medicas_total", "no_de_primeiras_consultas", "taxa_de_utilizacao_global_de_consultas_medicas_1_ano",
        "total_urgencias", "doentes_saidos", "demora_media_antes_da_cirurgia", "no_primeiras_ce_prestadas_dentro_do_tmrg",
        "no_primeiras_ce_realizadas_com_registo_no_cth", "1as_consultas_realizadas_em_tempo_adequado",
        "fraturas_anca_com_cirurgia_realizada_nas_primeiras_48_horas", "no_de_partos", "no_de_cesarianas", "no_intervencoes_cirurgicas_programadas",
        "divida_vencida_fornecedores_externos", "total_geral", "total_utentes_com_mdf_atribuido0",
        "no_de_consultas_medicas_presencias_qt", "no_de_consultas_medicas_nao_presenciais_ou_inespecificas_qt",
        "no_de_consultas_medicas_ao_domicilio_qt", "no_de_contactos_de_enfermagem_presenciais_qt",
        "no_de_contactos_de_enfermagem_nao_presenciais_qt", "ebitda",
        "gastos_com_te_e_suplementos_no_total_gastos_com_pessoal", "no_trabalhadores", "valor",
        "trabalho_extraordinario_diurno", "trabalho_extraordinario_nocturno",
        "trabalho_em_dias_de_descanso_semanal_complementar", "trabalho_em_dias_de_descanso_semanal_obrigatorio",
        "pessoal_de_enfermagem", "pessoal_em_formacao_pre_carreira", "pessoal_medico",
        "taxa_anual_de_ocupacao_em_internamento", "no_de_dias_ate_cirurgia_em_episodios_de_gdh_cirurgicos_programados",
        "no_de_episodios_em_gdh_cirurgicos_de_internamento_programados_com_exclusoes", "utentes_em_hemodialise",
        "no_intervencoes_cirurgicas_de_ambulatorio", "mortalidade_avc_hemorragico_30_dias", "mortalidade_avc_isquemico_30_dias",
        "proporcao_dm_c_ultima_hgba1c_8_0", "proporcao_hipertensos_65_a_com_pa_150_90",
        "proporcao_rn_c_cons_med_vigil_ate_28_dias_vida", "unidades_antibioticos", "unidades_totais", "taxa_mortalidade"
    ]
    cols_str = ", ".join(f'"{c}"' for c in cols_to_query)
    
    db_path = "sns_indicadores.db"
    conn = sqlite3.connect(db_path)
    all_periods = sorted(list(set(periods_current + periods_homologous + periods_2024)))
    placeholders = ",".join("?" for _ in all_periods)
    query = f"SELECT {cols_str} FROM indicadores_sns WHERE periodo IN ({placeholders})"
    df_raw = pd.read_sql(query, conn, params=all_periods)
    conn.close()
    
    uls_names = sorted(df_uls['ULS'].dropna().unique().tolist())
    
    # Store calculations
    output_var_hom = pd.DataFrame(index=[ind["name"] for ind in heatmap_indicators], columns=uls_names)
    output_var_hom_raw = pd.DataFrame(index=[ind["name"] for ind in heatmap_indicators], columns=uls_names)
    output_base_idx = pd.DataFrame(index=[ind["name"] for ind in heatmap_indicators], columns=uls_names)
    output_grupo_pos = pd.DataFrame(index=[ind["name"] for ind in heatmap_indicators], columns=uls_names)
    
    # Filter CSV by relevant periods
    df_curr_all = df_raw[df_raw['periodo'].isin(periods_current)]
    df_hom_all = df_raw[df_raw['periodo'].isin(periods_homologous)]
    df_2024_all = df_raw[df_raw['periodo'].isin(periods_2024)]
    
    # Pre-group subsets by ULS to gain a 25x speedup in iteration loops
    curr_by_uls = {u: grp for u, grp in df_curr_all.groupby('mapped_uls')}
    hom_by_uls = {u: grp for u, grp in df_hom_all.groupby('mapped_uls')}
    base_by_uls = {u: grp for u, grp in df_2024_all.groupby('mapped_uls')}
    
    for ind in heatmap_indicators:
        name = ind["name"]
        col = ind["col"]
        ind_type = ind["type"]
        is_pct = ind["is_pct"]
        sentido = ind["sentido"]
        ratio_cols = ind.get("ratio_cols")
        sum_cols = ind.get("sum_cols")
        src_filter = ind.get("source_filter")
        
        # Pull values per ULS
        for uls in uls_names:
            sub_curr = curr_by_uls.get(uls, pd.DataFrame())
            sub_hom = hom_by_uls.get(uls, pd.DataFrame())
            sub_2024 = base_by_uls.get(uls, pd.DataFrame())
            
            def get_val(subset, periods, latest_month):
                if subset.empty:
                    return np.nan
                if src_filter:
                    if '_fonte' in subset.columns:
                        subset = subset[subset['_fonte'] == src_filter]
                    else:
                        return np.nan
                if subset.empty:
                    return np.nan
                if ind_type == "Mensal":
                    # Sum values over year YTD, ignoring NaNs
                    if ratio_cols:
                        valid_sub = subset[subset[ratio_cols[0]].notna() & subset[ratio_cols[1]].notna()]
                        num = valid_sub[ratio_cols[0]].sum()
                        den = valid_sub[ratio_cols[1]].sum()
                        return (num / den * 100) if den > 0 else np.nan
                    elif sum_cols:
                        return subset[sum_cols].sum(skipna=True).sum()
                    else:
                        return subset[col].sum(skipna=True)
                else: # Stock / Acumulado
                    # Take value of the target month only
                    row_month = subset[subset['periodo'] == latest_month]
                    if row_month.empty:
                        return np.nan
                    if ratio_cols:
                        valid_rows = row_month[row_month[ratio_cols[0]].notna() & row_month[ratio_cols[1]].notna()]
                        if not valid_rows.empty:
                            num = valid_rows[ratio_cols[0]].values[0]
                            den = valid_rows[ratio_cols[1]].values[0]
                            return (num / den * 100) if den > 0 else np.nan
                        return np.nan
                    elif sum_cols:
                        valid_rows = row_month[row_month[sum_cols].notna().any(axis=1)]
                        if not valid_rows.empty:
                            return valid_rows[sum_cols].sum(axis=1).values[0]
                        return np.nan
                    else:
                        valid_rows = row_month[row_month[col].notna()]
                        if not valid_rows.empty:
                            return valid_rows[col].values[0]
                        return np.nan
            
            val_curr = get_val(sub_curr, periods_current, latest_month_curr)
            val_hom = get_val(sub_hom, periods_homologous, latest_month_hom)
            val_2024 = get_val(sub_2024, periods_2024, latest_month_2024)
            
            # --- 1. Homologous Variation ---
            if pd.isna(val_curr) or pd.isna(val_hom) or val_hom == 0 or val_curr == 0:
                output_var_hom.at[name, uls] = np.nan
            else:
                if is_pct:
                    # Percentage Point (pp) difference
                    diff = val_curr - val_hom
                    output_var_hom.at[name, uls] = diff if sentido == '+' else -diff
                else:
                    # Relative variation (%)
                    if sentido == '+':
                        output_var_hom.at[name, uls] = (val_curr / val_hom - 1) * 100
                    else:
                        output_var_hom.at[name, uls] = (val_hom / val_curr - 1) * 100
            
            # Keep raw actual value
            output_var_hom_raw.at[name, uls] = val_curr
            
            # --- 2. Base Index 2024 ---
            if pd.isna(val_curr) or pd.isna(val_2024) or val_2024 == 0 or val_curr == 0:
                output_base_idx.at[name, uls] = np.nan
            else:
                if sentido == '-':
                    output_base_idx.at[name, uls] = (val_2024 / val_curr) * 100
                else:
                    output_base_idx.at[name, uls] = (val_curr / val_2024) * 100
                    
    # --- 3. Position relative to Group ---
    # Map groups
    grp_map = dict(zip(df_uls['ULS'], df_uls['Grupo']))
    for ind in heatmap_indicators:
        name = ind["name"]
        sentido = ind["sentido"]
        for uls in uls_names:
            uls_grp = grp_map.get(uls)
            if not uls_grp:
                continue
            
            # Get peer ULS in the same financing group
            peers = [u for u, g in grp_map.items() if g == uls_grp]
            peer_vals = [output_var_hom_raw.at[name, p] for p in peers if p in output_var_hom_raw.columns and pd.notna(output_var_hom_raw.at[name, p])]
            
            val_uls = output_var_hom_raw.at[name, uls]
            if len(peer_vals) > 0 and pd.notna(val_uls) and val_uls > 0:
                avg_grp = np.mean(peer_vals)
                if avg_grp > 0:
                    if sentido == '+':
                        output_grupo_pos.at[name, uls] = (val_uls / avg_grp) * 100
                    else:
                        output_grupo_pos.at[name, uls] = (avg_grp / val_uls) * 100
                else:
                    output_grupo_pos.at[name, uls] = np.nan
            else:
                output_grupo_pos.at[name, uls] = np.nan
                
    return output_var_hom, output_base_idx, output_grupo_pos, output_var_hom_raw

# 6. Global Top Navigation Header
all_periods = sorted([str(p) for p in periods if str(p).strip().lower() != 'nan'])
reversed_periods = all_periods[::-1]

# Top Nav Container
nav_html = f"""
<div class="nav-container">
    <a href="?page=matriz" class="nav-tab {"nav-tab-active" if page == "matriz" else "nav-tab-inactive"}">← Matriz Operacional</a>
    <a href="?page=perfil" class="nav-tab {"nav-tab-active" if page == "perfil" else "nav-tab-inactive"}">Perfil Institucional</a>
</div>
"""
st.markdown(nav_html, unsafe_allow_html=True)

# ----------------------------------------------------
# PAGE 1: MATRIZ OPERACIONAL (HEATMAP)
# ----------------------------------------------------
if page == "matriz":
    col_title, col_de, col_ate, col_persp, col_dim, col_group = st.columns([1.3, 0.5, 0.5, 1.0, 0.8, 0.8])
    
    with col_title:
        st.markdown("<h3 style='margin: 0.3rem 0; font-size: 1.15rem; font-weight: 700; color: var(--text); line-height: 1.2;'>ULS Regionais<br><span style='font-size: 0.78rem; font-weight: 500; color: var(--text-muted);'>Relatório de Desempenho</span></h3>", unsafe_allow_html=True)
    
    with col_ate:
        ate_index = reversed_periods.index(default_period) if default_period in reversed_periods else 0
        if _url_end_month and _url_end_month in reversed_periods:
            ate_index = reversed_periods.index(_url_end_month)
        end_month = st.selectbox("Mês Final (Até):", options=reversed_periods, index=ate_index, key="end_month_sel")
        
    end_year = end_month[:4]
    default_start = f"{end_year}-01"
    if default_start not in all_periods:
        default_start = all_periods[0]
        
    start_options = [p for p in all_periods if p <= end_month]
    try:
        start_index = start_options.index(default_start)
    except ValueError:
        start_index = 0
    if _url_start_month and _url_start_month in start_options:
        start_index = start_options.index(_url_start_month)
        
    with col_de:
        start_month = st.selectbox("Mês Inicial (De):", options=start_options, index=start_index, key="start_month_sel")
        
    persp_options = [
        "Variação Homóloga (vs. Período Homólogo)",
        "Índice Base 2024 (2024 = 100)",
        "Posição Relativa face à Média do Grupo"
    ]
    persp_index = 0
    if _url_persp_idx is not None:
        try:
            persp_index = int(_url_persp_idx)
        except:
            persp_index = 0
            
    with col_persp:
        perspective = st.selectbox("Perspetiva de Análise:", options=persp_options, index=persp_index, key="persp_sel")
        
    with col_dim:
        st.markdown("<label style='font-size: 0.8rem; font-weight: 600; color: var(--text-dim); display: block; margin-bottom: 4px;'>Dimensões do Indicador:</label>", unsafe_allow_html=True)
        with st.popover("Selecionar Dimensões", use_container_width=True):
            available_dims = list(thematic_categories.keys())
            
            default_dims = ["Acesso"]
            if _url_dims:
                parsed_dims = [d for d in _url_dims.split(",") if d in available_dims]
                if parsed_dims:
                    default_dims = parsed_dims
            
            dim_checkboxes = {}
            for dim in available_dims:
                dim_checkboxes[dim] = st.checkbox(dim, value=(dim in default_dims), key=f"chk_dim_{dim}")
            
            dim_filter = [dim for dim, val in dim_checkboxes.items() if val]
            if not dim_filter:
                dim_filter = ["Acesso"]
        
    with col_group:
        st.markdown("<label style='font-size: 0.8rem; font-weight: 600; color: var(--text-dim); display: block; margin-bottom: 4px;'>Grupo de Financiamento:</label>", unsafe_allow_html=True)
        with st.popover("Selecionar Grupos", use_container_width=True):
            available_grps = sorted(df_uls['Grupo'].dropna().unique().tolist())
            
            default_grps = ["C"] if "C" in available_grps else [available_grps[0]]
            if _url_groups:
                parsed_grps = [g for g in _url_groups.split(",") if g in available_grps]
                if parsed_grps:
                    default_grps = parsed_grps
            
            grp_checkboxes = {}
            for grp in available_grps:
                grp_checkboxes[grp] = st.checkbox(f"Grupo {grp}", value=(grp in default_grps), key=f"chk_grp_{grp}")
            
            group_filter = [grp for grp, val in grp_checkboxes.items() if val]
            if not group_filter:
                group_filter = available_grps
        
    # Calculations
    df_var_hom, df_base_idx, df_grupo_pos, df_raw_vals = calculate_metrics(df_uls, df_ids, start_month, end_month)
    df_uls_filtered = df_uls[df_uls['Grupo'].isin(group_filter)]
    uls_to_show = sorted(df_uls_filtered['ULS'].unique().tolist())
    
    if "Variação Homóloga" in perspective:
        base_df = df_var_hom.copy()
        metric_title = "Variação Homóloga (%) ou Ponto Percentual (pp)"
        val_suffix = "%"
    elif "Índice Base 2024" in perspective:
        base_df = df_base_idx.copy()
        metric_title = "Índice Base 2024 (100 = Alinhado)"
        val_suffix = ""
    else:
        base_df = df_grupo_pos.copy()
        metric_title = "Posição face ao Grupo (100 = Média do Grupo)"
        val_suffix = ""
        
    val_sns = base_df.mean(axis=1)
    plot_df = base_df[uls_to_show].copy()
    plot_df.insert(0, "SNS", val_sns)
    if len(group_filter) == 1:
        val_grp = plot_df.drop(columns=["SNS"]).mean(axis=1)
        plot_df.insert(1, "Média Grupo", val_grp)
        
    raw_sns = df_raw_vals.mean(axis=1)
    raw_plot_vals = df_raw_vals[uls_to_show].copy()
    raw_plot_vals.insert(0, "SNS", raw_sns)
    if len(group_filter) == 1:
        raw_grp = raw_plot_vals.drop(columns=["SNS"]).mean(axis=1)
        raw_plot_vals.insert(1, "Média Grupo", raw_grp)
    df_raw_vals_plot = raw_plot_vals
    
    # Sort columns
    if st.session_state.sort_ind and st.session_state.sort_ind in plot_df.index:
        summary_cols = ["SNS"]
        if "Média Grupo" in plot_df.columns:
            summary_cols.append("Média Grupo")
        uls_cols = [c for c in plot_df.columns if c not in summary_cols]
        row_vals = plot_df.loc[st.session_state.sort_ind, uls_cols]
        if st.session_state.sort_state == 1:
            sorted_uls = row_vals.sort_values(ascending=True).index.tolist()
        elif st.session_state.sort_state == 2:
            sorted_uls = row_vals.sort_values(ascending=False).index.tolist()
        else:
            sorted_uls = uls_cols
        plot_df = plot_df[summary_cols + sorted_uls]
        df_raw_vals_plot = df_raw_vals_plot[summary_cols + sorted_uls]
        
    new_index = []
    for ind_name in plot_df.index:
        if st.session_state.sort_ind == ind_name:
            if st.session_state.sort_state == 1:
                new_index.append(f"▲ {ind_name}")
            elif st.session_state.sort_state == 2:
                new_index.append(f"▼ {ind_name}")
            else:
                new_index.append(ind_name)
        else:
            new_index.append(ind_name)
    plot_df.index = new_index
    
    # Helper to interpolate color based on performance values
    def get_color_for_value(val, sentido, perspective):
        if pd.isna(val):
            return "transparent", "#71717a"
        if "Variação" in perspective:
            norm_val = val / 15.0
            norm_val = max(min(norm_val, 1.0), -1.0)
            if sentido == "-":
                norm_val = -norm_val
        elif "Índice Base" in perspective:
            norm_val = (val - 100) / 20
            norm_val = max(min(norm_val, 1.0), -1.0)
            if sentido == "-":
                norm_val = -norm_val
        else:
            norm_val = (val - 100) / 15
            norm_val = max(min(norm_val, 1.0), -1.0)
            if sentido == "-":
                norm_val = -norm_val
        if norm_val < 0:
            ratio = abs(norm_val)
            r = int(244 - (244 - 220) * ratio)
            g = int(244 - (244 - 38) * ratio)
            b = int(245 - (245 - 38) * ratio)
            text_color = "white" if ratio > 0.45 else ("#000000" if not IS_DARK else "#ffffff")
        else:
            ratio = norm_val
            r = int(244 - (244 - 22) * ratio)
            g = int(244 - (244 - 163) * ratio)
            b = int(245 - (245 - 74) * ratio)
            text_color = "white" if ratio > 0.45 else ("#000000" if not IS_DARK else "#ffffff")
        return f"rgb({r},{g},{b})", text_color
        
    # Global maps used instead of local definitions
    
    html_table = []
    html_table.append(f"""
    <div style="overflow-x: auto; overflow-y: auto; max-height: 82vh; width: 100%; padding-bottom: 10px;">
    <table class="heatmap-table">
    <thead>
    <tr style="vertical-align: bottom;">
        <th style="text-align: right; font-size: 10px; padding-bottom: 8px; padding-right: 8px; border-right: 2px solid {'#3f3f46' if IS_DARK else '#e4e4e7'}; position: sticky; top: 0; left: 0; z-index: 12; background-color: {'#09090b' if IS_DARK else '#ffffff'}; font-weight: 700;">Indicador</th>
    """)
    for col_name in plot_df.columns:
        short_col = col_name.replace("ULS ", "")
        html_table.append(f'<th><div class="hdr-label">{short_col}</div></th>')
    html_table.append('</tr></thead><tbody>')
    
    # Map clean indicator name to actual index name in plot_df
    idx_map = {}
    for idx_name in plot_df.index:
        clean = idx_name.replace("▲ ", "").replace("▼ ", "").strip()
        idx_map[clean] = idx_name
        
    rendered_indices = set()
    
    # Render grouped indicators
    for theme_key, theme_data in thematic_categories.items():
        if theme_key not in dim_filter:
            continue
        # Filter indicators in this theme that are present in the dataset
        theme_inds = [ind for ind in theme_data["indicators"] if ind in idx_map]
        if not theme_inds:
            continue
            
        # Category separator row
        html_table.append(f"""
        <tr style="height: 26px;">
            <td class="row-lbl" style="position: sticky; left: 0; z-index: 5; background-color: {'#18181b' if IS_DARK else '#f4f4f5'}; border-right: 2px solid {'#3f3f46' if IS_DARK else '#e4e4e7'}; font-weight: 800; text-align: left; font-size: 9.5px; color: var(--accent); padding-left: 8px;">
                {theme_data["icon"]} {theme_data["title"]}
            </td>
            <td colspan="{len(plot_df.columns)}" style="background-color: {'#18181b' if IS_DARK else '#f4f4f5'}; border-bottom: 1px solid var(--border);"></td>
        </tr>
        """)
        
        for clean_ind in theme_inds:
            plot_idx = idx_map[clean_ind]
            rendered_indices.add(plot_idx)
            
            ind_safe = clean_ind.replace(" ", "_").replace("%", "pct").replace("/", "slash")
            persp_idx  = persp_options.index(perspective)
            grps_str   = ",".join(group_filter)
            dims_str   = ",".join(dim_filter)
            filter_params = f"&page=matriz&end={end_month}&start={start_month}&persp={persp_idx}&grps={grps_str}&dims={dims_str}"
            arrow = ""
            color_link = "#ffffff" if IS_DARK else "#000000"
            if st.session_state.sort_ind == clean_ind:
                if st.session_state.sort_state == 1:
                    arrow = "▲ "
                    next_href = f"?sort={ind_safe}&state=2{filter_params}"
                    color_link = "#22c55e"
                elif st.session_state.sort_state == 2:
                    arrow = "▼ "
                    next_href = f"?{filter_params.lstrip('&')}"
                    color_link = "#ef4444"
            else:
                next_href = f"?sort={ind_safe}&state=1{filter_params}"
                
            html_table.append('<tr style="height: 20px;">')
            html_table.append(f"""
            <td class="row-lbl" style="border-right: 2px solid {'#3f3f46' if IS_DARK else '#e4e4e7'}; font-weight: 700;">
                <a href="{next_href}" target="_self" style="color: {color_link}; text-decoration: none; display: block; width: 100%;">
                    {arrow}{clean_ind}
                </a>
            </td>
            """)
            
            is_pct = ind_pct_map.get(clean_ind, False)
            sentido = ind_sentido_map.get(clean_ind, "+")
            
            for col_name in plot_df.columns:
                val = plot_df.at[plot_idx, col_name]
                raw_val = df_raw_vals_plot.at[clean_ind, col_name]
                bg_color, text_color = get_color_for_value(val, sentido, perspective)
                is_pp = ("%" in clean_ind or "Taxa" in clean_ind or "Proporção" in clean_ind or "Percentagem" in clean_ind)
                if pd.isna(val):
                    val_str = "-"
                else:
                    val_format = f"{val:+.1f}" if "Variação" in perspective else f"{val:.1f}"
                    suffix = " pp" if (is_pp and "Variação" in perspective) else val_suffix
                    val_str = f"{val_format}{suffix}"
                if pd.isna(raw_val):
                    raw_str = "Sem dados"
                else:
                    if "Dívida" in clean_ind or "EBITDA" in clean_ind:
                        raw_str = f"{(raw_val/1e6):.2f} M€"
                    elif is_pp:
                        raw_str = f"{raw_val:.1f}%"
                    else:
                        raw_str = f"{raw_val:,.0f}"
                tooltip = f"{col_name} - {clean_ind}\nCalculado: {val_str}\nValor Real: {raw_str}"
                uls_target = col_name
                if col_name in ["SNS", "Média Grupo"]:
                    real_uls_cols = [c for c in plot_df.columns if c not in ["SNS", "Média Grupo"]]
                    uls_target = real_uls_cols[0] if real_uls_cols else sel_uls
                    
                uls_url_safe = uls_target.replace(" ", "_").replace("/", "slash")
                ind_url_safe = clean_ind.replace(" ", "_").replace("%", "pct").replace("/", "slash")
                cell_pmode = "comparacao" if "Média" in perspective or "Grupo" in perspective else "indicadores"
                cell_href = f"?page=perfil&uls={uls_url_safe}&ind={ind_url_safe}&pmode={cell_pmode}&end={end_month}"
                
                cell_link = f'<a href="{cell_href}" target="_self" style="color: {text_color}; text-decoration: none; display: block; width: 100%; height: 100%; line-height: 20px; text-align: center;">{val_str}</a>'
                html_table.append(f'<td title="{tooltip}" style="background-color: {bg_color}; padding: 0;" class="cell">{cell_link}</td>')
            html_table.append('</tr>')
            
    html_table.append('</tbody></table></div>')
    st.html("".join(html_table))

# ----------------------------------------------------
# PAGE 2: PERFIL INSTITUCIONAL (NEW)
# ----------------------------------------------------
else:
    indicator_areas = {
        "Cons. Hospitalares": "Hospitalar", "1ªs Consultas": "Hospitalar", "Acesso Cons. CSP": "Cuidados Primários", "Total Urgência (Link)": "Urgência",
        "Doentes Saídos": "Hospitalar", "Demora Média": "Hospitalar", "% 1ªs Cons. Tempo Adeq.": "Hospitalar", "Cir. Programadas": "Hospitalar",
        "Nº Partos": "Obstetrícia", "% Cesarianas": "Obstetrícia", "Total RH": "Recursos Humanos", "% Utentes c/ MdF": "Cuidados Primários",
        "Consultas CSP": "Cuidados Primários", "Urgências": "Urgência", "Dívida Vencida (M€)": "Financeiro", "% Frat. Anca 48h": "Ortopedia",
        "% LIC TMRG": "Hospitalar", "Cont. Enfermagem CSP": "Cuidados Primários", "EBITDA (M€)": "Financeiro", "% Gastos TE/Suplementares": "Financeiro",
        "Trab. por Vinculação": "Recursos Humanos", "Dias de Ausência": "Recursos Humanos", "Horas Trab. Extra": "Recursos Humanos",
        "Ausências Formação": "Recursos Humanos", "Taxa Ocup. Intern.": "Hospitalar", "Demora Pré-Cirurgia": "Hospitalar", "Hemodiálise": "Nefrologia",
        "Cir. Ambulatório": "Hospitalar", "Mortalidade AVC": "Cardiovascular", "Controlo Diabetes": "Cuidados Primários",
        "Controlo Hipertensão": "Cuidados Primários", "Vig. Recém-Nascidos": "Pediatria", "Consumo Antibióticos": "Infeciologia", "Mortalidade Hosp.": "Geral"
    }

    # Top Controls for Profile Page
    c_uls, c_period, c_pmode = st.columns([1.5, 0.8, 1.2])
    
    uls_list = sorted(df_uls['ULS'].dropna().unique().tolist())
    uls_index = uls_list.index(st.session_state.selected_uls) if st.session_state.selected_uls in uls_list else 0
    
    with c_uls:
        sel_uls = st.selectbox("Selecionar ULS / Instituição:", options=uls_list, index=uls_index, key="sel_uls_box")
    
    with c_pmode:
        sel_pmode = st.selectbox("Modo de Comparação:", options=["Indicadores da ULS", "Comparação do Grupo"], index=0 if st.session_state.profile_mode == "indicadores" else 1, key="sel_pmode_box")
        new_pmode = "indicadores" if "Indicadores" in sel_pmode else "comparacao"
        
    with c_period:
        period_idx = reversed_periods.index(default_period) if default_period in reversed_periods else 0
        if _url_end_month and _url_end_month in reversed_periods:
            period_idx = reversed_periods.index(_url_end_month)
        sel_period = st.selectbox("Mês de Referência:", options=reversed_periods, index=period_idx, key="sel_period_box")

    # Get financing group of selected ULS
    uls_grp = df_uls[df_uls['ULS'] == sel_uls]['Grupo'].dropna().values[0]
    peer_uls = sorted(df_uls[df_uls['Grupo'] == uls_grp]['ULS'].dropna().unique().tolist())
    
    # Run instant calculations for target period only
    df_var_hom_p, df_base_idx_p, df_grupo_pos_p, df_raw_vals_p = calculate_metrics(df_uls, df_ids, sel_period, sel_period)
    
    # Calculate group and national averages for that period
    raw_national_avg = df_raw_vals_p.mean(axis=1)
    raw_group_avg = df_raw_vals_p[peer_uls].mean(axis=1)
    
    # --- TREND MOMENTUM & OUTLIERS CALCULATIONS ---
    # Find recent 3 periods for trend analysis
    p_idx = periods.index(sel_period) if sel_period in periods else len(periods)-1
    recent_3_periods = periods[max(0, p_idx-2):p_idx+1]
    
    # Extract historical column names for query
    all_indicator_cols = []
    for ind in heatmap_indicators:
        if ind.get("col"): all_indicator_cols.append(ind["col"])
        if ind.get("sum_cols"): all_indicator_cols.extend(ind["sum_cols"])
        if ind.get("ratio_cols"): all_indicator_cols.extend(ind["ratio_cols"])
    all_indicator_cols = list(dict.fromkeys(all_indicator_cols))
    cols_fetch_str = ", ".join(f'"{c}"' for c in all_indicator_cols)
    
    db_path = "sns_indicadores.db"
    conn = sqlite3.connect(db_path)
    df_trend_raw = pd.read_sql(
        f"SELECT periodo, _fonte, {cols_fetch_str} FROM indicadores_sns WHERE mapped_uls = ? AND periodo IN ({','.join('?' for _ in recent_3_periods)})",
        conn, params=[sel_uls] + recent_3_periods
    )
    conn.close()
    
    # Calculate 3-month trend badges
    trend_badges = {}
    for ind in heatmap_indicators:
        ind_name = ind["name"]
        src_filter = ind.get("source_filter")
        ind_type = ind["type"]
        ratio_cols = ind.get("ratio_cols")
        sum_cols = ind.get("sum_cols")
        col = ind.get("col")
        sentido = ind["sentido"]
        
        vals_by_p = []
        for p in recent_3_periods:
            df_p = df_trend_raw[df_trend_raw['periodo'] == p]
            if df_p.empty:
                vals_by_p.append(np.nan)
                continue
            if src_filter:
                if '_fonte' in df_p.columns:
                    df_p = df_p[df_p['_fonte'] == src_filter]
                else:
                    df_p = pd.DataFrame()
            if df_p.empty:
                vals_by_p.append(np.nan)
                continue
                
            val = np.nan
            if ind_type == "Mensal":
                if ratio_cols:
                    valid_sub = df_p[df_p[ratio_cols[0]].notna() & df_p[ratio_cols[1]].notna()]
                    num = valid_sub[ratio_cols[0]].sum()
                    den = valid_sub[ratio_cols[1]].sum()
                    val = (num / den * 100) if den > 0 else np.nan
                elif sum_cols:
                    val = df_p[sum_cols].sum(skipna=True).sum()
                else:
                    val = df_p[col].sum(skipna=True)
            else: # Stock / Acumulado
                if ratio_cols:
                    valid_rows = df_p[df_p[ratio_cols[0]].notna() & df_p[ratio_cols[1]].notna()]
                    if not valid_rows.empty:
                        val = (valid_rows[ratio_cols[0]].values[0] / valid_rows[ratio_cols[1]].values[0]) * 100
                elif sum_cols:
                    valid_rows = df_p[df_p[sum_cols].notna().any(axis=1)]
                    if not valid_rows.empty:
                        val = valid_rows[sum_cols].sum(axis=1).values[0]
                else:
                    valid_rows = df_p[df_p[col].notna()]
                    if not valid_rows.empty:
                        val = valid_rows[col].values[0]
            vals_by_p.append(val)
            
        valid_vals = [v for v in vals_by_p if pd.notna(v)]
        if len(valid_vals) >= 2:
            v_old = valid_vals[0]
            v_new = valid_vals[-1]
            diff = v_new - v_old
            if abs(diff) < 1e-4:
                trend_badges[ind_name] = '<span style="color: var(--text-dim); margin-left: 6px; font-weight: 700;" title="Tendência: Estável">→</span>'
            else:
                is_fav = diff >= 0 if sentido == "+" else diff <= 0
                arrow = "▲" if is_fav else "▼"
                color = "var(--green)" if is_fav else "var(--red)"
                trend_badges[ind_name] = f'<span style="color: {color}; margin-left: 6px; font-weight: 700; font-size: 0.72rem;" title="Tendência de 3 meses">{arrow}</span>'
        else:
            trend_badges[ind_name] = '<span style="color: var(--text-dim); margin-left: 6px; font-weight: 700;" title="Tendência: Estável">→</span>'
            
    # Calculate Outliers Diagnostics
    diagnostics = []
    for ind in heatmap_indicators:
        ind_name = ind["name"]
        sentido = ind["sentido"]
        val_raw = df_raw_vals_p.at[ind_name, sel_uls] if ind_name in df_raw_vals_p.index else np.nan
        val_grp = raw_group_avg.get(ind_name, np.nan)
        val_nat = raw_national_avg.get(ind_name, np.nan)
        
        ref_val = val_grp if pd.notna(val_grp) and val_grp > 0 else (val_nat if pd.notna(val_nat) and val_nat > 0 else np.nan)
        if pd.notna(val_raw) and pd.notna(ref_val) and ref_val > 0:
            dev = ((val_raw - ref_val) / ref_val) * 100
            perf_score = dev if sentido == "+" else -dev
            
            is_pct_ind = ind_name in ind_pct_map and ind_pct_map[ind_name]
            is_pp_ind = ("%" in ind_name or "Taxa" in ind_name or "Proporção" in ind_name or "Percentagem" in ind_name)
            if "Dívida" in ind_name or "EBITDA" in ind_name:
                raw_str = f"{(val_raw/1e6):.2f} M€"
            elif is_pct_ind or is_pp_ind:
                raw_str = f"{val_raw:.1f}%"
            else:
                raw_str = f"{val_raw:,.0f}"
                
            diagnostics.append({
                "name": ind_name,
                "dev": dev,
                "score": perf_score,
                "raw_str": raw_str,
                "ref_type": "Grupo" if pd.notna(val_grp) and val_grp > 0 else "Nacional"
            })
            
    best_performers = sorted(diagnostics, key=lambda x: x["score"], reverse=True)[:3]
    worst_performers = sorted(diagnostics, key=lambda x: x["score"], reverse=False)[:3]
    
    # Display header of institutional profile
    st.markdown(f"""
    <div style="background: var(--card); border: 1px solid var(--border); border-radius: var(--radius); padding: 0.8rem 1.2rem; margin-bottom: 1rem; display: flex; justify-content: space-between; align-items: center; box-shadow: var(--shadow);">
        <div>
            <h4 style="margin: 0; font-size: 1.15rem; font-weight: 700;">{sel_uls}</h4>
            <div style="font-size: 0.74rem; color: var(--text-muted); font-weight: 500; margin-top: 2px;">
                Grupo Homogéneo: {uls_grp} | Período: {sel_period}
            </div>
        </div>
        <div style="display: flex; gap: 8px;">
            <span class="badge badge-blue">Grupo {uls_grp}</span>
            <span class="badge badge-neutral">34 Indicadores</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Render Outliers Diagnostic Panel
    outliers_html = []
    outliers_html.append('<div style="display: flex; gap: 16px; margin-bottom: 1.2rem; flex-wrap: wrap; width: 100%;">')
    outliers_html.append(f"""
    <div style="flex: 1; min-width: 280px; background: { 'rgba(34,197,94,0.04)' if not IS_DARK else 'rgba(34,197,94,0.015)' }; border: 1px solid { 'rgba(34,197,94,0.18)' if not IS_DARK else 'rgba(34,197,94,0.08)' }; border-radius: var(--radius); padding: 0.7rem 0.9rem;">
        <div style="color: var(--green); font-weight: 700; font-size: 0.76rem; margin-bottom: 0.4rem; display: flex; align-items: center; gap: 6px;">
            <span>🟢 Destaques Positivos (Top Perf.)</span>
        </div>
        <div style="display: flex; flex-direction: column; gap: 5px;">
    """)
    for item in best_performers:
        sign = "+" if item["dev"] >= 0 else ""
        outliers_html.append(f"""
            <div style="display: flex; justify-content: space-between; font-size: 0.72rem;">
                <span style="color: var(--text); font-weight: 500;">{item["name"]}</span>
                <span style="color: var(--green); font-weight: 700;">{item["raw_str"]} ({sign}{item["dev"]:.1f}% vs {item["ref_type"]})</span>
            </div>
        """)
    if not best_performers:
        outliers_html.append('<div style="font-size: 0.72rem; color: var(--text-dim);">Sem destaques identificados.</div>')
    outliers_html.append('</div></div>')
    
    outliers_html.append(f"""
    <div style="flex: 1; min-width: 280px; background: { 'rgba(239,68,68,0.04)' if not IS_DARK else 'rgba(239,68,68,0.015)' }; border: 1px solid { 'rgba(239,68,68,0.18)' if not IS_DARK else 'rgba(239,68,68,0.08)' }; border-radius: var(--radius); padding: 0.7rem 0.9rem;">
        <div style="color: var(--red); font-weight: 700; font-size: 0.76rem; margin-bottom: 0.4rem; display: flex; align-items: center; gap: 6px;">
            <span>🔴 Pontos Críticos (Alertas)</span>
        </div>
        <div style="display: flex; flex-direction: column; gap: 5px;">
    """)
    for item in worst_performers:
        sign = "+" if item["dev"] >= 0 else ""
        outliers_html.append(f"""
            <div style="display: flex; justify-content: space-between; font-size: 0.72rem;">
                <span style="color: var(--text); font-weight: 500;">{item["name"]}</span>
                <span style="color: var(--red); font-weight: 700;">{item["raw_str"]} ({sign}{item["dev"]:.1f}% vs {item["ref_type"]})</span>
            </div>
        """)
    if not worst_performers:
        outliers_html.append('<div style="font-size: 0.72rem; color: var(--text-dim);">Sem alertas identificados.</div>')
    outliers_html.append('</div></div></div>')
    
    st.html("".join(outliers_html))
    
    # Render the 4 columns grid
    profile_columns_html = []
    profile_columns_html.append('<div class="profile-grid">')
    
    for theme_key, theme_data in thematic_categories.items():
        profile_columns_html.append(f"""
        <div class="profile-card">
            <div class="profile-card-header">
                <span class="profile-card-header-icon">{theme_data["icon"]}</span>
                <span>{theme_data["title"]}</span>
            </div>
            <div class="profile-ind-list">
        """)
        
        for ind_name in theme_data["indicators"]:
            if ind_name not in df_raw_vals_p.index:
                continue
            
            val_raw = df_raw_vals_p.at[ind_name, sel_uls]
            val_grp = raw_group_avg.get(ind_name, np.nan)
            val_nat = raw_national_avg.get(ind_name, np.nan)
            
            # Formatting
            is_pct = ind_name in ind_pct_map and ind_pct_map[ind_name]
            is_pp = ("%" in ind_name or "Taxa" in ind_name or "Proporção" in ind_name or "Percentagem" in ind_name)
            sentido = ind_sentido_map.get(ind_name, "+")
            
            val_color_style = ""
            if pd.isna(val_raw):
                val_str = "-"
            else:
                if new_pmode == "comparacao":
                    if pd.notna(val_grp) and val_grp > 0:
                        dev_val = ((val_raw - val_grp) / val_grp) * 100
                        # Color coding based on whether the deviation is favorable or not
                        is_fav = dev_val >= 0 if sentido == "+" else dev_val <= 0
                        color = "var(--green)" if is_fav else "var(--red)"
                        val_color_style = f' style="color: {color}; font-weight: 700;"'
                        
                        sign = "+" if dev_val >= 0 else ""
                        val_str = f"{sign}{dev_val:.1f}%"
                    else:
                        val_str = "-"
                else:
                    if "Dívida" in ind_name or "EBITDA" in ind_name:
                        val_str = f"{(val_raw/1e6):.1f}M€"
                    elif is_pct or is_pp:
                        val_str = f"{val_raw:.1f}%"
                    else:
                        val_str = f"{val_raw:,.0f}"
                        
            # Compute deviations
            # Dev Group
            if pd.notna(val_raw) and pd.notna(val_grp) and val_grp > 0:
                dev_g = ((val_raw - val_grp) / val_grp) * 100
                if sentido == "-":
                    dev_g = -dev_g
                arrow_g = "▲" if dev_g >= 0 else "▼"
                color_g = "var(--green)" if dev_g >= 0 else "var(--red)"
                dev_g_str = f'<span style="color: {color_g}; font-weight: 700;">G: {arrow_g} {abs(dev_g):.1f}%</span>'
            else:
                dev_g_str = '<span style="color: var(--text-dim);">G: -</span>'
                
            # Dev National
            if pd.notna(val_raw) and pd.notna(val_nat) and val_nat > 0:
                dev_n = ((val_raw - val_nat) / val_nat) * 100
                if sentido == "-":
                    dev_n = -dev_n
                arrow_n = "▲" if dev_n >= 0 else "▼"
                color_n = "var(--green)" if dev_n >= 0 else "var(--red)"
                dev_n_str = f'<span style="color: {color_n}; font-weight: 700;">N: {arrow_n} {abs(dev_n):.1f}%</span>'
            else:
                dev_n_str = '<span style="color: var(--text-dim);">N: -</span>'
                
            is_selected = (st.session_state.selected_ind == ind_name)
            selected_class = "profile-ind-item-selected" if is_selected else ""
            
            ind_url_safe = ind_name.replace(" ", "_").replace("%", "pct").replace("/", "slash")
            uls_url_safe = sel_uls.replace(" ", "_").replace("/", "slash")
            item_href = f"?page=perfil&uls={uls_url_safe}&ind={ind_url_safe}&pmode={new_pmode}&end={sel_period}"
            
            area = indicator_areas.get(ind_name, "Geral")
            trend_badge = trend_badges.get(ind_name, "")
            
            profile_columns_html.append(f"""
            <a href="{item_href}" target="_self" class="profile-ind-item {selected_class}">
                <div class="profile-ind-name-row">
                    <span class="profile-ind-name">{ind_name}</span>
                    <span class="profile-ind-val"{val_color_style}>{val_str}{trend_badge}</span>
                </div>
                <div class="profile-ind-sub-row">
                    <span>Área: {area}</span>
                    <div class="profile-ind-devs">
                        {dev_g_str} {dev_n_str}
                    </div>
                </div>
            </a>
            """)
            
        profile_columns_html.append("""
            </div>
        </div>
        """)
        
    profile_columns_html.append('</div>')
    st.html("".join(profile_columns_html))
    
    # ----------------------------------------------------
    # PROFILE BOTTOM DETAIL & HISTORICAL CHART
    # ----------------------------------------------------
    st.subheader(f"{st.session_state.selected_ind} - Detalhe e Histórico Temporal")
    
    # KPIs calculations
    current_val = df_raw_vals_p.at[st.session_state.selected_ind, sel_uls]
    grp_avg_val = raw_group_avg.get(st.session_state.selected_ind, np.nan)
    nat_avg_val = raw_national_avg.get(st.session_state.selected_ind, np.nan)
    
    sentido = ind_sentido_map.get(st.session_state.selected_ind, "+")
    is_pct = st.session_state.selected_ind in ind_pct_map and ind_pct_map[st.session_state.selected_ind]
    is_pp = ("%" in st.session_state.selected_ind or "Taxa" in st.session_state.selected_ind or "Proporção" in st.session_state.selected_ind or "Percentagem" in st.session_state.selected_ind)
    
    def format_kpi(v):
        if pd.isna(v): return "-"
        if "Dívida" in st.session_state.selected_ind or "EBITDA" in st.session_state.selected_ind:
            return f"{(v/1e6):,.2f} M€"
        elif is_pct or is_pp:
            return f"{v:.1f}%"
        return f"{v:,.0f}"
        
    kpi_uls_str = format_kpi(current_val)
    kpi_grp_str = format_kpi(grp_avg_val)
    kpi_nat_str = format_kpi(nat_avg_val)
    
    # Compute deviations for KPIs
    dev_g_kpi = ""
    if pd.notna(current_val) and pd.notna(grp_avg_val) and grp_avg_val > 0:
        dev_val = ((current_val - grp_avg_val) / grp_avg_val) * 100
        if sentido == "-": dev_val = -dev_val
        color = "var(--green)" if dev_val >= 0 else "var(--red)"
        arrow = "▲" if dev_val >= 0 else "▼"
        dev_g_kpi = f'<span style="color: {color}; font-size: 0.72rem; font-weight: 700; margin-left: 8px;">G: {arrow} {abs(dev_val):.1f}%</span>'
        
    dev_n_kpi = ""
    if pd.notna(current_val) and pd.notna(nat_avg_val) and nat_avg_val > 0:
        dev_val = ((current_val - nat_avg_val) / nat_avg_val) * 100
        if sentido == "-": dev_val = -dev_val
        color = "var(--green)" if dev_val >= 0 else "var(--red)"
        arrow = "▲" if dev_val >= 0 else "▼"
        dev_n_kpi = f'<span style="color: {color}; font-size: 0.72rem; font-weight: 700; margin-left: 8px;">N: {arrow} {abs(dev_val):.1f}%</span>'

    st.markdown(f"""
    <div class="profile-kpis-grid">
        <div class="profile-kpi-card">
            <div>
                <div class="profile-kpi-lbl">ULS - {sel_period}</div>
                <div class="profile-kpi-val">{kpi_uls_str}</div>
            </div>
        </div>
        <div class="profile-kpi-card">
            <div>
                <div class="profile-kpi-lbl">Média Grupo (G)</div>
                <div class="profile-kpi-val">{kpi_grp_str}</div>
            </div>
            <div>{dev_g_kpi}</div>
        </div>
        <div class="profile-kpi-card">
            <div>
                <div class="profile-kpi-lbl">Média Nacional (N)</div>
                <div class="profile-kpi-val">{kpi_nat_str}</div>
            </div>
            <div>{dev_n_kpi}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 4. Generate Plotly line chart comparing ULS vs Group vs SNS over time
    db_path = "sns_indicadores.db"
    conn = sqlite3.connect(db_path)
    
    # Query complete historical raw values for selected indicator
    active_ind_meta = [ind for ind in heatmap_indicators if ind["name"] == st.session_state.selected_ind][0]
    
    # Handle indicators using sum_cols or ratio_cols
    cols_to_fetch = []
    if active_ind_meta.get("col"):
        cols_to_fetch.append(active_ind_meta["col"])
    if active_ind_meta.get("sum_cols"):
        cols_to_fetch.extend(active_ind_meta["sum_cols"])
    if active_ind_meta.get("ratio_cols"):
        cols_to_fetch.extend(active_ind_meta["ratio_cols"])
        
    cols_to_fetch = list(dict.fromkeys(cols_to_fetch))
    cols_fetch_str = ", ".join(f'"{c}"' for c in cols_to_fetch)
    
    # Source matching - direct query database table including _fonte column
    df_hist_raw = pd.read_sql(
        f"SELECT periodo, mapped_uls, _fonte, {cols_fetch_str} FROM indicadores_sns WHERE periodo >= '2024-01' ORDER BY periodo", conn
    )
    conn.close()
    
    # Perform same calculation over time
    historical_periods = sorted(df_hist_raw['periodo'].dropna().unique().tolist())
    
    uls_timeline = []
    grp_timeline = []
    sns_timeline = []
    
    # Pre-calculate mapping keys
    src_filter = active_ind_meta.get("source_filter")
    ind_type = active_ind_meta["type"]
    ratio_cols = active_ind_meta.get("ratio_cols")
    sum_cols = active_ind_meta.get("sum_cols")
    col = active_ind_meta.get("col")
    
    for p in historical_periods:
        df_p_data = df_hist_raw[df_hist_raw['periodo'] == p]
        if df_p_data.empty: continue
        
        # Calculate for each ULS in this period
        p_vals = {}
        for u in uls_list:
            u_df = df_p_data[df_p_data['mapped_uls'] == u]
            if u_df.empty: continue
            
            # Apply source filter if defined
            if src_filter:
                if '_fonte' in u_df.columns:
                    u_df = u_df[u_df['_fonte'] == src_filter]
                else:
                    u_df = pd.DataFrame()
                    
            if u_df.empty:
                p_vals[u] = np.nan
                continue
                
            if ind_type == "Mensal":
                if ratio_cols:
                    valid_sub = u_df[u_df[ratio_cols[0]].notna() & u_df[ratio_cols[1]].notna()]
                    num = valid_sub[ratio_cols[0]].sum()
                    den = valid_sub[ratio_cols[1]].sum()
                    p_vals[u] = (num / den * 100) if den > 0 else np.nan
                elif sum_cols:
                    p_vals[u] = u_df[sum_cols].sum(skipna=True).sum()
                else:
                    p_vals[u] = u_df[col].sum(skipna=True)
            else: # Stock / Acumulado
                # For historical monthly slice, u_df has only rows for period p. We fetch the first valid row values.
                if ratio_cols:
                    valid_rows = u_df[u_df[ratio_cols[0]].notna() & u_df[ratio_cols[1]].notna()]
                    if not valid_rows.empty:
                        num = valid_rows[ratio_cols[0]].values[0]
                        den = valid_rows[ratio_cols[1]].values[0]
                        p_vals[u] = (num / den * 100) if den > 0 else np.nan
                    else:
                        p_vals[u] = np.nan
                elif sum_cols:
                    valid_rows = u_df[u_df[sum_cols].notna().any(axis=1)]
                    if not valid_rows.empty:
                        p_vals[u] = valid_rows[sum_cols].sum(axis=1).values[0]
                    else:
                        p_vals[u] = np.nan
                else:
                    valid_rows = u_df[u_df[col].notna()]
                    p_vals[u] = valid_rows[col].values[0] if not valid_rows.empty else np.nan
            
        # Fill timeline points
        u_val = p_vals.get(sel_uls, np.nan)
        uls_timeline.append({"Periodo": p, "Valor": u_val, "Tipo": f"ULS {sel_uls}"})
        
        g_vals = [p_vals[u] for u in peer_uls if u in p_vals and pd.notna(p_vals[u])]
        g_val = np.mean(g_vals) if g_vals else np.nan
        grp_timeline.append({"Periodo": p, "Valor": g_val, "Tipo": f"Média Grupo {uls_grp}"})
        
        n_vals = [p_vals[u] for u in uls_list if u in p_vals and pd.notna(p_vals[u])]
        n_val = np.mean(n_vals) if n_vals else np.nan
        sns_timeline.append({"Periodo": p, "Valor": n_val, "Tipo": "Média SNS"})
        
    df_chart = pd.DataFrame(uls_timeline + grp_timeline + sns_timeline)
    
    # Import Plotly Graph Objects to build the custom chart with markers
    import plotly.graph_objects as go
    
    if df_chart.empty or 'Valor' not in df_chart.columns or df_chart['Valor'].dropna().empty:
        st.markdown('<div class="chart-wrap" style="text-align: center; padding: 2rem; color: var(--text-muted);">Não existem dados históricos suficientes para gerar o gráfico comparativo deste indicador.</div>', unsafe_allow_html=True)
    else:
        try:
            fig = go.Figure()
            
            # ULS Timeline (Thick blue line with markers)
            fig.add_trace(go.Scatter(
                x=df_chart[df_chart['Tipo'] == f"ULS {sel_uls}"]['Periodo'],
                y=df_chart[df_chart['Tipo'] == f"ULS {sel_uls}"]['Valor'],
                name=f"ULS {sel_uls}",
                line=dict(color="#2563eb", width=3),
                mode="lines+markers",
                marker=dict(size=6, symbol="circle")
            ))
            
            # Group Timeline (Yellow line)
            fig.add_trace(go.Scatter(
                x=df_chart[df_chart['Tipo'] == f"Média Grupo {uls_grp}"]['Periodo'],
                y=df_chart[df_chart['Tipo'] == f"Média Grupo {uls_grp}"]['Valor'],
                name=f"Média Grupo {uls_grp}",
                line=dict(color="#f59e0b", width=2, dash="dash"),
                mode="lines"
            ))
            
            # Play / SNS Timeline (Grey line)
            fig.add_trace(go.Scatter(
                x=df_chart[df_chart['Tipo'] == "Média SNS"]['Periodo'],
                y=df_chart[df_chart['Tipo'] == "Média SNS"]['Valor'],
                name="Média Nacional (SNS)",
                line=dict(color="#71717a", width=2, dash="dot"),
                mode="lines"
            ))
            
            # Apply theme styling
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="DM Sans, sans-serif", color="#71717a" if not IS_DARK else "#a1a1aa", size=11),
                margin=dict(l=40, r=20, t=10, b=40),
                hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                xaxis=dict(
                    gridcolor="rgba(0,0,0,0.06)" if not IS_DARK else "rgba(255,255,255,0.06)",
                    zerolinecolor="rgba(0,0,0,0.06)" if not IS_DARK else "rgba(255,255,255,0.06)",
                    tickangle=-45
                ),
                yaxis=dict(
                    gridcolor="rgba(0,0,0,0.06)" if not IS_DARK else "rgba(255,255,255,0.06)",
                    zerolinecolor="rgba(0,0,0,0.06)" if not IS_DARK else "rgba(255,255,255,0.06)",
                )
            )
            
            st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            st.markdown('</div>', unsafe_allow_html=True)
            
            # --- WHAT-IF SENSITIVITY ANALYSIS PANEL ---
            # Get current value for sensitivity analysis
            uls_timeline_df = df_chart[df_chart['Tipo'] == f"ULS {sel_uls}"]
            val_curr = np.nan
            if not uls_timeline_df.empty:
                val_row = uls_timeline_df[uls_timeline_df['Periodo'] == sel_period]
                if not val_row.empty and pd.notna(val_row['Valor'].values[0]):
                    val_curr = val_row['Valor'].values[0]
                else:
                    # Fallback to the latest available value
                    non_na = uls_timeline_df.dropna(subset=['Valor'])
                    if not non_na.empty:
                        val_curr = non_na['Valor'].values[-1]
                        
            if pd.notna(val_curr):
                st.markdown(f"""
                <div style="margin-top: 1.8rem; margin-bottom: 0.5rem;">
                    <h4 style="margin: 0; font-size: 0.95rem; font-weight: 700; display: flex; align-items: center; gap: 8px;">
                        <span>📊 Análise de Sensibilidade (Cenários ±10%)</span>
                    </h4>
                    <p style="margin: 2px 0 0 0; font-size: 0.72rem; color: var(--text-dim);">
                        Simulação do impacto de uma variação de ±10% no valor atual deste indicador em comparação com as médias de referência.
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                # Calculate scenarios
                val_minus = val_curr * 0.9
                val_plus = val_curr * 1.1
                
                # Fetch reference averages
                grp_df = df_chart[df_chart['Tipo'] == f"Média Grupo {uls_grp}"]
                val_grp = np.nan
                if not grp_df.empty:
                    grp_row = grp_df[grp_df['Periodo'] == sel_period]
                    if not grp_row.empty and pd.notna(grp_row['Valor'].values[0]):
                        val_grp = grp_row['Valor'].values[0]
                    else:
                        non_na_grp = grp_df.dropna(subset=['Valor'])
                        if not non_na_grp.empty:
                            val_grp = non_na_grp['Valor'].values[-1]
                            
                sns_df = df_chart[df_chart['Tipo'] == "Média SNS"]
                val_nat = np.nan
                if not sns_df.empty:
                    sns_row = sns_df[sns_df['Periodo'] == sel_period]
                    if not sns_row.empty and pd.notna(sns_row['Valor'].values[0]):
                        val_nat = sns_row['Valor'].values[0]
                    else:
                        non_na_sns = sns_df.dropna(subset=['Valor'])
                        if not non_na_sns.empty:
                            val_nat = non_na_sns['Valor'].values[-1]
                
                is_pct = ind_pct_map.get(selected_ind, False)
                sentido = ind_sentido_map.get(selected_ind, "+")
                
                def format_val(v):
                    if pd.isna(v):
                        return "-"
                    if "Dívida" in selected_ind or "EBITDA" in selected_ind:
                        if abs(v) > 10000:
                            return f"{(v/1e6):.2f} M€"
                        return f"{v:.2f} M€"
                    if is_pct:
                        return f"{v:.1f}%"
                    return f"{v:,.1f}" if abs(v - round(v)) > 0.01 else f"{v:,.0f}"
                
                def build_card_html(title, val, desc, theme):
                    if theme == "red":
                        hdr_color = "var(--red)"
                        bg_style = f"background: { 'rgba(239,68,68,0.03)' if not IS_DARK else 'rgba(239,68,68,0.01)' }; border-color: { 'rgba(239,68,68,0.2)' if not IS_DARK else 'rgba(239,68,68,0.1)' };"
                    elif theme == "green":
                        hdr_color = "var(--green)"
                        bg_style = f"background: { 'rgba(34,197,94,0.03)' if not IS_DARK else 'rgba(34,197,94,0.01)' }; border-color: { 'rgba(34,197,94,0.2)' if not IS_DARK else 'rgba(34,197,94,0.1)' };"
                    else:
                        hdr_color = "var(--accent)"
                        bg_style = f"background: { 'rgba(37,99,235,0.03)' if not IS_DARK else 'rgba(37,99,235,0.015)' }; border-color: var(--accent);"
                        
                    comp_html = []
                    
                    def get_comp_row(ref_val, label):
                        if pd.isna(ref_val) or ref_val == 0:
                            return f'<div style="display: flex; justify-content: space-between; color: var(--text-dim); font-size: 0.7rem;"><span>{label}:</span> <span>-</span></div>'
                        diff_pct = ((val - ref_val) / ref_val) * 100
                        is_fav = diff_pct >= 0 if sentido == "+" else diff_pct <= 0
                        color = "var(--green)" if is_fav else "var(--red)"
                        return f"""
                        <div style="display: flex; justify-content: space-between; font-size: 0.72rem;">
                            <span style="color: var(--text-muted); font-weight: 500;">{label}:</span>
                            <span style="color: {color}; font-weight: 700;">{diff_pct:+.1f}%</span>
                        </div>
                        """
                        
                    comp_html.append(get_comp_row(val_grp, f"Média Grupo ({format_val(val_grp)})"))
                    comp_html.append(get_comp_row(val_nat, f"Média Nacional ({format_val(val_nat)})"))
                    
                    return f"""
                    <div class="sens-card" style="{bg_style}">
                        <div>
                            <div class="sens-card-header" style="color: {hdr_color};">{title}</div>
                            <div class="sens-card-value">{format_val(val)}</div>
                            <div class="sens-card-desc">{desc}</div>
                        </div>
                        <div class="sens-card-comparison">
                            {"".join(comp_html)}
                        </div>
                    </div>
                    """
                
                minus_theme = "green" if sentido == "-" else "red"
                plus_theme = "green" if sentido == "+" else "red"
                
                html_sens = []
                html_sens.append("""
                <style>
                .sens-container {
                    display: flex;
                    gap: 16px;
                    margin-top: 0.5rem;
                    margin-bottom: 1.5rem;
                    flex-wrap: wrap;
                    width: 100%;
                }
                .sens-card {
                    flex: 1;
                    min-width: 250px;
                    background: var(--card);
                    border: 1px solid var(--border);
                    border-radius: var(--radius);
                    padding: 1rem 1.1rem;
                    box-shadow: var(--shadow);
                    display: flex;
                    flex-direction: column;
                    justify-content: space-between;
                }
                .sens-card-header {
                    font-size: 0.68rem;
                    font-weight: 700;
                    text-transform: uppercase;
                    letter-spacing: 0.05em;
                    margin-bottom: 0.3rem;
                }
                .sens-card-value {
                    font-size: 1.6rem;
                    font-weight: 800;
                    letter-spacing: -0.02em;
                    margin-bottom: 0.2rem;
                    color: var(--text);
                }
                .sens-card-desc {
                    font-size: 0.68rem;
                    color: var(--text-dim);
                    margin-bottom: 0.6rem;
                }
                .sens-card-comparison {
                    font-size: 0.72rem;
                    border-top: 1px solid var(--border-subtle);
                    padding-top: 0.5rem;
                    display: flex;
                    flex-direction: column;
                    gap: 4px;
                }
                </style>
                """)
                html_sens.append('<div class="sens-container">')
                html_sens.append(build_card_html("Cenário -10%", val_minus, "Simulação de desempenho com quebra de 10%.", minus_theme))
                html_sens.append(build_card_html("Desempenho Atual", val_curr, f"Valor real registado em {sel_period}.", "blue"))
                html_sens.append(build_card_html("Cenário +10%", val_plus, "Simulação de desempenho com melhoria de 10%.", plus_theme))
                html_sens.append('</div>')
                
                st.html("".join(html_sens))
            
        except Exception as chart_err:
            st.markdown(f'<div class="chart-wrap" style="text-align: center; padding: 2rem; color: var(--text-muted);">Não foi possível gerar o gráfico para este indicador: {str(chart_err)}</div>', unsafe_allow_html=True)
        
st.markdown("</div>", unsafe_allow_html=True)
