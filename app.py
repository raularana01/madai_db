import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, timedelta, date
import re

# ==============================================================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS CSS
# ==============================================================================
st.set_page_config(
    page_title="Agenda Madai",
    page_icon="📅",
    layout="wide"
)

st.markdown("""
    <style>
    /* Reducir superposición y dar espaciado adecuado dentro del modal */
    div[data-testid="stDialog"] div[data-testid="stVerticalBlock"] {
        gap: 0.8rem !important;
        padding-top: 5px !important;
    }

    /* Encabezados Ficha */
    .header-madai {
        background-color: #7B2CBF !important;
        color: white !important;
        padding: 8px 12px;
        border-radius: 6px;
        text-align: center;
        font-size: 14px;
        font-weight: bold;
        margin-top: 6px !important;
        margin-bottom: 8px !important;
        text-transform: capitalize;
        width: 100%;
    }

    .header-risuena {
        background-color: #2B9348 !important;
        color: white !important;
        padding: 8px 12px;
        border-radius: 6px;
        text-align: center;
        font-size: 14px;
        font-weight: bold;
        margin-top: 6px !important;
        margin-bottom: 8px !important;
        text-transform: capitalize;
        width: 100%;
    }

    .header-alquiler {
        background-color: #023E8A !important;
        color: white !important;
        padding: 8px 12px;
        border-radius: 6px;
        text-align: center;
        font-size: 14px;
        font-weight: bold;
        margin-top: 6px !important;
        margin-bottom: 8px !important;
        text-transform: capitalize;
        width: 100%;
    }

    /* Estilo para el botón Modificar Personal en tono amarillo */
    .btn-modificar-amarillo button {
        background-color: #FFC107 !important;
        color: #212529 !important;
        border: 1px solid #FFB300 !important;
        font-weight: bold !important;
        border-radius: 8px !important;
        padding: 8px 16px !important;
        transition: all 0.2s ease-in-out;
    }

    .btn-modificar-amarillo button:hover {
        background-color: #FFB300 !important;
        color: #000000 !important;
        border-color: #FFA000 !important;
    }

    /* Tarjetas principales con colores intensos */
    .card-madai {
        background-color: #E0B0FF !important;
        border-radius: 8px;
        padding: 12px 14px;
        margin-bottom: 8px;
        color: #111111 !important;
        box-shadow: 0px 2px 4px rgba(0,0,0,0.12);
        border-left: 6px solid #7B2CBF;
    }

    .card-risuena {
        background-color: #B7E4C7 !important;
        border-radius: 8px;
        padding: 12px 14px;
        margin-bottom: 8px;
        color: #111111 !important;
        box-shadow: 0px 2px 4px rgba(0,0,0,0.12);
        border-left: 6px solid #2B9348;
    }

    .card-alquiler {
        background-color: #A2D2FF !important;
        border-radius: 8px;
        padding: 12px 14px;
        margin-bottom: 8px;
        color: #111111 !important;
        box-shadow: 0px 2px 4px rgba(0,0,0,0.12);
        border-left: 6px solid #023E8A;
    }

    .event-title {
        font-size: 15px;
        font-weight: bold;
        color: #111111 !important;
        margin-top: 6px;
        margin-bottom: 8px;
    }

    .data-line {
        font-size: 13px;
        color: #111111 !important;
        margin-bottom: 8px !important;
        line-height: 1.6 !important;
    }

    .data-line b, .data-line span {
        color: #111111 !important;
    }

    /* Botones compactos de cada tarjeta */
    .botones-tarjeta {
        display: flex;
        gap: 8px;
        margin-top: 4px;
        margin-bottom: 0;
    }

    .botones-tarjeta button {
        background-color: #FFF3B0 !important;
        color: #5C4A00 !important;
        border: 1px solid #F2D675 !important;
        min-height: 34px !important;
        height: 34px !important;
        padding: 2px 8px !important;
        font-size: 13px !important;
        line-height: 1.1 !important;
        border-radius: 6px !important;
    }

    .botones-tarjeta button:hover {
        background-color: #FFE98A !important;
        color: #4A3B00 !important;
        border-color: #E8C94A !important;
    }

    .botones-tarjeta button:active {
        background-color: #FFE27A !important;
    }

    </style>
""", unsafe_allow_html=True)


