# frontend.py
import requests
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = "SUPER_SECRET_KEY"  # Clé pour la session, à personnaliser

# Modifiez cette variable pour pointer vers l'URL de votre API
# Par exemple si votre API est disponible sur http://localhost:5000
API_BASE_URL = "http://localhost:5000"

#
# Fonction utilitaire pour injecter le token dans l'en-tête Authorization
#
def api_headers():
    """
    Retourne un dictionnaire d'en-têtes incluant le Bearer token
    si l'utilisateur est connecté. Sinon, retourne un dict vide.
    """
    token = session.get("jwt_token")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers

#
# Page d’accueil : on redirige souvent vers /login s’il n’y a pas de token
#
@app.route("/")
def index():
    if "jwt_token" not in session:
        return redirect(url_for("login"))
    return redirect(url_for("orders"))

#
# Connexion (login)
#
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        payload = {"username": username, "password": password}

        try:
            resp = requests.post(f"{API_BASE_URL}/login", json=payload)
            if resp.status_code == 200:
                data = resp.json()
                # L'API supposée renvoyer un champ "token" et éventuellement "role"
                session["jwt_token"] = data["token"]
                session["role"] = data.get("role", "user")
                flash("Connexion réussie", "success")
                return redirect(url_for("orders"))
            else:
                flash("Identifiants invalides ou erreur de connexion", "danger")
        except Exception as e:
            flash(f"Erreur lors de la connexion : {str(e)}", "danger")

    return render_template("login.html")

#
# Déconnexion
#
@app.route("/logout")
def logout():
    session.clear()
    flash("Vous êtes déconnecté.", "info")
    return redirect(url_for("login"))

#
# Inscription (register)
#
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        role     = request.form.get("role", "user")

        payload = {
            "username": username,
            "password": password,
            "role": role
        }

        try:
            resp = requests.post(f"{API_BASE_URL}/register", json=payload)
            if resp.status_code == 201:
                flash("Inscription réussie ! Vous pouvez maintenant vous connecter.", "success")
                return redirect(url_for("login"))
            else:
                flash("Erreur à l'inscription (utilisateur existant ou champs manquants)", "danger")
        except Exception as e:
            flash(f"Erreur lors de l'inscription : {str(e)}", "danger")

    return render_template("register.html")

#
# Liste des commandes (orders)
#
@app.route("/orders")
def orders():
    if "jwt_token" not in session:
        return redirect(url_for("login"))

    try:
        resp = requests.get(f"{API_BASE_URL}/orders", headers=api_headers())
        if resp.status_code == 200:
            orders_data = resp.json()  # votre API doit renvoyer la liste de commandes
            # On passe le role également (stocké en session)
            return render_template("orders.html", orders=orders_data, role=session.get("role"))
        else:
            flash("Impossible de récupérer les commandes (token invalide ?).", "danger")
            return redirect(url_for("logout"))
    except Exception as e:
        flash(f"Erreur lors de la récupération des commandes : {str(e)}", "danger")
        return redirect(url_for("logout"))

