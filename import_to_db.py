import pandas as pd
import sqlite3
import unicodedata
import os
import sys

csv_path = r"c:\Users\jfili\Documents\Indicadores SNS\_MASTER_sns_uls_regionais.csv"
entidades_path = r"c:\Users\jfili\Documents\Indicadores SNS\T_Entidades.xlsx"
ids_path = r"c:\Users\jfili\Documents\Indicadores SNS\IDs_indicadores_com_nivel_cuidados.xlsx"
db_path = r"c:\Users\jfili\Documents\Indicadores SNS\sns_indicadores.db"

# Clear existing db if any
if os.path.exists(db_path):
    try:
        os.remove(db_path)
        print("Removed existing database.")
    except Exception as e:
        print(f"Error removing existing database: {e}")

print("Loading reference tables...")
df_uls = pd.read_excel(entidades_path, sheet_name="ULS")
df_eq = pd.read_excel(entidades_path, sheet_name="Equivalencia_Entidades")
df_ids = pd.read_excel(ids_path, sheet_name="Indicadores_base")

# Standardize equivalences
df_eq['entidade_portal'] = df_eq['entidade_portal'].astype(str).str.strip()
df_eq['ULS/IPO_corresp'] = df_eq['ULS/IPO_corresp'].astype(str).str.strip()
eq_dict = dict(zip(df_eq['entidade_portal'], df_eq['ULS/IPO_corresp']))

eq_dict.update({
    'UNIDADE LOCAL DE SAÚDE DA ARRÁBIDA, E.P.E.': 'ULS Arrábida',
    'UNIDADE LOCAL DE SAÚDE DA LEZÍRIA, E.P.E.': 'ULS Lezíria',
    'UNIDADE LOCAL DE SAÚDE DE ALMADA / SEIXAL, E.P.E.': 'ULS Almada / Seixal',
    'UNIDADE LOCAL DE SAÚDE DE AMADORA / SINTRA, E.P.E.': 'ULS Amadora / Sintra',
    'UNIDADE LOCAL DE SAÚDE DE LOURES / ODIVELAS, E.P.E.': 'ULS Loures / Odivelas',
    'UNIDADE LOCAL DE SAÚDE DE SANTA MARIA, E.P.E.': 'ULS Santa Maria',
    'UNIDADE LOCAL DE SAÚDE DE SÃO JOSÉ, E.P.E.': 'ULS São José',
    'UNIDADE LOCAL DE SAÚDE DO ARCO RIBEIRINHO, E.P.E.': 'ULS Arco Ribeirinho',
    'UNIDADE LOCAL DE SAÚDE DO ESTUÁRIO DO TEJO, E.P.E.': 'ULS Estuário do Tejo',
    'UNIDADE LOCAL DE SAÚDE DO MÉDIO TEJO, E.P.E.': 'ULS Médio Tejo',
    'UNIDADE LOCAL DE SAÚDE DO OESTE, E.P.E.': 'ULS Oeste',
    'UNIDADE LOCAL DE SAÚDE DE BARCELOS / ESPOSENDE, E.P.E.': 'ULS Barcelos / Esposende',
    'UNIDADE LOCAL DE SAÚDE DE BRAGA, E.P.E.': 'ULS Braga',
    'UNIDADE LOCAL DE SAÚDE DE ENTRE DOURO E VOUGA, E.P.E.': 'ULS Entre Douro e Vouga',
    'UNIDADE LOCAL DE SAÚDE DE GAIA / ESPINHO, E.P.E.': 'ULS Gaia / Espinho',
    'UNIDADE LOCAL DE SAÚDE DE SANTO ANTÓNIO, E.P.E.': 'ULS Santo António',
    'UNIDADE LOCAL DE SAÚDE DE SÃO JOÃO, E.P.E.': 'ULS São João',
    'UNIDADE LOCAL DE SAÚDE DO ALTO AVE, E.P.E.': 'ULS Alto Ave',
    'UNIDADE LOCAL DE SAÚDE DO ALTO MINHO,  E.P.E.': 'ULS Alto Minho',
    'UNIDADE LOCAL DE SAÚDE DO ALTO MINHO, E.P.E.': 'ULS Alto Minho',
    'UNIDADE LOCAL DE SAÚDE DO NORDESTE, E.P.E.': 'ULS Nordeste',
    'UNIDADE LOCAL DE SAÚDE DA PÓVOA DE VARZIM / VILA DO CONDE, E.P.E.': 'ULS Póvoa Varzim / Vila Conde',
    'UNIDADE LOCAL DE SAÚDE DE TRÁS-OS-MONTES E ALTO DOURO, E.P.E.': 'ULS Trás-os-Montes Alto Douro',
    'UNIDADE LOCAL SAÚDE DE MATOSINHOS, E.P.E.': 'ULS Matosinhos',
    'UNIDADE LOCAL DE SAÚDE DE MATOSINHOS, E.P.E.': 'ULS Matosinhos',
    'INST.PORT.ONCOLOGIA DE LISBOA-FRANC.GENTIL, E.P.E.': 'IPOL',
    'INSTITUTO PORT.ONCOLOGIA DO PORTO, E.P.E.': 'IPOP',
    'INST.PORT.ONC.FRANCISCO GENTIL-COIMBRA, E.P.E.': 'IPOC',
    'Hospital de Cascais, PPP': 'Hospital de Cascais, PPP',
})

