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

# ==============================================================================
# 2. CARGA DE FONDO E IMÁGENES
# ==============================================================================
def obtener_base64_de_archivo(ruta_archivo):
    if os.path.exists(ruta_archivo):
        with open(ruta_archivo, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return None

# Aplicar fondo.jpeg si existe
fondo_b64 = obtener_base64_de_archivo("fondo.jpeg")
css_fondo = ""
if fondo_b64:
    css_fondo = f"""
    .stApp {{
        background-image: linear-gradient(rgba(255, 255, 255, 0.85), rgba(255, 255, 255, 0.85)), url("data:image/jpeg;base64,{fondo_b64}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    """

# ==============================================================================
# 3. ESTILOS CSS PERSONALIZADOS INFANTILES Y ESTRUCTURA
# ==============================================================================
st.markdown(f"""
    <style>
    {css_fondo}

    /* Estilo del Título Infantil */
    .title-madai {{
        font-family: 'Comic Sans MS', 'Chalkboard SE', 'Quicksand', sans-serif;
        font-size: 2.6rem;
        font-weight: 900;
        background: linear-gradient(45deg, #7B2CBF, #FF007F, #FF9F1C, #2B9348);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        padding: 0;
        line-height: 1.1;
    }}
    
    .subtitle-madai {{
        font-family: 'Quicksand', sans-serif;
        font-size: 1.05rem;
        font-weight: 600;
        color: #5A189A;
        margin-top: 4px;
        margin-bottom: 0px;
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
        horas_add = 2
        if "1" in duracion_str:
            horas_add = 1
        elif "3" in duracion_str:
            horas_add = 3
        elif "4" in duracion_str:
            horas_add = 4
        
        dt_fin = dt_inicio + timedelta(hours=horas_add)
        return f"{dt_inicio.strftime('%I:%M %p')} a {dt_fin.strftime('%I:%M %p')}"
    except Exception:
        return f"{hora_inicio_str} ({duracion_str})"

def obtener_eventos():
    res = supabase.table("eventos").select("*, personal(*)").execute()
    return res.data if res.data else []

# ==============================================================================
# 5. MODALES
# ==============================================================================
def modal_asignar_personal(evento):
    e_id = int(evento["id"])
    
    @st.dialog("👤 Asignar / Editar Personal")
    def _mostrar_dialog():
        st.write(f"**Evento:** {evento.get('evento', '')} - {evento.get('cliente', '')}")
        
        res_p = supabase.table("personal").select("*").eq("evento_id", e_id).execute()
        datos_p = res_p.data[0] if res_p.data else {}

        with st.form(key=f"form_personal_{e_id}"):
            animador = st.text_input("🎤 **Animador(a)**", value=datos_p.get("animador", ""))
            dalinas = st.text_input("💃 **Dalinas**", value=datos_p.get("dalinas", ""))
            num_dalinas = st.number_input("**Número de Dalinas**", min_value=0, max_value=20, value=int(datos_p.get("num_dalinas", 0)))
            dj = st.text_input("🎧 **DJ**", value=datos_p.get("dj", ""))
            staff = st.text_input("🛠️ **Staff**", value=datos_p.get("staff", ""))
            duracion = st.selectbox("⏱️ **Duración del Show**", ["1 hora", "2 horas", "3 horas", "4 horas"], index=1)
            detalles = st.text_area("📝 **Notas / Observaciones**", value=datos_p.get("detalles", ""))

            if st.form_submit_button("💾 Guardar Personal", use_container_width=True):
                payload = {
                    "evento_id": e_id,
                    "animador": animador,
                    "dalinas": dalinas,
                    "num_dalinas": num_dalinas,
                    "dj": dj,
                    "staff": staff,
                    "duracion": duracion,
                    "detalles": detalles
                }
                if datos_p:
                    supabase.table("personal").update(payload).eq("id", datos_p["id"]).execute()
                else:
                    supabase.table("personal").insert(payload).execute()
                
                st.success("¡Personal guardado correctamente!")
                st.rerun()

    _mostrar_dialog()

def modal_ver_ficha(evento):
    e_id = int(evento["id"])
    nombre_evento = evento.get("evento", "Sin Nombre")
    
    @st.dialog(f"🎉 {nombre_evento}")
    def _mostrar_dialog():
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
        st.markdown(f'<div class="event-title">🎉 {ev.get("evento", "Sin Nombre")} {tipo_str}</div>', unsafe_allow_html=True)
        
        if tipo_raw.strip().lower() == "deco":
            st.markdown(f'<div class="data-line">⏰ <b>Hora:</b> {ev.get("hora_contrato", ev.get("hora_citacion", "04:30 PM"))}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="data-line">⏰ <b>Horario:</b> {rango_horas} (Citación: {ev.get("hora_citacion", "04:00 PM")})</div>', unsafe_allow_html=True)
            
        st.markdown(f'<div class="data-line">👤 <b>Cliente:</b> {ev.get("cliente", "N/A")} | 📱 <b>Tel:</b> {ev.get("telefono", "N/A")}</div>', unsafe_allow_html=True)
        
        if "local" not in marca:
            st.markdown(f'<div class="data-line">📍 <b>Lugar:</b> {ev.get("direccion", "N/A")}</div>', unsafe_allow_html=True)
            
        desc_raw = str(ev.get("descripcion", "") or "").strip()
        contrato_show = "SHOW" in desc_raw.upper() or "SHOW" in tipo_raw.upper()

        if "local" in marca and contrato_show:
            st.markdown(f'<div class="data-line">🎭 <b>Show:</b> {rango_horas}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="data-line">💵 <b>Monto Show:</b> S/ {costo:.0f}</div>', unsafe_allow_html=True)
        else:
            if desc_raw:
                solo_desc = desc_raw.replace("Alquiler:", "").split("(")[0].strip()
                if solo_desc:
                    st.markdown(f'<div class="data-line">📦 <b>Alquiler:</b> {solo_desc}</div>', unsafe_allow_html=True)

        st.markdown(f'<div class="data-line">💵 <b>Adelanto:</b> S/ {adelanto:.0f} | 💰 <b style="color: #D90429;">Pendiente: S/ {pendiente:.0f}</b></div>', unsafe_allow_html=True)

        st.markdown(f'<div class="{header_class}">👥 Personal Asignado</div>', unsafe_allow_html=True)

        tiene_personal = False
        if p_data:
            animador = p_data.get("animador", "")
            dalinas = p_data.get("dalinas", "")
            dj = p_data.get("dj", "")
            staff = p_data.get("staff", "")

            if (animador and animador != "Ninguno(a)") or dalinas or dj or staff:
                tiene_personal = True

        if tiene_personal:
            st.markdown(f'<div class="data-line">🎤 <b>Animador(a):</b> {p_data.get("animador", "Ninguno(a)")}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="data-line">💃 <b>Dalinas ({p_data.get("num_dalinas", 0)}):</b> {p_data.get("dalinas", "Ninguna")}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="data-line">🎧 <b>DJ:</b> {p_data.get("dj", "N/A")} | 🛠️ <b>Staff:</b> {p_data.get("staff", "N/A")}</div>', unsafe_allow_html=True)
            if p_data.get('detalles'):
                st.markdown(f'<div class="data-line" style="margin-top:6px; font-style:italic;">📝 <b>Notas:</b> {p_data.get("detalles")}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="data-line" style="color: #D90429;">⚠️ Aún no se ha asignado personal a este evento.</div>', unsafe_allow_html=True)

        st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)

        st.markdown('<div class="btn-modificar-amarillo">', unsafe_allow_html=True)
        if st.button("✏️ Modificar Personal", use_container_width=True, key=f"btn_mod_pers_{ev['id']}"):
            modal_asignar_personal(ev)
        st.markdown('</div>', unsafe_allow_html=True)

    _mostrar_dialog()

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
                if (animador and animador != "Ninguno(a)") or dalinas or dj or staff:
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
                linea_detalle_html = f'<div class="data-line">🎭 <b>Show:</b> {rango_horas}</div><div class="data-line">💵 <b>Monto Show:</b> S/ {costo:.0f}</div>'
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
                f'<div class="data-line">💰 <b>Total:</b> S/ {costo:.0f} | <b style="color: #D90429;">Pendiente: S/ {pendiente:.0f}</b></div>'
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
                                modal_asignar_personal(ev)
                        with col_btn2:
                            if st.button("📋 Ver Ficha", key=f"{key_prefix}_btn_ver_{ev['id']}", use_container_width=True):
                                modal_ver_ficha(ev)
                    else:
                        if st.button("📋 Ver Ficha", key=f"{key_prefix}_btn_ver_{ev['id']}", use_container_width=True):
                            modal_ver_ficha(ev)

# ==============================================================================
# 7. CABECERA PRINCIPAL (LOGO + TÍTULO COLORIDO)
# ==============================================================================
col_logo, col_titulo = st.columns([1, 5], vertical_alignment="center")

with col_logo:
    if os.path.exists("logo.jpeg"):
        st.image("logo.jpeg", width=95)

with col_titulo:
    st.markdown('<div class="title-madai">AGENDA VIRTUAL MADAI</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle-madai">🎈 Control & Gestión de Eventos Infantiles 🎈</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ==============================================================================
# 8. INTERFAZ PRINCIPAL Y NAVEGACIÓN
# ==============================================================================
tabs = ["📅 Eventos del Día", "📆 Próximos Eventos", "➕ Registrar Evento"]

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

st.markdown("---")

# ------------------------------------------------------------------------------
# PESTAÑA 1: EVENTOS DEL DÍA
# ------------------------------------------------------------------------------
if tab_seleccionada == "📅 Eventos del Día":
    st.subheader("📅 Eventos del Día de Hoy")
    hoy_str = str(date.today())
    eventos_todos = obtener_eventos()
    eventos_hoy = [e for e in eventos_todos if str(e.get("fecha")) == hoy_str]
    renderizar_lista_eventos(eventos_hoy, key_prefix="hoy")

# ------------------------------------------------------------------------------
# PESTAÑA 2: PRÓXIMOS EVENTOS
# ------------------------------------------------------------------------------
elif tab_seleccionada == "📆 Próximos Eventos":
    st.subheader("📆 Próximos Eventos")
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
# PESTAÑA 3: REGISTRAR EVENTO
# ------------------------------------------------------------------------------
elif tab_seleccionada == "➕ Registrar Evento":
    st.subheader("➕ Registrar Nuevo Evento")

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

        agregar_alquiler = st.checkbox("➕ **Agregar Alquiler**")
        
        desc_alquiler = ""
        monto_alquiler = 0
        
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

        monto_a = st.number_input("**Monto de Adelanto (S/)**", min_value=0, step=10, value=100)
        pendiente_calc = max(0, costo_t - monto_a)
        
        if agregar_alquiler:
            st.info(f"💰 **Monto Total (incluye Alquiler):** S/ {costo_t}")
            
        st.markdown(f"🔴 **Pendiente de Pago:** <b style='color: #D90429; font-size: 1.1rem;'>S/ {pendiente_calc}</b>", unsafe_allow_html=True)

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
                "descripcion": f"Alquiler: {desc_alquiler} (S/ {monto_alquiler})" if agregar_alquiler and desc_alquiler else ""
            }
            supabase.table("eventos").insert(nuevo_registro).execute()
            
            st.session_state["tab_activa"] = tabs[0]
            st.rerun()
