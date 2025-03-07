#Version 1 
#07/03/2025
#Aurore, Malorie, Louise
import os
import json
import bcrypt
import jwt
import datetime

from flask import Flask, request, jsonify, g
from flasgger import Swagger
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'MDP'


# Configuration Swagger

app.config['SWAGGER'] = {
    'title': 'TP API',
    'uiversion': 3,
    # Définition de la sécurité pour le Bearer token (JWT)
    'securityDefinitions': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
            'description': "Ajouter 'Bearer <votre_token_jwt>' dans le champ d'authentification"
        }
    },
    'security': [
        {
            'Bearer': []
        }
    ]
}

swagger = Swagger(app)

# Fichiers JSON
USERS_FILE = 'users.json'
ORDERS_FILE = 'orders.json'
PRODUCTS_FILE = 'products.json'

#Fonctions utilitaires

def load_json(filename):
    if not os.path.exists(filename):
        return []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (IOError, ValueError):
        return []

def save_json(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def init_json_files():
    if not os.path.exists(USERS_FILE):
        save_json(USERS_FILE, [])
    if not os.path.exists(ORDERS_FILE):
        save_json(ORDERS_FILE, [])
    if not os.path.exists(PRODUCTS_FILE):
        save_json(PRODUCTS_FILE, [])

def generate_token(user_id, role):
    payload = {
        'user_id': user_id,
        'role': role,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
    }
    token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
    return token

def decode_token(token):
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        raise Exception("Token expiré.")
    except jwt.InvalidTokenError:
        raise Exception("Token invalide.")

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', None)
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({'message': 'Token manquant ou invalide'}), 401

        token = auth_header.split(" ")[1]
        try:
            payload = decode_token(token)
            g.user_id = payload['user_id']
            g.user_role = payload['role']
        except Exception as e:
            return jsonify({'message': str(e)}), 401

        return f(*args, **kwargs)
    return decorated

def role_required(required_role):
    def wrapper(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if g.get('user_role') != required_role:
                return jsonify({'message': 'Autorisation refusée'}), 403
            return f(*args, **kwargs)
        return decorated
    return wrapper

def get_next_id(items_list):
    if not items_list:
        return 1
    return max(item['id'] for item in items_list) + 1

#Routes d’auth

@app.route('/register', methods=['POST'])
def register():
    """
    Crée un nouvel utilisateur (inscription).
    ---
    parameters:
      - in: body
        name: user
        description: Données du nouvel utilisateur
        schema:
          type: object
          required:
            - username
            - password
          properties:
            username:
              type: string
            password:
              type: string
            role:
              type: string
              description: 'Optionnel, par défaut user'
    responses:
      201:
        description: Utilisateur créé avec succès
      400:
        description: utilisateur existant ou champs manquants
    """
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    role = data.get('role', 'user')

    if not username or not password:
        return jsonify({'message': 'username et password sont requis'}), 400

    users = load_json(USERS_FILE)
    for user in users:
        if user['username'] == username:
            return jsonify({'message': 'Cet utilisateur existe déjà'}), 400

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    new_user = {
        'id': get_next_id(users),
        'username': username,
        'password': hashed_password.decode('utf-8'),
        'role': role
    }
    users.append(new_user)
    save_json(USERS_FILE, users)

    return jsonify({'message': 'Utilisateur créé avec succès'}), 201

@app.route('/login', methods=['POST'])
def login():
    """
    Authentifie un utilisateur et renvoie un token JWT.
    ---
    parameters:
      - in: body
        name: credentials
        description: Identifiants de l'utilisateur
        schema:
          type: object
          required:
            - username
            - password
          properties:
            username:
              type: string
            password:
              type: string
    responses:
      200:
        description: Connexion réussie (retourne token et rôle)
      401:
        description: Identifiants invalides
    """
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'username et password sont requis'}), 401

    users = load_json(USERS_FILE)
    user_found = next((u for u in users if u['username'] == username), None)
    if not user_found:
        return jsonify({'message': 'Utilisateur non trouvé'}), 401

    hashed_password_db = user_found['password'].encode('utf-8')
    if bcrypt.hashpw(password.encode('utf-8'), hashed_password_db) != hashed_password_db:
        return jsonify({'message': 'Mot de passe incorrect'}), 401

    token = generate_token(user_found['id'], user_found['role'])
    return jsonify({
        'message': 'Connexion réussie',
        'token': token,
        'role': user_found['role']
    }), 200

#Routes Utilisateurs

