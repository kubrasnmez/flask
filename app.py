
from flask import Flask,render_template,flash,redirect,request,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,SubmitField,validators
from passlib.hash import sha256_crypt #şifreleme işlemleri
from functools import wraps #Decarotarlar için
from flask_user import user_logged_in, user_logged_out
from flask_login import user_loaded_from_header,current_user,LoginManager
from werkzeug.utils import secure_filename

#Admin Giris Decarator'ı
#Admin olmayanlar bu sayafayı görüntüleyemezler.
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "adminlogged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Bu sayfayı görüntülemek için giriş yapmalısınız.","danger")
            return redirect(url_for("adminlogin"))
    return decorated_function

#Kullanıcı Giris Decarator'ı
#Kullanıcı olmayanlar bu  sayfayı görüntülüyemezler.
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Bu sayfayı görüntülemek için giriş yapmalısınız.","danger")
            return redirect(url_for("login"))
    return decorated_function

#KULLANICI KAYIT FORMU
class RegisterForm(Form):
    name = StringField("İsim Soyisim  : ",validators=[validators.Length(min=5,max=25)])
    username = StringField("Kullanıcı Adı  : ",validators=[validators.Length(min=4,max=25)])
    email = StringField("Email Adresi : ", validators=[validators.Email(message="Lütfen geçerli bir email adresi giriniz.")])
    password = PasswordField("Parola : " ,validators=[
    validators.DataRequired(message="Lutfen bir parola belirleyin"),
    validators.EqualTo(fieldname = "confirm", message="Parolanız uyuşmuyor...")#Parola eşitleme onaylama
    ])
    confirm = PasswordField("Parola Doğrula : ")

#ADMİN KAYIT FORMU 
class AdminRegisterForm(Form):
    username = StringField("Kullanıcı Adı  : ",validators=[validators.Length(min=4,max=25)])
    email = StringField("Email Adresi : ", validators=[validators.Email(message="Lütfen geçerli bir email adresi giriniz.")])
    password = PasswordField("Parola : " ,validators=[
    validators.DataRequired(message="Lutfen bir parola belirleyin"),
    validators.EqualTo(fieldname = "confirm", message="Parolanız uyuşmuyor...")
    ])
    confirm = PasswordField("Parola Doğrula : ")

#Kullanıcı Giriş Formu
class LoginForm(Form):
    username = StringField("Kullanıcı Adı : ")
    password = PasswordField("Parola : ")

#Admin Giriş Formu
class AdminForm(Form):
    username = StringField("Kullanıcı Adı : ")
    password = PasswordField("Parola : ")

#Otel Form
class OtelForm(Form):
    tittle = StringField("Otel Adı ",validators=[validators.Length(min=4,max=40)])
    kisi = StringField("Yazar Adı ", validators=[validators.Length(min=4,max=12)])
    bilgi = TextAreaField("Otel İçerik",validators=[validators.Length(min=10)])
    fiyat = StringField("Otel Fiyatı")
    konum = TextAreaField("Otel Adresi",validators=[validators.Length(min=7)])
    resim = StringField("Otel Resim")


app = Flask(__name__)
app.secret_key ="kbsnmz"


app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "proje"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"
mysql = MySQL(app)

#sepet için liste
sepet = list()

#Anasayfa
@app.route("/")
def index():
    return render_template("index.html")

#Misyon & Vizyon Sayfası
@app.route('/about')
def about():
    return render_template('about.html')

#Otel Sayfası
@app.route("/oteller")
def oteller():
    cursor = mysql.connection.cursor() #Veri tabanına bağlantı
    sorgu = "Select * From otellerimiz" #Otellerimiz tablosundaki tüm otelleri çek
    result = cursor.execute(sorgu) #Sorguyu çalıştır.
    if result > 0 : #tabloda eleman varsa
        oteller = cursor.fetchall() #hepsini çek
        return render_template("oteller.html",oteller=oteller)
    else:
        return render_template("oteller.html")

#Admin Kontrol Paneli
#Admin tarafından otel ekleme, silme, güncelleme işlemlerinin açıldığı url. 
@app.route("/dashboard")
@admin_required
def dashboard():
    cursor = mysql.connection.cursor()
    sorgu = "Select * From otellerimiz"
    result = cursor.execute(sorgu)
    if result > 0 :
        oteller = cursor.fetchall()
        return render_template("dashboard.html",oteller=oteller)
    else:
        return render_template("dashboard.html")


