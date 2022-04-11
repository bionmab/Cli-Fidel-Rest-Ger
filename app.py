# Librerias a importar
from flask import Flask, render_template,request,redirect,url_for,flash,session

# Librerias para operar con la base de datos
from flask_sqlalchemy import SQLAlchemy

#Librería para filtro de busqueda
from sqlalchemy import or_

# Librerias para el envío de mails
from flask_mail import Mail,Message
import smtplib

#Librerias de logueo de usuario
from flask_login import UserMixin, LoginManager, login_user, login_required, current_user, logout_user
from sqlalchemy.sql.expression import true

# Para crear la incriptacion de las claves
from werkzeug.security import generate_password_hash, check_password_hash

#Libreria QR
import qrcode
from PIL import Image

#Importar Libreria para chequeo de teléfonos
import phonenumbers

# Creacion de la ruta de la base de datos SQLITE3
import os
dbdir = "sqlite:///" + os.path.abspath(os.getcwd()) + "/fideldatabase.db" # Ruta absoluta de la base de datos.

# Creacion de la ruta de la base de datos PostgreSQL
#dbdir = "postgresql+psycopg2://{username}:{password}@{hostname}/{databasename}".format(username="", password="", hostname="", databasename="")

# Creacion de la ruta de la base de datos MySQL
#import os
#dbdir = "mysql+mysqlconnector://{username}:{password}@{hostname}/{databasename}".format(username="admin", password="qgYxXRR!PzMX)p]Z", hostname="localhost", databasename="fideldatabase")

#Ruta para el QR del cliente
rutaqr = os.path.abspath(os.getcwd()) + "/static/qr/"

##########################
# Configuraciones varias #
##########################
app = Flask(__name__)
app.config['SECRET_KEY'] = '7110c8ae51a4b5af97be6534caef90e4bb9bdcb3380af008f90b23a5d1616bf319bc298105da20fe'

app.config["SQLALCHEMY_DATABASE_URI"] = dbdir
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Parámetros de email
app.config["MAIL_SERVER"] = 'smtp.gmail.com'
app.config["MAIL_PORT"] = 465
app.config["MAIL_USE_SSL"] = True
app.config["MAIL_USERNAME"] = 'pepe@mail.com'
app.config["MAIL_PASSWORD"] = 'clave del mail'
mail = Mail(app)

# Instanciamos la base de datos a la app
db = SQLAlchemy(app) 

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

################################
# CLASE PARA LA TABLA USUARIOS #
################################
class Usuarios(UserMixin, db.Model):

    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key = True)
    apellido = db.Column(db.String(30), nullable=False)
    nombre = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(70), unique=True, nullable=False)
    fechanac = db.Column(db.String(10), nullable=True)
    password = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    telefono = db.Column(db.String(30), nullable=True)


###################################
# CLASE PARA LA TABLA MOVIMIENTOS #
###################################
class Movimientos(UserMixin, db.Model):

    __tablename__ = 'movimientos'

    id = db.Column(db.Integer, primary_key = True)
    idcliente = db.Column(db.Integer, nullable = False)
    fechamov = db.Column(db.String(10), nullable=False)
    comprobante = db.Column(db.String(20), nullable=False)
    tipomov = db.Column(db.String(10), nullable=False)
    puntos = db.Column(db.Integer, default=0, nullable=False)


##############################
# CLASE PARA LA TABLA SALDOS #
##############################
class Saldos(UserMixin, db.Model):

    __tablename__ = 'saldos'

    id = db.Column(db.Integer, primary_key = True)
    idcliente = db.Column(db.Integer, unique=True, nullable = False)
    saldo = db.Column(db.Integer, default=0, nullable=False)


# Parametros del usuario logueado
@login_manager.user_loader
def load_user(user_id):
    return Usuarios.query.get(int(user_id))


##################
# RUTA DEL INDEX #
##################
@app.route('/') 
@app.route("/index")
def index():
	return render_template('index.html')

###########################
# RUTA DEL AGREGARCLIENTE #
###########################
@app.route('/agregaclientes') 
def agregaclientes():
	return render_template('agregacliente.html')


#########################
# RUTA DE LA CREDENCIAL #
#########################
@app.route('/credencial') 
def credencial():
    #Contenido del QR
    qr = current_user.email
    #Nombre del archivo png con el código QR
    archivo= qr + '.png'

    #Generacion del QR
    imagen = qrcode.make(qr)
    archivo_imagen = open(rutaqr + archivo, 'wb')
    imagen.save(archivo_imagen)
    archivo_imagen.close()
    return render_template('credencial.html', archivo=archivo)


