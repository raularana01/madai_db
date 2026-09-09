import streamlit as st
import pandas as pd
import os
import base64
from datetime import datetime, timedelta
from supabase import create_client, Client

# Configuración de la página
st.set_page_config(page_title="Agenda Madai (DB)", page_icon="📅", layout="centered")

# =========================================================
# CONEXIÓN A SUPABASE
# =========================================================
SUPABASE_URL = st.secrets.get("SUPABASE_URL", os.environ.get("SUPABASE_URL", ""))
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", os.environ.get("SUPABASE_KEY", ""))

@st.cache_resource
def init_supabase() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        st.error("⚠️ Configura SUPABASE_URL y SUPABASE_KEY en los secretos de Streamlit.")
        st.stop()
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# Funciones de lectura y escritura
# Funciones de lectura y escritura corregidas
def obtener_eventos():
    # 'personal(*)' hace el JOIN automático entre eventos y la tabla personal
    response = supabase.table("eventos").select("*, personal(*)").order("fecha", desc=False).execute()
    return response.data

def guardar_personal(evento_id, data_personal):
    data_personal["evento_id"] = evento_id
    # 'upsert' inserta o actualiza si ya existe el registro para este evento
    res = supabase.table("personal").upsert(data_personal, on_conflict="evento_id").execute()
    return res.data

def guardar_evento(payload):
    res = supabase.table("eventos").insert(payload).execute()
    return res.data

