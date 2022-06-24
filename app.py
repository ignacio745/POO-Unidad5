from crypt import methods
from datetime import datetime
import hashlib
from flask import Flask, redirect, render_template, request, url_for, session
from flask_sqlalchemy import SQLAlchemy

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

@app.route("/login", methods = ["POST", "GET"])
def iniciarSesion():
    global usuario_actual
    if usuario_actual is None:
        if request.method=="POST":
            if not request.form["email"] or not request.form["password"]:
                return render_template("error.html", mensaje="Debe ingresar sus datos", url=url_for("iniciarSesion"), link="Volver a iniciar sesion")
            else:
                usuario = Usuario.query.filter_by(correo=request.form["email"]).first()
                if usuario is None:
                    return render_template("error.html", mensaje="El usuario no esta registrado", url=url_for("iniciarSesion"), link="Volver a iniciar sesion")
                else:
                    verificacion = usuario.clave == hashlib.md5(bytes(request.form["password"], encoding="utf-8")).hexdigest()
                    if verificacion:
                        usuario_actual = usuario
                        return redirect(url_for("principal"))
                    else:
                        return render_template("error.html", mensaje="Contraseña incorrecta", url=url_for("iniciarSesion"), link="Volver a iniciar sesion")
        else:
            return render_template("acceso.html")
    else:
        return render_template("sesion_iniciada.html", usuario=usuario_actual)



@app.route("/compartir_receta", methods=["POST", "GET"])
def compartirReceta():
    if usuario_actual is not None:
        if request.method == "POST":
            nueva_receta = Receta(nombre=request.form["nombre"], tiempo=request.form["tiempo"], fecha=datetime.now(), elaboracion=request.form["elaboracion"], cantidadMeGusta=0, usuarioid=usuario_actual.id)
            db.session.add(nueva_receta)
            db.session.commit()           
            return render_template("agregar_ingrediente.html", id_receta = nueva_receta.id, nombre_receta=nueva_receta.nombre, cantidad=0)
        else:
            return render_template("compartir_receta.html")
    else:
        return redirect(url_for("iniciarSesion"))



@app.route("/agregar_ingrediente/<id_receta>/<nombre_receta>/<cantidad>", methods=["POST", "GET"])
def agregarIngrediente(id_receta, nombre_receta, cantidad):
    if usuario_actual is not None:
        id_receta = int(id_receta)
        cantidad=int(cantidad)
        if request.method=="POST":
            nuevo_ingrediente = Ingrediente(nombre=request.form["nombre"], cantidad=request.form["cantidad"], unidad=request.form["unidad"], recetaid=id_receta)
            db.session.add(nuevo_ingrediente)
            db.session.commit()
            if cantidad < 10:
                return render_template("agregar_ingrediente.html", id_receta=id_receta, nombre_receta=nombre_receta, cantidad=cantidad)
            else:
                return redirect(url_for("recetaAgregada", nombre_receta=nombre_receta))
        else:
            return render_template("error.html", mensaje="Ocurrio un error en la carga de ingredientes")
    else:
        return redirect(url_for("iniciarSesion"))



@app.route("/receta_agregada/<nombre_receta>")
def recetaAgregada(nombre_receta):
    return render_template("receta_agregada.html", nombre_receta=nombre_receta)




@app.route("/consultar_recetas")
def consultarRecetas():
    if usuario_actual is not None:
        return render_template("consultar_recetas.html", titulo="Recetas", recetas=Receta.query.all(), usuario_id = usuario_actual.id)
    else:
        return redirect(url_for("iniciarSesion"))



@app.route("/ranking")
def consultarRanking():
    if usuario_actual is not None:
        lista = Receta.query.all()
        recetas = []
        i = 0
        while i < 5 and i < len(lista):
            unaReceta = None
            indice = 0
            for j in range(len(lista)):
                aux:Receta = lista[j]
                if aux!=None and (unaReceta == None or unaReceta.cantidadMeGusta < aux.cantidadMeGusta):
                    unaReceta = aux
                    indice = j
            recetas.append(unaReceta)
            lista[indice] = None
            i += 1
        return render_template("consultar_recetas.html", titulo="Ranking",recetas=recetas)
    else:
        return redirect(url_for("iniciarSesion"))



@app.route("/consultar_recetas_tiempo", methods=["POST", "GET"])
def consultarRecetasTiempo():
    if request.method=="POST":
        recetas = Receta.query.filter_by(tiempo=request.form["tiempo"])
        return render_template("consultar_recetas.html", recetas=recetas)
    else:
        return render_template("filtrar_recetas_tiempo.html")



@app.route("/mostrar_receta/<id_receta>")
def mostrarReceta(id_receta):
    if usuario_actual is not None:
        id_receta = int(id_receta)
        una_receta = Receta.query.get(id_receta)
        ingredientes = Ingrediente.query.filter_by(recetaid=id_receta)
        return render_template("mostrar_receta.html", una_receta=una_receta, usuario_id = usuario_actual.id, iteracion=1, ingredientes=ingredientes)
    else:
        return redirect(url_for("inicarSesion"))



@app.route("/dar_me_gusta/<id_receta>/<iteracion>", methods=["POST", "GET"])
def darMeGusta(id_receta, iteracion):
    if request.method == "POST":
        id_receta = int(id_receta)
        iteracion=int(iteracion)
        receta = Receta.query.get(id_receta)
        receta.cantidadMeGusta = Receta.cantidadMeGusta + 1
        db.session.commit()
        return render_template("mostrar_receta.html", una_receta=receta, iteracion=iteracion)
    else:
        return render_template("error.html", mensaje="Error al dar me gusta")



@app.route("/recetas_por_ingrediente", methods=["POST", "GET"])
def recetasPorIngrediente():
    if request.method == "POST":
        nombre_ingrediente = request.form["ingrediente"]
        nombre_ingrediente = "%{}%".format(nombre_ingrediente)
        recetas = Receta.query.join(Receta.ingredientes).filter(Ingrediente.nombre.like(nombre_ingrediente)).all()

        return render_template("/consultar_recetas.html", recetas=recetas, usuario_id=usuario_actual.id)
    else:
        return render_template("filtrar_recetas_ingrediente.html")



@app.route("/logout")
def cerrarSesion():
    global usuario_actual
    usuario_actual = None
    return redirect(url_for("iniciarSesion"))



if __name__ == "__main__":
    app.run(debug=True)