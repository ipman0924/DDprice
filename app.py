"""Dicker Data price & stock browser.

Reads data/feed.parquet (produced by refresh.py) and renders an Excel-like grid.
"""
import hmac
import io
import json
from pathlib import Path

import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, DataReturnMode, GridOptionsBuilder, GridUpdateMode

DEFAULT_PASSWORD = "jands"

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


def _expected_password() -> str:
    try:
        return st.secrets["APP_PASSWORD"]
    except Exception:
        return DEFAULT_PASSWORD


def check_password() -> bool:
    if st.session_state.get("authed"):
        return True
    with st.form("login", clear_on_submit=True):
        st.markdown("#### Enter password to view data")
        pw = st.text_input(
            "password",
            type="password",
            label_visibility="collapsed",
            placeholder="Password",
        )
        submitted = st.form_submit_button("Enter")
    if submitted:
        if hmac.compare_digest(pw, _expected_password()):
            st.session_state["authed"] = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    return False


def main() -> None:
    st.title("Dicker Data — Price & Stock")

    if not check_password():
        st.stop()

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
        "`StockAvailable = 999999999` denotes unlimited items (services / training / licenses)."
    )

    gb = GridOptionsBuilder.from_dataframe(filtered)
    gb.configure_default_column(
        filter=True,
        sortable=True,
        resizable=True,
        floatingFilter=True,
    )
    for col in ("RRPEx", "DealerEx", "StockAvailable"):
        gb.configure_column(col, type=["numericColumn", "numberColumnFilter"])
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
