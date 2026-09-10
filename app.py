def guardar_personal(evento_id, data_personal):
    # 1. Verificar si ya existe personal asignado a este evento
    existente = supabase.table("personal").select("id").eq("evento_id", evento_id).execute()
    
    if existente.data and len(existente.data) > 0:
        # Actualizar el registro existente
        res = supabase.table("personal").update(data_personal).eq("evento_id", evento_id).execute()
    else:
        # Insertar un nuevo registro vinculando el evento_id
        data_personal["evento_id"] = evento_id
        res = supabase.table("personal").insert(data_personal).execute()
        
    return res.data