# =========================================================
# DISEÑO Y ESTILOS CSS
# =========================================================
def obtener_base64_de_archivo(ruta_imagen):
    if os.path.exists(ruta_imagen):
        with open(ruta_imagen, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        extension = ruta_imagen.split('.')[-1].lower()
        mime = 'image/png' if extension == 'png' else 'image/jpeg'
        return f"data:{mime};base64,{encoded_string}"
    return None

imagen_fondo_b64 = obtener_base64_de_archivo("fondo.jpeg")
imagen_logo_b64 = obtener_base64_de_archivo("logo.jpeg")

css_fondo = f"""
.stApp {{
    background-image: linear-gradient(rgba(0, 0, 0, 0.65), rgba(0, 0, 0, 0.65)), url("{imagen_fondo_b64}");
    background-size: cover; background-position: center; background-repeat: no-repeat; background-attachment: fixed;
}}
""" if imagen_fondo_b64 else ""

st.markdown(f"""
<style>
    {css_fondo}
    [data-testid="stAppViewContainer"] > .main {{
        background-color: rgba(255, 255, 255, 0.96) !important;
        border-radius: 12px; padding: 8px !important; margin-top: 5px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4);
    }}
    .block-container {{ padding: 0.2rem 0.3rem !important; max-width: 100% !important; }}
    div[data-testid="stVerticalBlock"] > div {{ margin-bottom: -10px !important; padding-bottom: 0px !important; }}

    .header-container {{ display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }}
    .header-logo {{ width: 48px; height: 48px; object-fit: contain; border-radius: 50%; border: 2px solid #FFFFFF; }}
    .header-title {{
        font-size: 26px; font-weight: 900;
        background: linear-gradient(45deg, #FF007F, #FF8C00, #00E5FF);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin: 0; line-height: 1;
    }}

    label, p, span, div, .stMarkdown, .stRadio label, .stCheckbox label {{ color: #000000 !important; font-weight: 800 !important; }}

    .card-madai {{
        background: linear-gradient(135deg, #E0F7FA 0%, #B2EBF2 100%) !important;
        border-left: 6px solid #00838F; padding: 8px 12px; border-radius: 8px; margin-bottom: 4px;
    }}
    .card-risuena {{
        background: linear-gradient(135deg, #F3E5F5 0%, #E1BEE7 100%) !important;
        border-left: 6px solid #7B1FA2; padding: 8px 12px; border-radius: 8px; margin-bottom: 4px;
    }}
    .badge-madai {{ background-color: #00838F; color: #FFFFFF !important; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; }}
    .badge-risuena {{ background-color: #7B1FA2; color: #FFFFFF !important; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; }}

    .card-header {{ font-size: 15px; font-weight: bold; margin-bottom: 4px; color: #000000; display: flex; align-items: center; justify-content: space-between; }}
    .card-sub {{ font-size: 12px; color: #111111; margin-bottom: 2px; line-height: 1.2; }}

    div[data-testid="stColumn"] button {{ padding: 2px 6px !important; font-size: 11px !important; min-height: 28px !important; height: 28px !important; }}
</style>
""", unsafe_allow_html=True)

# Header
html_logo = f'<img src="{imagen_logo_b64}" class="header-logo">' if imagen_logo_b64 else ''
st.markdown(f'<div class="header-container">{html_logo}<h1 class="header-title">Agenda Madai (DB)</h1></div>', unsafe_allow_html=True)

if "menu_activo" not in st.session_state:
    st.session_state["menu_activo"] = "Eventos"

col_m1, col_m2, col_m3 = st.columns(3)
with col_m1:
    if st.button("📋 Eventos", use_container_width=True, type="primary" if st.session_state["menu_activo"] == "Eventos" else "secondary"):
        st.session_state["menu_activo"] = "Eventos"; st.rerun()
with col_m2:
    if st.button("🔍 Filtro", use_container_width=True, type="primary" if st.session_state["menu_activo"] == "Filtro" else "secondary"):
        st.session_state["menu_activo"] = "Filtro"; st.rerun()
with col_m3:
    if st.button("➕ Nuevo", use_container_width=True, type="primary" if st.session_state["menu_activo"] == "Nuevo" else "secondary"):
        st.session_state["menu_activo"] = "Nuevo"; st.rerun()

# =========================================================
# VENTANAS EMERGENTES (DIALOGS)
# =========================================================
@st.dialog("👤 Asignar Personal al Evento")
def abrir_dialogo_personal(evento):
    evento_id = evento["id"]
    personal_list = evento.get("personal", [])
    datos_guardados = personal_list[0] if personal_list else {}

    num_dalinas_init = datos_guardados.get("num_dalinas", 1)
    if f"temp_num_dalinas_{evento_id}" not in st.session_state:
        st.session_state[f"temp_num_dalinas_{evento_id}"] = num_dalinas_init

    num_dalinas = st.session_state[f"temp_num_dalinas_{evento_id}"]
    st.markdown(f"**💃 Dalinas ({num_dalinas}/7):**")

    dalinas_existentes = datos_guardados.get("dalinas", "").split(",") if datos_guardados.get("dalinas") else []
    dalinas_inputs = []
    for i in range(num_dalinas):
        val_default = dalinas_existentes[i].strip() if i < len(dalinas_existentes) else ""
        nombre_d = st.text_input(f"Dalina {i+1}", value=val_default, key=f"dlg_dalina_{i}_{evento_id}", placeholder=f"Nombre Dalina {i+1}")
        dalinas_inputs.append(nombre_d)

    c_add, c_rem = st.columns(2)
    with c_add:
        if num_dalinas < 7 and st.button("➕ Agregar Dalina", key=f"dlg_btn_add_{evento_id}", use_container_width=True):
            st.session_state[f"temp_num_dalinas_{evento_id}"] += 1; st.rerun()
    with c_rem:
        if num_dalinas > 1 and st.button("➖ Quitar Dalina", key=f"dlg_btn_rem_{evento_id}", use_container_width=True):
            st.session_state[f"temp_num_dalinas_{evento_id}"] -= 1; st.rerun()

    st.write("---")

    opciones_animador = ["Ninguno(a)", "Madai", "Martha", "Eusy", "Antonio", "Jair", "Britny", "Gina"]
    anim_actual = datos_guardados.get("animador", "Ninguno(a)")
    anim_idx = opciones_animador.index(anim_actual) if anim_actual in opciones_animador else 0
    animador_val = st.selectbox("🎤 Animador(a):", opciones_animador, index=anim_idx, key=f"dlg_anim_{evento_id}")

    c_dj, c_st = st.columns(2)
    with c_dj:
        dj_val = st.text_input("🎧 DJ:", value=datos_guardados.get("dj", ""), key=f"dlg_dj_{evento_id}", placeholder="Nombre DJ")
    with c_st:
        staff_val = st.text_input("🛠️ Staff:", value=datos_guardados.get("staff", ""), key=f"dlg_staff_{evento_id}", placeholder="Nombre Staff")

    duracion_val = st.text_input("⏳ Duración:", value=datos_guardados.get("duracion", ""), key=f"dlg_dur_{evento_id}", placeholder="ej. 2 Horas")
    detalles_val = st.text_area("📝 Detalles:", value=datos_guardados.get("detalles", ""), key=f"dlg_det_{evento_id}", placeholder="Observaciones...")

    if st.button("💾 Guardar Datos en BD", key=f"dlg_btn_save_{evento_id}", use_container_width=True, type="primary"):
        dalinas_str = ", ".join([d.strip() for d in dalinas_inputs if d.strip()])
        payload_personal = {
            "num_dalinas": num_dalinas,
            "dalinas": dalinas_str,
            "animador": animador_val,
            "dj": dj_val.strip(),
            "staff": staff_val.strip(),
            "duracion": duracion_val.strip(),
            "detalles": detalles_val.strip()
        }
        guardar_personal(evento_id, payload_personal)
        st.session_state["mensaje_exito"] = "✅ ¡Personal guardado permanentemente en la base de datos!"
        st.rerun()

@st.dialog("📜 Ficha Completa del Evento")
def abrir_dialogo_ficha(evento):
    marca = evento.get("marca", "Madai")
    v_fecha = evento.get("fecha", "")
    v_evento = evento.get("evento", "Evento")
    v_tipo = evento.get("tipo", "")
    h_contrato = evento.get("hora_contrato") or "N/A"
    h_citacion = evento.get("hora_citacion") or "N/A"
    v_cliente = evento.get("cliente") or "N/A"
    v_telefono = evento.get("telefono") or "N/A"
    v_lugar = evento.get("direccion") or "N/A"
    
    v_total = float(evento.get("costo_total") or 0)
    v_adelanto = float(evento.get("monto_adelanto") or 0)
    v_pendiente = max(0, int(v_total - v_adelanto))

    personal_list = evento.get("personal", [])
    datos_p = personal_list[0] if personal_list else {}

    dalinas_str = datos_p.get("dalinas") or "Ninguna asignada"
    anim_str = datos_p.get("animador") or "Ninguno(a)"
    dj_str = datos_p.get("dj") or "No asignado"
    staff_str = datos_p.get("staff") or "No asignado"
    dur_str = datos_p.get("duracion") or "No especificada"
    det_str = datos_p.get("detalles") or "Sin detalles"

    st.markdown(f"""
    <div style="font-size: 13px; line-height: 1.4;">
        <p><b>🏷️ Marca:</b> {marca.upper()} | <b>🎉 Evento:</b> {v_evento} ({v_tipo})</p>
        <p><b>📅 Fecha:</b> {v_fecha} | <b>⏰ Contrato:</b> {h_contrato} | <b>Citación:</b> {h_citacion}</p>
        <p><b>👤 Cliente:</b> {v_cliente} | <b>📱 Teléfono:</b> {v_telefono}</p>
        <p><b>📍 Ubicación:</b> {v_lugar}</p>
        <p><b>💰 Total:</b> S/ {int(v_total)} | <b>Monto Pendiente:</b> S/ {v_pendiente}</p>
        <hr style="margin: 6px 0;">
        <p style="color:#7B1FA2; font-weight:bold; margin-bottom:4px;">👥 PERSONAL Y SHOW:</p>
        <p><b>💃 Dalina(s):</b> {dalinas_str}</p>
        <p><b>🎤 Animador(a):</b> {anim_str}</p>
        <p><b>🎧 DJ:</b> {dj_str} | <b>🛠️ Staff:</b> {staff_str}</p>
        <p><b>⏳ Duración:</b> {dur_str}</p>
        <p><b>📝 Detalles:</b> {det_str}</p>
    </div>
    """, unsafe_allow_html=True)

def renderizar_tarjeta(evento, muestra_fecha=False):
    marca = evento.get("marca", "Madai")
    clase_tarjeta = "card-risuena" if marca.lower() == "risueña" else "card-madai"
    clase_badge = "badge-risuena" if marca.lower() == "risueña" else "badge-madai"

    v_fecha = evento.get("fecha", "")
    v_evento = evento.get("evento", "Evento")
    v_tipo = evento.get("tipo", "")
    h_contrato = evento.get("hora_contrato") or "N/A"
    h_citacion = evento.get("hora_citacion") or "N/A"
    v_cliente = evento.get("cliente") or "N/A"
    v_telefono = evento.get("telefono") or "N/A"
    v_lugar = evento.get("direccion") or "N/A"

    v_total = float(evento.get("costo_total") or 0)
    v_adelanto = float(evento.get("monto_adelanto") or 0)
    v_pendiente = max(0, int(v_total - v_adelanto))

    texto_fecha = f"📅 {v_fecha} | " if muestra_fecha else ""

    st.markdown(f"""
    <div class="{clase_tarjeta}">
        <div class="card-header">
            <span>{texto_fecha}🎉 {v_evento} ({v_tipo})</span>
            <span class="{clase_badge}">🏷️ {marca.upper()}</span>
        </div>
        <div class="card-sub">⏰ <b>Hora Contrato:</b> {h_contrato} | <b>Citación:</b> {h_citacion}</div>
        <div class="card-sub">👤 <b>Cliente:</b> {v_cliente} | 📱 <b>Tel:</b> {v_telefono}</div>
        <div class="card-sub">📍 <b>Lugar:</b> {v_lugar} | 💰 <b>Total:</b> S/ {int(v_total)} | <b>Pendiente:</b> S/ {v_pendiente}</div>
    </div>
    """, unsafe_allow_html=True)

    evento_id = evento["id"]
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        if st.button("👤 Asignar Personal", key=f"btn_asig_{evento_id}", use_container_width=True):
            abrir_dialogo_personal(evento)
    with btn_col2:
        if st.button("📋 Ver Ficha", key=f"btn_fich_{evento_id}", use_container_width=True):
            abrir_dialogo_ficha(evento)
    st.write("")

# =========================================================
# LÓGICA DE LAS PESTAÑAS DE LA APLICACIÓN
# =========================================================
lista_eventos = obtener_eventos()

if st.session_state["menu_activo"] == "Eventos":
    if "mensaje_exito" in st.session_state:
        st.success(st.session_state.pop("mensaje_exito"))

    c_top1, c_top2 = st.columns([3, 1])
    with c_top2:
        if st.button("🔄 Actualizar", key="btn_refresh", use_container_width=True):
            st.rerun()

    if lista_eventos:
        df_eventos = pd.DataFrame(lista_eventos)
        df_eventos["fecha_dt"] = pd.to_datetime(df_eventos["fecha"]).dt.date
        
        try:
            from zoneinfo import ZoneInfo
            hoy_date = datetime.now(ZoneInfo("America/Lima")).date()
        except Exception:
            hoy_date = (datetime.utcnow() - timedelta(hours=5)).date()

        modo_vista = st.radio("Categoría:", ["Eventos del día (Hoy)", "Próximos 3 días", "Todos los eventos"], horizontal=True)

        if modo_vista == "Eventos del día (Hoy)":
            df_hoy = df_eventos[df_eventos["fecha_dt"] == hoy_date]
            if not df_hoy.empty:
                for row in df_hoy.to_dict("records"):
                    renderizar_tarjeta(row, muestra_fecha=False)
            else:
                st.info(f"No hay eventos para hoy ({hoy_date.strftime('%Y-%m-%d')}).")

        elif modo_vista == "Próximos 3 días":
            limite_3dias = hoy_date + timedelta(days=3)
            df_3dias = df_eventos[(df_eventos["fecha_dt"] >= hoy_date) & (df_eventos["fecha_dt"] <= limite_3dias)]
            if not df_3dias.empty:
                for row in df_3dias.to_dict("records"):
                    renderizar_tarjeta(row, muestra_fecha=True)
            else:
                st.info("No hay eventos en los próximos 3 días.")

        else:
            for row in df_eventos.to_dict("records"):
                renderizar_tarjeta(row, muestra_fecha=True)
    else:
        st.info("No hay eventos registrados en la base de datos.")

elif st.session_state["menu_activo"] == "Filtro":
    st.subheader("🔍 Búsqueda y Filtros")
    filtro_cliente = st.text_input("👤 Cliente / Evento:", placeholder="Buscar...")
    filtro_telefono = st.text_input("📱 Teléfono:", placeholder="Buscar...")

    if lista_eventos:
        df_f = pd.DataFrame(lista_eventos)
        if filtro_cliente.strip():
            df_f = df_f[df_f["cliente"].str.contains(filtro_cliente, case=False, na=False) | df_f["evento"].str.contains(filtro_cliente, case=False, na=False)]
        if filtro_telefono.strip():
            df_f = df_f[df_f["telefono"].str.contains(filtro_telefono, case=False, na=False)]
        
        st.write(f"**Resultados:** {len(df_f)}")
        st.dataframe(df_f[["fecha", "marca", "evento", "cliente", "telefono", "direccion", "costo_total"]], use_container_width=True)

elif st.session_state["menu_activo"] == "Nuevo":
    marca_seleccionada = st.radio("🏷️ Marca", ["Madai", "Risueña"], horizontal=True)
    fecha_input = st.date_input("📅 Fecha", datetime.now())
    tipo_servicio = st.selectbox("🎭 Servicio", ["Show", "Decoración", "Show + Decoración", "Alquiler"])
    nombre_evento = st.text_input("🎉 Evento", placeholder="ej. Cumpleaños Gia")
    cliente = st.text_input("👤 Cliente", placeholder="ej. María López")

    st.caption("⏰ **Hora Contrato**")
    c1, c2 = st.columns([3.5, 1.2])
    with c1: h_contrato_val = st.text_input("HC", value="04:30", label_visibility="collapsed")
    with c2: ampm_contrato = st.selectbox("AP1", ["PM", "AM"], label_visibility="collapsed")

    st.caption("📩 **Hora Citación**")
    c3, c4 = st.columns([3.5, 1.2])
    with c3: h_citacion_val = st.text_input("HI", value="04:00", label_visibility="collapsed")
    with c4: ampm_citacion = st.selectbox("AP2", ["PM", "AM"], label_visibility="collapsed")

    direccion = st.text_input("📍 Dirección", placeholder="ej. Av. Las Flores 123")
    telefono = st.text_input("📱 Teléfono", placeholder="ej. 987654321")

    costo_total = st.number_input("Costo Total (S/)", min_value=0, step=1, value=0)
    monto_adelanto = st.number_input("Adelanto (S/)", min_value=0, step=1, value=0)
    descripcion = st.text_area("📝 Observaciones", placeholder="Detalles adicionales...")

    if st.button("💾 Guardar Evento en BD", use_container_width=True, type="primary"):
        payload_evento = {
            "marca": marca_seleccionada,
            "fecha": fecha_input.strftime("%Y-%m-%d"),
            "tipo": tipo_servicio,
            "evento": nombre_evento if nombre_evento else "Evento",
            "hora_contrato": f"{h_contrato_val.strip()} {ampm_contrato}",
            "hora_citacion": f"{h_citacion_val.strip()} {ampm_citacion}",
            "cliente": cliente,
            "telefono": telefono,
            "direccion": direccion,
            "costo_total": costo_total,
            "monto_adelanto": monto_adelanto,
            "descripcion": descripcion
        }
        guardar_evento(payload_evento)
        st.session_state["menu_activo"] = "Eventos"
        st.session_state["mensaje_exito"] = "🎉 ¡Evento guardado con éxito en Supabase!"
        st.rerun()
