import streamlit as st
from datetime import date, datetime, timedelta
from supabase import create_client, Client
import base64
import os

# ==============================================================================
# 1. CONFIGURACIÓN DE PÁGINA Y CONEXIÓN SUPABASE
# ==============================================================================
st.set_page_config(
    page_title="Agenda Virtual MADAI",
    page_icon="📅",
    layout="wide"
)

@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# Lista de animadoras actualizada
OPCIONES_ANIMADORAS = ["Madai", "Martha", "Eusy", "Carla", "Lucia", "Ninguno", "Otro Animador"]
# Opciones de duración para shows (1.5h a 3h de media en media hora)
OPCIONES_DURACION = ["1.5 horas", "2 horas", "2.5 horas", "3 horas"]

# Estados globales para controlar modales sin anidamiento
if "editar_personal_id" not in st.session_state:
    st.session_state["editar_personal_id"] = None
if "ver_ficha_id" not in st.session_state:
    st.session_state["ver_ficha_id"] = None

# ==============================================================================
# 2. CARGA DE FONDO E IMÁGENES EN BASE64
# ==============================================================================
def obtener_base64_de_archivo(ruta_archivo):
    if os.path.exists(ruta_archivo):
        with open(ruta_archivo, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return None

fondo_b64 = obtener_base64_de_archivo("fondo.jpeg")
logo_b64 = obtener_base64_de_archivo("logo.jpeg")

css_fondo = """
.stApp {
    background-color: #f3e8ff;
}
"""
if fondo_b64:
    css_fondo = f"""
    .stApp {{
        background-image: linear-gradient(rgba(240, 230, 255, 0.65), rgba(240, 230, 255, 0.65)), url("data:image/jpeg;base64,{fondo_b64}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    """

# ==============================================================================
# 3. ESTILOS CSS PERSONALIZADOS INFANTILES Y AJUSTE DE CABECERA
# ==============================================================================
st.markdown(f"""
    <style>
    {css_fondo}

    /* Padding superior para que la barra de Streamlit no lo tape */
    .block-container {{
        padding-top: 3.8rem !important;
        padding-bottom: 2rem !important;
    }}

    /* Cabecera Unificada (Logo + Título MADAI) */
    .header-container {{
        display: flex;
        align-items: center;
        justify-content: flex-start;
        gap: 12px;
        margin-bottom: 12px;
        margin-top: 5px;
    }}

    .logo-inline {{
        height: 44px;
        width: auto;
        object-fit: contain;
        border-radius: 6px;
    }}

    .title-inline {{
        font-family: 'Comic Sans MS', 'Chalkboard SE', 'Quicksand', sans-serif;
        font-size: 2.2rem;
        font-weight: 900;
        background: linear-gradient(45deg, #7B2CBF, #FF007F, #FF9F1C, #2B9348);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        padding: 0;
        line-height: 1;
        letter-spacing: 1px;
    }}

    /* Compactar Selector de Pestañas Radio */
    div[data-testid="stRadio"] {{
        margin-top: 0px !important;
        margin-bottom: 10px !important;
    }}

    div[data-testid="stRadio"] > div {{
        gap: 8px !important;
        padding: 0 !important;
    }}

    div[data-testid="stRadio"] label {{
        background-color: rgba(255, 255, 255, 0.85) !important;
        padding: 6px 18px !important;
        border-radius: 20px !important;
        border: 1.5px solid #7B2CBF !important;
        font-weight: bold !important;
        color: #7B2CBF !important;
        transition: all 0.2s ease-in-out;
        margin: 0 !important;
    }}

    div[data-testid="stRadio"] label:hover {{
        background-color: #7B2CBF !important;
        color: white !important;
    }}

    /* Estilos generales de tarjetas */
    .card-madai, .card-risuena, .card-alquiler {{
        padding: 0 0 12px 0;
        border-radius: 8px;
        margin-bottom: 12px;
        position: relative;
    }}

    /* Badge de marca */
    .badge-marca {{
        position: absolute;
        top: 8px;
        right: 12px;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: bold;
        color: white;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.2);
    }}
    .badge-madai {{ background-color: #7B2CBF; }}
    .badge-risuena {{ background-color: #2B9348; }}
    .badge-local {{ background-color: #023E8A; }}

    /* Encabezados */
    .header-madai {{ background-color: #7B2CBF; color: white; padding: 6px 12px; font-weight: bold; font-size: 0.95rem; border-radius: 4px 4px 0 0; }}
    .header-risuena {{ background-color: #2B9348; color: white; padding: 6px 12px; font-weight: bold; font-size: 0.95rem; border-radius: 4px 4px 0 0; }}
    .header-alquiler {{ background-color: #023E8A; color: white; padding: 6px 12px; font-weight: bold; font-size: 0.95rem; border-radius: 4px 4px 0 0; }}

    /* Formato de texto interno de tarjeta */
    .event-title {{
        font-size: 1.15rem;
        font-weight: bold;
        color: #111;
        padding: 10px 80px 4px 12px;
    }}
    .data-line {{
        font-size: 0.95rem;
        color: #222;
        padding: 2px 12px;
    }}

    /* Botón GUARDAR EVENTO en Verde Llamativo */
    div[data-testid="stForm"] button[kind="primaryFormSubmit"],
    div[data-testid="stForm"] button {{
        background-color: #28a745 !important;
        background-image: none !important;
        color: white !important;
        font-size: 1.1rem !important;
        font-weight: bold !important;
        border: none !important;
        padding: 10px 0 !important;
        border-radius: 8px !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.15) !important;
    }}
    div[data-testid="stForm"] button:hover {{
        background-color: #218838 !important;
        color: white !important;
    }}

    /* Botón amarillo personalizado */
    .btn-modificar-amarillo button {{
        background-color: #FFC107 !important;
        color: #000 !important;
        font-weight: bold !important;
        border: none !important;
    }}
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 4. FUNCIONES AUXILIARES Y FORMATO
# ==============================================================================
def formatear_fecha_larga(fecha_str):
    if not fecha_str:
        return "Sin fecha"
    try:
        dt = datetime.strptime(str(fecha_str), "%Y-%m-%d")
        dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        return f"{dias[dt.weekday()]} {dt.day} de {meses[dt.month - 1]} de {dt.year}"
    except Exception:
        return str(fecha_str)

def calcular_hora_fin(hora_inicio_str, duracion_str="2 horas"):
    try:
        dt_inicio = datetime.strptime(hora_inicio_str.strip(), "%I:%M %p")
        minutos_add = 120
        if "1.5" in duracion_str:
            minutos_add = 90
        elif "2.5" in duracion_str:
            minutos_add = 150
        elif "3" in duracion_str:
            minutos_add = 180
        elif "1" in duracion_str:
            minutos_add = 60
        
        dt_fin = dt_inicio + timedelta(minutes=minutos_add)
        return f"{dt_inicio.strftime('%I:%M %p')} a {dt_fin.strftime('%I:%M %p')}"
    except Exception:
        return f"{hora_inicio_str} ({duracion_str})"

def obtener_eventos():
    res = supabase.table("eventos").select("*, personal(*)").execute()
    return res.data if res.data else []

# ==============================================================================
# 5. MODALES DECLARADOS GLOBALMENTE (SIN ANIDAMIENTO)
# ==============================================================================
@st.dialog("👤 Asignar / Editar Personal")
def dialog_asignar_personal(evento):
    e_id = int(evento["id"])
    st.write(f"**Evento:** {evento.get('evento', '')} - {evento.get('cliente', '')}")
    
    res_p = supabase.table("personal").select("*").eq("evento_id", e_id).execute()
    datos_p = res_p.data[0] if res_p.data else {}

    # 1. Animadora
    anim_guardada = datos_p.get("animador", "")
    idx_anim = 0
    if anim_guardada in OPCIONES_ANIMADORAS:
        idx_anim = OPCIONES_ANIMADORAS.index(anim_guardada)
    elif anim_guardada:
        idx_anim = OPCIONES_ANIMADORAS.index("Otro Animador")

    anim_sel = st.selectbox("🎤 **Animadora**", OPCIONES_ANIMADORAS, index=idx_anim)
    
    if anim_sel == "Otro Animador":
        animador_final = st.text_input("Escribe el nombre de la Animadora:", value=anim_guardada if anim_guardada not in OPCIONES_ANIMADORAS else "")
    else:
        animador_final = anim_sel

    # 2. Dalinas
    st.write("💃 **Dalinas**")
    num_dalinas_val = int(datos_p.get("num_dalinas", 1) or 1)
    cant_dalinas = st.number_input("Número de Dalinas", min_value=0, max_value=20, value=num_dalinas_val)
    
    dalinas_guardadas_str = datos_p.get("dalinas", "")
    lista_dalinas_prev = [d.strip() for d in dalinas_guardadas_str.split(",") if d.strip()]
    
    nombres_dalinas = []
    for i in range(int(cant_dalinas)):
        val_prev = lista_dalinas_prev[i] if i < len(lista_dalinas_prev) else ""
        nom_d = st.text_input(f"Nombre Dalina {i+1}", value=val_prev, key=f"dalina_input_{e_id}_{i}")
        if nom_d.strip():
            nombres_dalinas.append(nom_d.strip())
    
    dalinas_final_str = ", ".join(nombres_dalinas)

    # 3. DJ
    dj_val = st.text_input("🎧 **DJ**", value=datos_p.get("dj", ""))

    # 4. Staff
    staff_val = st.text_input("🛠️ **Staff**", value=datos_p.get("staff", ""))

    # Duración del show
    duracion_guardada = datos_p.get("duracion", "2 horas")
    idx_dur = OPCIONES_DURACION.index(duracion_guardada) if duracion_guardada in OPCIONES_DURACION else 1
    duracion_val = st.selectbox("⏱️ **Duración del Show**", OPCIONES_DURACION, index=idx_dur)

    # 5. Observaciones
    obs_val = st.text_area("📝 **Observaciones / Notas**", value=datos_p.get("detalles", ""))

    if st.button("💾 Guardar Personal", use_container_width=True, type="primary"):
        payload = {
            "evento_id": e_id,
            "animador": animador_final,
            "dalinas": dalinas_final_str,
            "num_dalinas": int(cant_dalinas),
            "dj": dj_val,
            "staff": staff_val,
            "duracion": duracion_val,
            "detalles": obs_val
        }
        if datos_p:
            supabase.table("personal").update(payload).eq("id", datos_p["id"]).execute()
        else:
            supabase.table("personal").insert(payload).execute()
        
        st.session_state["editar_personal_id"] = None
        st.success("¡Personal guardado correctamente!")
        st.rerun()


@st.dialog("📋 Ficha del Evento")
def dialog_ver_ficha(evento):
    e_id = int(evento["id"])
    res_evento = supabase.table("eventos").select("*").eq("id", e_id).execute()
    if not res_evento.data:
        st.error("No se encontró el evento.")
        return

    ev = res_evento.data[0]
    res_personal = supabase.table("personal").select("*").eq("evento_id", e_id).execute()
    p_data = res_personal.data[0] if res_personal.data else {}

    fecha_fmt = formatear_fecha_larga(ev.get("fecha", ""))
    duracion_str = p_data.get("duracion", "2 horas") if p_data.get("duracion") else "2 horas"
    hora_inicio = ev.get("hora_contrato", "04:30 PM")
    rango_horas = calcular_hora_fin(hora_inicio, duracion_str)

    costo = float(ev.get('costo_total', 0) or 0)
    adelanto = float(ev.get('monto_adelanto', 0) or 0)
    pendiente = costo - adelanto
    tipo_raw = str(ev.get('tipo', 'Show'))
    tipo_str = f"({tipo_raw})" if tipo_raw else ""

    marca = str(ev.get("marca", "madai")).lower()
    if "local" in marca:
        header_class = "header-alquiler"
        color_fondo = "#A2D2FF"
        nombre_marca_header = "LOCAL"
    elif "risueña" in marca:
        header_class = "header-risuena"
        color_fondo = "#B7E4C7"
        nombre_marca_header = "RISUEÑA"
    else:
        header_class = "header-madai"
        color_fondo = "#E0B0FF"
        nombre_marca_header = "MADAI"

    st.markdown(f"""
        <style>
        div[data-testid="stDialog"] > div:first-child {{
            background-color: {color_fondo} !important;
        }}
        </style>
    """, unsafe_allow_html=True)

    st.markdown(f'<div class="{header_class}">🏷️ {nombre_marca_header} — 📅 {fecha_fmt}</div>', unsafe_allow_html=True)
    
    # Resumen del Evento
    st.markdown(f'<div class="event-title">🎉 <b>Nombre del Evento:</b> {ev.get("evento", "Sin Nombre")} {tipo_str}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="data-line">👤 <b>Cliente:</b> {ev.get("cliente", "N/A")} | 📱 <b>Tel:</b> {ev.get("telefono", "N/A")}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="data-line">⏰ <b>Hora de Contrato:</b> {ev.get("hora_contrato", "04:30 PM")} (Citación: {ev.get("hora_citacion", "04:00 PM")})</div>', unsafe_allow_html=True)
    
    if "local" not in marca:
        st.markdown(f'<div class="data-line">📍 <b>Dirección:</b> {ev.get("direccion", "N/A")}</div>', unsafe_allow_html=True)

    # Desglose de Local + Show
    desc_raw = str(ev.get("descripcion", "") or "").strip()
    contrato_show = "SHOW" in desc_raw.upper() or "SHOW" in tipo_raw.upper()

    if "local" in marca and contrato_show:
        monto_show = costo - 600 if costo > 600 else 0
        st.markdown(f'<div class="data-line">🏠 <b>Costo del Local:</b> S/ 600</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="data-line">🎭 <b>Precio del Show:</b> S/ {monto_show:.0f}</div>', unsafe_allow_html=True)
    elif desc_raw:
        solo_desc = desc_raw.replace("Alquiler:", "").split("(")[0].strip()
        if solo_desc:
            st.markdown(f'<div class="data-line">📦 <b>Alquiler:</b> {solo_desc}</div>', unsafe_allow_html=True)

    st.markdown(f'<div class="data-line">💵 <b>Monto Total:</b> S/ {costo:.0f} | 💳 <b>Adelanto:</b> S/ {adelanto:.0f} | 💰 <b style="color: #D90429;">Pendiente: S/ {pendiente:.0f}</b></div>', unsafe_allow_html=True)

    # Resumen de Personal Asignado
    st.markdown(f'<div class="{header_class}">👥 Personal Asignado</div>', unsafe_allow_html=True)

    animador = p_data.get("animador", "")
    dalinas = p_data.get("dalinas", "")
    dj = p_data.get("dj", "")
    staff = p_data.get("staff", "")
    detalles = p_data.get("detalles", "")

    tiene_personal = bool((animador and animador != "Ninguno") or dalinas or dj or staff)

    if tiene_personal:
        st.markdown(f'<div class="data-line">🎤 <b>Animadora:</b> {animador if animador else "No asignada"}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="data-line">💃 <b>Dalinas ({p_data.get("num_dalinas", 0)}):</b> {dalinas if dalinas else "Ninguna"}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="data-line">🎧 <b>DJ:</b> {dj if dj else "No asignado"}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="data-line">🛠️ <b>Staff:</b> {staff if staff else "No asignado"}</div>', unsafe_allow_html=True)
        if detalles:
            st.markdown(f'<div class="data-line" style="margin-top:6px; font-style:italic;">📝 <b>Observaciones:</b> {detalles}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="data-line" style="color: #D90429;">⚠️ Aún no se ha asignado personal a este evento.</div>', unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)

    st.markdown('<div class="btn-modificar-amarillo">', unsafe_allow_html=True)
    if st.button("✏️ Modificar Personal", use_container_width=True, key=f"btn_mod_pers_{ev['id']}"):
        st.session_state["ver_ficha_id"] = None
        st.session_state["editar_personal_id"] = ev["id"]
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ==============================================================================
# 6. TARJETAS DE EVENTO
# ==============================================================================
def renderizar_lista_eventos(lista_eventos, key_prefix="evt"):
    if not lista_eventos:
        st.info("No hay eventos registrados para este criterio.")
        return

    cols = st.columns(2)
    for idx, ev in enumerate(lista_eventos):
        with cols[idx % 2]:
            costo = float(ev.get('costo_total', 0) or 0)
            adelanto = float(ev.get('monto_adelanto', 0) or 0)
            pendiente = costo - adelanto
            tipo_str = str(ev.get('tipo', 'Show'))
            
            marca_raw = str(ev.get('marca', 'madai')).lower()
            card_border = "#28A745"
            
            if "local" in marca_raw:
                card_class = "card-alquiler"
                card_bg = "#A2D2FF"
                badge_class = "badge-local"
                nombre_marca_tag = "local"
            elif "risueña" in marca_raw or "risuena" in marca_raw:
                card_class = "card-risuena"
                card_bg = "#B7E4C7"
                badge_class = "badge-risuena"
                nombre_marca_tag = "risueña"
            else:
                card_class = "card-madai"
                card_bg = "#E0B0FF"
                badge_class = "badge-madai"
                nombre_marca_tag = "madai"
            
            personal_lista = ev.get("personal", [])
            p_data = {}
            if isinstance(personal_lista, list) and len(personal_lista) > 0:
                p_data = personal_lista[0]
            elif isinstance(personal_lista, dict):
                p_data = personal_lista
            
            tiene_personal = False
            duracion_show = "2 horas"
            if p_data:
                animador = p_data.get("animador", "")
                dalinas = p_data.get("dalinas", "")
                dj = p_data.get("dj", "")
                staff = p_data.get("staff", "")
                duracion_show = p_data.get("duracion", "2 horas") or "2 horas"
                if (animador and animador != "Ninguno") or dalinas or dj or staff:
                    tiene_personal = True

            es_local = "local" in marca_raw
            desc_raw = str(ev.get("descripcion", "") or "").strip()
            contrato_show = "SHOW" in desc_raw.upper() or "SHOW" in tipo_str.upper()

            es_solo_deco = tipo_str.strip().lower() == "deco"
            
            if es_solo_deco:
                linea_hora_html = f'<div class="data-line">⏰ <b>Hora:</b> {ev.get("hora_contrato", ev.get("hora_citacion", "04:30 PM"))}</div>'
            else:
                linea_hora_html = f'<div class="data-line">⏰ <b>Hora:</b> {ev.get("hora_contrato", "04:30 PM")} | <b>Citación:</b> {ev.get("hora_citacion", "04:00 PM")}</div>'

            linea_direccion_html = ""
            if not es_local:
                linea_direccion_html = f'<div class="data-line">📍 <b>Lugar:</b> {ev.get("direccion", "N/A")}</div>'

            linea_detalle_html = ""
            if es_local and contrato_show:
                hora_inicio = ev.get("hora_contrato", "04:30 PM")
                rango_horas = calcular_hora_fin(hora_inicio, duracion_show)
                monto_show = costo - 600 if costo > 600 else 0
                linea_detalle_html = (
                    f'<div class="data-line">🎭 <b>Show:</b> {rango_horas}</div>'
                    f'<div class="data-line">🏠 <b>Costo del Local:</b> S/ 600</div>'
                    f'<div class="data-line">🎭 <b>Precio del Show:</b> S/ {monto_show:.0f}</div>'
                )
            elif desc_raw:
                solo_desc = desc_raw.replace("Alquiler:", "").split("(")[0].strip()
                if solo_desc:
                    linea_detalle_html = f'<div class="data-line">📦 <b>Alquiler:</b> {solo_desc}</div>'

            html_tarjeta = (
                f'<div class="{card_class}">'
                f'<div class="badge-marca {badge_class}">{nombre_marca_tag}</div>'
                f'<div class="event-title">🎉 {ev.get("evento", "Sin Nombre")} - ({tipo_str})</div>'
                f'<div class="data-line">📅 <b>Fecha:</b> {formatear_fecha_larga(ev.get("fecha", ""))}</div>'
                f'{linea_hora_html}'
                f'<div class="data-line">👤 <b>Cliente:</b> {ev.get("cliente", "N/A")} | 📱 <b>Tel:</b> {ev.get("telefono", "N/A")}</div>'
                f'{linea_direccion_html}'
                f'{linea_detalle_html}'
                f'<div class="data-line">💵 <b>Total:</b> S/ {costo:.0f} | 💳 <b>Adelanto:</b> S/ {adelanto:.0f} | <b style="color: #D90429;">Pendiente: S/ {pendiente:.0f}</b></div>'
                f'</div>'
            )

            st.markdown(f"""
                <style>
                div.st-key-{key_prefix}_event_card_{ev['id']} {{
                    background-color: {card_bg} !important;
                    border-left: 6px solid {card_border} !important;
                    border-radius: 8px !important;
                    padding: 0 0 10px 0 !important;
                    margin-bottom: 14px !important;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.12) !important;
                    overflow: hidden !important;
                }}

                div.st-key-{key_prefix}_event_card_{ev['id']} [data-testid="stHorizontalBlock"] {{
                    gap: 1rem !important;
                    padding: 0 14px !important;
                    margin-top: 2px !important;
                }}

                div.st-key-{key_prefix}_event_card_{ev['id']} [data-testid="stButton"] button {{
                    width: 100% !important;
                    border-radius: 7px !important;
                    margin: 0 !important;
                }}
                </style>
            """, unsafe_allow_html=True)

            with st.container(key=f"{key_prefix}_event_card_{ev['id']}"):
                st.markdown(html_tarjeta, unsafe_allow_html=True)

                if es_local and not contrato_show:
                    pass
                else:
                    if not tiene_personal:
                        col_btn1, col_btn2 = st.columns(2)
                        with col_btn1:
                            if st.button("👤 Asignar Personal", key=f"{key_prefix}_btn_pers_{ev['id']}", use_container_width=True):
                                st.session_state["editar_personal_id"] = ev["id"]
                                st.rerun()
                        with col_btn2:
                            if st.button("📋 Ver Ficha", key=f"{key_prefix}_btn_ver_{ev['id']}", use_container_width=True):
                                st.session_state["ver_ficha_id"] = ev["id"]
                                st.rerun()
                    else:
                        if st.button("📋 Ver Ficha", key=f"{key_prefix}_btn_ver_{ev['id']}", use_container_width=True):
                            st.session_state["ver_ficha_id"] = ev["id"]
                            st.rerun()

# ==============================================================================
# 7. CABECERA ALINEADA EN UNA FILA (LOGO + TÍTULO "MADAI")
# ==============================================================================
html_logo = f'<img src="data:image/jpeg;base64,{logo_b64}" class="logo-inline">' if logo_b64 else ''

st.markdown(f"""
    <div class="header-container">
        {html_logo}
        <div class="title-inline">MADAI</div>
    </div>
""", unsafe_allow_html=True)

# ==============================================================================
# 8. NAVEGACIÓN COMPACTA Y SIN ESPACIOS
# ==============================================================================
tabs = ["HOY", "PROX 3 DIAS", "REGISTRO"]

if "tab_activa" not in st.session_state:
    st.session_state["tab_activa"] = tabs[0]

tab_seleccionada = st.radio(
    "Navegación", 
    tabs, 
    index=tabs.index(st.session_state["tab_activa"]),
    horizontal=True, 
    label_visibility="collapsed"
)

st.session_state["tab_activa"] = tab_seleccionada

# ------------------------------------------------------------------------------
# PESTAÑA 1: HOY
# ------------------------------------------------------------------------------
if tab_seleccionada == "HOY":
    st.write("### 📅 Eventos del Día de Hoy")
    hoy_str = str(date.today())
    eventos_todos = obtener_eventos()
    eventos_hoy = [e for e in eventos_todos if str(e.get("fecha")) == hoy_str]
    renderizar_lista_eventos(eventos_hoy, key_prefix="hoy")

# ------------------------------------------------------------------------------
# PESTAÑA 2: PROX 3 DIAS
# ------------------------------------------------------------------------------
elif tab_seleccionada == "PROX 3 DIAS":
    st.write("### 📆 Próximos Eventos")
    hoy = date.today()
    limite_3_dias = hoy + timedelta(days=3)
    
    col_f1, col_f2 = st.columns([1, 2])
    with col_f1:
        fecha_filtrada = st.date_input("🔎 **Filtrar por fecha específica:**", value=None)

    eventos_todos = obtener_eventos()

    if fecha_filtrada:
        str_f = str(fecha_filtrada)
        eventos_filtrados = [ev for ev in eventos_todos if str(ev.get("fecha")) == str_f]
        st.write(f"Mostrando resultados para: **{formatear_fecha_larga(str_f)}**")
    else:
        eventos_filtrados = []
        for ev in eventos_todos:
            f_str = str(ev.get("fecha"))
            try:
                f_dt = datetime.strptime(f_str, "%Y-%m-%d").date()
                if hoy <= f_dt <= limite_3_dias:
                    eventos_filtrados.append(ev)
            except ValueError:
                pass
        st.write(f"Mostrando eventos programados desde hoy **{hoy.strftime('%d/%m/%Y')}** hasta **{limite_3_dias.strftime('%d/%m/%Y')}**")

    renderizar_lista_eventos(eventos_filtrados, key_prefix="prox")

# ------------------------------------------------------------------------------
# PESTAÑA 3: REGISTRO
# ------------------------------------------------------------------------------
elif tab_seleccionada == "REGISTRO":
    st.write("### ➕ Registrar Nuevo Evento")

    col1, col2 = st.columns(2)
    
    with col1:
        marca = st.selectbox("**Marca**", ["madai", "risueña", "local"])
        evento_nom = st.text_input("**Nombre del Evento**")
        tipo_e = st.selectbox("**Tipo de Evento**", ["Show", "Show + Deco", "Deco", "Alquiler de Local"])
        cliente = st.text_input("**Cliente**")
        telefono = st.text_input("**Número (Teléfono)**")
        direccion = st.text_input("**Dirección**")
        fecha_e = st.date_input("**Fecha**", value=date.today())
    
    with col2:
        if tipo_e in ["Show", "Show + Deco"]:
            hora_cit = st.text_input("**Hora de Invitación / Citación**", value="04:00 PM")
            hora_c = st.text_input("**Hora de Contrato**", value="04:30 PM")
        else:
            hora_c = st.text_input("**Hora del Evento**", value="04:30 PM")
            hora_cit = hora_c

        desc_alquiler = ""
        monto_alquiler = 0
        
        # Desglose especial si es Marca LOCAL con Show
        if marca == "local" and tipo_e in ["Show", "Show + Deco"]:
            costo_local_fijo = 600
            st.text_input("**Costo del Local (S/)**", value="600 (Fijo)", disabled=True)
            precio_show_local = st.number_input("**Precio del Show (S/)**", min_value=0, step=10, value=250)
            costo_t = costo_local_fijo + precio_show_local
            st.info(f"🏠 **Costo del Local:** S/ 600 | 🎭 **Precio del Show:** S/ {precio_show_local}")
        else:
            agregar_alquiler = st.checkbox("➕ **Agregar Alquiler**")
            
            if agregar_alquiler:
                desc_alquiler = st.text_input("**Descripción del Alquiler**")
                monto_alquiler = st.number_input("**Monto del Alquiler (S/)**", min_value=0, step=10, value=250)

            if tipo_e == "Show + Deco":
                col_p1, col_p2 = st.columns(2)
                with col_p1:
                    precio_show = st.number_input("**Precio Show (S/)**", min_value=0, step=10, value=250)
                with col_p2:
                    precio_deco = st.number_input("**Precio Deco (S/)**", min_value=0, step=10, value=250)
                costo_base = precio_show + precio_deco
            else:
                costo_base = st.number_input("**Monto Total (S/)**", min_value=0, step=10, value=250)

            costo_t = costo_base + (monto_alquiler if agregar_alquiler else 0)

            if agregar_alquiler:
                st.info(f"💰 **Monto Total (incluye Alquiler):** S/ {costo_t}")

        st.markdown(f"💵 **Monto Total:** <b style='font-size: 1.1rem;'>S/ {costo_t:.0f}</b>", unsafe_allow_html=True)
        monto_a = st.number_input("**Monto de Adelanto (S/)**", min_value=0, step=10, value=100)
        pendiente_calc = max(0, costo_t - monto_a)
            
        st.markdown(f"🔴 **Pendiente de Pago:** <b style='color: #D90429; font-size: 1.1rem;'>S/ {pendiente_calc:.0f}</b>", unsafe_allow_html=True)

    with st.form("form_guardar_evento"):
        st.markdown("<br>", unsafe_allow_html=True)
        guardar_btn = st.form_submit_button("📌 GUARDAR EVENTO", use_container_width=True)

        if guardar_btn:
            nuevo_registro = {
                "marca": marca,
                "evento": evento_nom,
                "tipo": tipo_e,
                "cliente": cliente,
                "telefono": telefono,
                "direccion": direccion,
                "fecha": str(fecha_e),
                "hora_contrato": hora_c,
                "hora_citacion": hora_cit,
                "costo_total": float(costo_t),
                "monto_adelanto": float(monto_a),
                "descripcion": f"Alquiler: {desc_alquiler} (S/ {monto_alquiler})" if desc_alquiler else ""
            }
            supabase.table("eventos").insert(nuevo_registro).execute()
            
            st.session_state["tab_activa"] = tabs[0]
            st.rerun()

# ==============================================================================
# 9. DISPARADOR DE MODALES AL FINAL DE LA EJECUCIÓN
# ==============================================================================
if st.session_state["ver_ficha_id"] is not None:
    eventos_todos = obtener_eventos()
    ev_sel = next((e for e in eventos_todos if e["id"] == st.session_state["ver_ficha_id"]), None)
    if ev_sel:
        dialog_ver_ficha(ev_sel)

if st.session_state["editar_personal_id"] is not None:
    eventos_todos = obtener_eventos()
    ev_sel = next((e for e in eventos_todos if e["id"] == st.session_state["editar_personal_id"]), None)
    if ev_sel:
        dialog_asignar_personal(ev_sel)
