from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_mysqldb import MySQL
import json, re

app = Flask(__name__)
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'menu_db'

app.secret_key = '12345'

mysql = MySQL(app)

@app.route('/')
def index():
    return render_template('index.html')

# HALAMAN ADMIN

# Login
@app.route('/login', methods=['GET', 'POST'])  # Izinkan metode GET dan POST
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM admin WHERE username = %s AND password = %s", (username, password))
        user = cur.fetchone()
        cur.close()

        if user:
            # Logika login berhasil
            return redirect(url_for('dashboard', username=username))
        else:
            # Logika login gagal
            return render_template('login.html', error='Login gagal. Cek kembali username dan password.')
        
    # Jika metode adalah GET, tampilkan halaman login
    return render_template('login.html')

# Halaman dashboard
@app.route('/admin/dashboard/<username>')
def dashboard(username):
    greeting = f'Halo, {username}-!'
    return render_template('admin/dashboard.html', greeting=greeting, username=username)

@app.route('/admin/menu_admin/<username>')
def menu_admin(username):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM menu")
    items = cur.fetchall()
    cur.close()

    return render_template('admin/menu_admin.html', username=username, data=items)

@app.route('/logout')
def logout():
    # Membersihkan sesi
    session.pop('username', None)
    return redirect(url_for('login'))

# CRUD #
# Halaman Tambah Menu Baru
@app.route('/admin/process/add_menu/<username>', methods=['GET', 'POST'])
def add_menu(username):
    if request.method == 'POST':
        nama = request.form['nama']
        harga = request.form['harga']
        keterangan = request.form['keterangan']
        kategori = request.form['kategori']

        # Mengambil file gambar dari formulir
        gambar = request.files['gambar']
        # Menyimpan file gambar ke folder static/img (pastikan folder tersebut sudah ada)
        gambar.save('static/img/' + gambar.filename)

        # Menjalankan query untuk menambahkan data baru
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO menu (nama, harga, keterangan, kategori, gambar) VALUES (%s, %s, %s, %s, %s)",
                    (nama, harga, keterangan, request.form['kategori'], gambar.filename))
        mysql.connection.commit()
        cur.close()

        return redirect(url_for('menu_admin', username=username))  # Ganti dengan rute tujuan setelah menambah data

    return render_template('admin/process/add_menu.html', username=username)

# Halaman Edit Menu
@app.route('/admin/process/update_menu/<username>/<int:id_menu>', methods=['GET', 'POST'])
def update_menu(username, id_menu):
    # Menapatkan data menu dari database berdasarkan id_menu
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM menu WHERE id_menu = %s", (id_menu,))
    menu_data = cur.fetchone()
    cur.close()

    if request.method == 'POST':
        # Proses memperbarui data menu
        nama = request.form['nama']
        harga = request.form['harga']
        keterangan = request.form['keterangan']
        kategori = request.form['kategori']  # Tambahkan ini

        # Cek file gambar baru yang diunggah
        if 'gambar' in request.files:
            gambar = request.files['gambar']
            # Simpan gambar baru dan update gambar di database
            gambar.save('static/img/' + gambar.filename)
            cur = mysql.connection.cursor()
            cur.execute("UPDATE menu SET nama=%s, harga=%s, keterangan=%s, kategori=%s, gambar=%s WHERE id_menu=%s",
                        (nama, harga, keterangan, kategori, gambar.filename, id_menu))
        else:
            cur = mysql.connection.cursor()
            cur.execute("UPDATE menu SET nama=%s, harga=%s, keterangan=%s, kategori=%s WHERE id_menu=%s",
                        (nama, harga, keterangan, kategori, id_menu))

        mysql.connection.commit()
        cur.close()

        return redirect(url_for('menu_admin', username=username))

    # Render halaman update_menu dengan data menu
    return render_template('admin/process/update_menu.html', username=username, menu=menu_data)

