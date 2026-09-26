import os
import sqlite3
import libsql_experimental as libsql
from flask import Flask, render_template, request, redirect, url_for, session, flash
import random
import datetime

TURSO_TOKEN = os.environ.get("TURSO_AUTH_TOKEN", "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJqdGkiOiJrUXJJVTdsYkVmR0R1MDdXRWFlUHR3Iiwib3JnX2lkIjoxMDAwMjU0OTI1fQ.99DQb5qxBvVo89tLkDMp5rNocpjQ9IJYQtyIZ3hQs3NEIIJ5e7aXovy6HVDM59iKWgrdRjYAtooIYAkn0dWBBg")

def connect_db(env_var_name, local_file):
    url = os.environ.get(env_var_name)
    if url and TURSO_TOKEN:
        conn = libsql.connect(database=url, auth_token=TURSO_TOKEN)
    else:
        conn = sqlite3.connect(local_file)
    
    conn.row_factory = sqlite3.Row
    return conn

def get_db_usr():
    return connect_db("TURSO_USR_URL", "bdd_usr.db")

def get_db_trans():
    return connect_db("TURSO_TRANS_URL", "bdd_trans.db")

def get_db_oper():
    return connect_db("TURSO_OPER_URL", "bdd_oper.db")

def get_db_empl():
    return connect_db("TURSO_EMPL_URL", "bdd_empl.db")

def get_db_admin():
    return connect_db("TURSO_ADMIN_URL", "bdd_admin.db")

def init_db():
    conn_usr = get_db_usr()
    cursor_usr = conn_usr.cursor()
    cursor_usr.execute("CREATE TABLE IF NOT EXISTS tabla_usr(ID TEXT PRIMARY KEY, contr TEXT, nombre TEXT, apellidopat TEXT, apellidomat TEXT, edad INTEGER, curp TEXT, calle TEXT, numcalle TEXT, colonia TEXT, ciudad TEXT, estado TEXT, CP TEXT, detalles TEXT, saldo REAL)")
    cursor_usr.execute("CREATE TABLE IF NOT EXISTS tabla_tar_usr(numtaj TEXT, fechavenc TEXT, cvv TEXT, clabe TEXT, saldo REAL, ID TEXT)")
    cursor_usr.execute("CREATE TABLE IF NOT EXISTS tabla_tdc_usr(ID TEXT, numtaj TEXT, fechavenc TEXT, cvv TEXT, nombre_compl TEXT, sald_fav REAL, sald_contr REAL, exist INTEGER)")
    conn_usr.commit()
    conn_usr.close()

    conn_empl = get_db_empl()
    cursor_empl = conn_empl.cursor()
    cursor_empl.execute("CREATE TABLE IF NOT EXISTS tabla_emp(ID TEXT, contr TEXT, nombre TEXT, apellidopat TEXT, apellidomat TEXT)")
    cursor_empl.execute("CREATE TABLE IF NOT EXISTS tabla_tdc_emp(ID TEXT, nombre_compl TEXT, ingresos_men TEXT, ocupacion TEXT, numtaj TEXT, fechavenc TEXT, credito REAL, status TEXT, razon TEXT)")
    conn_empl.commit()
    conn_empl.close()

    conn_trans = get_db_trans()
    cursor_trans = conn_trans.cursor()
    cursor_trans.execute("CREATE TABLE IF NOT EXISTS tabla_trans(ID TEXT, transmont REAL, transdest TEXT, transfech TEXT, transconc TEXT)")
    conn_trans.commit()
    conn_trans.close()

    conn_oper = get_db_oper()
    cursor_oper = conn_oper.cursor()
    cursor_oper.execute("CREATE TABLE IF NOT EXISTS tabla_oper(calle TEXT, numcalle TEXT, colonia TEXT, ciudad TEXT, estado TEXT, CP TEXT, detalles TEXT, nombre_cli TEXT)")
    cursor_oper.execute("CREATE TABLE IF NOT EXISTS tabla_oper_id(ID TEXT, contr TEXT, nombre TEXT, apellidopat TEXT, apellidomat TEXT, empresa TEXT)")
    conn_oper.commit()
    conn_oper.close()

    conn_admin = get_db_admin()
    cursor_admin = conn_admin.cursor()
    cursor_admin.execute("CREATE TABLE IF NOT EXISTS reg_admin(ID TEXT, contr TEXT, nombre TEXT, apellidopat TEXT, apellidomat TEXT)")
    cursor_admin.execute("CREATE TABLE IF NOT EXISTS reg_ger_emp(ID TEXT, contr TEXT, nombre_compl TEXT)")
    cursor_admin.execute("CREATE TABLE IF NOT EXISTS reg_ger_oper(ID TEXT, contr TEXT, nombre_compl TEXT)")
    conn_admin.commit()
    conn_admin.close()

init_db()

app = Flask(__name__)
app.secret_key = 'clave_super_secreta_bbva_lina'

LLAVE_CORRECTA = 'LINA2026'

@app.route('/', methods=['GET', 'POST'])
def acceso_portal():
    error = None
    if request.method == 'POST':
        llave_ingresada = request.form.get('llave_acceso')
        if llave_ingresada == LLAVE_CORRECTA:
            session['autorizado'] = True
            return redirect(url_for('menu_roles'))
        else:
            error = 'Llave de acceso incorrecta. Intente de nuevo.'
    return render_template('index.html', error=error)

@app.route('/menu')
def menu_roles():
    if not session.get('autorizado'):
        return redirect(url_for('acceso_portal'))
    return render_template('menu.html')

@app.route('/salir')
def salir():
    session.clear()
    return redirect(url_for('acceso_portal'))

@app.route('/login/cliente', methods=['GET', 'POST'])
def login_cliente():
    if not session.get('autorizado'):
        return redirect(url_for('acceso_portal'))
        
    error = None
    if request.method == 'POST':
        check_id_usr = request.form.get('id_usr', '').upper()
        check_contr_usr = request.form.get('contr_usr')
        
        conn = get_db_usr()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tabla_usr WHERE ID = ?", (check_id_usr,))
            usuario = cursor.fetchone()
        finally:
            conn.close()
        
        if usuario is None:
            error = "El usuario no existe."
        elif usuario['contr'] != check_contr_usr:
            error = "Contraseña incorrecta."
        else:
            session['cliente_id'] = usuario['ID']
            session['cliente_nombre'] = usuario['nombre']
            return redirect(url_for('dashboard_cliente'))

    return render_template('login_cliente.html', error=error)

@app.route('/cliente/dashboard')
def dashboard_cliente():
    if not session.get('autorizado'):
        return redirect(url_for('acceso_portal'))
    if 'cliente_id' not in session:
        return redirect(url_for('login_cliente'))

    error = None
    conn_usr = get_db_usr()
    try:
        cursor_usr = conn_usr.cursor()
        cursor_usr.execute("SELECT * FROM tabla_usr WHERE ID=?", (session['cliente_id'],))
        check_datos_usr = cursor_usr.fetchone()
        
        cursor_usr.execute("SELECT * FROM tabla_tar_usr WHERE ID=?", (session['cliente_id'],))
        check_datos_usr_tar = cursor_usr.fetchone()
        
        cursor_usr.execute("SELECT * FROM tabla_tdc_usr WHERE ID=?", (session['cliente_id'],))
        check_datos_usr_tdc = cursor_usr.fetchone()
        
        tdc_exists = check_datos_usr_tdc['exist'] if check_datos_usr_tdc else 0
        nombre = check_datos_usr['nombre'] if check_datos_usr else ""
        saldo = check_datos_usr['saldo'] if check_datos_usr else 0.0
        numtaj = check_datos_usr_tar['numtaj'][-4:] if check_datos_usr_tar else "0000"
        numtajtdc = str(check_datos_usr_tdc[1])[-4:] if (check_datos_usr_tdc and check_datos_usr_tdc[1]) else "0000"
        saldofav=check_datos_usr_tdc[-3] if check_datos_usr_tdc else "0.0"
        saldocontr=check_datos_usr_tdc[-2] if check_datos_usr_tdc else "0.0"
        session['bienvenida_numtajTDC']=numtajtdc
        session['saldofavTDC']=saldofav
        session['saldocontrTDC']=saldocontr
        session['tdc_exists'] = tdc_exists
        session['bienvenida_numtaj_usr'] = numtaj
        session['bienvenida_saldo_usr'] = saldo
        session['bienvenida_nombre_usr'] = nombre
    finally:
        conn_usr.close()

    return render_template('dashboard_cliente.html', error=error)

@app.route('/cliente/crear_cuenta', methods=['GET', 'POST'])
def crear_cuenta():
    if not session.get('autorizado'):
        return redirect(url_for('acceso_portal'))
    error = None
    if request.method == "POST":
        ask_nombre_usr = request.form.get('nombre_usr', '')
        ask_apellpat_usr = request.form.get('apellpat_usr','')
        ask_apellmat_usr = request.form.get('apellmat_usr','')
        ask_edad_usr = request.form.get('edad_usr','')
        ask_curp_usr = request.form.get('curp_usr','').upper()
        ask_ine_usr = request.form.get('ine_usr','')
        ask_contr_usr = request.form.get('contr_usr', '')
        nombre_completo_usr = f"{ask_nombre_usr} {ask_apellpat_usr} {ask_apellmat_usr}"
        
        try:
            edad_usr_good = int(ask_edad_usr) > 17
        except ValueError:
            edad_usr_good = False

        curp_usr_good = len(ask_curp_usr) == 18
        ine_usr_good = len(ask_ine_usr) == 10
        contr_usr_good = len(ask_contr_usr) == 8

        if not edad_usr_good:
            error = "Necesita ser mayor de edad para abrir una cuenta."
        elif not curp_usr_good:
            error = "Verifique su CURP."
        elif not ine_usr_good:
            error = "Verifique los datos de su INE."
        elif not contr_usr_good:
            error = "La contraseña debe tener 8 dígitos."
        else:
            session['reg_nombre_usr'] = ask_nombre_usr
            session['reg_apellpat_usr'] = ask_apellpat_usr
            session['reg_apellmat_usr'] = ask_apellmat_usr
            session['reg_nombre_completo_usr'] = nombre_completo_usr
            session['reg_edad_usr'] = ask_edad_usr
            session['reg_curp_usr'] = ask_curp_usr
            session['reg_ine_usr'] = ask_ine_usr
            session['reg_contr_usr'] = ask_contr_usr
            return redirect(url_for('crear_cuenta_direccion'))

    return render_template('crear_cuenta.html', error=error)

