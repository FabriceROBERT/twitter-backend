# Twitter Clone avec Reconnaissance Faciale

Dans le cadre d'un projet scolaire de ma dernière semaine de formation en M1 à IPSSI, l'objectif est de créer une application de réseau social inspirée de Twitter en 3j, enrichie d'une fonctionnalité de reconnaissance des expressions faciales. Ce projet combine une API backend simplet avec une interface frontend moderne et efficace faite entièrement par moi (ROBERT Fabrice).

## Table des matières

- [Aperçu](#aperçu)
- [Stack Technologique](#stack-technologique)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Utilisation](#utilisation)
- [API Endpoints](#api-endpoints)
- [Structure du Projet](#structure-du-projet)

## Aperçu

Cette application permet aux utilisateurs de :

- **Créer un compte** et se connecter de manière sécurisée
- **Publier des tweets** avec support des hashtags
- **Interagir** avec les tweets (likes, retweets, commentaires)
- **Suivre/Dés-suivre** d'autres utilisateurs
- **Capture d'expressions faciales** automatique lors de la création de tweets
- **Analyse émotionnelle** des tweets basée sur la reconnaissance faciale
- **Signets** pour sauvegarder les tweets favoris

## Stack Technologique

### Backend

- **Python 3.11+**
- **FastAPI** - Framework web moderne et performant
- **SQLAlchemy** - ORM pour l'accès à la base de données
- **PostgreSQL** - Base de données relationnelle
- **Alembic** - Migrations de schéma de base de données
- **Python-jose** - Authentification JWT
- **OpenCV/Mediapipe** - Reconnaissance faciale et analyse d'expressions

### Frontend

- **React 18** - Bibliothèque UI
- **TailwindCSS** - Utility-first CSS framework

### Outils

- **Git** - Contrôle de version

## Architecture

```
twitter-clone/
├── twitter-backend/        # Projet du backend
│   ├── app/
│   │   ├── api/           # Routes API
│   │   ├── models/        # Modèles SQLAlchemy
│   │   ├── schemas/       # Schémas Pydantic
│   │   ├── services/      # Logique métier
│   │   ├── db/            # Configuration BD
│   │   ├── core/          # Configuration globale
│   │   └── utils/         # Utilitaires (sécurité, etc.)
│   ├── alembic/           # Migrations
│   └── main.py            # Point d'entrée
│
└── twitter-front/         # Application React
    ├── src/
    │   ├── components/    # Composants réutilisables
    │   ├── pages/        # Pages principales
    │   ├── contexts/     # Context API
    │   ├── services/     # Services API
    │   ├── utils/        # Fonctions utilitaires
    │   ├── modals/       # Modales
    │   └── App.js        # Composant racine
    │   └── Middleware.js        # Sécuriser les pages
    └── public/           # Actifs statiques
```

## Installation

### Prérequis

- Python 3.11+
- Node.js 16+
- PostgreSQL 12+
- Git

### Backend

1. **Cloner le repository**

```bash
git clone https://github.com/FabriceROBERT/twitter-backend.git
cd twitter-backend
```

2. **Créer un environnement virtuel**

```bash
python -m venv venv
venv\Scripts\activate  #Linux: source venv/bin/activate
```

3. **Installer les dépendances**

```bash
pip install -r requirements.txt
```

4. **Configurer la base de données**

```bash
alembic upgrade head
```

5. **Démarrer le serveur**

```bash
uvicorn app.main:app --reload
```

L'API sera disponible à `http://localhost:8000`
Documentation Swagger : `http://localhost:8000/docs`

### Frontend

1. **Cloner le repository et naviguer vers le dossier frontend**

```bash
git clone git@github.com:FabriceROBERT/twitter-front.git
cd twitter-front
```

2. **Installer les dépendances**

```bash
npm install
```

3. **Démarrer l'application**

```bash
npm start
```

L'application sera accessible à `http://localhost:3000`

## Configuration

### Backend (.env)

Créez un fichier `.env` dans le dossier `twitter-backend` :

```env
# Base de données
DATABASE_URL=create_your_db

# Authentification
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# API
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

```

### Frontend (.env)

Créez un fichier `.env` dans `twitter-front` :

```env
REACT_APP_API_URL=http://localhost:8000/api
REACT_APP_DEBUG=true
```

## Utilisation

### Pour l'utilisateur

1. Accédez à `http://localhost:3000`
2. Créez un compte ou connectez-vous
3. Composez un tweet ou alors activez la caméra et le reconnaissance se déclenchera automatiquement
4. Votre expression faciale sera analysée et associée à votre tweet
5. Explorez, likez, et suivez d'autres utilisateurs

## 📡 API Endpoints

### Authentification

- `POST /api/auth/register` - Créer un compte
- `POST /api/auth/login` - Se connecter
- `POST /api/auth/refresh` - Rafraîchir le token

### Utilisateurs

- `GET /api/users/{id}` - Obtenir le profil d'un utilisateur
- `PUT /api/users/{id}` - Mettre à jour le profil
- `GET /api/users/{id}/followers` - Lister les followers
- `POST /api/users/{id}/follow` - Suivre un utilisateur

### Tweets

- `GET /api/tweets` - Lister les tweets
- `POST /api/tweets` - Créer un tweet
- `GET /api/tweets/{id}` - Obtenir un tweet
- `DELETE /api/tweets/{id}` - Supprimer un tweet
- `POST /api/tweets/{id}/like` - Liker un tweet

### Interactions

- `POST /api/tweets/{id}/retweet` - Retweeter
- `POST /api/tweets/{id}/reply` - Répondre
- `GET /api/tweets/{id}/replies` - Lister les réponses

### Expressions Faciales

- `POST /api/facial-expressions/analyze` - Analyser une image
- `GET /api/facial-expressions/{tweet_id}` - Obtenir l'expression d'un tweet

## Structure du Projet Détaillée

### Backend

**`app/models/models.py`** - Modèles SQLAlchemy

- User - Modèle utilisateur
- Tweet - Modèle de tweet
- Interaction - Modèle d'interaction
- FacialExpression - Données faciales

**`app/api/`** - Routes API

- `auth.py` - Endpoints d'authentification
- `users.py` - Endpoints utilisateurs
- `tweets.py` - Endpoints tweets
- `interactions.py` - Endpoints d'interaction
- `facial_expressions.py` - Endpoints reconnaissance faciale

**`app/services/`** - Logique métier

- `facial_recognition_service.py` - Traitement des images
- `users_service.py` - Gestion utilisateurs

### Frontend

**`src/components/`** - Composants réutilisables

- Layout - Structure principale
- Sidebar - Navigation latérale
- MainContent - Contenu principal
- RightSidebar - Sidebar droit

**`src/pages/`** - Pages principales

- HomePage - Flux des tweets
- DashboardPage - Tableau de bord
- LoginPage - Connexion
- RegisterPage - Inscription
- FollowersPage - Gestion des followers

**`src/contexts/`** - Gestion d'état

- AuthContext - Contexte d'authentification
- BookmarkContext - Gestion des signets

**`src/modals/`** - Modales

- EmotionCapture - Capture d'expression faciale

## 🔒 Sécurité

- Les mots de passe sont hachés avec bcrypt
- L'authentification utilise JWT
- Les tokens expirent après 30 minutes
- CORS est configuré pour les domaines autorisés
- Les entrées utilisateur sont validées avec Pydantic
