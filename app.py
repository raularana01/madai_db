import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, timedelta
import re

# 1. Configuración de página
st.set_page_config(
    page_title="Agenda Madai",
    page_icon="📅",
    layout="wide"
)

# Estilos CSS Ultra-Compactos y Ficha en Cuadro
st.markdown("""
    <style>
    /* Tarjetas de eventos compactas */
    .card-box {
        background-color: #EBD9F3;
        border-radius: 8px;
        padding: 8px 12px;
        margin-bottom: 6px;
        color: #111111;
        box-shadow: 0px 2px 4px rgba(0,0,0,0.05);
    }
    .badge-marca {
        background-color: #7B2CBF;
        color: white;
        padding: 2px 6px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 10px;
        text-transform: uppercase;
    }
    .event-title {
        font-size: 14px;
        font-weight: bold;
        color: #000000;
        margin-bottom: 2px;
    }
    .data-line {
        font-size: 12px;
        color: #111111;
        margin-bottom: 2px;
        line-height: 1.2;
    }
    
    /* Cuadro de la Ficha Detallada */
    .ficha-container {
        border: 2px solid #7B2CBF;
        background-color: #FFFFFF;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.08);
    }
    .ficha-header {
        background-color: #7B2CBF;
        color: white;
        padding: 10px;
        border-radius: 8px;
        text-align: center;
        font-size: 18px;
        font-weight: bold;
        margin-bottom: 14px;
        text-transform: capitalize;
    }
    .ficha-item {
        font-size: 14px;
        color: #222222;
        margin-bottom: 6px;
    }
    .ficha-section-title {
        font-size: 15px;
        font-weight: bold;
        color: #7B2CBF;
        border-bottom: 1px solid #EBD9F3;
        padding-bottom: 4px;
        margin-top: 10px;
        margin-bottom: 8px;
    }
    </style>
""", unsafe_allow_html=True)

# 2. Conexión a Supabase
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

# 3. Funciones Auxiliares (Fechas y Horas)
def formatear_fecha_larga(fecha_str):
    """Convierte YYYY-MM-DD a 'Día, DD de Mes de YYYY'"""
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
    """Suma la duración a la hora de contrato"""
    try:
        match = re.search(r"(\d+(\.\d+)?)", str(duracion_str))
        if not match:
            return f"{hora_inicio_str} (Duración: {duracion_str})"
        
        horas_sumar = float(match.group(1))
        hora_clean = hora_inicio_str.strip().upper()
        dt_inicio = None
        
        for fmt in ["%I:%M %p", "%I:%M%p", "%H:%M"]:
            try:
                dt_inicio = datetime.strptime(hora_clean, fmt)
                break
            except ValueError:
                pass
                
        if not dt_inicio:
            return f"{hora_inicio_str} (+ {duracion_str})"
            
        dt_fin = dt_inicio + timedelta(hours=horas_sumar)
        hora_fin_formatted = dt_fin.strftime("%I:%M %p").lstrip("0")
        return f"{hora_inicio_str} a {hora_fin_formatted}"
    except Exception:
        return f"{hora_inicio_str} (+ {duracion_str})"

# 4. Funciones de Base de Datos
def obtener_eventos():
    response = supabase.table("eventos").select("*, personal(*)").order("fecha", desc=False).execute()
    return response.data

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

# Callback para agregar campos de Dalina
def agregar_dalina_callback(state_key):
    if len(st.session_state[state_key]) < 7:
        st.session_state[state_key].append("")

# 5. Modal para Asignar Personal (Carga y Mantiene Datos Persistentes)
@st.dialog("👤 Asignar Personal al Evento")
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
    duracion = st.text_input("⏳ Duración:", value=p_data.get("duracion", "2 Horas"), placeholder="ej. 2 Horas", key=f"in_dur_{evento['id']}")
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
            st.rerun()
        else:
            st.error(f"❌ Error al guardar en Supabase: {msg}")