# ==============================================================================
# 2. CONEXIÓN A SUPABASE
# ==============================================================================
@st.cache_resource
def init_supabase() -> Client:
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"⚠️ Error al conectar con Supabase. Revisa Secrets. Detalle: {e}")
        st.stop()

supabase = init_supabase()


# ==============================================================================
# 3. FUNCIONES AUXILIARES
# ==============================================================================
def formatear_fecha_larga(fecha_str):
    dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    try:
        dt = datetime.strptime(str(fecha_str), "%Y-%m-%d")
        nom_dia = dias[dt.weekday()]
        nom_mes = meses[dt.month - 1]
        return f"{nom_dia}, {dt.day} de {nom_mes} de {dt.year}"
    except Exception:
        return str(fecha_str)

def calcular_hora_fin(hora_inicio_str, duracion_str):
    if not duracion_str or str(duracion_str).strip() == "":
        duracion_str = "2 horas"
        
    try:
        match = re.search(r"(\d+(\.\d+)?)", str(duracion_str))
        if not match:
            return f"{hora_inicio_str} ({duracion_str})"
        
        horas_sumar = float(match.group(1))
        hora_clean = str(hora_inicio_str).strip().upper()
        dt_inicio = None
        
        for fmt in ["%I:%M %p", "%I:%M%p", "%H:%M"]:
            try:
                dt_inicio = datetime.strptime(hora_clean, fmt)
                break
            except ValueError:
                pass
                
        if not dt_inicio:
            return f"{hora_inicio_str} ({duracion_str})"
            
        dt_fin = dt_inicio + timedelta(hours=horas_sumar)
        hora_fin_formatted = dt_fin.strftime("%I:%M %p").lstrip("0")
        return f"{hora_inicio_str} a {hora_fin_formatted}"
    except Exception:
        return f"{hora_inicio_str} ({duracion_str})"


# ==============================================================================
# 4. OPERACIONES DE BASE DE DATOS Y FILTROS
# ==============================================================================
def obtener_eventos():
    try:
        response = supabase.table("eventos").select("*, personal(*)").order("fecha", desc=False).execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"⚠️ Error de conexión al consultar eventos: {e}")
        return []

def guardar_evento(datos_evento):
    res = supabase.table("eventos").insert(datos_evento).execute()
    return res.data

def guardar_personal(evento_id, data_personal):
    try:
        e_id = int(evento_id)
        data_personal["evento_id"] = e_id
        
        existente = supabase.table("personal").select("id").eq("evento_id", e_id).execute()
        
        if existente.data and len(existente.data) > 0:
            res = supabase.table("personal").update(data_personal).eq("evento_id", e_id).execute()
        else:
            res = supabase.table("personal").insert(data_personal).execute()
            
        return True, "Personal asignado correctamente"
    except Exception as e:
        return False, str(e)

def agregar_dalina_callback(state_key):
    if len(st.session_state[state_key]) < 7:
        st.session_state[state_key].append("")


