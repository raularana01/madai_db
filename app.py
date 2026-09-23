import streamlit as st
from datetime import date, datetime, timedelta
from supabase import create_client, Client

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
# 2. ESTILOS CSS PERSONALIZADOS
# ==============================================================================
st.markdown("""
    <style>
    /* Estilos generales de tarjetas */
    .card-madai, .card-risuena, .card-alquiler {
        padding: 0 0 12px 0;
        border-radius: 8px;
        margin-bottom: 12px;
    }

    /* Encabezados de marcas */
    .header-madai {
        background-color: #7B2CBF;
        color: white;
        padding: 6px 12px;
        font-weight: bold;
        font-size: 0.95rem;
        border-radius: 4px 4px 0 0;
    }
    .header-risuena {
        background-color: #2B9348;
        color: white;
        padding: 6px 12px;
        font-weight: bold;
        font-size: 0.95rem;
        border-radius: 4px 4px 0 0;
    }
    .header-alquiler {
        background-color: #023E8A;
        color: white;
        padding: 6px 12px;
        font-weight: bold;
        font-size: 0.95rem;
        border-radius: 4px 4px 0 0;
    }

    /* Formato de texto interno de tarjeta */
    .event-title {
        font-size: 1.15rem;
        font-weight: bold;
        color: #111;
        padding: 8px 12px 4px 12px;
    }
    .data-line {
        font-size: 0.95rem;
        color: #222;
        padding: 2px 12px;
    }

    /* Botón amarillo personalizado */
    .btn-modificar-amarillo button {
        background-color: #FFC107 !important;
        color: #000 !important;
        font-weight: bold !important;
        border: none !important;
    }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 3. FUNCIONES AUXILIARES Y FORMATO
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

def calcular_hora_fin(hora_inicio_str, duracion_str):
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
# 4. MODAL ASIGNAR / EDITAR PERSONAL
# ==============================================================================
def modal_asignar_personal(evento):
    e_id = int(evento["id"])
    
    @st.dialog("👤 Asignar / Editar Personal")
    def _mostrar_dialog():
        st.write(f"**Evento:** {evento.get('evento', '')} - {evento.get('cliente', '')}")
        
        res_p = supabase.table("personal").select("*").eq("evento_id", e_id).execute()
        datos_p = res_p.data[0] if res_p.data else {}

        with st.form(key=f"form_personal_{e_id}"):
            animador = st.text_input("🎤 Animador(a)", value=datos_p.get("animador", ""))
            dalinas = st.text_input("💃 Dalinas", value=datos_p.get("dalinas", ""))
            num_dalinas = st.number_input("Número de Dalinas", min_value=0, max_value=20, value=int(datos_p.get("num_dalinas", 0)))
            dj = st.text_input("🎧 DJ", value=datos_p.get("dj", ""))
            staff = st.text_input("🛠️ Staff", value=datos_p.get("staff", ""))
            duracion = st.selectbox("⏱️ Duración del Show", ["1 hora", "2 horas", "3 horas", "4 horas"], index=1)
            detalles = st.text_area("📝 Notas / Observaciones", value=datos_p.get("detalles", ""))

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

# ==============================================================================
# 5. MODAL FICHA DETALLADA
# ==============================================================================
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
        tipo_str = f"({ev.get('tipo', 'Show')})" if ev.get('tipo') else ""

        marca = str(ev.get("marca", "MADAI")).upper()
        if "LOCAL" in marca or "ALQUILER" in marca:
            header_class = "header-alquiler"
            color_fondo = "#A2D2FF"
            nombre_marca_header = "LOCAL / ALQUILER"
        elif "RISUEÑA" in marca:
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
        st.markdown(f'<div class="data-line">⏰ <b>Horario:</b> {rango_horas} (Citación: {ev.get("hora_citacion", "04:00 PM")})</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="data-line">👤 <b>Cliente:</b> {ev.get("cliente", "N/A")} | 📱 <b>Tel:</b> {ev.get("telefono", "N/A")}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="data-line">📍 <b>Lugar:</b> {ev.get("direccion", "N/A")}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="data-line">💵 <b>Adelanto:</b> S/ {adelanto:.2f} | 💰 <b style="color: #D90429;">Pendiente: S/ {pendiente:.2f}</b></div>', unsafe_allow_html=True)

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
# 6. FUNCIÓN COMPONENTES TARJETA (REUTILIZABLE)
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
            tipo_str = f"({ev.get('tipo', 'Show')})" if ev.get('tipo') else ""
            
            marca_str = str(ev.get('marca', 'MADAI')).upper()
            
            if "LOCAL" in marca_str or "ALQUILER" in marca_str:
                card_class = "card-alquiler"
                header_class = "header-alquiler"
                card_bg = "#A2D2FF"
                card_border = "#023E8A"
                nombre_marca = "LOCAL / ALQUILER"
            elif "RISUEÑA" in marca_str:
                card_class = "card-risuena"
                header_class = "header-risuena"
                card_bg = "#B7E4C7"
                card_border = "#2B9348"
                nombre_marca = "SHOWS RISUEÑA"
            else:
                card_class = "card-madai"
                header_class = "header-madai"
                card_bg = "#E0B0FF"
                card_border = "#7B2CBF"
                nombre_marca = "DECORACIONES MADAI"
            
            personal_lista = ev.get("personal", [])
            p_data = {}
            if isinstance(personal_lista, list) and len(personal_lista) > 0:
                p_data = personal_lista[0]
            elif isinstance(personal_lista, dict):
                p_data = personal_lista
            
            tiene_personal = False
            if p_data:
                animador = p_data.get("animador", "")
                dalinas = p_data.get("dalinas", "")
                dj = p_data.get("dj", "")
                staff = p_data.get("staff", "")
                if (animador and animador != "Ninguno(a)") or dalinas or dj or staff:
                    tiene_personal = True

            es_alquiler_local = "LOCAL" in marca_str or "ALQUILER" in marca_str
            contrato_show = "SHOW" in str(ev.get("descripcion", "")).upper() or "SHOW" in tipo_str.upper()

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

                div.st-key-{key_prefix}_event_card_{ev['id']} .card-madai,
                div.st-key-{key_prefix}_event_card_{ev['id']} .card-risuena,
                div.st-key-{key_prefix}_event_card_{ev['id']} .card-alquiler {{
                    margin-bottom: 0 !important;
                    box-shadow: none !important;
                    border-left: 0 !important;
                    border-radius: 0 !important;
                }}

                div.st-key-{key_prefix}_event_card_{ev['id']} [data-testid="stHorizontalBlock"] {{
                    gap: 1rem !important;
                    padding: 0 14px !important;
                    margin-top: 2px !important;
                }}

                div.st-key-{key_prefix}_event_card_{ev['id']} [data-testid="stButton"] {{
                    margin: 0 !important;
                }}

                div.st-key-{key_prefix}_event_card_{ev['id']} [data-testid="stButton"] button {{
                    width: 100% !important;
                    border-radius: 7px !important;
                    margin: 0 !important;
                }}
                </style>
            """, unsafe_allow_html=True)

            with st.container(key=f"{key_prefix}_event_card_{ev['id']}"):
                st.markdown(f"""
                    <div class="{card_class}" style="margin-bottom:0;">
                        <div class="{header_class}" style="margin-top: 0 !important; margin-bottom: 10px !important;">🏷️ {nombre_marca}</div>
                        <div class="event-title">🎉 {ev.get('evento', 'Sin Nombre')} {tipo_str}</div>
                        <div class="data-line">📅 <b>Fecha:</b> {formatear_fecha_larga(ev.get('fecha', ''))}</div>
                        <div class="data-line">⏰ <b>Hora:</b> {ev.get('hora_contrato', '04:30 PM')} | <b>Citación:</b> {ev.get('hora_citacion', '04:00 PM')}</div>
                        <div class="data-line">👤 <b>Cliente:</b> {ev.get('cliente', 'N/A')} | 📱 <b>Tel:</b> {ev.get('telefono', 'N/A')}</div>
                        <div class="data-line">📍 <b>Lugar:</b> {ev.get('direccion', 'N/A')}</div>
                        <div class="data-line">💰 <b>Total:</b> S/ {costo:.0f} | <b style="color: #D90429;">Pendiente: S/ {pendiente:.0f}</b></div>
                    </div>
                """, unsafe_allow_html=True)

                if es_alquiler_local and not contrato_show:
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
# 7. INTERFAZ PRINCIPAL CON PESTAÑAS (TABS)
# ==============================================================================
st.title("📌 Agenda Virtual MADAI")

