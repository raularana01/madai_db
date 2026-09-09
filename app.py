import streamlit as st
import pandas as pd
from supabase import create_client, Client

# 1. Configuración de página
st.set_page_config(
    page_title="Agenda Madai",
    page_icon="📅",
    layout="wide"
)

# 2. Conexión a Supabase mediante Secrets
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# 3. Funciones de Base de Datos
def obtener_eventos():
    # Trae los eventos y realiza el JOIN automático con la tabla personal
    response = supabase.table("eventos").select("*, personal(*)").order("fecha", desc=False).execute()
    return response.data

def guardar_evento(datos_evento):
    res = supabase.table("eventos").insert(datos_evento).execute()
    return res.data

def eliminar_evento(evento_id):
    supabase.table("eventos").delete().eq("id", evento_id).execute()

def guardar_personal(evento_id, data_personal):
    data_personal["evento_id"] = evento_id
    # Actualiza o inserta asegurando que no se duplique por evento_id
    res = supabase.table("personal").upsert(data_personal, on_conflict="evento_id").execute()
    return res.data

# 4. Modales (Dialogs)
@st.dialog("Asignar Personal")
def modal_asignar_personal(evento):
    st.subheader(f"Evento: {evento['evento']} ({evento['fecha']})")
    
    # Extraer datos previos si existen
    p_previo = evento.get("personal", [])
    p_data = p_previo[0] if isinstance(p_previo, list) and len(p_previo) > 0 else {}

    with st.form("form_personal"):
        num_dalinas = st.number_input("Número de Dalinas", min_value=0, max_value=10, value=int(p_data.get("num_dalinas", 1)))
        dalinas = st.text_input("Nombre de Dalina(s)", value=p_data.get("dalinas", ""))
        animador = st.text_input("Animador(a)", value=p_data.get("animador", ""))
        dj = st.text_input("DJ / Sonido", value=p_data.get("dj", ""))
        staff = st.text_input("Staff / Apoyo", value=p_data.get("staff", ""))
        duracion = st.text_input("Duración del Show", value=p_data.get("duracion", "2 horas"))
        detalles = st.text_area("Detalles / Indicaciones Especiales", value=p_data.get("detalles", ""))
        
        submitted = st.form_submit_button("Guardar Personal", use_container_width=True)
        if submitted:
            payload = {
                "num_dalinas": num_dalinas,
                "dalinas": dalinas,
                "animador": animador,
                "dj": dj,
                "staff": staff,
                "duracion": duracion,
                "detalles": detalles
            }
            guardar_personal(evento["id"], payload)
            st.success("¡Personal asignado con éxito!")
            st.rerun()

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
        st.write(f"• **N° Dalinas:** {p.get('num_dalinas', 'N/A')} ({p.get('dalinas', '-')})")
        st.write(f"• **Animador(a):** {p.get('animador', 'N/A')}")
        st.write(f"• **DJ:** {p.get('dj', 'N/A')}")
        st.write(f"• **Staff:** {p.get('staff', 'N/A')}")
        st.write(f"• **Duración:** {p.get('duracion', 'N/A')}")
        if p.get('detalles'):
            st.info(f"**Notas del Personal:** {p.get('detalles')}")
    else:
        st.warning("Aún no se ha asignado personal a este evento.")

    if evento.get('descripcion'):
        st.divider()
        st.markdown("### 📝 Descripción General")
        st.write(evento['descripcion'])

# 5. Interfaz Principal
st.title("📅 Agenda Madai - Gestión de Eventos")

tab1, tab2 = st.tabs(["📋 Lista de Eventos", "➕ Registrar Evento"])

with tab1:
    eventos = obtener_eventos()
    
    if not eventos:
        st.info("No hay eventos registrados.")
    else:
        for ev in eventos:
            with st.container(border=True):
                col1, col2, col3, col4 = st.columns([2, 3, 2, 3])
                
                with col1:
                    st.subheader(ev["fecha"])
                    st.caption(f"🏷️ {ev['marca']}")
                
                with col2:
                    st.write(f"**{ev['evento']}**")
                    st.write(f"📍 {ev.get('direccion', 'Sin dirección')}")
                
                with col3:
                    p_info = ev.get("personal", [])
                    tiene_personal = isinstance(p_info, list) and len(p_info) > 0
                    if tiene_personal:
                        st.success("👥 Personal OK")
                    else:
                        st.warning("⚠️ Sin Personal")
                
                with col4:
                    btn_col1, btn_col2, btn_col3 = st.columns(3)
                    if btn_col1.button("👁️ Ficha", key=f"ver_{ev['id']}"):
                        modal_ver_ficha(ev)
                    
                    if btn_col2.button("👤 Personal", key=f"pers_{ev['id']}"):
                        modal_asignar_personal(ev)
                    
                    if btn_col3.button("🗑️", key=f"del_{ev['id']}"):
                        eliminar_evento(ev['id'])
                        st.rerun()

with tab2:
    st.header("Registrar Nuevo Evento")
    with st.form("form_nuevo_evento"):
        col_a, col_b = st.columns(2)
        with col_a:
            marca = st.selectbox("Marca", ["Decoraciones MADAI", "Otra"])
            fecha = st.date_input("Fecha del Evento")
            tipo = st.text_input("Tipo de Evento", value="Infantil")
            evento = st.text_input("Nombre del Evento / Cumpleañero(a)")
            cliente = st.text_input("Nombre del Cliente")
            telefono = st.text_input("Teléfono")
        
        with col_b:
            hora_contrato = st.text_input("Hora Contrato", value="4:00 PM")
            hora_citacion = st.text_input("Hora Citación", value="3:30 PM")
            direccion = st.text_input("Dirección / Ubicación")
            costo_total = st.number_input("Costo Total (S/)", min_value=0.0, step=10.0)
            monto_adelanto = st.number_input("Monto Adelanto (S/)", min_value=0.0, step=10.0)
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