# ==============================================================================
# 5. MODAL PARA ASIGNAR / EDITAR PERSONAL
# ==============================================================================
@st.dialog("👤 Personal del Evento")
def modal_asignar_personal(evento):
    e_id = int(evento["id"])
    res_p = supabase.table("personal").select("*").eq("evento_id", e_id).execute()
    p_data = res_p.data[0] if res_p.data else {}

    state_key = f"dalinas_lista_{evento['id']}"

    if state_key not in st.session_state:
        dalinas_existentes = p_data.get("dalinas", "")
        if dalinas_existentes:
            st.session_state[state_key] = [d.strip() for d in dalinas_existentes.split(",") if d.strip()]
        else:
            st.session_state[state_key] = [""]

    dalinas = st.session_state[state_key]
    cant = len(dalinas)

    st.markdown(f"**💃 Dalinas ({cant}/7):**")

    for i in range(cant):
        if i == cant - 1 and cant < 7:
            col_in, col_btn = st.columns([5, 1])
        else:
            col_in, col_btn = st.columns([1, 0.0001])

        with col_in:
            val_actual = st.session_state[state_key][i]
            st.session_state[state_key][i] = st.text_input(
                f"Dalina {i+1}", 
                value=val_actual, 
                placeholder=f"Nombre Dalina {i+1}", 
                key=f"dal_in_{evento['id']}_{i}",
                label_visibility="collapsed" if i > 0 else "visible"
            )

        if i == cant - 1 and cant < 7:
            with col_btn:
                if i == 0:
                    st.write('<div style="margin-top: 28px;"></div>', unsafe_allow_html=True)
                else:
                    st.write('<div style="margin-top: 4px;"></div>', unsafe_allow_html=True)
                
                st.button(
                    "➕", 
                    key=f"btn_add_dalina_{evento['id']}_{i}", 
                    on_click=agregar_dalina_callback, 
                    args=(state_key,)
                )

    st.write("")

    opciones_animadores = ["Ninguno(a)", "Madai", "Martha", "Eusy", "Antonio", "Jair", "Britny", "Gina"]
    animador_previo = p_data.get("animador", "Ninguno(a)")
    idx_animador = opciones_animadores.index(animador_previo) if animador_previo in opciones_animadores else 0

    animador = st.selectbox("🎤 Animador(a):", opciones_animadores, index=idx_animador, key=f"sel_anim_{evento['id']}")
    dj = st.text_input("🎧 DJ:", value=p_data.get("dj", ""), placeholder="Nombre DJ", key=f"in_dj_{evento['id']}")
    staff = st.text_input("🛠️ Staff:", value=p_data.get("staff", ""), placeholder="Nombre Staff", key=f"in_staff_{evento['id']}")
    
    opciones_duracion = ["1.5 horas", "2 horas", "2.5 horas", "3 horas"]
    duracion_previa = str(p_data.get("duracion", "2 horas")).lower()
    idx_duracion = opciones_duracion.index(duracion_previa) if duracion_previa in opciones_duracion else 1
    
    duracion = st.selectbox("⏳ Duración del Show:", opciones_duracion, index=idx_duracion, key=f"sel_dur_{evento['id']}")
    detalles = st.text_area("📝 Detalles:", value=p_data.get("detalles", ""), placeholder="Observaciones...", key=f"in_det_{evento['id']}")

    st.write("")
    if st.button("💾 Guardar Datos", type="primary", use_container_width=True, key=f"btn_save_{evento['id']}"):
        dalinas_validas = [d.strip() for d in st.session_state[state_key] if d.strip()]
        
        payload = {
            "num_dalinas": len(dalinas_validas),
            "dalinas": ", ".join(dalinas_validas),
            "animador": animador,
            "dj": dj,
            "staff": staff,
            "duracion": duracion,
            "detalles": detalles
        }
        
        exito, msg = guardar_personal(evento["id"], payload)
        
        if exito:
            st.success("✅ ¡Personal guardado correctamente!")
            if "abrir_editar_evento" in st.session_state:
                del st.session_state["abrir_editar_evento"]
            st.rerun()
        else:
            st.error(f"❌ Error al guardar en Supabase: {msg}")