###################
# RUTA DEL ABOUT #
###################
@app.route('/about')
def about():
    return render_template('about.html')


####################
# RUTA DEL PRIVACY #
####################
@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

######################
# RUTA DE LAS PROMOS #
######################
@app.route('/promos')
def promos():
    return render_template('promos.html')


#####################
# RUTA DEL CONTACTO #
#####################
@app.route('/contact')
def contact():
    return render_template('contact.html')


###############################
# RUTA DEL PERFIL DEL USUARIO #
###############################
@app.route('/profile')
@login_required # necesita estar logueado para entrar
def profile():
    return render_template('profile.html', name=current_user.nombre)


#####################################
# RUTA DEL PERFIL DEL ADMINISTRADOR #
#####################################
@app.route('/profileadmin/')
@login_required # necesita estar logueado para entrar
def profileadmin():
    return render_template('profileadmin.html', name=current_user.nombre)


########################################
# RUTA PARA VER LOS CLIENTES DEL SITIO #
########################################
@app.route('/adminclientes/', methods=['GET','POST'], defaults={"page": 1})
@app.route('/adminclientes/<int:page>', methods=['GET'])
@login_required # necesita estar logueado para entrar
def adminclientes(page):
    page = page
    pages = 5
    #usuarios = Usuarios.query.filter().all() # trae todos
    #usuarios = Usuarios.query.paginate(page,pages,error_out=False) #trae todos paginados
    usuarios = Usuarios.query.order_by(Usuarios.id.desc()).paginate(page,pages,error_out=False)
    if request.method == 'POST' and 'tag' in request.form:
       tag = request.form["tag"]
       search = "%{}%".format(tag)
       usuarios = Usuarios.query.filter(or_(Usuarios.email.like(search))).paginate(per_page=pages, error_out=True) 
       return render_template('adminclientes.html', usuarios=usuarios, tag=tag)
    return render_template('adminclientes.html', usuarios=usuarios)

""" @app.route('/adminclientes/', methods=['GET','POST'], defaults={"page": 1})
@app.route('/adminclientes/<int:page>', methods=['GET','POST'])
@login_required # necesita estar logueado para entrar
def adminclientes(page):
    page = page
    pages = 5
    #usuarios = Usuarios.query.filter().all()
    usuarios = Usuarios.query.paginate(page,pages,error_out=False)
    return render_template('adminclientes.html', usuarios=usuarios) """


############################
# RUTA DE BAJA DEL CLIENTE #
############################
@app.route("/delete_user/<string:idcliente>",methods=['GET'])
@login_required # necesita estar logueado para entrar
def delete_user(idcliente):
    deletecliente = Usuarios.query.filter_by(id=idcliente).first()
    db.session.delete(deletecliente)
    db.session.commit()
    flash('CLIENTE DADO DE BAJA EXITOSAMENTE','warning')
    return redirect(url_for("adminclientes"))


###############################
# RUTA DE BAJA DEL MOVIMIENTO #
###############################
@app.route("/delete_movimiento/<string:idmovimiento>",methods=['GET'])
@login_required # necesita estar logueado para entrar
def delete_movimiento(idmovimiento):
    deletemovimiento = Movimientos.query.filter_by(id=idmovimiento).first()
    db.session.delete(deletemovimiento)
    db.session.commit()
    flash('MOVIMIENTO DADO DE BAJA EXITOSAMENTE','warning')
    return redirect(url_for("adminmovimientos"))
   

#################################
# RUTA DEL REGISTRO DE USUARIOS #
#################################
@app.route('/signup/', methods=['POST','GET'])
def signup():
    if request.method == 'POST':
        apellido = request.form['apellido']
        nombre = request.form['nombre']
        fechanac = request.form['fechanac']
        telefono = request.form['telefono']
        email = request.form['email']
        password = request.form['password']

        #Validamos el teléfono
        my_number = phonenumbers.parse(telefono, 'AR')  #'AR'' is ISO Alpha-2 code for argentina
        international_f = phonenumbers.format_number(my_number, phonenumbers.PhoneNumberFormat.INTERNATIONAL)

        # Comprobamos que no hay ya un usuario con ese email
        Cliente = Usuarios.query.filter_by(email=email).first()
        if Cliente is not None:
            flash('EL MAIL UTILIZADO YA EXISTE EN NUESTROS REGISTROS.','danger')
            return redirect(url_for('signup')) 
        else:
            # Creamos el usuario y lo guardamos encriptado al password
            Cliente = Usuarios(apellido = apellido, nombre = nombre, fechanac = fechanac, telefono = international_f, email = email, password = generate_password_hash(password, method='sha256'))
            db.session.add(Cliente)
            db.session.commit()
            flash('REGISTRADO CON EXITO, POR FAVOR INGRESE DESDE AQUI...','success')
            return redirect(url_for('login')) 
    return render_template("signup.html")


