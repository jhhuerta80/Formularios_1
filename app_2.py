import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

# --- 1. CONFIGURACIÓN Y BASE DE DATOS ---
st.set_page_config(page_title="DataMaster Pro", layout="wide")

# Conectamos a la base de datos v2
conn = sqlite3.connect('empresa_v2.db', check_same_thread=False)
c = conn.cursor()

# Creamos la tabla con más campos: ID, Fecha, Producto, Cantidad, Precio y Teléfono
c.execute('''CREATE TABLE IF NOT EXISTS ventas 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, 
              fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
              producto TEXT, 
              cantidad INTEGER, 
              precio REAL, 
              telefono TEXT)''')
conn.commit()

# --- 2. INTERFAZ DE NAVEGACIÓN (TABS) ---
# Esto crea las pestañas en la parte superior
tab1, tab2, tab3 = st.tabs(["📝 Registro de Ventas", "🔍 Buscador Inteligente", "📊 Dashboard y Reportes"])

# --- TAB 1: FORMULARIO CON VALIDACIÓN ---
with tab1:
    st.header("Añadir Nueva Venta ")
    with st.form("registro_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            prod = st.text_input("Ingres el Nombre del Producto")
            cant = st.number_input("Cantidad", min_value=1, step=1)
        with col2:
            prec = st.number_input("Ingresa el Precio Unitario", min_value=0.0, step=0.1)
            tel = st.text_input("Teléfono del Cliente (10 dígitos exactos)")
        
        submit = st.form_submit_button("Registrar Venta")

    if submit:
        # LÓGICA DE VALIDACIÓN (El "escudo" que platicamos)
        tel_limpio = tel.replace(" ", "").replace("-", "") 
        
        if len(prod) < 2:
            st.error("❌ El nombre del producto es demasiado corto.")
        elif not tel_limpio.isdigit() or len(tel_limpio) != 10:
            st.error("❌ El teléfono debe tener exactamente 10 números.")
        else:
            # Si pasa la validación, usamos los "?" para evitar inyección SQL
            c.execute('INSERT INTO ventas (producto, cantidad, precio, telefono) VALUES (?,?,?,?)', 
                      (prod, cant, prec, tel_limpio))
            conn.commit()
            st.success(f"✅ ¡Venta de {prod} registrada con éxito!")

# --- TAB 2: BUSCADOR INTELIGENTE ---
with tab2:
    st.header("Filtros de Búsqueda")
    # Leemos la tabla actualizada
    df = pd.read_sql('SELECT * FROM ventas', conn)
    
    busqueda = st.text_input("Buscar por nombre de producto o teléfono")
    
    if busqueda:
        # Buscamos coincidencias en producto O en teléfono
        df_filtrado = df[df['producto'].str.contains(busqueda, case=False) | df['telefono'].str.contains(busqueda)]
        st.dataframe(df_filtrado, use_container_width=True)
    else:
        st.dataframe(df, use_container_width=True)

# --- TAB 3: DASHBOARD Y EXPORTACIÓN ---
with tab3:
    st.header("Análisis de Negocio")
    
    # Recargamos DF para asegurar que tenemos los últimos datos
    df = pd.read_sql('SELECT * FROM ventas', conn)

    if not df.empty:
        # Cálculo de métricas en memoria con Pandas
        df['Total'] = df['cantidad'] * df['precio']
        total_ventas = df['Total'].sum()
        total_items = df['cantidad'].sum()
        
        # Mostrar métricas llamativas
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Ingresos Totales", f"${total_ventas:,.2f}")
        col_m2.metric("Productos Vendidos", total_items)
        col_m3.metric("Tickets Generados", len(df))

        # GRÁFICO INTERACTIVO (Plotly)
        st.subheader("Ingresos por Producto")
        # Agrupamos por producto para el gráfico
        df_resumen = df.groupby('producto')['Total'].sum().reset_index()
        fig = px.bar(df_resumen, x="producto", y="Total", 
                     color="producto", 
                     labels={'Total':'Ventas ($)', 'producto':'Producto'},
                     template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

        # EXPORTACIÓN A EXCEL
        st.divider()
        st.subheader("Exportar Datos")
        df.to_excel("reporte_gerencial.xlsx", index=False)
        with open("reporte_gerencial.xlsx", "rb") as f:
            st.download_button("📥 Descargar Reporte Completo (Excel)", f, "reporte_gerencial.xlsx")
    else:
        st.info("Aún no hay datos. Registra una venta en la primera pestaña para ver las gráficas.")