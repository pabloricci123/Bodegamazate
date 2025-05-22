import streamlit as st
import pandas as pd
from datetime import datetime
import time
import os
import sys
import subprocess
from streamlit_option_menu import option_menu
import tempfile
from PyPDF2 import PdfReader
import pdfplumber
import openpyxl

# ================================================
# FUNCIONES COMPATIBLES CON PYINSTALLER
# ================================================

def get_file_path(filename):
    if getattr(sys, 'frozen', False):
        base_path = os.path.join(sys._MEIPASS, 'datos')
    else:
        base_path = os.path.join(os.path.dirname(__file__), 'datos')
    
    # Crear directorio si no existe
    if not os.path.exists(base_path):
        os.makedirs(base_path)
    
    return os.path.join(base_path, filename)

def cargar_datos():
    try:
        # Crear archivos si no existen
        if not os.path.exists(get_file_path('productos.csv')):
            pd.DataFrame(columns=['Producto', 'Unidad de Medida', 'Tipo de Producto', 'Stock Inicial', 'Stock Minimo']).to_csv(get_file_path('productos.csv'), index=False)
        
        if not os.path.exists(get_file_path('entradas.csv')):
            pd.DataFrame(columns=['Producto', 'Cantidad', 'Fecha']).to_csv(get_file_path('entradas.csv'), index=False)
        
        if not os.path.exists(get_file_path('despachos.csv')):
            pd.DataFrame(columns=['Fecha', 'Cliente', 'Número de Pedido', 'Producto', 'Cantidad']).to_csv(get_file_path('despachos.csv'), index=False)

        productos_df = pd.read_csv(get_file_path('productos.csv'))
        entradas_df = pd.read_csv(get_file_path('entradas.csv'))
        despachos_df = pd.read_csv(get_file_path('despachos.csv'))
        
        # Conversión segura de fechas
        for df in [entradas_df, despachos_df]:
            if 'Fecha' in df.columns:
                df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce').dt.date
        
        return productos_df, entradas_df, despachos_df
    except Exception as e:
        st.error(f"Error cargando datos: {str(e)}")
        return (
            pd.DataFrame(columns=['Producto', 'Unidad de Medida', 'Tipo de Producto', 'Stock Inicial', 'Stock Minimo']),
            pd.DataFrame(columns=['Producto', 'Cantidad', 'Fecha']),
            pd.DataFrame(columns=['Fecha', 'Cliente', 'Número de Pedido', 'Producto', 'Cantidad'])
        )

# ================================================
# FUNCIONES DE IMPORTACIÓN/EXPORTACIÓN
# ================================================

