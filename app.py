"""Dicker Data price & stock browser.

Reads data/feed.parquet (produced by refresh.py) and renders an Excel-like grid.
"""
import io
import json
from pathlib import Path

import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, DataReturnMode, GridOptionsBuilder, GridUpdateMode

DATA_DIR = Path("data")
FEED_PATH = DATA_DIR / "feed.parquet"
META_PATH = DATA_DIR / "meta.json"

st.set_page_config(page_title="Dicker Data — Price & Stock", layout="wide")


@st.cache_data(show_spinner="Loading feed…")
def load_feed(cache_key: float) -> pd.DataFrame:
    # cache_key = file mtime; changing it invalidates the cache after a refresh commit.
    del cache_key
    return pd.read_parquet(FEED_PATH)


def load_meta() -> dict:
    if not META_PATH.exists():
        return {}
    try:
        return json.loads(META_PATH.read_text())
    except json.JSONDecodeError:
        return {}


def main() -> None:
    st.title("Dicker Data — Price & Stock")

    if not FEED_PATH.exists():
        st.error(
            "No data file found at `data/feed.parquet`.\n\n"
            "Seed it locally by running `DD_DOWNLOAD_URL=… python refresh.py`, "
            "or wait for the GitHub Actions workflow to publish one."
        )
        st.stop()

    df = load_feed(FEED_PATH.stat().st_mtime)
    meta = load_meta()

    all_vendors = sorted(v for v in df["Vendor"].dropna().unique().tolist() if v)
    default_vendors = [v for v in all_vendors if v.upper() == "SHURE"]
    selected_vendors = st.multiselect(
        "Vendor (default: Shure — clear to see all vendors)",
        options=all_vendors,
        default=default_vendors,
    )
    filtered = df[df["Vendor"].isin(selected_vendors)] if selected_vendors else df

    st.caption(
        f"Showing **{len(filtered):,}** of **{len(df):,}** SKUs. "
        "Per-column filter and sort are in the grid header. "
        "`Margin` = RRPEx − DealerEx (ex-GST). `Margin %` = margin / RRP. "
        "`StockAvailable = 999999999` denotes unlimited items (services / training / licenses)."
    )

    show_margin_summary = st.checkbox(
        "Show margin summary for the current vendor selection",
        value=False,
    )
    if show_margin_summary:
        stocked = filtered[filtered["StockAvailable"].between(1, 999_999_998)]
        with_price = stocked[(stocked["RRPEx"] > 0) & (stocked["DealerEx"] > 0)]
        if len(with_price) == 0:
            st.info("No in-stock SKUs with positive RRP and Dealer prices in this selection.")
        else:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("SKUs (in stock, priced)", f"{len(with_price):,}")
            c2.metric("Avg Margin %", f"{with_price['MarginPct'].mean():.1f}%")
            c3.metric("Median Margin %", f"{with_price['MarginPct'].median():.1f}%")
            c4.metric(
                "Stock value @ Dealer",
                f"${(with_price['DealerEx'] * with_price['StockAvailable']).sum():,.0f}",
            )

    gb = GridOptionsBuilder.from_dataframe(filtered)
    gb.configure_default_column(
        filter=True,
        sortable=True,
        resizable=True,
        floatingFilter=True,
    )
    for col in ("RRPEx", "DealerEx", "StockAvailable", "Margin", "MarginPct"):
        gb.configure_column(col, type=["numericColumn", "numberColumnFilter"])
    gb.configure_column("MarginPct", header_name="Margin %")
    gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=100)
    gb.configure_grid_options(domLayout="normal")

    grid_return = AgGrid(
        filtered,
        gridOptions=gb.build(),
        height=650,
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        update_mode=GridUpdateMode.FILTERING_CHANGED | GridUpdateMode.SORTING_CHANGED,
        allow_unsafe_jscode=False,
        enable_enterprise_modules=False,
        theme="streamlit",
    )

    displayed = pd.DataFrame(grid_return["data"]) if grid_return.get("data") is not None else filtered

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        displayed.to_excel(writer, index=False, sheet_name="Feed")
    st.download_button(
        label=f"Download filtered view as Excel ({len(displayed):,} rows)",
        data=buf.getvalue(),
        file_name="dd-price-stock-filtered.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    refreshed_at = meta.get("refreshed_at", "unknown")
    row_count = meta.get("row_count", "?")
    st.caption(f"Last refreshed: **{refreshed_at}** · source rows: **{row_count}**")


if __name__ == "__main__":
    main()
