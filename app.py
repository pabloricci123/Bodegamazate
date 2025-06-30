
# app.py
import streamlit as st
import pandas as pd
from datetime import datetime
import time
import os
import sys
import subprocess
from streamlit_option_menu import option_menu
import tempfile
from io import BytesIO
import pdfplumber
import openpyxl

# ================================================
# CONFIGURACIÓN DE AUTENTICACIÓN
# ================================================
CONTRASENA_DUENO = "admin123"

def verificar_credenciales(rol, contrasena=None):
    if rol == "Operario":
        return True
    elif rol == "Dueño" and contrasena == CONTRASENA_DUENO:
        return True
    return False

def pagina_login():
    st.set_page_config(page_title="Login - Gestión de Bodega", layout="centered")
    st.title("📦 Acceso al Sistema de Bodega")

    rol = st.radio("Seleccione su rol:", ["Operario", "Dueño"], horizontal=True)
    contrasena = st.text_input("Contraseña:", type="password") if rol == "Dueño" else None

    if st.button("Ingresar"):
        if verificar_credenciales(rol, contrasena):
            st.session_state['autenticado'] = True
            st.session_state['rol'] = rol
            st.success(f"Bienvenido {rol}!")
            time.sleep(1)
            st.rerun()
        else:
            st.error("Credenciales incorrectas. Intente nuevamente.")

def get_file_path(filename):
    if getattr(sys, 'frozen', False):
        base_path = os.path.join(sys._MEIPASS, 'datos')
    else:
        base_path = os.path.join(os.path.dirname(__file__), 'datos')
    os.makedirs(base_path, exist_ok=True)
    return os.path.join(base_path, filename)

def cargar_datos():
    try:
        archivos = {
            'productos.csv': ['Producto', 'Unidad de Medida', 'Tipo de Producto', 'Stock Inicial', 'Stock Minimo'],
            'entradas.csv': ['Producto', 'Cantidad', 'Fecha', 'Motivo'],
            'despachos.csv': ['Fecha', 'Cliente', 'Número de Pedido', 'Producto', 'Cantidad']
        }
        for archivo, columnas in archivos.items():
            path = get_file_path(archivo)
            if not os.path.exists(path):
                pd.DataFrame(columns=columnas).to_csv(path, index=False)

        productos_df = pd.read_csv(get_file_path('productos.csv'))
        entradas_df = pd.read_csv(get_file_path('entradas.csv'))
        despachos_df = pd.read_csv(get_file_path('despachos.csv'))

        for df in [entradas_df, despachos_df]:
            if 'Fecha' in df.columns:
                df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce').dt.date
        return productos_df, entradas_df, despachos_df
    except Exception as e:
        st.error(f"Error cargando datos: {str(e)}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

def importar_datos():
    st.subheader("Importar Datos")
    tab1, tab2, tab3 = st.tabs(["Desde CSV", "Desde Excel", "Desde PDF"])

    with tab1:
        csv_file = st.file_uploader("Subir archivo CSV", type=['csv'])
        if csv_file:
            try:
                df = pd.read_csv(csv_file)
                st.dataframe(df.head())
                if st.button("Guardar como Productos (CSV)"):
                    if all(col in df.columns for col in ['Producto', 'Unidad de Medida', 'Stock Inicial']):
                        df.to_csv(get_file_path('productos.csv'), index=False)
                        st.success("Productos importados correctamente.")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Faltan columnas requeridas.")
            except Exception as e:
                st.error(f"Error al leer CSV: {e}")

    with tab2:
        excel_file = st.file_uploader("Subir archivo Excel", type=['xlsx', 'xls'])
        if excel_file:
            try:
                df = pd.read_excel(excel_file)
                st.dataframe(df.head())
                if st.button("Guardar como Productos (Excel)"):
                    if all(col in df.columns for col in ['Producto', 'Unidad de Medida', 'Stock Inicial']):
                        df.to_csv(get_file_path('productos.csv'), index=False)
                        st.success("Productos importados correctamente.")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Faltan columnas requeridas.")
            except Exception as e:
                st.error(f"Error al leer Excel: {e}")

    with tab3:
        pdf_file = st.file_uploader("Subir archivo PDF", type=['pdf'])
        if pdf_file:
            try:
                with pdfplumber.open(pdf_file) as pdf:
                    text = "".join([page.extract_text() or "" for page in pdf.pages])
                st.text_area("Contenido extraído", text, height=300)
                if st.button("Procesar PDF"):
                    st.warning("Implementar lógica para extraer datos.")
            except Exception as e:
                st.error(f"Error al procesar PDF: {e}")

def exportar_datos(productos_df, entradas_df, despachos_df):
    st.subheader("Exportar Datos")
    col1, col2 = st.columns(2)
    formato = col1.selectbox("Formato", ["CSV", "Excel"])
    tipo = col2.selectbox("Datos", ["Productos", "Entradas", "Despachos"])

    df = {"Productos": productos_df, "Entradas": entradas_df, "Despachos": despachos_df}[tipo]

    if st.button("Generar Archivo"):
        if formato == "CSV":
            st.download_button("Descargar CSV", df.to_csv(index=False).encode('utf-8'),
                               file_name=f"{tipo.lower()}_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")
        else:
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False)
            st.download_button("Descargar Excel", output.getvalue(),
                               file_name=f"{tipo.lower()}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

def pagina_principal():
    st.set_page_config(page_title="Gestión de Bodega", layout="wide", page_icon="📦")

    if 'autenticado' not in st.session_state or not st.session_state['autenticado']:
        pagina_login()
        return

    productos_df, entradas_df, despachos_df = cargar_datos()

    with st.sidebar:
        st.image("https://via.placeholder.com/150x50?text=MiBodega", width=150)
        st.title(f"Menú ({st.session_state['rol']})")
        menu_items = ["📦 Productos", "📥 Entradas", "📤 Despachos"]
        if st.session_state['rol'] == "Dueño":
            menu_items.append("🔄 Importar/Exportar")
        menu = option_menu(None, menu_items, icons=None, default_index=0)
        st.divider()
        st.write(f"**Total Productos:** {len(productos_df)}")
        st.write(f"**Stock Total:** {productos_df['Stock Inicial'].sum()}")
        st.write(f"**Última Entrada:** {entradas_df['Fecha'].max() if not entradas_df.empty else 'N/A'}")
        if st.button("🔒 Cerrar Sesión"):
            st.session_state.clear()
            st.rerun()

    st.title(f"📦 Gestión de Bodega - {st.session_state['rol']}")
    if menu == "🔄 Importar/Exportar":
        tab1, tab2 = st.tabs(["Importar Datos", "Exportar Datos"])
        with tab1:
            importar_datos()
        with tab2:
            exportar_datos(productos_df, entradas_df, despachos_df)
    else:
        st.info("Las funciones específicas para cada módulo (Productos, Entradas, Despachos) pueden implementarse aquí.")

if __name__ == "__main__":
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
        script_path = os.path.join(base_path, 'app.py')
        if os.path.exists(script_path):
            subprocess.Popen(["streamlit", "run", script_path])
        else:
            print("Error: no se encontró 'app.py'.")
    else:
        pagina_principal()
