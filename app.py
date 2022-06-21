from datetime import datetime
from flask import Flask, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config.from_pyfile("config.py")
usuario_actual = None

from models import Ingrediente, db
from models import Usuario, Receta



@app.route("/")
def principal():
    global usuario_actual
    if usuario_actual is not None:
        return render_template("principal.html")
    else:
        return redirect(url_for("iniciarSesion"))


@app.route("/compartir_receta", methods=["POST", "GET"])
def compartirReceta():
    if usuario_actual is not None:
        if request.method == "POST":
            nueva_receta = Receta(nombre=request.form["nombre"], tiempo=request.form["tiempo"], fecha=datetime.now(), elaboracion=request.form["elaboracion"], cantidadMeGusta=0, usuarioid=usuario_actual.id)
            db.session.add(nueva_receta)
            db.session.commit()
            for i in range(10):
                if request.form["ingrediente"+str(i)] != "":
                    nuevo_ingrediente = Ingrediente(nombre=request.form["ingrediente"+str(i)], cantidad=request.form["cantidad"+str(i)], unidad=request.form["unidad"+str(i)], recetaid=nueva_receta.id)
                    db.session.add(nuevo_ingrediente)
            db.session.commit()            
            return redirect(url_for("principal"))
        else:
            return render_template("compartir_receta.html")
    else:
        return redirect(url_for("iniciarSesion"))

@app.route("/ranking")
def consultarRanking():
    if usuario_actual is not None:
        lista = Receta.query.all()
        recetas = []
        for i in range(5):
            unaReceta = None
            indice = 0
            for j in range(len(lista)):
                aux:Receta = lista[j]
                if unaReceta == None or unaReceta.cantidadMeGusta < aux.cantidadMeGusta:
                    unaReceta = aux
                    indice = j
            recetas.append(unaReceta)
            lista[indice] = None
        return render_template("ranking.html", recetas=recetas)
    else:
        return redirect(url_for("iniciarSesion"))


"""@app.route("/agregar_receta", methods=["POST", "GET"])
def agregarReceta():
    if usuario_actual is not None:
        if request.method == "POST":
            nueva_receta = Receta(nombre=request.form["nombre"], tiempo=request.form["tiempo"], fecha=datetime.now(), elaboracion=request.form["elaboracion"], cantidadMeGusta=0, usuario_id=request.form["id"])
        else:
            return render_template("compartir_recetea.html")
    else:
        return redirect(url_for("iniciarSesion"))"""



@app.route("/login", methods = ["POST", "GET"])
def iniciarSesion():
    global usuario_actual
    if usuario_actual is None:
        if request.method=="POST":
            if not request.form["email"] or not request.form["password"]:
                return render_template("error.html", error="Debe ingresar sus datos")
            else:
                usuario = Usuario.query.filter_by(correo=request.form["email"]).first()
                if usuario is None:
                    return render_template("error.html", error="El usuario no esta registrado")
                else:
                    verificacion = usuario.clave == request.form["password"]
                    if verificacion:
                        usuario_actual = usuario
                        return redirect(url_for("principal"))
                    else:
                        return render_template("error.html", mensaje="Contraseña incorrecta")
        else:
            return render_template("acceso.html")
    else:
        return render_template("sesion_iniciada.html", usuario=usuario_actual)

@app.route("/consultar_recetas")
def consultarRecetas():
    if usuario_actual is not None:
        return render_template("consultar_recetas.html", recetas=Receta.query.all())
    else:
        return redirect(url_for("iniciarSesion"))


@app.route("/dar_me_gusta")
def darMeGusta(receta=None):
    if receta==None:
        print("No se pudo dar me gusta")
    else:
        receta.cantidadMeGusta += 1
        db.session.commit()




@app.route("/logout")
def cerrarSesion():
    global usuario_actual
    usuario_actual = None
    return redirect(url_for("iniciarSesion"))


if __name__ == "__main__":
    app.run(debug=True)