# API-Project

# API de gestion des utilisateurs et des commandes

Ce projet consiste à créer une API REST complète de A à Z, avec une gestion des utilisateurs et des commandes. L'API permet de gérer différentes actions (GET, POST, PUT, DELETE, PATCH) sur des ressources `users` et `orders`. De plus, l'API inclut un mécanisme de génération de tokens d'authentification et sera hébergée sur notre infrastructure. Le projet sera aussi mis sur GitHub en public.

## Fonctionnalités

L'API dispose des fonctionnalités suivantes pour les endpoints `users` et `orders` :

- **GET** : Récupérer une liste de ressources ou une ressource spécifique.
- **POST** : Créer une nouvelle ressource.
- **PUT** : Mettre à jour une ressource existante.
- **DELETE** : Supprimer une ressource existante.
- **PATCH** : Mettre à jour partiellement une ressource.

### Endpoints

#### Users

- **GET /users** : Récupérer la liste de tous les utilisateurs.
- **GET /users/{id}** : Récupérer un utilisateur spécifique par son ID.
- **POST /users** : Créer un nouvel utilisateur.
- **PUT /users/{id}** : Mettre à jour un utilisateur par son ID.
- **DELETE /users/{id}** : Supprimer un utilisateur par son ID.
- **PATCH /users/{id}** : Mettre à jour partiellement un utilisateur par son ID.

#### Orders

- **GET /orders** : Récupérer la liste de toutes les commandes.
- **GET /orders/{id}** : Récupérer une commande spécifique par son ID.
- **POST /orders** : Créer une nouvelle commande.
- **PUT /orders/{id}** : Mettre à jour une commande par son ID.
- **DELETE /orders/{id}** : Supprimer une commande par son ID.
- **PATCH /orders/{id}** : Mettre à jour partiellement une commande par son ID.

### Authentification

L'API utilise un système de **tokens JWT** pour sécuriser les accès. Un utilisateur peut obtenir un token d'authentification après une connexion réussie, et ce token devra être inclus dans les en-têtes des requêtes pour effectuer des actions sécurisées.

- **POST /login** : Authentifier un utilisateur et retourner un token JWT.
- **POST /register** : Créer un compte utilisateur et obtenir un token.

Le token JWT devra être inclus dans l'en-tête `Authorization` de toutes les requêtes nécessitant une authentification (ex. : `Authorization: Bearer {token}`).
