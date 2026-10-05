import os
import sqlite3
import json
import io
import zipfile
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(
    page_title="Sistema CIDINT ULA",
    page_icon="📚",
    layout="wide"
)

def init_db():
    conn = sqlite3.connect("sistema_actividades.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS usuarios (cedula TEXT PRIMARY KEY, nombre TEXT, password TEXT, rol TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS actividades (id INTEGER PRIMARY KEY AUTOINCREMENT, cedula TEXT, trimestre TEXT, año INTEGER, categoria TEXT, detalles TEXT, archivo TEXT)")
    
    cursor.execute("INSERT OR IGNORE INTO usuarios VALUES ('admin', 'Administrador General', '1234', 'Administrador')")
    cursor.execute("INSERT OR IGNORE INTO usuarios VALUES ('12345678', 'José Antonio Pérez', '1234', 'Profesor')")
    conn.commit()
    conn.close()
    
    if not os.path.exists("evidencias"):
        os.makedirs("evidencias")

init_db()

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["user"] = None
    st.session_state["rol"] = None
    st.session_state["cedula"] = None

if not st.session_state["logged_in"]:
    c1, c2 = st.columns(2)
    with c1:
        if os.path.exists("logo_ula.png"):
            st.image("logo_ula.png", use_container_width=True)
        else:
            st.warning("⚠️ Falta logo_ula.png")
    with c2:
        if os.path.exists("logo_cidint.png"):
            st.image("logo_cidint.png", use_container_width=True)
        else:
            st.warning("⚠️ Falta logo_cidint.png")

    st.header("Sistema de Registro de Actividades Académicas y de Investigación")
    st.divider()

    _, cm, _ = st.columns([1, 1, 1])
    with cm:
        st.subheader("Iniciar Sesión")
        ced = st.text_input("Cédula de Identidad o Usuario")
        pas = st.text_input("Contraseña", type="password")

        if st.button("Ingresar al Sistema", use_container_width=True):
            conn = sqlite3.connect("sistema_actividades.db")
            cur = conn.cursor()
            cur.execute("SELECT nombre, rol FROM usuarios WHERE cedula = ? AND password = ?", (ced, pas))
            row = cur.fetchone()
            conn.close()

            if row:
                st.session_state["logged_in"] = True
                st.session_state["user"] = row[0]
                st.session_state["rol"] = row[1]
                st.session_state["cedula"] = ced
                st.rerun()
            else:
                st.error("Usuario/Cédula o contraseña incorrecta.")

    st.write("")
    st.write("")
    st.caption("Desarrollado por: **Ing. José Antonio Pérez Bracho**")

