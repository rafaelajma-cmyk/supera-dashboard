
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- CONFIG ---
st.set_page_config(page_title="Dashboard de Pedidos", layout="wide")

INPUT_PATH = "/mnt/data/Relatório de Status de Pedido Copia.xlsx"

@st.cache_data
def load_and_consolidate(path):
    xls = pd.read_excel(path, sheet_name=None)
    df_list = []
    for s, df in xls.items():
        df = df.copy()
        df['MES_ABA'] = s
        df_list.append(df)
    df_all = pd.concat(df_list, ignore_index=True)
    # normalize column names
    df_all.columns = [c.strip() for c in df_all.columns]
    # parse dates
    if 'DATA DO PEDIDO' in df_all.columns:
        df_all['DATA DO PEDIDO'] = pd.to_datetime(df_all['DATA DO PEDIDO'], errors='coerce')
    # helper cols
    df_all['ANO'] = df_all['DATA DO PEDIDO'].dt.year
    df_all['MES'] = df_all['DATA DO PEDIDO'].dt.month
    df_all['MES_ANO'] = df_all['DATA DO PEDIDO'].dt.to_period('M').astype(str)
    # find value column
    possible_value_cols = [c for c in df_all.columns if 'VALOR' in c.upper() and ('LÍQUIDO' in c.upper() or 'FATURADO' in c.upper() or 'TOTAL' in c.upper())]
    value_col = possible_value_cols[0] if possible_value_cols else None
    if value_col is None:
        possible_value_cols = [c for c in df_all.columns if 'VALOR' in c.upper()]
        value_col = possible_value_cols[0] if possible_value_cols else None
    if value_col is None:
        df_all['VALOR_FATURADO'] = 0.0
        value_col = 'VALOR_FATURADO'
    else:
        df_all[value_col] = pd.to_numeric(df_all[value_col], errors='coerce').fillna(0.0)
    # rename some useful cols
    rename_map = {}
    for col in df_all.columns:
        upper = col.upper()
        if 'NÚMERO DO PEDIDO' in upper or 'NUMERO DO PEDIDO' in upper:
            rename_map[col] = 'NUMERO_PEDIDO'
        if 'USUÁRIO' in upper or 'USUARIO' in upper:
            rename_map[col] = 'USUARIO_RESPONSAVEL'
        if 'ORIGEM' in upper and 'DO PEDIDO' in upper:
            rename_map[col] = 'ORIGEM_DO_PEDIDO'
        if 'STATUS' in upper and 'PEDIDO' in upper:
            rename_map[col] = 'STATUS_PEDIDO'
        if 'NOME DO CLIENTE' in upper or 'NOME CLIENTE' in upper:
            rename_map[col] = 'NOME_CLIENTE'
        if 'CÓDIGO DO CLIENTE' in upper or 'CODIGO DO CLIENTE' in upper:
            rename_map[col] = 'CODIGO_CLIENTE'
        if 'POLÍTICA' in upper or 'POLITICA' in upper:
            rename_map[col] = 'POLITICA_COMERCIAL'
        if 'CONDIC' in upper and 'PAGAMENTO' in upper:
            rename_map[col] = 'CONDICAO_PAGAMENTO'
    df_all = df_all.rename(columns=rename_map)
    return df_all, value_col

df, VALUE_COL = load_and_consolidate(INPUT_PATH)

st.title("Dashboard Interativo de Pedidos")
st.markdown("Painel gerado a partir do arquivo: **Relatório de Status de Pedido Copia.xlsx**")

# Sidebar filters
st.sidebar.header("Filtros")
min_date = df['DATA DO PEDIDO'].min()
max_date = df['DATA DO PEDIDO'].max()
date_range = st.sidebar.date_input("Período (data do pedido)", [min_date, max_date])

vendedores = ['Todos'] + sorted(df['USUARIO_RESPONSAVEL'].dropna().unique().tolist()) if 'USUARIO_RESPONSAVEL' in df.columns else ['Todos']
vendedor_sel = st.sidebar.selectbox("Vendedor", vendedores)

clientes = ['Todos'] + sorted(df['NOME_CLIENTE'].dropna().unique().tolist()) if 'NOME_CLIENTE' in df.columns else ['Todos']
cliente_sel = st.sidebar.selectbox("Cliente", clientes)

status_options = ['Todos'] + sorted(df['STATUS_PEDIDO'].dropna().unique().tolist()) if 'STATUS_PEDIDO' in df.columns else ['Todos']
status_sel = st.sidebar.multiselect("Status do Pedido (selecione um ou mais)", status_options, default=['Todos'])