# Halaman hapus Menu
@app.route('/admin/process/delete_menu/<username>/<int:id_menu>', methods=['POST'])
def delete_menu(username, id_menu):
    if request.method == 'POST':
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM menu WHERE id_menu = %s", (id_menu,))
        mysql.connection.commit()
        cur.close()

    return redirect(url_for('menu_admin', username=username))

# END CRUD #
# END HALAMAN ADMIN

# USER #
# Tampilan Home
@app.route('/home')
def home():
    return render_template('home.html')

# Tampilan Menu
@app.route('/menu')
def menu():
    # Ambil data menu dari database
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM menu")
    menu_data = cur.fetchall()
    cur.close()

    return render_template('menu.html', menu_data=menu_data)

# Kategori Menu
@app.route('/menu/<kategori>')
def menu_by_kategori(kategori):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM menu WHERE kategori = %s", (kategori,))
    menu_data = cur.fetchall()
    cur.close()

    return render_template('menu.html', menu_data=menu_data)

# Keranjang
def query_detail_menu(id_menu):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM menu WHERE id_menu = %s", (id_menu,))
    menu_detail = cur.fetchone()
    cur.close()
    return menu_detail

# Tambah Menu ke Keranjang
def convert_price_string_to_float(price_string):
    # Hapus karakter non-digit dari string harga
    cleaned_price_string = ''.join(char for char in price_string if char.isdigit() or char == '.')

    try:
        # Konversi string yang sudah dibersihkan menjadi float
        price_float = float(cleaned_price_string)
        return price_float
    except ValueError:
        # Handle kesalahan jika konversi gagal
        print(f"Error converting price string to float: {price_string}")
        return None


@app.route('/add_to_cart/<int:id_menu>')
def add_to_cart(id_menu):
    # Mengambil data keranjang dari sesi Flask atau sisi klien
    keranjang = session.get('keranjang', [])

    # Periksa apakah menu sudah ada di dalam keranjang
    if id_menu in keranjang:
        print("Menu already in cart.")
        # Jika sudah ada, kirim respons JSON dengan pesan peringatan
        return jsonify({'success': False, 'message': 'Menu already in cart.'})
    else:
        # Jika belum, tambahkan ID menu ke dalam keranjang
        keranjang.append(id_menu)

        # Menyimpan kembali keranjang ke sesi
        session['keranjang'] = keranjang

        # Kirim respons JSON dengan pesan sukses
        return jsonify({'success': True, 'message': 'Menu added to cart successfully. <i class="fa-solid fa-check fa-lg" style="color: #ff9f1a;"></i>'})


# @app.route('/add_to_cart/<int:id_menu>')
# def add_to_cart(id_menu):
#     keranjang = session.get('keranjang', {})

#     menu_detail = get_menu_detail_by_id(id_menu)

#     if menu_detail and menu_detail['harga'] is not None:
#         if id_menu in keranjang:
#             keranjang[id_menu]['quantity'] += 1
#         else:
#             keranjang[id_menu] = {
#                 'id_menu': menu_detail['id_menu'],
#                 'nama': menu_detail['nama'],
#                 'quantity': 1,
#                 'harga': menu_detail['harga'],
#             }

#         session['keranjang'] = keranjang

#         return redirect(url_for('menu'))
#     else:
#         return jsonify({'success': False, 'message': 'Menu not found or invalid price.'})

# Halaman Keranjang
# @app.route('/cart')
# def cart():
#     # Mengambil data keranjang dari sesi Flask atau sisi klien
#     data_keranjang = session.get('keranjang', [])

#     # Mengambil detail menu berdasarkan ID menu
#     detail_keranjang = []
#     for id_menu in data_keranjang:
#         menu_detail = query_detail_menu(id_menu)
#         if menu_detail:
#             detail_keranjang.append(menu_detail)

#     return render_template('keranjang.html', detail_keranjang=detail_keranjang)

