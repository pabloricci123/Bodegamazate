import streamlit as st
import pandas as pd
from datetime import datetime
import time
import os
import sys
import subprocess
from streamlit_option_menu import option_menu

# ================================================
# FUNCIONES COMPATIBLES CON PYINSTALLER
# ================================================

def get_file_path(filename):
    if getattr(sys, 'frozen', False):
        base_path = os.path.join(sys._MEIPASS, 'datos')
    else:
        base_path = os.path.join(os.path.dirname(__file__), 'datos')
    return os.path.join(base_path, filename)

def cargar_datos():
    try:
        productos_df = pd.read_csv(get_file_path('productos.csv'))
        entradas_df = pd.read_csv(get_file_path('entradas.csv'))
        despachos_df = pd.read_csv(get_file_path('despachos.csv'))
        
        # Conversión segura de fechas
        for df in [entradas_df, despachos_df]:
            if 'Fecha' in df.columns:
                df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
        
        return productos_df, entradas_df, despachos_df
    except Exception as e:
        st.error(f"Error cargando datos: {str(e)}")
        return (
            pd.DataFrame(columns=['Producto', 'Unidad de Medida', 'Tipo de Producto', 'Stock Inicial', 'Stock Minimo']),
            pd.DataFrame(columns=['Producto', 'Cantidad', 'Fecha']),
            pd.DataFrame(columns=['Fecha', 'Cliente', 'Número de Pedido', 'Producto', 'Cantidad'])
        )

# ================================================
# FUNCIONES DE LA APLICACIÓN
# ================================================

def mostrar_productos(productos_df):
    st.subheader("Lista de Productos")
    st.dataframe(productos_df)
    stock_actual = productos_df['Stock Inicial'].sum()
    st.info(f"Stock Total: {stock_actual}")

    bajo_stock = productos_df[productos_df['Stock Inicial'] <= productos_df['Stock Minimo']]
    if not bajo_stock.empty:
        st.warning("Productos con Stock Bajo")
        st.dataframe(bajo_stock)

def agregar_producto(productos_df):
    st.subheader("Agregar Producto")
    with st.form("producto_form"):
        nombre = st.text_input("Nombre")
        unidad = st.text_input("Unidad de Medida")
        tipo = st.text_input("Tipo de Producto")
        stock_inicial = st.number_input("Stock Inicial", 0, step=1)
        stock_minimo = st.number_input("Stock Mínimo", 0, step=1)
        
        if st.form_submit_button("Agregar Producto"):
            nuevo = pd.DataFrame([{
                "Producto": nombre,
                "Unidad de Medida": unidad,
                "Tipo de Producto": tipo,
                "Stock Inicial": stock_inicial,
                "Stock Minimo": stock_minimo
            }])
            productos_df = pd.concat([productos_df, nuevo], ignore_index=True)
            productos_df.to_csv(get_file_path('productos.csv'), index=False)
            st.success(f"Producto '{nombre}' agregado.")
            time.sleep(1)
            st.rerun()

def editar_producto(productos_df):
    st.subheader("Editar Producto")
    seleccion = st.selectbox("Seleccionar Producto", productos_df['Producto'])
    
    if seleccion:
        data = productos_df[productos_df['Producto'] == seleccion].iloc[0]
        with st.form("editar_form"):
            nuevo_nombre = st.text_input("Nuevo Nombre", value=data['Producto'])
            nuevo_stock = st.number_input("Nuevo Stock", value=int(data['Stock Inicial']), min_value=0)
            nuevo_minimo = st.number_input("Nuevo Stock Mínimo", value=int(data['Stock Minimo']), min_value=0)
            
            if st.form_submit_button("Guardar Cambios"):
                idx = productos_df[productos_df['Producto'] == seleccion].index[0]
                productos_df.at[idx, 'Producto'] = nuevo_nombre
                productos_df.at[idx, 'Stock Inicial'] = nuevo_stock
                productos_df.at[idx, 'Stock Minimo'] = nuevo_minimo
                productos_df.to_csv(get_file_path('productos.csv'), index=False)
                st.success(f"Producto '{nuevo_nombre}' actualizado.")
                time.sleep(1)
                st.rerun()

def registrar_entrada(productos_df, entradas_df):
    st.subheader("Registrar Entrada")
    with st.form("entrada_form"):
        producto = st.selectbox("Producto", productos_df['Producto'])
        cantidad = st.number_input("Cantidad", 1, step=1)
        fecha = st.date_input("Fecha", value=datetime.today())
        
        if st.form_submit_button("Registrar Entrada"):
            nueva = pd.DataFrame([{
                "Producto": producto,
                "Cantidad": cantidad,
                "Fecha": fecha
            }])
            entradas_df = pd.concat([entradas_df, nueva], ignore_index=True)
            productos_df.loc[productos_df['Producto'] == producto, 'Stock Inicial'] += cantidad
            entradas_df.to_csv(get_file_path('entradas.csv'), index=False)
            productos_df.to_csv(get_file_path('productos.csv'), index=False)
            st.success(f"Entrada de {cantidad} unidades para '{producto}' registrada.")
            time.sleep(1)
            st.rerun()

