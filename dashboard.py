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
    /* 1. Fondo y Métricas (Mantenemos tu estilo Pro) */
    .main {background-color: #0e1117;}
    .stMetric {background-color: #1e2130; padding: 20px; border-radius: 12px;}

    /* 2. Ocultar elementos innecesarios */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    #viewerBadge {display: none;}
    .stAppDeployButton {display: none;}

    /* 3. MENÚ INTELIGENTE: Bloqueado en PC, funcional en Móvil */
    @media (min-width: 768px) {
        [data-testid="sidebar-close-button"],
        [data-testid="stSidebarCollapseButton"] {
            display: none !important;
        }
    }

    /* 4. Ajustar espacio superior */
    .block-container {padding-top: 1rem;}
    </style>
""", unsafe_allow_html=True)
# --- INICIALIZACIÓN DE SESSION STATE (Al inicio del archivo) ---
if 'empresa_memoria' not in st.session_state:
    # Definimos la empresa inicial por defecto
    st.session_state.empresa_memoria = "MERCANTIL C.A."
def actualizar_empresa():
    st.session_state.empresa_memoria = st.session_state.selector_empresa

# =================================================================
# 2. RUTAS Y CARGA DE DATOS (CACHEADO)
# =================================================================
RUTA_EXCEL = "Dashboard IFM historico.xlsx"

@st.cache_data
def cargar_datos_maestros():
    """Carga las pestañas de Compilado y Ramos desde el Excel."""
    try:
        # Carga pestaña Compilado (General)
        df_comp = pd.read_excel(RUTA_EXCEL, sheet_name="Compilado", header=5)
        # Carga pestaña PNC_Ramos (Detallado por ramos)
        df_ram = pd.read_excel(RUTA_EXCEL, sheet_name="PNC_Ramos", header=0)
        df_tas = pd.read_excel(RUTA_EXCEL, sheet_name="TasasBCV", header=0)
        
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
        df_tas.columns = [str(c).strip() for c in df_tas.columns]
        return df_comp, df_ram, df_tas
    except Exception as e:
        st.error(f"Error crítico al leer el archivo Excel: {e}")
        return None, None, None

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
df_compilado, df_ramos, df_tas = cargar_datos_maestros()
meses_orden = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 
               'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
if df_compilado is not None:
# --- BARRA LATERAL (Panel de Control) ---
    st.sidebar.title("🎮 Panel de Control")

    # 1. Selector de Año
    lista_años = sorted(df_compilado['AÑO'].unique(), reverse=True)
    ano_actual = st.sidebar.selectbox("Seleccione el Año", lista_años, index=0)

    # 2. Preparar lista de meses para el año seleccionado
    meses_disponibles = df_compilado[df_compilado['AÑO'] == ano_actual]['MES'].unique()
    lista_meses = [m for m in meses_orden if m in meses_disponibles]

    # --- LÓGICA DE PERSISTENCIA DEL MES (MEMORIA) ---
    if 'mes_memoria' not in st.session_state:
        # La primera vez, apuntamos al último mes disponible (ej. Marzo)
        idx_inicio = len(lista_meses) - 1 if lista_meses else 0
    else:
        # Si cambiamos de año, intentamos encontrar el mes que ya teníamos
        if st.session_state['mes_memoria'] in lista_meses:
            idx_inicio = lista_meses.index(st.session_state['mes_memoria'])
        else:
            # Si el mes no existe en el nuevo año, vamos al último disponible
            idx_inicio = len(lista_meses) - 1 if lista_meses else 0

    mes_actual = st.sidebar.selectbox(
        "Seleccione el Mes", 
        lista_meses, 
        index=idx_inicio
    )

    # Actualizamos la memoria con la selección actual
    st.session_state['mes_memoria'] = mes_actual

    moneda = st.sidebar.radio("Seleccione Tipo de Moneda", ["VES", "USD"])
    st.sidebar.markdown("---")
    # Selector de Sección
    menu = st.sidebar.radio(
        "Ir a la sección:",
        ["📊 Resultados Financieros", "📈 Serie Temporal", "🚗 Detalle por Ramos", "🏢 Resumen por Empresa"],
        index=0
    )
    
    # Filtrado de Dataframes según selección
    df_act = df_compilado[(df_compilado['AÑO'] == ano_actual) & (df_compilado['MES'] == mes_actual)]
    df_ant = df_compilado[(df_compilado['AÑO'] == (ano_actual - 1)) & (df_compilado['MES'] == mes_actual)]
    total_mercado_pnc = df_act['PrimasNetasCobradas'].sum()

# =================================================================
# SECCIÓN A: RESULTADOS FINANCIEROS (CON MATRIZ DE 7 INDICADORES)
# =================================================================
    if menu == "📊 Resultados Financieros":
        st.title(f"📊 Análisis de Mercado: {mes_actual} {ano_actual}")
        
        simbolo = "$" if moneda == "USD" else "Bs."

        # --- 1. VALORES BASE EN BS (Para Gauges y Fallback) ---
        pnc_act_bs = df_act['PrimasNetasCobradas'].sum()
        so_act_bs = df_act['SaldodeOperaciones'].sum()
        rtn_act_bs = df_act['ResultadoTecnicoNeto'].sum()
        si_act_bs = df_act['TotalGenralSI'].sum()
        
        # Inicializamos variables de visualización por defecto (en Bs.)
        pnc_vis = pnc_act_bs
        pnc_comp_aa = df_ant['PrimasNetasCobradas'].sum() if not df_ant.empty else 0
        so_vis = so_act_bs
        so_comp_aa = df_ant['SaldodeOperaciones'].sum() if not df_ant.empty else 0
        rtn_vis = rtn_act_bs
        si_vis = si_act_bs

        # --- 2. LÓGICA DE DOLARIZACIÓN (ESPEJO DE LA VISTA INDIVIDUAL) ---
        if moneda == "USD":
            try:
                # Función segura para obtener tasas
                def get_tasa_segura(ano, mes_nombre, tipo):
                    m_clean = str(mes_nombre).strip().capitalize()
                    reg = df_tas[(df_tas['AÑO'] == ano) & (df_tas['MES'].str.strip().str.capitalize() == m_clean)]
                    col = 'Tasa_Cierre' if tipo == 'cierre' else 'TasaPromedio'
                    # Buscamos la columna de forma flexible por si acaso
                    col_real = next((c for c in reg.columns if col.upper() in c.upper()), None)
                    return reg[col_real].values[0] if col_real and not reg.empty else 1.0

                # --- DESACUMULACIÓN MENSUAL DEL MERCADO ---
                idx_actual = meses_orden.index(mes_actual.capitalize())
                meses_a_recorrer = meses_orden[:idx_actual + 1]
                
                pnc_usd_mercado = 0.0
                pnc_usd_mercado_aa = 0.0
                acum_bs_prev = 0.0
                acum_bs_prev_aa = 0.0

                for m in meses_a_recorrer:
                    # Mercado Año Actual
                    df_m = df_compilado[(df_compilado['AÑO'] == ano_actual) & (df_compilado['MES'].str.capitalize() == m.capitalize())]
                    bs_m = df_m['PrimasNetasCobradas'].sum()
                    t_p = get_tasa_segura(ano_actual, m, 'promedio')
                    pnc_usd_mercado += ((bs_m - acum_bs_prev) / t_p)
                    acum_bs_prev = bs_m

                    # Mercado Año Anterior
                    df_m_aa = df_compilado[(df_compilado['AÑO'] == ano_actual - 1) & (df_compilado['MES'].str.capitalize() == m.capitalize())]
                    bs_m_aa = df_m_aa['PrimasNetasCobradas'].sum()
                    t_p_aa = get_tasa_segura(ano_actual - 1, m, 'promedio')
                    pnc_usd_mercado_aa += ((bs_m_aa - acum_bs_prev_aa) / t_p_aa)
                    acum_bs_prev_aa = bs_m_aa

                # Tasas de Cierre para Saldos y Resultados
                t_cierre_act = get_tasa_segura(ano_actual, mes_actual, 'cierre')
                t_cierre_aa = get_tasa_segura(ano_actual - 1, mes_actual, 'cierre')

                # Asignación final para los Metrics
                pnc_vis = pnc_usd_mercado
                pnc_comp_aa = pnc_usd_mercado_aa
                so_vis = so_act_bs / t_cierre_act
                so_comp_aa = so_comp_aa / t_cierre_aa
                rtn_vis = rtn_act_bs / t_cierre_act
                si_vis = si_act_bs / t_cierre_act

            except Exception as e:
                st.sidebar.error(f"Error en conversión USD Mercado: {e}")

        # --- 3. CÁLCULO DE VARIACIONES ---
        var_pnc = ((pnc_vis / pnc_comp_aa) - 1) * 100 if pnc_comp_aa > 0 else 0
        var_so = ((so_vis / so_comp_aa) - 1) * 100 if so_comp_aa != 0 else 0

        # --- 4. RENDERIZADO DE KPIs ---
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric("Total Primas (PNC)", f"{formato_ves(pnc_vis)} {simbolo}", f"{var_pnc:.2f}% vs AA")
        with c2: st.metric("Saldo de Operaciones", f"{formato_ves(so_vis)} {simbolo}", f"{var_so:.2f}% vs AA")
        with c3: st.metric("Resultado Técnico Neto", f"{formato_ves(rtn_vis)} {simbolo}")
        with c4: st.metric("Siniestros Incurridos", f"{formato_ves(si_vis)} {simbolo}")

        st.markdown("---")

        # --- 3. GAUGES DE MERCADO ---
        p_dev_t = df_act['Total GeneralPDev'].sum() if 'Total GeneralPDev' in df_act.columns else 0
        r_com_t = (df_act['Comisiones'].sum() / pnc_act_bs * 100) if pnc_act_bs > 0 else 0
        r_gaq_t = (df_act['GastosdeAdquision'].sum() / pnc_act_bs * 100) if pnc_act_bs > 0 else 0
        r_gad_t = (df_act['Gastosdeadministracion'].sum() / pnc_act_bs * 100) if pnc_act_bs > 0 else 0
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

# --- 4. MONITOR POR INSTITUCIÓN (DESMENSUALIZADO Y DINÁMICO) ---
        st.subheader("⚖️ Monitor de Gestión Técnica")
        modo_vista = st.radio("Filtro visual:", ["Top 10 por PNC", "Mercado Completo"], horizontal=True)
        
        simbolo = "$" if moneda == "USD" else "Bs."

        # 1. Preparación de Ranking (Copia de seguridad)
        df_ranking = df_act.copy()
        
        # --- LÓGICA DE DESMENSUALIZACIÓN PNC (Espejo de Fila 1) ---
        if moneda == "USD":
            try:
                idx_actual = meses_orden.index(mes_actual.capitalize())
                meses_a_recorrer = meses_orden[:idx_actual + 1]
                pnc_usd_final = {}

                # Procesamos cada empresa del mercado
                for empresa in df_ranking['NombreCorto'].unique():
                    pnc_acum_usd = 0.0
                    pnc_bs_previo = 0.0
                    
                    for m in meses_a_recorrer:
                        # Buscamos dato histórico
                        f_h = df_compilado[
                            (df_compilado['AÑO'] == ano_actual) & 
                            (df_compilado['MES'].str.strip().str.capitalize() == m.capitalize()) & 
                            (df_compilado['NombreCorto'] == empresa)
                        ]
                        
                        if not f_h.empty:
                            bs_m = f_h['PrimasNetasCobradas'].values[0]
                            # Obtener tasa promedio segura
                            reg_t = df_tas[(df_tas['AÑO'] == ano_actual) & (df_tas['MES'].str.strip().str.capitalize() == m.capitalize())]
                            # Buscamos columna que contenga 'PROMEDIO'
                            col_prom = next((c for c in reg_t.columns if 'PROMEDIO' in c.upper()), None)
                            t_p = reg_t[col_prom].values[0] if col_prom and not reg_t.empty else 1.0
                            
                            # Desmensualizar: (Acumulado Mes Actual - Acumulado Mes Anterior) / Tasa Promedio
                            pnc_acum_usd += (bs_m - pnc_bs_previo) / t_p
                            pnc_bs_previo = bs_m
                    
                    pnc_usd_final[empresa] = pnc_acum_usd

                # Inyectamos los valores USD en el ranking
                df_ranking['PrimasNetasCobradas'] = df_ranking['NombreCorto'].map(pnc_usd_final)
            except Exception as e:
                st.error(f"Error en desmensualización: {e}")

        # 2. Cálculos de Participación y Ratios Técnicos
        total_mkt_pnc = df_ranking['PrimasNetasCobradas'].sum()
        df_ranking['Mkt (%)'] = (df_ranking['PrimasNetasCobradas'] / total_mkt_pnc * 100).fillna(0)

        # Los ratios se calculan sobre df_act (Bs originales) para evitar errores de redondeo cambiario
        df_ranking['Com (%)'] = (df_act['Comisiones'] / df_act['PrimasNetasCobradas'] * 100).fillna(0)
        df_ranking['IA (%)'] = (df_act['GastosdeAdquision'] / df_act['PrimasNetasCobradas'] * 100).fillna(0)
        df_ranking['IGA (%)'] = (df_act['Gastosdeadministracion'] / df_act['PrimasNetasCobradas'] * 100).fillna(0)
        df_ranking['SI (%)'] = (df_act['TotalGenralSI'] / df_act['Total GeneralPDev'] * 100).fillna(0)
        df_ranking['REA (%)'] = (-(df_act['ResultadodelReaseguroCedido']) / df_act['Total GeneralPDev'] * 100).fillna(0)
        df_ranking['TC (%)'] = df_ranking['Com (%)'] + df_ranking['IA (%)'] + df_ranking['IGA (%)'] + df_ranking['SI (%)'] + df_ranking['REA (%)']
        df_ranking['ICR_IND'] = (df_act['InversionesAptas'] / df_act['ReservasTecnicas']).fillna(0)

        cols_table = ['NombreCorto', 'PrimasNetasCobradas', 'Mkt (%)', 'Com (%)', 'IA (%)', 'IGA (%)', 'SI (%)', 'REA (%)', 'TC (%)', 'ICR_IND']
        df_ranking = df_ranking.sort_values('PrimasNetasCobradas', ascending=False).reset_index(drop=True)

        # --- FUNCIÓN DE ESTILO ---
        def style_matrix_clean(df):
            def format_val(val, fmt="{:.2f}%"):
                if val is None or pd.isna(val) or val == "": return ""
                return fmt.format(val) if isinstance(val, (int, float)) else str(val)

            return df.style\
                .map(lambda x: 'color: #ff4b4b; font-weight: bold' if isinstance(x, (int, float)) and x > 100 else '', subset=['TC (%)'])\
                .map(lambda x: 'background-color: rgba(255, 75, 75, 0.15); color: #ff4b4b; font-weight: bold' if isinstance(x, (int, float)) and x < 1 else '', subset=['ICR_IND'])\
                .format({
                    'PrimasNetasCobradas': lambda x: f"{formato_ves(x)} {simbolo}",
                    'Mkt (%)': lambda x: format_val(x),
                    'ICR_IND': lambda x: format_val(x, "{:.2f}"),
                    'TC (%)': lambda x: format_val(x), 
                    'SI (%)': lambda x: format_val(x), 
                    'Com (%)': lambda x: format_val(x),
                    'IA (%)': lambda x: format_val(x), 
                    'IGA (%)': lambda x: format_val(x), 
                    'REA (%)': lambda x: format_val(x)
                })

        paleta_azul_pro = ["#E3F2FD", "#90CAF9", "#2196F3", "#1565C0", "#0D47A1"]

        # --- FUNCIÓN DE RENDERIZADO ACTUALIZADA ---
        def render_bloque_filtrado(df_sub, titulo, inicio_ranking, altura=500):
            df_plot = df_sub[df_sub['PrimasNetasCobradas'] > 0].copy()
            suma_pnc = df_sub['PrimasNetasCobradas'].sum()
            mkt_pct_bloque = (suma_pnc / total_mkt_pnc * 100) if total_mkt_pnc > 0 else 0
            
            df_resumen = pd.DataFrame({
                ' ': [f'SUB-TOTAL {titulo.upper()}'],
                'PrimasNetasCobradas': [f"{formato_ves(suma_pnc)} {simbolo}"],
                'Mkt (%)': [f"{mkt_pct_bloque:.2f}%"]
            })
            df_resumen.index = [""] 

            c_g, c_t = st.columns([0.25, 0.75])
            with c_g:
                st.write(f"**{titulo}: Primas**")
                fig = px.bar(df_plot, x='PrimasNetasCobradas', y='NombreCorto', orientation='h', 
                             color='PrimasNetasCobradas', color_continuous_scale=paleta_azul_pro, 
                             custom_data=['Mkt (%)'])
                fig.update_traces(hovertemplate=f"<b>%{{y}}</b><br>Primas: {simbolo} %{{x:,.2f}}<br>Participación: %{{customdata[0]:.2f}}%<extra></extra>")
                fig.update_layout(yaxis={'categoryorder':'total ascending'}, height=altura, showlegend=False, 
                                  coloraxis_showscale=False, margin=dict(t=20, b=20))
                st.plotly_chart(fig, use_container_width=True)
            
            with c_t:
                st.write(f"**Matriz Técnica ({titulo})**")
                df_v = df_sub[cols_table].copy()
                df_v.index = range(inicio_ranking, inicio_ranking + len(df_v))
                st.dataframe(style_matrix_clean(df_v), use_container_width=True, height=altura - 95)
                st.table(df_resumen)

        # --- EJECUCIÓN DE BLOQUES ---
        render_bloque_filtrado(df_ranking.head(10), "Top 10", inicio_ranking=1)

        if modo_vista == "Mercado Completo":
            if len(df_ranking) > 10:
                st.markdown("---")
                render_bloque_filtrado(df_ranking.iloc[10:20], "11-20", inicio_ranking=11)
            if len(df_ranking) > 20:
                st.markdown("---")
                render_bloque_filtrado(df_ranking.iloc[20:], "Resto del Mercado", inicio_ranking=21, altura=600)

# ======================================================================
# SECCIÓN: SERIE TEMPORAL (HISTÓRICO MENSUAL DOLARIZADO)
# ======================================================================
    elif menu == "📈 Serie Temporal":
        st.title("📈 Evolución Histórica del Mercado (Dolarización Dinámica)")
        
        simbolo = "$" if moneda == "USD" else "Bs."

        # 1. Preparación de datos base
        df_h = df_compilado.copy()
        df_h['Fecha'] = pd.to_datetime(df_h['Fecha'])
        df_h = df_h.sort_values(['AÑO', 'Fecha'])
        
        # 2. Agrupación por Fecha para el Mercado Total
        cols_necesarias = [
            'PrimasNetasCobradas', 'Total GeneralPDev', 'TotalGenralSI', 
            'Comisiones', 'GastosdeAdquision', 'Gastosdeadministracion', 
            'ResultadodelReaseguroCedido', 'InversionesAptas', 'ReservasTecnicas',
            'ResultadoTecnicoNeto', 'SaldodeOperaciones'
        ]
        dict_agg = {c: 'sum' for c in cols_necesarias if c in df_h.columns}
        df_timeline = df_h.groupby(['AÑO', 'Fecha'], as_index=False).agg(dict_agg)

        # 3. LÓGICA DE CONVERSIÓN Y DESACUMULACIÓN
        if moneda == "USD":
            try:
                # Diccionario para asegurar match con nombres de meses en df_tas
                meses_map = {
                    1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio',
                    7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
                }

                def obtener_tasa_h(row, tipo='promedio'):
                    m_nombre = meses_map[row['Fecha'].month]
                    reg_t = df_tas[(df_tas['AÑO'] == row['AÑO']) & (df_tas['MES'].str.strip().str.capitalize() == m_nombre.capitalize())]
                    
                    if reg_t.empty:
                        return 1.0
                    
                    # Búsqueda flexible para 'TasaPromedio' o 'Tasa_Cierre'
                    termino = 'PROMEDIO' if tipo == 'promedio' else 'CIERRE'
                    col_real = next((c for c in reg_t.columns if termino in c.upper()), None)
                    
                    if col_real:
                        val = reg_t[col_real].values[0]
                        return val if val > 0 else 1.0
                    return 1.0

                # --- A. PNC MENSUAL (Flujo: Usando TasaPromedio) ---
                df_timeline['PNC_Mensual_Bs'] = df_timeline.groupby('AÑO')['PrimasNetasCobradas'].diff().fillna(df_timeline['PrimasNetasCobradas'])
                df_timeline['Tasa_P'] = df_timeline.apply(lambda r: obtener_tasa_h(r, 'promedio'), axis=1)
                df_timeline['PNC Mensual Real'] = df_timeline['PNC_Mensual_Bs'] / df_timeline['Tasa_P']

                # --- B. MONTOS DE SALDO (Stock: Usando Tasa_Cierre) ---
                df_timeline['Tasa_C'] = df_timeline.apply(lambda r: obtener_tasa_h(r, 'cierre'), axis=1)
                df_timeline['SI Monto'] = df_timeline['TotalGenralSI'] / df_timeline['Tasa_C']
                df_timeline['Resultado Técnico Neto'] = df_timeline['ResultadoTecnicoNeto'] / df_timeline['Tasa_C']
                df_timeline['Saldo Operaciones'] = df_timeline['SaldodeOperaciones'] / df_timeline['Tasa_C']
                
            except Exception as e:
                st.error(f"Error en conversión cambiaria: {e}")
        else:
            # Lógica en Bolívares
            df_timeline['PNC Mensual Real'] = df_timeline.groupby('AÑO')['PrimasNetasCobradas'].diff().fillna(df_timeline['PrimasNetasCobradas'])
            df_timeline['SI Monto'] = df_timeline['TotalGenralSI']
            df_timeline['Resultado Técnico Neto'] = df_timeline['ResultadoTecnicoNeto']
            df_timeline['Saldo Operaciones'] = df_timeline['SaldodeOperaciones']

        # 4. RATIOS TÉCNICOS (Base Bs. original)
        df_timeline['SI (%)'] = (df_timeline['TotalGenralSI'] / df_timeline['Total GeneralPDev'] * 100).fillna(0)
        df_timeline['Com (%)'] = (df_timeline['Comisiones'] / df_timeline['PrimasNetasCobradas'] * 100).fillna(0)
        df_timeline['IA (%)'] = (df_timeline['GastosdeAdquision'] / df_timeline['PrimasNetasCobradas'] * 100).fillna(0)
        df_timeline['IGA (%)'] = (df_timeline['Gastosdeadministracion'] / df_timeline['PrimasNetasCobradas'] * 100).fillna(0)
        df_timeline['REA (%)'] = (-(df_timeline['ResultadodelReaseguroCedido']) / df_timeline['Total GeneralPDev'] * 100).fillna(0)
        df_timeline['Índice Combinado (%)'] = df_timeline['SI (%)'] + df_timeline['Com (%)'] + df_timeline['IA (%)'] + df_timeline['IGA (%)'] + df_timeline['REA (%)']

# -------------------------------------------------------------
        # --- BLOQUE 1: COMPARATIVO INTERANUAL (FILTRADO POR MES) ---
        # -------------------------------------------------------------
        ano_previo = ano_actual - 1
        st.subheader(f"📊 Crecimiento Real: {ano_actual} vs {ano_previo} ({simbolo})")

        # 1. Definimos la lista exacta de meses y el corte numérico
        nombres_meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 
                         'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
        
        mapa_meses = {m: i+1 for i, m in enumerate(nombres_meses)}
        mes_corte_num = mapa_meses.get(mes_actual, 12)

        # 2. Filtrar DataFrames por año y aplicar el límite del mes seleccionado
        df_act_line = df_timeline[
            (df_timeline['AÑO'] == ano_actual) & 
            (df_timeline['Fecha'].dt.month <= mes_corte_num)
        ].copy()
        
        df_ant_line = df_timeline[
            (df_timeline['AÑO'] == ano_previo) & 
            (df_timeline['Fecha'].dt.month <= mes_corte_num)
        ].copy()

        if not df_act_line.empty:
            # Asignar nombres de meses usando tu lista original
            df_act_line['Mes_Nombre'] = df_act_line['Fecha'].dt.month.apply(lambda x: nombres_meses[x-1])
            df_ant_line['Mes_Nombre'] = df_ant_line['Fecha'].dt.month.apply(lambda x: nombres_meses[x-1])

            col_act, col_ant = str(ano_actual), str(ano_previo)
            
            # 3. Cruzar datos de ambos años
            df_comp = df_act_line[['Mes_Nombre', 'PNC Mensual Real']].rename(columns={'PNC Mensual Real': col_act}).merge(
                df_ant_line[['Mes_Nombre', 'PNC Mensual Real']].rename(columns={'PNC Mensual Real': col_ant}),
                on='Mes_Nombre', how='left'
            ).fillna(0)

            # Forzar el orden categórico según tu lista original
            df_comp['Mes_Nombre'] = pd.Categorical(df_comp['Mes_Nombre'], categories=nombres_meses, ordered=True)
            df_comp = df_comp.sort_values('Mes_Nombre')
            
            # Cálculo de variaciones
            df_comp['Var%'] = ((df_comp[col_act] / df_comp[col_ant]) - 1) * 100

            # Fila de TOTAL (Suma del periodo seleccionado: Enero -> Mes Corte)
            total_act, total_ant = df_comp[col_act].sum(), df_comp[col_ant].sum()
            total_var = ((total_act / total_ant) - 1) * 100 if total_ant != 0 else 0
            df_total = pd.DataFrame({'Mes_Nombre': ['TOTAL'], col_act: [total_act], col_ant: [total_ant], 'Var%': [total_var]})
            df_comp_final = pd.concat([df_comp, df_total], ignore_index=True)

            # 4. Renderizado de Interfaz
            col_t, col_g = st.columns([1, 1.6])
            with col_t:
                st.write(f"**📝 Primaje Mensual ({simbolo})**")
                st.dataframe(
                    df_comp_final.style.format({
                        col_act: lambda x: f"{formato_ves(x)}", 
                        col_ant: lambda x: f"{formato_ves(x)}", 
                        'Var%': "{:,.2f}%"
                    }).apply(lambda x: ['font-weight: bold; background-color: #1A5F7A' if x.name == df_comp_final.index[-1] else '' for i in x], axis=1),
                    use_container_width=True, height=500, hide_index=True
                )

            with col_g:
                fig_comp = go.Figure()
                fig_comp.add_trace(go.Bar(x=df_comp['Mes_Nombre'], y=df_comp[col_ant], name=f'{ano_previo}', marker_color='#91C8E4'))
                fig_comp.add_trace(go.Bar(x=df_comp['Mes_Nombre'], y=df_comp[col_act], name=f'{ano_actual}', marker_color='#1A5F7A'))
                fig_comp.add_trace(go.Scatter(x=df_comp['Mes_Nombre'], y=df_comp['Var%'], name='Var %', yaxis='y2', line=dict(color='#00D4FF', width=3)))
                
                fig_comp.update_layout(
                    template="plotly_dark", height=400, 
                    yaxis2=dict(overlaying='y', side='right', showgrid=False, title="Variación %"), 
                    legend=dict(orientation="h", y=-0.2), 
                    margin=dict(t=20, b=20),
                    hovermode="x unified"
                )
                st.plotly_chart(fig_comp, use_container_width=True)

        st.markdown("---")

        # -------------------------------------------------------------
        # --- BLOQUE 2: TENDENCIA HISTÓRICA ---
        # -------------------------------------------------------------
        st.subheader(f"📈 Tendencia de Largo Plazo ({simbolo})")
        col_tipo, col_var = st.columns([0.3, 0.7])
        
        with col_tipo:
            tipo_h = st.radio("Ver tendencia de:", [f"Montos Mensuales ({simbolo})", "Ratios Técnicos (%)"], horizontal=True)
        
        with col_var:
            if tipo_h == f"Montos Mensuales ({simbolo})":
                opciones_h = ['PNC Mensual Real', 'SI Monto', 'Resultado Técnico Neto', 'Saldo Operaciones']
                labels = {'PNC Mensual Real': 'PNC (Flujo)', 'SI Monto': 'Siniestros', 'Resultado Técnico Neto': 'Res. Técnico', 'Saldo Operaciones': 'Saldo Operaciones'}
                default_h = ['PNC Mensual Real']
            else:
                opciones_h = ['SI (%)', 'Índice Combinado (%)', 'Com (%)', 'IA (%)', 'IGA (%)', 'REA (%)']
                if 'ICR (Veces)' in df_timeline.columns: opciones_h.append('ICR (Veces)')
                labels = {opt: opt for opt in opciones_h}
                default_h = ['SI (%)', 'Índice Combinado (%)']
            
            vars_sel = st.multiselect("Indicadores:", opciones_h, default=default_h)

        if vars_sel:
            fig_h = go.Figure()
            for v in vars_sel:
                fig_h.add_trace(go.Scatter(
                    x=df_timeline['Fecha'], y=df_timeline[v], name=labels.get(v, v),
                    mode='lines+markers', hovertemplate='<b>%{x|%B %Y}</b><br>'+labels.get(v,v)+': %{y:,.2f}<extra></extra>'
                ))
            fig_h.update_layout(template="plotly_dark", height=500, hovermode="x unified", 
                               xaxis=dict(rangeslider=dict(visible=True), type="date"))
            st.plotly_chart(fig_h, use_container_width=True)

    # -----------------------------------------------------------------
    # SECCIÓN: ANÁLISIS DINÁMICO DE RAMOS (RADIAL + INFOGRAFÍA + SERIE)
    # -----------------------------------------------------------------
    elif menu == "🚗 Detalle por Ramos":
        st.title(f"🚗 Detalle por Ramos: {mes_actual} {ano_actual}")
        
        # 1. Preparación de Datos y Filtros
        df_r_hist = df_ramos.copy()
        df_r_hist['Fecha'] = pd.to_datetime(df_r_hist['Fecha'])
        
        def formato_latino(valor):
            return "{:,.2f}".format(valor).replace(",", "X").replace(".", ",").replace("X", ".")
        
        exclusiones = [
            'Cod', 'Nombre Empresa', 'NombreCorto', 'AÑO', 'MES', 
            'CIERRE AL', 'Acumulada Al', 'Fecha', 'NumerodeInscripciondelaEmpresa',
            'TOTAL PNC', 'TOTAL VIDA', 'TOTAL HCM', 'TOTAL NO VIDA', 
            'TOTAL PATRIMONIALES', 'TOTAL OBLIGACIONALES']
        
        columnas_ramos = [c for c in df_r_hist.select_dtypes(include=['number']).columns 
                         if c not in exclusiones and "TOTAL" not in c.upper()]

        st.subheader(f"🌀 Composición por Ramos: Comparativo de Segmentos Mercado 🌐 (Acumulado a {mes_actual})")

        df_base_ramos = df_r_hist[(df_r_hist['AÑO'] == ano_actual) & (df_r_hist['MES'] == mes_actual)].copy()

        if not df_base_ramos.empty:
            ranking_ramos = df_base_ramos.sort_values('TOTAL PNC', ascending=False)
            top_10_ramos = ranking_ramos.head(10)['NombreCorto'].tolist()
            next_10_ramos = ranking_ramos.iloc[10:20]['NombreCorto'].tolist()

            def preparar_data_donut_v2(df_segmento):
                if df_segmento.empty: return pd.DataFrame()
                all_data = df_segmento[columnas_ramos].sum().sort_values(ascending=False).reset_index()
                all_data.columns = ['Ramo', 'Monto']
                total_seg = all_data['Monto'].sum()
                if total_seg == 0: return pd.DataFrame()
                mask_fianza = all_data['Ramo'].str.upper() == 'FIANZA'
                top_6 = all_data[~mask_fianza].head(6).copy()
                monto_resto = all_data[~all_data['Ramo'].isin(top_6['Ramo'].tolist())]['Monto'].sum()
                df_resto = pd.DataFrame({'Ramo': ['RESTO DE RAMOS'], 'Monto': [monto_resto]})
                final_df = pd.concat([top_6, df_resto]).sort_values(by='Monto', ascending=False)
                final_df['Porcentaje_Real'] = (final_df['Monto'] / total_seg) * 100
                return final_df

            data_mercado = preparar_data_donut_v2(df_base_ramos)
            data_top10 = preparar_data_donut_v2(df_base_ramos[df_base_ramos['NombreCorto'].isin(top_10_ramos)])
            data_next10 = preparar_data_donut_v2(df_base_ramos[df_base_ramos['NombreCorto'].isin(next_10_ramos)])

            paleta_azul_premium = ["#004b93", "#007ab3", "#00a9e0", "#4ec3e0", "#9adbe8", "#c5e9f3", "#34495e"]

            def render_donut(df, centro_text):
                if df is None or df.empty: return None
                df['Etiqueta_Texto'] = df.apply(lambda x: f"{x['Ramo']}<br>{formato_latino(x['Porcentaje_Real'])}%", axis=1)
                
                fig = px.pie(df, values='Monto', names='Ramo', hole=0.5, template="plotly_dark", color_discrete_sequence=paleta_azul_premium)
                
                fig.update_traces(
                    direction='clockwise', rotation=30, 
                    textposition='outside',
                    text=df['Etiqueta_Texto'], textinfo='text',
                    marker=dict(line=dict(color='#0e1117', width=2)),
                    customdata=df['Monto'].apply(formato_latino),
                    hovertemplate='<b>%{label}</b><br>Monto: %{customdata} Bs.<extra></extra>',
                    # --- AQUÍ ESTÁ EL TRUCO PARA EL TAMAÑO ---
                    domain=dict(x=[0.1, 0.9], y=[0.1, 0.9]) 
                )
                
                fig.update_layout(
                    showlegend=False,
                    annotations=[dict(text=centro_text, x=0.5, y=0.5, font_size=12, showarrow=False, font_family="Arial Black")],
                    # Forzamos márgenes fijos para que no varíe el radio
                    margin=dict(t=60, b=60, l=10, r=10), 
                    height=450,
                    autosize=False
                )
                return fig

            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown("<center><b>🌐 TOTAL MERCADO</b></center>", unsafe_allow_html=True)
                f1 = render_donut(data_mercado, f"MERCADO<br>{ano_actual}")
                if f1: st.plotly_chart(f1, use_container_width=True)
            with c2:
                st.markdown("<center><b>🏆 TOP 10 EMPRESAS</b></center>", unsafe_allow_html=True)
                f2 = render_donut(data_top10, f"TOP 10<br>PNC")
                if f2: st.plotly_chart(f2, use_container_width=True)
            with c3:
                st.markdown("<center><b>📊 SEGUNDAS 10 (11-20)</b></center>", unsafe_allow_html=True)
                f3 = render_donut(data_next10, f"TOP 11-20<br>PNC")
                if f3: st.plotly_chart(f3, use_container_width=True)

# --- BLOQUE: EVOLUCIÓN MENSUAL (DOLARIZADA Y DESACUMULADA POR RAMOS) ---
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
            
            # 1. Desacumular flujos en Bolívares primero
            df_mensual_bs = df_evol[columnas_ramos].diff().fillna(df_evol[columnas_ramos].iloc[0])
            
            # 2. Aplicar Dolarización por mes (usando TasaPromedio porque es producción/flujo)
            if moneda == "USD":
                for idx, row in df_evol.iterrows():
                    m_nombre = row['MES']
                    # Buscar tasa promedio del mes específico
                    reg_t = df_tas[(df_tas['AÑO'] == ano_actual) & (df_tas['MES'].str.strip().str.capitalize() == m_nombre.capitalize())]
                    col_t = next((c for c in reg_t.columns if 'PROMEDIO' in c.upper()), None)
                    tasa = reg_t[col_t].values[0] if col_t and not reg_t.empty else 1.0
                    
                    # Convertir toda la fila de ramos de ese mes a USD
                    df_mensual_bs.iloc[idx] = df_mensual_bs.iloc[idx] / tasa
                
                simbolo_grafico = "$"
                func_formato = formato_ves
            else:
                simbolo_grafico = "Bs."
                func_formato = formato_ves

            # 3. Identificar Top 6 y "Otros" sobre los datos ya procesados
            total_pnc_mensual = df_mensual_bs.sum(axis=1)
            ultima_foto_mes = df_mensual_bs.iloc[-1].sort_values(ascending=False)
            top_6_global = [r for r in ultima_foto_mes.index if r.upper() != 'FIANZA'][:6]
            
            df_mensual_bs['OTROS RAMOS'] = total_pnc_mensual - df_mensual_bs[top_6_global].sum(axis=1)
            df_mensual_bs['OTROS RAMOS'] = df_mensual_bs['OTROS RAMOS'].clip(lower=0)
            
            df_mensual_bs['MES'] = df_evol['MES']
            df_mensual_bs['MES_NUM'] = df_evol['MES_NUM']

            # 4. Filtro por mes seleccionado
            df_plot = df_mensual_bs[df_mensual_bs['MES_NUM'] <= mes_corte_num].copy()
            
            fig_barras = go.Figure()
            secuencia_azules = ['#D1E9F6', '#A1C8E4', '#71A8D4', '#4682A9', '#1A5F7A', '#00425A', '#002B36']
            
            for i, row in df_plot.iterrows():
                mes_iter = row['MES']
                ramos_x = top_6_global + ['OTROS RAMOS']
                valores_y = [row[r] for r in ramos_x]
                
                # Etiquetas dinámicas según moneda
                etiquetas = [f"{func_formato(v)} {simbolo_grafico}" if v > 0 else "" for v in valores_y]
                
                fig_barras.add_trace(go.Bar(
                    x=ramos_x,
                    y=valores_y,
                    name=mes_iter,
                    marker_color=secuencia_azules[i % len(secuencia_azules)],
                    text=etiquetas,
                    textposition='outside',
                    cliponaxis=False,
                    hovertemplate=f"<b>{mes_iter}</b><br>Ramo: %{{x}}<br>Monto: %{{y:,.2f}} {simbolo_grafico}<extra></extra>"
                ))

            fig_barras.update_layout(
                template="plotly_dark",
                barmode='group',
                height=600,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                xaxis=dict(title="Principales Ramos de Seguros", type='category'),
                yaxis=dict(title=f"Volumen en {simbolo_grafico}", showgrid=True, gridcolor="rgba(255,255,255,0.1)"),
                margin=dict(t=120)
            )

            st.plotly_chart(fig_barras, use_container_width=True)

# --- NIVEL 2: INFOGRAFÍA TOP 3 POR EMPRESA (ACUMULADO YTD) ---
        st.subheader(f"🏆 Top 3 Ramos por Empresa (Acumulado a {mes_actual})")
        
        # Corregimos la variable: usamos df_base_ramos que es la que definimos arriba
        df_r_ytd = df_base_ramos.copy()
        
        # Calculamos el total por fila para sacar los porcentajes
        df_r_ytd['Total_YTD'] = df_r_ytd[columnas_ramos].sum(axis=1)
        
        # Ordenamos por producción para obtener el Top 10
        top_10_ytd = df_r_ytd.nlargest(10, 'TOTAL PNC')

        # Dibujamos en 2 filas de 5
        filas_infog = [top_10_ytd.iloc[0:5], top_10_ytd.iloc[5:10]]
        for fila_data in filas_infog:
            cols_inf = st.columns(5)
            for i, (idx, row) in enumerate(fila_data.iterrows()):
                with cols_inf[i]:
                    st.markdown(f"""<div style="background-color: #1b263b; color: white; padding: 8px; text-align: center; border-radius: 5px; font-size: 0.75em; font-weight: bold; min-height: 45px; display: flex; align-items: center; justify-content: center; border: 1px solid #415a77;">{row['NombreCorto']}</div>""", unsafe_allow_html=True)
                    top_3 = row[columnas_ramos].astype(float).nlargest(3)
                    colores_inf = ["#004b93", "#007ab3", "#00a9e0"]
                    for rank, (ramo, valor) in enumerate(top_3.items()):
                        pct = (valor / row['Total_YTD'] * 100) if row['Total_YTD'] > 0 else 0
                        st.markdown(f"""<div style="background-color: {colores_inf[rank]}; color: white; padding: 8px; border-radius: 3px; margin-top: 4px; text-align: center; border-left: 3px solid white;"><p style="margin: 0; font-size: 0.6em; font-weight: bold; line-height: 1.1;">{ramo}</p><p style="margin: 0; font-size: 0.75em; font-weight: bold;">{pct:.1f}%</p></div>""", unsafe_allow_html=True)
            st.write("") 

        st.markdown("---")

        # --- NIVEL 2.1: INFOGRAFÍA 11 AL 20 ---
        st.subheader(f"🏆 Top 3 Ramos: Empresas 11 al 20")
        
        # Obtenemos las empresas del 11 al 20 usando la misma lógica
        top_11_20_ytd = df_r_ytd.sort_values('TOTAL PNC', ascending=False).iloc[10:20]

        if not top_11_20_ytd.empty:
            filas_11_20 = [top_11_20_ytd.iloc[0:5], top_11_20_ytd.iloc[5:10]]
            for fila_data in filas_11_20:
                cols_inf = st.columns(5)
                for i, (idx, row) in enumerate(fila_data.iterrows()):
                    with cols_inf[i]:
                        st.markdown(f"""<div style="background-color: #1b263b; color: white; padding: 8px; text-align: center; border-radius: 5px; font-size: 0.75em; font-weight: bold; min-height: 45px; display: flex; align-items: center; justify-content: center; border: 1px solid #415a77;">{row['NombreCorto']}</div>""", unsafe_allow_html=True)
                        top_3 = row[columnas_ramos].astype(float).nlargest(3)
                        colores_inf = ["#004b93", "#007ab3", "#00a9e0"]
                        for rank, (ramo, valor) in enumerate(top_3.items()):
                            pct = (valor / row['Total_YTD'] * 100) if row['Total_YTD'] > 0 else 0
                            st.markdown(f"""<div style="background-color: {colores_inf[rank]}; color: white; padding: 8px; border-radius: 3px; margin-top: 4px; text-align: center; border-left: 3px solid white;"><p style="margin: 0; font-size: 0.6em; font-weight: bold; line-height: 1.1;">{ramo}</p><p style="margin: 0; font-size: 0.75em; font-weight: bold;">{pct:.1f}%</p></div>""", unsafe_allow_html=True)
                st.write("") 

        st.markdown("---")

        # --- NIVEL 2.2: INFOGRAFÍA RESTO DEL MERCADO ---
        st.subheader(f"🏆 Top 3 Ramos: Resto del Mercado")
        
        # Obtenemos de la 21 en adelante
        resto_ytd = df_r_ytd.sort_values('TOTAL PNC', ascending=False).iloc[20:]

        if not resto_ytd.empty:
            with st.expander("Ver detalle de las demás empresas"):
                import math
                num_filas = math.ceil(len(resto_ytd) / 5)
                for f in range(num_filas):
                    fila_data = resto_ytd.iloc[f*5 : (f+1)*5]
                    cols_inf = st.columns(5)
                    for i, (idx, row) in enumerate(fila_data.iterrows()):
                        with cols_inf[i]:
                            st.markdown(f"""<div style="background-color: #1b263b; color: white; padding: 8px; text-align: center; border-radius: 5px; font-size: 0.75em; font-weight: bold; min-height: 45px; display: flex; align-items: center; justify-content: center; border: 1px solid #415a77;">{row['NombreCorto']}</div>""", unsafe_allow_html=True)
                            top_3 = row[columnas_ramos].astype(float).nlargest(3)
                            colores_inf = ["#004b93", "#007ab3", "#00a9e0"]
                            for rank, (ramo, valor) in enumerate(top_3.items()):
                                pct = (valor / row['Total_YTD'] * 100) if row['Total_YTD'] > 0 else 0
                                st.markdown(f"""<div style="background-color: {colores_inf[rank]}; color: white; padding: 8px; border-radius: 3px; margin-top: 4px; text-align: center; border-left: 3px solid white;"><p style="margin: 0; font-size: 0.6em; font-weight: bold; line-height: 1.1;">{ramo}</p><p style="margin: 0; font-size: 0.75em; font-weight: bold;">{pct:.1f}%</p></div>""", unsafe_allow_html=True)
                    st.write("")
# --- NIVEL 3: SERIE TEMPORAL POR RAMO (ESTILO COMPARATIVO DOLARIZADO) ---
        st.subheader("🔍 Evolución Histórica Mensual")
        
        # 1. Definimos los ramos predeterminados
        ramos_default = ["HCM INDIVIDUAL", "HCM COLECTIVO", "AUTO CASCO"]
        
        # Validamos que existan en tus datos para evitar errores
        seleccion_inicial = [r for r in ramos_default if r in columnas_ramos]

        # 2. Multiselect con la configuración de inicio
        ramos_sel = st.multiselect(
            "Seleccione los ramos para comparar la evolución real mensual:", 
            options=sorted(columnas_ramos),
            default=seleccion_inicial
        )

        if ramos_sel:
            fig_linea = go.Figure()
            
            # Ordenar por fecha para que las líneas no zigzagueen
            df_r_hist = df_r_hist.sort_values(['NombreCorto', 'Fecha'])
            simbolo_l = "$" if moneda == "USD" else "Bs."

            # Colores vivos para contraste sobre fondo oscuro
            colores_vivos = ['#00d4ff', '#ff4b4b', '#00ff85', '#ffeb3b', '#e91e63', '#ffffff']

            # Diccionario de meses para la conversión
            m_map = {1:'Enero', 2:'Febrero', 3:'Marzo', 4:'Abril', 5:'Mayo', 6:'Junio',
                     7:'Julio', 8:'Agosto', 9:'Septiembre', 10:'Octubre', 11:'Noviembre', 12:'Diciembre'}

            for i, ramo in enumerate(ramos_sel):
                # A. Cálculo del valor mensual desacumulado (en Bs.)
                col_temp = f"Temp_{ramo}"
                df_r_hist[col_temp] = df_r_hist.groupby(['NombreCorto', 'AÑO'])[ramo].diff().fillna(df_r_hist[ramo])
                
                # B. Agrupar por fecha para el total mercado (Suma de todas las compañías para ese ramo)
                serie_ramo = df_r_hist.groupby(['Fecha', 'AÑO'], as_index=False)[col_temp].sum()
                serie_ramo = serie_ramo.sort_values('Fecha')

                # C. Aplicar Dolarización dinámica punto por punto si aplica
                if moneda == "USD":
                    def convertir_punto(row):
                        mes_n = m_map[row['Fecha'].month]
                        reg_t = df_tas[(df_tas['AÑO'] == row['AÑO']) & (df_tas['MES'].str.strip().str.capitalize() == mes_n)]
                        col_t = next((c for c in reg_t.columns if 'PROMEDIO' in c.upper()), None)
                        tasa = reg_t[col_t].values[0] if col_t and not reg_t.empty else 1.0
                        return row[col_temp] / tasa
                    
                    serie_ramo['Valor_Final'] = serie_ramo.apply(convertir_punto, axis=1)
                else:
                    serie_ramo['Valor_Final'] = serie_ramo[col_temp]

                # D. Crear la línea
                fig_linea.add_trace(go.Scatter(
                    x=serie_ramo['Fecha'], 
                    y=serie_ramo['Valor_Final'],
                    mode='lines+markers',
                    name=ramo,
                    line=dict(width=3, color=colores_vivos[i % len(colores_vivos)]),
                    marker=dict(size=7),
                    hovertemplate=f"%{{y:,.2f}} {simbolo_l}<extra></extra>"
                ))

            # 4. Diseño del gráfico
            fig_linea.update_layout(
                template="plotly_dark", 
                height=550,
                hovermode="x unified",
                hoverlabel=dict(bgcolor="rgba(33, 33, 33, 0.9)", font_size=13),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
                xaxis=dict(
                    title="Periodo Mensual",
                    showgrid=False,
                    rangeslider=dict(visible=True),
                    type="date"
                ),
                yaxis=dict(
                    title=f"Monto Mensual ({simbolo_l})", 
                    showgrid=True, 
                    gridcolor="rgba(255,255,255,0.1)"
                ),
                margin=dict(t=100, l=10, r=10, b=10)
            )
            
            st.plotly_chart(fig_linea, use_container_width=True)
        else:
            st.info("💡 Por favor, selecciona uno o más ramos para generar la comparativa temporal.")

# --- 5. PERFIL INDIVIDUAL DE COMPAÑÍA ---
    elif menu == "🏢 Resumen por Empresa":        
        st.title(f"🏢 Resumen {st.session_state.empresa_memoria}: {mes_actual} {ano_actual}")
        
        # 2. PREPARAR LISTA ORDENADA
        df_ranking = df_act.sort_values(by='PrimasNetasCobradas', ascending=False)
        lista_empresas = df_ranking['NombreCorto'].tolist()
        
        # 3. DETERMINAR EL ÍNDICE ACTUAL
        try:
            idx_persistente = lista_empresas.index(st.session_state.empresa_memoria)
        except ValueError:
            idx_persistente = 0

        # 4. EL SELECTOR
        st.selectbox(
            "Seleccione una Empresa:", 
            lista_empresas, 
            index=idx_persistente,
            key="selector_empresa", 
            on_change=actualizar_empresa
        )
        
        # 5. SINCRONIZAR LA VARIABLE DE FILTRADO
        empresa_sel = st.session_state.empresa_memoria
        
        # 6. FILTRO DE DATOS (Empresa Actual)
        df_emp = df_act[df_act['NombreCorto'] == empresa_sel].iloc[0]

        # 7. FILTRO DE DATOS (Empresa Año Anterior) - CRÍTICO PARA VARIACIONES
        df_emp_ant_aa = df_compilado[
            (df_compilado['AÑO'] == ano_actual - 1) & 
            (df_compilado['MES'].str.capitalize() == mes_actual.capitalize()) & 
            (df_compilado['NombreCorto'] == empresa_sel)
        ]
        
# --- FILA 1: INDICADORES (TARJETAS) CON VARIACIONES Y FORMATO ---
        simbolo = "$" if moneda == "USD" else "Bs."

        # 1. Definición base para Gauges (Siempre en Bs.)
        pnc_ind = df_emp['PrimasNetasCobradas']

        # 2. Variables de visualización (Lo que se muestra en el metric)
        pnc_vis = pnc_ind
        so_vis = df_emp['SaldodeOperaciones']
        rtn_vis = df_emp['ResultadoTecnicoNeto']
        si_vis = df_emp['TotalGenralSI']

        # 3. Valores Año Anterior (Base en Bs.) para variaciones
        pnc_comp_aa = df_emp_ant_aa['PrimasNetasCobradas'].iloc[0] if not df_emp_ant_aa.empty else 0
        so_comp_aa = df_emp_ant_aa['SaldodeOperaciones'].iloc[0] if not df_emp_ant_aa.empty else 0

        if moneda == "USD":
            try:
                # Tasa Cierre Actual
                reg_tasa_act = df_tas[(df_tas['AÑO'] == ano_actual) & (df_tas['MES'].str.capitalize() == mes_actual.capitalize())]
                t_cierre_act = reg_tasa_act['Tasa_Cierre'].values[0] if not reg_tasa_act.empty else 1.0
                
                # --- PNC Actual USD (Desacumulada) ---
                idx_actual = meses_orden.index(mes_actual.capitalize())
                meses_a_recorrer = meses_orden[:idx_actual + 1]
                pnc_usd_actual = 0.0
                acum_bs_prev = 0.0
                for m in meses_a_recorrer:
                    f_h = df_compilado[(df_compilado['AÑO'] == ano_actual) & (df_compilado['MES'].str.capitalize() == m.capitalize()) & (df_compilado['NombreCorto'] == empresa_sel)]
                    if not f_h.empty:
                        bs_m = f_h['PrimasNetasCobradas'].values[0]
                        t_p = df_tas[(df_tas['AÑO'] == ano_actual) & (df_tas['MES'].str.capitalize() == m.capitalize())]['TasaPromedio'].values[0]
                        pnc_usd_actual += ((bs_m - acum_bs_prev) / t_p)
                        acum_bs_prev = bs_m
                
                # --- PNC Año Anterior USD (Desacumulada) ---
                pnc_usd_aa = 0.0
                acum_bs_prev_aa = 0.0
                for m in meses_a_recorrer:
                    f_h_aa = df_compilado[(df_compilado['AÑO'] == ano_actual - 1) & (df_compilado['MES'].str.capitalize() == m.capitalize()) & (df_compilado['NombreCorto'] == empresa_sel)]
                    if not f_h_aa.empty:
                        bs_m_aa = f_h_aa['PrimasNetasCobradas'].values[0]
                        t_p_aa = df_tas[(df_tas['AÑO'] == ano_actual - 1) & (df_tas['MES'].str.capitalize() == m.capitalize())]['TasaPromedio'].values[0]
                        pnc_usd_aa += ((bs_m_aa - acum_bs_prev_aa) / t_p_aa)
                        acum_bs_prev_aa = bs_m_aa

                # Tasa Cierre Año Anterior
                reg_tasa_aa = df_tas[(df_tas['AÑO'] == ano_actual - 1) & (df_tas['MES'].str.capitalize() == mes_actual.capitalize())]
                t_cierre_aa = reg_tasa_aa['Tasa_Cierre'].values[0] if not reg_tasa_aa.empty else 1.0

                # Asignación para métricas
                pnc_vis = pnc_usd_actual
                pnc_comp_aa = pnc_usd_aa 
                so_vis = so_vis / t_cierre_act
                so_comp_aa = so_comp_aa / t_cierre_aa
                rtn_vis = rtn_vis / t_cierre_act
                si_vis = si_vis / t_cierre_act

            except Exception as e:
                st.sidebar.error(f"Error en conversión USD: {e}")

        # 4. Cálculo de Variaciones finales (Comparación coherente Bs vs Bs o USD vs USD)
        var_pnc = ((pnc_vis / pnc_comp_aa) - 1) * 100 if pnc_comp_aa > 0 else 0
        var_so = ((so_vis / so_comp_aa) - 1) * 100 if so_comp_aa != 0 else 0

        # 5. RENDERIZADO
        c1, c2, c3, c4, c5 = st.columns(5)

        with c1:
            st.metric("Primas Netas Cobradas", f"{formato_ves(pnc_vis)} {simbolo}", f"{var_pnc:.2f}% vs AA")

        with c2:
            st.metric("Resultado Técnico", f"{formato_ves(rtn_vis)} {simbolo}")

        with c3:
            st.metric("Saldo de Operaciones", f"{formato_ves(so_vis)} {simbolo}", f"{var_so:.2f}% vs AA")

        with c4:
            mkt_share = (pnc_ind / total_mercado_pnc * 100) if total_mercado_pnc > 0 else 0
            st.metric("Participación Mercado", f"{mkt_share:.2f}%")

        with c5:
            st.metric("Siniestros Incurridos", f"{formato_ves(si_vis)} {simbolo}")

        st.markdown("---")

# --- FILA 2: RATIOS TÉCNICOS Y FINANCIEROS (7 RELOJES OPTIMIZADOS) ---
        st.write("#### ⚖️ Ratios Técnicos y Financieros Individuales")
        
        # 1. Cálculos de Ratios con la empresa seleccionada
        p_dev_ind = df_emp['Total GeneralPDev']
        
        r_com = (df_emp['Comisiones'] / pnc_ind * 100) if pnc_ind > 0 else 0
        r_ia = (df_emp['GastosdeAdquision'] / pnc_ind * 100) if pnc_ind > 0 else 0
        r_gad = (df_emp['Gastosdeadministracion'] / pnc_ind * 100) if pnc_ind > 0 else 0
        r_si = (df_emp['TotalGenralSI'] / p_dev_ind * 100) if p_dev_ind > 0 else 0
        r_rea = (-(df_emp['ResultadodelReaseguroCedido']) / p_dev_ind * 100) if p_dev_ind > 0 else 0
        
        tc_ind_calc = r_com + r_ia + r_gad + r_si + r_rea 
        icr_ind = (df_emp['InversionesAptas'] / df_emp['ReservasTecnicas']) if df_emp['ReservasTecnicas'] > 0 else 0

        # Función para generar los relojes compactos con títulos visibles
        def crear_gauge_final(valor, titulo, color="#2196F3", es_porcentaje=True):
            color_final = color
            if titulo == "Tasa Comb %" and valor > 100:
                color_final = "#ff4b4b"
            if titulo == "ICR (Inv/Res)" and valor < 1: # Uso 1 porque tus datos parecen estar en escala 0-100
                color_final = "#ff4b4b"
            fig = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = valor,
                # Forzamos 2 decimales en el número central (.2f)
                number = {'suffix': "%" if es_porcentaje else "", 'valueformat': ".2f", 'font': {'size': 16}},
                title = {'text': titulo, 'font': {'size': 11}}, 
                gauge = {
                    'axis': {'range': [0, 120] if es_porcentaje else [0, 2], 'tickwidth': 1, 'tickfont': {'size': 8}},
                    'bar': {'color': color_final},
                    'steps': [{'range': [0, 100] if es_porcentaje else [0, 1], 'color': "rgba(0,0,0,0.05)"}]
                }
            ))
            # Ajuste de márgenes: t=50 da espacio para que el título no se corte
            fig.update_layout(
                height=170, 
                margin=dict(l=5, r=5, t=50, b=5), 
                paper_bgcolor="rgba(0,0,0,0)", 
                plot_bgcolor="rgba(0,0,0,0)"
            )
            return fig

        # --- Renderizado de los 7 indicadores en una sola fila ---
        cols = st.columns(7)
        
        # Diccionario de configuración para los 7 gauges
        config_relojes = [
            (r_com, "Comisiones %", "#2196F3", True),
            (r_ia, "G. Adquisición %", "#2196F3", True),
            (r_gad, "G. Admin %", "#FF9800", True),
            (r_si, "Siniestralidad %", "#ff4b4b", True),
            (r_rea, "Costo Reaseg %", "#64B5F6", True),
            (tc_ind_calc, "Tasa Comb %", "#795548", True),
            (icr_ind, "ICR (Inv/Res)", "#9C27B0", False)
        ]

        for i, (val, tit, col, perc) in enumerate(config_relojes):
            cols[i].plotly_chart(crear_gauge_final(val, tit, col, perc), use_container_width=True)

# --- FILA 3: EVOLUCIÓN MENSUAL DINÁMICA (HISTÓRICO MULTIANUAL) ---
        st.markdown("---")
        st.write(f"#### 📈 Análisis Evolutivo Dinámico Histórico - {empresa_sel}")

        # 1. Preparar el DataFrame histórico (QUITAMOS el filtro de ano_actual)
        df_hist = df_compilado[
            (df_compilado['NombreCorto'] == empresa_sel)
        ].copy()

        # Aseguramos formato de fecha y orden cronológico real
        df_hist['Fecha'] = pd.to_datetime(df_hist['Fecha'])
        df_hist = df_hist.sort_values('Fecha')
        df_hist['MES_CAP'] = df_hist['MES'].str.strip().str.capitalize()

        # 2. Lógica de Dolarización Multianual
        etiqueta_y = "Monto (Bs.)"

        if moneda == "USD":
            etiqueta_y = "Monto (USD)"
            
            # Función ajustada para buscar tasa por MES y AÑO específico del registro
            def obtener_tasa_hist(row, tipo_tasa):
                mes_n = row['MES_CAP']
                anio_n = row['AÑO']
                reg = df_tas[(df_tas['AÑO'] == anio_n) & (df_tas['MES'].str.strip().str.capitalize() == mes_n)]
                if not reg.empty:
                    for col in reg.columns:
                        if tipo_tasa.upper() in col.upper():
                            val = reg[col].values[0]
                            return val if val > 0 else 1.0
                return 1.0

            # Aplicamos conversión fila por fila considerando su propio año
            df_hist['t_prom'] = df_hist.apply(lambda r: obtener_tasa_hist(r, 'Promedio'), axis=1)
            df_hist['t_cier'] = df_hist.apply(lambda r: obtener_tasa_hist(r, 'Cierre'), axis=1)

            # Desacumulamos PNC y SI por AÑO para evitar saltos extraños entre diciembres y eneros
            df_hist['PNC_Mensual'] = df_hist.groupby('AÑO')['PrimasNetasCobradas'].diff().fillna(df_hist['PrimasNetasCobradas']) / df_hist['t_prom']
            df_hist['SI_Mensual'] = df_hist.groupby('AÑO')['TotalGenralSI'].diff().fillna(df_hist['TotalGenralSI']) / df_hist['t_cier']
            df_hist['ResultadoTecnicoNeto_Val'] = df_hist['ResultadoTecnicoNeto'] / df_hist['t_cier']
            df_hist['SaldodeOperaciones_Val'] = df_hist['SaldodeOperaciones'] / df_hist['t_cier']
        else:
            # Lógica en Bolívares (Desacumulada)
            df_hist['PNC_Mensual'] = df_hist.groupby('AÑO')['PrimasNetasCobradas'].diff().fillna(df_hist['PrimasNetasCobradas'])
            df_hist['SI_Mensual'] = df_hist.groupby('AÑO')['TotalGenralSI'].diff().fillna(df_hist['TotalGenralSI'])
            df_hist['ResultadoTecnicoNeto_Val'] = df_hist['ResultadoTecnicoNeto']
            df_hist['SaldodeOperaciones_Val'] = df_hist['SaldodeOperaciones']

        # 3. Mapeo de variables para el selector
        opciones_vars = {
            "PNC_Mensual": "Primas Netas (Mensual)",
            "SI_Mensual": "Siniestros (Mensual)",
            "ResultadoTecnicoNeto_Val": "Resultado Técnico Neto",
            "SaldodeOperaciones_Val": "Saldo de Operaciones"
        }

        seleccionadas = st.multiselect(
            "Seleccione los indicadores a graficar:",
            options=list(opciones_vars.keys()),
            default=["PNC_Mensual", "SI_Mensual"],
            format_func=lambda x: opciones_vars[x],
            key="ms_empresa_hist"
        )

        if seleccionadas and not df_hist.empty:
            fig_line = go.Figure()
            
            # Usamos Plotly Graph Objects para mayor control sobre el eje X (Fecha)
            for var in seleccionadas:
                fig_line.add_trace(go.Scatter(
                    x=df_hist['Fecha'], 
                    y=df_hist[var],
                    mode='lines+markers',
                    name=opciones_vars[var],
                    hovertemplate="<b>%{x|%B %Y}</b><br>Monto: %{y:,.2f}<extra></extra>"
                ))
            
            fig_line.update_layout(
                template="plotly_dark",
                title=f"Evolución {moneda} - {empresa_sel} (Histórico Completo)",
                hovermode="x unified",
                height=500,
                xaxis=dict(
                    title="Línea de Tiempo",
                    rangeslider=dict(visible=True),
                    type='date'
                ),
                yaxis=dict(title=etiqueta_y, tickformat=","),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            
            st.plotly_chart(fig_line, use_container_width=True)

        elif not seleccionadas:
            st.warning("⚠️ Seleccione al menos un indicador.")
        else:
            st.info(f"No hay datos históricos suficientes para {empresa_sel}.")

# =================================================================
# 5. MENSAJE DE PIE DE PÁGINA O ERROR
# =================================================================
else:
    st.warning("⚠️ No se pudieron cargar los datos. Verifique la ruta del archivo Excel y que no esté abierto por otro programa.")

st.sidebar.markdown("---")
st.sidebar.caption("🏦🛡️**Sistema de Inteligencia IFM - Dashboard Corporativo**")
st.sidebar.caption("© 2026 - Todos los derechos reservados")

st.sidebar.caption("⚠️*Los datos convertidos a dólares (USD) son estrictamente de referencia. No representan necesariamente la contabilidad oficial en divisas de las Empresas.*")
