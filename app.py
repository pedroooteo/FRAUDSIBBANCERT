import streamlit as st
import pandas as pd
import plotly.express as px
from backend.catalogos import LISTA_BANCOS
from backend.procesador import procesar_txt_sib, validar_reglas_sib, obtener_recomendacion

# --- TU API KEY ---
MI_API_KEY = "AIzaSyC71imL8xiMrBCXLsgJ8IpA47c8jknZQX8"

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="BanCERT | Observatorio", page_icon="🛡️", layout="wide")

# --- COLORES CORPORATIVOS (VARIABLES) ---
COLOR_PRUSSIAN_BLUE = "#063A59"
COLOR_CADET_GREY = "#8CA1B3"
COLOR_BLACK = "#010101"
COLOR_WHITE = "#FFFFFF"

# --- ESTILOS CSS PERSONALIZADOS ---
st.markdown(f"""
<style>
    /* Importar Fuente Montserrat */
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Montserrat', sans-serif;
        color: {COLOR_BLACK};
    }}
    
    /* Fondo General */
    .stApp {{
        background-color: #F4F6F8;
    }}

    /* Estilo de las Métricas (Tarjetas) para que sean iguales */
    div[data-testid="stMetric"] {{
        background-color: {COLOR_WHITE};
        border: 1px solid {COLOR_CADET_GREY};
        border-radius: 8px;
        padding: 20px 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        text-align: center;
        height: 160px; /* Altura fija para alineación */
        display: flex;
        flex-direction: column;
        justify_content: center;
        align-items: center;
    }}

    /* Títulos de las métricas */
    div[data-testid="stMetricLabel"] p {{
        font-size: 14px !important;
        font-weight: 600;
        color: {COLOR_CADET_GREY} !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }}

    /* Valores de las métricas */
    div[data-testid="stMetricValue"] div {{
        font-size: 28px !important;
        font-weight: 700;
        color: {COLOR_PRUSSIAN_BLUE} !important;
    }}

    /* Títulos Principales */
    h1, h2, h3 {{
        color: {COLOR_PRUSSIAN_BLUE} !important;
        font-weight: 700;
    }}

    /* Barra Lateral */
    section[data-testid="stSidebar"] {{
        background-color: {COLOR_WHITE};
        border-right: 2px solid {COLOR_CADET_GREY};
    }}
    
    /* Botones y Widgets */
    .stSelectbox label, .stFileUploader label, .stMultiSelect label {{
        color: {COLOR_PRUSSIAN_BLUE};
        font-weight: 600;
    }}
    
    /* Botón de descarga */
    button[data-testid="baseButton-secondary"] {{
        border-color: {COLOR_PRUSSIAN_BLUE};
        color: {COLOR_PRUSSIAN_BLUE};
    }}
</style>
""", unsafe_allow_html=True)

# --- BARRA LATERAL ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2092/2092663.png", width=70)
    st.markdown(f"<h3 style='color:{COLOR_PRUSSIAN_BLUE};'>BanCERT Panel</h3>", unsafe_allow_html=True)
    st.markdown("---")
    banco_seleccionado = st.selectbox("🏦 Entidad Bancaria:", LISTA_BANCOS)
    st.write("")
    
    # --- 1. CARGA MASIVA (accept_multiple_files=True) ---
    archivos = st.file_uploader("📂 Cargar Reportes SIB (.txt)", type=['txt'], accept_multiple_files=True)
    
    if archivos:
        st.success(f"✅ {len(archivos)} archivos cargados.")
        st.markdown("---")
    
    st.caption(f"© 2026 BanCERT | Seguridad SIB")

# --- APP PRINCIPAL ---
# Título con estilo personalizado
st.markdown(f"<h1 style='text-align: left; color: {COLOR_PRUSSIAN_BLUE};'>🛡️ Observatorio de Amenazas</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='color: {COLOR_CADET_GREY}; font-size: 18px;'>Monitor de Ciberseguridad: <b>{banco_seleccionado}</b></p>", unsafe_allow_html=True)
st.markdown("---")

