"""
Script de démonstration : Utilisation des modèles et données initiales.

À exécuter avec : python manage.py shell < demo_script.py
"""

from django.contrib.auth import get_user_model
from core.models import Province, Employeur, Incident, Commentaire, PieceJointe

User = get_user_model()

print("=" * 80)
print("DÉMONSTRATION : Plateforme de Dénonciation des Incidents de Travail")
print("=" * 80)

# ============================================================================
# 1. AFFICHER LES PROVINCES
# ============================================================================
print("\n[1] Provinces disponibles:")
print("-" * 80)
provinces = Province.objects.all()
for province in provinces:
    print(f"  • {province.nom} ({province.code})")

print(f"\nTotal : {provinces.count()} provinces\n")

# ============================================================================
# 2. CRÉER DES UTILISATEURS
# ============================================================================
print("[2] Création d'utilisateurs de test:")
print("-" * 80)

# Récupérer la province Kinshasa
kinshasa = Province.objects.get(nom='Kinshasa')

# Créer un travailleur
travailleur, created = User.objects.get_or_create(
    username='travailleur.demo',
    defaults={
        'email': 'travailleur.demo@mept.cd',
        'first_name': 'Jean',
        'last_name': 'Munkeni',
        'role': 'travailleur',
        'is_active': True
    }
)
if created:
    travailleur.set_password('password123')
    travailleur.save()
print(f"✓ Travailleur créé : {travailleur.username}")

# Créer un agent
agent, created = User.objects.get_or_create(
    username='agent.demo',
    defaults={
        'email': 'agent.demo@mept.cd',
        'first_name': 'Marie',
        'last_name': 'Kalonda',
        'role': 'agent',
        'is_active': True
    }
)
if created:
    agent.set_password('password123')
    agent.save()
    agent.provinces.add(kinshasa)
print(f"✓ Agent créé : {agent.username}")
print(f"  → Province assignée : {', '.join(agent.provinces.values_list('nom', flat=True))}")

# ============================================================================
# 3. CRÉER UN EMPLOYEUR
# ============================================================================
print("\n[3] Création d'employeur de test:")
print("-" * 80)

employeur, created = Employeur.objects.get_or_create(
    nom='CONGO INDUSTRIAL SA',
    defaults={
        'secteur': 'industrie',
        'province': kinshasa,
        'ville': 'Kinshasa',
        'email': 'contact@congoindustrial.cd',
        'telephone': '+243 123 456 789',
        'description': 'Entreprise de transformation minière'
    }
)
if created:
    print(f"✓ Employeur créé : {employeur.nom}")
else:
    print(f"✓ Employeur existant : {employeur.nom}")
print(f"  → Secteur : {employeur.get_secteur_display()}")
print(f"  → Localisation : {employeur.ville}, {employeur.province.nom}")

# ============================================================================
# 4. CRÉER UNE DÉNONCIATION
# ============================================================================
print("\n[4] Création d'une dénonciation/incident:")
print("-" * 80)

incident = Incident.objects.create(
    travailleur=travailleur,
    employeur=employeur,
    province=kinshasa,
    ville='Kinshasa',
    type_incident='salaire',
    description='L\'employeur n\'a pas versé mon salaire depuis 4 mois. J\'ai des documents justificatifs et des témoins.',
    est_anonyme=False,
    statut='nouvelle'
)

print(f"✓ Incident créé avec succès")
print(f"  → Code de suivi : {incident.code_suivi}")
print(f"  → Type : {incident.get_type_incident_display()}")
print(f"  → Statut : {incident.get_statut_display()}")
print(f"  → Travailleur : {incident.travailleur.get_full_name()}")
print(f"  → Employeur : {incident.employeur.nom}")
print(f"  → Date de création : {incident.date_creation.strftime('%d/%m/%Y %H:%M:%S')}")

# ============================================================================
# 5. AJOUTER UN COMMENTAIRE INTERNE
# ============================================================================
print("\n[5] Ajout de commentaires:")
print("-" * 80)

commentaire_interne = Commentaire.objects.create(
    incident=incident,
    auteur=agent,
    texte='Dossier reçu. En attente de vérification des documents. Demander des preuves supplémentaires.',
    type_commentaire='interne'
)
print(f"✓ Commentaire interne ajouté (Agent {agent.username})")