#
# Créer une commande
#
@app.route("/create_order", methods=["GET", "POST"])
def create_order():
    if "jwt_token" not in session:
        return redirect(url_for("login"))

    # Pour afficher la liste des produits dans le formulaire
    try:
        products_resp = requests.get(f"{API_BASE_URL}/products", headers=api_headers())
        products_data = products_resp.json() if products_resp.status_code == 200 else []
    except Exception:
        products_data = []

    if request.method == "POST":
        # On récupère les champs du formulaire
        product_id = request.form.get("product_id")
        quantity   = request.form.get("quantity")
        price      = request.form.get("price")       # utile seulement si admin
        status     = request.form.get("status")      # idem

        # Construction du JSON à envoyer (selon swagger).
        # L'API attend (product_name, quantity, [price], [status]).
        # Ici on doit éventuellement récupérer le nom du produit à partir de l'ID
        # selon comment vous avez conçu le back. 
        # Si l'API attend product_name, on doit le retrouver via products_data:
        selected_product = next((p for p in products_data if str(p["id"]) == product_id), None)
        product_name = selected_product["name"] if selected_product else "Unknown"

        payload = {
            "product_name": product_name,
            "quantity": int(quantity)
        }
        # Pour l'admin, on ajoute price et status si fournis
        if session.get("role") == "admin":
            if price:
                payload["price"] = float(price)
            if status:
                payload["status"] = status

        try:
            resp = requests.post(f"{API_BASE_URL}/orders", json=payload, headers=api_headers())
            if resp.status_code == 201:
                flash("Commande créée avec succès.", "success")
                return redirect(url_for("orders"))
            else:
                flash("Échec de la création de la commande.", "danger")
        except Exception as e:
            flash(f"Erreur lors de la création de la commande : {str(e)}", "danger")

    return render_template("create_order.html", products=products_data, role=session.get("role"))

#
# Mettre à jour une commande
#
@app.route("/update_order/<int:order_id>", methods=["GET", "POST"])
def update_order(order_id):
    if "jwt_token" not in session:
        return redirect(url_for("login"))

    # Récupérer la commande actuelle
    try:
        order_resp = requests.get(f"{API_BASE_URL}/orders/{order_id}", headers=api_headers())
        if order_resp.status_code == 200:
            order_data = order_resp.json()
        else:
            flash("Commande introuvable ou accès refusé.", "danger")
            return redirect(url_for("orders"))
    except Exception as e:
        flash(f"Erreur de récupération de la commande : {str(e)}", "danger")
        return redirect(url_for("orders"))

    # Récupérer la liste des produits (pour le dropdown)
    try:
        products_resp = requests.get(f"{API_BASE_URL}/products", headers=api_headers())
        products_data = products_resp.json() if products_resp.status_code == 200 else []
    except Exception:
        products_data = []

    if request.method == "POST":
        product_id = request.form.get("product_id")
        quantity   = request.form.get("quantity")
        price      = request.form.get("price")  # admin seulement
        status     = request.form.get("status") # admin seulement

        # On retrouve le nom du produit
        selected_product = next((p for p in products_data if str(p["id"]) == product_id), None)
        product_name = selected_product["name"] if selected_product else order_data.get("product_name", "")

        # On reconstruit le payload en fonction du swagger
        payload = {
            "product_name": product_name,
            "quantity": int(quantity) if quantity else order_data["quantity"]
        }
        # Si admin
        if session.get("role") == "admin":
            if price:
                payload["price"] = float(price)
            if status:
                payload["status"] = status
        else:
            # Normal user peut éventuellement mettre status="canceled"
            # Mais c’est déjà géré côté API si besoin.
            pass

        try:
            resp = requests.put(f"{API_BASE_URL}/orders/{order_id}", json=payload, headers=api_headers())
            if resp.status_code == 200:
                flash("Commande mise à jour avec succès.", "success")
            elif resp.status_code == 403:
                flash("Autorisation refusée pour cette mise à jour.", "danger")
            else:
                flash("Erreur lors de la mise à jour de la commande.", "danger")
        except Exception as e:
            flash(f"Erreur lors de la mise à jour : {str(e)}", "danger")

        return redirect(url_for("orders"))

    # Affiche la page d'édition
    return render_template("update_order.html", order=order_data, products=products_data, role=session.get("role"))

#
# Supprimer une commande (admin seulement)
#
@app.route("/delete_order/<int:order_id>")
def delete_order(order_id):
    if "jwt_token" not in session:
        return redirect(url_for("login"))

    try:
        resp = requests.delete(f"{API_BASE_URL}/orders/{order_id}", headers=api_headers())
        if resp.status_code == 200:
            flash("Commande supprimée.", "info")
        elif resp.status_code == 403:
            flash("Vous n’avez pas le droit de supprimer cette commande.", "danger")
        else:
            flash("Erreur lors de la suppression de la commande.", "danger")
    except Exception as e:
        flash(f"Erreur : {str(e)}", "danger")

    return redirect(url_for("orders"))

