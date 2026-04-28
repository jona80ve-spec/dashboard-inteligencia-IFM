import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# =================================================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILO
# =================================================================
st.set_page_config(
    page_title="Sistema de Inteligencia IFM - Dashboard Corporativo",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.markdown("""
    <style>
    /* 1. Fondo y Métricas */
    .main {background-color: #0e1117;}
    .stMetric {background-color: #1e2130; padding: 20px; border-radius: 12px;}

    /* 2. Ocultar TODO lo que sobra (Header, Footer, Botones) */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    #viewerBadge {display: none;} /* Quita la corona roja */
    .stAppDeployButton {display: none;} /* Quita botones de despliegue */
    
    /* 3. Bloquear el menú lateral (quitar la X) */
    [data-testid="sidebar-close-button"], 
    [data-testid="stSidebarCollapseButton"] {
        display: none !important;
    }

    /* 4. Ajustar espacio para que se vea Pro */
    .block-container {padding-top: 0rem;}
    </style>
    """, unsafe_allow_html=True)
# =================================================================
# 2. RUTAS Y CARGA DE DATOS (CACHEADO)
# =================================================================
df = pd.read_excel('Dashboard IFM historico.xlsx')

@st.cache_data
def cargar_datos_maestros():
    """Carga las pestañas de Compilado y Ramos desde el Excel."""
    try:
        archivo = 'Dashboard IFM historico.xlsx'
        # 2. Cargamos las hojas usando ese nombre
        df_comp = pd.read_excel(archivo, sheet_name="Compilado", header=5)
        df_ram = pd.read_excel(archivo, sheet_name="PNC_Ramos", header=0)
        # Limpieza y normalización de meses para orden cronológico
        meses_orden = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 
                       'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
        for df in [df_comp, df_ram]:
            df.columns = [str(c).strip() for c in df.columns]
            if 'MES' in df.columns:
                df['MES'] = df['MES'].str.strip().str.capitalize()
                df['MES'] = pd.Categorical(df['MES'], categories=meses_orden, ordered=True)
        # Limpieza de espacios en nombres de columnas
        df_comp.columns = [str(c).strip() for c in df_comp.columns]
        df_ram.columns = [str(c).strip() for c in df_ram.columns]
        
        return df_comp, df_ram
    except Exception as e:
        st.error(f"Error crítico al leer el archivo Excel: {e}")
        return None, None

# =================================================================
# 3. FUNCIONES DE VISUALIZACIÓN Y FORMATEO
# =================================================================
def formato_ves(valor):
    """Convierte un número al formato: 127.939.090,53"""
    if pd.isna(valor): return "0,00"
    return "{:,.2f}".format(valor).replace(',', 'X').replace('.', ',').replace('X', '.')

def crear_indicador_tecnico(valor, titulo, color="#00d4ff"):
    """Crea un gráfico de medio círculo (Gauge) para indicadores de gestión."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=valor,
        number={'suffix': "%", 'font': {'size': 22, 'color': "white"}},
        title={'text': titulo, 'font': {'size': 14, 'color': "#9ea4b0"}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "gray"},
            'bar': {'color': color},
            'bgcolor': "rgba(0,0,0,0)",
            'borderwidth': 2,
            'bordercolor': "#3d4461",
            'steps': [
                {'range': [0, 100], 'color': 'rgba(255,255,255,0.03)'}
            ],
        }
    ))
    fig.update_layout(
        height=200, 
        margin=dict(l=25, r=25, t=50, b=10), 
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig

# =================================================================
# 4. LÓGICA PRINCIPAL DE LA APLICACIÓN
# =================================================================
df_compilado, df_ramos = cargar_datos_maestros()

if df_compilado is not None:
    # --- BARRA LATERAL (Panel de Control) ---
    st.sidebar.title("🎮 Panel de Control")
    st.sidebar.markdown("Configure los filtros de tiempo y navegación.")
    
    # Selectores de tiempo
    lista_años = sorted(df_compilado['AÑO'].unique(), reverse=True)
    ano_actual = st.sidebar.selectbox("Seleccione el Año", lista_años)
    
    lista_meses = df_compilado[df_compilado['AÑO'] == ano_actual]['MES'].unique()
    mes_actual = st.sidebar.selectbox("Seleccione el Mes", lista_meses)
    
    st.sidebar.markdown("---")
    
    # Selector de Sección
    menu = st.sidebar.radio(
        "Ir a la sección:",
        ["📊 Resultados Financieros", "📈 Serie Temporal", "🚗 Detalle por Ramos"],
        index=0
    )
    
    # Filtrado de Dataframes según selección
    df_act = df_compilado[(df_compilado['AÑO'] == ano_actual) & (df_compilado['MES'] == mes_actual)]
    df_ant = df_compilado[(df_compilado['AÑO'] == (ano_actual - 1)) & (df_compilado['MES'] == mes_actual)]

# =================================================================
# SECCIÓN A: RESULTADOS FINANCIEROS (CON MATRIZ DE 7 INDICADORES)
# =================================================================
    if menu == "📊 Resultados Financieros":
        st.title(f"📊 Análisis de Mercado: {mes_actual} {ano_actual}")
        
        # --- 1. CÁLCULOS DE MERCADO ---
        pnc_act = df_act['PrimasNetasCobradas'].sum()
        rtn_act = df_act['ResultadoTecnicoNeto'].sum()
        so_act = df_act['SaldodeOperaciones'].sum()
        pnc_ant = df_ant['PrimasNetasCobradas'].sum()
        so_ant = df_ant['SaldodeOperaciones'].sum()
        
        var_pnc = ((pnc_act / pnc_ant) - 1) * 100 if pnc_ant > 0 else 0
        var_so = ((so_act / so_ant) - 1) * 100 if so_ant != 0 else 0

        # --- 2. CABECERA DE KPIs ---
        k1, k2, k3 = st.columns(3)
        with k1: st.metric("Total Primas (PNC)", f"{formato_ves(pnc_act)} Bs.", f"{var_pnc:.2f}% vs AA")
        with k2: st.metric("Saldo de Operaciones", f"{formato_ves(so_act)} Bs.", f"{var_so:.2f}% vs AA")
        with k3: st.metric("Resultado Técnico Neto", f"{formato_ves(rtn_act)} Bs.")

        st.markdown("---")

        # --- 3. GAUGES DE MERCADO ---
        p_dev_t = df_act['Total GeneralPDev'].sum() if 'Total GeneralPDev' in df_act.columns else 0
        r_com_t = (df_act['Comisiones'].sum() / pnc_act * 100) if pnc_act > 0 else 0
        r_gaq_t = (df_act['GastosdeAdquision'].sum() / pnc_act * 100) if pnc_act > 0 else 0
        r_gad_t = (df_act['Gastosdeadministracion'].sum() / pnc_act * 100) if pnc_act > 0 else 0
        r_sin_t = (df_act['TotalGenralSI'].sum() / p_dev_t * 100) if p_dev_t > 0 else 0
        r_rea_t = (-(df_act['ResultadodelReaseguroCedido'].sum()) / p_dev_t * 100) if p_dev_t > 0 else 0
        ind_tc_t = r_com_t + r_gaq_t + r_gad_t + r_sin_t + r_rea_t
        
        # ICR Mercado: Inversiones / Reservas (Sin %)
        icr_mercado_val = (df_act['InversionesAptas'].sum() / df_act['ReservasTecnicas'].sum()) if df_act['ReservasTecnicas'].sum() > 0 else 0

        st.subheader("🎯 Indicadores de Gestión Técnica (Mercado)")
        g_cols = st.columns(7)
        
        # Lógica de colores para los Gauges
        color_tc = "#ff4b4b" if ind_tc_t > 100 else "#1A5F7A"
        color_icr = "#ff4b4b" if icr_mercado_val < 1 else "#00f5d4"
        
        metrics_data = [
            (r_com_t, "Comisiones", "#4e3b8c", "%"), 
            (r_gaq_t, "Gtos. Adq.", "#0077b6", "%"),
            (r_gad_t, "Gtos. Admin", "#00b4d8", "%"), 
            (r_sin_t, "Siniestralidad", "#5b84b1", "%"),
            (r_rea_t, "Costo Reaseg.", "#3d4461", "%"), 
            (ind_tc_t, "Tasa Comb.", color_tc, "%"),
            (icr_mercado_val, "ICR", color_icr, "") # ICR sin sufijo %
        ]
        
        for col, (val, lab, col_hex, suf) in zip(g_cols, metrics_data):
            with col: 
                fig_g = crear_indicador_tecnico(val, lab, col_hex)
                fig_g.update_traces(number={'suffix': suf})
                st.plotly_chart(fig_g, use_container_width=True)

        st.markdown("---")

# --- 4. MONITOR POR INSTITUCIÓN ---
        st.subheader("⚖️ Monitor de Gestión Técnica")
        modo_vista = st.radio("Filtro visual:", ["Top 10 por PNC", "Mercado Completo"], horizontal=True)

        # Preparación de Ranking
        df_ranking = df_act.copy()
        
        # 1. Cálculo de Cuota de Mercado Global (2 decimales)
        total_mercado_pnc = df_ranking['PrimasNetasCobradas'].sum()
        df_ranking['Mkt (%)'] = (df_ranking['PrimasNetasCobradas'] / total_mercado_pnc * 100).fillna(0)

        # 2. Ratios Técnicos
        df_ranking['Com (%)'] = (df_ranking['Comisiones'] / df_ranking['PrimasNetasCobradas'] * 100).fillna(0)
        df_ranking['IA (%)'] = (df_ranking['GastosdeAdquision'] / df_ranking['PrimasNetasCobradas'] * 100).fillna(0)
        df_ranking['IGA (%)'] = (df_ranking['Gastosdeadministracion'] / df_ranking['PrimasNetasCobradas'] * 100).fillna(0)
        df_ranking['SI (%)'] = (df_ranking['TotalGenralSI'] / df_ranking['Total GeneralPDev'] * 100).fillna(0)
        df_ranking['REA (%)'] = (-(df_ranking['ResultadodelReaseguroCedido']) / df_ranking['Total GeneralPDev'] * 100).fillna(0)
        df_ranking['TC (%)'] = df_ranking['Com (%)'] + df_ranking['IA (%)'] + df_ranking['IGA (%)'] + df_ranking['SI (%)'] + df_ranking['REA (%)']
        df_ranking['ICR_IND'] = (df_ranking['InversionesAptas'] / df_ranking['ReservasTecnicas']).fillna(0)

        # Columnas y orden
        cols_table = ['NombreCorto', 'PrimasNetasCobradas', 'Mkt (%)', 'Com (%)', 'IA (%)', 'IGA (%)', 'SI (%)', 'REA (%)', 'TC (%)', 'ICR_IND']
        df_ranking = df_ranking.sort_values('PrimasNetasCobradas', ascending=False).reset_index(drop=True)

        # --- FUNCIÓN DE ESTILO (Ajustada a 2 decimales y enumeración limpia) ---
        def style_matrix_clean(df):
            return df.style\
                .map(lambda x: 'color: #ff4b4b; font-weight: bold' if isinstance(x, (int, float)) and x > 100 else '', subset=['TC (%)'])\
                .map(lambda x: 'background-color: rgba(255, 75, 75, 0.15); color: #ff4b4b; font-weight: bold' if isinstance(x, (int, float)) and x < 1 else '', subset=['ICR_IND'])\
                .apply(lambda x: ['background-color: #1e2130; font-weight: bold; color: #90CAF9' if 'SUB-TOTAL' in str(x.NombreCorto) else '' for i in range(len(x))], axis=1)\
                .format({
                    'PrimasNetasCobradas': lambda x: formato_ves(x) if pd.notnull(x) else "",
                    'Mkt (%)': lambda x: f"{x:.2f}%" if pd.notnull(x) else "", # 2 decimales
                    'ICR_IND': lambda x: f"{x:.2f}" if pd.notnull(x) else "",
                    'TC (%)': lambda x: f"{x:.2f}%" if pd.notnull(x) else "", 
                    'SI (%)': lambda x: f"{x:.2f}%" if pd.notnull(x) else "", 
                    'Com (%)': lambda x: f"{x:.2f}%" if pd.notnull(x) else "",
                    'IA (%)': lambda x: f"{x:.2f}%" if pd.notnull(x) else "", 
                    'IGA (%)': lambda x: f"{x:.2f}%" if pd.notnull(x) else "", 
                    'REA (%)': lambda x: f"{x:.2f}%" if pd.notnull(x) else ""
                })

        paleta_azul_pro = ["#E3F2FD", "#90CAF9", "#2196F3", "#1565C0", "#0D47A1"]

        def render_bloque_filtrado(df_sub, titulo, altura=450):
            df_plot = df_sub[df_sub['PrimasNetasCobradas'] > 0].copy()
            
            # Sub-Total del bloque
            suma_pnc = df_sub['PrimasNetasCobradas'].sum()
            mkt_pct = (suma_pnc / total_mercado_pnc * 100) if total_mercado_pnc > 0 else 0
            
            fila_st = pd.DataFrame({'NombreCorto': [f'SUB-TOTAL {titulo.upper()}'], 'PrimasNetasCobradas': [suma_pnc], 'Mkt (%)': [mkt_pct]})
            for col in cols_table:
                if col not in fila_st.columns: fila_st[col] = None

            c_g, c_t = st.columns([0.25, 0.75])
            with c_g:
                st.write(f"**{titulo}: Primas**")
                if not df_plot.empty:
                    fig = px.bar(df_plot, x='PrimasNetasCobradas', y='NombreCorto', orientation='h', color='PrimasNetasCobradas', color_continuous_scale=paleta_azul_pro, custom_data=['Mkt (%)'])
                    fig.update_traces(hovertemplate="<b>%{y}</b><br>Primas: Bs. %{x:,.2f}<br>Cuota: %{customdata[0]:.2f}%<extra></extra>")
                    fig.update_layout(yaxis={'categoryorder':'total ascending'}, height=altura, showlegend=False, coloraxis_showscale=False, margin=dict(t=20, b=20))
                    st.plotly_chart(fig, use_container_width=True)
            
            with c_t:
                st.write(f"**Matriz Técnica ({titulo})**")
                # Ajuste de índices: Empresas 1-10, Sub-total vacío
                df_v = df_sub[cols_table].copy()
                df_v.index = range(1, len(df_v) + 1)
                
                fila_st_final = fila_st[cols_table].copy()
                fila_st_final.index = [""] 
                
                df_final = pd.concat([df_v, fila_st_final])
                st.dataframe(style_matrix_clean(df_final), use_container_width=True, height=altura)

        # Renderizado
        render_bloque_filtrado(df_ranking.head(10), "Top 10")
        if modo_vista == "Mercado Completo":
            if len(df_ranking) > 10:
                st.markdown("---")
                render_bloque_filtrado(df_ranking.iloc[10:20], "11-20")
            if len(df_ranking) > 20:
                st.markdown("---")
                render_bloque_filtrado(df_ranking.iloc[20:], "Resto del Mercado", altura=600)

# ======================================================================
# SECCIÓN: SERIE TEMPORAL (HISTÓRICO MENSUAL DINÁMICO Y COMPARATIVO)
# ======================================================================
    elif menu == "📈 Serie Temporal":
        st.title("📈 Evolución Histórica del Mercado (Valores Mensuales)")
        
        # 1. Preparación de datos base
        df_h = df_compilado.copy()
        df_h['Fecha'] = pd.to_datetime(df_h['Fecha'])
        df_h = df_h.sort_values(['AÑO', 'Fecha'])
        
        # 2. Agrupación Única: Incluimos TODAS las columnas necesarias para los cálculos posteriores
        cols_necesarias = [
            'PrimasNetasCobradas', 'Total GeneralPDev', 'TotalGenralSI', 
            'Comisiones', 'GastosdeAdquision', 'Gastosdeadministracion', 
            'ResultadodelReaseguroCedido', 'InversionesAptas', 'ReservasTecnicas',
            'ResultadoTecnicoNeto', 'SaldodeOperaciones'
        ]
        # Filtramos solo las que existen en el Excel para evitar errores en .agg
        dict_agg = {c: 'sum' for c in cols_necesarias if c in df_h.columns}
        df_timeline = df_h.groupby(['AÑO', 'Fecha'], as_index=False).agg(dict_agg)

        # 3. Lógica de Cálculos (Corrección de KeyErrors)
        # A. MONTOS
        # Usamos nombres consistentes para evitar el KeyError: 'PNC Mensual'
        df_timeline['PNC Mensual Real'] = df_timeline.groupby('AÑO')['PrimasNetasCobradas'].diff().fillna(df_timeline['PrimasNetasCobradas'])
        df_timeline['SI Monto'] = df_timeline['TotalGenralSI']
        df_timeline['Resultado Técnico Neto'] = df_timeline['ResultadoTecnicoNeto']
        df_timeline['Saldo Operaciones'] = df_timeline['SaldodeOperaciones']

        # B. RATIOS (Calculados sobre primas acumuladas originales)
        pnc_ref = df_timeline['PrimasNetasCobradas']
        pdev_ref = df_timeline['Total GeneralPDev']

        # Definimos los componentes antes de sumarlos para evitar KeyError: 'SI (%)'
        df_timeline['SI (%)'] = (df_timeline['TotalGenralSI'] / pdev_ref * 100).fillna(0)
        df_timeline['Com (%)'] = (df_timeline['Comisiones'] / pnc_ref * 100).fillna(0)
        df_timeline['IA (%)'] = (df_timeline['GastosdeAdquision'] / pnc_ref * 100).fillna(0)
        df_timeline['IGA (%)'] = (df_timeline['Gastosdeadministracion'] / pnc_ref * 100).fillna(0)
        df_timeline['REA (%)'] = (-(df_timeline['ResultadodelReaseguroCedido']) / pdev_ref * 100).fillna(0)
        
        # Índice Combinado (TC %)
        df_timeline['Índice Combinado (%)'] = (
            df_timeline['SI (%)'] + df_timeline['Com (%)'] + 
            df_timeline['IA (%)'] + df_timeline['IGA (%)'] + df_timeline['REA (%)']
        )
        
        # ICR: Manejo seguro para evitar KeyError: 'InversionesAptas'
        if 'InversionesAptas' in df_timeline.columns and 'ReservasTecnicas' in df_timeline.columns:
            df_timeline['ICR (Veces)'] = (df_timeline['InversionesAptas'] / df_timeline['ReservasTecnicas']).fillna(0)

# -------------------------------------------------------------
        # --- BLOQUE 1: COMPARATIVO INTERANUAL ---
# -------------------------------------------------------------
        ano_previo = ano_actual - 1
        st.subheader(f"📊 Comparativo de Crecimiento: {ano_actual} vs {ano_previo}")

        # Extraemos datos usando el nombre de columna correcto
        pnc_actual = df_timeline[df_timeline['AÑO'] == ano_actual][['Fecha', 'PNC Mensual Real']].copy()
        pnc_anterior = df_timeline[df_timeline['AÑO'] == ano_previo][['Fecha', 'PNC Mensual Real']].copy()

        if not pnc_actual.empty:
            nombres_meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 
                            'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
            pnc_actual['Mes_Nombre'] = pnc_actual['Fecha'].dt.month.apply(lambda x: nombres_meses[x-1])
            pnc_anterior['Mes_Nombre'] = pnc_anterior['Fecha'].dt.month.apply(lambda x: nombres_meses[x-1])

            col_act, col_ant = str(ano_actual), str(ano_previo)
            df_comp = pnc_actual[['Mes_Nombre', 'PNC Mensual Real']].rename(columns={'PNC Mensual Real': col_act}).merge(
                pnc_anterior[['Mes_Nombre', 'PNC Mensual Real']].rename(columns={'PNC Mensual Real': col_ant}),
                on='Mes_Nombre', how='left'
            ).fillna(0)

            df_comp['Mes_Nombre'] = pd.Categorical(df_comp['Mes_Nombre'], categories=nombres_meses, ordered=True)
            df_comp = df_comp.sort_values('Mes_Nombre')
            df_comp['Var%'] = ((df_comp[col_act] / df_comp[col_ant]) - 1) * 100
            
            # --- CÁLCULO DE FILA TOTAL ---
            total_act = df_comp[col_act].sum()
            total_ant = df_comp[col_ant].sum()
            total_var = ((total_act / total_ant) - 1) * 100 if total_ant != 0 else 0

            df_total = pd.DataFrame({
                'Mes_Nombre': ['TOTAL'],
                col_act: [total_act],
                col_ant: [total_ant],
                'Var%': [total_var]
            })
            
            # Unimos para la tabla
            df_comp_final = pd.concat([df_comp, df_total], ignore_index=True)

            # Visualización de tabla y gráfico azul
            col_t, col_g = st.columns([1, 1.6])
            with col_t:
                st.write("**📝 Detalle de Primaje Real**")
                def formato_latino(valor):
                    return "{:,.2f}".format(valor).replace(",", "X").replace(".", ",").replace("X", ".")
                
                # Mostramos df_comp_final con estilo resaltado para la última fila
                st.dataframe(
                    df_comp_final.style.format({
                        col_act: formato_latino, 
                        col_ant: formato_latino, 
                        'Var%': lambda x: f"{x:,.2f}%".replace(".", ",")
                    }).apply(lambda x: ['font-weight: bold; background-color: #1A5F7A' if x.name == df_comp_final.index[-1] else '' for i in x], axis=1), 
                    use_container_width=True, 
                    height=500, 
                    hide_index=True
                )

            with col_g:
                # El gráfico usa df_comp (SIN el total) para no distorsionar la escala
                fig_comp = go.Figure()
                fig_comp.add_trace(go.Bar(x=df_comp['Mes_Nombre'], y=df_comp[col_ant], name=f'PNC {ano_previo}', marker_color='#91C8E4'))
                fig_comp.add_trace(go.Bar(x=df_comp['Mes_Nombre'], y=df_comp[col_act], name=f'PNC {ano_actual}', marker_color='#1A5F7A'))
                fig_comp.add_trace(go.Scatter(x=df_comp['Mes_Nombre'], y=df_comp['Var%'], name='Var %', yaxis='y2', line=dict(color='#00D4FF', width=3)))
                fig_comp.update_layout(template="plotly_dark", height=400, yaxis2=dict(overlaying='y', side='right', showgrid=False), legend=dict(orientation="h", y=-0.2))
                st.plotly_chart(fig_comp, use_container_width=True)
            
        st.markdown("---")

        # -------------------------------------------------------------
        # --- BLOQUE 2: TENDENCIA HISTÓRICA ---
        # -------------------------------------------------------------
        st.subheader("📈 Tendencia Histórica de Largo Plazo")
        col_tipo, col_var = st.columns([0.3, 0.7])
        
        with col_tipo:
            tipo_h = st.radio("Ver tendencia de:", ["Montos Mensuales (Bs.)", "Ratios Técnicos (%)"], horizontal=True)
        
        with col_var:
            if tipo_h == "Montos Mensuales (Bs.)":
                opciones_h = ['PNC Mensual Real', 'SI Monto', 'Resultado Técnico Neto', 'Saldo Operaciones']
                labels = {'PNC Mensual Real': 'PNC (Desac.)', 'SI Monto': 'Siniestros', 'Resultado Técnico Neto': 'Res. Técnico', 'Saldo Operaciones': 'Saldo Operaciones'}
                default_h = ['PNC Mensual Real']
            else:
                opciones_h = ['SI (%)', 'Índice Combinado (%)', 'Com (%)', 'IA (%)', 'IGA (%)', 'REA (%)']
                if 'ICR (Veces)' in df_timeline.columns: opciones_h.append('ICR (Veces)')
                labels = {opt: opt for opt in opciones_h}
                default_h = ['SI (%)', 'Índice Combinado (%)']
            
            vars_seleccionadas = st.multiselect("Seleccione indicadores:", opciones_h, default=default_h)

        if vars_seleccionadas:
            fig_h = go.Figure()
            for v in vars_seleccionadas:
                fig_h.add_trace(go.Scatter(
                    x=df_timeline['Fecha'], y=df_timeline[v], name=labels.get(v, v),
                    mode='lines+markers', hovertemplate='<b>%{x|%B %Y}</b><br>'+labels.get(v,v)+': %{y:,.2f}<extra></extra>'
                ))
            fig_h.update_layout(template="plotly_dark", hovermode="x unified", xaxis=dict(rangeslider=dict(visible=True), type="date"))
            st.plotly_chart(fig_h, use_container_width=True)

    # -----------------------------------------------------------------
    # SECCIÓN: ANÁLISIS DINÁMICO DE RAMOS (RADIAL + INFOGRAFÍA + SERIE)
    # -----------------------------------------------------------------
    elif menu == "🚗 Detalle por Ramos":
        st.title(f"🚗 Detalle por Ramos: {mes_actual} {ano_actual}")
        
        # 1. Preparación de Datos y Filtros
        df_r_hist = df_ramos.copy()
        df_r_hist['Fecha'] = pd.to_datetime(df_r_hist['Fecha'])
        
        exclusiones = [
            'Cod', 'Nombre Empresa', 'NombreCorto', 'AÑO', 'MES', 
            'CIERRE AL', 'Acumulada Al', 'Fecha', 'NumerodeInscripciondelaEmpresa',
            'TOTAL PNC', 'TOTAL VIDA', 'TOTAL HCM', 'TOTAL NO VIDA', 
            'TOTAL PATRIMONIALES', 'TOTAL OBLIGACIONALES', 'NombreCorto']
        columnas_ramos = [c for c in df_r_hist.select_dtypes(include=['number']).columns 
                         if c not in exclusiones and "TOTAL" not in c.upper()]

# --- NIVEL 1: MIX DE MERCADO (CORRECCIÓN DE PORCENTAJES Y FORMATO) ---
        st.subheader(f"🌀 Composición por Ramos💼: Distribución Total Mercado 🌐 (Acumulado a {mes_actual})")
        
        df_mes_rad = df_r_hist[(df_r_hist['AÑO'] == ano_actual) & (df_r_hist['MES'] == mes_actual)].copy()
        
        if not df_mes_rad.empty:
            # 1. Preparación de datos
            all_data = df_mes_rad[columnas_ramos].sum().sort_values(ascending=False).reset_index()
            all_data.columns = ['Ramo', 'Monto']
            total_mercado = all_data['Monto'].sum()
            
            mask_fianza = all_data['Ramo'].str.upper() == 'FIANZA'
            top_6 = all_data[~mask_fianza].head(6).copy()
            nombres_top6 = top_6['Ramo'].tolist()
            monto_resto = all_data[~all_data['Ramo'].isin(nombres_top6)]['Monto'].sum()
            
            df_resto = pd.DataFrame({'Ramo': ['RESTO DE RAMOS'], 'Monto': [monto_resto]})
            data_don = pd.concat([top_6, df_resto]).sort_values(by='Monto', ascending=False)

            # --- CORRECCIÓN DE CÁLCULO ---
            # Calculamos el porcentaje real manualmente para evitar el error de 0.40%
            data_don['Porcentaje_Real'] = (data_don['Monto'] / total_mercado) * 100

            # 2. Paleta de colores Premium
            paleta_azul_premium = ["#004b93", "#007ab3", "#00a9e0", "#4ec3e0", "#9adbe8", "#c5e9f3", "#34495e"]

            # 3. Función para formato latino (1.000,00)
            def formato_latino(valor):
                return "{:,.2f}".format(valor).replace(",", "X").replace(".", ",").replace("X", ".")

            # 4. Creación del Gráfico Donut
            import plotly.express as px

            fig_donut = px.pie(
                data_don, 
                values='Monto', 
                names='Ramo', 
                hole=0.5, 
                template="plotly_dark",
                color_discrete_sequence=paleta_azul_premium
            )

            # 5. AJUSTE DE ETIQUETAS MANUALES
            # Usamos text para forzar el formato corregido
            data_don['Etiqueta_Texto'] = data_don.apply(
                lambda x: f"{x['Ramo']}<br>{formato_latino(x['Porcentaje_Real'])}%", axis=1
            )

            fig_donut.update_traces(
                direction='clockwise', 
                rotation=30,
                textposition='outside',
                text=data_don['Etiqueta_Texto'], # Aplicamos la etiqueta calculada
                textinfo='text',                 # Decimos a Plotly que use nuestro texto, no el suyo
                marker=dict(line=dict(color='#0e1117', width=2)),
                pull=[0.05 if i == 0 else 0 for i in range(len(data_don))],
                customdata=data_don['Monto'].apply(formato_latino),
                hovertemplate='<b>%{label}</b><br>Monto: %{customdata} Bs.<extra></extra>'
            )

            # 6. Texto central y márgenes
            fig_donut.update_layout(
                showlegend=False, 
                annotations=[dict(
                    text=f"{mes_actual}<br>{ano_actual}", 
                    x=0.5, y=0.5, 
                    font_size=20, 
                    showarrow=False, 
                    font_family="Arial Black",
                    font_color="white"
                )],
                margin=dict(t=80, b=80, l=20, r=20),
                height=600
            )

            st.plotly_chart(fig_donut, use_container_width=True)

# --- BLOQUE: EVOLUCIÓN MENSUAL (CON FORMATO Bs. Y FILTRO DINÁMICO) ---
        st.subheader(f"📊 Producción Real Mensual por Ramo ({ano_actual})")

        mapa_meses = {
            'Enero': 1, 'Febrero': 2, 'Marzo': 3, 'Abril': 4, 
            'Mayo': 5, 'Junio': 6, 'Julio': 7, 'Agosto': 8, 
            'Septiembre': 9, 'Octubre': 10, 'Noviembre': 11, 'Diciembre': 12
        }

        mes_corte_num = mapa_meses.get(mes_actual, 12)
        df_year = df_r_hist[df_r_hist['AÑO'] == ano_actual].copy()

        if not df_year.empty:
            df_year['MES_NUM'] = df_year['MES'].map(mapa_meses)
            df_evol = df_year.groupby(['MES_NUM', 'MES'])[columnas_ramos].sum().sort_index().reset_index()
            
            # Desacumular ramos
            df_mensual_real = df_evol[columnas_ramos].diff().fillna(df_evol[columnas_ramos].iloc[0])
                       
            total_pnc_mensual = df_mensual_real[columnas_ramos].sum(axis=1)
            
            # Identificar Top 6 (Excluyendo Fianza)
            ultima_foto_acum = df_evol.iloc[-1][columnas_ramos].sort_values(ascending=False)
            top_6_global = [r for r in ultima_foto_acum.index if r.upper() != 'FIANZA'][:6]
            
            # Otros = Total - Suma(Top 6)
            suma_top_6 = df_mensual_real[top_6_global].sum(axis=1)
            df_mensual_real['OTROS RAMOS'] = total_pnc_mensual - suma_top_6
            df_mensual_real['OTROS RAMOS'] = df_mensual_real['OTROS RAMOS'].clip(lower=0)
            
            df_mensual_real['MES'] = df_evol['MES']
            df_mensual_real['MES_NUM'] = df_evol['MES_NUM']

            # Filtro por mes seleccionado
            df_plot_mensual = df_mensual_real[df_mensual_real['MES_NUM'] <= mes_corte_num].copy()
            
            fig_barras = go.Figure()
            secuencia_azules = ['#D1E9F6', '#A1C8E4', '#71A8D4', '#4682A9', '#1A5F7A', '#00425A', '#002B36']
            
            for i, row in df_plot_mensual.iterrows():
                mes_iter = row['MES']
                ramos_x = top_6_global + ['OTROS RAMOS']
                valores_y = [row[r] for r in ramos_x]
                
                # --- APLICACIÓN DE FORMATO Bs. ---
                # Si el valor es > 0, aplicamos formato_ves y agregamos " Bs."
                etiquetas_bs = [f"{formato_ves(v)} Bs." if v > 0 else "" for v in valores_y]
                
                fig_barras.add_trace(go.Bar(
                    x=ramos_x,
                    y=valores_y,
                    name=mes_iter,
                    marker_color=secuencia_azules[i % len(secuencia_azules)],
                    text=etiquetas_bs, # Etiquetas con formato completo
                    textposition='outside',
                    cliponaxis=False, # Evita que se corte el texto arriba
                    hovertemplate="<b>" + mes_iter + "</b><br>Ramo: %{x}<br>Monto: %{y:,.2f} Bs.<extra></extra>"
                ))

            fig_barras.update_layout(
                template="plotly_dark",
                barmode='group',
                height=600, # Aumenté un poco la altura para que las etiquetas respiren
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                xaxis=dict(title="Ramos Principales", type='category'),
                yaxis=dict(title="Bolívares (Bs.)", showgrid=True, gridcolor="rgba(255,255,255,0.1)"),
                margin=dict(t=120) # Margen superior para los nombres de meses y etiquetas
            )

            st.plotly_chart(fig_barras, use_container_width=True)

        # --- NIVEL 2: INFOGRAFÍA TOP 3 POR EMPRESA (ACUMULADO YTD) ---
        st.subheader(f"🏆 Top 3 Ramos por Empresa (Acumulado a {mes_actual})")
        
        df_r_ytd = df_mes_rad.copy()
        df_r_ytd['Total_YTD'] = df_r_ytd[columnas_ramos].sum(axis=1)
        top_10_ytd = df_r_ytd.nlargest(10, 'Total_YTD')

        # Dibujamos en 2 filas de 5
        filas_infog = [top_10_ytd.iloc[0:5], top_10_ytd.iloc[5:10]]
        for fila_data in filas_infog:
            cols_inf = st.columns(5)
            for i, (idx, row) in enumerate(fila_data.iterrows()):
                with cols_inf[i]:
                    st.markdown(f"""<div style="background-color: #1b263b; color: white; padding: 8px; text-align: center; border-radius: 5px; font-size: 0.75em; font-weight: bold; min-height: 45px; display: flex; align-items: center; justify-content: center; border: 1px solid #415a77;">{row['NombreCorto']}</div>""", unsafe_allow_html=True)
                    top_3 = row[columnas_ramos].astype(float).nlargest(3)
                    colores_inf = ["#00509d", "#007ea7", "#00a8e8"]
                    for rank, (ramo, valor) in enumerate(top_3.items()):
                        pct = (valor / row['Total_YTD'] * 100) if row['Total_YTD'] > 0 else 0
                        st.markdown(f"""<div style="background-color: {colores_inf[rank]}; color: white; padding: 8px; border-radius: 3px; margin-top: 4px; text-align: center; border-left: 3px solid white;"><p style="margin: 0; font-size: 0.6em; font-weight: bold; line-height: 1.1;">{ramo}</p><p style="margin: 0; font-size: 0.75em; font-weight: bold;">{pct:.1f}%</p></div>""", unsafe_allow_html=True)
            st.write("") 

        st.markdown("---")

# --- NIVEL 2.1: INFOGRAFÍA 11 AL 20 ---
        st.subheader(f"🏆 Top 3 Ramos: Empresas 11 al 20")
        
        # Obtenemos las empresas del 11 al 20
        top_11_20_ytd = df_r_ytd.nlargest(20, 'Total_YTD').iloc[10:20]

        if not top_11_20_ytd.empty:
            filas_11_20 = [top_11_20_ytd.iloc[0:5], top_11_20_ytd.iloc[5:10]]
            for fila_data in filas_11_20:
                cols_inf = st.columns(5)
                for i, (idx, row) in enumerate(fila_data.iterrows()):
                    with cols_inf[i]:
                        st.markdown(f"""<div style="background-color: #1b263b; color: white; padding: 8px; text-align: center; border-radius: 5px; font-size: 0.75em; font-weight: bold; min-height: 45px; display: flex; align-items: center; justify-content: center; border: 1px solid #415a77;">{row['NombreCorto']}</div>""", unsafe_allow_html=True)
                        top_3 = row[columnas_ramos].astype(float).nlargest(3)
                        colores_inf = ["#00509d", "#007ea7", "#00a8e8"]
                        for rank, (ramo, valor) in enumerate(top_3.items()):
                            pct = (valor / row['Total_YTD'] * 100) if row['Total_YTD'] > 0 else 0
                            st.markdown(f"""<div style="background-color: {colores_inf[rank]}; color: white; padding: 8px; border-radius: 3px; margin-top: 4px; text-align: center; border-left: 3px solid white;"><p style="margin: 0; font-size: 0.6em; font-weight: bold; line-height: 1.1;">{ramo}</p><p style="margin: 0; font-size: 0.75em; font-weight: bold;">{pct:.1f}%</p></div>""", unsafe_allow_html=True)
                st.write("") 

        st.markdown("---")

        # --- NIVEL 2.2: INFOGRAFÍA RESTO DEL MERCADO (DENTRO DE EXPANDER) ---
        st.subheader(f"🏆 Top 3 Ramos: Resto del Mercado")
        
        # Obtenemos de la 21 en adelante
        resto_ytd = df_r_ytd.nlargest(len(df_r_ytd), 'Total_YTD').iloc[20:]

        if not resto_ytd.empty:
            with st.expander("Ver detalle de las demás empresas"):
                # Calculamos cuántas filas de 5 necesitamos
                import math
                num_empresas = len(resto_ytd)
                num_filas = math.ceil(num_empresas / 5)
                
                for f in range(num_filas):
                    fila_data = resto_ytd.iloc[f*5 : (f+1)*5]
                    cols_inf = st.columns(5)
                    for i, (idx, row) in enumerate(fila_data.iterrows()):
                        with cols_inf[i]:
                            st.markdown(f"""<div style="background-color: #1b263b; color: white; padding: 8px; text-align: center; border-radius: 5px; font-size: 0.75em; font-weight: bold; min-height: 45px; display: flex; align-items: center; justify-content: center; border: 1px solid #415a77;">{row['NombreCorto']}</div>""", unsafe_allow_html=True)
                            top_3 = row[columnas_ramos].astype(float).nlargest(3)
                            colores_inf = ["#00509d", "#007ea7", "#00a8e8"]
                            for rank, (ramo, valor) in enumerate(top_3.items()):
                                pct = (valor / row['Total_YTD'] * 100) if row['Total_YTD'] > 0 else 0
                                st.markdown(f"""<div style="background-color: {colores_inf[rank]}; color: white; padding: 8px; border-radius: 3px; margin-top: 4px; text-align: center; border-left: 3px solid white;"><p style="margin: 0; font-size: 0.6em; font-weight: bold; line-height: 1.1;">{ramo}</p><p style="margin: 0; font-size: 0.75em; font-weight: bold;">{pct:.1f}%</p></div>""", unsafe_allow_html=True)
                    st.write("")

# --- NIVEL 3: SERIE TEMPORAL POR RAMO (ESTILO COMPARATIVO CON DEFAULT) ---
        st.subheader("🔍 Evolución Histórica Mensual")
        
        # 1. Definimos los ramos predeterminados
        ramos_default = ["HCM INDIVIDUAL", "HCM COLECTIVO", "AUTO CASCO"]
        
        # Validamos que existan en tus datos para evitar errores
        seleccion_inicial = [r for r in ramos_default if r in columnas_ramos]

        # 2. Multiselect con la configuración de inicio
        ramos_sel = st.multiselect(
            "Seleccione los ramos para comparar la evolución real mensual:", 
            options=sorted(columnas_ramos),
            default=seleccion_inicial # <--- Aquí cargan tus 3 ramos automáticamente
        )

        if ramos_sel:
            fig_linea = go.Figure()
            
            # Ordenar por fecha para que las líneas no zigzagueen
            df_r_hist = df_r_hist.sort_values(['NombreCorto', 'Fecha'])

            # Colores vivos para contraste sobre fondo oscuro
            colores_vivos = ['#00d4ff', '#ff4b4b', '#00ff85', '#ffeb3b', '#e91e63', '#ffffff']

            for i, ramo in enumerate(ramos_sel):
                # Cálculo del valor mensual (Resta del acumulado)
                col_temp = f"Temp_{ramo}"
                df_r_hist[col_temp] = df_r_hist.groupby(['NombreCorto', 'AÑO'])[ramo].diff().fillna(df_r_hist[ramo])
                
                # Agrupar por fecha para el total mercado
                serie_ramo = df_r_hist.groupby('Fecha', as_index=False)[col_temp].sum().sort_values('Fecha')

                # Crear la línea (Scatter con markers)
                fig_linea.add_trace(go.Scatter(
                    x=serie_ramo['Fecha'], 
                    y=serie_ramo[col_temp],
                    mode='lines+markers',
                    name=ramo,
                    line=dict(width=3, color=colores_vivos[i % len(colores_vivos)]),
                    marker=dict(size=8),
                    # Formato del texto al pasar el mouse
                    hovertemplate="%{y:,.2f} Bs.<extra></extra>"
                ))

            # 4. Diseño del gráfico (Layout - El estilo que te gusta)
            fig_linea.update_layout(
                template="plotly_dark", 
                height=500,
                # Muestra todos los valores al pasar el mouse
                hovermode="x unified",
                hoverlabel=dict(bgcolor="rgba(33, 33, 33, 0.9)", font_size=13),
                legend=dict(
                    orientation="h", 
                    yanchor="bottom", y=1.02, 
                    xanchor="center", x=0.5
                ),
                xaxis=dict(
                    title="Periodo Mensual",
                    showgrid=False,
                    rangeslider=dict(visible=True) # El slider de tiempo abajo
                ),
                yaxis=dict(
                    title="Bolívares (Bs.)", 
                    showgrid=True, 
                    gridcolor="rgba(255,255,255,0.1)",
                    tickformat=",." # Formato de miles con comas
                ),
                margin=dict(t=100, l=10, r=10, b=10)
            )
            
            st.plotly_chart(fig_linea, use_container_width=True)
        else:
            st.info("💡 Por favor, selecciona uno o más ramos para generar la comparativa temporal.")
# =================================================================
# 5. MENSAJE DE PIE DE PÁGINA O ERROR
# =================================================================
else:
    st.warning("⚠️ No se pudieron cargar los datos. Verifique la ruta del archivo Excel y que no esté abierto por otro programa.")

st.sidebar.markdown("---")
st.sidebar.caption("🏢🛡️Sistema de Inteligencia IFM - Dashboard Corporativo")
