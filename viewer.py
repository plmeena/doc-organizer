# pip install streamlit pandas
# streamlit run viewer.py
import sqlite3, pandas as pd, base64
from pathlib import Path
import streamlit as st

from config import get_config

CONFIG = get_config()
DB_PATH = CONFIG["db_path"]


def ensure_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT,
        category TEXT,
        vendor TEXT,
        doc_date TEXT,
        expiry_date TEXT,
        amount TEXT,
        status TEXT,
        filepath TEXT,
        created_at TEXT
    )""")
    conn.commit()
    conn.close()


ensure_db()
st.set_page_config(page_title="DocOrganizer - Local AI", layout="wide")
st.title("📂 DocOrganizer - 100% Offline")

conn = sqlite3.connect(DB_PATH)
df = pd.read_sql("SELECT filename, category, vendor, doc_date, expiry_date, amount, status, filepath FROM documents ORDER BY expiry_date", conn)
conn.close()

# filters
cat = st.selectbox("Category", ["All"] + sorted(df.category.unique().tolist()) if len(df)>0 else ["All"])
if cat != "All": df = df[df.category==cat]

st.dataframe(df.drop(columns=["filepath"]), use_container_width=True)
st.download_button("⬇️ Export CSV", df.drop(columns=["filepath"]).to_csv(index=False), "documents.csv")

st.divider()
st.subheader("Preview")

for idx, row in df.iterrows():
    with st.expander(f"{'🔴' if row['status']=='Expired' else '🟡' if row['status']=='Expiring Soon' else '🟢'} {row['filename']} — {row['status']}"):
        st.write(f"**Vendor:** {row['vendor']} | **Category:** {row['category']} | **Expiry:** {row['expiry_date']} | **Amount:** {row['amount']}")
        fp = Path(row['filepath']) if pd.notna(row['filepath']) else None
        if fp and fp.exists():
            if fp.suffix.lower() == ".pdf":
                # inline PDF preview
                with open(fp, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode()
                st.markdown(f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="600"></iframe>', unsafe_allow_html=True)
            elif fp.suffix.lower() in [".png",".jpg",".jpeg"]:
                st.image(str(fp))
            else:
                st.info("Preview not available for this file type")
            
            with open(fp, "rb") as f:
                st.download_button("⬇️ Download this file", f, file_name=row['filename'], key=f"dl_{idx}")
        else:
            st.warning("File not found on disk")