commentaire_public = Commentaire.objects.create(
    incident=incident,
    auteur=agent,
    texte='Merci pour votre signalement. Votre dossier est en cours d\'analyse. Nous vous tiendrons informé de l\'évolution.',
    type_commentaire='public'
)
print(f"✓ Commentaire public ajouté (visible au travailleur)")

# ============================================================================
# 6. ASSIGNER L'INCIDENT À UN AGENT
# ============================================================================
print("\n[6] Assignation de l'incident:")
print("-" * 80)

incident.agent_assigné = agent
incident.statut = 'analyse'
incident.est_lu = True
incident.save()
print(f"✓ Incident assigné à : {incident.agent_assigné.get_full_name()}")
print(f"✓ Statut changé en : {incident.get_statut_display()}")
print(f"✓ Marqué comme lu : {incident.est_lu}")

# ============================================================================
# 7. AFFICHER LE RÉSUMÉ DE L'INCIDENT
# ============================================================================
print("\n[7] Résumé de l'incident:")
print("-" * 80)
print(f"Code de suivi     : {incident.code_suivi}")
print(f"Type              : {incident.get_type_incident_display()}")
print(f"Statut            : {incident.get_statut_display()}")
print(f"Employeur         : {incident.employeur.nom}")
print(f"Travailleur       : {incident.travailleur.get_full_name()}")
print(f"Agent assigné     : {incident.agent_assigné.get_full_name()}")
print(f"Province          : {incident.province.nom}")
print(f"Ville             : {incident.ville}")
print(f"Anonyme           : {'Oui' if incident.est_anonyme else 'Non'}")
print(f"Créé le           : {incident.date_creation.strftime('%d/%m/%Y à %H:%M:%S')}")
print(f"Commentaires      : {incident.commentaires.count()}")
print(f"  - Internes      : {incident.commentaires.filter(type_commentaire='interne').count()}")
print(f"  - Publics       : {incident.commentaires.filter(type_commentaire='public').count()}")

# ============================================================================
# 8. STATISTIQUES
# ============================================================================
print("\n[8] Statistiques:")
print("-" * 80)

total_incidents = Incident.objects.count()
incidents_par_statut = {
    'Nouvelle': Incident.objects.filter(statut='nouvelle').count(),
    'En cours d\'analyse': Incident.objects.filter(statut='analyse').count(),
    'En attente d\'informations': Incident.objects.filter(statut='attente').count(),
    'Résolue': Incident.objects.filter(statut='resolue').count(),
    'Classée sans suite': Incident.objects.filter(statut='classée').count(),
}

print(f"Total incidents     : {total_incidents}")
for statut, count in incidents_par_statut.items():
    print(f"  • {statut:30} : {count}")

total_utilisateurs = User.objects.count()
travailleurs = User.objects.filter(role='travailleur').count()
agents = User.objects.filter(role='agent').count()
admins = User.objects.filter(role='administrateur').count()

print(f"\nUtilisateurs        : {total_utilisateurs}")
print(f"  • Travailleurs    : {travailleurs}")
print(f"  • Agents          : {agents}")
print(f"  • Administrateurs : {admins}")

# ============================================================================
# 9. AFFICHAGE DES COMMENTAIRES
# ============================================================================
print("\n[9] Détail des commentaires pour ce dossier:")
print("-" * 80)
for i, comentaire in enumerate(incident.commentaires.all(), 1):
    type_badge = "🔒 INTERNE" if comentaire.type_commentaire == 'interne' else "🔓 PUBLIC"
    print(f"\nCommentaire {i} ({type_badge})")
    print(f"  Auteur : {comentaire.auteur.get_full_name()}")
    print(f"  Date   : {comentaire.date_creation.strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"  Texte  : {comentaire.texte[:70]}...")

print("\n" + "=" * 80)
print("FIN DE LA DÉMONSTRATION")
print("=" * 80)
print("\n✅ Application configurée et prête pour l'Étape 2 !")
print("\nProchaines étapes:")
print("  1. Créer les vues Django pour le formulaire public")
print("  2. Implémenter la logique de génération du code de suivi")
print("  3. Développer les templates HTML/CSS")
print("  4. Créer les dashboards Agent et Admin")
print("\nPour accéder à l'admin : http://localhost:8000/admin/")
print("  Username : admin")
print("  Password : admin123")
print()
