import pandas as pd
# Importamos los diccionarios que acabas de crear
from .catalogos import DICT_ATAQUES, DICT_DETECTOR, DICT_CRITICIDAD, DICT_PAISES

def procesar_txt_sib(archivo_subido):
    """
    Lee el archivo TXT crudo y lo convierte en una tabla (DataFrame)
    siguiendo las reglas de posiciones de la SIB.
    """
    registros = []
    
    # Decodificamos el archivo de bytes a texto
    contenido = archivo_subido.getvalue().decode("utf-8").splitlines()
    
    for linea in contenido:
        # Saltamos líneas vacías o muy cortas (menos de 34 caracteres que es el estándar)
        if len(linea) < 30: continue 
        
        try:
            # --- CORTE DE POSICIONES (SEGÚN GUÍA SIB) ---
            # Python cuenta desde 0. 
            
            # 1. Fecha (Posición 1-8 en PDF -> Python [0:8])
            fecha_raw = linea[0:8]
            # Formato visual: DD/MM/AAAA
            fecha_fmt = f"{fecha_raw[0:2]}/{fecha_raw[2:4]}/{fecha_raw[4:8]}"
            
            # 2. Monitoreo (Posición 9)
            monitoreo = "Interno" if linea[8:9] == '1' else "Externo"
            
            # 3. Detector (Posición 10-13) - Quitamos espacios extra con .strip()
            det_code = linea[9:13].strip() 
            
            # 4. Tipo Ataque (Posición 14-17)
            ataque_code = linea[13:17]
            
            # 5. Criticidad (Posición 18)
            crit_code = linea[17:18]
            
            # 6. País (Posición 19-21)
            pais_code = linea[18:21]
            
            # 7. Cantidad (Posición 22-33) - Convertimos "000000000015" a 15
            cantidad = int(linea[21:33])
            
            # --- BUSCAMOS EN DICCIONARIOS ---
            nombre_ataque = DICT_ATAQUES.get(ataque_code, f"Ataque desconocido ({ataque_code})")
            nombre_detector = DICT_DETECTOR.get(det_code, f"Detector código {det_code}")
            nombre_criticidad = DICT_CRITICIDAD.get(crit_code, "No definido")
            nombre_pais = DICT_PAISES.get(pais_code, f"País {pais_code}")

            # --- GUARDAMOS EL REGISTRO LIMPIO ---
            registros.append({
                'Fecha': fecha_fmt,
                'Origen': monitoreo,
                'Herramienta': nombre_detector,
                'Tipo de Ataque': nombre_ataque,
                'Criticidad': nombre_criticidad,
                'País': nombre_pais,
                'Cantidad': cantidad,
                'Código Ataque': ataque_code # Útil para referencias técnicas
            })
            
        except Exception as e:
            # Si una línea falla, la imprimimos en consola pero no rompemos el programa
            print(f"Error procesando línea: {linea} -> {e}")
            continue

    return pd.DataFrame(registros)