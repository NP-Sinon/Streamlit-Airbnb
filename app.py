import re
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(
    page_title="Monitor Airbnb Barcelona",
    page_icon="🕵️‍♀️",
    layout="wide"
)

COLOR_MAP = {
    "Il·legal/Fals": "#EF553B",
    "Verificat": "#00CC96",
    "Sense Llicència / Exempt": "#636EFA",
    "NRA": "#FF9900",
    "Desconegut": "#B6B6B6",
}

LICENSE_ORDER = ["Verificat", "Il·legal/Fals", "NRA", "Sense Llicència / Exempt", "Desconegut"]

@st.cache_data(show_spinner=False)
def load_data(path: str = "airbnb_barcelona_final.csv") -> pd.DataFrame:
    try:
        df = pd.read_csv(path)
    except FileNotFoundError:
        return pd.DataFrame()

    needed_cols = [
        "id","name","host_id","host_name",
        "neighbourhood_cleansed","latitude","longitude",
        "property_type","room_type","price_cleaned",
        "minimum_nights","license","License_Verification","listing_url",
        "license_stripped","Cleaned_license","License_Status","License_Base"
    ]
    for c in needed_cols:
        if c not in df.columns:
            df[c] = np.nan

    if "License_Status" in df.columns:
        mask_nra = df["License_Status"] == "NRA"
        df.loc[mask_nra, "License_Verification"] = "NRA"

    df["License_Verification"] = df["License_Verification"].fillna("Unknown")
    
    df["is_illegal"] = (df["License_Verification"] == "Ilegal/Fake").astype(int)
    df["is_nra"] = (df["License_Verification"] == "NRA").astype(int)
    df["is_verified"] = (df["License_Verification"] == "Verified").astype(int)

    translation_map = {
        "Ilegal/Fake": "Il·legal/Fals",
        "Verified": "Verificat",
        "No License / Exempt": "Sense Llicència / Exempt",
        "NRA": "NRA",
        "Unknown": "Desconegut"
    }
    df["License_Verification"] = df["License_Verification"].map(translation_map).fillna("Desconegut")

    df.loc[~df["License_Verification"].isin(COLOR_MAP.keys()), "License_Verification"] = "Desconegut"

    df["neighbourhood_cleansed"] = df["neighbourhood_cleansed"].fillna("Desconegut")
    df["property_type"] = df["property_type"].fillna("Desconegut")
    df["room_type"] = df["room_type"].fillna("Desconegut")
    df["host_name"] = df["host_name"].fillna("Desconegut")

    df["price_cleaned"] = pd.to_numeric(df["price_cleaned"], errors="coerce")
    df["minimum_nights"] = pd.to_numeric(df["minimum_nights"], errors="coerce")
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")

    df["id"] = pd.to_numeric(df["id"], errors="coerce").astype("Int64")
    df["host_id"] = pd.to_numeric(df["host_id"], errors="coerce").astype("Int64")

    if df["price_cleaned"].notna().any():
        upper_limit = df["price_cleaned"].quantile(0.99)
        df["price_for_viz"] = df["price_cleaned"].clip(lower=0, upper=upper_limit)
    else:
        df["price_for_viz"] = df["price_cleaned"]

    return df


def extract_room_id(url_or_id: str):
    if url_or_id is None:
        return None
    s = str(url_or_id).strip()
    if not s:
        return None

    if re.fullmatch(r"\d+", s):
        return int(s)

    m = re.search(r"rooms/(\d+)", s)
    if m:
        return int(m.group(1))

    return None


def apply_filters(df: pd.DataFrame,
                  barrios, room_types, property_types, verifs,
                  price_range, nights_range) -> pd.DataFrame:

    out = df.copy()

    if barrios:
        out = out[out["neighbourhood_cleansed"].isin(barrios)]
    if room_types:
        out = out[out["room_type"].isin(room_types)]
    if property_types:
        out = out[out["property_type"].isin(property_types)]
    if verifs:
        out = out[out["License_Verification"].isin(verifs)]

    if price_range is not None:
        mask = out["price_cleaned"].between(price_range[0], price_range[1], inclusive="both")
        out = out[mask.fillna(False)]
        
    if nights_range is not None:
        mask = out["minimum_nights"].between(nights_range[0], nights_range[1], inclusive="both")
        out = out[mask.fillna(False)]

    return out


