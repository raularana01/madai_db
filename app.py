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
if "lista_items_alquiler" not in st.session_state:
    st.session_state["lista_items_alquiler"] = []

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
.stApp {
    background-color: #f3e8ff;
}
"""
if fondo_b64:
    css_fondo = f"""
    .stApp {{
        background-image: linear-gradient(rgba(240, 230, 255, 0.65), rgba(240, 230, 255, 0.65)), url("data:image/jpeg;base64,{fondo_b64}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
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
    div[data-testid="stRadio"] > div {{ gap: 8px !important; padding: 0 !important; }}
    div[data-testid="stRadio"] label {{
        background-color: rgba(255, 255, 255, 0.85) !important;
        padding: 6px 18px !important; border-radius: 20px !important;
        border: 1.5px solid #7B2CBF !important; font-weight: bold !important; color: #7B2CBF !important;
    }}
    .badge-marca {{
        position: absolute; top: 8px; right: 12px; padding: 3px 10px; border-radius: 12px;
        font-size: 0.75rem; font-weight: bold; color: white; text-transform: uppercase;
    }}
    .badge-madai {{ background-color: #7B2CBF; }}
    .badge-risuena {{ background-color: #2B9348; }}
    .badge-local {{ background-color: #1D3557; }}
    .badge-mobiliario {{ background-color: #0077B6; }}
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

@st.cache_data(ttl=5)
def obtener_alquileres():
    res = supabase.table("alquileres").select("*").execute()
    return res.data if res.data else []

def generar_texto_ficha(ev):
    p_data = ev.get("personal", [{}])
    p_data = p_data[0] if isinstance(p_data, list) and len(p_data) > 0 else (p_data if isinstance(p_data, dict) else {})
    
    marca = str(ev.get("marca", "madai")).lower()
    tipo = str(ev.get("tipo", "Show"))
    fecha = formatear_fecha_larga(ev.get("fecha", ""))
    costo = float(ev.get('costo_total', 0) or 0)
    adelanto = float(ev.get('monto_adelanto', 0) or 0)
    pendiente = costo - adelanto

    if marca == "local":
        incluye_show = ev.get("incluye_show", False)
        costo_local = float(ev.get('costo_local', 600) or 600)
        adelanto_local = float(ev.get('adelanto_local', 0) or 0)
        costo_show = float(ev.get('costo_show', 0) or 0)
        adelanto_show = float(ev.get('adelanto_show', 0) or 0)
        
        texto = (
            f"🏰 *ALQUILER DE LOCAL MADAI*\n"
            f"📅 *FECHA:* {fecha}\n"
            f"⏰ *HORA LOCAL:* {ev.get('hora_contrato', '10:00 AM')}\n"
            f"👤 *CLIENTE:* {ev.get('cliente', 'N/A')} | 📱 *Tel:* {ev.get('telefono', 'N/A')}\n"
            f"💵 *Local:* S/ {costo_local:.0f} (Adelanto: S/ {adelanto_local:.0f} | Pend: S/ {max(0, costo_local - adelanto_local):.0f})\n"
        )
        if incluye_show:
            texto += (
                f"🎉 *SHOW ADICIONAL:* Sí\n"
                f"⏰ *Hora Show:* {ev.get('hora_show', 'N/A')}\n"
                f"💵 *Show:* S/ {costo_show:.0f} (Adelanto: S/ {adelanto_show:.0f} | Pend: S/ {max(0, costo_show - adelanto_show):.0f})\n"
                f"👥 *PERSONAL ASIGNADO:*\n"
                f"  • Animadora: {p_data.get('animador', 'No asignada')}\n"
                f"  • Dalinas: {p_data.get('dalinas', 'Ninguna')}\n"
                f"  • DJ: {p_data.get('dj', 'No asignado')}\n"
                f"  • Staff: {p_data.get('staff', 'No asignado')}\n"
            )
        texto += f"💰 *TOTAL GENERAL:* S/ {costo:.0f} | 💳 *ADELANTO TOTAL:* S/ {adelanto:.0f} | 🔴 *PENDIENTE TOTAL:* S/ {pendiente:.0f}\n"
        return texto

    texto = (
        f"🏷️ *MARCA: {marca.upper()}*\n"
        f"🎉 *RESUMEN DE EVENTO:* {ev.get('evento', 'Sin Nombre')} ({tipo})\n"
        f"📅 *FECHA:* {fecha}\n"
        f"⏰ *HORA:* {ev.get('hora_contrato', '04:30 PM')}\n"
        f"👤 *CLIENTE:* {ev.get('cliente', 'N/A')}\n"
        f"📍 *DIRECCIÓN:* {ev.get('direccion', 'N/A')}\n"
        f"👥 *PERSONAL ASIGNADO:*\n"
        f"  • Animadora: {p_data.get('animador', 'No asignada')}\n"
        f"  • Dalinas: {p_data.get('dalinas', 'Ninguna')}\n"
        f"  • DJ: {p_data.get('dj', 'No asignado')}\n"
        f"  • Staff: {p_data.get('staff', 'No asignado')}\n"
        f"  • Duración: {p_data.get('duracion', '2 horas')}\n"
    )
    if p_data.get("detalles"):
        texto += f"📝 *Notas:* {p_data.get('detalles')}\n"
        
    texto += f"💵 *Total:* S/ {costo:.0f} | 💳 *Adelanto:* S/ {adelanto:.0f} | 💰 *Pendiente:* S/ {pendiente:.0f}\n"
    return texto

# ==============================================================================
# 5. MODALES (CON KEYS ÚNICAS PARA EVITAR ERRORES)
# ==============================================================================
@st.dialog("👤 Asignar / Editar Personal")
def dialog_asignar_personal(evento):
    e_id = int(evento["id"])
    st.write(f"**Evento / Show:** {evento.get('evento', '')} - {evento.get('cliente', '')}")
    
    res_p = supabase.table("personal").select("*").eq("evento_id", e_id).execute()
    datos_p = res_p.data[0] if res_p.data else {}

    anim_guardada = datos_p.get("animador", "")
    idx_anim = OPCIONES_ANIMADORAS.index(anim_guardada) if anim_guardada in OPCIONES_ANIMADORAS else (OPCIONES_ANIMADORAS.index("Otro Animador") if anim_guardada else 0)

    # Se agregan keys dinámicas únicas
    anim_sel = st.selectbox("🎤 **Animadora**", OPCIONES_ANIMADORAS, index=idx_anim, key=f"anim_sel_{e_id}")
    
    if anim_sel == "Otro Animador":
        animador_final = st.text_input("Escribe el nombre:", value=anim_guardada if anim_guardada not in OPCIONES_ANIMADORAS else "", key=f"anim_text_{e_id}")
    else:
        animador_final = anim_sel

    cant_dalinas = st.number_input("Número de Dalinas", min_value=0, max_value=20, value=int(datos_p.get("num_dalinas", 1) or 1), key=f"num_dal_{e_id}")
    lista_dalinas_prev = [d.strip() for d in datos_p.get("dalinas", "").split(",") if d.strip()]
    
    nombres_dalinas = []
    for i in range(int(cant_dalinas)):
        val_prev = lista_dalinas_prev[i] if i < len(lista_dalinas_prev) else ""
        nom_d = st.text_input(f"Nombre Dalina {i+1}", value=val_prev, key=f"dal_nom_{e_id}_{i}")
        if nom_d.strip(): nombres_dalinas.append(nom_d.strip())

    dj_val = st.text_input("🎧 **DJ**", value=datos_p.get("dj", ""), key=f"dj_val_{e_id}")
    staff_val = st.text_input("🛠️ **Staff**", value=datos_p.get("staff", ""), key=f"staff_val_{e_id}")
    
    duracion_guardada = datos_p.get("duracion", "2 horas")
    idx_dur = OPCIONES_DURACION.index(duracion_guardada) if duracion_guardada in OPCIONES_DURACION else 1
    duracion_val = st.selectbox("⏱️ **Duración**", OPCIONES_DURACION, index=idx_dur, key=f"dur_sel_{e_id}")
    
    obs_val = st.text_area("📝 **Observaciones**", value=datos_p.get("detalles", ""), key=f"obs_val_{e_id}")

    if st.button("💾 Guardar Personal", use_container_width=True, type="primary", key=f"btn_save_pers_{e_id}"):
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

@st.dialog("📋 Resumen y Personal Asignado")
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
    
    if marca == "local":
        color_fondo, color_texto = "#1D3557", "#FFFFFF"
    elif marca == "risueña":
        color_fondo, color_texto = "#B7E4C7", "#1B5E20"
    else:
        color_fondo, color_texto = "#E0B0FF", "#4A0E4E"

    st.markdown(f'<style>div[data-testid="stDialog"] > div:first-child {{ background-color: {color_fondo} !important; color: {color_texto} !important; }}</style>', unsafe_allow_html=True)
    st.markdown(f'<div style="background-color: {color_fondo}; color: {color_texto}; padding: 10px; border-radius: 6px; font-weight: bold;">🏷️ {marca.upper()} — 📅 {fecha_fmt}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="event-title">🎉 {ev.get("evento", "Alquiler Local")}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="data-line">👤 <b>Cliente:</b> {ev.get("cliente", "N/A")} | 📱 <b>Tel:</b> {ev.get("telefono", "N/A")}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="data-line">⏰ <b>Hora Local:</b> {ev.get("hora_contrato", "10:00 AM")}</div>', unsafe_allow_html=True)
    
    if marca == "local":
        costo_local = float(ev.get('costo_local', 600) or 600)
        adelanto_local = float(ev.get('adelanto_local', 0) or 0)
        st.markdown(f'<div class="data-line">🏰 <b>Local:</b> Total S/ {costo_local:.0f} | Adelanto S/ {adelanto_local:.0f} | Pendiente S/ {max(0, costo_local - adelanto_local):.0f}</div>', unsafe_allow_html=True)
        
        if ev.get("incluye_show"):
            costo_show = float(ev.get('costo_show', 0) or 0)
            adelanto_show = float(ev.get('adelanto_show', 0) or 0)
            st.markdown(f'<div class="data-line">🎉 <b>Show Adicional:</b> S/ {costo_show:.0f} (Adelanto: S/ {adelanto_show:.0f}) | ⏰ <b>Hora Show:</b> {ev.get("hora_show", "N/A")}</div>', unsafe_allow_html=True)
            st.markdown(f'<div style="font-weight:bold; margin-top:6px;">👥 Personal Asignado al Show</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="data-line">🎤 <b>Animadora:</b> {p_data.get("animador", "No asignada")}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="data-line">💃 <b>Dalinas:</b> {p_data.get("dalinas", "Ninguna")}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="data-line">🎧 <b>DJ:</b> {p_data.get("dj", "No asignado")}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="data-line">🛠️ <b>Staff:</b> {p_data.get("staff", "No asignado")}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="data-line">📍 <b>Dirección:</b> {ev.get("direccion", "N/A")}</div>', unsafe_allow_html=True)
        st.markdown(f'<div style="font-weight:bold; margin-top:6px;">👥 Personal Asignado</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="data-line">🎤 <b>Animadora:</b> {p_data.get("animador", "No asignada")}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="data-line">💃 <b>Dalinas:</b> {p_data.get("dalinas", "Ninguna")}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="data-line">🎧 <b>DJ:</b> {p_data.get("dj", "No asignado")}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="data-line">🛠️ <b>Staff:</b> {p_data.get("staff", "No asignado")}</div>', unsafe_allow_html=True)

    st.markdown(f'<div class="data-line" style="margin-top: 8px;">💵 <b>Total General:</b> S/ {costo:.0f} | 💳 <b>Adelanto:</b> S/ {adelanto:.0f} | <b style="color: #D90429;">Pendiente Total: S/ {pendiente:.0f}</b></div>', unsafe_allow_html=True)
    
    if marca != "local" or ev.get("incluye_show"):
        if st.button("✏️ Modificar Personal", use_container_width=True, key=f"mod_btn_ficha_{ev['id']}"):
            st.session_state["ver_ficha_id"] = None
            st.session_state["editar_personal_id"] = ev["id"]
            st.rerun()

# ==============================================================================
# 6. RENDERIZAR LISTAS (EVENTOS Y ALQUILERES)
# ==============================================================================
def renderizar_lista_eventos(lista_eventos, key_prefix="evt"):
    if not lista_eventos:
        st.info("No hay eventos registrados para esta fecha.")
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
            
            p_data = ev.get("personal", [{}])
            p_data = p_data[0] if isinstance(p_data, list) and len(p_data) > 0 else (p_data if isinstance(p_data, dict) else {})
            
            tiene_personal = bool(p_data.get("animador") and p_data.get("animador") != "Ninguno" or p_data.get("dalinas") or p_data.get("dj") or p_data.get("staff"))

            if marca_raw == "local":
                card_bg = "#E2E8F0"
                border_color = "#1D3557"
                badge_class = "badge-local"
                nombre_marca_tag = "alquiler local"
                
                costo_local = float(ev.get('costo_local', 600) or 600)
                adelanto_local = float(ev.get('adelanto_local', 0) or 0)
                pendiente_local = max(0, costo_local - adelanto_local)
                incluye_show = ev.get("incluye_show", False)
                
                html_tarjeta = (
                    f'<div style="padding: 0 0 12px 0; border-radius: 8px; margin-bottom: 12px; position: relative;">'
                    f'<div class="badge-marca {badge_class}">{nombre_marca_tag}</div>'
                    f'<div class="event-title">🏰 {ev.get("evento", "Alquiler de Local")}</div>'
                    f'<div class="data-line">📅 <b>Fecha:</b> {formatear_fecha_larga(ev.get("fecha", ""))}</div>'
                    f'<div class="data-line">⏰ <b>Hora Local:</b> {ev.get("hora_contrato", "10:00 AM")}</div>'
                    f'<div class="data-line">👤 <b>Cliente:</b> {ev.get("cliente", "N/A")} | 📱 <b>Tel:</b> {ev.get("telefono", "N/A")}</div>'
                    f'<hr style="margin: 6px 10px; border-top: 1px dashed #bbb;">'
                    f'<div class="data-line">🏢 <b>Local:</b> S/ {costo_local:.0f} | Adelanto: S/ {adelanto_local:.0f} | <b style="color: #D90429;">Pend: S/ {pendiente_local:.0f}</b></div>'
                )
                if incluye_show:
                    costo_show = float(ev.get('costo_show', 0) or 0)
                    adelanto_show = float(ev.get('adelanto_show', 0) or 0)
                    pendiente_show = max(0, costo_show - adelanto_show)
                    html_tarjeta += (
                        f'<div class="data-line" style="color: #7B2CBF; font-weight: bold;">🎉 Show Adicional (Hora: {ev.get("hora_show", "N/A")})</div>'
                        f'<div class="data-line">💵 <b>Show:</b> S/ {costo_show:.0f} | Adelanto: S/ {adelanto_show:.0f} | <b style="color: #D90429;">Pend: S/ {pendiente_show:.0f}</b></div>'
                        f'<div class="data-line">🎤 <b>Animadora:</b> {p_data.get("animador", "No asignada")} | 💃 <b>Dalinas:</b> {p_data.get("dalinas", "Ninguna")}</div>'
                    )
                else:
                    html_tarjeta += f'<div class="data-line" style="color: #666; font-style: italic;">ℹ️ Solo Alquiler de Local (Modo Lectura)</div>'
                
                html_tarjeta += f'<div class="data-line" style="margin-top: 4px;">💵 <b>Total General:</b> S/ {costo:.0f} | 💳 <b>Adelanto Total:</b> S/ {adelanto:.0f} | <b style="color: #D90429;">Pendiente Total: S/ {pendiente:.0f}</b></div>'
                html_tarjeta += f'</div>'
            else:
                card_bg = "#B7E4C7" if marca_raw == "risueña" else "#E0B0FF"
                border_color = "#28A745" if marca_raw == "risueña" else "#7B2CBF"
                badge_class = "badge-risuena" if marca_raw == "risueña" else "badge-madai"
                nombre_marca_tag = marca_raw

                html_tarjeta = (
                    f'<div style="padding: 0 0 12px 0; border-radius: 8px; margin-bottom: 12px; position: relative;">'
                    f'<div class="badge-marca {badge_class}">{nombre_marca_tag}</div>'
                    f'<div class="event-title">🎉 {ev.get("evento", "Sin Nombre")} - ({tipo_str})</div>'
                    f'<div class="data-line">📅 <b>Fecha:</b> {formatear_fecha_larga(ev.get("fecha", ""))}</div>'
                    f'<div class="data-line">⏰ <b>Hora:</b> {ev.get("hora_contrato", "04:30 PM")}</div>'
                    f'<div class="data-line">👤 <b>Cliente:</b> {ev.get("cliente", "N/A")} | 📱 <b>Tel:</b> {ev.get("telefono", "N/A")}</div>'
                    f'<div class="data-line">📍 <b>Dirección:</b> {ev.get("direccion", "N/A")}</div>'
                    f'<hr style="margin: 6px 10px; border-top: 1px dashed #bbb;">'
                    f'<div class="data-line">🎤 <b>Animadora:</b> {p_data.get("animador", "No asignada")} | 💃 <b>Dalinas:</b> {p_data.get("dalinas", "Ninguna")}</div>'
                    f'<div class="data-line">🎧 <b>DJ:</b> {p_data.get("dj", "No asignado")} | 🛠️ <b>Staff:</b> {p_data.get("staff", "No asignado")}</div>'
                    f'<div class="data-line">💵 <b>Total:</b> S/ {costo:.0f} | 💳 <b>Adelanto:</b> S/ {adelanto:.0f} | <b style="color: #D90429;">Pendiente: S/ {pendiente:.0f}</b></div>'
                    f'</div>'
                )

            st.markdown(f"""
                <style>
                div.st-key-{key_prefix}_card_{ev['id']} {{
                    background-color: {card_bg} !important; border-left: 6px solid {border_color} !important;
                    border-radius: 8px !important; padding: 0 0 10px 0 !important; margin-bottom: 14px !important;
                }}
                div.st-key-{key_prefix}_card_{ev['id']} [data-testid="stHorizontalBlock"] {{ gap: 0.5rem !important; padding: 0 10px !important; }}
                div.st-key-{key_prefix}_card_{ev['id']} [data-testid="stButton"] button {{ width: 100% !important; font-size: 0.85rem !important; padding: 6px 4px !important; }}
                </style>
            """, unsafe_allow_html=True)

            with st.container(key=f"{key_prefix}_card_{ev['id']}"):
                st.markdown(html_tarjeta, unsafe_allow_html=True)
                mostrar_botones = (marca_raw != "local") or (marca_raw == "local" and ev.get("incluye_show"))
                
                if mostrar_botones:
                    col1, col2, col3 = st.columns([1.2, 1.2, 1.5])
                    with col1:
                        if not tiene_personal:
                            if st.button("👤 Asignar", key=f"{key_prefix}_asg_{ev['id']}"):
                                st.session_state["editar_personal_id"] = ev["id"]
                                st.rerun()
                        else:
                            if st.button("📋 Ver Ficha", key=f"{key_prefix}_ver_{ev['id']}"):
                                st.session_state["ver_ficha_id"] = ev["id"]
                                st.rerun()
                    with col2:
                        if tiene_personal:
                            if st.button("✏️ Editar", key=f"{key_prefix}_edt_{ev['id']}"):
                                st.session_state["editar_personal_id"] = ev["id"]
                                st.rerun()
                    with col3:
                        if st.checkbox("☑️ Enviar", key=f"{key_prefix}_chk_{ev['id']}"):
                            seleccionados.append(ev)
                else:
                    col_lectura, col_chk = st.columns([2, 1.5])
                    with col_lectura:
                        if st.button("📋 Ver Ficha", key=f"{key_prefix}_ver_lectura_{ev['id']}"):
                            st.session_state["ver_ficha_id"] = ev["id"]
                            st.rerun()
                    with col_chk:
                        if st.checkbox("☑️ Enviar", key=f"{key_prefix}_chk_{ev['id']}"):
                            seleccionados.append(ev)
    return seleccionados

def renderizar_lista_alquileres_lectura(lista_alquileres, key_prefix="alq_lectura"):
    if not lista_alquileres:
        return
    
    st.markdown("### 📦 Alquileres de Mobiliario y Productos (Fecha Seleccionada)")
    cols = st.columns(2)
    
    for idx, alq in enumerate(lista_alquileres):
        with cols[idx % 2]:
            costo = float(alq.get('costo_total', 0) or 0)
            adelanto = float(alq.get('monto_adelanto', 0) or 0)
            pendiente = costo - adelanto
            
            html_tarjeta = (
                f'<div style="padding: 0 0 12px 0; border-radius: 8px; margin-bottom: 12px; position: relative;">'
                f'<div class="badge-marca badge-mobiliario">mobiliario</div>'
                f'<div class="event-title">📦 Alquiler de Productos</div>'
                f'<div class="data-line">📅 <b>Fecha Entrega:</b> {formatear_fecha_larga(alq.get("fecha", ""))}</div>'
                f'<div class="data-line">⏰ <b>Hora:</b> {alq.get("hora_entrega", "N/A")}</div>'
                f'<div class="data-line">👤 <b>Cliente:</b> {alq.get("cliente", "N/A")} | 📱 <b>Tel:</b> {alq.get("telefono", "N/A")}</div>'
                f'<div class="data-line">📍 <b>Dirección:</b> {alq.get("direccion", "No especificada")}</div>'
                f'<hr style="margin: 6px 10px; border-top: 1px dashed #bbb;">'
                f'<div class="data-line">🛍️ <b>Items:</b> {alq.get("items", "N/A")}</div>'
                f'<div class="data-line">💵 <b>Total:</b> S/ {costo:.0f} | 💳 <b>Adelanto:</b> S/ {adelanto:.0f} | <b style="color: #D90429;">Pendiente: S/ {pendiente:.0f}</b></div>'
                f'<div class="data-line" style="color: #666; font-style: italic; margin-top: 4px;">🔒 Vista en modo lectura</div>'
                f'</div>'
            )

            st.markdown(f"""
                <style>
                div.st-key-{key_prefix}_card_{alq['id']} {{
                    background-color: #E0F2FE !important; border-left: 6px solid #0077B6 !important;
                    border-radius: 8px !important; padding: 0 0 10px 0 !important; margin-bottom: 14px !important;
                }}
                </style>
            """, unsafe_allow_html=True)

            with st.container(key=f"{key_prefix}_card_{alq['id']}"):
                st.markdown(html_tarjeta, unsafe_allow_html=True)

# ==============================================================================
# 7. LLAMADAS ÚNICAS A LOS DIÁLOGOS
# ==============================================================================
eventos_todos = obtener_eventos()
alquileres_todos = obtener_alquileres()

# Se ubican aquí una ÚNICA VEZ antes del renderizado de los tabs
if st.session_state.get("ver_ficha_id"):
    ev_f = next((e for e in eventos_todos if e["id"] == st.session_state["ver_ficha_id"]), None)
    if ev_f: dialog_ver_ficha(ev_f)

if st.session_state.get("editar_personal_id"):
    ev_p = next((e for e in eventos_todos if e["id"] == st.session_state["editar_personal_id"]), None)
    if ev_p: dialog_asignar_personal(ev_p)

# ==============================================================================
# 8. INTERFAZ PRINCIPAL Y NAVEGACIÓN
# ==============================================================================
st.markdown(f'<div class="header-container"><img src="data:image/jpeg;base64,{logo_b64}" class="logo-inline"><div class="title-inline">MADAI</div></div>', unsafe_allow_html=True)

tabs = ["HOY", "DÍA SIGUIENTE", "ALQUILERES", "REGISTRO"]
tab_seleccionada = st.radio("Navegación", tabs, index=tabs.index(st.session_state["tab_activa"]), horizontal=True, label_visibility="collapsed")

if tab_seleccionada != st.session_state["tab_activa"]:
    st.session_state["tab_activa"] = tab_seleccionada
    st.session_state["editar_personal_id"] = None
    st.session_state["ver_ficha_id"] = None
    st.rerun()

if tab_seleccionada == "HOY":
    st.write("### 📅 Eventos y Alquileres del Día de Hoy")
    hoy_str = str(date.today())
    
    renderizar_lista_alquileres_lectura([a for a in alquileres_todos if str(a.get("fecha")) == hoy_str], key_prefix="hoy_alq")
    st.markdown("---")
    sel_hoy = renderizar_lista_eventos([e for e in eventos_todos if str(e.get("fecha")) == hoy_str], key_prefix="hoy")

    if sel_hoy:
        texto_masivo = f"📋 *RESUMEN DE EVENTOS SELECCIONADOS* ({formatear_fecha_larga(hoy_str)})\n\n"
        for i, ev_m in enumerate(sel_hoy, 1): texto_masivo += f"--- *EVENTO {i}* ---\n" + generar_texto_ficha(ev_m) + "\n"
        st.markdown(f'<a href="https://wa.me/?text={urllib.parse.quote(texto_masivo)}" target="_blank"><button style="width: 100%; background-color: #25D366; color: white; border: none; padding: 12px; border-radius: 8px; font-weight: bold; cursor: pointer;">📤 Enviar Fichas Seleccionadas al WhatsApp Grupal</button></a>', unsafe_allow_html=True)

elif tab_seleccionada == "DÍA SIGUIENTE":
    st.write("### 📆 Eventos y Alquileres del Día Siguiente")
    sig_str = str(date.today() + timedelta(days=1))
    
    renderizar_lista_alquileres_lectura([a for a in alquileres_todos if str(a.get("fecha")) == sig_str], key_prefix="sig_alq")
    st.markdown("---")
    sel_sig = renderizar_lista_eventos([e for e in eventos_todos if str(e.get("fecha")) == sig_str], key_prefix="sig")

    if sel_sig:
        texto_masivo_sig = f"📋 *RESUMEN DE EVENTOS PARA MAÑANA* ({formatear_fecha_larga(sig_str)})\n\n"
        for i, ev_s in enumerate(sel_sig, 1): texto_masivo_sig += f"--- *EVENTO {i}* ---\n" + generar_texto_ficha(ev_s) + "\n"
        st.markdown(f'<a href="https://wa.me/?text={urllib.parse.quote(texto_masivo_sig)}" target="_blank"><button style="width: 100%; background-color: #25D366; color: white; border: none; padding: 12px; border-radius: 8px; font-weight: bold; cursor: pointer;">📤 Enviar Fichas Seleccionadas al WhatsApp Grupal</button></a>', unsafe_allow_html=True)

elif tab_seleccionada == "ALQUILERES":
    st.write("### 🛋️ Gestión y Registro de Alquileres de Productos")
    
    with st.expander("➕ Registrar Nuevo Alquiler de Productos", expanded=True):
        col_a1, col_a2 = st.columns(2)
        with col_a1:
            alq_cliente = st.text_input("**Nombre del Cliente**", key="alq_cli_reg")
            alq_tel = st.text_input("**Teléfono**", key="alq_tel_reg")
            alq_dir = st.text_input("**Dirección (Opcional)**", key="alq_dir_reg")
            alq_fecha = st.date_input("**Fecha de Entrega**", value=date.today(), key="alq_fec_reg")
            alq_hora = st.text_input("**Hora de Entrega**", value="10:00 AM", key="alq_hor_reg")
            
        with col_a2:
            st.markdown("**📝 Ingreso de Ítems (Uno por uno)**")
            col_it1, col_it2 = st.columns([3, 1])
            with col_it1:
                nuevo_item = st.text_input("Escribe el producto/ítem:", key="input_nuevo_item", label_visibility="collapsed", placeholder="Ej: Mesa vestida, silla...")
            with col_it2:
                if st.button("➕ Agregar", key="btn_add_item"):
                    if nuevo_item.strip():
                        st.session_state["lista_items_alquiler"].append(nuevo_item.strip())
                        st.rerun()
            
            if st.session_state["lista_items_alquiler"]:
                for idx, item in enumerate(st.session_state["lista_items_alquiler"]):
                    ci1, ci2 = st.columns([4, 1])
                    ci1.text(f"• {item}")
                    if ci2.button("❌", key=f"del_item_reg_{idx}"):
                        st.session_state["lista_items_alquiler"].pop(idx)
                        st.rerun()
            else:
                st.caption("Aún no hay ítems agregados en la lista.")

        st.markdown("---")
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            alq_costo = st.number_input("**Monto Total del Alquiler (S/)**", min_value=0, step=10, value=150, key="alq_cos_reg")
        with col_m2:
            alq_adelanto = st.number_input("**Adelanto (S/)**", min_value=0, step=10, value=50, key="alq_ade_reg")
        
        st.markdown(f"🔴 **Saldo Pendiente:** S/ {max(0, alq_costo - alq_adelanto):.0f}")

        if st.button("📌 GUARDAR ALQUILER", use_container_width=True, key="btn_guardar_alq_final"):
            if alq_cliente and st.session_state["lista_items_alquiler"]:
                items_texto = ", ".join(st.session_state["lista_items_alquiler"])
                supabase.table("alquileres").insert({
                    "cliente": alq_cliente, "telefono": alq_tel, "direccion": alq_dir,
                    "fecha": str(alq_fecha), "hora_entrega": alq_hora, "items": items_texto,
                    "costo_total": float(alq_costo), "monto_adelanto": float(alq_adelanto)
                }).execute()
                st.session_state["lista_items_alquiler"] = []
                st.cache_data.clear()
                st.success("¡Alquiler registrado con éxito!")
                st.rerun()
            else:
                st.warning("Debes ingresar el nombre del cliente y al menos un ítem de alquiler.")

    st.markdown("---")
    st.write("### 📋 Historial de Alquileres Programados")
    filtro_fecha_alq = st.date_input("Filtrar por fecha de entrega:", value=date.today(), key="filtro_alq_fec")
    
    alquileres_filtrados = [a for a in alquileres_todos if str(a.get("fecha")) == str(filtro_fecha_alq)]
    if alquileres_filtrados:
        cols_alq = st.columns(2)
        for idx, alq in enumerate(alquileres_filtrados):
            with cols_alq[idx % 2]:
                costo = float(alq.get('costo_total', 0) or 0)
                adelanto = float(alq.get('monto_adelanto', 0) or 0)
                pendiente = costo - adelanto
                
                with st.container(border=True):
                    st.markdown(f"**📦 Cliente:** {alq.get('cliente', 'N/A')} | **Tel:** {alq.get('telefono', 'N/A')}")
                    st.write(f"⏰ **Hora:** {alq.get('hora_entrega', 'N/A')} | 📍 **Dir:** {alq.get('direccion', 'N/A')}")
                    st.write(f"🛍️ **Items:** {alq.get('items', 'N/A')}")
                    st.markdown(f"💵 **Total:** S/ {costo:.0f} | 💳 **Adelanto:** S/ {adelanto:.0f} | <b style='color: #D90429;'>Pendiente: S/ {pendiente:.0f}</b>", unsafe_allow_html=True)
    else:
        st.info("No hay alquileres registrados para la fecha seleccionada.")

elif tab_seleccionada == "REGISTRO":
    st.write("### ➕ Registrar Nuevo Evento / Alquiler de Local")
    col1, col2 = st.columns(2)
    
    with col1:
        marca = st.selectbox("**Marca o Tipo**", ["madai", "risueña", "local"], key="reg_marca")
        
        if marca == "local":
            evento_nom = "Alquiler de Local MADAI"
            tipo_e = "Alquiler de Local"
        else:
            evento_nom = st.text_input("**Nombre del Evento**", key="reg_ev_nom")
            tipo_e = st.selectbox("**Tipo**", ["Show", "Show + Deco", "Deco"], key="reg_tipo")
            
        cliente = st.text_input("**Cliente**", key="reg_cli")
        telefono = st.text_input("**Teléfono**", key="reg_tel")
        direccion = "Local MADAI" if marca == "local" else st.text_input("**Dirección**", key="reg_dir")
        fecha_e = st.date_input("**Fecha**", value=date.today(), key="reg_fec")
    
    with col2:
        if marca == "local":
            hora_c = st.text_input("**Hora de Inicio Local**", value="10:00 AM", key="reg_hor_c_loc")
            costo_local = st.number_input("**Monto Alquiler Local (S/)**", min_value=0, step=10, value=600, key="reg_cost_loc")
            adelanto_local = st.number_input("**Adelanto Local (S/)**", min_value=0, step=10, value=200, key="reg_adel_loc")
            
            st.markdown("---")
            incluye_show = st.checkbox("🎉 ¿Adicionar Show al Local?", key="reg_inc_show")
            
            if incluye_show:
                hora_show = st.text_input("**Hora del Show**", value="04:00 PM", key="reg_hor_show")
                costo_show = st.number_input("**Monto del Show (S/)**", min_value=0, step=10, value=300, key="reg_cost_show")
                adelanto_show = st.number_input("**Adelanto del Show (S/)**", min_value=0, step=10, value=100, key="reg_adel_show")
            else:
                hora_show = ""
                costo_show = 0
                adelanto_show = 0
                
            costo_t = costo_local + costo_show
            monto_a = adelanto_local + adelanto_show
            st.markdown(f"🔴 **Pendiente Total:** S/ {max(0, costo_t - monto_a):.0f}")
        else:
            hora_c = st.text_input("**Hora**", value="04:30 PM", key="reg_hor_c")
            costo_t = st.number_input("**Monto Total (S/)**", min_value=0, step=10, value=250, key="reg_cost_t")
            monto_a = st.number_input("**Adelanto (S/)**", min_value=0, step=10, value=100, key="reg_adel_t")
            incluye_show = False
            costo_local = 0
            adelanto_local = 0
            costo_show = 0
            adelanto_show = 0
            hora_show = ""
            st.markdown(f"🔴 **Pendiente:** S/ {max(0, costo_t - monto_a):.0f}")

    if st.button("📌 GUARDAR REGISTRO", use_container_width=True, key="btn_guardar_registro_final"):
        payload = {
            "marca": marca, "evento": evento_nom, "tipo": tipo_e, "cliente": cliente,
            "telefono": telefono, "direccion": direccion, "fecha": str(fecha_e),
            "hora_contrato": hora_c, "costo_total": float(costo_t), "monto_adelanto": float(monto_a),
            "incluye_show": incluye_show if marca == "local" else False,
            "costo_local": float(costo_local) if marca == "local" else 0,
            "adelanto_local": float(adelanto_local) if marca == "local" else 0,
            "costo_show": float(costo_show) if marca == "local" else 0,
            "adelanto_show": float(adelanto_show) if marca == "local" else 0,
            "hora_show": hora_show if marca == "local" else ""
        }
        supabase.table("eventos").insert(payload).execute()
        st.cache_data.clear()
        st.session_state["tab_activa"] = "HOY"
        st.rerun()