# 6. Modal Ficha Detallada (Diseño de Cuadro con Campos Solicitados Únicamente)
# 6. Modal Ficha Detallada (Diseño en Cuadro Nativo sin errores de HTML)
@st.dialog("📋 Ficha del Evento")
def modal_ver_ficha(evento_id):
    e_id = int(evento_id)
    
    res_evento = supabase.table("eventos").select("*").eq("id", e_id).execute()
    if not res_evento.data:
        st.error("No se encontró el evento.")
        return

    evento = res_evento.data[0]
    res_personal = supabase.table("personal").select("*").eq("evento_id", e_id).execute()
    p_data = res_personal.data[0] if res_personal.data else {}

    # Cálculos
    fecha_formateada = formatear_fecha_larga(evento.get("fecha", ""))
    duracion_str = p_data.get("duracion", "2 Horas")
    hora_inicio = evento.get("hora_contrato", "04:30 PM")
    rango_horas = calcular_hora_fin(hora_inicio, duracion_str)

    costo = float(evento.get('costo_total', 0) or 0)
    adelanto = float(evento.get('monto_adelanto', 0) or 0)
    pendiente = costo - adelanto

    # ENCABEZADO GRANDE
    st.markdown(f"""
        <div class="ficha-header">
            📅 {fecha_formateada.title()}
        </div>
    """, unsafe_allow_html=True)

    # CUADRO DE CONTENIDO
    with st.container(border=True):
        st.markdown(f"**🎭 Tipo de Show:** {evento.get('tipo', 'Show Infantil')} ({evento.get('evento', 'Sin Nombre')})")
        st.markdown(f"**⏰ Horario del Show:** {rango_horas}")
        st.markdown(f"**📍 Dirección:** {evento.get('direccion', 'N/A')}")
        
        st.divider()
        
        st.markdown("##### 💰 Información Financiera")
        st.markdown(f"**💵 Monto Adelanto:** S/ {adelanto:.2f}")
        st.markdown(f"**🔴 Saldo Pendiente:** :red[**S/ {pendiente:.2f}**]")
        
        st.divider()
        
        st.markdown("##### 👥 Personal Asignado")
        if p_data:
            st.markdown(f"**🎤 Animador(a):** {p_data.get('animador', 'Ninguno(a)')}")
            st.markdown(f"**💃 Dalinas ({p_data.get('num_dalinas', 0)}):** {p_data.get('dalinas', 'Ninguna')}")
            st.markdown(f"**🎧 DJ:** {p_data.get('dj', 'N/A')}")
            st.markdown(f"**🛠️ Staff:** {p_data.get('staff', 'N/A')}")
            
            if p_data.get('detalles'):
                st.info(f"**📝 Notas:** {p_data.get('detalles')}")
        else:
            st.warning("⚠️ Aún no se ha asignado personal a este evento.")


# 7. Vista Principal
st.title("📅 Agenda Madai")

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
                
                # Tarjeta de evento compacta
                st.markdown(f"""
                    <div class="card-box">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px;">
                            <div class="event-title">🎉 {ev['evento']} {tipo_str}</div>
                            <span class="badge-marca">{ev.get('marca', 'MADAI')}</span>
                        </div>
                        <div class="data-line">⏰ <b>Hora:</b> {ev.get('hora_contrato', '04:30 PM')} | <b>Citación:</b> {ev.get('hora_citacion', '04:00 PM')}</div>
                        <div class="data-line">👤 <b>Cliente:</b> {ev.get('cliente', 'N/A')} | 📱 <b>Tel:</b> {ev.get('telefono', 'N/A')}</div>
                        <div class="data-line">📍 <b>Lugar:</b> {ev.get('direccion', 'N/A')}</div>
                        <div class="data-line">💰 <b>Total:</b> S/ {costo:.0f} | <b style="color: #D90429;">Pendiente: S/ {pendiente:.0f}</b></div>
                    </div>
                """, unsafe_allow_html=True)

                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("👤 Personal", key=f"btn_pers_{ev['id']}", use_container_width=True):
                        modal_asignar_personal(ev)
                with col_btn2:
                    if st.button("📋 Ver Ficha", key=f"btn_ver_{ev['id']}", use_container_width=True):
                        modal_ver_ficha(ev['id'])

                st.markdown("<div style='margin-bottom: 6px;'></div>", unsafe_allow_html=True)

with tab2:
    st.header("Registrar Nuevo Evento")
    with st.form("form_nuevo_evento"):
        col_a, col_b = st.columns(2)
        with col_a:
            marca = st.selectbox("Marca", ["Decoraciones MADAI", "RISUEÑA", "Otra"])
            fecha = st.date_input("Fecha del Evento")
            tipo = st.text_input("Tipo de Evento", value="Show Infantil")
            evento = st.text_input("Nombre del Evento / Cumpleañero(a)")
            cliente = st.text_input("Nombre del Cliente")
            telefono = st.text_input("Teléfono")
        
        with col_b:
            hora_contrato = st.text_input("Hora Contrato", value="04:30 PM")
            hora_citacion = st.text_input("Hora Citación", value="04:00 PM")
            direccion = st.text_input("Dirección / Ubicación")
            costo_total = st.number_input("Costo Total (S/)", min_value=0.0, step=10.0, value=300.0)
            monto_adelanto = st.number_input("Monto Adelanto (S/)", min_value=0.0, step=10.0, value=100.0)
            concepto_alquiler = st.text_input("Concepto / Alquiler", value="Show Infantil Completo")
        
        descripcion = st.text_area("Notas adicionales del evento")
        
        btn_crear = st.form_submit_button("Guardar Evento", use_container_width=True)
        if btn_crear:
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
            st.success("Evento creado exitosamente.")
            st.rerun()