origem_options = ['Todos'] + sorted(df['ORIGEM_DO_PEDIDO'].dropna().unique().tolist()) if 'ORIGEM_DO_PEDIDO' in df.columns else ['Todos']
origem_sel = st.sidebar.multiselect("Origem do Pedido", origem_options, default=['Todos'])

policy_options = ['Todos'] + sorted(df['POLITICA_COMERCIAL'].dropna().unique().tolist()) if 'POLITICA_COMERCIAL' in df.columns else ['Todos']
policy_sel = st.sidebar.multiselect("Política Comercial", policy_options, default=['Todos'])

# Apply filters
df_filtered = df.copy()

# date filter
if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
    start_dt = pd.to_datetime(date_range[0])
    end_dt = pd.to_datetime(date_range[1])
    df_filtered = df_filtered[(df_filtered['DATA DO PEDIDO'] >= start_dt) & (df_filtered['DATA DO PEDIDO'] <= end_dt)]
# vendedor
if vendedor_sel != 'Todos':
    df_filtered = df_filtered[df_filtered['USUARIO_RESPONSAVEL'] == vendedor_sel]
# cliente
if cliente_sel != 'Todos':
    df_filtered = df_filtered[df_filtered['NOME_CLIENTE'] == cliente_sel]
# status
if status_sel and 'Todos' not in status_sel:
    df_filtered = df_filtered[df_filtered['STATUS_PEDIDO'].isin(status_sel)]
# origem
if origem_sel and 'Todos' not in origem_sel:
    df_filtered = df_filtered[df_filtered['ORIGEM_DO_PEDIDO'].isin(origem_sel)]
# policy
if policy_sel and 'Todos' not in policy_sel:
    df_filtered = df_filtered[df_filtered['POLITICA_COMERCIAL'].isin(policy_sel)]

# --- Top metrics ---
col1, col2, col3, col4, col5 = st.columns(5)
total_pedidos = df_filtered['NUMERO_PEDIDO'].nunique() if 'NUMERO_PEDIDO' in df_filtered.columns else df_filtered.shape[0]
valor_total = df_filtered[VALUE_COL].sum()
pct_faturado = (df_filtered[df_filtered['STATUS_PEDIDO'].str.upper().str.contains('FATURADO', na=False)]['NUMERO_PEDIDO'].nunique() / total_pedidos * 100) if ('STATUS_PEDIDO' in df_filtered.columns and total_pedidos>0) else None
vendedores_ativos = df_filtered['USUARIO_RESPONSAVEL'].nunique() if 'USUARIO_RESPONSAVEL' in df_filtered.columns else 0
clientes_ativos = df_filtered['NOME_CLIENTE'].nunique() if 'NOME_CLIENTE' in df_filtered.columns else 0

col1.metric("Total de Pedidos", f"{total_pedidos:,}")
col2.metric("Valor Total (R$)", f"{valor_total:,.2f}")
col3.metric("% Faturado", f"{pct_faturado:.2f}%" if pct_faturado is not None else "N/A")
col4.metric("Vendedores Ativos", vendedores_ativos)
col5.metric("Clientes Atendidos", clientes_ativos)

# --- Charts layout ---
# 1) Valor Faturado por Mês (coluna)
st.markdown("## Valor Faturado por Mês")
if 'MES_ANO' in df_filtered.columns:
    monthly = df_filtered.groupby('MES_ANO').agg(TOTAL_PEDIDOS=('NUMERO_PEDIDO', lambda x: x.nunique() if x.dtype == 'O' else x.count()), VALOR_TOTAL=(VALUE_COL, 'sum')).reset_index().sort_values('MES_ANO')
    fig_month = px.bar(monthly, x='MES_ANO', y='VALOR_TOTAL', labels={'MES_ANO':'Mês/Ano','VALOR_TOTAL':'Valor (R$)'}, hover_data=['TOTAL_PEDIDOS'])
    fig_month.add_trace(go.Scatter(x=monthly['MES_ANO'], y=monthly['TOTAL_PEDIDOS'], name='Qtd Pedidos', yaxis='y2'))
    fig_month.update_layout(yaxis2=dict(overlaying='y', side='right', title='Qtd Pedidos'), xaxis_tickangle=-45, height=450)
    st.plotly_chart(fig_month, use_container_width=True)
else:
    st.info("Coluna MES_ANO não encontrada para gerar gráfico mensal.")