if archivos:
    # --- PROCESAMIENTO MULTI-ARCHIVO ---
    lista_dfs = []
    
    # Barra de progreso visual
    if len(archivos) > 1:
        bar = st.progress(0)
    
    for i, archivo_individual in enumerate(archivos):
        df_temp = procesar_txt_sib(archivo_individual)
        lista_dfs.append(df_temp)
        if len(archivos) > 1:
            bar.progress((i + 1) / len(archivos))
            
    # Unir todos
    if lista_dfs:
        df_raw = pd.concat(lista_dfs, ignore_index=True)
    else:
        df_raw = pd.DataFrame()

    if not df_raw.empty:
        
        # --- 2. FILTROS INTERACTIVOS (SIDEBAR) ---
        with st.sidebar:
            st.subheader("🔍 Filtros")
            
            # Filtro Criticidad
            opciones_crit = df_raw['Criticidad'].unique().tolist()
            sel_crit = st.multiselect("Nivel de Criticidad:", opciones_crit, default=opciones_crit)
            
            # Filtro Detector
            opciones_tool = df_raw['Herramienta'].unique().tolist()
            sel_tool = st.multiselect("Detector:", opciones_tool, default=opciones_tool)
            
        # Aplicar filtros
        df = df_raw[
            (df_raw['Criticidad'].isin(sel_crit)) & 
            (df_raw['Herramienta'].isin(sel_tool))
        ]
        
        if df.empty:
            st.warning("⚠️ Los filtros seleccionados no devolvieron datos. Intenta seleccionar más opciones.")
        else:
            # --- SECCIÓN 1: KPIs (TARJETAS UNIFORMES) ---
            c1, c2, c3, c4 = st.columns(4)
            
            total = df['Cantidad'].sum()
            criticos = df[df['Criticidad']=='Crítico']['Cantidad'].sum()
            paises = df['País'].nunique()
            
            # Lógica Top Vector
            top_df = df.groupby('Tipo de Ataque')['Cantidad'].sum().reset_index().sort_values('Cantidad', ascending=False)
            if not top_df.empty:
                top_name = top_df.iloc[0]['Tipo de Ataque']
                # Acortar nombre si es muy largo
                if len(top_name) > 20: top_name = top_name[:18] + "..."
                
                # Datos para IA (basado en lo filtrado)
                top_code_ia = df.groupby('Código Ataque')['Cantidad'].sum().idxmax()
                top_qty_ia = df.groupby('Código Ataque')['Cantidad'].sum().max()
                top_pais_ia = df[df['Código Ataque']==top_code_ia]['País'].mode()[0]
            else:
                top_name, top_code_ia, top_qty_ia, top_pais_ia = "N/A", "0000", 0, "N/A"

            c1.metric("Intentos Bloqueados", f"{total:,.0f}")
            c2.metric("Incidentes Críticos", f"{criticos}")
            c3.metric("Orígenes Únicos", f"{paises}")
            c4.metric("Vector Principal", top_name)
            
            st.write("") # Espacio

            # --- SECCIÓN 2: AUDITORÍA Y CISO ---
            col_aud, col_ia = st.columns(2)
            
            with col_aud:
                st.markdown(f"<h4 style='color:{COLOR_PRUSSIAN_BLUE}'>👮 Auditoría Normativa SIB</h4>", unsafe_allow_html=True)
                # Validamos sobre el RAW (completo) para no esconder errores con filtros
                errs = validar_reglas_sib(df_raw)
                if not errs:
                    st.success(f"✅ **APROBADO:** Los {len(archivos)} archivos cumplen con la estructura SIB.")
                else:
                    for e in errs:
                        if "CRÍTICO" in e: st.error(e)
                        else: st.warning(e)

            with col_ia:
                st.markdown(f"<h4 style='color:{COLOR_PRUSSIAN_BLUE}'>🧠 CISO Advisor (IA)</h4>", unsafe_allow_html=True)
                with st.spinner("Analizando datos filtrados..."):
                    consejo = obtener_recomendacion(top_code_ia, MI_API_KEY, top_qty_ia, top_pais_ia)
                st.info(consejo)

            st.markdown("---")
            
            # --- SECCIÓN 3: GRÁFICAS ---
            PALETA_BANCERT = [COLOR_PRUSSIAN_BLUE, COLOR_CADET_GREY, "#5D7485", "#2C5169", "#AABBC9"]
            
            c_graf1, c_graf2 = st.columns([2, 1])

            with c_graf1:
                st.subheader("📊 Top 10 Vectores de Ataque")
                bar_data = df.groupby('Tipo de Ataque')['Cantidad'].sum().reset_index().sort_values('Cantidad', ascending=True).tail(10)
                
                fig_bar = px.bar(
                    bar_data, 
                    x='Cantidad', 
                    y='Tipo de Ataque', 
                    orientation='h', 
                    text_auto=True,
                    color_discrete_sequence=[COLOR_PRUSSIAN_BLUE]
                )
                fig_bar.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    font={'family': "Montserrat"},
                    xaxis=dict(showgrid=False),
                    yaxis=dict(showgrid=False)
                )
                st.plotly_chart(fig_bar, use_container_width=True)

            with c_graf2:
                st.subheader("🛡️ Detección")
                fig_sun = px.sunburst(
                    df, 
                    path=['Herramienta', 'Criticidad'], 
                    values='Cantidad',
                    color_discrete_sequence=PALETA_BANCERT
                )
                fig_sun.update_layout(font={'family': "Montserrat"})
                st.plotly_chart(fig_sun, use_container_width=True)

            # Mapa de Calor
            st.subheader("🌡️ Mapa de Calor: Riesgo vs Vector")
            try:
                heat_data = df.groupby(['Criticidad', 'Tipo de Ataque'])['Cantidad'].sum().reset_index()
                fig_heat = px.density_heatmap(
                    heat_data, x="Criticidad", y="Tipo de Ataque", z="Cantidad", text_auto=True,
                    color_continuous_scale="Blues"
                )
                fig_heat.update_layout(font={'family': "Montserrat"})
                st.plotly_chart(fig_heat, use_container_width=True)
            except:
                pass
                
            # --- 3. BOTÓN DE EXPORTAR ---
            with st.expander("📂 Ver Datos y Descargar"):
                st.dataframe(df, use_container_width=True)
                
                # Convertir a CSV
                csv = df.to_csv(index=False).encode('utf-8')
                
                st.download_button(
                    label="📥 Descargar Reporte Ejecutivo (CSV)",
                    data=csv,
                    file_name=f"Reporte_BanCERT_{banco_seleccionado}.csv",
                    mime='text/csv',
                )

    else:
        st.error("⚠️ El archivo cargado no contiene datos válidos o legibles.")
else:
    st.info("👈 Carga uno o varios reportes .TXT en la barra lateral para comenzar.")