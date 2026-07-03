import sqlite3
import pandas as pd
import requests
import datetime
import os
import unicodedata

# 1. Configuration and Paths
DB_PATH = r"c:\Users\jfili\Documents\Indicadores SNS\sns_indicadores.db"
ENTIDADES_PATH = r"c:\Users\jfili\Documents\Indicadores SNS\T_Entidades.xlsx"
API_BASE_URL = "https://transparencia.sns.gov.pt/api/explore/v2.1"

# 2. Corrected mapping: _fonte -> (dataset_id, date_field, inst_field)
# Discovered via live API catalog inspection
DATASET_MAPPING = {
    '1as Consultas em Tempo Adequado':              ('consultas-em-tempo-real',                                         'tempo',   'instituicao'),
    'CSP - Evolucao Consultas Medicas':             ('evolucao-das-consultas-medicas-nos-csp',                          'tempo',   'entidade'),
    'CSP - Evolucao Contactos Enfermagem':          ('evolucao-dos-contactos-de-enfermagem-nos-csp',                    'tempo',   'entidade'),
    'Cirurgia - Demora Media antes da Cirurgia':    ('demora-media-antes-da-cirurgia',                                  'tempo',   'instituicao'),
    'Cirurgias - Intervencoes Hospitalares':        ('intervencoes-cirurgicas',                                         'tempo',   'instituicao'),
    'Cirurgias em Ambulatorio':                     ('cirurgias-em-ambulatorio',                                        'tempo',   'instituicao'),
    'Consultas CSP - Acesso Populacao Inscrita':    ('acesso-de-consultas-medicas-pela-populacao-inscrita',             'tempo',   'entidade'),
    'Consultas Hospitalares (SICA)':                ('01_sica_evolucao-mensal-das-consultas-medicas-hospitalares',      'tempo',   'instituicao'),
    'Doenca Renal Cronica (GID IRC)':               ('gestao-integrada-da-doenca-insuficiencia-renal-cronica',          'periodo', 'entidade'),
    'Financeiro - Agregados Economico-Financeiros': ('agregados-economico-financeiros',                                 'tempo',   'entidade'),
    'Financeiro - Divida Vencida e Pagamentos':     ('divida-total-vencida-e-pagamentos',                               'periodo', 'entidade'),
    'Financeiro - Gastos TE e Suplementos':         ('percentagem-de-gastos-com-te-e-suplementos-no-total-gastos-com-pessoal', 'tempo', 'entidade'),
    'Internamento - Doentes Saidos / Dias':         ('atividade-de-internamento-hospitalar',                            'tempo',   'instituicao'),
    'Internamento - Ocupacao':                      ('atividade-de-internamento-hospitalar',                            'tempo',   'instituicao'),
    'Morbilidade e Mortalidade Hospitalar':         ('morbilidade-e-mortalidade-hospitalar',                            'ano',     'instituicao'),
    'Mortalidade - AVC Isquemico e Hemorragico':    ('taxa-de-mortalidade-por-avc-isquemico-e-hemorragico',             'tempo',   'instituicao'),
    'Ortopedia - Fraturas Anca 48h':                ('fraturas-da-anca-cirurgias-nas-primeiras-48h',                    'tempo',   'instituicao'),
    'Partos e Cesarianas':                          ('partos-e-cesarianas',                                             'tempo',   'instituicao'),
    'Qualidade Clinica - Antibioticos':             ('antibioticos',                                                    'periodo', 'nome_hospital'),
    'Qualidade Clinica - Diabetes':                 ('diabetes',                                                        'tempo',   'entidade'),
    'Qualidade Clinica - Hipertensao':              ('hipertensao',                                                     'tempo',   'entidade'),
    'RH - Ausencias para Formacao':                 ('ausencias-para-formacao-e-aperfeicoamento-profissional',          'tempo',   'entidade'),
    'RH - Dias de Ausencia por Motivo':             ('contagem-dos-dias-de-ausencia-ao-trabalho-segundo-o-motivo-de-ausencia', 'tempo', 'entidade'),
    'RH - Horas Trabalho Nocturno e Extraordinario':('contagem-das-horas-de-trabalho-nocturno-normal-e-extraordinario', 'tempo',   'entidade'),
    'RH - Trabalhadores por Grupo Profissional':    ('trabalhadores-por-grupo-profissional',                            'periodo', 'instituicao'),
    'RH - Trabalhadores por Modalidade de Vinculacao': ('trabalhadores-por-modalidade-de-vinculacao',                  'tempo',   'entidade'),
    'Saude da Mulher e Crianca':                    ('saude-da-mulher-e-crianca',                                       'tempo',   'area_csp'),
    'Urgencia - Triagem Manchester':                ('atendimentos-em-urgencia-triagem-manchester',                     'tempo',   'instituicao'),
    'Urgencias - Atendimentos por Tipo':            ('atendimentos-por-tipo-de-urgencia-hospitalar-link',               'tempo',   'instituicao'),
    'Utentes Inscritos CSP':                        ('utentes-inscritos-em-cuidados-de-saude-primarios',                'periodo', 'aces'),
}