# 2) Distribuição por Status
st.markdown("## Distribuição por Status do Pedido")
if 'STATUS_PEDIDO' in df_filtered.columns:
    status_df = df_filtered.groupby('STATUS_PEDIDO').agg(QTDE=('NUMERO_PEDIDO', lambda x: x.nunique() if x.dtype == 'O' else x.count()), VALOR=(VALUE_COL, 'sum')).reset_index().sort_values('QTDE', ascending=False)
    fig_status = px.pie(status_df, names='STATUS_PEDIDO', values='QTDE', hole=0.4)
    st.plotly_chart(fig_status, use_container_width=True)
else:
    st.info("Coluna STATUS_PEDIDO não encontrada.")

# 3) Top Vendedores
st.markdown("## Top Vendedores por Valor Faturado")
if 'USUARIO_RESPONSAVEL' in df_filtered.columns:
    vend_df = df_filtered.groupby('USUARIO_RESPONSAVEL').agg(TOTAL_PEDIDOS=('NUMERO_PEDIDO', lambda x: x.nunique() if x.dtype == 'O' else x.count()), VALOR_TOTAL=(VALUE_COL, 'sum')).reset_index().sort_values('VALOR_TOTAL', ascending=False)
    fig_vend = px.bar(vend_df.head(20), x='USUARIO_RESPONSAVEL', y='VALOR_TOTAL', labels={'VALOR_TOTAL':'Valor (R$)','USUARIO_RESPONSAVEL':'Vendedor'})
    st.plotly_chart(fig_vend, use_container_width=True)
else:
    st.info("Coluna USUARIO_RESPONSAVEL não encontrada.")

# 4) Top Clientes
st.markdown("## Top 10 Clientes por Valor")
if 'NOME_CLIENTE' in df_filtered.columns:
    cli_df = df_filtered.groupby('NOME_CLIENTE').agg(TOTAL_PEDIDOS=('NUMERO_PEDIDO', lambda x: x.nunique() if x.dtype == 'O' else x.count()), VALOR_TOTAL=(VALUE_COL, 'sum')).reset_index().sort_values('VALOR_TOTAL', ascending=False)
    fig_cli = px.bar(cli_df.head(10), x='NOME_CLIENTE', y='VALOR_TOTAL', labels={'NOME_CLIENTE':'Cliente','VALOR_TOTAL':'Valor (R$)'})
    st.plotly_chart(fig_cli, use_container_width=True)
else:
    st.info("Coluna NOME_CLIENTE não encontrada.")

# 5) Valor por Política Comercial
st.markdown("## Valor por Política Comercial")
if 'POLITICA_COMERCIAL' in df_filtered.columns:
    pol_df = df_filtered.groupby('POLITICA_COMERCIAL').agg(TOTAL_PEDIDOS=('NUMERO_PEDIDO', lambda x: x.nunique() if x.dtype == 'O' else x.count()), VALOR_TOTAL=(VALUE_COL, 'sum')).reset_index().sort_values('VALOR_TOTAL', ascending=False)
    fig_pol = px.bar(pol_df.head(15), x='POLITICA_COMERCIAL', y='VALOR_TOTAL', labels={'POLITICA_COMERCIAL':'Política','VALOR_TOTAL':'Valor (R$)'})
    st.plotly_chart(fig_pol, use_container_width=True)
else:
    st.info("Coluna POLITICA_COMERCIAL não encontrada.")

# 6) Tabela de pedidos (detalhe) — com opção de baixar
st.markdown("## Tabela de Pedidos (detalhes filtrados)")
table_cols = ['DATA DO PEDIDO','NUMERO_PEDIDO','NOME_CLIENTE','USUARIO_RESPONSAVEL','ORIGEM_DO_PEDIDO','STATUS_PEDIDO', VALUE_COL]
existing_cols = [c for c in table_cols if c in df_filtered.columns]
st.dataframe(df_filtered[existing_cols].sort_values('DATA DO PEDIDO', ascending=False).reset_index(drop=True))

@st.cache_data
def convert_df_to_csv(df_in):
    return df_in.to_csv(index=False, sep=';').encode('utf-8')

csv = convert_df_to_csv(df_filtered[existing_cols])
st.download_button("🔽 Baixar CSV dos pedidos filtrados", data=csv, file_name="pedidos_filtrados.csv", mime="text/csv")

st.markdown("---")
st.markdown("**Observações / Instruções:**")
st.markdown("""
- Este app carrega o arquivo presente em: **/mnt/data/Relatório de Status de Pedido Copia.xlsx**.
- Para executá-lo localmente: instale dependências (`pip install streamlit pandas plotly openpyxl`) e rode:
```
streamlit run streamlit_dashboard.py
```
- Se quiser que eu gere uma versão com autenticação ou hospedagem (Heroku, Streamlit Cloud, etc.), me avise.
""")