######################################
# RUTA PARA EL LOGIN DE LOS USUARIOS #
######################################
@app.route('/login/',methods=['POST','GET'])
def login():
    status=True
    if request.method=='POST':
        email=request.form["email"]
        password=request.form["password"]
        
         # Comprobamos que el usuario exista con ese email
        Cliente = Usuarios.query.filter_by(email=email).first()

        if not Cliente or not check_password_hash(Cliente.password, password):
            flash('POR FAVOR REVISE SUS CREDENCIALES E INTENTELO NUEVAMENTE.','danger')
            return redirect(url_for('login'))
        else:
            if Cliente.is_admin:
                login_user(Cliente)
                return redirect(url_for('profileadmin'))
            else:
                login_user(Cliente)
                return redirect(url_for('profile'))
    return render_template('login.html')
    
    
##########################################
# RUTA PARA EL DESLOGUEO DE LOS USUARIOS #
##########################################
@app.route('/logout')
@login_required # necesita estar logueado para entrar
def logout():
    logout_user()
    return redirect(url_for('index'))


#################################
# RUTA DE AGREGAR CLIENTE NUEVO #
#################################
@app.route("/agregarcliente/", methods=['POST','GET'])
@login_required # necesita estar logueado para entrar
def agregarcliente():
    if request.method == 'POST':
        apellido = request.form['apellido']
        nombre = request.form['nombre']
        fechanac = request.form['fechanac']
        telefono = request.form['telefono']
        email = request.form['email']
        password = request.form['password']
        password = request.form['password']
        tipo = request.form.get('tipo')
        if tipo is not None:
            tipo = 1 # administrador, si es ok el checked del formulario
        else:
            tipo = 0

        #Validamos el teléfono
        my_number = phonenumbers.parse(telefono, 'AR')  #'AR'' is ISO Alpha-2 code for argentina
        international_f = phonenumbers.format_number(my_number, phonenumbers.PhoneNumberFormat.INTERNATIONAL)

        # Comprobamos que no hay ya un usuario con ese email
        Cliente = Usuarios.query.filter_by(email=email).first()
        if Cliente is not None:
            flash('EL MAIL UTILIZADO YA EXISTE EN NUESTROS REGISTROS.','danger')
            return redirect(url_for('agregarcliente')) 
        else:
            # Creamos el usuario y lo guardamos encriptado al password
            Cliente = Usuarios(apellido = apellido, nombre = nombre, fechanac = fechanac, telefono = international_f, email = email, password = generate_password_hash(password, method='sha256'), is_admin = tipo)
            db.session.add(Cliente)
            db.session.commit()
            flash('NUEVO CLIENTE REGISTRADO CON EXITO','success')  
    return render_template("profileadmin.html")


#############################
# RUTA DE MODIFICAR CLIENTE #
#############################
@app.route("/edit_user/<string:idcliente>")
@login_required # necesita estar logueado para entrar
def edit_user(idcliente):
   cliente = Usuarios.query.filter_by(id=idcliente).first()
   return render_template('updatecliente.html', cliente=cliente)


################################
# RUTA DE MODIFICAR MOVIMIENTO #
################################
@app.route("/edit_movimiento/<string:idmovimiento>")
@login_required # necesita estar logueado para entrar
def edit_movimiento(idmovimiento):
   movimiento = Movimientos.query.filter_by(id=idmovimiento).first()
   return render_template('updatemovimiento.html', movimiento=movimiento)


##############################
# RUTA DE ACTUALIZAR CLIENTE #
##############################
@app.route("/actualizar_user/", methods=["POST"])
@login_required # necesita estar logueado para entrar
def actualizar_user():
   if request.method=='POST':
        id=request.form['id']
        updatecliente = Usuarios.query.filter_by(id=id).first()
        apellido=request.form['apellido']
        nombre=request.form['nombre']
        fechanac=request.form['fechanac']
        telefono=request.form['telefono']
        email=request.form['email']
        tipo = request.form.get('tipo')
        if tipo is not None:
            tipo = 1 # administrador, si es ok el checked del formulario
        else:
            tipo = 0

         #Validamos el teléfono
        my_number = phonenumbers.parse(telefono, 'AR')  #'AR'' is ISO Alpha-2 code for argentina
        international_f = phonenumbers.format_number(my_number, phonenumbers.PhoneNumberFormat.INTERNATIONAL)

        #cliente = Usuarios(apellido=apellido, nombre=nombre, fechanac=fechanac, telefono=telefono, password = generate_password_hash(password, method='sha256'), email=email)
        updatecliente.apellido=apellido
        updatecliente.nombre=nombre
        updatecliente.fechanac=fechanac
        updatecliente.telefono=international_f
        updatecliente.email=email
        updatecliente.is_admin=tipo
        db.session.commit()
        flash('SE ACTUALIZARON LOS DATOS DEL CLIENTE EN FORMA CORRECTA.','success')
        return redirect(url_for("profileadmin"))


