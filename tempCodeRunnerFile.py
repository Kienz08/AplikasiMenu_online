@app.route('/done/<int:id_order_cust>', methods=['GET'])
def done(id_order_cust):
    # Mengambil data dari database atau dari sesi jika disimpan sebelumnya
    # Gantilah dengan metode sesuai kebutuhan aplikasi Anda
    nama_pemesan = "Nama Pelanggan"  # Ganti dengan data yang sesuai
    no_meja = "Nomor Meja"  # Ganti dengan data yang sesuai
    total_harga_semua = "Total Harga"  # Ganti dengan data yang sesuai
    order_details = "Detail Pesanan"  # Ganti dengan data yang sesuai

    return render_template('done.html', id_order_cust=id_order_cust, nama_pemesan=nama_pemesan, no_meja=no_meja, total_harga_semua=total_harga_semua, order_details=order_details)
