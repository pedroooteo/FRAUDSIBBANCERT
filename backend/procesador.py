import pandas as pd
import google.generativeai as genai
from .catalogos import DICT_ATAQUES, DICT_DETECTOR, DICT_CRITICIDAD, DICT_PAISES

# --- FUNCIÓN PRINCIPAL DE PROCESAMIENTO ---
def procesar_txt_sib(archivo_subido):
    registros = []
    
    # Intentamos leer con diferentes codificaciones para evitar errores
    try:
        contenido = archivo_subido.getvalue().decode("utf-8").splitlines()
    except UnicodeDecodeError:
        contenido = archivo_subido.getvalue().decode("latin-1").splitlines()
    
    for linea in contenido:
        if len(linea) < 30: continue 
        try:
            # Parseo basado en posiciones fijas SIB
            fecha_fmt = f"{linea[0:2]}/{linea[2:4]}/{linea[4:8]}"
            monitoreo = "Interno" if linea[8:9] == '1' else "Externo"
            det_code = linea[9:13].strip() 
            ataque_code = linea[13:17]
            crit_code = linea[17:18]
            pais_code = linea[18:21]
            cantidad = int(linea[21:33])
            
            registros.append({
                'Fecha': fecha_fmt,
                'Origen': monitoreo,
                'Herramienta': DICT_DETECTOR.get(det_code, f"Detector {det_code}"),
                'Tipo de Ataque': DICT_ATAQUES.get(ataque_code, f"Desconocido ({ataque_code})"),
                'Criticidad': DICT_CRITICIDAD.get(crit_code, "No definido"),
                'País': DICT_PAISES.get(pais_code, f"País {pais_code}"),
                'Cantidad': cantidad,
                'Código Ataque': ataque_code
            })
        except: continue
    return pd.DataFrame(registros)

# --- VALIDACIONES SIB (CORREGIDO PARA DUPLICADOS) ---
def validar_reglas_sib(df):
    errores = []
    
    # REGLA 6: Cantidad no puede ser 0
    if not df[df['Cantidad'] <= 0].empty:
        errores.append(f"❌ ERROR CRÍTICO: Registros con cantidad 0.")
        
    # REGLA 7: Duplicados EXACTOS (Corregido)
    # Ahora solo marca error si TODA la fila es idéntica (incluyendo cantidad)
    if not df[df.duplicated(keep=False)].empty:
        errores.append(f"⚠️ ADVERTENCIA: Existen registros idénticos duplicados.")
        
    return errores

# --- CISO ADVISOR CON IA ---
def obtener_recomendacion(codigo_ataque_str, api_key=None, cantidad=0, pais_frecuente="Desconocido"):
    code = str(codigo_ataque_str).strip()
    nombre_ataque = DICT_ATAQUES.get(code, "Ciberataque Genérico")

    if api_key:
        try:
            genai.configure(api_key=api_key)
            # Usamos Flash que es rápido. Si falla, caerá al except.
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            prompt = f"""
            Rol: CISO experto en banca. Tono: Ejecutivo y técnico.
            Evento: {cantidad} ataques de tipo "{nombre_ataque}" (Código SIB: {code}).
            Origen: {pais_frecuente}.
            Tarea: Dame 1 recomendación técnica precisa y estima el nivel de riesgo. Máximo 40 palabras.
            """
            
            response = model.generate_content(prompt)
            return f"🤖 **ANÁLISIS IA:** {response.text}"
        except Exception as e:
            # Si falla la IA, no mostramos el error técnico feo, mostramos el estático
            print(f"Error IA: {e}") 

    # --- RESPALDO ESTÁTICO (Si no hay llave o falla la conexión) ---
    if code.startswith('1'): return "📧 Revisar reglas Antispam y SPF/DKIM."
    if code.startswith('2101'): return "🛑 **RANSOMWARE:** Aislar red, verificar backups offline y no apagar equipos."
    if code.startswith('2'): return "🦠 Ejecutar escaneo completo de Antivirus/EDR y aislar host."
    if code.startswith('32'): return "🎣 Phishing: Bloquear dominio en Proxy/DNS y alertar a usuarios."
    if code.startswith('41'): return "💉 SQLi/XSS: Revisar logs del WAF y sanitizar inputs en código."
    if code.startswith('51'): return "🌊 DDoS: Activar mitigación con ISP y Rate Limiting en borde."
    
    return "🔵 Monitoreo estándar de logs y correlación de eventos."