from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId

app = Flask(__name__)

# Conexión a MongoDB (con respaldo automático en memoria si el servicio local está apagado)
usar_mongo = True
try:
    cliente = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=2000)
    cliente.server_info()
    db = cliente["inventario_inteligente"]
    coleccion_productos = db["productos"]
except Exception:
    usar_mongo = False
    productos_memoria = [
        {"_id": "1", "codigo_rfid": "RFID-1001", "nombre": "Lector Código de Barras Láser", "categoria": "Hardware", "stock": 15, "precio": 180000},
        {"_id": "2", "codigo_rfid": "RFID-1002", "nombre": "Etiquetas Inteligentes RFID x100", "categoria": "Insumos", "stock": 40, "precio": 45000}
    ]

# Ruta principal: Interfaz Web y Móvil (Responsive)
@app.route("/")
def inicio():
    return render_template("index.html")

# API REST: Consultar todos los productos (GET)
@app.route("/api/productos", methods=["GET"])
def obtener_productos():
    if usar_mongo:
        lista = []
        for p in coleccion_productos.find():
            p["_id"] = str(p["_id"])
            lista.append(p)
        return jsonify(lista), 200
    return jsonify(productos_memoria), 200

# API REST: Registrar nuevo producto por código de barras/RFID (POST)
@app.route("/api/productos", methods=["POST"])
def crear_producto():
    datos = request.json
    nuevo = {
        "codigo_rfid": datos.get("codigo_rfid"),
        "nombre": datos.get("nombre"),
        "categoria": datos.get("categoria"),
        "stock": int(datos.get("stock", 0)),
        "precio": float(datos.get("precio", 0))
    }
    if usar_mongo:
        res = coleccion_productos.insert_one(nuevo)
        nuevo["_id"] = str(res.inserted_id)
    else:
        nuevo["_id"] = str(len(productos_memoria) + 1)
        productos_memoria.append(nuevo)
    return jsonify({"mensaje": "Producto registrado con éxito", "producto": nuevo}), 201

# API REST: Actualizar stock o datos de producto (PUT)
@app.route("/api/productos/<id>", methods=["PUT"])
def actualizar_producto(id):
    datos = request.json
    actualizacion = {
        "codigo_rfid": datos.get("codigo_rfid"),
        "nombre": datos.get("nombre"),
        "categoria": datos.get("categoria"),
        "stock": int(datos.get("stock", 0)),
        "precio": float(datos.get("precio", 0))
    }
    if usar_mongo:
        coleccion_productos.update_one({"_id": ObjectId(id)}, {"$set": actualizacion})
    else:
        for p in productos_memoria:
            if p["_id"] == id:
                p.update(actualizacion)
    return jsonify({"mensaje": "Producto actualizado correctamente"}), 200

# API REST: Eliminar producto (DELETE)
@app.route("/api/productos/<id>", methods=["DELETE"])
def eliminar_producto(id):
    if usar_mongo:
        coleccion_productos.delete_one({"_id": ObjectId(id)})
    else:
        global productos_memoria
        productos_memoria = [p for p in productos_memoria if p["_id"] != id]
    return jsonify({"mensaje": "Producto eliminado del inventario"}), 200

if __name__ == "__main__":
    app.run(debug=True, port=5000)