# Halaman Keranjang
@app.route('/cart')
def cart():
    # Mengambil data keranjang dari sesi Flask atau sisi klien
    data_keranjang = session.get('keranjang', [])

    # Mengambil detail menu berdasarkan ID menu
    detail_keranjang = []
    for id_menu in data_keranjang:
        menu_detail = query_detail_menu(id_menu)
        if menu_detail:
            detail_keranjang.append(menu_detail)

    # Simpan data ke sesi Flask
    session['detail_keranjang'] = detail_keranjang

    return render_template('keranjang.html', detail_keranjang=detail_keranjang)

# Hapus Menu dari Keranjang
@app.route('/hapus_dari_keranjang/<int:id_menu>')
def hapus_dari_keranjang(id_menu):
    keranjang = session.get('keranjang', [])

    if id_menu in keranjang:
        keranjang.remove(id_menu)
        session['keranjang'] = keranjang

    return redirect(url_for('cart'))

# END Halaman Keranjang

# Halaman Order Menu
@app.route('/order_menu', methods=['POST'])
def order_menu():
    if request.method == 'POST':
        selected_menus = request.form.get('selected_menus').split(',')
        quantities = request.form.get('quantities').split(',')
        # selected_menus = request.form.getlist('selected_menus[]')
        # quantities = request.form.getlist('quantities[]')

        print('Received Selected Menus:', selected_menus)  # Pemantauan di konsol server
        print('Received Quantities:', quantities)  # Pemantauan di konsol server

        # Mengambil detail menu berdasarkan ID
        detail_menus = []
        total_harga_semua = 0  # Tambahkan variabel untuk total harga semua menu

        for i in range(len(selected_menus)):
            menu_detail = query_detail_menu(selected_menus[i])
            if menu_detail:
                # Membersihkan format harga menggunakan regex
                harga_string = menu_detail[2]
                harga_clean = re.sub(r'[^0-9.]', '', harga_string)  # Hanya biarkan karakter numerik dan titik

                # Menambahkan satu nol setelah koma desimal
                harga_formatted = f'{harga_clean},00'

                # Menghitung total harga per menu
                # Pemeriksaan nilai quantities[i] sebelum konversi ke integer
                quantity_str = quantities[i] if quantities[i] else '0'

                harga_float = float(harga_clean) if harga_clean else 0.0
                total_harga_menu = harga_float * int(quantity_str)

                total_harga_menu_formatted = f'{total_harga_menu}00,00'

                # Menambahkan total harga menu ke total harga semua
                total_harga_semua += total_harga_menu

                detail_menus.append({
                    'id': selected_menus[i],
                    'nama': menu_detail[1],
                    'harga': harga_formatted,
                    'jumlah': int(quantity_str),
                    'total_harga': f'{total_harga_menu_formatted}'  # Format total harga per menu
                })

        # Menambahkan total harga semua ke detail_menus
        total_harga_semua_formatted = f'{total_harga_semua}00,00'
        detail_menus.append({'total_harga_semua': total_harga_semua_formatted})

        # Pemantauan di konsol server
        print(f"Detail Menus: {detail_menus}")

        return render_template('order_menu.html', detail_menus=detail_menus)

    return render_template('order_menu.html')

# Route untuk proses order
@app.route('/process_order', methods=['POST'])
def process_order():
    if request.method == 'POST':
        nama_pemesan = request.form['nama_pemesan']
        no_meja = request.form['no_meja']
        order_details_str = request.form['order_details']

        # Cetak nilai order_details_str untuk debugging
        print('Order Details String:', order_details_str)

        # Mengecek apakah string JSON tidak kosong
        if not order_details_str:
            return "Empty JSON data", 400

        try:
            # Mengubah string JSON menjadi objek Python
            order_details = json.loads(order_details_str)
        except json.JSONDecodeError as e:
            print("JSON Decode Error:", e)
            return "Invalid JSON data", 400

        # Pemeriksaan panjang list sebelum mengakses elemen
        if order_details and len(order_details) > 0:
            if 'total_harga_semua' in order_details[-1]:
                total_harga_semua = order_details[-1]['total_harga_semua']
            else:
                return "Invalid order_details (total_harga_semua not found in the last item)", 400
        else:
            return "Invalid order_details (empty or has length 0)", 400

        # Cetak nilai untuk debugging
        print('Nama Pemesan:', nama_pemesan)
        print('Nomor Meja:', no_meja)
        print('Panjang order_details:', len(order_details))

        # Menjalankan query untuk menambahkan data ke tabel order_cust
        cur = mysql.connection.cursor()

        try:
            cur.execute("INSERT INTO order_cust (id_kasir, nama_pemesan, no_meja, total) VALUES (%s, %s, %s, %s)",
                        (1, nama_pemesan, no_meja, total_harga_semua))
            mysql.connection.commit()

            # Dapatkan ID order_cust yang baru saja dimasukkan
            id_order_cust = cur.lastrowid

            cur.close()

            return redirect(url_for('done', id_order_cust=id_order_cust))  # Ganti dengan rute tujuan setelah menambah data
        
        except Exception as e:
            print("Kesalahan saat menambahkan data ke order_cust:", e)

    return render_template('order_menu.html')