#
# Annuler une commande (pour un user normal)
#
@app.route("/cancel_order/<int:order_id>", methods=["POST"])
def cancel_order(order_id):
    if "jwt_token" not in session:
        return redirect(url_for("login"))

    # Mettre status="canceled"
    payload = {"status": "canceled"}
    try:
        resp = requests.put(f"{API_BASE_URL}/orders/{order_id}", json=payload, headers=api_headers())
        if resp.status_code == 200:
            flash("Commande annulée.", "info")
        else:
            flash("Impossible d’annuler la commande.", "danger")
    except Exception as e:
        flash(f"Erreur lors de l’annulation : {str(e)}", "danger")

    return redirect(url_for("orders"))

#
# Liste des produits
#
@app.route("/products")
def products():
    if "jwt_token" not in session:
        return redirect(url_for("login"))

    try:
        resp = requests.get(f"{API_BASE_URL}/products", headers=api_headers())
        if resp.status_code == 200:
            products_data = resp.json()
        else:
            products_data = []
            flash("Impossible de récupérer la liste des produits.", "danger")
    except Exception as e:
        products_data = []
        flash(f"Erreur : {str(e)}", "danger")

    return render_template("products.html", products=products_data, role=session.get("role"))

#
# Créer un produit (admin). Dans l’exemple HTML, on le fait directement sur la page /products
# => Le form POST va sur /create_product (traitement)
#
@app.route("/create_product", methods=["POST"])
def create_product():
    if "jwt_token" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "admin":
        flash("Vous n’avez pas les droits pour créer un produit.", "danger")
        return redirect(url_for("products"))

    name  = request.form.get("name")
    price = request.form.get("price")
    payload = {"name": name, "price": float(price)}

    try:
        resp = requests.post(f"{API_BASE_URL}/products", json=payload, headers=api_headers())
        if resp.status_code == 201:
            flash("Produit créé avec succès.", "success")
        else:
            flash("Échec de la création du produit.", "danger")
    except Exception as e:
        flash(f"Erreur lors de la création du produit : {str(e)}", "danger")

    return redirect(url_for("products"))

#
# Mettre à jour un produit (admin)
#
@app.route("/update_product/<int:product_id>", methods=["GET", "POST"])
def update_product(product_id):
    if "jwt_token" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "admin":
        flash("Vous n’avez pas les droits pour modifier un produit.", "danger")
        return redirect(url_for("products"))

    # Récupérer le produit existant
    try:
        resp = requests.get(f"{API_BASE_URL}/products/{product_id}", headers=api_headers())
        if resp.status_code == 200:
            product_data = resp.json()
        else:
            flash("Produit introuvable.", "danger")
            return redirect(url_for("products"))
    except Exception as e:
        flash(f"Erreur : {str(e)}", "danger")
        return redirect(url_for("products"))

    if request.method == "POST":
        name  = request.form.get("name") or product_data["name"]
        price = request.form.get("price") or product_data["price"]

        payload = {"name": name, "price": float(price)}
        try:
            update_resp = requests.put(f"{API_BASE_URL}/products/{product_id}",
                                       json=payload, headers=api_headers())
            if update_resp.status_code == 200:
                flash("Produit mis à jour.", "success")
            else:
                flash("Échec de la mise à jour du produit.", "danger")
        except Exception as e:
            flash(f"Erreur : {str(e)}", "danger")

        return redirect(url_for("products"))

    return render_template("update_product.html", product=product_data)

#
# Supprimer un produit (admin)
#
@app.route("/delete_product/<int:product_id>")
def delete_product(product_id):
    if "jwt_token" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "admin":
        flash("Vous n’avez pas les droits pour supprimer un produit.", "danger")
        return redirect(url_for("products"))

    try:
        resp = requests.delete(f"{API_BASE_URL}/products/{product_id}", headers=api_headers())
        if resp.status_code == 200:
            flash("Produit supprimé.", "info")
        else:
            flash("Impossible de supprimer ce produit.", "danger")
    except Exception as e:
        flash(f"Erreur : {str(e)}", "danger")

    return redirect(url_for("products"))