def clean_text(txt):
    if not txt or pd.isna(txt):
        return ""
    txt = str(txt).strip().lower()
    txt = "".join(c for c in unicodedata.normalize('NFD', txt) if unicodedata.category(c) != 'Mn')
    for word in ['unidade local de saude de', 'unidade local de saude da', 'unidade local de saude do',
                 'unidade local de saude', 'uls', 'e.p.e.', 'e.pe', 'epe']:
        txt = txt.replace(word, '')
    return txt.strip().replace('/', ' ').replace('-', ' ').replace(',', '')

def get_entity_mapping():
    if not os.path.exists(ENTIDADES_PATH):
        return {}, []
    df_uls = pd.read_excel(ENTIDADES_PATH, sheet_name="ULS")
    df_eq  = pd.read_excel(ENTIDADES_PATH, sheet_name="Equivalencia_Entidades")
    df_eq['entidade_portal']  = df_eq['entidade_portal'].astype(str).str.strip()
    df_eq['ULS/IPO_corresp']  = df_eq['ULS/IPO_corresp'].astype(str).str.strip()
    eq_dict  = dict(zip(df_eq['entidade_portal'], df_eq['ULS/IPO_corresp']))
    uls_list = df_uls['ULS'].dropna().unique().tolist()
    return eq_dict, uls_list

def map_to_uls(raw_name, eq_dict, uls_list):
    if not raw_name:
        return None
    raw_str = str(raw_name).strip()
    if raw_str in eq_dict:
        return eq_dict[raw_str]
    raw_clean    = clean_text(raw_name)
    uls_clean_map = {clean_text(u): u for u in uls_list}
    for u_clean, u_orig in uls_clean_map.items():
        if not u_clean:
            continue
        u_words   = u_clean.split()
        raw_words = raw_clean.split()
        if all(w in raw_words for w in u_words if len(w) > 2):
            return u_orig
        if u_clean in raw_clean or raw_clean in u_clean:
            return u_orig
    for u_orig in uls_list:
        if raw_str.lower() in u_orig.lower() or u_orig.lower() in raw_str.lower():
            return u_orig
    return None

def get_last_period_for_source(cursor, fonte):
    """Get the maximum period already stored for a specific source."""
    cursor.execute("SELECT MAX(periodo) FROM indicadores_sns WHERE _fonte = ?", (fonte,))
    row = cursor.fetchone()
    return row[0] if row and row[0] else "2013-01"

