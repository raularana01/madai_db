import streamlit as st
from datetime import date, datetime, timedelta
from supabase import create_client, Client
import base64
import os
import urllib.parse

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

OPCIONES_ANIMADORAS = ["Madai", "Martha", "Eusy", "Carla", "Lucia", "Ninguno", "Otro Animador"]
OPCIONES_DURACION = ["1.5 horas", "2 horas", "2.5 horas", "3 horas"]

if "editar_personal_id" not in st.session_state:
    st.session_state["editar_personal_id"] = None
if "ver_ficha_id" not in st.session_state:
    st.session_state["ver_ficha_id"] = None
if "tab_activa" not in st.session_state:
    st.session_state["tab_activa"] = "HOY"
if "num_items_alquiler" not in st.session_state:
    st.session_state["num_items_alquiler"] = 1

# ==============================================================================
# 2. CARGA DE RECURSOS EN BASE64
# ==============================================================================
@st.cache_data
def obtener_base64_de_archivo(ruta_archivo):
    if os.path.exists(ruta_archivo):
        with open(ruta_archivo, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

fondo_b64 = obtener_base64_de_archivo("fondo.jpeg")
logo_b64 = obtener_base64_de_archivo("logo.jpeg")

css_fondo = """
.stApp { background-color: #f3e8ff; }
"""
if fondo_b64:
    css_fondo = f"""
    .stApp {{
        background-image: linear-gradient(rgba(240, 230, 255, 0.65), rgba(240, 230, 255, 0.65)), url("data:image/jpeg;base64,{fondo_b64}");
        background-size: cover; background-position: center; background-attachment: fixed;
    }}
    """

# ==============================================================================
# 3. ESTILOS CSS OPTIMIZADOS
# ==============================================================================
st.markdown(f"""
    <style>
    {css_fondo}
    .block-container {{ padding-top: 3.8rem !important; padding-bottom: 2rem !important; }}
    .header-container {{ display: flex; align-items: center; gap: 12px; margin: 5px 0 12px 0; }}
    .logo-inline {{ height: 44px; width: auto; object-fit: contain; border-radius: 6px; }}
    .title-inline {{
        font-family: 'Comic Sans MS', 'Chalkboard SE', 'Quicksand', sans-serif;
        font-size: 2.2rem; font-weight: 900;
        background: linear-gradient(45deg, #7B2CBF, #FF007F, #FF9F1C, #2B9348);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin: 0; line-height: 1; letter-spacing: 1px;
    }}
    div[data-testid="stRadio"] {{ margin: 0 0 10px 0 !important; }}
    div[data-testid="stRadio"] > div {{ gap: 6px !important; padding: 0 !important; }}
    div[data-testid="stRadio"] label {{
        background-color: rgba(255, 255, 255, 0.85) !important;
        padding: 6px 14px !important; border-radius: 20px !important;
        border: 1.5px solid #7B2CBF !important; font-weight: bold !important; color: #7B2CBF !important; font-size: 0.85rem !important;
    }}
    .card-madai, .card-risuena, .card-alquiler {{ padding: 0 0 12px 0; border-radius: 8px; margin-bottom: 12px; position: relative; }}
    .badge-marca {{
        position: absolute; top: 8px; right: 12px; padding: 3px 10px; border-radius: 12px;
        font-size: 0.75rem; font-weight: bold; color: white; text-transform: uppercase;
    }}
    .badge-madai {{ background-color: #7B2CBF; }}
    .badge-risuena {{ background-color: #2B9348; }}
    .badge-alquiler {{ background-color: #023E8A; }}
    .header-madai {{ background-color: #7B2CBF; color: white; padding: 6px 12px; font-weight: bold; font-size: 0.95rem; border-radius: 4px 4px 0 0; }}
    .header-risuena {{ background-color: #2B9348; color: white; padding: 6px 12px; font-weight: bold; font-size: 0.95rem; border-radius: 4px 4px 0 0; }}
    .header-alquiler {{ background-color: #023E8A; color: white; padding: 6px 12px; font-weight: bold; font-size: 0.95rem; border-radius: 4px 4px 0 0; }}
    .event-title {{ font-size: 1.15rem; font-weight: bold; color: #111; padding: 10px 80px 4px 12px; }}
    .data-line {{ font-size: 0.95rem; color: #222; padding: 2px 12px; }}
    div.stButton > button {{
        background-color: #28a745 !important; color: white !important; font-weight: bold !important;
        border: none !important; border-radius: 8px !important; width: 100% !important;
    }}
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 4. FUNCIONES AUXILIARES
# ==============================================================================
def formatear_fecha_larga(fecha_str):
    if not fecha_str: return "Sin fecha"
    try:
        dt = datetime.strptime(str(fecha_str), "%Y-%m-%d")
        dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        return f"{dias[dt.weekday()]} {dt.day} de {meses[dt.month - 1]} de {dt.year}"
    except Exception:
        return str(fecha_str)

@st.cache_data(ttl=5)
def obtener_eventos():
    res = supabase.table("eventos").select("*, personal(*)").execute()
    return res.data if res.data else []

def generar_texto_ficha(ev):
    p_data = ev.get("personal", [{}])
    p_data = p_data[0] if isinstance(p_data, list) and len(p_data) > 0 else (p_data if isinstance(p_data, dict) else {})
    
    marca = str(ev.get("marca", "madai")).upper()
    tipo = str(ev.get("tipo", "Show"))
    fecha = formatear_fecha_larga(ev.get("fecha", ""))
    costo = float(ev.get('costo_total', 0) or 0)
    adelanto = float(ev.get('monto_adelanto', 0) or 0)
    pendiente = costo - adelanto

    texto = (
        f"🏷️ *MARCA: {marca}*\n"
        f"🎉 *EVENTO:* {ev.get('evento', 'Sin Nombre')} ({tipo})\n"
        f"📅 *FECHA:* {fecha}\n"
        f"⏰ *HORA:* {ev.get('hora_contrato', '04:30 PM')}\n"
        f"👤 *CLIENTE:* {ev.get('cliente', 'N/A')} (Tel: {ev.get('telefono', 'N/A')})\n"
    )
    if "LOCAL" not in marca:
        texto += f"📍 *DIRECCIÓN:* {ev.get('direccion', 'N/A')}\n"
    
    if ev.get("incluye_alquiler"):
        texto += f"📦 *ALQUILER EXTRA:* {ev.get('detalle_alquiler', 'N/A')} (S/ {float(ev.get('monto_alquiler', 0)):.0f})\n"

    if p_data.get("animador") or p_data.get("dalinas") or p_data.get("dj") or p_data.get("staff"):
        texto += (
            f"👥 *PERSONAL ASIGNADO:*\n"
            f"  • Animadora: {p_data.get('animador', 'No asignada')}\n"
            f"  • Dalinas: {p_data.get('dalinas', 'Ninguna')}\n"
            f"  • DJ: {p_data.get('dj', 'No asignado')}\n"
            f"  • Staff: {p_data.get('staff', 'No asignado')}\n"
        )
    if p_data.get("detalles"):
        texto += f"📝 *Notas:* {p_data.get('detalles')}\n"
        
    texto += f"💵 *Total:* S/ {costo:.0f} | 💳 *Adelanto:* S/ {adelanto:.0f} | 💰 *Pendiente:* S/ {pendiente:.0f}\n"
    return texto

# ==============================================================================
# 5. MODALES
# ==============================================================================
@st.dialog("👤 Asignar / Editar Personal")
def dialog_asignar_personal(evento):
    e_id = int(evento["id"])
    st.write(f"**Evento:** {evento.get('evento', '')} - {evento.get('cliente', '')}")
    
    res_p = supabase.table("personal").select("*").eq("evento_id", e_id).execute()
    datos_p = res_p.data[0] if res_p.data else {}

    anim_guardada = datos_p.get("animador", "")
    idx_anim = OPCIONES_ANIMADORAS.index(anim_guardada) if anim_guardada in OPCIONES_ANIMADORAS else (OPCIONES_ANIMADORAS.index("Otro Animador") if anim_guardada else 0)

    anim_sel = st.selectbox("🎤 **Animadora**", OPCIONES_ANIMADORAS, index=idx_anim)
    animador_final = st.text_input("Escribe el nombre:", value=anim_guardada if anim_guardada not in OPCIONES_ANIMADORAS else "") if anim_sel == "Otro Animador" else anim_sel

    cant_dalinas = st.number_input("Número de Dalinas", min_value=0, max_value=20, value=int(datos_p.get("num_dalinas", 1) or 1))
    lista_dalinas_prev = [d.strip() for d in datos_p.get("dalinas", "").split(",") if d.strip()]
    
    nombres_dalinas = []
    for i in range(int(cant_dalinas)):
        val_prev = lista_dalinas_prev[i] if i < len(lista_dalinas_prev) else ""
        nom_d = st.text_input(f"Nombre Dalina {i+1}", value=val_prev, key=f"d_in_{e_id}_{i}")
        if nom_d.strip(): nombres_dalinas.append(nom_d.strip())

    dj_val = st.text_input("🎧 **DJ**", value=datos_p.get("dj", ""))
    staff_val = st.text_input("🛠️ **Staff**", value=datos_p.get("staff", ""))
    
    duracion_guardada = datos_p.get("duracion", "2 horas")
    duracion_val = st.selectbox("⏱️ **Duración**", OPCIONES_DURACION, index=OPCIONES_DURACION.index(duracion_guardada) if duracion_guardada in OPCIONES_DURACION else 1)
    obs_val = st.text_area("📝 **Observaciones**", value=datos_p.get("detalles", ""))

    if st.button("💾 Guardar Personal", use_container_width=True, type="primary"):
        payload = {
            "evento_id": e_id, "animador": animador_final, "dalinas": ", ".join(nombres_dalinas),
            "num_dalinas": int(cant_dalinas), "dj": dj_val, "staff": staff_val, "duracion": duracion_val, "detalles": obs_val
        }
        if datos_p:
            supabase.table("personal").update(payload).eq("id", datos_p["id"]).execute()
        else:
            supabase.table("personal").insert(payload).execute()
        
        st.cache_data.clear()
        st.session_state["editar_personal_id"] = None
        st.success("¡Guardado!")
        st.rerun()

@st.dialog("📋 Ficha del Evento")
def dialog_ver_ficha(evento):
    e_id = int(evento["id"])
    ev = supabase.table("eventos").select("*").eq("id", e_id).execute().data[0]
    p_data = supabase.table("personal").select("*").eq("evento_id", e_id).execute().data
    p_data = p_data[0] if p_data else {}

    fecha_fmt = formatear_fecha_larga(ev.get("fecha", ""))
    costo = float(ev.get('costo_total', 0) or 0)
    adelanto = float(ev.get('monto_adelanto', 0) or 0)
    pendiente = costo - adelanto
    marca = str(ev.get("marca", "madai")).lower()
    
    header_class, color_fondo, nombre_marca = ("header-alquiler", "#A2D2FF", "ALQUILER") if "local" in marca else (("header-risuena", "#B7E4C7", "RISUEÑA") if "risueña" in marca else ("header-madai", "#E0B0FF", "MADAI"))

    st.markdown(f'<style>div[data-testid="stDialog"] > div:first-child {{ background-color: {color_fondo} !important; }}</style>', unsafe_allow_html=True)
    st.markdown(f'<div class="{header_class}">🏷️ {nombre_marca} — 📅 {fecha_fmt}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="event-title">🎉 {ev.get("evento", "Sin Nombre")}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="data-line">👤 <b>Cliente:</b> {ev.get("cliente", "N/A")} | 📱 {ev.get("telefono", "N/A")}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="data-line">⏰ <b>Hora:</b> {ev.get("hora_contrato", "04:30 PM")}</div>', unsafe_allow_html=True)
    
    if "local" not in marca:
        st.markdown(f'<div class="data-line">📍 <b>Dirección:</b> {ev.get("direccion", "N/A")}</div>', unsafe_allow_html=True)
        
    if ev.get("incluye_alquiler"):
        st.markdown(f'<div class="data-line">📦 <b>Alquiler Extra:</b> {ev.get("detalle_alquiler", "")} (S/ {float(ev.get("monto_alquiler", 0)):.0f})</div>', unsafe_allow_html=True)

    st.markdown(f'<div class="data-line">💵 <b>Total:</b> S/ {costo:.0f} | 💳 <b>Adelanto:</b> S/ {adelanto:.0f} | <b style="color: #D90429;">Pendiente: S/ {pendiente:.0f}</b></div>', unsafe_allow_html=True)
    
    if "local" not in marca:
        st.markdown(f'<div class="{header_class}">👥 Personal Asignado</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="data-line">🎤 <b>Animadora:</b> {p_data.get("animador", "No asignada")}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="data-line">💃 <b>Dalinas:</b> {p_data.get("dalinas", "Ninguna")}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="data-line">🎧 <b>DJ:</b> {p_data.get("dj", "No asignado")}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="data-line">🛠️ <b>Staff:</b> {p_data.get("staff", "No asignado")}</div>', unsafe_allow_html=True)
        
        if st.button("✏️ Modificar Personal", use_container_width=True, key=f"mod_{ev['id']}"):
            st.session_state["ver_ficha_id"] = None
            st.session_state["editar_personal_id"] = ev["id"]
            st.rerun()

# ==============================================================================
# 6. RENDERIZAR LISTA
# ==============================================================================
def renderizar_lista_eventos(lista_eventos, key_prefix="evt"):
    if not lista_eventos:
        st.info("No hay eventos registrados.")
        return []

    seleccionados = []
    cols = st.columns(2)
    
    for idx, ev in enumerate(lista_eventos):
        with cols[idx % 2]:
            costo = float(ev.get('costo_total', 0) or 0)
            adelanto = float(ev.get('monto_adelanto', 0) or 0)
            pendiente = costo - adelanto
            tipo_str = str(ev.get('tipo', 'Show'))
            marca_raw = str(ev.get('marca', 'madai')).lower()
            is_local = "local" in marca_raw
            
            card_class, card_bg, badge_class, nombre_marca_tag = ("card-alquiler", "#A2D2FF", "badge-alquiler", "alquiler") if is_local else (("card-risuena", "#B7E4C7", "badge-risuena", "risueña") if "risueña" in marca_raw else ("card-madai", "#E0B0FF", "badge-madai", "madai"))
            
            p_data = ev.get("personal", [{}])
            p_data = p_data[0] if isinstance(p_data, list) and len(p_data) > 0 else (p_data if isinstance(p_data, dict) else {})
            
            tiene_personal = bool(p_data.get("animador") and p_data.get("animador") != "Ninguno" or p_data.get("dalinas") or p_data.get("dj") or p_data.get("staff"))

            html_tarjeta = (
                f'<div class="{card_class}">'
                f'<div class="badge-marca {badge_class}">{nombre_marca_tag}</div>'
                f'<div class="event-title">🎉 {ev.get("evento", "Sin Nombre")} - ({tipo_str})</div>'
                f'<div class="data-line">📅 <b>Fecha:</b> {formatear_fecha_larga(ev.get("fecha", ""))}</div>'
                f'<div class="data-line">⏰ <b>Hora:</b> {ev.get("hora_contrato", "04:30 PM")}</div>'
                f'<div class="data-line">👤 <b>Cliente:</b> {ev.get("cliente", "N/A")} | 📱 <b>Tel:</b> {ev.get("telefono", "N/A")}</div>'
            )
            if ev.get("incluye_alquiler"):
                html_tarjeta += f'<div class="data-line">📦 <b>Alquiler:</b> {ev.get("detalle_alquiler", "")} (S/ {float(ev.get("monto_alquiler", 0)):.0f})</div>'
            
            html_tarjeta += (
                f'<div class="data-line">💵 <b>Total:</b> S/ {costo:.0f} | 💳 <b>Adelanto:</b> S/ {adelanto:.0f} | <b style="color: #D90429;">Pendiente: S/ {pendiente:.0f}</b></div>'
                f'</div>'
            )

            st.markdown(f"""
                <style>
                div.st-key-{key_prefix}_card_{ev['id']} {{
                    background-color: {card_bg} !important; border-left: 6px solid #28A745 !important;
                    border-radius: 8px !important; padding: 0 0 10px 0 !important; margin-bottom: 14px !important;
                }}
                div.st-key-{key_prefix}_card_{ev['id']} [data-testid="stHorizontalBlock"] {{ gap: 0.5rem !important; padding: 0 10px !important; }}
                div.st-key-{key_prefix}_card_{ev['id']} [data-testid="stButton"] button {{ width: 100% !important; font-size: 0.85rem !important; padding: 6px 4px !important; }}
                </style>
            """, unsafe_allow_html=True)

            with st.container(key=f"{key_prefix}_card_{ev['id']}"):
                st.markdown(html_tarjeta, unsafe_allow_html=True)
                col1, col2, col3 = st.columns([1.2, 1.2, 1.5])
                
                with col1:
                    if is_local:
                        if st.button("📋 Ver Ficha", key=f"{key_prefix}_ver_{ev['id']}"):
                            st.session_state["ver_ficha_id"] = ev["id"]
                            st.rerun()
                    else:
                        if not tiene_personal:
                            if st.button("👤 Asignar", key=f"{key_prefix}_asg_{ev['id']}"):
                                st.session_state["editar_personal_id"] = ev["id"]
                                st.rerun()
                        else:
                            if st.button("📋 Ver Ficha", key=f"{key_prefix}_ver_{ev['id']}"):
                                st.session_state["ver_ficha_id"] = ev["id"]
                                st.rerun()
                with col2:
                    if not is_local and tiene_personal:
                        if st.button("✏️ Editar", key=f"{key_prefix}_edt_{ev['id']}"):
                            st.session_state["editar_personal_id"] = ev["id"]
                            st.rerun()
                with col3:
                    if st.checkbox("☑️ Enviar", key=f"{key_prefix}_chk_{ev['id']}"):
                        seleccionados.append(ev)
    return seleccionados

# ==============================================================================
# 7. INTERFAZ PRINCIPAL Y PESTAÑAS
# ==============================================================================
st.markdown(f'<div class="header-container"><img src="data:image/jpeg;base64,{logo_b64}" class="logo-inline"><div class="title-inline">MADAI</div></div>', unsafe_allow_html=True)

tabs = ["HOY", "DÍA SIGUIENTE", "REGISTRO", "ALQUILERES"]

tab_seleccionada = st.radio("Navegación", tabs, index=tabs.index(st.session_state["tab_activa"]), horizontal=True, label_visibility="collapsed")

if tab_seleccionada != st.session_state["tab_activa"]:
    st.session_state["tab_activa"] = tab_seleccionada
    st.session_state["editar_personal_id"] = None
    st.session_state["ver_ficha_id"] = None
    st.rerun()

eventos_todos = obtener_eventos()

if tab_seleccionada == "HOY":
    st.write("### 📅 Eventos del Día de Hoy")
    hoy_str = str(date.today())
    sel_hoy = renderizar_lista_eventos([e for e in eventos_todos if str(e.get("fecha")) == hoy_str], key_prefix="hoy")

    if sel_hoy:
        texto_masivo = f"📋 *RESUMEN DE EVENTOS SELECCIONADOS* ({formatear_fecha_larga(hoy_str)})\n\n"
        for i, ev_m in enumerate(sel_hoy, 1):
            texto_masivo += f"--- *EVENTO {i}* ---\n" + generar_texto_ficha(ev_m) + "\n\n\n"
        st.markdown(f'<a href="https://wa.me/?text={urllib.parse.quote(texto_masivo)}" target="_blank"><button style="width: 100%; background-color: #25D366; color: white; border: none; padding: 12px; border-radius: 8px; font-weight: bold; cursor: pointer;">📤 Enviar Fichas Seleccionadas al WhatsApp Grupal</button></a>', unsafe_allow_html=True)

elif tab_seleccionada == "DÍA SIGUIENTE":
    st.write("### 📆 Eventos del Día Siguiente")
    sig_str = str(date.today() + timedelta(days=1))
    sel_sig = renderizar_lista_eventos([e for e in eventos_todos if str(e.get("fecha")) == sig_str], key_prefix="sig")

    if sel_sig:
        texto_masivo_sig = f"📋 *RESUMEN DE EVENTOS PARA MAÑANA* ({formatear_fecha_larga(sig_str)})\n\n"
        for i, ev_s in enumerate(sel_sig, 1):
            texto_masivo_sig += f"--- *EVENTO {i}* ---\n" + generar_texto_ficha(ev_s) + "\n\n\n"
        st.markdown(f'<a href="https://wa.me/?text={urllib.parse.quote(texto_masivo_sig)}" target="_blank"><button style="width: 100%; background-color: #25D366; color: white; border: none; padding: 12px; border-radius: 8px; font-weight: bold; cursor: pointer;">📤 Enviar Fichas Seleccionadas al WhatsApp Grupal</button></a>', unsafe_allow_html=True)

elif tab_seleccionada == "REGISTRO":
    st.write("### ➕ Registrar Nuevo Evento")
    col1, col2 = st.columns(2)
    
    with col1:
        marca = st.selectbox("**Marca**", ["madai", "risueña"])
        evento_nom = st.text_input("**Nombre del Evento**")
        tipo_e = st.selectbox("**Tipo**", ["Show", "Show + Deco", "Deco"])
        cliente = st.text_input("**Cliente**")
        telefono = st.text_input("**Teléfono**")
        direccion = st.text_input("**Dirección**")
        fecha_e = st.date_input("**Fecha**", value=date.today())
    
    with col2:
        hora_c = st.text_input("**Hora**", value="04:30 PM")
        
        # Opción de alquiler extra antes del monto total
        incluye_alq = st.checkbox("📦 ¿Incluye Alquiler adicional en este evento?")
        detalle_alq = ""
        monto_alq = 0.0
        if incluye_alq:
            detalle_alq = st.text_input("Descripción del alquiler (ej. Sillas, mesas, toldo)")
            monto_alq = st.number_input("Monto del Alquiler (S/)", min_value=0.0, step=10.0, value=50.0)

        costo_t = st.number_input("**Monto Total del Show (S/)**", min_value=0.0, step=10.0, value=250.0)
        costo_total_final = costo_t + (monto_alq if incluye_alq else 0.0)
        monto_a = st.number_input("**Adelanto (S/)**", min_value=0.0, step=10.0, value=100.0)
        st.markdown(f"🔴 **Total General:** S/ {costo_total_final:.0f} | 🔴 **Pendiente:** S/ {max(0, costo_total_final - monto_a):.0f}")

    if st.button("📌 GUARDAR EVENTO", use_container_width=True):
        supabase.table("eventos").insert({
            "marca": marca, "evento": evento_nom, "tipo": tipo_e, "cliente": cliente,
            "telefono": telefono, "direccion": direccion, "fecha": str(fecha_e),
            "hora_contrato": hora_c, "costo_total": float(costo_total_final), "monto_adelanto": float(monto_a),
            "incluye_alquiler": incluye_alq, "detalle_alquiler": detalle_alq, "monto_alquiler": float(monto_alq)
        }).execute()
        st.cache_data.clear()
        st.session_state["tab_activa"] = "HOY"
        st.rerun()

elif tab_seleccionada == "ALQUILERES":
    st.write("### 📦 Registro de Alquileres Independientes")
    
    col_a1, col_a2 = st.columns(2)
    with col_a1:
        cliente_alq = st.text_input("**Nombre del Cliente**", key="alq_cli")
        telefono_alq = st.text_input("**Número de Teléfono**", key="alq_tel")
        direccion_alq = st.text_input("**Dirección (Opcional)**", key="alq_dir")
        fecha_alq = st.date_input("**Fecha del Alquiler**", value=date.today(), key="alq_fec")
        hora_alq = st.text_input("**Hora de Entrega / Recojo**", value="10:00 AM", key="alq_hora")
        
    with col_a2:
        st.markdown("#### 📋 Ítems Alquilados")
        if st.button("➕ Adicionar otro ítem"):
            st.session_state["num_items_alquiler"] += 1
            st.rerun()
            
        items_lista = []
        suma_items = 0.0
        for i in range(st.session_state["num_items_alquiler"]):
            col_i1, col_i2 = st.columns([2, 1])
            with col_i1:
                it_nom = st.text_input(f"Nombre producto {i+1}", key=f"it_nom_{i}")
            with col_i2:
                it_precio = st.number_input(f"Precio S/ {i+1}", min_value=0.0, step=10.0, value=0.0, key=f"it_prec_{i}")
            if it_nom.strip():
                items_lista.append(f"{it_nom.strip()} (S/ {it_precio:.0f})")
                suma_items += it_precio

        monto_adelanto_alq = st.number_input("**Adelanto recibido (S/)**", min_value=0.0, step=10.0, value=0.0, key="alq_adel")
        st.markdown(f"💵 **Total Alquiler:** S/ {suma_items:.0f} | 🔴 **Pendiente:** S/ {max(0, suma_items - monto_adelanto_alq):.0f}")

    if st.button("📌 GUARDAR ALQUILER", use_container_width=True):
        detalle_completo_items = " - ".join(items_lista)
        supabase.table("eventos").insert({
            "marca": "local", 
            "evento": f"Alquiler: {detalle_completo_items[:40]}...", 
            "tipo": "Alquiler", 
            "cliente": cliente_alq,
            "telefono": telefono_alq, 
            "direccion": direccion_alq if direccion_alq else "Local MADAI", 
            "fecha": str(fecha_alq),
            "hora_contrato": hora_alq, 
            "costo_total": float(suma_items), 
            "monto_adelanto": float(monto_adelanto_alq),
            "incluye_alquiler": True,
            "detalle_alquiler": detalle_completo_items,
            "monto_alquiler": float(suma_items)
        }).execute()
        st.cache_data.clear()
        st.session_state["num_items_alquiler"] = 1
        st.session_state["tab_activa"] = "HOY"
        st.success("¡Alquiler registrado correctamente!")
        st.rerun()

# ==============================================================================
# 8. DISPARADORES DE MODALES
# ==============================================================================
if st.session_state["ver_ficha_id"]:
    dialog_ver_ficha(next((e for e in eventos_todos if e["id"] == st.session_state["ver_ficha_id"]), {}))

if st.session_state["editar_personal_id"]:
    dialog_asignar_personal(next((e for e in eventos_todos if e["id"] == st.session_state["editar_personal_id"]), {}))
