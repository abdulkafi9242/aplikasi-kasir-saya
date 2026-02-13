# 1. Tulis file aplikasi dulu
%%writefile app.py
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- Konfigurasi Halaman ---
st.set_page_config(page_title="Sistem Kasir Pro", layout="wide")

# --- Inisialisasi Data ---
if 'inventory' not in st.session_state:
    st.session_state['inventory'] = pd.DataFrame(columns=[
        'Produk', 'Varian', 'Harga_Beli', 'Harga_Jual', 'Stok', 'Tanggal_Beli', 'Foto'
    ])
if 'transactions' not in st.session_state:
    st.session_state['transactions'] = pd.DataFrame(columns=[
        'Tanggal', 'Tipe', 'Keterangan', 'Nominal', 'Varian_Terkait'
    ])
if 'targets' not in st.session_state:
    st.session_state['targets'] = [] 

def format_rupiah(angka):
    return f"Rp {angka:,.0f}"

# --- SIDEBAR MENU ---
menu = st.sidebar.selectbox("Menu Utama", 
    ["Kasir (Penjualan)", "Manajemen Produk", "Keuangan (Lain-lain)", "Target Keuangan", "Laporan & Grafik"])

# ==========================
# 1. MANAJEMEN PRODUK
# ==========================
if menu == "Manajemen Produk":
    st.header("📦 Input Produk & Varian")
    with st.form("form_produk"):
        col1, col2 = st.columns(2)
        with col1:
            nama_produk = st.text_input("Nama Produk Utama")
            nama_varian = st.text_input("Nama Varian (Warna/Ukuran)")
            stok = st.number_input("Stok Awal", min_value=1, step=1)
            tgl_beli = st.date_input("Tanggal Beli Stok")
        with col2:
            harga_beli = st.number_input("Harga Dapat (Beli)", min_value=0)
            harga_jual = st.number_input("Harga Jual", min_value=0)
            # Di Colab upload foto agak terbatas, jadi kita pakai placeholder nama saja
            st.info("Fitur Upload Foto disederhanakan di mode Demo Web")
        
        submit = st.form_submit_button("Simpan Produk")
        
        if submit:
            new_data = {
                'Produk': nama_produk,
                'Varian': f"{nama_produk} - {nama_varian}",
                'Harga_Beli': harga_beli,
                'Harga_Jual': harga_jual,
                'Stok': stok,
                'Tanggal_Beli': tgl_beli,
                'Foto': "Demo Mode"
            }
            st.session_state['inventory'] = pd.concat([st.session_state['inventory'], pd.DataFrame([new_data])], ignore_index=True)
            st.success(f"Berhasil menambahkan {nama_produk} varian {nama_varian}")
    
    st.subheader("Daftar Stok")
    st.dataframe(st.session_state['inventory'])

# ==========================
# 2. KASIR (PENJUALAN)
# ==========================
elif menu == "Kasir (Penjualan)":
    st.header("🛒 Kasir Penjualan")
    df_inv = st.session_state['inventory']
    if df_inv.empty:
        st.warning("Belum ada produk. Input dulu di menu Manajemen Produk.")
    else:
        pilihan = st.selectbox("Pilih Produk", df_inv['Varian'].unique())
        item = df_inv[df_inv['Varian'] == pilihan].iloc[0]
        st.info(f"Stok: {item['Stok']} | Harga: {format_rupiah(item['Harga_Jual'])}")
        
        qty = st.number_input("Jumlah Beli", min_value=1, max_value=int(item['Stok']))
        total_harga = qty * item['Harga_Jual']
        
        st.metric("Total Bayar", format_rupiah(total_harga))
        
        if st.button("Proses Transaksi"):
            idx = df_inv[df_inv['Varian'] == pilihan].index[0]
            st.session_state['inventory'].at[idx, 'Stok'] -= qty
            new_trans = {
                'Tanggal': datetime.now(),
                'Tipe': 'Pemasukan (Penjualan)',
                'Keterangan': f"Jual {qty}x {pilihan}",
                'Nominal': total_harga,
                'Varian_Terkait': pilihan
            }
            st.session_state['transactions'] = pd.concat([st.session_state['transactions'], pd.DataFrame([new_trans])], ignore_index=True)
            st.success("Transaksi Berhasil!")

# ==========================
# 3. KEUANGAN & TARGET (GABUNGAN DEMO)
# ==========================
elif menu == "Keuangan (Lain-lain)":
    st.header("💰 Keuangan Lain")
    tipe = st.selectbox("Tipe", ["Pemasukan Lain", "Pengeluaran"])
    ket = st.text_input("Keterangan")
    nom = st.number_input("Nominal", min_value=0)
    if st.button("Simpan"):
        new_trans = {'Tanggal': datetime.now(), 'Tipe': tipe, 'Keterangan': ket, 'Nominal': nom, 'Varian_Terkait': "-"}
        st.session_state['transactions'] = pd.concat([st.session_state['transactions'], pd.DataFrame([new_trans])], ignore_index=True)
        st.success("Disimpan")

elif menu == "Target Keuangan":
    st.header("🎯 Target")
    df_trans = st.session_state['transactions']
    saldo = df_trans[df_trans['Tipe'].str.contains('Pemasukan')]['Nominal'].sum() - df_trans[df_trans['Tipe'].str.contains('Pengeluaran')]['Nominal'].sum()
    st.metric("Saldo Kas", format_rupiah(saldo))
    
    tgt_nama = st.text_input("Nama Target")
    tgt_nom = st.number_input("Butuh Dana", min_value=1000)
    if st.button("Set Target"):
        st.session_state['targets'].append({'Nama': tgt_nama, 'Target': tgt_nom})
    
    for t in st.session_state['targets']:
        st.write(f"Target: {t['Nama']}")
        st.progress(min(saldo / t['Target'], 1.0))

elif menu == "Laporan & Grafik":
    st.header("📊 Laporan")
    df_trans = st.session_state['transactions']
    if not df_trans.empty:
        fig = px.pie(df_trans, values='Nominal', names='Tipe')
        st.plotly_chart(fig)
        st.dataframe(df_trans)
        st.download_button("Download CSV", df_trans.to_csv().encode('utf-8'), "data.csv")
    else:
        st.write("Belum ada data.")

# --- END OF APP FILE ---
pass

# 2. Install Library yang dibutuhkan
print("Sedang menginstall library... Mohon tunggu sebentar...")
!pip install streamlit pandas plotly -q

# 3. Jalankan Tunneling agar bisa diakses public
print("Menyiapkan link aplikasi...")
!wget -q -O - ipv4.icanhazip.com > ip.txt
print("PASSWORD/IP ENDPOINT ANDA ADALAH:")
!cat ip.txt
print("\nKlik link 'your url is' di bawah ini, lalu masukkan IP di atas jika diminta:")
!streamlit run app.py & npx localtunnel --port 8501