@app.route('/users', methods=['GET'])
@token_required
@role_required('admin')
def get_users():
    """
    Récupère la liste de tous les utilisateurs (réservé à l'admin).
    ---
    security:
      - Bearer: []
    responses:
      200:
        description: Liste des utilisateurs
      401:
        description: Token invalide ou manquant
      403:
        description: Autorisation refusée (rôle manquant)
    """
    users = load_json(USERS_FILE)
    result = []
    for u in users:
        result.append({
            'id': u['id'],
            'username': u['username'],
            'role': u['role']
        })
    return jsonify(result), 200

@app.route('/users/<int:user_id>', methods=['GET'])
@token_required
def get_user(user_id):
    """
    Récupère les infos d'un utilisateur (admin ou owner seulement).
    ---
    security:
      - Bearer: []
    parameters:
      - in: path
        name: user_id
        type: integer
        required: true
    responses:
      200:
        description: Détails de l'utilisateur
      403:
        description: Autorisation refusée
      404:
        description: Utilisateur introuvable
    """
    if g.user_role != 'admin' and g.user_id != user_id:
        return jsonify({'message': 'Autorisation refusée'}), 403

    users = load_json(USERS_FILE)
    user_found = next((u for u in users if u['id'] == user_id), None)
    if not user_found:
        return jsonify({'message': 'Utilisateur introuvable'}), 404

    result = {
        'id': user_found['id'],
        'username': user_found['username'],
        'role': user_found['role']
    }
    return jsonify(result), 200

@app.route('/users/<int:user_id>', methods=['PUT'])
@token_required
def update_user(user_id):
    """
    Modifie un utilisateur (admin ou owner).
    ---
    security:
      - Bearer: []
    parameters:
      - in: path
        name: user_id
        required: true
        type: integer
      - in: body
        name: user_data
        schema:
          type: object
          properties:
            password:
              type: string
            role:
              type: string
    responses:
      200:
        description: Utilisateur mis à jour
      403:
        description: Autorisation refusée
      404:
        description: Utilisateur introuvable
    """
    if g.user_role != 'admin' and g.user_id != user_id:
        return jsonify({'message': 'Autorisation refusée'}), 403

    data = request.get_json()
    new_password = data.get('password')
    new_role = data.get('role')

    users = load_json(USERS_FILE)
    user_found = next((u for u in users if u['id'] == user_id), None)
    if not user_found:
        return jsonify({'message': 'Utilisateur introuvable'}), 404

    if new_password:
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        user_found['password'] = hashed_password.decode('utf-8')

    if new_role and g.user_role == 'admin':
        user_found['role'] = new_role

    save_json(USERS_FILE, users)
    return jsonify({'message': 'Utilisateur mis à jour avec succès'}), 200

@app.route('/users/<int:user_id>', methods=['DELETE'])
@token_required
@role_required('admin')
def delete_user(user_id):
    """
    Supprime un utilisateur (admin seulement).
    ---
    security:
      - Bearer: []
    parameters:
      - in: path
        name: user_id
        required: true
        type: integer
    responses:
      200:
        description: Utilisateur supprimé
      404:
        description: Utilisateur introuvable
      403:
        description: Autorisation refusée
    """
    users = load_json(USERS_FILE)
    user_found = next((u for u in users if u['id'] == user_id), None)

    if not user_found:
        return jsonify({'message': 'Utilisateur introuvable'}), 404

    users = [u for u in users if u['id'] != user_id]
    save_json(USERS_FILE, users)
    return jsonify({'message': 'Utilisateur supprimé avec succès'}), 200

# -------------------------------------------------------------------
#                      Routes Produits (Products)
# -------------------------------------------------------------------

@app.route('/products', methods=['GET'])
def get_products():
    """
    Récupère la liste de tous les produits (accessible à tous).
    ---
    responses:
      200:
        description: Liste de produits
    """
    products = load_json(PRODUCTS_FILE)
    return jsonify(products), 200

@app.route('/products', methods=['POST'])
@token_required
@role_required('admin')
def create_product():
    """
    Crée un produit (admin seulement).
    ---
    security:
      - Bearer: []
    parameters:
      - in: body
        name: product
        schema:
          type: object
          required:
            - name
            - price
          properties:
            name:
              type: string
            price:
              type: number
    responses:
      201:
        description: Produit créé
      400:
        description: Champs manquants
    """
    data = request.get_json()
    name = data.get('name')
    price = data.get('price')

    if not name or price is None:
        return jsonify({'message': 'Les champs name et price sont requis'}), 400

    products = load_json(PRODUCTS_FILE)
    new_id = get_next_id(products)

    new_product = {
        'id': new_id,
        'name': name,
        'price': price
    }
    products.append(new_product)
    save_json(PRODUCTS_FILE, products)

    return jsonify({'message': 'Produit créé avec succès'}), 201

