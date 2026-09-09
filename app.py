import streamlit as st
import pandas as pd
from supabase import create_client, Client

# 1. Configuración de página
st.set_page_config(
    page_title="Agenda Madai",
    page_icon="📅",
    layout="wide"
)

# Estilos CSS idénticos a las capturas
st.markdown("""
    <style>
    /* Estilo de la tarjeta violeta */
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
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# 3. Funciones de Base de Datos
def obtener_eventos():
    response = supabase.table("eventos").select("*, personal(*)").order("fecha", desc=False).execute()
    return response.data

def guardar_evento(datos_evento):
    res = supabase.table("eventos").insert(datos_evento).execute()
    return res.data

def eliminar_evento(evento_id):
    supabase.table("eventos").delete().eq("id", evento_id).execute()

def guardar_personal(evento_id, data_personal):
    data_personal["evento_id"] = evento_id
    res = supabase.table("personal").upsert(data_personal, on_conflict="evento_id").execute()
    return res.data

# 4. Modal para Asignar Personal
@st.dialog("👤 Asignar Personal al Evento")
def modal_asignar_personal(evento):
    p_previo = evento.get("personal", [])
    p_data = p_previo[0] if isinstance(p_previo, list) and len(p_previo) > 0 else {}

    # Manejo de múltiples Dalinas
    dalinas_existentes = p_data.get("dalinas", "")
    lista_dalinas_previa = [d.strip() for d in dalinas_existentes.split(",") if d.strip()] if dalinas_existentes else [""]
    
    if "num_dalinas_input" not in st.session_state:
        st.session_state.num_dalinas_input = max(len(lista_dalinas_previa), 1)

    cant_dalinas = st.session_state.num_dalinas_input
    st.markdown(f"**💃 Dalinas ({cant_dalinas}/7):**")
    
    dalinas_respuestas = []
    for i in range(cant_dalinas):
        val_default = lista_dalinas_previa[i] if i < len(lista_dalinas_previa) else ""
        d_val = st.text_input(f"Dalina {i+1}", value=val_default, placeholder=f"Nombre Dalina {i+1}", key=f"dalina_in_{i}")
        if d_val.strip():
            dalinas_respuestas.append(d_val.strip())

    if cant_dalinas < 7:
        if st.button("➕ Agregar Dalina", use_container_width=True):
            st.session_state.num_dalinas_input += 1
            st.rerun()

    st.divider()

    # Opciones de Selector de Animadores idénticas a la imagen
    opciones_animadores = ["Ninguno(a)", "Madai", "Martha", "Eusy", "Antonio", "Jair", "Britny", "Gina"]
    animador_previo = p_data.get("animador", "Ninguno(a)")
    idx_animador = opciones_animadores.index(animador_previo) if animador_previo in opciones_animadores else 0

    animador = st.selectbox("🎤 Animador(a):", opciones_animadores, index=idx_animador)
    dj = st.text_input("🎧 DJ:", value=p_data.get("dj", ""), placeholder="Nombre DJ")
    staff = st.text_input("🛠️ Staff:", value=p_data.get("staff", ""), placeholder="Nombre Staff")
    duracion = st.text_input("⏳ Duración:", value=p_data.get("duracion", ""), placeholder="ej. 2 Horas")
    detalles = st.text_area("📝 Detalles:", value=p_data.get("detalles", ""), placeholder="Observaciones...")

    st.write("")
    if st.button("💾 Guardar Datos", type="primary", use_container_width=True):
        payload = {
            "num_dalinas": len(dalinas_respuestas),
            "dalinas": ", ".join(dalinas_respuestas),
            "animador": animador,
            "dj": dj,
            "staff": staff,
            "duracion": duracion,
            "detalles": detalles
        }
        guardar_personal(evento["id"], payload)
        if "num_dalinas_input" in st.session_state:
            del st.session_state["num_dalinas_input"]
        st.rerun()

# Modal para Ficha Detallada
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
        st.write(f"**Concepto Alquiler:** {evento.get('concepto_alquiler', 'N/A')}")

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
                
                # Renderizado HTML con la estructura exacta de la imagen
                st.markdown(f"""
                    <div class="card-box">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                            <div class="event-title">🎉 {ev['evento']} {tipo_str}</div>
                            <span class="badge-marca">{ev.get('marca', 'RISUEÑA')}</span>
                        </div>
                        <div class="data-line">⏰ <b>Hora Contrato:</b> {ev.get('hora_contrato', '04:30 PM')} | <b>Citación:</b> {ev.get('hora_citacion', '04:00 PM')}</div>
                        <div class="data-line">👤 <b>Cliente:</b> {ev.get('cliente', 'N/A')} | 📱 <b>Tel:</b> {ev.get('telefono', 'N/A')}</div>
                        <div class="data-line">📍 <b>Lugar:</b> {ev.get('direccion', 'N/A')} | 💰 <b>Total: S/ {costo:.0f}</b> | <b>Pendiente: S/ {pendiente:.0f}</b></div>
                    </div>
                """, unsafe_allow_html=True)

                # Botones en bloque como la captura
                if st.button("👤 Asignar Personal", key=f"pers_{ev['id']}", use_container_width=True):
                    modal_asignar_personal(ev)
                
                if st.button("📋 Ver Ficha", key=f"ver_{ev['id']}", use_container_width=True):
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
