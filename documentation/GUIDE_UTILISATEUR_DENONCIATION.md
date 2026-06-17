# 👤 Guide Utilisateur - Déposer une Dénonciation

## 📌 Vue d'ensemble

La plateforme de dénonciation permet à **tout travailleur ou demandeur d'emploi en RDC** de signaler des violations des droits du travail de manière **sécurisée et confidentielle**.

---

## 🚀 Comment Déposer une Dénonciation

### Étape 1: Accéder au Formulaire

#### Option A - Depuis la Page d'Accueil
1. Visitez **http://127.0.0.1:8000** (local) ou l'URL de production
2. Faites défiler jusqu'à la section **"DÉPOSER UNE DÉNONCIATION RAPIDE"**
3. Cliquez sur le bouton bleu **"ACCÉDER AU FORMULAIRE COMPLET"**

#### Option B - URL Directe
Allez directement à: `/denoncier/`

---

### Étape 2: Remplir le Formulaire

Le formulaire est divisé en **3 sections principales**:

#### 🏢 **Section 1: Informations de Base**

**Champs obligatoires** (*):

| Champ | Description | Exemple |
|-------|-------------|---------|
| **Employeur** * | Sélectionnez votre employeur/entreprise | SCTP, Google, Banque ABC |
| **Type d'Incident** * | Nature de la violation | Non-paiement de salaire |
| **Province** * | Sélectionnez votre province | Kinshasa, Sud-Kivu |
| **Ville** * | Nom de la localité | Gombe, Bukavu |

💡 **Conseils**: 
- Si votre employeur n'existe pas, contactez l'administration
- Choisissez le type d'incident le plus proche de votre situation

---

#### 📝 **Section 2: Détails de l'Incident**

**Description** * (Requis)
- Décrivez précisément ce qui s'est passé
- Incluez les dates, noms de témoins si possible
- Soyez détaillé pour faciliter l'enquête

**Exemple de description**:
```
En novembre 2025, mon employeur n'a pas payé mon salaire 
d'octobre. J'ai rappelé le responsable RH (Monsieur Jean) 
plusieurs fois, il promet à chaque fois mais ne paie pas.
Trois autres collègues sont dans la même situation.
```

**Pièces Jointes** (Optionnel)
- Téléchargez des documents de support
- Formats acceptés: PDF, DOCX, Images, Vidéos, Audios
- Taille maximale: **50 MB par fichier**

**Comment ajouter des fichiers**:
1. Cliquez sur la zone grise "📎 Cliquez pour sélectionner..."
2. Sélectionnez vos fichiers
3. **OU** glissez-déposez les fichiers dans la zone

**Exemples de pièces jointes utiles**:
- 📄 Contrat de travail
- 📄 Bulletins de paie (manquants)
- 📸 Photos de conditions de travail
- 🎤 Enregistrements audios (conversations)
- 📊 Documents de salaire

---

#### 🔒 **Section 3: Confidentialité et Contact**

**Rester Anonyme** ✓ (Coché par défaut)
- ✅ Votre identité sera **COMPLÈTEMENT PROTÉGÉE**
- ✅ Jamais visible pour l'employeur
- ✅ Jamais révélée à d'autres parties
- ✅ Utilisez uniquement votre code de suivi pour le suivi

**Email & Téléphone** (Optionnel)
- Utile si les agents ont besoin de clarifications
- Ces informations resteront **CONFIDENTIELLES**
- Vous serez contacté uniquement si nécessaire

**Exemple**: 
```
Anonyme: ✓ OUI (coché)
Email: contact@email.com (optionnel)
Tél: +243 123 456 789 (optionnel)
```

**Acceptation** ✓ (Obligatoire)
- Cochez: "J'accepte que mes données personnelles soient traitées..."
- Cela confirme que vous avez lu la politique de confidentialité

---

### Étape 3: Soumettre le Formulaire

1. Vérifiez que tous les champs requis (*) sont remplis
2. Relisez votre description pour les détails
3. Cliquez sur le bouton **"✓ SOUMETTRE MA DÉNONCIATION"**
4. Attendez le traitement (quelques secondes)

---

### Étape 4: Obtenir votre Code de Suivi

Une page de **succès** s'affichera avec:

```
════════════════════════════════════════
  Merci pour votre dénonciation
════════════════════════════════════════

Votre code de suivi: ABC-2024-12345

⚠️ CONSERVEZ CE CODE PRÉCIEUSEMENT
Vous en aurez besoin pour suivre votre dossier
════════════════════════════════════════
```

📌 **Actions possibles**:
- ✅ **Copier le code** et le sauvegarder quelque part
- ✅ **Consulter votre dénonciation** avec le code
- ✅ **Créer un compte** pour suivre plus facilement
- ✅ **Revenir à l'accueil** ou **soumettre une autre**

---

