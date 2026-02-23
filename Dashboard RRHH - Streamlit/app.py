import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# Configuración de la página
st.set_page_config(
    page_title="HR Analytics Pro",
    page_icon="👥",
    layout="wide",
)

# --- ESTILOS CSS PERSONALIZADOS ---
st.markdown("""
    <style>
    /* Reducir espacio superior del Sidebar */
    [data-testid="stSidebarContent"] {
        padding-top: 0rem !important;
    }
    /* Estilizar el título de filtros para que se vea más grande y jerárquico */
    .filter-header {
        font-size: 2rem !important;
        font-weight: 800;
        margin-bottom: 0px;
        padding-top: 0px;
        color: #1f2937;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CARGA Y LIMPIEZA DE DATOS ---
@st.cache_data
def get_clean_data():
    df = pd.read_csv('employees.csv')
    df['Department'] = df['Department'].str.strip().str.title()
    df['Position'] = df['Position'].str.strip().str.title()
    df['Salary'] = pd.to_numeric(df['Salary'], errors='coerce')
    df['Salary'] = df.groupby('Department')['Salary'].transform(lambda x: x.fillna(x.median()))
    mask = df['YearsAtCompany'] > df['Age']
    df.loc[mask, 'YearsAtCompany'] = df.loc[mask, 'Age'] - 18
    
    # Nueva columna estratégica: Rango de Edad
    bins = [0, 30, 45, 100]
    labels = ['Joven (<30)', 'Media (30-45)', 'Senior (>45)']
    df['AgeRange'] = pd.cut(df['Age'], bins=bins, labels=labels)
    
    return df

df = get_clean_data()

# --- SIDEBAR: FILTROS MEJORADOS ---
st.sidebar.markdown('<p class="filter-header">🔍 Filtros de Control</p>', unsafe_allow_html=True)
st.sidebar.markdown("---")

# 1. Filtro por Nombre (El primer filtro, búsqueda textual)
nombre_busqueda = st.sidebar.text_input("Búsqueda por Nombre:", placeholder="Ej. John Smith")

# 2. Filtro de Departamento
selected_depts = st.sidebar.multiselect(
    "Filtrar por Departamento:",
    options=sorted(df["Department"].unique()),
    help="Si dejas este campo vacío, se mostrarán todos los departamentos."
)

# 3. Filtro de Género
selected_genders = st.sidebar.multiselect(
    "Filtrar por Género:",
    options=sorted(df["Gender"].dropna().unique()),
    help="Si dejas este campo vacío, se mostrarán todos los géneros."
)

# 4. Filtro de Salario
st.sidebar.subheader("Rango Salarial")
s_min_data = int(df["Salary"].min())
s_max_data = int(df["Salary"].max())

col_s_min, col_s_max = st.sidebar.columns(2)
with col_s_min:
    val_s_min = st.number_input("Mínimo:", min_value=s_min_data, max_value=s_max_data, value=s_min_data, key="sal_min")
with col_s_max:
    val_s_max = st.number_input("Máximo:", min_value=s_min_data, max_value=s_max_data, value=s_max_data, key="sal_max")

rango_salario = st.sidebar.slider(
    "Ajuste visual de Salario:",
    min_value=s_min_data,
    max_value=s_max_data,
    value=(val_s_min, val_s_max),
    label_visibility="collapsed"
)

# 5. Filtro de Edad
st.sidebar.subheader("Rango de Edad")
a_min_data = int(df["Age"].min())
a_max_data = int(df["Age"].max())

col_a_min, col_a_max = st.sidebar.columns(2)
with col_a_min:
    val_a_min = st.number_input("Mín. Edad:", min_value=a_min_data, max_value=a_max_data, value=a_min_data, key="age_min")
with col_a_max:
    val_a_max = st.number_input("Máx. Edad:", min_value=a_min_data, max_value=a_max_data, value=a_max_data, key="age_max")

rango_edad = st.sidebar.slider(
    "Ajuste visual de Edad:",
    min_value=a_min_data,
    max_value=a_max_data,
    value=(val_a_min, val_a_max),
    label_visibility="collapsed"
)

# 6. Filtro de Puntuación de Desempeño
st.sidebar.subheader("Score de Desempeño")
p_min_data = int(df["PerformanceScore"].min())
p_max_data = int(df["PerformanceScore"].max())

col_p_min, col_p_max = st.sidebar.columns(2)
with col_p_min:
    val_p_min = st.number_input("Mín. Score:", min_value=p_min_data, max_value=p_max_data, value=p_min_data, key="perf_min")
with col_p_max:
    val_p_max = st.number_input("Máx. Score:", min_value=p_min_data, max_value=p_max_data, value=p_max_data, key="perf_max")

rango_perf = st.sidebar.slider(
    "Ajuste visual de Score:",
    min_value=p_min_data,
    max_value=p_max_data,
    value=(val_p_min, val_p_max),
    label_visibility="collapsed"
)

# --- APLICACIÓN DE FILTROS ---
final_depts = selected_depts if selected_depts else df["Department"].unique()
final_genders = selected_genders if selected_genders else df["Gender"].unique()

df_selection = df[
    (df["Department"].isin(final_depts)) & 
    (df["Gender"].isin(final_genders)) &
    (df["Salary"].between(rango_salario[0], rango_salario[1])) &
    (df["Age"].between(rango_edad[0], rango_edad[1])) &
    (df["PerformanceScore"].between(rango_perf[0], rango_perf[1]))
]

# Aplicar búsqueda textual de nombre si el usuario ingresó algo
if nombre_busqueda:
    df_selection = df_selection[df_selection["Name"].str.contains(nombre_busqueda, case=False, na=False)]

# --- CABECERA ---
st.title("📊 Dashboard Avanzado de Datos de RRHH")
st.markdown(f"Análisis detallado de la fuerza laboral | **{len(df_selection)}** empleados seleccionados")

# --- TABS PARA SEGMENTACIÓN ---
tab_general, tab_rendimiento, tab_diversidad = st.tabs([
    "📊 Visión General", 
    "📈 Rendimiento y Salarios", 
    "⚖️ Diversidad e Inclusión"
])

def get_plotly_title(title, subtitle):
    return f"<b>{title}</b><br><sup><i>{subtitle}</i></sup>"

# --- TAB 1: VISIÓN GENERAL ---
with tab_general:
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Empleados", len(df_selection))
    k2.metric("Salario Promedio", f"${df_selection['Salary'].mean():,.0f}" if not df_selection.empty else "$0")
    k3.metric("Edad Promedio", f"{df_selection['Age'].mean():.1f} años" if not df_selection.empty else "0 años")
    k4.metric("Antigüedad Prom.", f"{df_selection['YearsAtCompany'].mean():.1f} años" if not df_selection.empty else "0 años")

    st.markdown("---")
    
    if not df_selection.empty:
        dept_counts = df_selection.groupby('Department').size().reset_index(name='Empleados')
        fig_dept = px.bar(
            dept_counts,
            x="Department", y="Empleados", 
            title=get_plotly_title("Empleados por Departamento", "Distribución del total de colaboradores en las áreas clave."),
            text_auto=True, color="Department",
            labels={"Department": "Departamento", "Empleados": "Empleados"},
            template="plotly_white"
        )
        fig_dept.update_layout(
            showlegend=True,
            legend_title_text="Departamento",
            yaxis={'visible': False, 'showticklabels': False},
            xaxis={'showgrid': False}
        )
        st.plotly_chart(fig_dept, use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)

        df_counts = df_selection.copy()
        counts = df_counts.groupby(['Department', 'Position']).size().reset_index(name='count')
        df_counts = df_counts.merge(counts, on=['Department', 'Position'])
        df_counts['Label'] = df_counts['Position'] + " (" + df_counts['count'].astype(str) + ")"

        fig_pos = px.treemap(
            df_counts, path=['Department', 'Label'], 
            title=get_plotly_title("Estructura Jerárquica", "Desglose por departamento y posiciones para visualizar la organización."),
            template="plotly_white",
            color="Department"
        )
        st.plotly_chart(fig_pos, use_container_width=True)
    else:
        st.warning("No hay datos para mostrar con los filtros seleccionados.")

# --- TAB 2: RENDIMIENTO Y SALARIOS ---
with tab_rendimiento:
    if not df_selection.empty:
        c1, c2 = st.columns(2)
        with c1:
            fig_sal = px.histogram(
                df_selection, x="Salary", nbins=15, 
                title=get_plotly_title("Distribución de Salarios", "Frecuencia de rangos salariales en la plantilla."),
                color_discrete_sequence=['#2ecc71'],
                labels={"Salary": "Salario", "count": "Empleados"}, 
                template="plotly_white"
            )
            fig_sal.update_layout(yaxis_title="Empleados", xaxis_title="Salario")
            st.plotly_chart(fig_sal, use_container_width=True)
            
        with c2:
            fig_perf = px.scatter(
                df_selection, x="YearsAtCompany", y="PerformanceScore",
                size="Salary", color="Department", hover_name="Name",
                title=get_plotly_title("Relación entre Desempeño y Antigüedad", "El tamaño de la burbuja representa la magnitud del salario."),
                labels={"PerformanceScore": "Score de Desempeño", "YearsAtCompany": "Años"},
                template="plotly_white"
            )
            st.plotly_chart(fig_perf, use_container_width=True)
    else:
        st.warning("No hay datos para mostrar con los filtros seleccionados.")

# --- TAB 3: DIVERSIDAD E INCLUSIÓN ---
with tab_diversidad:
    if not df_selection.empty:
        c1, c2 = st.columns(2)
        with c1:
            fig_gender = px.pie(
                df_selection, names='Gender', 
                title=get_plotly_title("Composición por Género", "Proporción de hombres y mujeres en la fuerza laboral."),
                hole=0.4, color_discrete_sequence=['#3498db', '#e74c3c']
            )
            st.plotly_chart(fig_gender, use_container_width=True)
        with c2:
            age_dist = df_selection.groupby('AgeRange', observed=True).size().reset_index(name='Empleados')
            fig_age = px.bar(
                age_dist, x='AgeRange', y='Empleados',
                title=get_plotly_title("Distribución por Rango de Edad", "Segmentación generacional para identificar la madurez de la fuerza laboral."),
                color='AgeRange', text_auto=True,
                template="plotly_white",
                labels={'AgeRange': 'Rango de Edad'}
            )
            fig_age.update_layout(xaxis={'showgrid': False}, yaxis={'showgrid': False})
            st.plotly_chart(fig_age, use_container_width=True)

        st.markdown("---")
        pay_gap = df_selection.groupby('Gender')['Salary'].mean().reset_index()
        fig_gap = px.bar(
            pay_gap, x='Gender', y='Salary', 
            title=get_plotly_title("Salario Promedio por Género", "Comparativa de ingresos promedio para analizar la equidad salarial."),
            color='Gender', text_auto='.2s',
            labels={"Gender": "Género", "Salary": "Salario"},
            template="plotly_white"
        )
        fig_gap.update_layout(yaxis_title="Salario", xaxis_title="Género", xaxis={'showgrid': False}, yaxis={'showgrid': False})
        st.plotly_chart(fig_gap, use_container_width=True)
    else:
        st.warning("No hay datos para mostrar con los filtros seleccionados.")

# --- TABLA DE DATOS FINAL ---
with st.expander("🔍 Ver detalle de empleados filtrados"):
    if not df_selection.empty:
        st.dataframe(df_selection.sort_values(by="PerformanceScore", ascending=False), use_container_width=True)
    else:
        st.write("Ningún empleado coincide con esos parámetros.")