#Admin Kayıt
@app.route("/adminregister",methods=['GET','POST'])
def adminregister():
    form = AdminRegisterForm(request.form) #Admin kayıt formuna request 
    if request.method=="POST" and form.validate(): #POST  ve form değerleri uygunsa
        username = form.username.data #formdaki usernamein datasını username değişkenine ata.
        email = form.email.data #formdaki email datasını email değişkenine ata
        password = sha256_crypt.encrypt(form.password.data) #şifreyi şifreli bir şekilde tutuyoruz.
        cursor = mysql.connection.cursor()
        sorgu = "Insert into admin(email,username,password) VALUES(%s,%s,%s)" #Veritabanına ekleme işlemi
        cursor.execute(sorgu,(email,username,password))
        mysql.connection.commit()
        cursor.close()
        flash ("Başarılı bir şekilde admin oldunuz.",category="success")
        return redirect(url_for("adminlogin"))
    else:
        return render_template("adminregister.html",form=form)


#Kullanıcı Kayıt Olma
@app.route("/register",methods = ['GET','POST'])
def register():
    form = RegisterForm(request.form)
    if request.method =="POST" and form.validate():
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)
        cursor = mysql.connection.cursor()
        sorgu = "Insert into users(name,email,username,password) VALUES(%s,%s,%s,%s)"

        cursor.execute(sorgu,(name,email,username,password))
        mysql.connection.commit()
        cursor.close()
        flash("Başarılı bir şekilde kayıt oldunuz.",category="success")

        return redirect(url_for("login"))
    else:
         return render_template("register.html",form=form)


#Admin Giriş
@app.route("/adminlogin",methods=["GET","POST"])
def adminlogin():
    form = AdminForm(request.form)
    if request.method == "POST":
        username = form.username.data
        password_entered = form.password.data
        cursor = mysql.connection.cursor()
        sorgu = "Select * From admin where username = %s"
        result = cursor.execute(sorgu,(username,))
        if result>0:
            data = cursor.fetchone()
            real_password = data["password"]  #sifrelenmis sekilde
            if sha256_crypt.verify(password_entered,real_password):
                flash("Başarıyla giriş yaptınız.","success")
                session["adminlogged_in"] = True
                session["username"] = username
                return redirect(url_for("index"))
            else:
                flash("Parolanızı yanlış girdiniz.","danger")
                return redirect(url_for("adminlogin"))
        else:
            flash("Böyle bir kullanıcı bulunmuyor.","danger")
            return redirect(url_for("adminlogin"))

    return render_template("admin.html",form = form)
    
