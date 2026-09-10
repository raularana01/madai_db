import streamlit as st
import pandas as pd
from supabase import create_client, Client

# 1. Configuración de página
st.set_page_config(
    page_title="Agenda Madai",
    page_icon="📅",
    layout="wide"
)

# Estilos CSS compactos
st.markdown("""
    <style>
    .card-box {
        background-color: #EBD9F3;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        color: #111111;
        box-shadow: 0px 2px 5px rgba(0,0,0,0.05);
    }
    .badge-marca {
        background-color: #7B2CBF;
        color: white;
        padding: 4px 12px;
        border-radius: 6px;
        font-weight: bold;
        font-size: 12px;
        text-transform: uppercase;
    }
    .event-title {
        font-size: 17px;
        font-weight: bold;
        color: #000000;
        margin-bottom: 6px;
    }
    .data-line {
        font-size: 13.5px;
        color: #111111;
        margin-bottom: 4px;
        line-height: 1.4;
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

# 3. Funciones de Base de Datos
def obtener_eventos():
    response = supabase.table("eventos").select("*, personal(*)").order("fecha", desc=False).execute()
    return response.data

def guardar_evento(datos_evento):
    res = supabase.table("eventos").insert(datos_evento).execute()
    return res.data

def guardar_personal(evento_id, data_personal):
    try:
        existente = supabase.table("personal").select("id").eq("evento_id", evento_id).execute()
        
        if existente.data and len(existente.data) > 0:
            res = supabase.table("personal").update(data_personal).eq("evento_id", evento_id).execute()
        else:
            data_personal["evento_id"] = evento_id
            res = supabase.table("personal").insert(data_personal).execute()
            
        return True, "Personal guardado correctamente"
    except Exception as e:
        return False, str(e)

# Callback para agregar campos de Dalina en tiempo real
def agregar_dalina_callback(state_key):
    if len(st.session_state[state_key]) < 7:
        st.session_state[state_key].append("")

# 4. Modal para Asignar Personal
@st.dialog("👤 Asignar Personal al Evento")
def modal_asignar_personal(evento):
    p_previo = evento.get("personal", [])
    p_data = p_previo[0] if isinstance(p_previo, list) and len(p_previo) > 0 else {}

    state_key = f"dalinas_lista_{evento['id']}"

    # Cargar datos guardados o inicializar 1 campo
    if state_key not in st.session_state:
        dalinas_existentes = p_data.get("dalinas", "")
        if dalinas_existentes:
            st.session_state[state_key] = [d.strip() for d in dalinas_existentes.split(",") if d.strip()]
        else:
            st.session_state[state_key] = [""]

    dalinas = st.session_state[state_key]
    cant = len(dalinas)

    st.markdown(f"**💃 Dalinas ({cant}/7):**")

    # Inputs para Dalinas + Botón '+'
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

    # Selección de Animadores
    opciones_animadores = ["Ninguno(a)", "Madai", "Martha", "Eusy", "Antonio", "Jair", "Britny", "Gina"]
    animador_previo = p_data.get("animador", "Ninguno(a)")
    idx_animador = opciones_animadores.index(animador_previo) if animador_previo in opciones_animadores else 0

    animador = st.selectbox("🎤 Animador(a):", opciones_animadores, index=idx_animador, key=f"sel_anim_{evento['id']}")
    dj = st.text_input("🎧 DJ:", value=p_data.get("dj", ""), placeholder="Nombre DJ", key=f"in_dj_{evento['id']}")
    staff = st.text_input("🛠️ Staff:", value=p_data.get("staff", ""), placeholder="Nombre Staff", key=f"in_staff_{evento['id']}")
    duracion = st.text_input("⏳ Duración:", value=p_data.get("duracion", ""), placeholder="ej. 2 Horas", key=f"in_dur_{evento['id']}")
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
            if state_key in st.session_state:
                del st.session_state[state_key]
            st.rerun()
        else:
            st.error(f"❌ Error al guardar en Supabase: {msg}")

# Modal Ficha Detallada
@st.dialog("Ficha Detallada del Evento")
def modal_ver_ficha(evento):
    st.title(f"📌 {evento['evento']}")
    st.caption(f"Marca: {evento['marca']} | Fecha: {evento['fecha']}")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 👤 Datos del Cliente")
        st.write(f"**Cliente:** {evento.get('cliente', 'N/A')}")
        st.write(f"**Teléfono:** {evento.get('telefono', 'N/A')}")
        st.write(f"**Dirección:** {evento.get('direccion', 'N/A')}")
        st.write(f"**Hora Contrato:** {evento.get('hora_contrato', 'N/A')}")
        st.write(f"**Hora Citación:** {evento.get('hora_citacion', 'N/A')}")

    with col2:
        st.markdown("### 💰 Detalles Financieros")
        costo = float(evento.get('costo_total', 0) or 0)
        adelanto = float(evento.get('monto_adelanto', 0) or 0)
        saldo = costo - adelanto
        st.write(f"**Costo Total:** S/ {costo:.2f}")
        st.write(f"**Adelanto:** S/ {adelanto:.2f}")
        st.write(f"**Saldo Pendiente:** S/ {saldo:.2f}")

    st.divider()
    st.markdown("### 👥 Personal Asignado")
    p_lista = evento.get("personal", [])
    if isinstance(p_lista, list) and len(p_lista) > 0:
        p = p_lista[0]
        st.write(f"• **N° Dalinas:** {p.get('num_dalinas', 0)} ({p.get('dalinas', 'Ninguna')})")
        st.write(f"• **Animador(a):** {p.get('animador', 'Ninguno(a)')}")
        st.write(f"• **DJ:** {p.get('dj', 'N/A')}")
        st.write(f"• **Staff:** {p.get('staff', 'N/A')}")
        st.write(f"• **Duración:** {p.get('duracion', 'N/A')}")
        if p.get('detalles'):
            st.info(f"**Notas:** {p.get('detalles')}")
    else:
        st.warning("Aún no se ha asignado personal a este evento.")

# 5. Vista Principal
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
                
                st.markdown(f"""
                    <div class="card-box">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                            <div class="event-title">🎉 {ev['evento']} {tipo_str}</div>
                            <span class="badge-marca">{ev.get('marca', 'Decoraciones MADAI')}</span>
                        </div>
                        <div class="data-line">⏰ <b>Hora Contrato:</b> {ev.get('hora_contrato', '04:30 PM')} | <b>Citación:</b> {ev.get('hora_citacion', '04:00 PM')}</div>
                        <div class="data-line">👤 <b>Cliente:</b> {ev.get('cliente', 'N/A')} | 📱 <b>Tel:</b> {ev.get('telefono', 'N/A')}</div>
                        <div class="data-line">📍 <b>Lugar:</b> {ev.get('direccion', 'N/A')} | 💰 <b>Total: S/ {costo:.0f}</b> | <b>Pendiente: S/ {pendiente:.0f}</b></div>
                    </div>
                """, unsafe_allow_html=True)

                if st.button("👤 Asignar Personal", key=f"btn_pers_{ev['id']}", use_container_width=True):
                    modal_asignar_personal(ev)
                
                if st.button("📋 Ver Ficha", key=f"btn_ver_{ev['id']}", use_container_width=True):
                    modal_ver_ficha(ev)

                st.write("")

with tab2:
    st.header("Registrar Nuevo Evento")
    with st.form("form_nuevo_evento"):
        col_a, col_b = st.columns(2)
        with col_a:
            marca = st.selectbox("Marca", ["Decoraciones MADAI", "RISUEÑA", "Otra"])
            fecha = st.date_input("Fecha del Evento")
            tipo = st.text_input("Tipo de Evento", value="Show")
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