# Halaman Setelah Order
@app.route('/done', methods=['GET'])
def done():
    # Mendapatkan data dari formulir pertama (dapat disimpan di sesi atau basis data)
    nama_pemesan = request.args.get('nama_pemesan_done')
    no_meja = request.args.get('no_meja_done')

    # Logika untuk menampilkan data atau melakukan operasi lain sesuai kebutuhan

    # Render template formulir kedua dengan data yang dikirim
    return render_template('done.html', nama_pemesan=nama_pemesan, no_meja=no_meja)


# @app.route('/process_order', methods=['POST'])
# def process_order():
#     if request.method == 'POST':
#         nama_pemesan = request.form['nama_pemesan']
#         no_meja = request.form['no_meja']
#         order_details_str = request.form['order_details']

#         # Cetak nilai order_details_str untuk debugging
#         print('Order Details String:', order_details_str)

#         # Mengecek apakah string JSON tidak kosong
#         if not order_details_str:
#             return "Empty JSON data", 400

#         try:
#             # Mengubah string JSON menjadi objek Python
#             order_details = json.loads(order_details_str)
#         except json.JSONDecodeError as e:
#             print("JSON Decode Error:", e)
#             return "Invalid JSON data", 400

#         # Pemeriksaan panjang list sebelum mengakses elemen
#         if order_details and len(order_details) > 0:
#             if 'total_harga_semua' in order_details[-1]:
#                 total_harga_semua = order_details[-1]['total_harga_semua']
#             else:
#                 return "Invalid order_details (total_harga_semua not found in the last item)", 400
#         else:
#             return "Invalid order_details (empty or has length 0)", 400

#         # Cetak nilai untuk debugging
#         print('Nama Pemesan:', nama_pemesan)
#         print('Nomor Meja:', no_meja)
#         print('Panjang order_details:', len(order_details))

#         # Menjalankan query untuk menambahkan data ke tabel order_cust
#         cur = mysql.connection.cursor()
#         cur.execute("INSERT INTO order_cust (id_kasir, nama_pemesan, no_meja, total) VALUES (%s, %s, %s, %s)",
#                     (1, nama_pemesan, no_meja, total_harga_semua))
#         mysql.connection.commit()

#         # Dapatkan ID order_cust yang baru saja dimasukkan
#         id_order_cust = cur.lastrowid

#         # Menjalankan query untuk menambahkan data ke tabel order_menu
#         for menu_detail in order_details[:-1]:
#             id_menu = menu_detail['id_menu']  # Ambil id_menu dari setiap menu_detail
#             cur.execute("INSERT INTO order_menu (id_orderCust, id_kasir, id_menu, nama, jumlah, harga_item, harga_total_menu, total) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
#                         (id_order_cust, 1, id_menu, menu_detail['nama'], menu_detail['jumlah'], menu_detail['harga'], menu_detail['total_harga'], total_harga_semua))
#             mysql.connection.commit()

#         cur.close()

#         return redirect(url_for('done'))  # Ganti dengan rute tujuan setelah menambah data

#     return render_template('order_menu.html')

# END USER #

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