def registrar_despacho(productos_df, despachos_df):
    st.subheader("Registrar Despacho")

    def limpiar_formulario():
        st.session_state.resetear_formulario = True

    if "resetear_formulario" in st.session_state and st.session_state.resetear_formulario:
        for key in ["cliente", "numero_pedido", "productos_seleccionados"]:
            if key in st.session_state:
                del st.session_state[key]
        for p in productos_df['Producto']:
            key_cant = f"cant_{p}"
            if key_cant in st.session_state:
                del st.session_state[key_cant]
        st.session_state.resetear_formulario = False
        st.session_state.clear()  # Limpiar el estado de la sesión

        # Actualizar la página reiniciando el formulario
        st.experimental_rerun()  # Reiniciar la página después de limpiar el estado

    # Asegúrate de que todas las líneas dentro de la función tengan la misma indentación.
    for key in ["cliente", "numero_pedido", "productos_seleccionados"]:
        if key not in st.session_state:
            st.session_state[key] = "" if key != "productos_seleccionados" else []

    cliente = st.text_input("Cliente", key="cliente")
    numero_pedido = st.text_input("Número de Pedido", key="numero_pedido")
    productos = st.multiselect(
        "Productos", 
        productos_df['Producto'], 
        key="productos_seleccionados"
    )

    cantidades = {}
    for p in productos:
        stock = productos_df.loc[productos_df['Producto'] == p, 'Stock Inicial'].values[0]
        cantidades[p] = st.number_input(
            f"Cantidad para {p} (Stock: {stock})", 
            1, stock, step=1, key=f"cant_{p}"
        )
    
    fecha = st.date_input("Fecha de Despacho", value=datetime.today())

    with st.form("despacho_form"):
        submitted = st.form_submit_button("Registrar Despacho")

    if submitted:
        if not cliente or not numero_pedido or not productos:
            st.error("Por favor completa todos los campos antes de registrar.")
            return

        if numero_pedido in despachos_df['Número de Pedido'].astype(str).values:
            st.warning("¡Este número de pedido ya existe!")
            return

        nuevos_despachos = []
        for p in productos:
            cantidad = cantidades[p]
            nuevo = {
                "Fecha": fecha,
                "Cliente": cliente,
                "Número de Pedido": numero_pedido,
                "Producto": p,
                "Cantidad": cantidad
            }
            nuevos_despachos.append(nuevo)
            productos_df.loc[productos_df['Producto'] == p, 'Stock Inicial'] -= cantidad

        despachos_df = pd.concat([despachos_df, pd.DataFrame(nuevos_despachos)], ignore_index=True)

        # Guardar fecha como string
        despachos_df["Fecha"] = pd.to_datetime(despachos_df["Fecha"], errors="coerce").dt.strftime('%Y-%m-%d')

        despachos_df.to_csv(get_file_path('despachos.csv'), index=False)
        productos_df.to_csv(get_file_path('productos.csv'), index=False)

        st.success("Despacho registrado exitosamente!")
        limpiar_formulario()


def mostrar_despachos(despachos_df):
    st.subheader("Registro de Despachos")

    col1, col2 = st.columns(2)

    with col1:
        buscador = st.text_input("Buscar por Número de Pedido")
    
    with col2:
        fecha_rango = st.date_input(
            "Rango de Fechas",
            value=(datetime.today(), datetime.today())
        )

    aplicar = st.button("Aplicar Filtros")

    filtrado = despachos_df.copy()

    if aplicar:
        if buscador:
            filtrado = filtrado[filtrado['Número de Pedido'].astype(str).str.contains(buscador)]
        
        if fecha_rango:
            fecha_inicio, fecha_fin = fecha_rango
            filtrado = filtrado[
                (pd.to_datetime(filtrado['Fecha'], errors="coerce").dt.date >= fecha_inicio) &
                (pd.to_datetime(filtrado['Fecha'], errors="coerce").dt.date <= fecha_fin)
            ]

    if not filtrado.empty:
        st.dataframe(filtrado)
        total = filtrado['Cantidad'].sum()
        st.info(f"{len(filtrado)} despachos encontrados. Total despachado: {total}")
    else:
        st.warning("No hay registros de despachos.")

# ================================================
# INTERFAZ PRINCIPAL
# ================================================

def pagina_principal():
    st.set_page_config(
        page_title="Gestión de Bodega", 
        layout="wide",
        page_icon="📦"
    )
    
    if not os.path.exists(os.path.dirname(get_file_path(''))):
        os.makedirs(os.path.dirname(get_file_path('')))
        st.warning("Se creó la carpeta 'datos'. Por favor coloca allí tus archivos CSV.")
        st.stop()
    
    productos_df, entradas_df, despachos_df = cargar_datos()
    
    with st.sidebar:
        st.image("https://via.placeholder.com/150x50?text=MiBodega", width=150)
        st.title("Menú Principal")
        menu = option_menu(
            None, ["Productos", "Entradas", "Despachos"],
            icons=["box", "plus-circle", "truck"],
            default_index=0
        )
    
    st.title("📦 Gestión de Bodega")
    
    if menu == "Productos":
        opcion = st.radio(
            "Operaciones", 
            ["Ver Inventario", "Agregar Producto", "Editar Producto"],
            horizontal=True
        )
        if opcion == "Ver Inventario":
            mostrar_productos(productos_df)
        elif opcion == "Agregar Producto":
            agregar_producto(productos_df)
        elif opcion == "Editar Producto":
            editar_producto(productos_df)
    
    elif menu == "Entradas":
        registrar_entrada(productos_df, entradas_df)
    
    elif menu == "Despachos":
        opcion = st.radio(
            "Operaciones", 
            ["Registrar Despacho", "Historial de Despachos"],
            horizontal=True
        )
        if opcion == "Registrar Despacho":
            registrar_despacho(productos_df, despachos_df)
        else:
            mostrar_despachos(despachos_df)

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