def metrics_block(df_all: pd.DataFrame, df_f: pd.DataFrame):
    total = len(df_f)
    
    ilegal = int((df_f["License_Verification"] == "Il·legal/Fals").sum())
    nra = int((df_f["License_Verification"] == "NRA").sum())
    verified = int((df_f["License_Verification"] == "Verificat").sum())
    exempt = int((df_f["License_Verification"] == "Sense Llicència / Exempt").sum())
    
    pct_ilegal = (ilegal / total * 100) if total else 0.0

    total_all = len(df_all)
    ilegal_all = int((df_all["License_Verification"] == "Il·legal/Fals").sum())
    pct_ilegal_all = (ilegal_all / total_all * 100) if total_all else 0.0

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Allotjaments (filtre)", f"{total:,}")
    c2.metric("Il·legal / Fals", f"{ilegal:,}", delta=f"{pct_ilegal - pct_ilegal_all:+.1f} pp vs mitjana", delta_color="inverse")
    c3.metric("NRA (No Registrat)", f"{nra:,}", help="No consta al Registre de Turisme (NRA)")
    c4.metric("Verificats", f"{verified:,}")
    c5.metric("Exents / Sense llic.", f"{exempt:,}")

    st.caption(f"Mitjana global d'Il·legals/Falsos: **{pct_ilegal_all:.1f}%** (sobre {total_all:,} anuncis totals).")

st.title("🏙️ Barcelona Airbnb: Monitor de Legalitat")
st.markdown(
    "Quadre de comandament interactiu per **explorar llicències**, detectar **possibles il·legals (i NRA)** i entendre "
    "la distribució per **barris**, **amfitrions** i **preus**."
)

df = load_data()
if df.empty:
    st.error("⚠️ No s'ha trobat l'arxiu `airbnb_barcelona_final.csv` o està buit.")
    st.stop()

st.sidebar.header("🕵️‍♀️ Inspector de Llicències")
st.sidebar.markdown("Introdueix una **URL** o un **ID** d'Airbnb per cercar-lo.")

with st.sidebar.form("inspector_form"):
    query_input = st.text_input("URL o ID", placeholder="https://www.airbnb.com/rooms/18674 o 18674")
    search_submitted = st.form_submit_button("Cercar")

if search_submitted and query_input:
    room_id = extract_room_id(query_input)
    match = pd.DataFrame()
    
    match = df[df["listing_url"] == query_input]
    if match.empty and room_id is not None:
        match = df[df["id"] == room_id]

    st.sidebar.markdown("---")
    if not match.empty:
        row = match.iloc[0]
        estado = row["License_Verification"]
        barrio = row["neighbourhood_cleansed"]

        df_b = df[df["neighbourhood_cleansed"] == barrio]
        pct_b = (df_b["License_Verification"].eq("Il·legal/Fals").mean() * 100) if len(df_b) else 0.0
        pct_all = df["License_Verification"].eq("Il·legal/Fals").mean() * 100

        st.sidebar.write(f"**Allotjament:** {row.get('name','(sense nom)')}")
        st.sidebar.write(f"**Barri:** {barrio}")
        st.sidebar.write(f"**Tipus:** {row.get('room_type','?')} · {row.get('property_type','?')}")
        st.sidebar.write(f"**Preu:** {row.get('price_cleaned',np.nan):.0f} € · **Nits mín.:** {row.get('minimum_nights',np.nan)}")
        st.sidebar.write(f"**URL:** {row.get('listing_url','')}")

        if estado == "Verificat":
            st.sidebar.success(f"✅ **LLICÈNCIA VERIFICADA**\n\nLlicència: {row.get('license','')}")
        elif estado == "Il·legal/Fals":
            st.sidebar.error("🚫 **POSSIBLE IL·LEGAL / FRAU**\n\nNo apareix com a llicència vàlida al creuament.")
        elif estado == "NRA":
            st.sidebar.error("⚠️ **NRA (NO REGISTRAT)**\n\nNo consta registre a l'Ajuntament.")
        elif estado == "Sense Llicència / Exempt":
            st.sidebar.warning("⚠️ **EXENT / SENSE LLICÈNCIA**\n\nRevisar normativa (ex. estades llargues).")
        else:
            st.sidebar.info(f"ℹ️ **Estat:** {estado}")

        st.sidebar.caption(f"% Il·legal al seu barri: **{pct_b:.1f}%** (mitjana ciutat: **{pct_all:.1f}%**)")
    else:
        st.sidebar.warning("No trobat al dataset.")

st.sidebar.markdown("---")
st.sidebar.header("🎛️ Filtres globals")

barrios_all = sorted(df["neighbourhood_cleansed"].dropna().unique().tolist())
room_types_all = sorted(df["room_type"].dropna().unique().tolist())
property_types_all = sorted(df["property_type"].dropna().unique().tolist())