###############################
# RUTA DE VER LOS MOVIMIENTOS #
###############################
@app.route('/vermovimientos', methods=['GET','POST'], defaults={"page": 1})
@app.route('/vermovimientos/<int:page>', methods=['GET','POST'])
@login_required # necesita estar logueado para entrar
def vermovimientos(page):
    page = page
    pages = 20
    #movimientos = Movimientos.query.filter().all()
    movimientos = Movimientos.query.paginate(page,pages,error_out=False)
    return render_template('vermovimientos.html', movimientos=movimientos)


###################################
# RUTA DE ADMINISTRAR MOVIMIENTOS #
###################################
#@app.route('/edit_movimientos/<string:tag>', methods=['POST'])
@app.route('/edit_movimientos/<string:idcliente>/<int:page>', methods=['GET','POST'])
@login_required # necesita estar logueado para entrar
def edit_movimientos(idcliente, page):
    page = page
    pages = 10
    #movimientos = Movimientos.query.filter().all()
    #movimientos = Movimientos.query.paginate(page,pages,error_out=False)
    movimientos = Movimientos.query.filter(Movimientos.idcliente == idcliente).paginate(per_page=pages, error_out=True)
    if request.method == 'POST' and 'tag' in request.form:
       tag = request.form["tag"]
       search = "%{}%".format(tag)
       movimientos = Movimientos.query.filter(or_(Movimientos.comprobante.like(search))).paginate(per_page=pages, error_out=True) 
       return render_template('adminmovimientos.html', movimientos=movimientos, tag=tag)
    return render_template('adminmovimientos.html', movimientos=movimientos)


##########################
# RUTA DE VER LOS SALDOS #
##########################
@app.route('/versaldos', methods=['GET','POST'], defaults={"page": 1})
@app.route('/versaldos/<int:page>', methods=['GET','POST'])
@login_required # necesita estar logueado para entrar
def versaldos(page):
    page = page
    pages = 10
    #movimientos = Movimientos.query.filter().all()
    saldos = Saldos.query.paginate(page,pages,error_out=False)
    return render_template('versaldos.html', saldos=saldos)
    
    
################################
# ENVIO DE EMAILS POR CLIENTES #
################################
@app.route("/email_user/<string:idcliente>",methods=['GET'])
@login_required # necesita estar logueado para entrar
def email_user(idcliente):
  try:
    msg = Message("FidelApp - Comunicación al usuario",
      sender="prueba@gmail.com",
      recipients=["mbiondini@outlook.com"])
    msg.body = "Por favor revise los movimientos de su cuenta Restó, cliente: ",idcliente           
    msg.html = "<h1 style='color:green;'>Sample Message Body Here With HTML and CSS Style</h1>"           
    mail.send(msg)
    flash('Email enviado satisfactoriamente','success')
    return redirect(url_for("adminclientes"))
    
  except Exception as e:
    print(str(e))
    flash('Error al enviar Email','warning')
    return redirect(url_for("adminclientes"))

##################################
# ENVIO DE EMAILS POR MOVIMIENTO #
##################################
@app.route("/email_user_movimiento/<string:idcliente>",methods=['GET'])
@login_required # necesita estar logueado para entrar
def email_user_movimiento(idcliente):
  try:
    msg = Message("FidelApp - Comunicación al usuario",
      sender="prueba@gmail.com",
      recipients=["mbiondini@outlook.com"])
    msg.body = "Por favor revise los movimientos de su cuenta Restó, cliente: ",idcliente           
    msg.html = "<h1 style='color:green;'>Sample Message Body Here With HTML and CSS Style</h1>"           
    mail.send(msg)
    flash('Email enviado satisfactoriamente','success')
    return redirect(url_for("adminclientes"))
    
  except Exception as e:
    print(str(e))
    flash('Error al enviar Email','warning')
    return redirect(url_for("adminclientes"))

#



# Ejecutamos la app
if __name__ == "__main__":
    db.create_all() # Si la base no estuviera creada la crea automaticamente.
    app.run(debug = True)



