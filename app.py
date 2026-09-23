import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, timedelta
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

    /* Tarjetas principales de la lista general con mayor intensidad de color */
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
# 4. OPERACIONES DE BASE DE DATOS
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
        marca = ev.get("marca", "Decoraciones MADAI").upper()
        if "ALQUILER" in marca:
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
# 7. CONTROL DE NAVEGACIÓN Y SESSION STATE
# ==============================================================================
if "abrir_editar_evento" in st.session_state:
    evento_a_editar = st.session_state["abrir_editar_evento"]
    modal_asignar_personal(evento_a_editar)


# ==============================================================================
# 8. VISTA PRINCIPAL
# ==============================================================================
st.title("📅 Agenda Madai")

# Control de pestaña activa
if "tab_activa" not in st.session_state:
    st.session_state["tab_activa"] = 0

tab1, tab2 = st.tabs(["📋 Lista de Eventos", "➕ Registrar Evento"])

with tab1:
    eventos = obtener_eventos()
    
    if not eventos:
        st.info("No hay eventos registrados.")
    else:
        cols = st.columns(2)
        for idx, ev in enumerate(eventos):
            with cols[idx % 2]:
                costo = float(ev.get('costo_total', 0) or 0)
                adelanto = float(ev.get('monto_adelanto', 0) or 0)
                pendiente = costo - adelanto
                tipo_str = f"({ev.get('tipo', 'Show')})" if ev.get('tipo') else ""
                
                marca_str = str(ev.get('marca', 'Decoraciones MADAI')).upper()
                
                # Asignación de color de tarjeta según marca
                if "ALQUILER" in marca_str:
                    card_class = "card-alquiler"
                elif "RISUEÑA" in marca_str:
                    card_class = "card-risuena"
                else:
                    card_class = "card-madai"
                
                # Evaluación de personal
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

                # Identificar si es un Alquiler de Local con Show
                es_alquiler_local = "ALQUILER" in marca_str
                contrato_show = "SHOW" in str(ev.get("descripcion", "")).upper() or "SHOW" in tipo_str.upper()

                # Renderizado de Tarjeta
                st.markdown(f"""
                    <div class="{card_class}">
                        <div class="event-title">🎉 {ev.get('evento', 'Sin Nombre')} {tipo_str}</div>
                        <div class="data-line">⏰ <b>Hora:</b> {ev.get('hora_contrato', '04:30 PM')} | <b>Citación:</b> {ev.get('hora_citacion', '04:00 PM')}</div>
                        <div class="data-line">👤 <b>Cliente:</b> {ev.get('cliente', 'N/A')} | 📱 <b>Tel:</b> {ev.get('telefono', 'N/A')}</div>
                        <div class="data-line">📍 <b>Lugar:</b> {ev.get('direccion', 'N/A')}</div>
                        <div class="data-line">💰 <b>Total:</b> S/ {costo:.0f} | <b style="color: #D90429;">Pendiente: S/ {pendiente:.0f}</b></div>
                    </div>
                """, unsafe_allow_html=True)

                # Regla de visibilidad de botones
                # Si es Alquiler de Local SIN Show -> NO MUESTRA BOTONES
                # Si es Alquiler de Local CON Show O cualquier otra marca -> MUESTRA BOTONES
                if es_alquiler_local and not contrato_show:
                    pass  # Sin botones para alquileres puros
                else:
                    if not tiene_personal:
                        col_btn1, col_btn2 = st.columns(2)
                        with col_btn1:
                            if st.button("👤 Asignar Personal", key=f"btn_pers_{ev['id']}", use_container_width=True):
                                modal_asignar_personal(ev)
                        with col_btn2:
                            if st.button("📋 Ver Ficha", key=f"btn_ver_{ev['id']}", use_container_width=True):
                                modal_ver_ficha(ev)
                    else:
                        if st.button("📋 Ver Ficha", key=f"btn_ver_{ev['id']}", use_container_width=True):
                            modal_ver_ficha(ev)

                st.markdown("<div style='margin-bottom: 6px;'></div>", unsafe_allow_html=True)


# ==============================================================================
# TAB 2: REGISTRAR NUEVO EVENTO CON FORMULARIO AJUSTADO
# ==============================================================================
with tab2:
    st.header("Registrar Nuevo Evento")
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        # Selector de Marcas actualizado (sin "Otros")
        marca = st.selectbox("Marca", ["Decoraciones MADAI", "RISUEÑA", "Alquiler de Local"])
        fecha = st.date_input("Fecha del Evento")
        
        # Opciones para tipo de evento (sin "Alquiler de Local")
        opciones_tipo = ["Show", "Decoración", "Show + Decoración", "Alquiler de otros"]
        tipo = st.selectbox("Tipo de Evento", opciones_tipo)
        
        # Lógica si la marca seleccionada es Alquiler de Local
        if marca == "Alquiler de Local":
            hora_inicio_local = st.text_input("Hora de Inicio del Alquiler", value="03:00 PM")
            evento = st.text_input("Nombre del Show / Evento / Cumpleañero(a)")
            cliente = st.text_input("Nombre del Cliente")
            telefono = st.text_input("Teléfono")
            
            # Checkbox para show/animación adicional
            contrata_show = st.checkbox("¿Desea contratar Show o Animación?")
            if contrata_show:
                col_show1, col_show2 = st.columns(2)
                with col_show1:
                    hora_inicio_show = st.text_input("Hora Inicio del Show", value="04:30 PM")
                with col_show2:
                    hora_fin_show = st.text_input("Hora Fin del Show", value="06:30 PM")
            else:
                hora_inicio_show = ""
                hora_fin_show = ""
        else:
            contrata_show = False
            evento = st.text_input("Nombre del Evento / Cumpleañero(a)")
            cliente = st.text_input("Nombre del Cliente")
            telefono = st.text_input("Teléfono")

    with col_b:
        if marca == "Alquiler de Local":
            hora_contrato = hora_inicio_local
            hora_citacion = st.text_input("Hora Citación", value="02:30 PM")
            direccion_default = "Local MADAI"
        else:
            hora_contrato = st.text_input("Hora Contrato", value="04:30 PM")
            hora_citacion = st.text_input("Hora Citación", value="04:00 PM")
            direccion_default = ""
            
        direccion = st.text_input("Dirección / Ubicación", value=direccion_default)
        costo_total = st.number_input("Costo Total (S/)", min_value=0.0, step=10.0, value=300.0)
        monto_adelanto = st.number_input("Monto Adelanto (S/)", min_value=0.0, step=10.0, value=100.0)
        concepto_alquiler = st.text_input("Concepto / Alquiler", value=f"Servicio de {tipo}")

    # Construcción de notas adicionales
    notas_extra = ""
    if marca == "Alquiler de Local" and contrata_show:
        notas_extra = f"SHOW CONTRATADO: {hora_inicio_show} a {hora_fin_show}. "

    descripcion = st.text_area("Notas adicionales del evento", value=notas_extra)
    
    st.write("")
    btn_crear = st.button("Guardar Evento", type="primary", use_container_width=True)
    
    if btn_crear:
        if not evento or not cliente:
            st.error("Por favor completa el nombre del evento y del cliente.")
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
                "concepto_alquiler": concepto_alquiler,
                "descripcion": descripcion
            }
            guardar_evento(nuevo_payload)
            st.success("✅ ¡Evento creado exitosamente!")
            
            # Volver a la pestaña principal y refrescar
            st.session_state["tab_activa"] = 0
            st.rerun()