else:
    st.sidebar.title("Menú del Sistema")
    st.sidebar.write("Usuario: " + str(st.session_state["user"]))
    st.sidebar.write("Rol: " + str(st.session_state["rol"]))
    st.sidebar.divider()

    if st.sidebar.button("Cerrar Sesión"):
        st.session_state["logged_in"] = False
        st.rerun()

    # ==========================================
    # MÓDULO DEL PROFESOR / INVESTIGADOR
    # ==========================================
    if st.session_state["rol"] in ["Profesor", "Investigador"]:
        titulo_modulo = "Módulo de Carga de Actividades (Profesor)" if st.session_state["rol"] == "Profesor" else "Módulo de Carga de Actividades (Investigador)"
        st.title(titulo_modulo)
        
        tab_registro, tab_historial, tab_stats, tab_perfil = st.tabs(["📝 Registrar Actividad", "🗂️️ Mi Historial", "📊 Mis Estadísticas", "🔑 Mi Perfil y Contraseña"])
        
        with tab_registro:
            if "lista_temporal" not in st.session_state:
                st.session_state["lista_temporal"] = []

            st.write("Por favor, indique el período de reporte antes de registrar sus actividades:")
            col_per1, col_per2 = st.columns(2)
            with col_per1:
                trimestre = st.selectbox("Trimestre a reportar:", ["Trimestre I", "Trimestre II", "Trimestre III", "Trimestre IV"])
            with col_per2:
                año_actual = datetime.now().year
                año = st.number_input("Año:", min_value=2020, max_value=2050, value=año_actual, step=1)
                
            st.divider()

            categoria = st.selectbox("1. Seleccione la categoría a registrar:", ["Actividades Académicas", "Investigación y Proyectos", "Publicaciones", "Otros (Tutorías y Asesorías)"])
            
            with st.form("form_carga", clear_on_submit=True):
                st.subheader("2. Llene los datos de la actividad")
                
                datos_nuevos = {
                    "Trimestre": trimestre,
                    "Año": año,
                    "Categoría": categoria
                }
                
                evidencia_cargada = None
                
                if categoria == "Actividades Académicas":
                    datos_nuevos["Asignatura"] = st.text_input("Nombre de la asignatura")
                    datos_nuevos["Horas Semanales"] = st.number_input("Horas semanales", min_value=1, step=1)
                    datos_nuevos["Período"] = st.text_input("Período académico (Ej. A-2026)")
                    
                elif categoria == "Investigación y Proyectos":
                    datos_nuevos["Título"] = st.text_input("Título del proyecto")
                    datos_nuevos["Rol"] = st.text_input("Rol en el proyecto")
                    datos_nuevos["Línea de Inv."] = st.text_input("Línea de investigación")
                    datos_nuevos["Colaboradores"] = st.text_input("Colaboradores")
                    datos_nuevos["Instituciones"] = st.text_input("Instituciones aliadas")
                    datos_nuevos["Horas Totales"] = st.number_input("Horas de trabajo totales", min_value=1, step=1)
                    evidencia_cargada = st.file_uploader("Evidencia (Portada/Documento)", type=["png", "jpg", "pdf"])
                        
                elif categoria == "Publicaciones":
                    datos_nuevos["Tipo"] = st.selectbox("Tipo", ["Artículo arbitrado", "Libro", "Capítulo", "Otro"])
                    datos_nuevos["Título"] = st.text_input("Título de la publicación")
                    datos_nuevos["Revista/Editorial"] = st.text_input("Nombre de la revista o editorial")
                    datos_nuevos["DOI/Enlace"] = st.text_input("DOI o enlace")
                    datos_nuevos["Año Pub."] = st.number_input("Año de publicación", min_value=1950, max_value=2030, step=1)
                    datos_nuevos["Colaboradores"] = st.text_input("Colaboradores")
                    evidencia_cargada = st.file_uploader("Evidencia (Portada/Artículo)", type=["png", "jpg", "pdf"])
                        
                elif categoria == "Otros (Tutorías y Asesorías)":
                    datos_nuevos["Tipo"] = st.text_input("Tipo de actividad (Ej. Tutoría de Tesis)")
                    datos_nuevos["Descripción"] = st.text_input("Descripción o título")
                    datos_nuevos["Beneficiario"] = st.text_input("Beneficiario o contraparte")
                    datos_nuevos["Horas/Período"] = st.text_input("Horas dedicadas o Período")

                enviado = st.form_submit_button("Añadir a la lista temporal", type="secondary")
                
                if enviado:
                    nombre_archivo = "Sin archivo"
                    if evidencia_cargada is not None:
                        nombre_archivo = str(año) + "_" + trimestre.replace(" ", "") + "_" + evidencia_cargada.name
                        ruta_guardado = os.path.join("evidencias", nombre_archivo)
                        with open(ruta_guardado, "wb") as f:
                            f.write(evidencia_cargada.getbuffer())
                    
                    datos_nuevos["Archivo"] = nombre_archivo
                    st.session_state["lista_temporal"].append(datos_nuevos)
                    st.success("¡Actividad añadida a la lista de revisión temporal!")

            st.divider()
            st.subheader("3. Resumen de Actividades por Guardar")
            if len(st.session_state["lista_temporal"]) > 0:
                df = pd.DataFrame(st.session_state["lista_temporal"])
                st.dataframe(df, use_container_width=True)
                
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("Limpiar Lista", use_container_width=True):
                        st.session_state["lista_temporal"] = []
                        st.rerun()
                with col_btn2:
                    if st.button("Confirmar y Guardar Definitivamente", type="primary", use_container_width=True):
                        conn = sqlite3.connect("sistema_actividades.db")
                        cur = conn.cursor()
                        for act in st.session_state["lista_temporal"]:
                            t = act.get("Trimestre", "")
                            a = act.get("Año", 0)
                            c = act.get("Categoría", "")
                            ar = act.get("Archivo", "Sin archivo")
                            detalles = json.dumps(act, ensure_ascii=False)
                            
                            cur.execute("INSERT INTO actividades (cedula, trimestre, año, categoria, detalles, archivo) VALUES (?, ?, ?, ?, ?, ?)", 
                                        (st.session_state["cedula"], t, a, c, detalles, ar))
                        conn.commit()
                        conn.close()
                        
                        st.success("¡Información guardada permanentemente en la Base de Datos!")
                        st.session_state["lista_temporal"] = []
            else:
                st.info("Aún no has agregado actividades en esta sesión. Llena el formulario de arriba.")

        with tab_historial:
            st.subheader("Historial de Actividades Registradas")
            conn = sqlite3.connect("sistema_actividades.db")
            df_historial = pd.read_sql_query("SELECT trimestre AS Trimestre, año AS Año, categoria AS Categoría, detalles AS Detalles, archivo AS Archivo FROM actividades WHERE cedula = ?", conn, params=(st.session_state["cedula"],))
            conn.close()
            
            if not df_historial.empty:
                st.dataframe(df_historial, use_container_width=True)
            else:
                st.info("Aún no tienes actividades registradas en la base de datos.")

        with tab_stats:
            st.subheader("Gráficos de Resumen Personal")
            conn = sqlite3.connect("sistema_actividades.db")
            df_stats = pd.read_sql_query("SELECT trimestre AS Trimestre, año AS Año, categoria AS Categoría FROM actividades WHERE cedula = ?", conn, params=(st.session_state["cedula"],))
            conn.close()
            
            if not df_stats.empty:
                col_st1, col_st2 = st.columns(2)
                with col_st1:
                    fig_mi_cat = px.pie(df_stats, names="Categoría", title="Mis Actividades por Categoría", hole=0.4)
                    st.plotly_chart(fig_mi_cat, use_container_width=True)
                with col_st2:
                    df_mi_trim = df_stats.groupby("Trimestre").size().reset_index(name="Cantidad")
                    fig_mi_trim = px.bar(df_mi_trim, x="Trimestre", y="Cantidad", title="Mis Actividades por Trimestre", text_auto=True)
                    st.plotly_chart(fig_mi_trim, use_container_width=True)
            else:
                st.info("Aún no hay suficientes actividades registradas para mostrar estadísticas gráficas.")

        with tab_perfil:
            st.subheader("Cambiar Contraseña")
            with st.form("form_password_prof"):
                pass_actual = st.text_input("Contraseña Actual", type="password")
                pass_nueva = st.text_input("Nueva Contraseña", type="password")
                pass_confirmar = st.text_input("Confirmar Nueva Contraseña", type="password")
                
                btn_cambiar = st.form_submit_button("Actualizar Contraseña")
                
                if btn_cambiar:
                    conn = sqlite3.connect("sistema_actividades.db")
                    cur = conn.cursor()
                    cur.execute("SELECT password FROM usuarios WHERE cedula = ?", (st.session_state["cedula"],))
                    resultado_pwd = cur.fetchone()
                    
                    if resultado_pwd:
                        pwd_db = resultado_pwd[0]
                        if pass_actual != pwd_db:
                            st.error("La contraseña actual es incorrecta.")
                        elif pass_nueva != pass_confirmar:
                            st.error("Las nuevas contraseñas no coinciden.")
                        elif len(pass_nueva) < 4:
                            st.warning("La contraseña debe tener al menos 4 caracteres.")
                        else:
                            cur.execute("UPDATE usuarios SET password = ? WHERE cedula = ?", (pass_nueva, st.session_state["cedula"]))
                            conn.commit()
                            conn.close()
                            st.success("¡Contraseña actualizada exitosamente!")
                    else:
                        st.error("No se encontró el usuario en la base de datos.")

    # ==========================================
    # MÓDULO DEL ADMINISTRADOR
    # ==========================================
    elif st.session_state["rol"] == "Administrador":
        st.title("Panel Gerencial e Institucional")
        
        tab_dashboard, tab_usuarios, tab_perfil_admin = st.tabs(["📊 Dashboard y Reportes", "👥 Gestión de Usuarios", "🔑 Mi Perfil y Contraseña"])
        
        with tab_dashboard:
            st.write("Vista global de actividades de la institución y exportación de reportes.")
            
            conn = sqlite3.connect("sistema_actividades.db")
            query = """
            SELECT a.año AS Año, a.trimestre AS Trimestre, a.cedula AS Cédula, u.nombre AS Profesor, u.rol AS Rol, a.categoria AS Categoría, a.detalles AS Detalles, a.archivo AS Evidencia
            FROM actividades a
            LEFT JOIN usuarios u ON a.cedula = u.cedula
            """
            df_admin = pd.read_sql_query(query, conn)
            conn.close()

            if df_admin.empty:
                st.info("Aún no hay actividades registradas en el sistema.")
            else:
                st.subheader("Filtros de Búsqueda")
                col_f1, col_f2, col_f3, col_f4 = st.columns(4)
                
                with col_f1:
                    anios = ["Todos"] + sorted(df_admin["Año"].unique().tolist(), reverse=True)
                    filtro_anio = st.selectbox("Filtrar por Año", anios)
                with col_f2:
                    trims = ["Todos"] + sorted(df_admin["Trimestre"].unique().tolist())
                    filtro_trim = st.selectbox("Filtrar por Trimestre", trims)
                with col_f3:
                    cats = ["Todas"] + sorted(df_admin["Categoría"].unique().tolist())
                    filtro_cat = st.selectbox("Filtrar por Categoría", cats)
                with col_f4:
                    profs = ["Todos"] + sorted(df_admin["Profesor"].dropna().unique().tolist())
                    filtro_prof = st.selectbox("Filtrar por Usuario", profs)
                    
                df_filtrado = df_admin.copy()
                if filtro_anio != "Todos":
                    df_filtrado = df_filtrado[df_filtrado["Año"] == filtro_anio]
                if filtro_trim != "Todos":
                    df_filtrado = df_filtrado[df_filtrado["Trimestre"] == filtro_trim]
                if filtro_cat != "Todas":
                    df_filtrado = df_filtrado[df_filtrado["Categoría"] == filtro_cat]
                if filtro_prof != "Todos":
                    df_filtrado = df_filtrado[df_filtrado["Profesor"] == filtro_prof]

                st.divider()
                col_m1, col_m2, col_m3, col_descarga = st.columns([1, 1, 1, 1.8])
                col_m1.metric("Actividades", len(df_filtrado))
                col_m2.metric("Participantes", df_filtrado["Profesor"].nunique())
                col_m3.metric("Evidencias", len(df_filtrado[df_filtrado["Evidencia"] != "Sin archivo"]))
                
                with col_descarga:
                    st.write("**Opciones de Exportación:**")
                    col_b1, col_b2 = st.columns(2)
                    
                    with col_b1:
                        if not df_filtrado.empty:
                            csv_data = df_filtrado.drop(columns=["Detalles"]).to_csv(index=False).encode('utf-8')
                            st.download_button(
                                label="📊 Descargar CSV",
                                data=csv_data,
                                file_name="Tabla_Resumen.csv",
                                mime="text/csv",
                                use_container_width=True
                            )
                    
                    with col_b2:
                        if st.button("📄 Ayuda PDF", use_container_width=True):
                            st.info("💡 Para guardar esta vista completa en PDF, presiona **Ctrl + P** y elige 'Guardar como PDF'.")

                    if not df_filtrado.empty:
                        nombre_archivo_zip = "Reporte_Institucional_Global.zip"
                        if filtro_prof != "Todos":
                            cedula_seleccionada = df_filtrado["Cédula"].iloc[0]
                            nombre_limpio = filtro_prof.replace(" ", "_")
                            nombre_archivo_zip = f"Reporte_{nombre_limpio}_{cedula_seleccionada}.zip"

                        lista_datos = []
                        for _, row in df_filtrado.iterrows():
                            detalle = json.loads(row["Detalles"])
                            detalle["Participante"] = row["Profesor"]
                            detalle["Rol"] = row["Rol"]
                            detalle["Cédula"] = row["Cédula"]
                            lista_datos.append(detalle)
                        df_excel = pd.DataFrame(lista_datos)
                        
                        cols = ["Participante", "Rol", "Cédula"] + [c for c in df_excel.columns if c not in ["Participante", "Rol", "Cédula"]]
                        df_excel = df_excel[cols]

                        zip_buffer = io.BytesIO()
                        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                            excel_buffer = io.BytesIO()
                            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                                df_excel.to_excel(writer, index=False, sheet_name="Reporte")
                            nombre_excel_interno = nombre_archivo_zip.replace(".zip", ".xlsx")
                            zip_file.writestr(nombre_excel_interno, excel_buffer.getvalue())
                            
                            for archivo in df_filtrado["Evidencia"]:
                                if archivo != "Sin archivo":
                                    ruta_local = os.path.join("evidencias", archivo)
                                    if os.path.exists(ruta_local):
                                        zip_file.write(ruta_local, f"Evidencias_Adjuntas/{archivo}")
                        
                        st.download_button(
                            label="📦 Descargar Excel + Evidencias (ZIP)",
                            data=zip_buffer.getvalue(),
                            file_name=nombre_archivo_zip,
                            mime="application/zip",
                            use_container_width=True,
                            type="primary"
                        )

                st.write("")
                col_g1, col_g2 = st.columns(2)
                with col_g1:
                    if not df_filtrado.empty:
                        fig_cat = px.pie(df_filtrado, names="Categoría", title="Distribución por Categoría", hole=0.4)
                        st.plotly_chart(fig_cat, use_container_width=True)
                with col_g2:
                    if not df_filtrado.empty:
                        df_trim_count = df_filtrado.groupby("Trimestre").size().reset_index(name="Cantidad")
                        fig_trim = px.bar(df_trim_count, x="Trimestre", y="Cantidad", title="Actividades por Trimestre", text_auto=True)
                        st.plotly_chart(fig_trim, use_container_width=True)

                st.subheader("Registro General (Vista Rápida)")
                df_mostrar = df_filtrado.drop(columns=["Detalles"])
                st.dataframe(df_mostrar, use_container_width=True)

        with tab_usuarios:
            st.subheader("Registrar Nuevo Usuario (Profesor o Investigador)")
            with st.form("form_nuevo_usuario", clear_on_submit=True):
                col_nu1, col_nu2 = st.columns(2)
                with col_nu1:
                    nueva_cedula = st.text_input("Cédula de Identidad")
                    nuevo_nombre = st.text_input("Nombre y Apellido")
                with col_nu2:
                    nuevo_rol = st.selectbox("Rol en la Institución", ["Profesor", "Investigador", "Administrador"])
                    nuevo_pass = st.text_input("Contraseña Temporal", value="1234", type="password")
                
                btn_crear_user = st.form_submit_button("Crear Usuario en el Sistema", type="primary")
                
                if btn_crear_user:
                    if nueva_cedula and nuevo_nombre:
                        try:
                            conn = sqlite3.connect("sistema_actividades.db")
                            cur = conn.cursor()
                            cur.execute("INSERT INTO usuarios (cedula, nombre, password, rol) VALUES (?, ?, ?, ?)",
                                        (nueva_cedula, nuevo_nombre, nuevo_pass, nuevo_rol))
                            conn.commit()
                            conn.close()
                            st.success(f"¡Usuario {nuevo_nombre} registrado con éxito como **{nuevo_rol}** (Cédula: {nueva_cedula}, Clave provisional: {nuevo_pass})!")
                        except sqlite3.IntegrityError:
                            st.error("Ya existe un usuario registrado con esa misma cédula.")
                    else:
                        st.warning("Por favor complete al menos la Cédula y el Nombre.")

            st.divider()
            st.subheader("Listado de Usuarios Registrados")
            conn = sqlite3.connect("sistema_actividades.db")
            df_users = pd.read_sql_query("SELECT cedula AS Cédula, nombre AS Nombre, rol AS Rol FROM usuarios", conn)
            conn.close()
            st.dataframe(df_users, use_container_width=True)

        with tab_perfil_admin:
            st.subheader("Cambiar Contraseña de Administrador")
            with st.form("form_password_admin"):
                pass_actual_a = st.text_input("Contraseña Actual", type="password")
                pass_nueva_a = st.text_input("Nueva Contraseña", type="password")
                pass_confirmar_a = st.text_input("Confirmar Nueva Contraseña", type="password")
                
                btn_cambiar_a = st.form_submit_button("Actualizar Contraseña")
                
                if btn_cambiar_a:
                    conn = sqlite3.connect("sistema_actividades.db")
                    cur = conn.cursor()
                    cur.execute("SELECT password FROM usuarios WHERE cedula = ?", (st.session_state["cedula"],))
                    resultado_pwd_a = cur.fetchone()
                    
                    if resultado_pwd_a:
                        pwd_db_a = resultado_pwd_a[0]
                        if pass_actual_a != pwd_db_a:
                            st.error("La contraseña actual es incorrecta.")
                        elif pass_nueva_a != pass_confirmar_a:
                            st.error("Las nuevas contraseñas no coinciden.")
                        elif len(pass_nueva_a) < 4:
                            st.warning("La contraseña debe tener al menos 4 caracteres.")
                        else:
                            cur.execute("UPDATE usuarios SET password = ? WHERE cedula = ?", (pass_nueva_a, st.session_state["cedula"]))
                            conn.commit()
                            conn.close()
                            st.success("¡Contraseña de administrador actualizada exitosamente!")
                    else:
                        st.error("No se encontró el usuario en la base de datos.")

    st.sidebar.divider()
    st.sidebar.caption("Desarrollado por: **Ing. José Antonio Pérez Bracho**")