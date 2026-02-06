# Streamlit-Airbnb

# 🏙️ Barcelona Airbnb: Monitor de Legalitat

Este proyecto es un dashboard interactivo desarrollado con **Streamlit** diseñado para auditar la legalidad de los anuncios de Airbnb en Barcelona. La herramienta cruza datos de anuncios públicos con registros de licencias para identificar posibles fraudes, licencias falsas y alojamientos no registrados (NRA).

👉 **Puedes ver la app en vivo aquí:** [Barcelona Airbnb Monitor](https://app-airbnb-f5vtgprw2q3srzcacky42u.streamlit.app/)

## 🚀 Funcionalidades

- **Inspector de Licencias:** Búsqueda directa por URL o ID de Airbnb para verificar el estado legal de un inmueble específico.
- **Mapa Interactivo:** Visualización geográfica de los alojamientos clasificados por estado (Verificado, Ilegal/Falso, NRA, Exento).
- **Análisis por Barrios:** Comparativa de los distritos con mayor tasa de irregularidades y distribución de precios.
- **Monitor de Anfitriones (Hosts):** Identificación de "malos actores" o perfiles con múltiples anuncios sospechosos.
- **Filtros Avanzados:** Segmentación por tipo de propiedad, rango de precios y noches mínimas de estancia.

## 🛠️ Tecnologías utilizadas

- **Python** (Pandas, Numpy, Re)
- **Streamlit** (Framework de la aplicación)
- **Plotly Express** (Visualizaciones dinámicas y mapas)
- **Dataset:** Datos procesados de Airbnb Barcelona cruzados con el Registro de Turismo.

## 📊 Clasificación de Licencias
El sistema clasifica cada anuncio en 5 categorías:
1. ✅ **Verificado:** Licencia válida y comprobada.
2. 🚫 **Il·legal/Fals:** Licencia que no existe o es fraudulenta.
3. ⚠️ **NRA:** No consta en el Registro de Turismo de la Generalitat.
4. 🔵 **Sense Llicència / Exempt:** Situaciones especiales o alquileres de larga estancia.
5. ⚪ **Desconegut:** Datos insuficientes para verificación.

## 💻 Instalación Local

1. Clona el repositorio:
   ```bash
   git clone [https://github.com/tu-usuario/nombre-repo.git](https://github.com/tu-usuario/nombre-repo.git)