## 📋 Suivi de votre Dénonciation

### Avec Code de Suivi (Anonyme)
1. Allez sur `/consulter/`
2. Entrez votre **code de suivi** (ex: ABC-2024-12345)
3. Consultez le **statut** et les **commentaires**
4. **Aucun login requis**

### Avec Compte (Non-anonyme)
1. Créez un compte utilisateur
2. Connectez-vous
3. Consultez toutes vos dénonciations dans votre **dashboard**
4. Recevez des **notifications** de mise à jour

---

## 📊 Statuts Possibles

| Statut | Signification | Durée Estimée |
|--------|---------------|---------------|
| **Nouvelle** 🆕 | Reçue et enregistrée | Immédiat |
| **En cours d'analyse** 📊 | Agent examine le dossier | 2-7 jours |
| **En attente d'infos** ⏳ | Info supplémentaire demandée | Variable |
| **Résolue** ✅ | Problème résolu avec succès | Variable |
| **Classée sans suite** 📁 | Dossier fermé sans action | Variable |

---

## 🔒 Confidentialité & Sécurité

### Vos Données Sont Protégées Par:

✅ **Chiffrement HTTPS** (Production)
✅ **Anonymat Optionnel** (Identité masquée)
✅ **Données Stockées en Sécurité** (Base de données sécurisée)
✅ **Contrôle d'Accès** (Seuls les agents autorisés y accèdent)
✅ **Conformité RGPD** (Respect des droits personnels)

### Qui Peut Voir Vos Données?
- ❌ L'employeur dénoncé
- ❌ D'autres utilisateurs
- ✅ Les agents du ministère autorisés
- ✅ Vous (avec votre code de suivi)

---

## ❓ Questions Fréquentes

### Q: Est-ce vraiment anonyme?
**R:** Oui, si vous cochez "Rester anonyme". Votre identité n'est jamais visible pour l'employeur.

### Q: Que se passe-t-il après que j'envoie?
**R:** 
1. Votre dénonciation est enregistrée
2. Un agent est assigné dans les 24-48 heures
3. L'agent examine votre cas
4. Vous pouvez suivre la progression avec votre code

### Q: Puis-je ajouter des pièces jointes?
**R:** Oui! Glissez-déposez ou cliquez pour ajouter (max 50 MB par fichier)

### Q: Et si je me trompe en remplissant?
**R:** 
- Cliquez "Réinitialiser" pour vider tous les champs
- Ou n'y a pas d'auto-save, donc vous pouvez revenir en arrière

### Q: Combien de temps avant une réponse?
**R:** 
- Statut "Nouvelle": Immédiat
- Assignation agent: 1-2 jours
- Enquête: 2-30 jours selon la complexité
- Vous pouvez suivre en temps réel

### Q: Je n'ai pas de code, comment suivre?
**R:** 
- Vous recevrez un email de confirmation avec votre code
- Sinon, créez un compte et connectez-vous
- Contactez l'assistance avec votre email

### Q: Puis-je soumettre plusieurs dénonciations?
**R:** Oui, il n'y a pas de limite. Chaque sera traité indépendamment.

### Q: Et si mon employeur figure pas dans la liste?
**R:** Contactez l'administration pour le faire ajouter (par email ou téléphone)

---

## 🎯 Conseils pour Être Plus Efficace

✅ **Soyez Précis**
- Dates exactes
- Noms et prénoms
- Montants exacts (salaires, retenues)

✅ **Apportez des Preuves**
- Contrats de travail
- Bulletins de paie
- Messages, emails
- Photos, vidéos

✅ **Identifiez les Témoins**
- Collègues
- Responsables du département
- Représentants du personnel

✅ **Décrivez l'Impact**
- Difficultés financières
- Problèmes de santé
- Discrimination subie

---

## 📞 Besoin d'Aide?

### Contact du Ministère
- **Email**: support@mept.rdc.gov.cd
- **Téléphone**: +243 XX XXX XXXX
- **Adresse**: Kinshasa, RDC

### Pages Utiles
- 📖 **À Propos**: Comprendre nos droits
- 📞 **Contact**: Nous joindre directement
- 📊 **Dashboard**: Voir toutes vos dénonciations

---

## ⚠️ Points Importants à Retenir

🔴 **IMPORTANT**:
1. **Sauvegardez votre code de suivi** dans un endroit sûr
2. **N'oubliez jamais votre code** pour consulter votre dossier
3. **Soyez honnête** dans votre description
4. **Fournissez des preuves** si possible
5. **Restez courtois** dans votre communication

---

## ✨ Vous Êtes Maintenant Prêt!

Vous pouvez commencer à déposer une dénonciation:

👉 **[Accéder au Formulaire](http://127.0.0.1:8000/denoncier/)**

Merci d'utiliser cette plateforme pour défendre vos droits! 🙏

