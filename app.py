import streamlit as st
import pandas as pd
import plotly.express as px
from backend.catalogos import LISTA_BANCOS
from backend.procesador import procesar_txt_sib

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="BanCERT | Monitor Dinámico",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. ESTILOS CSS ---
st.markdown("""
<style>
    .stApp { background-color: #F8F9FA; }
    
    div[data-testid="stMetric"] {
        background-color: #FFFFFF;
        border: 1px solid #E0E0E0;
        padding: 10px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        text-align: center;
        transition: transform 0.2s;
        min-height: 120px;
        display: flex;
        flex-direction: column;
        justify_content: center;
    }
    
    div[data-testid="stMetric"]:hover {
        transform: scale(1.02);
        box-shadow: 0 6px 8px rgba(0,0,0,0.1);
    }
    
    div[data-testid="stMetricValue"] {
        font-size: 22px !important;
        word-wrap: break-word !important;
        white-space: normal !important;
        line-height: 1.2 !important;
    }

    h1, h2, h3 { color: #0F2537; font-family: 'Segoe UI', sans-serif; }
    
    section[data-testid="stSidebar"] { background-color: #FFFFFF; border-right: 1px solid #E0E0E0; }
</style>
""", unsafe_allow_html=True)

# --- 3. BARRA LATERAL ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2092/2092663.png", width=80)
    st.markdown("## **BanCERT** Control Panel")
    st.markdown("---")
    st.caption("CONFIGURACIÓN DE ENTIDAD")
    banco_seleccionado = st.selectbox("🏦 Seleccionar Banco:", LISTA_BANCOS)
    st.write("")
    st.caption("FUENTE DE DATOS")
    archivo_cargado = st.file_uploader("Subir Reporte SIB (.txt)", type=['txt'])
    st.markdown("---")
    st.info("ℹ️ **Privacidad:** Procesamiento local.")

# --- 4. CUERPO PRINCIPAL ---
with st.container():
    col_logo, col_titulo = st.columns([1, 10])
    with col_logo: st.write("")
    with col_titulo:
        st.title(f"🛡️ Monitor Dinámico: {banco_seleccionado}")
        st.markdown(f"**Validación de Normativa SIB** | Fecha: *{pd.Timestamp.now().strftime('%d/%m/%Y')}*")

if archivo_cargado is not None:
    # Procesar archivo
    df = procesar_txt_sib(archivo_cargado)

    if not df.empty:
        st.write("")
        
        # --- KPIs ---
        col1, col2, col3, col4 = st.columns(4)
        total = df['Cantidad'].sum()
        criticos = df[df['Criticidad'] == 'Crítico']['Cantidad'].sum()
        
        if not df.empty:
            top_vector = df.groupby('Tipo de Ataque')['Cantidad'].sum().idxmax()
        else:
            top_vector = "N/A"
            
        paises = df['País'].nunique()
        
        col1.metric("🛡️ Intentos Bloqueados", f"{total:,.0f}")
        col2.metric("🚨 Incidentes Críticos", f"{criticos}", delta="Atención", delta_color="inverse")
        col3.metric("🌍 Orígenes Únicos", f"{paises}")
        col4.metric("🔥 Vector Principal", top_vector)

        st.markdown("---")

        # --- GRÁFICAS ANIMADAS ---
        
        # COLUMNA 1: BARRAS (Con potencial de animación temporal)
        c_chart1, c_chart2 = st.columns([2, 1])

        with c_chart1:
            st.subheader("📊 Top Vectores (Evolución)")
            
            # Verificamos si hay múltiples fechas para activar la animación "PLAY"
            if df['Fecha'].nunique() > 1:
                st.caption("💡 Dale al botón ▶️ 'Play' abajo a la izquierda para ver la evolución por días.")
                # Agrupamos por Fecha y Tipo
                data_bar = df.groupby(['Fecha', 'Tipo de Ataque'])['Cantidad'].sum().reset_index()
                # Ordenamos por fecha para que la animación sea correcta
                data_bar = data_bar.sort_values('Fecha')
                
                fig_bar = px.bar(
                    data_bar, 
                    x='Cantidad', 
                    y='Tipo de Ataque', 
                    orientation='h', 
                    color='Cantidad',
                    animation_frame="Fecha",   # <--- ESTO CREA LA ANIMACIÓN DE TIEMPO
                    range_x=[0, data_bar['Cantidad'].max()*1.1], # Fija el eje X para que no salte
                    color_continuous_scale='Blues'
                )
            else:
                # Si es un solo día, mostramos la estática normal
                data_bar = df.groupby('Tipo de Ataque')['Cantidad'].sum().reset_index().sort_values('Cantidad', ascending=True).tail(10)
                fig_bar = px.bar(
                    data_bar, 
                    x='Cantidad', 
                    y='Tipo de Ataque', 
                    orientation='h', 
                    text='Cantidad',
                    color='Cantidad',
                    color_continuous_scale='Blues'
                )
            
            fig_bar.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_bar, use_container_width=True)

        # COLUMNA 2: SUNBURST (La "Joya" interactiva)
        with c_chart2:
            st.subheader("🧬 Análisis de Profundidad")
            st.caption("👆 Haz clic en los anillos interiores para expandir.")
            
            # [cite_start]Gráfico SOLAR (Sunburst) [cite: 5]
            # Muestra jerarquía: Herramienta -> Criticidad -> Ataque
            fig_sun = px.sunburst(
                df, 
                path=['Herramienta', 'Criticidad', 'Tipo de Ataque'], 
                values='Cantidad',
                color='Criticidad',
                color_discrete_map={
                    'Crítico': '#FF4B4B', 
                    'Alta': '#FFA15A', 
                    'Media': '#FFD700', 
                    'Baja': '#00CC96', 
                    'Informativo': '#636EFA'
                }
            )
            fig_sun.update_layout(
                margin=dict(t=0, l=0, r=0, b=0),
                paper_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig_sun, use_container_width=True)

        # --- MAPA DE CALOR ---
        st.subheader("🌡️ Mapa de Calor: Intensidad")
        try:
            heatmap_data = df.groupby(['Criticidad', 'Tipo de Ataque'])['Cantidad'].sum().reset_index()
            fig_heat = px.density_heatmap(
                heatmap_data, 
                x="Criticidad", 
                y="Tipo de Ataque", 
                z="Cantidad", 
                text_auto=True,
                color_continuous_scale="Viridis" 
            )
            fig_heat.update_layout(plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_heat, use_container_width=True)
        except:
            st.info("Faltan datos.")

        # --- TABLA ---
        with st.expander("📂 Ver Auditoría de Registros"):
            st.dataframe(df, use_container_width=True)
            
    else:
        st.error("Archivo vacío o formato incorrecto.")
else:
    st.markdown("""
    <div style='text-align: center; padding: 50px;'>
        <h2 style='color: #cccccc;'>Esperando archivo...</h2>
    </div>
    """, unsafe_allow_html=True)