def fetch_dataset_records(dataset_id, date_field, last_period, limit=5000):
    """
    Fetch records from Opendatasoft v2.1 API newer than last_period.
    Uses 'tempo' or 'periodo' as the date column depending on the dataset.
    Paginates in batches of 100.
    """
    url    = f"{API_BASE_URL}/catalog/datasets/{dataset_id}/records"
    # Morbilidade uses 'ano' (integer year) – skip incremental filter, fetch all and filter locally
    if date_field == 'ano':
        last_year = int(last_period[:4])
        where_clause = f"ano > {last_year}"
    else:
        where_clause = f"{date_field} > '{last_period}'"

    all_records = []
    offset = 0
    batch  = 100
    while True:
        params = {
            'where': where_clause,
            'limit': batch,
            'offset': offset,
        }
        try:
            res = requests.get(url, params=params, timeout=20)
            if res.status_code == 200:
                data    = res.json()
                results = data.get('results', [])
                # v2.1 may return records directly or wrapped in 'record'
                for r in results:
                    if 'record' in r:
                        all_records.append(r['record']['fields'])
                    else:
                        all_records.append(r)
                if len(results) < batch:
                    break   # last page
                offset += batch
                if offset >= limit:
                    break
            elif res.status_code == 404:
                print(f"  Dataset {dataset_id} not found (404).")
                return []
            else:
                print(f"  API Error {res.status_code} for {dataset_id}: {res.text[:200]}")
                return []
        except Exception as e:
            print(f"  Connection error for {dataset_id}: {e}")
            return []
    return all_records

def main():
    print(f"[{datetime.datetime.now()}] Starting Portal da Transparência API Sync...")

    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}. Run import_to_db.py first.")
        return

    conn   = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get DB schema
    cursor.execute("PRAGMA table_info(indicadores_sns)")
    db_cols = [row[1] for row in cursor.fetchall()]

    # Load entity mappings
    eq_dict, uls_list = get_entity_mapping()

    new_records_count = 0

    for fonte, (dataset_id, date_field, inst_field) in DATASET_MAPPING.items():
        last_period = get_last_period_for_source(cursor, fonte)
        print(f"Syncing '{fonte}' (dataset={dataset_id}, date={date_field}) | last in DB: {last_period}")

        records = fetch_dataset_records(dataset_id, date_field, last_period)
        if not records:
            print(f"  No new records.")
            continue

        print(f"  Fetched {len(records)} raw records. Processing...")
        df_new = pd.DataFrame(records)
        df_new['_fonte'] = fonte

        # Normalise the period column to 'periodo' (YYYY-MM format)
        if date_field == 'ano':
            # annual – stored as integer year; map to YYYY-01
            if 'ano' in df_new.columns:
                df_new['periodo'] = df_new['ano'].astype(str).str[:4] + '-01'
        elif date_field in df_new.columns:
            df_new['periodo'] = df_new[date_field].astype(str).str[:7]  # keep YYYY-MM
        else:
            print(f"  Date field '{date_field}' not found in response – skipping.")
            continue

        # Map entity to ULS name
        if inst_field in df_new.columns:
            df_new['entity_raw'] = df_new[inst_field].astype(str)
            df_new['mapped_uls'] = df_new['entity_raw'].apply(
                lambda x: map_to_uls(x, eq_dict, uls_list))
        else:
            df_new['entity_raw'] = None
            df_new['mapped_uls'] = None

        # Fill missing DB columns
        for col in db_cols:
            if col not in df_new.columns:
                df_new[col] = None

        df_to_insert = df_new[db_cols]
        df_to_insert.to_sql('indicadores_sns', conn, if_exists='append', index=False)
        new_records_count += len(df_to_insert)
        print(f"  Inserted {len(df_to_insert)} records.")

    conn.close()

    if new_records_count > 0:
        print(f"\nSync completed. Added {new_records_count} new records total.")
        try:
            import streamlit as st
            st.cache_data.clear()
            print("Streamlit cache cleared.")
        except:
            pass
    else:
        print("\nSync completed. No new data to import.")

if __name__ == "__main__":
    main()