verifs_all = [v for v in LICENSE_ORDER if v in df["License_Verification"].unique()]

barrios = st.sidebar.multiselect("Barris", options=barrios_all, default=[])
room_types = st.sidebar.multiselect("Tipus d'habitació", options=room_types_all, default=[])
property_types = st.sidebar.multiselect("Tipus de propietat", options=property_types_all, default=[])
verifs = st.sidebar.multiselect("Estat de llicència", options=verifs_all, default=verifs_all)

price_min = float(np.nanmin(df["price_cleaned"])) if df["price_cleaned"].notna().any() else 0.0
price_max = float(np.nanmax(df["price_cleaned"])) if df["price_cleaned"].notna().any() else 1000.0
p1, p99 = df["price_cleaned"].quantile([0.01, 0.99]).values if df["price_cleaned"].notna().any() else (0, 1000)

price_range = st.sidebar.slider(
    "Preu (€)",
    min_value=float(max(0, price_min)),
    max_value=float(price_max if np.isfinite(price_max) else 1000.0),
    value=(float(max(0, p1)), float(p99)),
    step=1.0
)

n_min = int(np.nanmin(df["minimum_nights"])) if df["minimum_nights"].notna().any() else 1
n_max = int(np.nanmax(df["minimum_nights"])) if df["minimum_nights"].notna().any() else 365
nights_range = st.sidebar.slider("Nits mínimes", min_value=int(n_min), max_value=int(n_max), value=(int(n_min), int(min(n_max, 31))))

st.sidebar.markdown("---")
st.sidebar.info("Font: Dataset processat + creuament amb Registre.")

df_f = apply_filters(df, barrios, room_types, property_types, verifs, price_range, nights_range)

metrics_block(df, df_f)

tab_overview, tab_map, tab_neigh, tab_hosts, tab_prices, tab_explorer = st.tabs(
    ["📌 Resum", "🗺️ Mapa", "🏘️ Barris", "👤 Amfitrions", "💶 Preus", "🧾 Explorador"]
)