#LOGIN İŞLEMİ
@app.route("/login",methods = ["GET","POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST":
        username = form.username.data
        password_entered = form.password.data
        cursor = mysql.connection.cursor()
        sorgu = "Select * From users where username = %s"
        result = cursor.execute(sorgu,(username,))
        if result>0:
            data = cursor.fetchone()
            real_password = data["password"]  #sifrelenmis sekilde
            if sha256_crypt.verify(password_entered,real_password):
                flash("Başarıyla giriş yaptınız.","success")
                session["logged_in"] = True
                session["username"] = username
                return redirect(url_for("index"))
            else:
                flash("Parolanızı yanlış girdiniz.","danger")
                return redirect(url_for("login"))
        else:
            flash("Böyle bir kullanıcı bulunmuyor.","danger")
            return redirect(url_for("login"))

    return render_template("login.html",form = form)


#Detay Sayfası 
@app.route("/otel/<string:otelid>")
def otel(otelid):
    cursor = mysql.connection.cursor()
    sorgu = "Select * from otellerimiz where otelid = %s"
    result = cursor.execute(sorgu,(otelid,))
    if result>0:
        otel = cursor.fetchone()
        return render_template("otel.html",otel=otel)
    else:
        return render_template("otel.html")
    
#Logaout İşlemi
@app.route("/logout")
def logout():
    session.clear()
    sepet.clear()
    return redirect(url_for("login"))

#Otel Ekleme
@app.route("/otelekle",methods=["GET","POST"])
def otelekle():
    form = OtelForm(request.form)
    if request.method == "POST" and form.validate():
        tittle = form.tittle.data
        kisi = form.kisi.data
        bilgi = form.bilgi.data
        fiyat = form.fiyat.data
        konum = form.konum.data
        resim = form.resim.data
        cursor = mysql.connection.cursor()
        sorgu = "Insert into otellerimiz (tittle,kisi,bilgi,fiyat,konum,resim) VALUES(%s,%s,%s,%s,%s,%s)"
        cursor.execute(sorgu,(tittle,kisi,bilgi,fiyat,konum,resim))
        mysql.connection.commit()
        cursor.close()
        flash("Otel basariyla eklendi","success")
        return redirect(url_for("dashboard"))
    return render_template("otelekle.html",form=form)

#Otel Silme
@app.route("/delete/<string:otelid>")
@admin_required
def delete(otelid):
    cursor = mysql.connection.cursor()
    sorgu = "Select * from otellerimiz where kisi = %s and otelid = %s "
    result = cursor.execute(sorgu,(session["username"],otelid))
    if result>0:
        sorgu2 = "Delete from otellerimiz where otelid = %s"
        cursor.execute(sorgu2,(otelid,))
        mysql.connection.commit()
        return redirect(url_for("dashboard"))
    else:
        flash("Böyle bir otel yok veya bu işleme yetkiniz yok.","danger")
        return redirect(url_for("index"))


#Otel Güncelleme 
@app.route("/edit/<string:otelid>",methods = ["GET","POST"])
@admin_required
def update(otelid):
    if request.method == "GET": 
        cursor = mysql.connection.cursor()
        sorgu = "Select * from otellerimiz where otelid =%s and kisi = %s"
        result = cursor.execute(sorgu,(otelid,session["username"]))
        if result == 0:
            flash("Boyle bir otel yok veya yetkiniz yok","danger")
            return redirect(url_for("index"))
        else:
            otel = cursor.fetchone()
            form = OtelForm()
            form.tittle.data = otel["tittle"]
            form.kisi.data = otel["kisi"]
            form.bilgi.data = otel["bilgi"]
            form.fiyat.data = otel["fiyat"]
            form.konum.data = otel["konum"]
            form.resim.data = otel["resim"]
            return render_template("update.html", form = form)
        
    else:
        #POST REQUEST
        form = OtelForm(request.form)
        newTitle = form.tittle.data
        newAuthor = form.kisi.data
        newContent = form.bilgi.data
        newFiyat = form.fiyat.data
        newKonum = form.konum.data
        newResim = form.resim.data

        sorgu2 = "Update otellerimiz Set tittle = %s,kisi=%s,bilgi=%s,fiyat=%s,konum=%s,resim=%s where otelid = %s"
        cursor= mysql.connection.cursor()
        cursor.execute(sorgu2,(newTitle,newAuthor,newContent,newFiyat,newKonum,newResim,otelid))
        mysql.connection.commit()
        flash("Otel başarıyla güncellendi","success")
        return redirect(url_for("dashboard"))
        
    
#Arama İşlemi
@app.route("/search",methods= ["GET","POST"])
def search():
    if request.method == "GET": #URL'den gitmemek için
        return redirect(url_for("index"))
    else : 
        keyword = request.form.get("keyword")
        cursor = mysql.connection.cursor()
        sorgu = "Select * from otellerimiz where tittle like '%" + keyword + "%'"
        result = cursor.execute(sorgu)
        if result == 0:
            flash("Aranan kelimeye uygun otel bulunamadi..","warning")
            return redirect(url_for("oteller"))
        else:
            oteller = cursor.fetchall()
            return render_template("oteller.html",oteller = oteller)

#Sepet İşlemleri
@app.route("/sepetim",methods=['GET','POST'])
@login_required
def sepetim():
    temp = list()
    otelid = request.form.get("otel.otelid")
    tittle = request.form.get("otel.tittle")
    fiyat = request.form.get("otel.fiyat")
    if tittle != None and fiyat != None:
        temp.append(otelid)
        temp.append(tittle)
        temp.append(fiyat)
        sepet.append(temp)
    return render_template("sepetim.html",sepet = sepet)
    


#Sepet Sil  
@app.route("/sepetsil",methods=['GET','POST'])
@login_required
def sepetsil():
    tittle = request.form.get("s[1]")
    for i in sepet:
        if i[1] == tittle:
            index = sepet.index(i)
            sepet.pop(index)
    return render_template("sepetim.html",sepet=sepet)
   

if __name__=='__main__':
    app.run(debug=True)