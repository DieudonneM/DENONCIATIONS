# Données et sécurité - Google Play Data Safety

## 1) Données collectées par l'application

L'application collecte et traite les éléments suivants pour permettre la création de compte, l'accès sécurisé à l'espace utilisateur et le traitement des signalements :

- Adresse e-mail
- Prénom et nom
- Numéro de téléphone
- Mot de passe (stocké via mécanisme sécurisé côté application et serveur)
- Données de signalement / dénonciation
- Fichiers joints associés aux signalements
- Token de notification mobile (FCM / Firebase Cloud Messaging)

## 2) Usage des données

Les données sont utilisées pour :

- créer et gérer le compte utilisateur ;
- authentifier l'utilisateur ;
- traiter les signalements et suivre les dossiers ;
- envoyer des notifications pertinentes à l'utilisateur ;
- sécuriser les accès et la gestion des incidents.

## 3) Partage avec des tiers

Les données ne sont pas vendues.

Les données peuvent être traitées via les services techniques suivants :

- Firebase Cloud Messaging pour les notifications push ;
- le backend Django hébergé sur le domaine officiel de l'application ;
- stockage de fichiers et ressources selon l'infrastructure de production.

## 4) Protection et chiffrement

- Le trafic est exigé en HTTPS / TLS.
- Les tokens de session et les informations sensibles côté application sont stockés via Flutter Secure Storage.
- Les échanges entre l'application et l'API utilisent des requêtes sécurisées sur le domaine de production.
- Les mots de passe ne sont pas stockés en clair côté stockage local.

## 5) Réponse recommandée pour le questionnaire Google Play

### Section : Données de compte
- Oui : adresse e-mail
- Oui : nom et prénom
- Oui : numéro de téléphone
- Oui : mot de passe

### Section : Données de l'app
- Oui : contenu utilisateur / signalements
- Oui : fichiers joints / pièces jointes

### Section : Données de diagnostic
- Non, sauf si explicitement collectées au cours de la production ou du support technique

### Section : Données partagées avec des tiers
- Oui, uniquement pour les notifications push et l'infrastructure technique nécessaire au service

### Section : Transfert de données
- Oui, via HTTPS/TLS

### Section : Conservation
- Les données sont conservées tant que le compte est actif et selon les besoins de traitement du service, puis peuvent être supprimées ou désactivées à la demande de l'utilisateur.

## 6) Déclaration de conformité

L'application traite des données personnelles strictement nécessaires au service, les protège en transit et en stockage local, et propose une procédure de suppression de compte afin de respecter les exigences de conformité de publication sur les stores.

## 7) Vérification à faire côté console Play

Dans la Console Play, remplir le questionnaire Data Safety avec les éléments suivants :

- Collecte de données personnelles : Oui
- Type principal : Contact / Compte / Signalements
- Transmission chiffrée : Oui, HTTPS/TLS
- Stockage local protégé : Oui
- Confidentialité : données utilisées uniquement pour le service
- Partage : uniquement services techniques nécessaires (FCM, backend, hébergement)
- Suppression de compte : disponible depuis l'application et via API
