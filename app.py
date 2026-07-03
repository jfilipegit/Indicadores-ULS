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
if "sort" in params:
    q_sort = params["sort"].replace("_", " ").replace("pct", "%").replace("slash", "/")
    st.session_state.sort_ind = q_sort
    st.session_state.sort_state = int(params.get("state", 0))
else:
    st.session_state.sort_ind = None
    st.session_state.sort_state = 0

# Restore filter values from URL params (set when sort links are clicked)
_url_end_month  = params.get("end",   None)
_url_start_month= params.get("start", None)
_url_persp_idx  = params.get("persp", None)
_url_groups     = params.get("grps",  None)  # comma-separated group names

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
    margin-bottom: 1px !important;
    padding-bottom: 0px !important;
    font-size: 0.72rem !important;
    font-weight: 600 !important;
}}
/* Reduce general spacing */
div[data-testid="stVerticalBlock"] > div {{
    gap: 0.2rem !important;
}}
div[data-baseweb="popover"] {{
    background-color: var(--card) !important;
    color: var(--text) !important;
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

# Load data once
df_uls, df_ids, periods = load_data()

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
    
    db_path = r"c:\Users\jfili\Documents\Indicadores SNS\sns_indicadores.db"
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
                if src_filter:
                    subset = subset[subset['_fonte'] == src_filter]
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

# 6. Main Page Top Header with Title and all Inline selectors on a single line
col_title, col_de, col_ate, col_persp, col_group = st.columns([1.5, 0.6, 0.6, 1.1, 1.1])

all_periods = sorted([str(p) for p in periods if str(p).strip().lower() != 'nan'])

with col_title:
    st.markdown("<h3 style='margin: 0.3rem 0; font-size: 1.15rem; font-weight: 700; color: var(--text); line-height: 1.2;'>ULS Regionais<br><span style='font-size: 0.78rem; font-weight: 500; color: var(--text-muted);'>Relatório de Desempenho</span></h3>", unsafe_allow_html=True)

with col_ate:
    # End Month selector — restore from URL if coming from a sort link
    reversed_periods = all_periods[::-1]
    ate_index = 0
    if _url_end_month and _url_end_month in reversed_periods:
        ate_index = reversed_periods.index(_url_end_month)
    end_month = st.selectbox(
        "ATÉ:",
        options=reversed_periods,
        index=ate_index,
        key="end_month_sel"
    )

# Standard YTD start period logic based on end month
end_year = end_month[:4]
default_start = f"{end_year}-01"
if default_start not in all_periods:
    default_start = all_periods[0]
    
start_options = [p for p in all_periods if p <= end_month]
try:
    start_index = start_options.index(default_start)
except ValueError:
    start_index = 0
# Override with URL value if present
if _url_start_month and _url_start_month in start_options:
    start_index = start_options.index(_url_start_month)

with col_de:
    start_month = st.selectbox(
        "DE:",
        options=start_options,
        index=start_index,
        key="start_month_sel"
    )

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
    perspective = st.selectbox(
        "PERSPETIVA:",
        options=persp_options,
        index=persp_index,
        key="persp_sel"
    )

with col_group:
    available_grps = sorted(df_uls['Grupo'].dropna().unique().tolist())
    # Restore group selection from URL if present (set when sort links are clicked)
    if _url_groups:
        default_grps = [g for g in _url_groups.split(",") if g in available_grps]
        if not default_grps:
            default_grps = available_grps
    else:
        # Default on fresh page load: only Grupo C (for testing purposes)
        default_grps = [g for g in available_grps if g == "Grupo C"]
        if not default_grps:
            default_grps = available_grps
    group_filter = st.multiselect(
        "GRUPO ULS:",
        options=available_grps,
        default=default_grps,
        key="group_sel"
    )

# Compute calculations
df_var_hom, df_base_idx, df_grupo_pos, df_raw_vals = calculate_metrics(df_uls, df_ids, start_month, end_month)

# Filter ULS columns based on Group
df_uls_filtered = df_uls[df_uls['Grupo'].isin(group_filter)]
uls_to_show = sorted(df_uls_filtered['ULS'].unique().tolist())

# Select proper metric DataFrame
if "Variação Homóloga" in perspective:
    base_df = df_var_hom.copy()
    metric_title = "Variação Homóloga (%) ou Ponto Percentual (pp)"
    colorscale = [[0.0, "#dc2626"], [0.5, "#f4f4f5"], [1.0, "#16a34a"]] # Red to white to green
    zmin, zmax = -15, 15
    val_suffix = "%"
elif "Índice Base 2024" in perspective:
    base_df = df_base_idx.copy()
    metric_title = "Índice Base 2024 (100 = Alinhado)"
    colorscale = [[0.0, "#dc2626"], [0.5, "#f4f4f5"], [1.0, "#16a34a"]]
    zmin, zmax = 80, 120
    val_suffix = ""
else:
    base_df = df_grupo_pos.copy()
    metric_title = "Posição face ao Grupo (100 = Média do Grupo)"
    colorscale = [[0.0, "#dc2626"], [0.5, "#f4f4f5"], [1.0, "#16a34a"]]
    zmin, zmax = 85, 115
    val_suffix = ""

# Calculate summary columns (SNS is average of all ULS; Média Grupo is average of active group)
val_sns = base_df.mean(axis=1)
plot_df = base_df[uls_to_show].copy()

# Add to plot_df at the first positions
plot_df.insert(0, "SNS", val_sns)
if len(group_filter) == 1:
    val_grp = plot_df.drop(columns=["SNS"]).mean(axis=1)
    plot_df.insert(1, "Média Grupo", val_grp)

# Add to df_raw_vals as well for hover text
raw_sns = df_raw_vals.mean(axis=1)
raw_plot_vals = df_raw_vals[uls_to_show].copy()

raw_plot_vals.insert(0, "SNS", raw_sns)
if len(group_filter) == 1:
    raw_grp = raw_plot_vals.drop(columns=["SNS"]).mean(axis=1)
    raw_plot_vals.insert(1, "Média Grupo", raw_grp)
    
df_raw_vals_plot = raw_plot_vals

# --- Sort ULS columns based on selected indicator row ---
if st.session_state.sort_ind and st.session_state.sort_ind in plot_df.index:
    # Separate summary columns from ULS columns
    summary_cols = ["SNS"]
    if "Média Grupo" in plot_df.columns:
        summary_cols.append("Média Grupo")
    uls_cols = [c for c in plot_df.columns if c not in summary_cols]
    
    # Get values for sorting
    row_vals = plot_df.loc[st.session_state.sort_ind, uls_cols]
    if st.session_state.sort_state == 1:
        sorted_uls = row_vals.sort_values(ascending=True).index.tolist()
    elif st.session_state.sort_state == 2:
        sorted_uls = row_vals.sort_values(ascending=False).index.tolist()
    else:
        sorted_uls = uls_cols
        
    plot_df = plot_df[summary_cols + sorted_uls]
    df_raw_vals_plot = df_raw_vals_plot[summary_cols + sorted_uls]

# Rename index to show visual arrow indicator on the y-axis labels
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
        return "transparent", "#71717a" # grey text for nan
        
    # Normalize values to [-1, 1] relative to logical limits
    if "Variação" in perspective:
        vmin, vmax = -15, 15
        is_inverted = (sentido == "-")
        norm_val = max(min(val, vmax), vmin) / vmax
        if is_inverted:
            norm_val = -norm_val
    elif "Índice Base" in perspective:
        vmin, vmax = 80, 120
        is_inverted = (sentido == "-")
        norm_val = (val - 100) / 20 # scale deviation
        norm_val = max(min(norm_val, 1.0), -1.0)
        if is_inverted:
            norm_val = -norm_val
    else: # Posição Relativa
        vmin, vmax = 85, 115
        is_inverted = (sentido == "-")
        norm_val = (val - 100) / 15
        norm_val = max(min(norm_val, 1.0), -1.0)
        if is_inverted:
            norm_val = -norm_val

    # Interpolate colors: Red (#dc2626) <-> Zinc (#f4f4f5) <-> Green (#16a34a)
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

# Map indicators to their properties
ind_pct_map = {ind["name"]: ind["is_pct"] for ind in heatmap_indicators}
ind_sentido_map = {ind["name"]: ind["sentido"] for ind in heatmap_indicators}
# Build HTML Table Heatmap
html_table = []
html_table.append(f"""
<style>
.heatmap-table {{
    border-collapse: collapse;
    font-family: 'DM Sans', sans-serif;
    color: {"#ffffff" if IS_DARK else "#000000"};
    width: 100%;
}}
.heatmap-table th {{
    font-size: 8.5px;
    font-weight: bold;
    text-align: center;
    vertical-align: bottom;
    border-bottom: 2px solid {"#3f3f46" if IS_DARK else "#e4e4e7"};
    padding: 4px 4px 8px 4px;
    min-width: 20px;
    position: sticky;
    top: 0;
    z-index: 10;
    background-color: {"#09090b" if IS_DARK else "#ffffff"};
}}
.heatmap-table th .hdr-label {{
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    word-break: break-word;
    line-height: 1.3;
    max-height: 2.6em;
}}
.heatmap-table td.row-lbl {{
    font-size: 9.5px;
    font-weight: bold;
    text-align: right;
    padding: 3px 8px;
    border-right: 2px solid {"#3f3f46" if IS_DARK else "#e4e4e7"};
    min-width: 165px;
    max-width: 165px;
    width: 165px;
    white-space: nowrap;
}}
.heatmap-table td.cell {{
    text-align: center;
    font-weight: bold;
    font-size: 8px;
    min-width: 20px;
    height: 20px;
    border: 1px solid {"#27272a" if IS_DARK else "#ffffff"};
    cursor: help;
}}
</style>
<div style="overflow-x: auto; overflow-y: auto; max-height: 82vh; width: 100%; padding-bottom: 10px;">
<table class="heatmap-table">
<thead>
<tr style="vertical-align: bottom;">
    <th style="text-align: right; font-size: 10px; padding-bottom: 8px; padding-right: 8px; border-right: 2px solid {'#3f3f46' if IS_DARK else '#e4e4e7'}; position: sticky; top: 0; z-index: 11; background-color: {'#09090b' if IS_DARK else '#ffffff'};">Indicador</th>
""")

for col_name in plot_df.columns:
    short_col = col_name.replace("ULS ", "")
    html_table.append(f"""
    <th><div class="hdr-label">{short_col}</div></th>
    """)
html_table.append('</tr></thead><tbody>')

for ind_name in plot_df.index:
    clean_ind = ind_name.replace("▲ ", "").replace("▼ ", "").strip()
    ind_safe = clean_ind.replace(" ", "_").replace("%", "pct").replace("/", "slash")

    # Encode current filter state so it survives the page reload triggered by clicking a sort link
    persp_idx  = persp_options.index(perspective)
    grps_str   = ",".join(group_filter)
    filter_params = f"&end={end_month}&start={start_month}&persp={persp_idx}&grps={grps_str}"

    # Visual cues for active sort
    arrow = ""
    color_link = "#ffffff" if IS_DARK else "#000000"
    if st.session_state.sort_ind == clean_ind:
        if st.session_state.sort_state == 1:
            arrow = "▲ "
            next_href = f"?sort={ind_safe}&state=2{filter_params}"
            color_link = "#22c55e"
        elif st.session_state.sort_state == 2:
            arrow = "▼ "
            next_href = f"?{filter_params.lstrip('&')}"  # reset sort, keep filters
            color_link = "#ef4444"
    else:
        next_href = f"?sort={ind_safe}&state=1{filter_params}"
        
    html_table.append('<tr style="height: 20px;">')
    html_table.append(f"""
    <td class="row-lbl">
        <a href="{next_href}" target="_self" style="text-decoration: none; color: {color_link}; transition: color 0.15s;">
            {arrow}{clean_ind}
        </a>
    </td>
    """)
    
    is_pct = ind_pct_map.get(clean_ind, False)
    is_pp = is_pct or "%" in clean_ind or "pp" in clean_ind
    sentido = ind_sentido_map.get(clean_ind, "+")
    
    for uls_name in plot_df.columns:
        val = plot_df.at[ind_name, uls_name]
        raw_val = df_raw_vals_plot.at[clean_ind, uls_name]
        
        # Color scale calculation
        bg_color, text_color = get_color_for_value(val, sentido, perspective)
        
        # Formatted val
        if pd.isna(val):
            val_str = "-"
        else:
            val_format = f"{val:+.1f}" if "Variação" in perspective else f"{val:.1f}"
            suffix = " pp" if (is_pp and "Variação" in perspective) else val_suffix
            val_str = f"{val_format}{suffix}"
            
        # Tooltip text
        if pd.isna(raw_val):
            raw_str = "Sem dados"
        else:
            if "Dívida" in clean_ind or "EBITDA" in clean_ind:
                raw_str = f"{(raw_val/1e6):.2f} M€"
            elif is_pp:
                raw_str = f"{raw_val:.1f}%"
            else:
                raw_str = f"{raw_val:,.0f}"
                
        tooltip = f"{uls_name} - {clean_ind}\nCalculado: {val_str}\nValor Real: {raw_str}"
        
        html_table.append(f"""
        <td title="{tooltip}" style="background-color: {bg_color}; color: {text_color};" class="cell">
            {val_str}
        </td>
        """)
    html_table.append('</tr>')

html_table.append('</tbody></table></div>')
table_block = "".join(html_table)

# Render native HTML table
st.html(table_block)

st.markdown("</div>", unsafe_allow_html=True)


# 10. Summary info
st.markdown("""
> **Dica de Leitura:**
> * **Tons de Verde** representam melhorias de desempenho (aumento de indicadores positivos como consultas/cirurgias ou diminuição de indicadores negativos como urgências/demora média/dívida).
> * **Tons de Vermelho** indicam evolução desfavorável ou desvios desfavoráveis face ao período homólogo ou ano base.
""")