tabs = ["📅 Eventos del Día", "📆 Próximos Eventos", "➕ Registrar Evento"]

if "tab_activa" not in st.session_state:
    st.session_state["tab_activa"] = tabs[0]

tab_seleccionada = st.radio("Navegación", tabs, horizontal=True, label_visibility="collapsed")
st.session_state["tab_activa"] = tab_seleccionada

st.markdown("---")

# ------------------------------------------------------------------------------
# PESTAÑA 1: EVENTOS DEL DÍA
# ------------------------------------------------------------------------------
if st.session_state["tab_activa"] == "📅 Eventos del Día":
    st.subheader("📅 Eventos del Día de Hoy")
    
    hoy_str = str(date.today())
    eventos_todos = obtener_eventos()
    eventos_hoy = [e for e in eventos_todos if str(e.get("fecha")) == hoy_str]
    
    renderizar_lista_eventos(eventos_hoy, key_prefix="hoy")

# ------------------------------------------------------------------------------
# PESTAÑA 2: PRÓXIMOS EVENTOS (CORREGIDA CON 'days=3')
# ------------------------------------------------------------------------------
elif st.session_state["tab_activa"] == "📆 Próximos Eventos":
    st.subheader("📆 Próximos Eventos")
    
    hoy = date.today()
    limite_3_dias = hoy + timedelta(days=3)
    
    col_f1, col_f2 = st.columns([1, 2])
    with col_f1:
        fecha_filtrada = st.date_input(
            "🔎 Filtrar por fecha específica:",
            value=None,
            help="Selecciona una fecha para ver solo sus eventos, o borra el campo para ver los próximos 3 días."
        )

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
elif st.session_state["tab_activa"] == "➕ Registrar Evento":
    st.subheader("➕ Registrar Nuevo Evento")
    
    with st.form("form_nuevo_evento", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            marca = st.selectbox("Marca / Empresa", ["DECORACIONES MADAI", "SHOWS RISUEÑA", "LOCAL / ALQUILER"])
            evento_nom = st.text_input("Nombre del Evento (ej: Cumpleaños de Lucas)")
            cliente = st.text_input("Nombre del Cliente")
            telefono = st.text_input("Teléfono del Cliente")
            direccion = st.text_input("Lugar / Dirección del Evento")
        
        with col2:
            fecha_e = st.date_input("Fecha del Evento", value=date.today())
            hora_c = st.text_input("Hora del Contrato", value="04:30 PM")
            hora_cit = st.text_input("Hora de Citación", value="04:00 PM")
            costo_t = st.number_input("Costo Total (S/)", min_value=0.0, step=10.0)
            monto_a = st.number_input("Monto Adelanto (S/)", min_value=0.0, step=10.0)
            tipo_e = st.selectbox("Tipo", ["Show Infantil", "Alquiler de Local", "Decoración", "Otros"])

        if st.form_submit_button("📌 Guardar Evento", use_container_width=True):
            nuevo_registro = {
                "marca": marca,
                "evento": evento_nom,
                "cliente": cliente,
                "telefono": telefono,
                "direccion": direccion,
                "fecha": str(fecha_e),
                "hora_contrato": hora_c,
                "hora_citacion": hora_cit,
                "costo_total": costo_t,
                "monto_adelanto": monto_a,
                "tipo": tipo_e
            }
            supabase.table("eventos").insert(nuevo_registro).execute()
            st.success("¡Evento registrado con éxito!")
            st.rerun()