with tab_overview:
    st.subheader("Distribució general")
    c1, c2 = st.columns([1, 1])

    with c1:
        dist = (df_f["License_Verification"]
                .value_counts(dropna=False)
                .reindex(LICENSE_ORDER)
                .dropna()
                .reset_index())
        dist.columns = ["License_Verification", "count"]
        
        fig = px.pie(
            dist, values="count", names="License_Verification", hole=0.55,
            color="License_Verification", color_discrete_map=COLOR_MAP
        )
        fig.update_layout(height=380, margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        tmp = (df_f.groupby(["room_type", "License_Verification"])
               .size().reset_index(name="n"))
        total_rt = tmp.groupby("room_type")["n"].transform("sum")
        tmp["pct"] = tmp["n"] / total_rt * 100

        fig2 = px.bar(
            tmp, x="pct", y="room_type", color="License_Verification",
            barmode="stack", orientation="h",
            color_discrete_map=COLOR_MAP,
            category_orders={"License_Verification": LICENSE_ORDER}
        )
        fig2.update_layout(height=380, margin=dict(l=10, r=10, t=30, b=10))
        fig2.update_xaxes(title="% dins del tipus d'habitació")
        fig2.update_yaxes(title="")
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Nits mínimes (Distribució)")
    df_n = df_f[df_f["minimum_nights"].notna()].copy()
    if len(df_n):
        df_n["min_nights_bucket"] = pd.cut(
            df_n["minimum_nights"],
            bins=[0, 1, 2, 3, 7, 14, 30, 60, 3650],
            labels=["1", "2", "3", "4-7", "8-14", "15-30", "31-60", "61+"],
            include_lowest=True
        )
        tmp = df_n.groupby(["min_nights_bucket", "License_Verification"]).size().reset_index(name="n")
        fig3 = px.bar(
            tmp, x="min_nights_bucket", y="n", color="License_Verification",
            color_discrete_map=COLOR_MAP,
            category_orders={"License_Verification": LICENSE_ORDER}
        )
        fig3.update_layout(height=360, margin=dict(l=10, r=10, t=30, b=10))
        fig3.update_xaxes(title="Nits mínimes (agrupat)")
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("No hi ha dades suficients de `minimum_nights`.")

with tab_map:
    st.subheader("Mapa interactiu")

    c1, c2, c3 = st.columns([1.2, 1, 1])
    with c1:
        mode = st.radio("Mode", ["Punts", "Densitat (heatmap)"], horizontal=True)
    with c2:
        max_samples = min(20000, len(df_f))
        sample = st.slider("Mostreig (màx 20k)", 1000, max(1001, max_samples), value=min(10000, max_samples), step=1000)
    with c3:
        zoom = st.slider("Zoom", 9, 14, 11)

    df_map = df_f.dropna(subset=["latitude", "longitude"]).copy()
    if len(df_map) > sample:
        df_map = df_map.sample(sample, random_state=42)

    if df_map.empty:
        st.warning("No hi ha punts amb coordenades vàlides.")
    else:
        if mode == "Punts":
            figm = px.scatter_mapbox(
                df_map,
                lat="latitude",
                lon="longitude",
                color="License_Verification",
                color_discrete_map=COLOR_MAP,
                hover_name="name",
                hover_data={
                    "price_cleaned": True,
                    "minimum_nights": True,
                    "neighbourhood_cleansed": True,
                    "listing_url": True,
                    "latitude": False, "longitude": False
                },
                zoom=zoom,
                mapbox_style="carto-positron",
                height=600
            )
        else:
            df_heat = df_map.copy()
            df_heat["weight"] = np.where(df_heat["License_Verification"].isin(["Il·legal/Fals", "NRA"]), 1.0, 0.2)
            figm = px.density_mapbox(
                df_heat,
                lat="latitude",
                lon="longitude",
                z="weight",
                radius=18,
                zoom=zoom,
                mapbox_style="carto-positron",
                height=600
            )
        figm.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
        st.plotly_chart(figm, use_container_width=True)

with tab_neigh:
    st.subheader("Anàlisi per barri")

    g = (df_f.groupby("neighbourhood_cleansed")
         .agg(
             listings=("id", "count"),
             ilegal=("is_illegal", "sum"),
             nra=("is_nra", "sum"),
             verified=("is_verified", "sum"),
             median_price=("price_cleaned", "median")
         )
         .reset_index())
    
    g["suspicious_count"] = g["ilegal"] + g["nra"]
    g["pct_suspicious"] = np.where(g["listings"] > 0, g["suspicious_count"] / g["listings"] * 100, 0)

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("##### Barris amb més **Sospitosos (Il·legal + NRA)**")
        topN = st.slider("Top N (volum)", 5, 30, 12, key="topN_vol")
        g1 = g.sort_values("suspicious_count", ascending=False).head(topN)
        fig = px.bar(g1, x="suspicious_count", y="neighbourhood_cleansed", orientation="h",
                     color_discrete_sequence=[COLOR_MAP["Il·legal/Fals"]])
        fig.update_layout(height=460, margin=dict(l=10, r=10, t=30, b=10))
        fig.update_yaxes(title="", autorange="reversed")
        fig.update_xaxes(title="Núm. anuncis (Il·legal + NRA)")
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown("##### Barris amb major **Taxa** de Sospitosos (%)")
        min_listings = st.slider("Mínim anuncis (%)", 10, 300, 50, step=10, key="min_listings_rate")
        g2 = g[g["listings"] >= min_listings].sort_values("pct_suspicious", ascending=False).head(topN)
        fig2 = px.bar(g2, x="pct_suspicious", y="neighbourhood_cleansed", orientation="h",
                      color_discrete_sequence=["#FFA15A"])
        fig2.update_layout(height=460, margin=dict(l=10, r=10, t=30, b=10))
        fig2.update_yaxes(title="", autorange="reversed")
        fig2.update_xaxes(title="% (Il·legal/Fals + NRA)")
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")
    st.subheader("Detall per barri")

    barrio_sel = st.selectbox("Selecciona un barri", options=sorted(df_f["neighbourhood_cleansed"].unique()))
    df_b = df_f[df_f["neighbourhood_cleansed"] == barrio_sel].copy()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Anuncis", len(df_b))
    c2.metric("Il·legal/Fals", int(df_b["is_illegal"].sum()))
    c3.metric("NRA", int(df_b["is_nra"].sum()))
    c4.metric("Mediana €", f"{np.nanmedian(df_b['price_cleaned']):.0f}" if df_b["price_cleaned"].notna().any() else "—")

    cc1, cc2 = st.columns(2)
    with cc1:
        tmp = df_b.groupby(["room_type", "License_Verification"]).size().reset_index(name="n")
        fig = px.bar(tmp, x="n", y="room_type", color="License_Verification", orientation="h",
                     color_discrete_map=COLOR_MAP,
                     category_orders={"License_Verification": LICENSE_ORDER})
        fig.update_layout(height=420, margin=dict(l=10, r=10, t=30, b=10))
        fig.update_yaxes(title="")
        st.plotly_chart(fig, use_container_width=True)

    with cc2:
        df_bp = df_b[df_b["price_for_viz"].notna()].copy()
        if len(df_bp):
            fig = px.violin(
                df_bp, x="License_Verification", y="price_for_viz",
                color="License_Verification",
                color_discrete_map=COLOR_MAP,
                category_orders={"License_Verification": LICENSE_ORDER},
                box=True, points="outliers"
            )
            fig.update_layout(height=420, margin=dict(l=10, r=10, t=30, b=10))
            fig.update_xaxes(title="")
            fig.update_yaxes(title="Preu (clip p99)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sense preus vàlids.")

with tab_hosts:
    st.subheader("Anàlisi per Amfitrió (Host)")

    hosts = (df_f.groupby(["host_id", "host_name"], dropna=False)
             .agg(
                 listings=("id", "count"),
                 ilegal=("is_illegal", "sum"),
                 nra=("is_nra", "sum"),
                 median_price=("price_cleaned", "median"),
                 barrios=("neighbourhood_cleansed", lambda s: s.nunique()),
             )
             .reset_index())
    
    hosts["bad_count"] = hosts["ilegal"] + hosts["nra"]
    hosts["pct_bad"] = np.where(hosts["listings"] > 0, hosts["bad_count"] / hosts["listings"] * 100, 0)
    hosts = hosts.sort_values(["bad_count", "listings"], ascending=False)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("##### Amfitrions amb més Il·legal + NRA")
        st.dataframe(
            hosts[["host_id","host_name","listings","bad_count","nra","pct_bad","median_price"]].head(25),
            use_container_width=True,
            hide_index=True
        )

    with c2:
        st.markdown("##### Scatter: Mida vs % Sospitós")
        hplot = hosts[hosts["listings"] >= 2].copy()
        fig = px.scatter(
            hplot,
            x="listings",
            y="pct_bad",
            size="bad_count",
            hover_data=["host_name", "nra", "median_price", "barrios"],
            labels={"listings":"Núm anuncis", "pct_bad":"% Il·legal/NRA"},
            color_discrete_sequence=["#EF553B"]
        )
        fig.update_layout(height=420, margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("Top anuncis NRA / Il·legals per preu")
    df_il = df_f[df_f["License_Verification"].isin(["Il·legal/Fals", "NRA"])].copy()
    df_il = df_il.sort_values("price_cleaned", ascending=False)
    
    st.dataframe(
        df_il[["id","name","neighbourhood_cleansed","License_Verification","host_name","price_cleaned","listing_url"]].head(50),
        use_container_width=True,
        hide_index=True
    )

with tab_prices:
    st.subheader("Exploració de preus")
    dfp = df_f[df_f["price_for_viz"].notna()].copy()

    if dfp.empty:
        st.warning("No hi ha preus.")
    else:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("##### Histograma")
            fig = px.histogram(
                dfp, x="price_for_viz", color="License_Verification",
                nbins=60, barmode="overlay", opacity=0.65,
                color_discrete_map=COLOR_MAP,
                category_orders={"License_Verification": LICENSE_ORDER}
            )
            fig.update_layout(height=420, margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            st.markdown("##### Preu vs Nits Mínimes")
            df_sc = dfp.sample(min(15000, len(dfp)), random_state=42)
            fig2 = px.scatter(
                df_sc, x="minimum_nights", y="price_cleaned",
                color="License_Verification",
                color_discrete_map=COLOR_MAP,
                category_orders={"License_Verification": LICENSE_ORDER},
                hover_data=["name"]
            )
            fig2.update_layout(height=420, margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig2, use_container_width=True)

with tab_explorer:
    st.subheader("Explorador de dades")
    c1, c2 = st.columns([1.4, 1])
    with c1:
        text_search = st.text_input("Cercar (nom, amfitrió, llicència...)", value="")
    with c2:
        max_rows = st.number_input("Files màx", 100, 20000, 1000, step=100)

    df_x = df_f.copy()
    if text_search.strip():
        q = text_search.strip().lower()
        mask = (
            df_x["name"].astype(str).str.lower().str.contains(q, na=False) |
            df_x["host_name"].astype(str).str.lower().str.contains(q, na=False) |
            df_x["neighbourhood_cleansed"].astype(str).str.lower().str.contains(q, na=False) |
            df_x["license"].astype(str).str.lower().str.contains(q, na=False) |
            df_x["listing_url"].astype(str).str.lower().str.contains(q, na=False)
        )
        df_x = df_x[mask]

    st.dataframe(df_x.head(int(max_rows)), use_container_width=True, hide_index=True)
    
    csv = df_x.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Descarregar CSV", data=csv, file_name="airbnb_filtrado.csv", mime="text/csv")
