# API de gestion des utilisateurs et des commandes

Ce projet vise à développer une API REST complète permettant la gestion des utilisateurs, des commandes et des produits. L'API prend en charge les actions essentielles (GET, POST, PUT, DELETE, PATCH) sur ces ressources. Elle intègre également un système de génération de tokens d'authentification et sera déployée sur notre infrastructure.

## Fonctionnalités

L'API dispose des fonctionnalités suivantes pour les endpoints `authentification`, `commandes`, `utilisateurs` et `produits` :

- **GET** : Récupérer une liste de ressources ou une ressource spécifique.
- **POST** : Créer une nouvelle ressource.
- **PUT** : Mettre à jour une ressource existante.
- **DELETE** : Supprimer une ressource existante.
- **PATCH** : Mettre à jour partiellement une ressource.

## API Collection

### Authentification

- **POST /login** : Authentifier un utilisateur et retourner un token JWT.
- **POST /register** : Créer un compte utilisateur et obtenir un token.

Le token JWT devra être inclus dans l'en-tête `Authorization` de toutes les requêtes nécessitant une authentification :
```sh
Authorization: Bearer {token}
```

### Commandes

- **GET /orders** : Liste des commandes.
- **POST /orders** : Créer une commande.
- **GET /orders/{id}** : Récupérer une commande par son ID.
- **PUT /orders/{id}** : Modifier une commande.
- **DELETE /orders/{id}** : Supprimer une commande.

### Utilisateurs

- **GET /users** : Liste des utilisateurs.
- **GET /users/{id}** : Récupérer un utilisateur par son ID.
- **PUT /users/{id}** : Modifier un utilisateur.
- **DELETE /users/{id}** : Supprimer un utilisateur.

### Produits

- **GET /products** : Liste des produits.
- **POST /products** : Créer un produit.
- **GET /products/{id}** : Récupérer un produit par son ID.
- **PUT /products/{id}** : Modifier un produit.
- **DELETE /products/{id}** : Supprimer un produit.