#
# Panel Admin pour gérer les utilisateurs
#
@app.route("/admin")
def admin_panel():
    if "jwt_token" not in session:
        return redirect(url_for("login"))

    # Seul l'admin peut voir la liste des utilisateurs
    if session.get("role") != "admin":
        flash("Accès interdit : vous n’êtes pas admin.", "danger")
        return redirect(url_for("orders"))

    try:
        resp = requests.get(f"{API_BASE_URL}/users", headers=api_headers())
        if resp.status_code == 200:
            users_data = resp.json()
        else:
            users_data = []
            flash("Impossible de récupérer la liste des utilisateurs.", "danger")
    except Exception as e:
        users_data = []
        flash(f"Erreur : {str(e)}", "danger")

    return render_template("admin.html", users=users_data)



# Mettre à jour un utilisateur (admin ou owner)
#
@app.route("/update_user/<int:user_id>", methods=["GET", "POST"])
def update_user(user_id):
    if "jwt_token" not in session:
        return redirect(url_for("login"))

    # Récupérer les infos existantes de l'utilisateur
    try:
        resp = requests.get(f"{API_BASE_URL}/users/{user_id}", headers=api_headers())
        if resp.status_code == 200:
            user_data = resp.json()
        else:
            flash("Utilisateur introuvable ou droits insuffisants.", "danger")
            return redirect(url_for("admin_panel") if session.get("role") == "admin" else url_for("orders"))
    except Exception as e:
        flash(f"Erreur : {str(e)}", "danger")
        return redirect(url_for("admin_panel") if session.get("role") == "admin" else url_for("orders"))

    # Vérifier si c’est le propriétaire ou un admin
    is_owner = (session.get("role") == "admin") or (user_data["id"] == user_id)
    if not is_owner:
        flash("Vous ne pouvez pas modifier un autre utilisateur.", "danger")
        return redirect(url_for("orders"))

    if request.method == "POST":
        password = request.form.get("password")
        role     = request.form.get("role")

        payload = {}
        if password:
            payload["password"] = password
        if role:  # l’admin peut changer le rôle; un user normal ne devrait pas y accéder
            payload["role"] = role

        try:
            update_resp = requests.put(f"{API_BASE_URL}/users/{user_id}", json=payload, headers=api_headers())
            if update_resp.status_code == 200:
                flash("Utilisateur mis à jour avec succès.", "success")
            elif update_resp.status_code == 403:
                flash("Autorisation refusée.", "danger")
            else:
                flash("Échec de la mise à jour de l’utilisateur.", "danger")
        except Exception as e:
            flash(f"Erreur : {str(e)}", "danger")

        if session.get("role") == "admin":
            return redirect(url_for("admin_panel"))
        else:
            # Si c'est un user normal qui modifie son propre compte
            return redirect(url_for("orders"))

    return render_template("update_user.html", user=user_data)

#
# Supprimer un utilisateur (admin uniquement)
#
@app.route("/admin_delete_user/<int:user_id>")
def admin_delete_user(user_id):
    if "jwt_token" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "admin":
        flash("Accès refusé.", "danger")
        return redirect(url_for("orders"))

    try:
        resp = requests.delete(f"{API_BASE_URL}/users/{user_id}", headers=api_headers())
        if resp.status_code == 200:
            flash("Utilisateur supprimé.", "info")
        elif resp.status_code == 404:
            flash("Utilisateur introuvable.", "danger")
        else:
            flash("Impossible de supprimer cet utilisateur.", "danger")
    except Exception as e:
        flash(f"Erreur : {str(e)}", "danger")

    return redirect(url_for("admin_panel"))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