def clean_text(txt):
    if not txt or pd.isna(txt):
        return ""
    txt = str(txt).strip().lower()
    txt = "".join(c for c in unicodedata.normalize('NFD', txt) if unicodedata.category(c) != 'Mn')
    for word in ['unidade local de saude de', 'unidade local de saude da', 'unidade local de saude do', 'unidade local de saude', 'uls', 'e.p.e.', 'e.pe', 'epe']:
        txt = txt.replace(word, '')
    return txt.strip().replace('/', ' ').replace('-', ' ').replace(',', '')

uls_list = df_uls['ULS'].dropna().unique().tolist()
uls_clean_map = {clean_text(u): u for u in uls_list}

def map_to_uls_mapped(raw_name):
    if not raw_name:
        return None
    raw_str = str(raw_name).strip()
    if raw_str in eq_dict:
        return eq_dict[raw_str]
    raw_clean = clean_text(raw_name)
    for u_clean, u_orig in uls_clean_map.items():
        if not u_clean:
            continue
        u_words = u_clean.split()
        raw_words = raw_clean.split()
        if all(w in raw_words for w in u_words if len(w) > 2):
            return u_orig
        if u_clean in raw_clean or raw_clean in u_clean:
            return u_orig
    for u_orig in uls_list:
        if raw_str.lower() in u_orig.lower() or u_orig.lower() in raw_str.lower():
            return u_orig
    return None

def get_entity(row):
    if row['_fonte'] == 'Doenca Renal Cronica (GID IRC)':
        val = row['ars_uls']
        if pd.notna(val) and str(val).strip() != "":
            return str(val).strip()
    for col in ['instituicao', 'entidade', 'nome_hospital', 'ars_uls', 'aces', 'ars_hospital', 'area_csp']:
        val = row[col]
        if pd.notna(val) and str(val).strip() != "":
            return str(val).strip()
    return None

print("Loading main CSV file (takes a few seconds)...")
df_raw = pd.read_csv(csv_path, sep=';', encoding='utf-8-sig', low_memory=False, on_bad_lines='skip')

print("Mapping entities to ULS standard...")
df_raw['entity_raw'] = df_raw.apply(get_entity, axis=1)
df_raw['mapped_uls'] = df_raw['entity_raw'].apply(map_to_uls_mapped)

print("Dropping rows without mapped ULS...")
df_raw = df_raw.dropna(subset=['mapped_uls'])

print("Standardizing periods...")
df_raw['periodo'] = df_raw['periodo'].astype(str).str.strip()

# Map year/quarter to period for Mortality
mask_mort = df_raw['_fonte'] == 'Morbilidade e Mortalidade Hospitalar'
if mask_mort.any():
    def make_period(row):
        try:
            y = int(float(row['ano']))
            t = str(row['trimestre']).strip().lower()
            if 'primeiro' in t:
                m = '03'
            elif 'segundo' in t:
                m = '06'
            elif 'terceiro' in t:
                m = '09'
            elif 'quarto' in t:
                m = '12'
            else:
                return None
            return f"{y}-{m}"
        except:
            return None
    df_raw.loc[mask_mort, 'periodo'] = df_raw[mask_mort].apply(make_period, axis=1)

print("Opening database connection...")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Writing ULS metadata...")
uls_meta = df_uls[['ULS', 'Grupo', 'ARS/Região']].drop_duplicates()
uls_meta['ULS'] = uls_meta['ULS'].astype(str).str.strip()
uls_meta['Grupo'] = uls_meta['Grupo'].astype(str).str.strip()
uls_meta.to_sql("uls_metadata", conn, if_exists="replace", index=False)

print("Writing Indicators metadata...")
ind_meta = df_ids.dropna(subset=['ID_Indicador']).copy()
ind_meta['ID_Indicador'] = ind_meta['ID_Indicador'].astype(str).str.strip()
ind_meta['_fonte'] = ind_meta['_fonte'].astype(str).str.strip()
ind_meta['Sentido desejável'] = ind_meta.iloc[:, 10].astype(str).str.strip()
# Drop non-serializable columns
ind_meta = ind_meta.loc[:, ~ind_meta.columns.str.contains('^Unnamed')]
ind_meta.to_sql("ind_metadata", conn, if_exists="replace", index=False)

print("Writing main indicators dataset...")
# Write the table
df_raw.to_sql("indicadores_sns", conn, if_exists="replace", index=False)

print("Creating indexes on main table...")
cursor.execute("CREATE INDEX idx_indicadores_periodo ON indicadores_sns (periodo)")
cursor.execute("CREATE INDEX idx_indicadores_mapped ON indicadores_sns (mapped_uls)")
cursor.execute("CREATE INDEX idx_indicadores_fonte ON indicadores_sns (_fonte)")
conn.commit()

print("Verifying database size...")
cursor.execute("SELECT COUNT(*) FROM indicadores_sns")
row_count = cursor.fetchone()[0]
print(f"Total rows successfully imported into indicadores_sns: {row_count}")

conn.close()
print("Database migration complete and saved to sns_indicadores.db!")