# ==============================================================================
# 6. MODAL FICHA DETALLADA
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

        # Datos de fecha y hora
        fecha_fmt = formatear_fecha_larga(ev.get("fecha", ""))
        duracion_str = p_data.get("duracion", "2 horas") if p_data.get("duracion") else "2 horas"
        hora_inicio = ev.get("hora_contrato", "04:30 PM")
        rango_horas = calcular_hora_fin(hora_inicio, duracion_str)

        costo = float(ev.get('costo_total', 0) or 0)
        adelanto = float(ev.get('monto_adelanto', 0) or 0)
        pendiente = costo - adelanto
        tipo_str = f"({ev.get('tipo', 'Show')})" if ev.get('tipo') else ""

        # Marca y Color
        marca = ev.get("marca", "MADAI").upper()
        if "LOCAL" in marca or "ALQUILER" in marca:
            header_class = "header-alquiler"
            color_fondo = "#A2D2FF"
        elif "RISUEÑA" in marca:
            header_class = "header-risuena"
            color_fondo = "#B7E4C7"
        else:
            header_class = "header-madai"
            color_fondo = "#E0B0FF"

        st.markdown(f"""
            <style>
            div[data-testid="stDialog"] > div:first-child {{
                background-color: {color_fondo} !important;
            }}
            </style>
        """, unsafe_allow_html=True)

        # 1. Cabecera Fecha
        st.markdown(f'<div class="{header_class}">📅 {fecha_fmt}</div>', unsafe_allow_html=True)

        # 2. Título e Información del evento
        st.markdown(f'<div class="event-title">🎉 {ev.get("evento", "Sin Nombre")} {tipo_str}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="data-line">⏰ <b>Horario:</b> {rango_horas} (Citación: {ev.get("hora_citacion", "04:00 PM")})</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="data-line">👤 <b>Cliente:</b> {ev.get("cliente", "N/A")} | 📱 <b>Tel:</b> {ev.get("telefono", "N/A")}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="data-line">📍 <b>Lugar:</b> {ev.get("direccion", "N/A")}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="data-line">💵 <b>Adelanto:</b> S/ {adelanto:.2f} | 💰 <b style="color: #D90429;">Pendiente: S/ {pendiente:.2f}</b></div>', unsafe_allow_html=True)

        # 3. Cabecera Personal
        st.markdown(f'<div class="{header_class}">👥 Personal Asignado</div>', unsafe_allow_html=True)

        # 4. Datos del Personal
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

        # 5. Botón Modificar Personal
        st.markdown('<div class="btn-modificar-amarillo">', unsafe_allow_html=True)
        if st.button("✏️ Modificar Personal", use_container_width=True, key=f"btn_mod_pers_{ev['id']}"):
            st.session_state["abrir_editar_evento"] = ev
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    _mostrar_dialog()


# ==============================================================================
# 7. FUNCIÓN COMPONENTES TARJETA (REUTILIZABLE)
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
                card_bg = "#A2D2FF"
                card_border = "#023E8A"
            elif "RISUEÑA" in marca_str:
                card_class = "card-risuena"
                card_bg = "#B7E4C7"
                card_border = "#2B9348"
            else:
                card_class = "card-madai"
                card_bg = "#E0B0FF"
                card_border = "#7B2CBF"
            
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
# 8. CONTROL DE NAVEGACIÓN Y SESSION STATE
# ==============================================================================
if "abrir_editar_evento" in st.session_state:
    evento_a_editar = st.session_state["abrir_editar_evento"]
    modal_asignar_personal(evento_a_editar)

# Inicializar estados de navegación y formulario
if "tab_activa" not in st.session_state:
    st.session_state["tab_activa"] = "📅 Eventos del Día"

if "form_id" not in st.session_state:
    st.session_state["form_id"] = 0


# ==============================================================================
# 9. VISTA PRINCIPAL CON NAVEGACIÓN DINÁMICA
# ==============================================================================
st.title("📅 Agenda Madai")

# Radio horizontal con las 3 pestañas requeridas
opcion_menu = st.radio(
    "Navegación",
    ["📅 Eventos del Día", "📆 Próximos Eventos", "➕ Registrar Evento"],
    index=["📅 Eventos del Día", "📆 Próximos Eventos", "➕ Registrar Evento"].index(st.session_state["tab_activa"]) if st.session_state["tab_activa"] in ["📅 Eventos del Día", "📆 Próximos Eventos", "➕ Registrar Evento"] else 0,
    horizontal=True,
    label_visibility="collapsed"
)

# Sincronizar el radio con el estado global
st.session_state["tab_activa"] = opcion_menu
st.markdown("<hr style='margin-top: 5px; margin-bottom: 15px;'/>", unsafe_allow_html=True)


# ------------------------------------------------------------------------------
# PESTAÑA 1: EVENTOS DEL DÍA
# ------------------------------------------------------------------------------
if st.session_state["tab_activa"] == "📅 Eventos del Día":
    hoy_str = str(date.today())
    eventos_todos = obtener_eventos()
    
    # Filtrar solo eventos de HOY
    eventos_hoy = [ev for ev in eventos_todos if str(ev.get("fecha")) == hoy_str]
    
    st.subheader(f"📌 Eventos programados para hoy ({formatear_fecha_larga(hoy_str)})")
    renderizar_lista_eventos(eventos_hoy, key_prefix="hoy")