@app.route('/cliente/crear_cuenta_direccion', methods=['GET', 'POST'])
def crear_cuenta_direccion():
    if not session.get('autorizado'):
        return redirect(url_for('acceso_portal'))
    if 'reg_nombre_usr' not in session:
        return redirect(url_for('crear_cuenta'))

    error = None 
    if request.method == 'POST':
        ask_calle_usr = request.form.get('calle_usr', '')
        ask_numcalle_usr = request.form.get('numcalle_usr', '')
        ask_col_usr = request.form.get('col_usr', '')
        ask_ciudad_usr = request.form.get('ciudad_usr', '')
        ask_estado_usr = request.form.get('estado_usr', '')
        ask_cp_usr = request.form.get('cp_usr', '')
        ask_detallesdirec_usr = request.form.get('detallesdirec_usr', '')

        if len(ask_calle_usr) <= 2:
            error = "Escriba una calle correcta."
        elif len(ask_col_usr) <= 2:
            error = "Escriba una colonia correcta."
        elif len(ask_ciudad_usr) <= 2:
            error = "Escriba una ciudad correcta."
        elif len(ask_estado_usr) <= 2:
            error = "Escriba un estado correcto."
        elif len(ask_cp_usr) != 5:
            error = "Código Postal incorrecto."
        else:
            session['reg_calle_usr'] = ask_calle_usr
            session['reg_numcalle_usr'] = ask_numcalle_usr
            session['reg_col_usr'] = ask_col_usr
            session['reg_ciudad_usr'] = ask_ciudad_usr
            session['reg_estado_usr'] = ask_estado_usr
            session['reg_cp_usr'] = ask_cp_usr
            session['reg_detallesdirec_usr'] = ask_detallesdirec_usr

            conn_usr = get_db_usr()
            conn_oper = get_db_oper()
            try:
                cursor_usr = conn_usr.cursor()
                cursor_oper = conn_oper.cursor()

                inicial_nombre_usr = session['reg_nombre_usr'][0].upper()
                inicial_apellpat_usr = session['reg_apellpat_usr'][0:2].upper()
                inicial_apellmat_usr = session['reg_apellmat_usr'][0].upper()
                id_usr = f"{inicial_apellpat_usr}{inicial_apellmat_usr}{inicial_nombre_usr}{session['reg_ine_usr']}"
                session['reg_id_usr'] = id_usr

                saldo_usr = 0.0
                numtaj_usr_com = f"{random.randint(5500, 5599)} {random.randint(3001, 3998)} {random.randint(4503, 4699)} {random.randint(9801, 9899)}"
                fech_ven_usr_comp = f"{random.randint(1, 12):02d}/32"
                cvv_usr = str(random.randint(100, 999))
                clabe_usr_comp = f"012180{random.randint(10000000000, 99999999999)}9"

                solicitud_tdc = 0
                cursor_usr.execute("INSERT INTO tabla_tdc_usr(exist, ID) VALUES(?, ?)", (solicitud_tdc, id_usr))
                cursor_usr.execute("INSERT INTO tabla_tar_usr(numtaj, fechavenc, cvv, clabe, saldo, ID) VALUES(?, ?, ?, ?, ?, ?)", (numtaj_usr_com, fech_ven_usr_comp, cvv_usr, clabe_usr_comp, saldo_usr, id_usr))
                cursor_usr.execute("INSERT INTO tabla_usr(ID, contr, nombre, apellidopat, apellidomat, edad, curp, calle, numcalle, colonia, ciudad, estado, CP, detalles, saldo) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (id_usr, session['reg_contr_usr'], session['reg_nombre_usr'], session['reg_apellpat_usr'], session['reg_apellmat_usr'], session['reg_edad_usr'], session['reg_curp_usr'], session['reg_calle_usr'], session['reg_numcalle_usr'], session['reg_col_usr'], session['reg_ciudad_usr'], session['reg_estado_usr'], session['reg_cp_usr'], session['reg_detallesdirec_usr'], saldo_usr))
                cursor_oper.execute("INSERT INTO tabla_oper(calle, numcalle, colonia, ciudad, estado, CP, detalles, nombre_cli) VALUES(?, ?, ?, ?, ?, ?, ?, ?)", (session['reg_calle_usr'], session['reg_numcalle_usr'], session['reg_col_usr'], session['reg_ciudad_usr'], session['reg_estado_usr'], session['reg_cp_usr'], session['reg_detallesdirec_usr'], session['reg_nombre_completo_usr']))

                conn_usr.commit()
                conn_oper.commit()
            finally:
                conn_usr.close()
                conn_oper.close()

            return redirect(url_for('direccion_aviso'))

    return render_template('crear_cuenta_direccion.html', error=error)

@app.route('/cliente/direccion_aviso', methods=['GET', 'POST'])
def direccion_aviso():
    if not session.get('autorizado'):
        return redirect(url_for('acceso_portal'))
    return render_template('direccion_aviso.html')

@app.route('/cliente/movimientos', methods=['GET', 'POST'])
def movimientos_cliente():
    if not session.get('autorizado'):
        return redirect(url_for('acceso_portal'))
    if 'cliente_id' not in session:
        return redirect(url_for('login_cliente'))

    conn_trans = get_db_trans()
    try:
        cursor_trans = conn_trans.cursor()
        cursor_trans.execute("SELECT transmont, transdest, transfech, transconc FROM tabla_trans WHERE ID=?", (session['cliente_id'],))
        check_mov = cursor_trans.fetchall()
        movimientos_limpios = [dict(fila) for fila in check_mov]
        session['movimientos_usr'] = movimientos_limpios
    finally:
        conn_trans.close()

    return render_template('movimientos_cliente.html')

@app.route('/cliente/tarjeta_digital', methods=['GET', 'POST'])
def tarjeta_digital():
    if not session.get('autorizado'):
        return redirect(url_for('acceso_portal'))
    if 'cliente_id' not in session:
        return redirect(url_for('login_cliente'))

    conn_usr = get_db_usr()
    try:
        cursor_usr = conn_usr.cursor()
        cursor_usr.execute("SELECT * FROM tabla_tar_usr WHERE ID=?", (session['cliente_id'],))
        check_tarjeta_digital = cursor_usr.fetchone()
        
        if check_tarjeta_digital:
            session['clabe_debito'] = check_tarjeta_digital['clabe']
            session['numtaj_debito'] = check_tarjeta_digital['numtaj']
            session['fechavenc_debito'] = check_tarjeta_digital['fechavenc']
            session['cvv_debito'] = check_tarjeta_digital['cvv']
    finally:
        conn_usr.close()

    return render_template('tarjeta_digital.html')
@app.route('/cliente/tdc_digital', methods=['GET', 'POST'])
def tdc_digital():
    if not session.get('autorizado'):
        return redirect(url_for('acceso_portal'))
    if 'cliente_id' not in session:
        return redirect(url_for('login_cliente'))

    conn_usr = get_db_usr()
    try:
        cursor_usr = conn_usr.cursor()
        cursor_usr.execute("SELECT * FROM tabla_tdc_usr WHERE ID=?", (session['cliente_id'],))
        check_tarjeta_digital = cursor_usr.fetchone()
        
        if check_tarjeta_digital:
            session['numtaj_tdc'] = check_tarjeta_digital['numtaj']
            session['fechavenc_tdc'] = check_tarjeta_digital['fechavenc']
            session['cvv_tdc'] = check_tarjeta_digital['cvv']
    finally:
        conn_usr.close()

    return render_template('tdc_digital.html')
@app.route('/cliente/tdc/pagar', methods=['GET', 'POST'])
def pagar_tdc():
    if not session.get('autorizado'):
        return redirect(url_for('acceso_portal'))
    if 'cliente_id' not in session:
        return redirect(url_for('login_cliente'))

    check_usr = session.get('cliente_id')
    conn_usr = get_db_usr()
    cursor_usr = conn_usr.cursor()

    cursor_usr.execute("SELECT * FROM tabla_usr WHERE ID=?", (check_usr,))
    fetch_usr = cursor_usr.fetchone()

    cursor_usr.execute("SELECT * FROM tabla_tdc_usr WHERE ID=?", (check_usr,))
    fetch_tdc = cursor_usr.fetchone()

    if not fetch_tdc or not fetch_usr:
        conn_usr.close()
        return "Información no encontrada", 404

    saldo_debito = fetch_usr[-1]
    saldo_deuda = fetch_tdc[-2]
    saldo_favor = fetch_tdc[-3]
    
    num_cuenta_debito = f"14**{str(check_usr).zfill(4)}"
    num_tarjeta_tdc = f"5508**{str(session.get('numtaj_tdc', '7837'))[-4:]}"

    error = None

    if request.method == 'POST':
        opcion_pago = request.form.get('opcion_pago')
        monto_pago = 0.0

        if opcion_pago == 'no_intereses':
            monto_pago = float(saldo_deuda)
        elif opcion_pago == 'minimo':
            monto_pago = float(saldo_deuda) * 0.10
        elif opcion_pago == 'otra_cantidad':
            try:
                monto_pago = float(request.form.get('monto_otra_cantidad', 0))
            except ValueError:
                error = "Ingrese una cantidad válida."

        if not error:
            if monto_pago <= 0:
                error = "El monto a pagar debe ser mayor a $0.00"
            elif monto_pago > saldo_debito:
                error = "Saldo insuficiente en la cuenta de cargo."
            elif monto_pago > saldo_deuda:
                error = "El monto excede el saldo pendiente."
            else:
                nv_sld_contr = saldo_deuda - monto_pago
                nv_sald_from_tdc = saldo_debito - monto_pago
                nv_sld_fav_pago = saldo_favor + monto_pago

                cursor_usr.execute("UPDATE tabla_tdc_usr SET sald_contr=?, sald_fav=? WHERE ID=?", (nv_sld_contr, nv_sld_fav_pago, check_usr))
                cursor_usr.execute("UPDATE tabla_tar_usr SET saldo=? WHERE ID=?", (nv_sald_from_tdc, check_usr))
                cursor_usr.execute("UPDATE tabla_usr SET saldo=? WHERE ID=?", (nv_sald_from_tdc, check_usr))
                conn_usr.commit()
                conn_usr.close()

                session['ultimo_comprobante'] = {
                    'monto': monto_pago,
                    'cuenta_cargo': num_cuenta_debito,
                    'cuenta_abono': num_tarjeta_tdc,
                    'referencia': random.randint(1000000, 9999999),
                    'hora': datetime.datetime.now().strftime("%H:%M"),
                    'fecha': datetime.datetime.now().strftime("%d de %B, %Y")
                }

                return redirect(url_for('comprobante_tdc'))

    conn_usr.close()
    return render_template(
        'pagar_tdc.html',
        saldo_debito=saldo_debito,
        saldo_deuda=saldo_deuda,
        cuenta_debito=num_cuenta_debito,
        tarjeta_tdc=num_tarjeta_tdc,
        error=error
    )


@app.route('/cliente/tdc/comprobante')
def comprobante_tdc():
    if not session.get('autorizado'):
        return redirect(url_for('acceso_portal'))
    if 'cliente_id' not in session:
        return redirect(url_for('login_cliente'))

    datos_comprobante = session.get('ultimo_comprobante')

    if not datos_comprobante:
        return redirect(url_for('dashboard_cliente'))

    return render_template('comprobante_tdc.html', c=datos_comprobante)
@app.route('/cliente/tdc/comprar', methods=['GET', 'POST'])
def comprar_tdc():
    if not session.get('autorizado'):
        return redirect(url_for('acceso_portal'))
    if 'cliente_id' not in session:
        return redirect(url_for('login_cliente'))

    check_usr = session.get('cliente_id')
    conn_usr = get_db_usr()
    cursor_usr = conn_usr.cursor()

    cursor_usr.execute("SELECT * FROM tabla_tdc_usr WHERE ID=?", (check_usr,))
    fetch_tdc = cursor_usr.fetchone()

    if not fetch_tdc:
        conn_usr.close()
        return "Información no encontrada", 404

    saldo_favor = fetch_tdc[-3] 
    saldo_deuda = fetch_tdc[-2]  
    
    num_tarjeta_tdc = f"5508**{str(session.get('numtaj_tdc', '7837'))[-4:]}"
    error = None

    if request.method == 'POST':
        try:
            compras_demo = float(request.form.get('monto_compra', 0))
            establecimiento = request.form.get('establecimiento', 'Comercio Demo').strip() or 'Comercio Demo'
        except ValueError:
            compras_demo = 0.0
            error = "Ingrese una cantidad válida."

        if not error:
            if compras_demo <= 0:
                error = "El monto de la compra debe ser mayor a $0.00"
            elif compras_demo > saldo_favor:
                error = "Saldo insuficiente en la línea de crédito disponible."
            else:
                nv_sld_fav = saldo_favor - compras_demo
                nv_sld_contr_demo = saldo_deuda + compras_demo

                cursor_usr.execute(
                    "UPDATE tabla_tdc_usr SET sald_fav=?, sald_contr=? WHERE ID=?", 
                    (nv_sld_fav, nv_sld_contr_demo, check_usr)
                )
                conn_usr.commit()
                conn_usr.close()

                session['ultimo_comprobante_compra'] = {
                    'monto': compras_demo,
                    'establecimiento': establecimiento,
                    'tarjeta': num_tarjeta_tdc,
                    'referencia': random.randint(1000000, 9999999),
                    'hora': datetime.datetime.now().strftime("%H:%M"),
                    'fecha': datetime.datetime.now().strftime("%d de %B, %Y")
                }

                return redirect(url_for('comprobante_compra_tdc'))

    conn_usr.close()
    return render_template(
        'form_comprar_tdc.html',
        saldo_favor=saldo_favor,
        saldo_deuda=saldo_deuda,
        tarjeta_tdc=num_tarjeta_tdc,
        error=error
    )

@app.route('/cliente/tdc/comprobante_compra')
def comprobante_compra_tdc():
    if not session.get('autorizado'):
        return redirect(url_for('acceso_portal'))
    if 'cliente_id' not in session:
        return redirect(url_for('login_cliente'))

    datos_comprobante = session.get('ultimo_comprobante_compra')
    if not datos_comprobante:
        return redirect(url_for('dashboard_cliente'))

    return render_template('comprobante_compra_tdc.html', c=datos_comprobante)
@app.route('/cliente/transferencia', methods=['GET', 'POST'])
def transferencia():
    if not session.get('autorizado'):
        return redirect(url_for('acceso_portal'))
    if 'cliente_id' not in session:
        return redirect(url_for('login_cliente'))

    error = None
    if request.method == 'POST':
        ask_cuentadest = request.form.get('cuentadest', '').strip()
        session['cliente_destino'] = ask_cuentadest
        conn_usr = get_db_usr()
        try:
            cursor_usr = conn_usr.cursor()
            cursor_usr.execute("SELECT * FROM tabla_tar_usr WHERE numtaj=? OR clabe=?", (ask_cuentadest, ask_cuentadest))
            check_cuenta = cursor_usr.fetchone()

            if check_cuenta:
                nombre_rec_id = check_cuenta['ID']
                cursor_usr.execute("SELECT * FROM tabla_usr WHERE ID=?", (nombre_rec_id,))
                check_nombrerec = cursor_usr.fetchone()
                
                if check_nombrerec:
                    nombrecompl_rec = f"{check_nombrerec['nombre']} {check_nombrerec['apellidopat']} {check_nombrerec['apellidomat']}"
                    session['ID_recipiente'] = check_nombrerec['ID']
                    session['nombre_recipiente'] = nombrecompl_rec
                    return redirect(url_for('transferencia_datos'))

            error = "La cuenta o CLABE ingresada no existe."
        finally:
            conn_usr.close()

    return render_template('transferencia.html', error=error)

@app.route('/cliente/ingresar_dinero', methods=['GET', 'POST'])
def ingresar_dinero():
    if not session.get('autorizado'):
        return redirect(url_for('acceso_portal'))
    if 'cliente_id' not in session:
        return redirect(url_for('login_cliente'))

    conn_usr = get_db_usr()
    try:
        cursor_usr = conn_usr.cursor()
        cursor_usr.execute("SELECT * FROM tabla_tar_usr WHERE ID=?", (session['cliente_id'],))
        check_tarjeta_digital = cursor_usr.fetchone()
        
        cursor_usr.execute("SELECT * FROM tabla_usr WHERE ID=?", (session['cliente_id'],))
        check_nombre = cursor_usr.fetchone()

        if check_nombre and check_tarjeta_digital:
            nombre_compl = f"{check_nombre['nombre']} {check_nombre['apellidopat']} {check_nombre['apellidomat']}"
            session['numtaj_debito2'] = check_tarjeta_digital['numtaj']
            session['clabe_debito'] = check_tarjeta_digital['clabe']
            session['nombre_completo_usr'] = nombre_compl
    finally:
        conn_usr.close()

    return render_template('ingresar_dinero.html')

@app.route('/cliente/tdc', methods=['GET', 'POST'])
def tdc_cliente():
    if not session.get('autorizado'):
        return redirect(url_for('acceso_portal'))
    if 'cliente_id' not in session:
        return redirect(url_for('login_cliente'))

    error = None

    if request.method == 'POST':
        ask_ingresos_usr = request.form.get('ingresos_usr', '')
        ask_trabajo_usr = (request.form.get('ocupacion') or request.form.get('trabajo_usr') or '').lower()
        session['trabajo_cliente'] = ask_trabajo_usr

        try:
            ingresos = float(ask_ingresos_usr)
            session['ingresos_cliente'] = ingresos
        except (ValueError, TypeError):
            ingresos = -1.0

        if ingresos <= 0:
            error = "Ingrese un monto válido de ingresos."
        else:
            conn_empl = get_db_empl()
            conn_usr = get_db_usr()
            conn_trans = get_db_trans()
            try:
                cursor_empl = conn_empl.cursor()
                cursor_usr = conn_usr.cursor()
                cursor_trans = conn_trans.cursor()

                cursor_trans.execute("SELECT * FROM tabla_trans WHERE ID=?", (session['cliente_id'],))
                check_fraude = cursor_trans.fetchone()
                
                trabajo_fraude = ask_trabajo_usr in ["desempleado", "estudiante"]

                if check_fraude is None and trabajo_fraude:
                    status_tdc = "Denegada"
                    asig_exist = 3

                    cursor_usr.execute("SELECT nombre, apellidopat, apellidomat FROM tabla_usr WHERE ID=?", (session['cliente_id'],))
                    check_usr_tdc = cursor_usr.fetchone()
                    
                    nombrecompl = f"{check_usr_tdc['nombre']} {check_usr_tdc['apellidopat']} {check_usr_tdc['apellidomat']}" if check_usr_tdc else "Cliente Desconocido"

                    cursor_usr.execute("UPDATE tabla_tdc_usr SET exist=? WHERE ID=?", (asig_exist, session['cliente_id']))
                    
                    cursor_empl.execute(
                        "INSERT INTO tabla_tdc_emp(ID, nombre_compl, ingresos_men, ocupacion, status) VALUES(?, ?, ?, ?, ?)",
                        (session['cliente_id'], nombrecompl, str(session['ingresos_cliente']), session['trabajo_cliente'], status_tdc)
                    )

                    conn_usr.commit()
                    conn_empl.commit()
                    return redirect(url_for('tdc_denegada'))
                else:
                    return redirect(url_for('tdc_aviso'))
            finally:
                conn_empl.close()
                conn_trans.close()
                conn_usr.close()

    return render_template('tdc_cliente.html', error=error)

@app.route('/cliente/transferencia_datos', methods=['GET', 'POST'])
def transferencia_datos():
    if not session.get('autorizado'):
        return redirect(url_for('acceso_portal'))
    if 'cliente_id' not in session:
        return redirect(url_for('login_cliente'))

    error = None

    if request.method == 'POST':
        ask_transconc = request.form.get('transconc', '').strip()
        ask_transmont_raw = request.form.get('transmont', '').strip()
        session['concepto_trans'] = ask_transconc
        session['monto_trans'] = ask_transmont_raw

        try:
            monto = float(ask_transmont_raw)
        except (ValueError, TypeError):
            monto = 0.0

        if monto <= 0:
            error = "Ingresa un monto válido mayor a 0."
        else:
            conn_usr = get_db_usr()
            conn_trans = get_db_trans()
            try:
                cursor_usr = conn_usr.cursor()
                cursor_trans = conn_trans.cursor()

                cursor_usr.execute("SELECT saldo FROM tabla_usr WHERE ID=?", (session['cliente_id'],))
                check_saldo = cursor_usr.fetchone()

                if check_saldo and check_saldo['saldo'] >= monto:
                    saldo_act = check_saldo['saldo']

                    cursor_usr.execute("SELECT saldo FROM tabla_usr WHERE ID=?", (session['ID_recipiente'],))
                    check_saldo_rec = cursor_usr.fetchone()
                    saldo_act_rec = check_saldo_rec['saldo'] if check_saldo_rec else 0.0

                    saldo_nv = saldo_act - monto
                    saldo_nv_rec = saldo_act_rec + monto

                    fecha_hoy = datetime.datetime.now().strftime("%d/%m/%Y")
                    session['fecha_hoy'] = fecha_hoy

                    cursor_usr.execute("UPDATE tabla_usr SET saldo=? WHERE ID=?", (saldo_nv, session['cliente_id']))
                    cursor_usr.execute("UPDATE tabla_tar_usr SET saldo=? WHERE ID=?", (saldo_nv, session['cliente_id']))
                    cursor_usr.execute("UPDATE tabla_usr SET saldo=? WHERE ID=?", (saldo_nv_rec, session['ID_recipiente']))
                    cursor_usr.execute("UPDATE tabla_tar_usr SET saldo=? WHERE ID=?", (saldo_nv_rec, session['ID_recipiente']))

                    cursor_trans.execute(
                        "INSERT INTO tabla_trans (ID, transmont, transdest, transfech, transconc) VALUES(?, ?, ?, ?, ?)",
                        (session['cliente_id'], monto, session['cliente_destino'], fecha_hoy, ask_transconc)
                    )

                    conn_trans.commit()
                    conn_usr.commit()

                    return redirect(url_for('transferencia_aviso'))
                else:
                    error = "Saldo insuficiente para realizar la transferencia."

            finally:
                conn_usr.close()
                conn_trans.close()

    return render_template('transferencia_datos.html', error=error)

@app.route('/cliente/transferencia_aviso', methods=['GET', 'POST'])
def transferencia_aviso():
    if not session.get('autorizado'):
        return redirect(url_for('acceso_portal'))
    if 'cliente_id' not in session:
        return redirect(url_for('login_cliente'))

    conn_usr = get_db_usr()
    try:
        cursor_usr = conn_usr.cursor()
        cursor_usr.execute("SELECT numtaj FROM tabla_tar_usr WHERE ID=?", (session['cliente_id'],))
        check_tarjeta = cursor_usr.fetchone()

        if check_tarjeta:
            session['numtaj_trans'] = check_tarjeta['numtaj'][-4:]
    finally:
        conn_usr.close()

    numtaj_rec = session.get('cliente_destino', '')[-4:]
    session['numtaj_recipiente'] = numtaj_rec
    hora=datetime.datetime.now().strftime("%H:%M")
    session['hora']=hora
    return render_template('transferencia_aviso.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def login_admin():
    if not session.get('autorizado'):
        return redirect(url_for('acceso_portal'))
    error = None
    if request.method == 'POST':
        check_id_admin = request.form.get('id_admin', '').upper()
        check_contr_admin = request.form.get('contr_admin')
        
        conn = get_db_admin()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM reg_admin WHERE ID = ?", (check_id_admin,))
            usuario = cursor.fetchone()
        finally:
            conn.close()
        
        if usuario is None:
            error = "El usuario no existe."
        elif usuario['contr'] != check_contr_admin:
            error = "Contraseña incorrecta."
        else:
            session['admin_id'] = usuario['ID']
            session['admin_nombre'] = usuario['nombre']
            return redirect(url_for('dashboard_admin'))

    return render_template('login_admin.html', error=error)

@app.route('/cliente/tdc_denegada', methods=['GET', 'POST'])
def tdc_denegada():
    if not session.get('autorizado'):
        return redirect(url_for('acceso_portal'))
    if 'cliente_id' not in session:
        return redirect(url_for('login_cliente'))
    return render_template('tdc_denegada.html')

@app.route('/cliente/tdc_aviso', methods=['GET', 'POST'])
def tdc_aviso():
    if not session.get('autorizado'):
        return redirect(url_for('acceso_portal'))
    if 'cliente_id' not in session:
        return redirect(url_for('login_cliente'))
    
    ingresos = session.get('ingresos_cliente')
    trabajo = session.get('trabajo_cliente')

    if ingresos is None or trabajo is None:
        return redirect(url_for('tdc_cliente'))

    trabajo_good = trabajo in ["desempleado", "estudiante"]
    if trabajo_good:
        saldo_fav = ingresos * 0.6
    else:
        saldo_fav = ingresos * 0.8

    session['saldo_favor'] = saldo_fav
    return render_template('tdc_aviso.html')

@app.route('/cliente/tdc_fin', methods=['GET', 'POST'])
def tdc_fin():
    if not session.get('autorizado'):
        return redirect(url_for('acceso_portal'))
    if 'cliente_id' not in session:
        return redirect(url_for('login_cliente'))

    conn_usr = get_db_usr()
    conn_empl = get_db_empl()
    try:
        cursor_usr = conn_usr.cursor()
        cursor_empl = conn_empl.cursor()

        cursor_usr.execute("SELECT nombre, apellidopat, apellidomat FROM tabla_usr WHERE ID=?", (session['cliente_id'],))
        check_usr_tdc = cursor_usr.fetchone()
        
        if check_usr_tdc:
            nombrecompl = f"{check_usr_tdc['nombre']} {check_usr_tdc['apellidopat']} {check_usr_tdc['apellidomat']}"
        else:
            nombrecompl = "Cliente Desconocido"

        numtaj_tdc_com = f"{random.randint(5500, 5599)} {random.randint(4001, 4998)} {random.randint(5503, 5699)} {random.randint(7801, 7899)}"
        fech_ven_tdc_comp = f"{random.randint(1, 12):02d}/32"
        cvv_tdc = str(random.randint(100, 999))
        status_tdc = "Pendiente"
        asig_exist = 1
        saldo_contra = 0.0

        ingresos_val = session.get('ingresos_cliente', 0)
        trabajo_val = session.get('trabajo_cliente', '')
        saldo_favor_val = session.get('saldo_favor', 0.0)

        cursor_usr.execute(
            "UPDATE tabla_tdc_usr SET numtaj=?, fechavenc=?, cvv=?, nombre_compl=?, sald_fav=?, sald_contr=?, exist=? WHERE ID=?",
            (numtaj_tdc_com, fech_ven_tdc_comp, cvv_tdc, nombrecompl, saldo_favor_val, saldo_contra, asig_exist, session['cliente_id'])
        )

        cursor_empl.execute(
            "INSERT INTO tabla_tdc_emp(ID, nombre_compl, ingresos_men, ocupacion, numtaj, fechavenc, credito, status) VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
            (session['cliente_id'], nombrecompl, str(ingresos_val), trabajo_val, numtaj_tdc_com, fech_ven_tdc_comp, saldo_favor_val, status_tdc)
        )

        conn_usr.commit()
        conn_empl.commit()
    finally:
        conn_usr.close()
        conn_empl.close()
    return render_template('tdc_fin.html')

@app.route('/admin/dashboard')
def dashboard_admin():
    if not session.get('autorizado'):
        return redirect(url_for('acceso_portal'))
    if 'admin_id' not in session:
        return redirect(url_for('login_admin'))

    error = None
    conn_admin = get_db_admin()
    try:
        cursor_admin = conn_admin.cursor()
        cursor_admin.execute("SELECT * FROM reg_admin WHERE ID=?", (session['admin_id'],))
        check_datos_admin = cursor_admin.fetchone()
        nombre = check_datos_admin['nombre'] if check_datos_admin else ""
        session['bienvenida_nombre_admin'] = nombre
    finally:
        conn_admin.close()

    return render_template('dashboard_admin.html', error=error)
@app.route('/admin/crear_admin', methods=['GET', 'POST'])
def crear_admin():
    if not session.get('autorizado'):
        return redirect(url_for('acceso_portal'))
    if 'admin_id' not in session:
        return redirect(url_for('login_admin'))

    error = None
    if request.method == 'POST':
        ask_nombre_admin = request.form.get('nombre_admin', '').strip()
        ask_apellpat_admin = request.form.get('apellpat_admin', '').strip()
        ask_apellmat_admin = request.form.get('apellmat_admin', '').strip()
        ask_contr_admin = request.form.get('contr_admin', '').strip()

        if not (ask_nombre_admin and ask_apellpat_admin and ask_apellmat_admin):
            error = "Todos los campos de nombre y apellidos son obligatorios."
        elif len(ask_contr_admin) != 14:
            error = "La contraseña debe tener 14 dígitos."
        else:
            session['reg_nombre_admin'] = ask_nombre_admin
            session['reg_apellpat_admin'] = ask_apellpat_admin
            session['reg_apellmat_admin'] = ask_apellmat_admin
            session['reg_contr_admin'] = ask_contr_admin

            id_random = str(random.randint(10000, 19999))
            id_admin_comp = f"{ask_apellpat_admin[:2].upper()}{ask_apellmat_admin[0].upper()}{ask_nombre_admin[0].upper()}{id_random}"
            session['reg_id_admin'] = id_admin_comp

            conn_admin = get_db_admin()
            try:
                cursor_admin = conn_admin.cursor()
                cursor_admin.execute(
                    "INSERT INTO reg_admin(ID, contr, nombre, apellidopat, apellidomat) VALUES(?, ?, ?, ?, ?)",
                    (id_admin_comp, ask_contr_admin, ask_nombre_admin, ask_apellpat_admin, ask_apellmat_admin)
                )
                conn_admin.commit()
            finally:
                conn_admin.close()

            return redirect(url_for('crear_admin_aviso'))

    return render_template('crear_admin.html', error=error)


@app.route('/admin/crear_admin_aviso')
def crear_admin_aviso():
    if not session.get('autorizado'):
        return redirect(url_for('acceso_portal'))
    if 'admin_id' not in session:
        return redirect(url_for('login_admin'))

    return render_template('crear_admin_aviso.html')
@app.route('/admin/crear_empleado', methods=['GET', 'POST'])
def crear_empleado():
    if not session.get('autorizado'):
        return redirect(url_for('acceso_portal'))
    if 'admin_id' not in session:
        return redirect(url_for('login_admin'))

    error = None
    if request.method == 'POST':
        ask_nombre_empleado = request.form.get('nombre_empleado', '').strip()
        ask_apellpat_empleado = request.form.get('apellpat_empleado', '').strip()
        ask_apellmat_empleado = request.form.get('apellmat_empleado', '').strip()
        ask_contr_empleado = request.form.get('contr_empleado', '').strip()

        if not (ask_nombre_empleado and ask_apellpat_empleado and ask_apellmat_empleado):
            error = "Todos los campos de nombre y apellidos son obligatorios."
        elif len(ask_contr_empleado) != 12:
            error = "La contraseña debe tener 12 dígitos."
        else:
            session['reg_nombre_empleado'] = ask_nombre_empleado
            session['reg_apellpat_empleado'] = ask_apellpat_empleado
            session['reg_apellmat_empleado'] = ask_apellmat_empleado
            session['reg_contr_empleado'] = ask_contr_empleado

            id_random = str(random.randint(20000, 29999))
            id_empleado_comp = f"{ask_apellpat_empleado[:2].upper()}{ask_apellmat_empleado[0].upper()}{ask_nombre_empleado[0].upper()}{id_random}"
            session['reg_id_empleado'] = id_empleado_comp

            conn_empl = get_db_empl()
            try:
                cursor_empl = conn_empl.cursor()
                cursor_empl.execute(
                    "INSERT INTO tabla_emp(ID, contr, nombre, apellidopat, apellidomat) VALUES(?, ?, ?, ?, ?)",
                    (id_empleado_comp, ask_contr_empleado, ask_nombre_empleado, ask_apellpat_empleado, ask_apellmat_empleado)
                )
                conn_empl.commit()
            finally:
                conn_empl.close()

            return redirect(url_for('crear_empleado_aviso'))

    return render_template('crear_empleado.html', error=error)


@app.route('/admin/crear_empleado_aviso')
def crear_empleado_aviso():
    if not session.get('autorizado'):
        return redirect(url_for('acceso_portal'))
    if 'admin_id' not in session:
        return redirect(url_for('login_admin'))

    return render_template('crear_empleado_aviso.html')
@app.route('/admin/crear_operador', methods=['GET', 'POST'])
def crear_operador():
    if not session.get('autorizado'):
        return redirect(url_for('acceso_portal'))
    if 'admin_id' not in session:
        return redirect(url_for('login_admin'))

    error = None
    if request.method == 'POST':
        ask_nombre_operador = request.form.get('nombre_operador', '').strip()
        ask_apellpat_operador = request.form.get('apellpat_operador', '').strip()
        ask_apellmat_operador = request.form.get('apellmat_operador', '').strip()
        ask_contr_operador = request.form.get('contr_operador', '').strip()
        ask_empresa_operador = request.form.get('empresa_operador', '').strip()

        empresas_validas = ['DHL', 'FedEx', 'Estafeta']

        if not (ask_nombre_operador and ask_apellpat_operador and ask_apellmat_operador):
            error = "Todos los campos de nombre y apellidos son obligatorios."
        elif ask_empresa_operador not in empresas_validas:
            error = "Seleccione una empresa de paquetería válida (DHL, FedEx o Estafeta)."
        elif len(ask_contr_operador) != 10:
            error = "La contraseña debe tener exactamente 10 dígitos numéricos."
        else:
            session['reg_nombre_operador'] = ask_nombre_operador
            session['reg_apellpat_operador'] = ask_apellpat_operador
            session['reg_apellmat_operador'] = ask_apellmat_operador
            session['reg_contr_operador'] = ask_contr_operador
            session['reg_empresa_operador'] = ask_empresa_operador

            id_random = str(random.randint(30000, 39999))
            id_operador_comp = f"{ask_apellpat_operador[:2].upper()}{ask_apellmat_operador[0].upper()}{ask_nombre_operador[0].upper()}{id_random}"
            session['reg_id_operador'] = id_operador_comp

            conn_oper = get_db_oper()
            try:
                cursor_oper = conn_oper.cursor()
                cursor_oper.execute(
                    "INSERT INTO tabla_oper_id(ID, contr, nombre, apellidopat, apellidomat, empresa) VALUES(?, ?, ?, ?, ?, ?)",
                    (id_operador_comp, ask_contr_operador, ask_nombre_operador, ask_apellpat_operador, ask_apellmat_operador, ask_empresa_operador)
                )
                conn_oper.commit()
            finally:
                conn_oper.close()

            return redirect(url_for('crear_operador_aviso'))

    return render_template('crear_operador.html', error=error)


@app.route('/admin/crear_operador_aviso')
def crear_operador_aviso():
    if not session.get('autorizado'):
        return redirect(url_for('acceso_portal'))
    if 'admin_id' not in session:
        return redirect(url_for('login_admin'))

    if 'reg_id_operador' not in session:
        return redirect(url_for('crear_operador'))

    return render_template('crear_operador_aviso.html')
@app.route('/admin/consultar_cuentas', methods=['GET', 'POST'])
def consultar_cuentas():
    if not session.get('autorizado'):
        return redirect(url_for('acceso_portal'))
    if 'admin_id' not in session:
        return redirect(url_for('login_admin'))

    error = None
    if request.method == 'POST':
        ask_consultarcuenta_admin = request.form.get('consultarcuenta_admin', '').strip()
        
        conn = get_db_usr()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tabla_usr WHERE ID = ?", (ask_consultarcuenta_admin,))
            check_usr = cursor.fetchone()

            if check_usr is None:
                error = "El usuario ingresado no existe."
            else:
                session['consultar_cuenta_admin'] = ask_consultarcuenta_admin
                return redirect(url_for('consultar_cuentas_result'))
        finally:
            conn.close()

    return render_template('consultar_cuentas.html', error=error)


@app.route('/admin/consultar_cuentas_result', methods=['GET', 'POST'])
def consultar_cuentas_result():
    if not session.get('autorizado'):
        return redirect(url_for('acceso_portal'))
    if 'admin_id' not in session:
        return redirect(url_for('login_admin'))

    id_consulta = session.get('consultar_cuenta_admin')
    if not id_consulta:
        return redirect(url_for('consultar_cuentas'))

    datos_usr = {}
    conn = get_db_usr()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tabla_usr WHERE ID = ?", (id_consulta,))
        check_usr = cursor.fetchone()

        if not check_usr:
            return redirect(url_for('consultar_cuentas'))

        cursor.execute("SELECT * FROM tabla_tar_usr WHERE ID = ?", (id_consulta,))
        check_tar = cursor.fetchone()

        nombre_compl = f"{check_usr[2]} {check_usr[3]} {check_usr[4]}".strip()
        datos_usr = {
            'id': check_usr[0],
            'nombre': nombre_compl,
            'edad': check_usr[5] if len(check_usr) > 5 else '',
            'curp': check_usr[6] if len(check_usr) > 6 else '',
            'tarjetanum': check_tar[0] if check_tar else 'Sin tarjeta',
            'fechavenc': check_tar[1] if check_tar else 'N/A',
            'clabe': check_tar[3] if check_tar else 0.0
        }

        session['datos_cuenta_consultada'] = datos_usr
    finally:
        conn.close()

    return render_template('consultar_cuentas_result.html', usuario=datos_usr)
@app.route('/admin/consultar_movimientos', methods=['GET', 'POST'])
def consultar_movimientos():
    if not session.get('autorizado'):
        return redirect(url_for('acceso_portal'))
    if 'admin_id' not in session:
        return redirect(url_for('login_admin'))

    error = None
    if request.method == 'POST':
        ask_consultarmov_admin = request.form.get('consultarmov_admin', '').strip()
        
        conn = get_db_usr()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tabla_usr WHERE ID = ?", (ask_consultarmov_admin,))
            check_usr = cursor.fetchone()

            if check_usr is None:
                error = "El usuario ingresado no existe."
            else:
                session['consultar_mov_admin'] = ask_consultarmov_admin
                return redirect(url_for('consultar_movimientos_result'))
        finally:
            conn.close()
    return render_template('consultar_movimientos.html', error=error)
@app.route('/admin/consultar_movimientos_result')
def consultar_movimientos_result():
    if not session.get('autorizado'):
        return redirect(url_for('acceso_portal'))
    if 'admin_id' not in session:
        return redirect(url_for('login_admin'))

    error = None
    conn_trans = get_db_trans()
    try:
        cursor_trans = conn_trans.cursor()
        cursor_trans.execute("SELECT transmont, transdest, transfech, transconc FROM tabla_trans WHERE ID=?", (session['consultar_mov_admin'],))
        check_mov = cursor_trans.fetchall()
        movimientos_limpios = [dict(fila) for fila in check_mov]
        session['movimientos_admin'] = movimientos_limpios
    finally:
        conn_trans.close()
    return render_template('consultar_movimientos_result.html', error=error)    
@app.route('/admin/calendario_admin')
def calendario_admin():
    if not session.get('autorizado'):
        return redirect(url_for('acceso_portal'))
    if 'admin_id' not in session:
        return redirect(url_for('login_admin'))

    error = None
    conn = get_db_oper()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT calle, numcalle, colonia, ciudad, estado, CP, detalles, nombre_cli FROM tabla_oper")
        check_co = cursor.fetchall()
        co_limpios = [dict(fila) for fila in check_co]
        session['calendario_admin'] = co_limpios
    finally:
        conn.close()
    return render_template('calendario_admin.html', error=error)
@app.route('/admin/consultar_empleados')
def consultar_empleados():
    if not session.get('autorizado'):
        return redirect(url_for('acceso_portal'))
    if 'admin_id' not in session:
        return redirect(url_for('login_admin'))

    error = None
    conn = get_db_empl()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT ID, contr, nombre, apellidopat, apellidomat FROM tabla_emp")
        check_emp = cursor.fetchall()
        emp_limpios = [dict(fila) for fila in check_emp]
        session['empleados_admin'] = emp_limpios
    finally:
        conn.close()
    return render_template('consultar_empleados.html', error=error)
@app.route('/admin/consultar_operadores')
def consultar_operadores():
    if not session.get('autorizado'):
        return redirect(url_for('acceso_portal'))
    if 'admin_id' not in session:
        return redirect(url_for('login_admin'))

    error = None
    conn = get_db_oper()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT ID, contr, nombre, apellidopat, apellidomat, empresa FROM tabla_oper_id")
        check_opr = cursor.fetchall()
        opr_limpios = [dict(fila) for fila in check_opr]
        session['operadores_admin'] = opr_limpios
    finally:
        conn.close()
    return render_template('consultar_operadores.html', error=error)
@app.route('/admin/gerencia_empleados', methods=['GET', 'POST'])
def gerencia_empleados():
    if not session.get('autorizado'):
        return redirect(url_for('acceso_portal'))
    if 'admin_id' not in session:
        return redirect(url_for('login_admin'))

    error = None
    if request.method == 'POST':
        ask_ger_emp = request.form.get('idger_empadmin', '').strip()
        ask_contrger_emp = request.form.get('contrger_empadmin', '').strip()

        if not ask_ger_emp or not ask_contrger_emp:
            error = "Todos los campos son obligatorios."
        elif len(ask_contrger_emp)!=6:
            error="La contraseña debe tener 6 digitos"
        else:
            conn = get_db_admin()
            conn2 = get_db_empl()
            try:
                cursor = conn.cursor()
                cursor2 = conn2.cursor()

                cursor2.execute("SELECT * FROM tabla_emp WHERE ID=?", (ask_ger_emp,))
                check_emp = cursor2.fetchone()

                if check_emp is None:
                    error = "El empleado no existe en la base de datos."
                else:
                    nom = check_emp['nombre'] if hasattr(check_emp, 'keys') else check_emp[2]
                    pat = check_emp['apellidopat'] if hasattr(check_emp, 'keys') else check_emp[3]
                    mat = check_emp['apellidomat'] if hasattr(check_emp, 'keys') else check_emp[4]
                    nombrecompl_geremp = f"{nom} {pat} {mat}"

                    cursor.execute(
                        "INSERT INTO reg_ger_emp(ID, contr, nombre_compl) VALUES(?, ?, ?)",
                        (ask_ger_emp, ask_contrger_emp, nombrecompl_geremp)
                    )
                    conn.commit()
                    return redirect(url_for('gerencia_avisoemp'))
            finally:
                conn2.close()
                conn.close()

    return render_template('gerencia_empleados.html', error=error)

@app.route('/admin/gerencia_avisoemp')
def gerencia_avisoemp():
    if not session.get('autorizado'):
        return redirect(url_for('acceso_portal'))
    if 'admin_id' not in session:
        return redirect(url_for('login_admin'))

    error = None
    return render_template('gerencia_avisoemp.html', error=error)

@app.route('/admin/gerencia_avisoopr')
def gerencia_avisoopr():
    if not session.get('autorizado'):
        return redirect(url_for('acceso_portal'))
    if 'admin_id' not in session:
        return redirect(url_for('login_admin'))

    error = None
    return render_template('gerencia_avisoopr.html', error=error)
@app.route('/admin/gerencia_operadores', methods=['GET', 'POST'])
def gerencia_operadores():
    if not session.get('autorizado'):
        return redirect(url_for('acceso_portal'))
    if 'admin_id' not in session:
        return redirect(url_for('login_admin'))

    error = None
    if request.method == 'POST':
        ask_ger_opr = request.form.get('idopr_empadmin', '').strip()
        ask_contrger_opr = request.form.get('contropr_empadmin', '').strip()

        if not ask_ger_opr or not ask_contrger_opr:
            error = "Todos los campos son obligatorios."
        elif len(ask_contrger_opr)!=6:
            error="La contraseña debe tener 6 digitos"
        else:
            conn = get_db_admin()
            conn2 = get_db_oper()
            try:
                cursor = conn.cursor()
                cursor2 = conn2.cursor()
                cursor2.execute("SELECT * FROM tabla_oper_id WHERE ID=?", (ask_ger_opr,))
                check_opr = cursor2.fetchone()

                if check_opr is None:
                    error = "El operador no existe en la base de datos."
                else:
                    nom = check_opr['nombre'] if hasattr(check_opr, 'keys') else check_opr[2]
                    pat = check_opr['apellidopat'] if hasattr(check_opr, 'keys') else check_opr[3]
                    mat = check_opr['apellidomat'] if hasattr(check_opr, 'keys') else check_opr[4]
                    nombrecompl_geropr = f"{nom} {pat} {mat}"

                    cursor.execute(
                        "INSERT INTO reg_ger_oper(ID, contr, nombre_compl) VALUES(?, ?, ?)",
                        (ask_ger_opr, ask_contrger_opr, nombrecompl_geropr)
                    )
                    conn.commit()
                    return redirect(url_for('gerencia_avisoopr'))
            finally:
                conn2.close()
                conn.close()

    return render_template('gerencia_operadores.html', error=error)
@app.route('/admin/money_tool', methods=['GET', 'POST'])
def money_tool():
    if not session.get('autorizado'):
        return redirect(url_for('acceso_portal'))
    if 'admin_id' not in session:
        return redirect(url_for('login_admin'))

    error = None
    if request.method == 'POST':
        ask_cuentamt = request.form.get('cuentamt', '').strip()
        session['cliente_mt'] = ask_cuentamt
        
        conn_usr = get_db_usr()
        try:
            cursor_usr = conn_usr.cursor()
            cursor_usr.execute("SELECT * FROM tabla_tar_usr WHERE numtaj=? OR clabe=?", (ask_cuentamt, ask_cuentamt))
            check_cuenta = cursor_usr.fetchone()

            if check_cuenta:
                nombre_rec_id = check_cuenta['ID'] if isinstance(check_cuenta, dict) or hasattr(check_cuenta, 'keys') else check_cuenta[0]
                
                cursor_usr.execute("SELECT * FROM tabla_usr WHERE ID=?", (nombre_rec_id,))
                check_nombrerec = cursor_usr.fetchone()
                
                if check_nombrerec:
                    nom = check_nombrerec['nombre'] if hasattr(check_nombrerec, 'keys') else check_nombrerec[2]
                    pat = check_nombrerec['apellidopat'] if hasattr(check_nombrerec, 'keys') else check_nombrerec[3]
                    mat = check_nombrerec['apellidomat'] if hasattr(check_nombrerec, 'keys') else check_nombrerec[4]
                    
                    session['ID_recipientemt'] = check_nombrerec['ID'] if hasattr(check_nombrerec, 'keys') else check_nombrerec[0]
                    session['nombre_recipientemt'] = f"{nom} {pat} {mat}"
                    return redirect(url_for('moneytool_datos'))

            error = "La cuenta o CLABE ingresada no existe."
        finally:
            conn_usr.close()

    return render_template('money_tool.html', error=error)


@app.route('/admin/moneytool_datos', methods=['GET', 'POST'])
def moneytool_datos():
    if not session.get('autorizado'):
        return redirect(url_for('acceso_portal'))
    if 'admin_id' not in session:
        return redirect(url_for('login_admin'))
    id_recipiente = session.get('ID_recipientemt')
    if not id_recipiente:
        return redirect(url_for('money_tool'))

    error = None

    if request.method == 'POST':
        ask_transmont_mt = request.form.get('transmontmt', '').strip()
        
        try:
            monto = float(ask_transmont_mt)
        except (ValueError, TypeError):
            monto = 0.0

        if monto <= 0:
            error = "Ingresa un monto válido mayor a $0.00."
        else:
            session['monto_transmt'] = monto
            conn_usr = get_db_usr()

            try:
                cursor_usr = conn_usr.cursor()
                cursor_usr.execute("SELECT saldo FROM tabla_usr WHERE ID=?", (id_recipiente,))
                check_saldo_rec = cursor_usr.fetchone()

                if not check_saldo_rec:
                    error = "El destinatario ya no existe en el sistema."
                else:
                    saldo_act = check_saldo_rec['saldo'] if hasattr(check_saldo_rec, 'keys') else check_saldo_rec[0]
                    saldo_act_rec = saldo_act if saldo_act is not None else 0.0
                    saldo_nv_rec = saldo_act_rec + monto
                    cursor_usr.execute("UPDATE tabla_usr SET saldo=? WHERE ID=?", (saldo_nv_rec, id_recipiente))
                    cursor_usr.execute("UPDATE tabla_tar_usr SET saldo=? WHERE ID=?", (saldo_nv_rec, id_recipiente))

                    conn_usr.commit()
                    return redirect(url_for('moneytool_aviso'))

            finally:
                conn_usr.close()

    return render_template('moneytool_datos.html', error=error)


@app.route('/admin/moneytool_aviso', methods=['GET', 'POST'])
def moneytool_aviso():
    if not session.get('autorizado'):
        return redirect(url_for('acceso_portal'))
    if 'admin_id' not in session:
        return redirect(url_for('login_admin'))

    return render_template('moneytool_aviso.html')
@app.route('/login/empleado', methods=['GET', 'POST'])
def login_empleado():
    if not session.get('autorizado'):
        return redirect(url_for('acceso_portal'))
        
    error = None
    if request.method == 'POST':
        check_id_empleado = request.form.get('id_empleado', '').upper()
        check_contr_empleado = request.form.get('contr_empleado')
        
        conn = get_db_empl()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tabla_emp WHERE ID = ?", (check_id_empleado,))
            usuario = cursor.fetchone()
        finally:
            conn.close()
        
        if usuario is None:
            error = "El usuario no existe."
        elif usuario['contr'] != check_contr_empleado:
            error = "Contraseña incorrecta."
        else:
            session['empleado_id'] = usuario['ID']
            session['empleado_nombre'] = usuario['nombre']
            return redirect(url_for('dashboard_empleado'))

    return render_template('login_empleado.html', error=error)

@app.route('/empleado/dashboard')
def dashboard_empleado():
    if not session.get('autorizado'):
        return redirect(url_for('acceso_portal'))
    if 'empleado_id' not in session:
        return redirect(url_for('login_empleado'))

    error = None
    conn = get_db_empl()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tabla_emp WHERE ID=?", (session['empleado_id'],))
        check_datos_emp = cursor.fetchone()

        nombre = check_datos_emp['nombre'] if check_datos_emp else ""
        
        session['bienvenida_nombre_empleado'] = nombre
    finally:
        conn.close()

    return render_template('dashboard_empleado.html', error=error)
@app.route('/empleado/calendario_empleado')
def calendario_empleado():
    if not session.get('autorizado'):
        return redirect(url_for('acceso_portal'))
    if 'empleado_id' not in session:
        return redirect(url_for('login_empleado'))

    error = None
    conn = get_db_oper()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT calle, numcalle, colonia, ciudad, estado, CP, detalles, nombre_cli FROM tabla_oper")
        check_co = cursor.fetchall()
        co_limpios = [dict(fila) for fila in check_co]
        session['calendario_empleado'] = co_limpios
    finally:
        conn.close()
    return render_template('calendario_empleado.html', error=error)
@app.route('/empleado/consultar_cuentasemp', methods=['GET', 'POST'])
def consultar_cuentasemp():
    if not session.get('autorizado'):
        return redirect(url_for('acceso_portal'))
    if 'empleado_id' not in session:
        return redirect(url_for('login_empleado'))

    error = None
    if request.method == 'POST':
        ask_consultarcuenta_emp = request.form.get('consultarcuenta_emp', '').strip()
        
        conn = get_db_usr()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tabla_usr WHERE ID = ?", (ask_consultarcuenta_emp,))
            check_usr = cursor.fetchone()

            if check_usr is None:
                error = "El usuario ingresado no existe."
            else:
                session['consultar_cuenta_empleado'] = ask_consultarcuenta_emp
                return redirect(url_for('consultar_cuentasemp_result'))
        finally:
            conn.close()

    return render_template('consultar_cuentasemp.html', error=error)


@app.route('/admin/consultar_cuentasemp_result', methods=['GET', 'POST'])
def consultar_cuentasemp_result():
    if not session.get('autorizado'):
        return redirect(url_for('acceso_portal'))
    if 'empleado_id' not in session:
        return redirect(url_for('login_empleado'))

    id_consulta = session.get('consultar_cuenta_empleado')
    if not id_consulta:
        return redirect(url_for('consultar_cuentasemp'))

    datos_usr = {}
    conn = get_db_usr()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tabla_usr WHERE ID = ?", (id_consulta,))
        check_usr = cursor.fetchone()

        if not check_usr:
            return redirect(url_for('consultar_cuentasemp'))

        cursor.execute("SELECT * FROM tabla_tar_usr WHERE ID = ?", (id_consulta,))
        check_tar = cursor.fetchone()

        nombre_compl = f"{check_usr[2]} {check_usr[3]} {check_usr[4]}".strip()
        datos_usr = {
            'id': check_usr[0],
            'nombre': nombre_compl,
            'tarjetanum': check_tar[0] if check_tar else 'Sin tarjeta',
            'fechavenc': check_tar[1] if check_tar else 'N/A',
            'clabe': check_tar[3] if check_tar else 0.0
        }

        session['datos_cuenta_consultadaemp'] = datos_usr
    finally:
        conn.close()

    return render_template('consultar_cuentasemp_result.html', usuario=datos_usr)
@app.route('/empleado/tdc_apro_lista', methods=['GET', 'POST'])
def tdc_apro_lista():
    if not session.get('autorizado'):
        return redirect(url_for('acceso_portal'))
    if 'empleado_id' not in session:
        return redirect(url_for('login_empleado'))

    error = None

    if request.method == 'POST':
        id_usr = request.form.get('id_usr', '').strip().upper()

        if not id_usr:
            error = "Por favor, ingrese el ID del usuario."
        else:
            conn_empl = get_db_empl()
            try:
                cursor_empl = conn_empl.cursor()
                cursor_empl.execute("SELECT * FROM tabla_tdc_emp WHERE ID=? AND status='Pendiente'", (id_usr,))
                solicitud = cursor_empl.fetchone()

                if not solicitud:
                    error = f"El ID '{id_usr}' no existe o no tiene solicitudes pendientes."
                else:
                    return redirect(url_for('tdc_apro_detalle', id_usr=id_usr))
            finally:
                conn_empl.close()

    conn_empl = get_db_empl()
    try:
        cursor_empl = conn_empl.cursor()
        cursor_empl.execute("SELECT * FROM tabla_tdc_emp WHERE status='Pendiente'")
        pendientes = cursor_empl.fetchall()
    finally:
        conn_empl.close()

    return render_template('tdc_apro_lista.html', solicitudes=pendientes, error=error)


@app.route('/empleado/tdc_apro_detalle/<id_usr>', methods=['GET', 'POST'])
def tdc_apro_detalle(id_usr):
    if not session.get('autorizado'):
        return redirect(url_for('acceso_portal'))
    if 'empleado_id' not in session:
        return redirect(url_for('login_empleado'))

    error = None

    if request.method == 'POST':
        decision = request.form.get('decision', '').strip().lower() # 'a' o 'r'
        razon = request.form.get('razon', '').strip()

        if decision not in ['a', 'r']:
            error = "Selección de decisión inválida."
        else:
            sts_emp_tdc = "Aprobada" if decision == "a" else "Rechazada"

            conn_usr = get_db_usr()
            conn_empl = get_db_empl()
            try:
                cursor_usr = conn_usr.cursor()
                cursor_empl = conn_empl.cursor()

                cursor_usr.execute("UPDATE tabla_tdc_usr SET exist=? WHERE ID=?", (2, id_usr))
                conn_usr.commit()

                cursor_empl.execute(
                    "UPDATE tabla_tdc_emp SET status=?, razon=? WHERE ID=?",
                    (sts_emp_tdc, razon, id_usr)
                )
                conn_empl.commit()

                flash(f"La cuenta {id_usr} fue procesada como: {sts_emp_tdc}.")
                return redirect(url_for('tdc_apro_lista'))
            finally:
                conn_usr.close()
                conn_empl.close()

    conn_empl = get_db_empl()
    conn_usr = get_db_usr()
    try:
        cursor_empl = conn_empl.cursor()
        cursor_usr = conn_usr.cursor()

        cursor_empl.execute("SELECT * FROM tabla_tdc_emp WHERE ID=?", (id_usr,))
        solicitud_emp = cursor_empl.fetchone()

        cursor_usr.execute("SELECT * FROM tabla_usr WHERE ID=?", (id_usr,))
        datos_usr = cursor_usr.fetchone()

        if not solicitud_emp:
            flash("No se encontró la información de la solicitud.")
            return redirect(url_for('tdc_apro_lista'))
    finally:
        conn_empl.close()
        conn_usr.close()

    return render_template('tdc_apro_detalle.html', solicitud=solicitud_emp, usuario=datos_usr, error=error)
@app.route('/login/empleadoger', methods=['GET', 'POST'])
def login_empleadoger():
    if not session.get('autorizado'):
        return redirect(url_for('acceso_portal'))
    if 'empleado_id' not in session:
        return redirect(url_for('login_empleado'))
    error = None
    if request.method == 'POST':
        check_id_empleadoger = request.form.get('id_empleadoger', '').upper()
        check_contr_empleadoger = request.form.get('contr_empleadoger')
        
        conn = get_db_admin()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM reg_ger_emp WHERE ID = ?", (check_id_empleadoger,))
            usuarioger = cursor.fetchone()
        finally:
            conn.close()
        
        if usuarioger is None:
            error = "El usuario no existe."
        elif usuarioger['contr'] != check_contr_empleadoger:
            error = "Contraseña incorrecta."
        else:
            session['empleadoger_id'] = usuarioger['ID']
            return redirect(url_for('portal_ger_empleado'))

    return render_template('login_empleadoger.html', error=error)
@app.route('/gerencia/empleados')
def portal_ger_empleado():
    if not session.get('autorizado'):
        return redirect(url_for('acceso_portal'))
    if 'empleadoger_id' not in session:
        return redirect(url_for('login_empleadoger'))
    return render_template('gerencia_menu_emp.html')


@app.route('/gerencia/empleados/alta', methods=['GET', 'POST'])
def gerencia_alta_emp():
    if not session.get('autorizado'):
        return redirect(url_for('acceso_portal'))
    if 'empleadoger_id' not in session:
        return redirect(url_for('login_empleadoger'))

    error = None

    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        apellpat = request.form.get('apellpat', '').strip()
        apellmat = request.form.get('apellmat', '').strip()
        contr = request.form.get('contr', '').strip()

        if len(nombre) < 3 or len(apellpat) <= 3 or len(apellmat) <= 3:
            error = "El nombre debe tener al menos 3 caracteres y cada apellido más de 3 caracteres."
        elif len(contr) != 12:
            error = "La contraseña debe tener exactamente 12 dígitos."
        else:
            id_rand = str(random.randint(30000, 39999))
            id_empl_comp = f"{apellpat[:2].upper()}{apellmat[0].upper()}{nombre[0].upper()}{id_rand}"

            conn_empl = get_db_empl()
            try:
                cursor_empl = conn_empl.cursor()
                cursor_empl.execute(
                    "INSERT INTO tabla_emp(ID, contr, nombre, apellidopat, apellidomat) VALUES(?, ?, ?, ?, ?)",
                    (id_empl_comp, contr, nombre, apellpat, apellmat)
                )
                conn_empl.commit()
                # Redirige a la nueva función creada
                return redirect(url_for('gerencia_aviso_alta_emp'))
            except Exception as e:
                error = f"Error en la base de datos: {e}"
            finally:
                conn_empl.close()

    return render_template('gerencia_alta_emp.html', error=error)

@app.route('/gerencia/empleados/aviso_alta')
def gerencia_aviso_alta_emp():
    if not session.get('autorizado'):
        return redirect(url_for('acceso_portal'))
    if 'empleadoger_id' not in session:
        return redirect(url_for('login_empleadoger'))
    return render_template('gerencia_aviso_alta_emp.html')


@app.route('/gerencia/empleados/baja', methods=['GET', 'POST'])
def gerencia_baja_emp():
    if not session.get('autorizado'):
        return redirect(url_for('acceso_portal'))
    if 'empleadoger_id' not in session:
        return redirect(url_for('login_empleadoger'))

    error = None
    exito = None

    if request.method == 'POST':
        emp_baja = request.form.get('id_emp_baja', '').strip().upper()

        if not emp_baja:
            error = "Debe ingresar o seleccionar un ID de empleado."
        else:
            conn_empl = get_db_empl()
            try:
                cursor_empl = conn_empl.cursor()
                cursor_empl.execute("SELECT * FROM tabla_emp WHERE ID=?", (emp_baja,))
                check_emp = cursor_empl.fetchone()

                if not check_emp:
                    error = f"El empleado con ID '{emp_baja}' no existe."
                else:
                    cursor_empl.execute("DELETE FROM tabla_emp WHERE ID=?", (emp_baja,))
                    conn_empl.commit()
                    exito = f"El empleado {check_emp['nombre']} {check_emp['apellidopat']} ({emp_baja}) ha sido dado de baja."
            finally:
                conn_empl.close()

    conn_empl = get_db_empl()
    try:
        cursor_empl = conn_empl.cursor()
        cursor_empl.execute("SELECT * FROM tabla_emp")
        lista_empleados = cursor_empl.fetchall()
    finally:
        conn_empl.close()

    return render_template('gerencia_baja_emp.html', empleados=lista_empleados, error=error, exito=exito)
@app.route('/login/operador', methods=['GET', 'POST'])
def login_operador():
    if not session.get('autorizado'):
        return redirect(url_for('acceso_portal'))
        
    error = None
    if request.method == 'POST':
        check_id_operador = request.form.get('id_operador', '').upper()
        check_contr_operador = request.form.get('contr_operador')
        
        conn = get_db_oper()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tabla_oper_id WHERE ID = ?", (check_id_operador,))
            usuario = cursor.fetchone()
        finally:
            conn.close()
        
        if usuario is None:
            error = "El usuario no existe."
        elif usuario['contr'] != check_contr_operador:
            error = "Contraseña incorrecta."
        else:
            session['operador_id'] = usuario['ID']
            session['operador_nombre'] = usuario['nombre']
            session['operador_empresa']= usuario['empresa']
            return redirect(url_for('dashboard_operador'))

    return render_template('login_operador.html', error=error)

@app.route('/operador/dashboard')
def dashboard_operador():
    if not session.get('autorizado'):
        return redirect(url_for('acceso_portal'))
    if 'operador_id' not in session:
        return redirect(url_for('login_operador'))

    error = None
    conn = get_db_oper()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tabla_oper_id WHERE ID=?", (session['operador_id'],))
        check_datos_opr = cursor.fetchone()

        nombre = check_datos_opr['nombre'] if check_datos_opr else ""
        empresa=check_datos_opr['empresa'] if check_datos_opr else ""
        session['bienvenida_empresa_operador']=empresa
        session['bienvenida_nombre_operador'] = nombre
    finally:
        conn.close()

    return render_template('dashboard_operador.html', error=error)
@app.route('/operador/calendario_operador')
def calendario_operador():
    if not session.get('autorizado'):
        return redirect(url_for('acceso_portal'))
    if 'operador_id' not in session:
        return redirect(url_for('login_operador'))

    error = None
    conn = get_db_oper()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT calle, numcalle, colonia, ciudad, estado, CP, detalles, nombre_cli FROM tabla_oper")
        check_co = cursor.fetchall()
        co_limpios = [dict(fila) for fila in check_co]
        session['calendario_operador'] = co_limpios
    finally:
        conn.close()
    return render_template('calendario_operador.html', error=error)
@app.route('/login/operadorger', methods=['GET', 'POST'])
def login_operadorger():
    if not session.get('autorizado'):
        return redirect(url_for('acceso_portal'))
    if 'operador_id' not in session:
        return redirect(url_for('login_operador'))
    error = None
    if request.method == 'POST':
        check_id_operadorger = request.form.get('id_operadorger', '').upper()
        check_contr_operadorger = request.form.get('contr_operadorger')
        
        conn = get_db_admin()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM reg_ger_oper WHERE ID = ?", (check_id_operadorger,))
            usuarioger = cursor.fetchone()
        finally:
            conn.close()
        
        if usuarioger is None:
            error = "El usuario no existe."
        elif usuarioger['contr'] != check_contr_operadorger:
            error = "Contraseña incorrecta."
        else:
            session['operadorger_id'] = usuarioger['ID']
            return redirect(url_for('portal_ger_operador'))

    return render_template('login_operadorger.html', error=error)
@app.route('/gerencia/operadores')
def portal_ger_operador():
    if not session.get('autorizado'):
        return redirect(url_for('acceso_portal'))
    if 'operadorger_id' not in session:
        return redirect(url_for('login_operadorger'))
    return render_template('gerencia_menu_oper.html')


@app.route('/gerencia/operadores/alta', methods=['GET', 'POST'])
def gerencia_alta_oper():
    if not session.get('autorizado'):
        return redirect(url_for('acceso_portal'))
    if 'operadorger_id' not in session:
        return redirect(url_for('login_operadorger'))
    error = None

    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        apellpat = request.form.get('apellpat', '').strip()
        apellmat = request.form.get('apellmat', '').strip()
        contr = request.form.get('contr', '').strip()
        empresa=request.form.get('empresa_operador', '').strip()

        if len(nombre) <= 3 or len(apellpat) <= 3 or len(apellmat) <= 3:
            error = "El nombre debe tener al menos 3 caracteres y cada apellido más de 3 caracteres."
        elif len(contr) != 10:
            error = "La contraseña debe tener exactamente 10 dígitos."
        else:
            id_rand = str(random.randint(30000, 39999))
            id_oper_comp = f"{apellpat[:2].upper()}{apellmat[0].upper()}{nombre[0].upper()}{id_rand}"

            conn_empl = get_db_oper()
            try:
                cursor_empl = conn_empl.cursor()
                cursor_empl.execute(
                    "INSERT INTO tabla_oper_id(ID, contr, nombre, apellidopat, apellidomat, empresa) VALUES(?, ?, ?, ?, ?, ?)",
                    (id_oper_comp, contr, nombre, apellpat, apellmat, empresa)
                )
                conn_empl.commit()
                return redirect(url_for('gerencia_aviso_alta_oper'))
            except Exception as e:
                error = f"Error en la base de datos: {e}"
            finally:
                conn_empl.close()

    return render_template('gerencia_alta_oper.html', error=error)

@app.route('/gerencia/operadores/aviso_alta')
def gerencia_aviso_alta_oper():
    if not session.get('autorizado'):
        return redirect(url_for('acceso_portal'))
    if 'operadorger_id' not in session:
        return redirect(url_for('login_operadorger'))
    error = None
    return render_template('gerencia_aviso_alta_oper.html')


@app.route('/gerencia/operadores/baja', methods=['GET', 'POST'])
def gerencia_baja_oper():
    if not session.get('autorizado'):
        return redirect(url_for('acceso_portal'))
    if 'operadorger_id' not in session:
        return redirect(url_for('login_operadorger'))
    error = None
    exito = None

    if request.method == 'POST':
        emp_baja = request.form.get('id_emp_baja', '').strip().upper()

        if not emp_baja:
            error = "Debe ingresar o seleccionar un ID de empleado."
        else:
            conn_empl = get_db_oper()
            try:
                cursor_empl = conn_empl.cursor()
                cursor_empl.execute("SELECT * FROM tabla_oper_id WHERE ID=?", (emp_baja,))
                check_emp = cursor_empl.fetchone()

                if not check_emp:
                    error = f"El empleado con ID '{emp_baja}' no existe."
                else:
                    cursor_empl.execute("DELETE FROM tabla_oper_id WHERE ID=?", (emp_baja,))
                    conn_empl.commit()
                    exito = f"El empleado {check_emp['nombre']} {check_emp['apellidopat']} ({emp_baja}) ha sido dado de baja."
            finally:
                conn_empl.close()

    conn_empl = get_db_oper()
    try:
        cursor_empl = conn_empl.cursor()
        cursor_empl.execute("SELECT * FROM tabla_oper_id")
        lista_empleados = cursor_empl.fetchall()
    finally:
        conn_empl.close()

    return render_template('gerencia_baja_oper.html', empleados=lista_empleados, error=error, exito=exito)
if __name__ == '__main__':
    app.run(debug=True)