@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """
    Récupère un produit par son ID (accessible à tous).
    ---
    parameters:
      - in: path
        name: product_id
        type: integer
        required: true
    responses:
      200:
        description: Informations du produit
      404:
        description: Produit introuvable
    """
    products = load_json(PRODUCTS_FILE)
    product_found = next((p for p in products if p['id'] == product_id), None)
    if not product_found:
        return jsonify({'message': 'Produit introuvable'}), 404
    return jsonify(product_found), 200

@app.route('/products/<int:product_id>', methods=['PUT'])
@token_required
@role_required('admin')
def update_product(product_id):
    """
    Met à jour un produit (admin seulement).
    ---
    security:
      - Bearer: []
    parameters:
      - in: path
        name: product_id
        type: integer
        required: true
      - in: body
        name: product_data
        schema:
          type: object
          properties:
            name:
              type: string
            price:
              type: number
    responses:
      200:
        description: Produit mis à jour
      404:
        description: Produit introuvable
      403:
        description: Autorisation refusée
    """
    data = request.get_json()
    new_name = data.get('name')
    new_price = data.get('price')

    products = load_json(PRODUCTS_FILE)
    product_found = next((p for p in products if p['id'] == product_id), None)
    if not product_found:
        return jsonify({'message': 'Produit introuvable'}), 404

    if new_name:
        product_found['name'] = new_name
    if new_price is not None:
        product_found['price'] = new_price

    save_json(PRODUCTS_FILE, products)
    return jsonify({'message': 'Produit mis à jour avec succès'}), 200

@app.route('/products/<int:product_id>', methods=['DELETE'])
@token_required
@role_required('admin')
def delete_product(product_id):
    """
    Supprime un produit (admin seulement).
    ---
    security:
      - Bearer: []
    parameters:
      - in: path
        name: product_id
        type: integer
        required: true
    responses:
      200:
        description: Produit supprimé
      404:
        description: Produit introuvable
    """
    products = load_json(PRODUCTS_FILE)
    product_found = next((p for p in products if p['id'] == product_id), None)
    if not product_found:
        return jsonify({'message': 'Produit introuvable'}), 404

    products = [p for p in products if p['id'] != product_id]
    save_json(PRODUCTS_FILE, products)
    return jsonify({'message': 'Produit supprimé avec succès'}), 200

# Routes Orders

@app.route('/orders', methods=['POST'])
@token_required
def create_order():
    """
    Crée une nouvelle commande (JWT requis).
    ---
    security:
      - Bearer: []
    parameters:
      - in: body
        name: order
        description: Données de la commande
        schema:
          type: object
          required:
            - product_name
            - quantity
          properties:
            product_name:
              type: string
            quantity:
              type: integer
    responses:
      201:
        description: Commande créée
      400:
        description: Champs obligatoires manquants ou produit non trouvé
      401:
        description: Token invalide ou expiré
    """
    data = request.get_json()
    product_name = data.get('product_name')
    quantity = data.get('quantity')

    if not product_name or quantity is None:
        return jsonify({'message': 'Les champs product_name et quantity sont requis'}), 400

    # Charger les produits
    products = load_json(PRODUCTS_FILE)
    product = next((p for p in products if p['name'].lower() == product_name.lower()), None)

    if not product:
        return jsonify({'message': 'Produit non trouvé'}), 400

    # Calculer le prix total
    price = product['price'] * quantity

    # Si c'est un admin, on peut prendre le status envoyé (sinon, on force "pending")
    status = data.get('status', 'pending') if g.user_role == 'admin' else 'pending'

    orders = load_json(ORDERS_FILE)
    new_id = get_next_id(orders)

    new_order = {
        'id': new_id,
        'product_name': product_name,
        'quantity': quantity,
        'price': price,
        'status': status,
        'user_id': g.user_id
    }
    orders.append(new_order)
    save_json(ORDERS_FILE, orders)

    return jsonify({'message': 'Commande créée avec succès'}), 201