def importar_datos():
    st.subheader("Importar Datos")
    
    tab1, tab2, tab3 = st.tabs(["Desde CSV", "Desde Excel", "Desde PDF"])
    
    with tab1:
        st.write("Importar desde archivo CSV")
        csv_file = st.file_uploader("Subir archivo CSV", type=['csv'], key='csv_uploader')
        
        if csv_file is not None:
            try:
                df = pd.read_csv(csv_file)
                st.success("Archivo CSV cargado correctamente")
                st.dataframe(df.head())
                
                if st.button("Guardar como Productos"):
                    # Validar estructura básica
                    required_cols = ['Producto', 'Unidad de Medida', 'Stock Inicial']
                    if all(col in df.columns for col in required_cols):
                        df.to_csv(get_file_path('productos.csv'), index=False)
                        st.success("Datos de productos guardados correctamente!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"El archivo CSV debe contener al menos estas columnas: {', '.join(required_cols)}")
            
            except Exception as e:
                st.error(f"Error al leer el archivo CSV: {str(e)}")
    
    with tab2:
        st.write("Importar desde archivo Excel")
        excel_file = st.file_uploader("Subir archivo Excel", type=['xlsx', 'xls'], key='excel_uploader')
        
        if excel_file is not None:
            try:
                df = pd.read_excel(excel_file)
                st.success("Archivo Excel cargado correctamente")
                st.dataframe(df.head())
                
                if st.button("Guardar como Productos (Excel)"):
                    # Validar estructura básica
                    required_cols = ['Producto', 'Unidad de Medida', 'Stock Inicial']
                    if all(col in df.columns for col in required_cols):
                        df.to_csv(get_file_path('productos.csv'), index=False)
                        st.success("Datos de productos guardados correctamente!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"El archivo Excel debe contener al menos estas columnas: {', '.join(required_cols)}")
            
            except Exception as e:
                st.error(f"Error al leer el archivo Excel: {str(e)}")
    
    with tab3:
        st.write("Importar desde archivo PDF (extraer texto)")
        pdf_file = st.file_uploader("Subir archivo PDF", type=['pdf'], key='pdf_uploader')
        
        if pdf_file is not None:
            try:
                with pdfplumber.open(pdf_file) as pdf:
                    text = ""
                    for page in pdf.pages:
                        text += page.extract_text()
                
                st.success("Texto extraído del PDF:")
                st.text_area("Contenido del PDF", value=text, height=300)
                
                if st.button("Procesar PDF"):
                    # Aquí podrías añadir lógica para parsear el texto y convertirlo a DataFrame
                    st.warning("Esta función necesita implementación específica para tu formato de PDF")
            
            except Exception as e:
                st.error(f"Error al leer el archivo PDF: {str(e)}")

def exportar_datos(productos_df, entradas_df, despachos_df):
    st.subheader("Exportar Datos")
    
    col1, col2 = st.columns(2)
    
    with col1:
        formato = st.selectbox("Formato de exportación", ["CSV", "Excel"])
    
    with col2:
        datos = st.selectbox("Datos a exportar", ["Productos", "Entradas", "Despachos"])
    
    if st.button("Generar Archivo"):
        if datos == "Productos":
            df = productos_df
        elif datos == "Entradas":
            df = entradas_df
        else:
            df = despachos_df
        
        if formato == "CSV":
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Descargar CSV",
                data=csv,
                file_name=f"{datos.lower()}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime='text/csv'
            )
        else:
            excel = df.to_excel(index=False, engine='openpyxl')
            st.download_button(
                label="Descargar Excel",
                data=excel,
                file_name=f"{datos.lower()}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )

# ================================================
# FUNCIONES DE LA APLICACIÓN (MEJORADAS)
# ================================================

def mostrar_productos(productos_df):
    st.subheader("Inventario de Productos")
    
    # Mostrar métricas resumidas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Productos", len(productos_df))
    with col2:
        st.metric("Stock Total", productos_df['Stock Inicial'].sum())
    with col3:
        bajo_stock = productos_df[productos_df['Stock Inicial'] <= productos_df['Stock Minimo']]
        st.metric("Productos bajo stock", len(bajo_stock))
    
    # Mostrar tabla con todos los productos
    st.dataframe(productos_df.style.applymap(
        lambda x: 'background-color: #ffcccc' if x <= productos_df['Stock Minimo'].iloc[0] else '', 
        subset=['Stock Inicial']
    ))
    
    # Mostrar productos con stock bajo
    if not bajo_stock.empty:
        st.warning("Productos con Stock Bajo el Mínimo")
        st.dataframe(bajo_stock)

def agregar_producto(productos_df):
    st.subheader("Agregar Nuevo Producto")
    
    with st.expander("O importar desde archivo", expanded=False):
        importar_datos()
    
    with st.form("producto_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            nombre = st.text_input("Nombre del Producto*", help="Nombre descriptivo del producto")
            unidad = st.selectbox("Unidad de Medida*", ["Unidades", "Kg", "Litros", "Cajas", "Paquetes"])
            tipo = st.text_input("Tipo de Producto", help="Categoría o tipo del producto")
        
        with col2:
            stock_inicial = st.number_input("Stock Inicial*", 0, step=1, value=0)
            stock_minimo = st.number_input("Stock Mínimo*", 0, step=1, value=0)
        
        st.markdown("(*) Campos obligatorios")
        
        if st.form_submit_button("Agregar Producto"):
            if not nombre or not unidad:
                st.error("Por favor complete los campos obligatorios")
            else:
                nuevo = pd.DataFrame([{
                    "Producto": nombre,
                    "Unidad de Medida": unidad,
                    "Tipo de Producto": tipo,
                    "Stock Inicial": stock_inicial,
                    "Stock Minimo": stock_minimo
                }])
                productos_df = pd.concat([productos_df, nuevo], ignore_index=True)
                productos_df.to_csv(get_file_path('productos.csv'), index=False)
                st.success(f"Producto '{nombre}' agregado correctamente!")
                time.sleep(1)
                st.rerun()

def editar_producto(productos_df):
    st.subheader("Editar Producto Existente")
    
    seleccion = st.selectbox("Seleccionar Producto a Editar", productos_df['Producto'])
    
    if seleccion:
        data = productos_df[productos_df['Producto'] == seleccion].iloc[0]
        
        with st.form("editar_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                nuevo_nombre = st.text_input("Nombre", value=data['Producto'])
                nueva_unidad = st.selectbox(
                    "Unidad de Medida",
                    ["Unidades", "Kg", "Litros", "Cajas", "Paquetes"],
                    index=["Unidades", "Kg", "Litros", "Cajas", "Paquetes"].index(data['Unidad de Medida'])
                )
            
            with col2:
                nuevo_stock = st.number_input("Stock Actual", value=int(data['Stock Inicial']), min_value=0)
                nuevo_minimo = st.number_input("Stock Mínimo", value=int(data['Stock Minimo']), min_value=0)
            
            if st.form_submit_button("Guardar Cambios"):
                idx = productos_df[productos_df['Producto'] == seleccion].index[0]
                productos_df.at[idx, 'Producto'] = nuevo_nombre
                productos_df.at[idx, 'Unidad de Medida'] = nueva_unidad
                productos_df.at[idx, 'Stock Inicial'] = nuevo_stock
                productos_df.at[idx, 'Stock Minimo'] = nuevo_minimo
                
                productos_df.to_csv(get_file_path('productos.csv'), index=False)
                st.success(f"Producto '{nuevo_nombre}' actualizado correctamente!")
                time.sleep(1)
                st.rerun()

def registrar_entrada(productos_df, entradas_df):
    st.subheader("Registrar Entrada de Productos")
    
    with st.form("entrada_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            producto = st.selectbox("Producto*", productos_df['Producto'])
            cantidad = st.number_input("Cantidad*", 1, step=1)
        
        with col2:
            fecha = st.date_input("Fecha*", value=datetime.today())
            motivo = st.text_input("Motivo (opcional)", help="Ej: Compra, Donación, etc.")
        
        st.markdown("(*) Campos obligatorios")
        
        if st.form_submit_button("Registrar Entrada"):
            nueva_entrada = pd.DataFrame([{
                "Producto": producto,
                "Cantidad": cantidad,
                "Fecha": fecha,
                "Motivo": motivo
            }])
            
            entradas_df = pd.concat([entradas_df, nueva_entrada], ignore_index=True)
            productos_df.loc[productos_df['Producto'] == producto, 'Stock Inicial'] += cantidad
            
            entradas_df.to_csv(get_file_path('entradas.csv'), index=False)
            productos_df.to_csv(get_file_path('productos.csv'), index=False)
            
            st.success(f"Entrada de {cantidad} unidades para '{producto}' registrada correctamente!")
            time.sleep(1)
            st.rerun()

def registrar_despacho(productos_df, despachos_df):
    st.subheader("Registrar Despacho")
    
    if "despacho_data" not in st.session_state:
        st.session_state.despacho_data = {
            "cliente": "",
            "numero_pedido": "",
            "productos": [],
            "cantidades": {}
        }
    
    with st.form("despacho_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            cliente = st.text_input("Cliente*", value=st.session_state.despacho_data["cliente"])
            fecha = st.date_input("Fecha de Despacho*", value=datetime.today())
        
        with col2:
            numero_pedido = st.text_input("Número de Pedido*", value=st.session_state.despacho_data["numero_pedido"])
        
        st.divider()
        
        # Selección de productos
        productos_seleccionados = st.multiselect(
            "Productos a Despachar",
            productos_df['Producto'],
            default=st.session_state.despacho_data["productos"]
        )
        
        # Cantidades por producto
        cantidades = {}
        for p in productos_seleccionados:
            stock = productos_df.loc[productos_df['Producto'] == p, 'Stock Inicial'].values[0]
            cantidades[p] = st.number_input(
                f"Cantidad para {p} (Stock disponible: {stock})",
                1, stock, step=1,
                value=st.session_state.despacho_data["cantidades"].get(p, 1)
            )
        
        st.markdown("(*) Campos obligatorios")
        
        submitted = st.form_submit_button("Registrar Despacho")
        
        if submitted:
            # Validaciones
            if not cliente or not numero_pedido or not productos_seleccionados:
                st.error("Por favor complete todos los campos obligatorios")
                return
            
            if numero_pedido in despachos_df['Número de Pedido'].astype(str).values:
                st.warning("¡Este número de pedido ya existe!")
                return
            
            # Registrar el despacho
            nuevos_despachos = []
            for p in productos_seleccionados:
                cantidad = cantidades[p]
                nuevo_despacho = {
                    "Fecha": fecha,
                    "Cliente": cliente,
                    "Número de Pedido": numero_pedido,
                    "Producto": p,
                    "Cantidad": cantidad
                }
                nuevos_despachos.append(nuevo_despacho)
                productos_df.loc[productos_df['Producto'] == p, 'Stock Inicial'] -= cantidad
            
            despachos_df = pd.concat([despachos_df, pd.DataFrame(nuevos_despachos)], ignore_index=True)
            
            # Guardar los datos
            despachos_df.to_csv(get_file_path('despachos.csv'), index=False)
            productos_df.to_csv(get_file_path('productos.csv'), index=False)
            
            st.success("Despacho registrado exitosamente!")
            
            # Limpiar el formulario
            st.session_state.despacho_data = {
                "cliente": "",
                "numero_pedido": "",
                "productos": [],
                "cantidades": {}
            }
            time.sleep(1)
            st.rerun()

def mostrar_despachos(despachos_df):
    st.subheader("Historial de Despachos")
    
    # Filtros
    with st.expander("Filtros", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            buscador = st.text_input("Buscar por Cliente o N° Pedido")
        
        with col2:
            fecha_inicio = st.date_input("Fecha inicio", value=datetime.today().replace(day=1))
            fecha_fin = st.date_input("Fecha fin", value=datetime.today())
    
    # Aplicar filtros
    filtrado = despachos_df.copy()
    
if buscador:
    mask = (
        filtrado['Cliente'].str.contains(buscador, case=False) | 
        filtrado['Número de Pedido'].astype(str).str.contains(buscador)
    )
    filtrado = filtrado[mask]
    
    if fecha_inicio and fecha_fin:
        filtrado = filtrado[
            (pd.to_datetime(filtrado['Fecha']).dt.date >= fecha_inicio) &
            (pd.to_datetime(filtrado['Fecha']).dt.date <= fecha_fin)
        ]
    
    # Mostrar resultados
    if not filtrado.empty:
        # Resumen estadístico
        st.write(f"Mostrando {len(filtrado)} despachos entre {fecha_inicio} y {fecha_fin}")
        
        # Agrupar por cliente
        grouped = filtrado.groupby('Cliente').agg({
            'Cantidad': 'sum',
            'Número de Pedido': 'nunique'
        }).rename(columns={
            'Cantidad': 'Total Unidades',
            'Número de Pedido': 'Total Pedidos'
        })
        
        st.dataframe(grouped.sort_values('Total Unidades', ascending=False))
        
        # Mostrar tabla detallada
        st.dataframe(filtrado.sort_values('Fecha', ascending=False))
        
        # Opción de exportación
        if st.button("Exportar a Excel"):
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
                filtrado.to_excel(tmp.name, index=False)
                st.download_button(
                    label="Descargar Excel",
                    data=open(tmp.name, 'rb').read(),
                    file_name=f"despachos_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
    else:
        st.warning("No se encontraron despachos con los filtros aplicados")

# ================================================
# INTERFAZ PRINCIPAL MEJORADA
# ================================================

def pagina_principal():
    st.set_page_config(
        page_title="Gestión de Bodega", 
        layout="wide",
        page_icon="📦"
    )
    
    # Cargar datos
    productos_df, entradas_df, despachos_df = cargar_datos()
    
    # Sidebar
    with st.sidebar:
        st.image("https://via.placeholder.com/150x50?text=MiBodega", width=150)
        st.title("Menú Principal")
        
        menu = option_menu(
            None, 
            ["📦 Productos", "📥 Entradas", "📤 Despachos", "🔄 Importar/Exportar"],
            icons=None,
            default_index=0
        )
        
        st.divider()
        st.write(f"**Total Productos:** {len(productos_df)}")
        st.write(f"**Stock Total:** {productos_df['Stock Inicial'].sum()}")
        st.write(f"**Última Entrada:** {entradas_df['Fecha'].max() if not entradas_df.empty else 'N/A'}")
    
    # Página principal
    st.title("📦 Gestión de Bodega")
    
    if menu == "📦 Productos":
        tab1, tab2, tab3 = st.tabs(["Inventario", "Agregar Producto", "Editar Producto"])
        
        with tab1:
            mostrar_productos(productos_df)
        
        with tab2:
            agregar_producto(productos_df)
        
        with tab3:
            editar_producto(productos_df)
    
    elif menu == "📥 Entradas":
        registrar_entrada(productos_df, entradas_df)
    
    elif menu == "📤 Despachos":
        tab1, tab2 = st.tabs(["Registrar Despacho", "Historial"])
        
        with tab1:
            registrar_despacho(productos_df, despachos_df)
        
        with tab2:
            mostrar_despachos(despachos_df)
    
    elif menu == "🔄 Importar/Exportar":
        tab1, tab2 = st.tabs(["Importar Datos", "Exportar Datos"])
        
        with tab1:
            importar_datos()
        
        with tab2:
            exportar_datos(productos_df, entradas_df, despachos_df)

# ================================================
# PUNTO DE ENTRADA
# ================================================

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