# ------------------------------------------------------------------------------
# PESTAÑA 2: PRÓXIMOS EVENTOS (MÁX. 3 DÍAS CON FILTRO DE FECHA)
# ------------------------------------------------------------------------------
elif st.session_state["tab_activa"] == "📆 Próximos Eventos":
    st.subheader("📆 Próximos Eventos")
    
    hoy = date.today()
    limite_3_dias = hoy + timedelta(dias=3)
    
    col_f1, col_f2 = st.columns([1, 2])
    with col_f1:
        fecha_filtrada = st.date_input(
            "🔎 Filtrar por fecha específica:",
            value=None,
            help="Selecciona una fecha para ver solo sus eventos, o borra el campo para ver los próximos 3 días."
        )

    eventos_todos = obtener_eventos()

    if fecha_filtrada:
        # Si eligió una fecha en el date_input
        str_f = str(fecha_filtrada)
        eventos_filtrados = [ev for ev in eventos_todos if str(ev.get("fecha")) == str_f]
        st.write(f"Mostrando resultados para: **{formatear_fecha_larga(str_f)}**")
    else:
        # Si no hay fecha elegida, mostrar eventos de hoy a los próximos 3 días
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
# PESTAÑA 3: REGISTRAR NUEVO EVENTO
# ------------------------------------------------------------------------------
elif st.session_state["tab_activa"] == "➕ Registrar Evento":
    st.header("Registrar Nuevo Evento")
    
    # ID incremental para limpiar formulario completamente tras guardar
    f_id = st.session_state["form_id"]
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        marca = st.selectbox("Marca", ["MADAI", "RISUEÑA", "LOCAL"], key=f"marca_{f_id}")
        
        # MARCA LOCAL
        if marca == "LOCAL":
            tipo = "Alquiler de Local"
            evento = st.text_input("Temática del Evento", key=f"evt_{f_id}")
            fecha = st.date_input("Fecha del Evento", key=f"fec_{f_id}")
            hora_contrato = st.text_input("Hora del Alquiler", value="03:00 PM", key=f"hcon_{f_id}")
            cliente = st.text_input("Nombre del Cliente", key=f"cli_{f_id}")
            telefono = st.text_input("Celular", key=f"tel_{f_id}")
            
            contrata_show = st.checkbox("¿Desea agregar Show o Animación?", key=f"cshow_{f_id}")
            if contrata_show:
                hora_inicio_show = st.text_input("Hora Inicio del Show", value="04:30 PM", key=f"hishow_{f_id}")
                monto_show = st.number_input("Monto del Show (S/)", min_value=0.0, step=10.0, value=300.0, key=f"mshow_{f_id}")
            else:
                hora_inicio_show = ""
                monto_show = 0.0
            
            contrata_alquiler_extra = False
            monto_alquiler_extra = 0.0
            monto_show_sd = 0.0
            monto_deco_sd = 0.0

        else:
            opciones_tipo = ["Show", "Decoración", "Show + Decoración", "Alquiler de otros"]
            tipo = st.selectbox("Tipo de Evento", opciones_tipo, key=f"tipo_{f_id}")
            
            # SI ES "Alquiler de otros"
            if tipo == "Alquiler de otros":
                evento = st.text_input("Descripción del Alquiler", key=f"evt_{f_id}")
                direccion = st.text_input("Dirección / Ubicación", key=f"dir_{f_id}")
                cliente = st.text_input("Nombre del Cliente", key=f"cli_{f_id}")
                telefono = st.text_input("Celular", key=f"tel_{f_id}")
                fecha = st.date_input("Fecha del Evento", key=f"fec_{f_id}")
                hora_contrato = st.text_input("Hora", value="04:00 PM", key=f"hcon_{f_id}")
                
                contrata_show = False
                contrata_alquiler_extra = False
                monto_alquiler_extra = 0.0
                monto_show_sd = 0.0
                monto_deco_sd = 0.0
            
            # SI ES "Show + Decoración"
            elif tipo == "Show + Decoración":
                fecha = st.date_input("Fecha del Evento", key=f"fec_{f_id}")
                evento = st.text_input("Nombre del Evento / Cumpleañero(a)", key=f"evt_{f_id}")
                cliente = st.text_input("Nombre del Cliente", key=f"cli_{f_id}")
                telefono = st.text_input("Teléfono", key=f"tel_{f_id}")
                
                monto_show_sd = st.number_input("Monto del Show (S/)", min_value=0.0, step=10.0, value=300.0, key=f"mshowsd_{f_id}")
                monto_deco_sd = st.number_input("Monto de la Decoración (S/)", min_value=0.0, step=10.0, value=250.0, key=f"mdecosd_{f_id}")
                
                contrata_show = False
                contrata_alquiler_extra = st.checkbox("¿Desea agregar Alquiler de otros?", key=f"calqex_{f_id}")
                if contrata_alquiler_extra:
                    desc_alquiler_extra = st.text_input("Descripción del Alquiler", key=f"descalqex_{f_id}")
                    monto_alquiler_extra = st.number_input("Monto del Alquiler (S/)", min_value=0.0, step=10.0, value=150.0, key=f"malqex_{f_id}")
                else:
                    desc_alquiler_extra = ""
                    monto_alquiler_extra = 0.0
            
            # SI ES "Show" O "Decoración"
            else:
                fecha = st.date_input("Fecha del Evento", key=f"fec_{f_id}")
                evento = st.text_input("Nombre del Evento / Cumpleañero(a)", key=f"evt_{f_id}")
                cliente = st.text_input("Nombre del Cliente", key=f"cli_{f_id}")
                telefono = st.text_input("Teléfono", key=f"tel_{f_id}")
                
                contrata_show = False
                monto_show_sd = 0.0
                monto_deco_sd = 0.0
                
                contrata_alquiler_extra = st.checkbox("¿Desea agregar Alquiler de otros?", key=f"calqex_{f_id}")
                if contrata_alquiler_extra:
                    desc_alquiler_extra = st.text_input("Descripción del Alquiler", key=f"descalqex_{f_id}")
                    monto_alquiler_extra = st.number_input("Monto del Alquiler (S/)", min_value=0.0, step=10.0, value=150.0, key=f"malqex_{f_id}")
                else:
                    desc_alquiler_extra = ""
                    monto_alquiler_extra = 0.0

    with col_b:
        if marca == "LOCAL":
            hora_citacion = st.text_input("Hora Citación Staff", value="02:30 PM", key=f"hcit_{f_id}")
            direccion = st.text_input("Dirección / Ubicación", value="Local MADAI", key=f"dir_{f_id}")
            
            costo_base_alquiler = 600.0
            costo_total = costo_base_alquiler + monto_show
            
            if contrata_show:
                st.markdown(f"**Costo Total Calculado:** S/ {costo_total:.2f} *(Base Local S/ 600.00 + Show S/ {monto_show:.2f})*")
            else:
                st.markdown(f"**Costo Total:** S/ {costo_total:.2f}")

            monto_adelanto = st.number_input("Monto de Adelanto (S/)", min_value=0.0, max_value=costo_total, step=10.0, value=200.0, key=f"madel_{f_id}")
            saldo_pendiente = costo_total - monto_adelanto
            st.markdown(f"**Saldo Pendiente:** <span style='color: #D90429; font-weight: bold;'>S/ {saldo_pendiente:.2f}</span>", unsafe_allow_html=True)

        elif tipo == "Alquiler de otros":
            hora_citacion = "N/A"
            costo_total = st.number_input("Costo Total (S/)", min_value=0.0, step=10.0, value=200.0, key=f"ctot_{f_id}")
            monto_adelanto = st.number_input("Monto Adelanto (S/)", min_value=0.0, step=10.0, value=50.0, key=f"madel_{f_id}")
            saldo_pendiente = costo_total - monto_adelanto
            st.markdown(f"**Saldo Pendiente:** <span style='color: #D90429; font-weight: bold;'>S/ {saldo_pendiente:.2f}</span>", unsafe_allow_html=True)

        elif tipo == "Show + Decoración":
            hora_contrato = st.text_input("Hora Contrato", value="04:30 PM", key=f"hcon_{f_id}")
            hora_citacion = st.text_input("Hora Citación", value="04:00 PM", key=f"hcit_{f_id}")
            direccion = st.text_input("Dirección / Ubicación", value="", key=f"dir_{f_id}")
            
            costo_total = monto_show_sd + monto_deco_sd + monto_alquiler_extra
            
            if contrata_alquiler_extra:
                st.markdown(f"**Costo Total Calculado:** S/ {costo_total:.2f} *(Show S/ {monto_show_sd:.2f} + Deco S/ {monto_deco_sd:.2f} + Alquiler S/ {monto_alquiler_extra:.2f})*")
            else:
                st.markdown(f"**Costo Total Calculado:** S/ {costo_total:.2f} *(Show S/ {monto_show_sd:.2f} + Deco S/ {monto_deco_sd:.2f})*")
                
            monto_adelanto = st.number_input("Monto Adelanto (S/)", min_value=0.0, step=10.0, value=200.0, key=f"madel_{f_id}")
            saldo_pendiente = costo_total - monto_adelanto
            st.markdown(f"**Saldo Pendiente:** <span style='color: #D90429; font-weight: bold;'>S/ {saldo_pendiente:.2f}</span>", unsafe_allow_html=True)

        else:
            hora_contrato = st.text_input("Hora Contrato", value="04:30 PM", key=f"hcon_{f_id}")
            hora_citacion = st.text_input("Hora Citación", value="04:00 PM", key=f"hcit_{f_id}")
            direccion = st.text_input("Dirección / Ubicación", value="", key=f"dir_{f_id}")
            
            costo_base_servicio = st.number_input("Costo Servicio (S/)", min_value=0.0, step=10.0, value=300.0, key=f"cserv_{f_id}")
            costo_total = costo_base_servicio + monto_alquiler_extra
            
            if contrata_alquiler_extra:
                st.markdown(f"**Costo Total Calculado:** S/ {costo_total:.2f} *(Servicio S/ {costo_base_servicio:.2f} + Alquiler S/ {monto_alquiler_extra:.2f})*")
            else:
                st.markdown(f"**Costo Total:** S/ {costo_total:.2f}")
                
            monto_adelanto = st.number_input("Monto Adelanto (S/)", min_value=0.0, step=10.0, value=100.0, key=f"madel_{f_id}")
            saldo_pendiente = costo_total - monto_adelanto
            st.markdown(f"**Saldo Pendiente:** <span style='color: #D90429; font-weight: bold;'>S/ {saldo_pendiente:.2f}</span>", unsafe_allow_html=True)

    # Notas adicionales automáticas
    notas_extra = ""
    if marca == "LOCAL" and contrata_show:
        notas_extra += f"SHOW ADICIONAL CONTRATADO: Inicio {hora_inicio_show} (S/ {monto_show:.2f}). "
    if contrata_alquiler_extra:
        notas_extra += f"ALQUILER EXTRA CONTRATADO: {desc_alquiler_extra} (S/ {monto_alquiler_extra:.2f}). "

    descripcion = st.text_area("Notas adicionales del evento", value=notas_extra, key=f"desc_{f_id}")
    
    st.write("")
    btn_crear = st.button("Guardar Evento", type="primary", use_container_width=True, key=f"btn_save_evt_{f_id}")
    
    if btn_crear:
        if not evento or not cliente:
            st.error("Por favor completa los datos obligatorios del evento y cliente.")
        else:
            nuevo_payload = {
                "marca": marca,
                "fecha": str(fecha),
                "tipo": tipo,
                "evento": evento,
                "cliente": cliente,
                "telefono": telefono,
                "hora_contrato": hora_contrato,
                "hora_citacion": hora_citacion,
                "direccion": direccion,
                "costo_total": costo_total,
                "monto_adelanto": monto_adelanto,
                "concepto_alquiler": tipo,
                "descripcion": descripcion
            }
            guardar_evento(nuevo_payload)
            
            # Redirigir a la pestaña de eventos del día
            st.session_state["tab_activa"] = "📅 Eventos del Día"
            
            # Resetear el ID del formulario
            st.session_state["form_id"] += 1
            
            st.rerun()