@app.route('/orders', methods=['GET'])
@token_required
def get_orders():
    """
    Récupère toutes les commandes (admin) ou celles de l'utilisateur connecté.
    ---
    security:
      - Bearer: []
    responses:
      200:
        description: Liste des commandes
      401:
        description: Token invalide ou expiré
    """
    orders = load_json(ORDERS_FILE)
    if g.user_role == 'admin':
        visible_orders = orders
    else:
        visible_orders = [o for o in orders if o['user_id'] == g.user_id]
    return jsonify(visible_orders), 200

@app.route('/orders/<int:order_id>', methods=['GET'])
@token_required
def get_order(order_id):
    """
    Récupère une commande par son ID (admin ou owner).
    ---
    security:
      - Bearer: []
    parameters:
      - in: path
        name: order_id
        type: integer
        required: true
    responses:
      200:
        description: Détails de la commande
      403:
        description: Autorisation refusée
      404:
        description: Commande introuvable
    """
    orders = load_json(ORDERS_FILE)
    order = next((o for o in orders if o['id'] == order_id), None)
    if not order:
        return jsonify({'message': 'Commande introuvable'}), 404

    if g.user_role != 'admin' and order['user_id'] != g.user_id:
        return jsonify({'message': 'Autorisation refusée'}), 403

    return jsonify(order), 200

@app.route('/orders/<int:order_id>', methods=['PUT'])
@token_required
def update_order(order_id):
    """
    Met à jour une commande (admin ou owner).
    - L'admin peut modifier le prix et le status.
    - L'utilisateur normal peut modifier product_name, quantity et mettre status = 'canceled'.
    ---
    security:
      - Bearer: []
    parameters:
      - in: path
        name: order_id
        type: integer
        required: true
      - in: body
        name: order_data
        schema:
          type: object
          properties:
            product_name:
              type: string
            quantity:
              type: integer
            price:
              type: number
            status:
              type: string
    responses:
      200:
        description: Commande mise à jour
      403:
        description: Autorisation refusée
      404:
        description: Commande introuvable
    """
    data = request.get_json()
    new_product_name = data.get('product_name')
    new_quantity = data.get('quantity')
    new_price = data.get('price')
    new_status = data.get('status')

    orders = load_json(ORDERS_FILE)
    order = next((o for o in orders if o['id'] == order_id), None)

    if not order:
        return jsonify({'message': 'Commande introuvable'}), 404

    if g.user_role != 'admin' and order['user_id'] != g.user_id:
        return jsonify({'message': 'Autorisation refusée'}), 403

    products = load_json(PRODUCTS_FILE)

    if new_product_name:
        product = next((p for p in products if p['name'].lower() == new_product_name.lower()), None)
        if not product:
            return jsonify({'message': 'Produit non trouvé'}), 400
        order['product_name'] = new_product_name
        order['price'] = product['price'] * order['quantity']

    if new_quantity is not None:
        order['quantity'] = new_quantity
        product = next((p for p in products if p['name'].lower() == order['product_name'].lower()), None)
        if product:
            order['price'] = product['price'] * new_quantity

    if g.user_role == 'admin':
        if new_price is not None:
            order['price'] = new_price
    # user normal => on ignore le price

    if new_status is not None:
        if g.user_role == 'admin':
            order['status'] = new_status
        else:
            if new_status == 'canceled':
                order['status'] = 'canceled'
            # sinon, on ignore

    save_json(ORDERS_FILE, orders)
    return jsonify({'message': 'Commande mise à jour avec succès'}), 200

@app.route('/orders/<int:order_id>', methods=['DELETE'])
@token_required
def delete_order(order_id):
    """
    Supprime une commande (admin seulement).
    ---
    security:
      - Bearer: []
    parameters:
      - in: path
        name: order_id
        type: integer
        required: true
    responses:
      200:
        description: Commande supprimée
      403:
        description: Autorisation refusée
      404:
        description: Commande introuvable
    """
    orders = load_json(ORDERS_FILE)
    order = next((o for o in orders if o['id'] == order_id), None)

    if not order:
        return jsonify({'message': 'Commande introuvable'}), 404

    if g.user_role != 'admin':
        return jsonify({'message': 'Autorisation refusée : vous ne pouvez pas supprimer la commande.'}), 403

    orders = [o for o in orders if o['id'] != order_id]
    save_json(ORDERS_FILE, orders)
    return jsonify({'message': 'Commande supprimée avec succès'}), 200

# start du script

if __name__ == '__main__':
    init_json_files()
    app.run(debug=True, host='0.0.0.0')
