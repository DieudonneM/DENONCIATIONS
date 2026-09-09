from datetime import timedelta
from io import StringIO
import os
from tempfile import NamedTemporaryFile

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.core.management import call_command
from openpyxl import Workbook

from users.models import User

from .forms import OrdreDeMissionForm
from .models import Entreprise, Etablissement, OrdreDeMission


class OrdreDeMissionCollisionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='inspecteur',
            email='inspecteur@example.com',
            password='mot-de-passe-test',
            role='agent',
        )
        self.entreprise = Entreprise.objects.create(nom='Entreprise test')
        self.site_a = Etablissement.objects.create(
            entreprise=self.entreprise,
            nom_site='Agence A',
            province='KINSHASA',
            ville_territoire='Kinshasa',
        )
        self.site_b = Etablissement.objects.create(
            entreprise=self.entreprise,
            nom_site='Agence B',
            province='KINSHASA',
            ville_territoire='Kinshasa',
        )
        self.today = timezone.localdate()

    def mission(self, **overrides):
        values = {
            'entite_emetteure': 'IGT',
            'scope': 'LOCAL',
            'entreprise': self.entreprise,
            'etablissement': self.site_a,
            'objet_mission': 'Controle des conditions de travail',
            'date_debut': self.today,
            'date_fin': self.today + timedelta(days=2),
            'created_by': self.user,
        }
        values.update(overrides)
        return OrdreDeMission(**values)

    def test_numero_om_est_genere_a_la_creation(self):
        mission = self.mission()
        mission.save()

        self.assertTrue(mission.numero_om.startswith(f'OM-{self.today.year}-'))

    def test_collision_sur_le_meme_site_aux_dates_chevauchantes(self):
        self.mission().save()
        nouvelle_mission = self.mission(
            date_debut=self.today + timedelta(days=1),
            date_fin=self.today + timedelta(days=3),
        )

        self.assertTrue(nouvelle_mission.check_collision())

    def test_mission_locale_d_un_autre_site_ne_collisionne_pas(self):
        self.mission().save()
        nouvelle_mission = self.mission(etablissement=self.site_b)

        self.assertFalse(nouvelle_mission.check_collision())

    def test_mission_nationale_collisionne_avec_une_mission_locale(self):
        self.mission().save()
        mission_nationale = self.mission(scope='NATIONAL', etablissement=None)

        self.assertTrue(mission_nationale.check_collision())

    def test_mission_finalisee_de_moins_de_90_jours_collisionne(self):
        self.mission(
            statut='FINALISE',
            date_debut=self.today - timedelta(days=10),
            date_fin=self.today - timedelta(days=5),
        ).save()
        nouvelle_mission = self.mission(
            date_debut=self.today + timedelta(days=120),
            date_fin=self.today + timedelta(days=122),
        )

        self.assertTrue(nouvelle_mission.check_collision())

    def test_mission_finalisee_depuis_90_jours_ne_collisionne_pas(self):
        self.mission(
            statut='FINALISE',
            date_debut=self.today - timedelta(days=100),
            date_fin=self.today - timedelta(days=91),
        ).save()
        nouvelle_mission = self.mission(
            date_debut=self.today + timedelta(days=120),
            date_fin=self.today + timedelta(days=122),
        )

        self.assertFalse(nouvelle_mission.check_collision())

    def test_api_retourne_les_details_d_une_collision(self):
        self.mission().save()
        self.client.force_login(self.user)

        response = self.client.get(reverse('inspections:check_collision_api'), {
            'entreprise_id': self.entreprise.pk,
            'etablissement_id': self.site_a.pk,
            'scope': 'LOCAL',
            'date_debut': self.today.isoformat(),
            'date_fin': (self.today + timedelta(days=1)).isoformat(),
        })

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['has_collision'])
        self.assertTrue(response.json()['requires_derogation'])
        self.assertIn('IGT', response.json()['conflict_details'])

    def test_soumission_en_collision_sans_derogation_est_rejetee(self):
        self.mission().save()
        self.client.force_login(self.user)

        response = self.client.post(reverse('inspections:soumettre_mission'), {
            'entite_emetteure': 'CABINET',
            'scope': 'LOCAL',
            'entreprise': self.entreprise.pk,
            'etablissement': self.site_a.pk,
            'objet_mission': 'Nouvelle mission',
            'date_debut': self.today.isoformat(),
            'date_fin': (self.today + timedelta(days=1)).isoformat(),
            'derogation_justification': '',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Une justification de derogation est obligatoire')
        self.assertEqual(OrdreDeMission.objects.count(), 1)

    def test_travailleur_ne_peut_pas_acceder_a_la_soumission_ni_a_l_api(self):
        travailleur = User.objects.create_user(
            username='travailleur',
            email='travailleur@example.com',
            password='mot-de-passe-test',
            role='travailleur',
        )
        self.client.force_login(travailleur)

        page_response = self.client.get(reverse('inspections:soumettre_mission'))
        api_response = self.client.get(reverse('inspections:check_collision_api'))

        self.assertRedirects(
            page_response,
            reverse('core:dashboard'),
            fetch_redirect_response=False,
        )
        self.assertEqual(api_response.status_code, 403)

    def test_agent_peut_exporter_l_ordre_de_mission_en_pdf(self):
        mission = self.mission()
        mission.save()
        self.client.force_login(self.user)

        response = self.client.get(reverse('inspections:ordre_mission_pdf', args=[mission.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn(f'{mission.numero_om}.pdf', response['Content-Disposition'])
        self.assertTrue(response.content.startswith(b'%PDF-'))

    def test_api_recherche_les_entreprises_pour_un_agent(self):
        Entreprise.objects.create(nom='Societe Alpha')
        Entreprise.objects.create(nom='Societe Alpine')
        self.client.force_login(self.user)

        response = self.client.get(reverse('inspections:search_entreprises_api'), {'q': 'alp'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual([result['nom'] for result in response.json()['results']], [
            'Societe Alpha', 'Societe Alpine',
        ])

    def test_agent_peut_rechercher_et_creer_un_etablissement(self):
        self.client.force_login(self.user)

        create_response = self.client.post(reverse('inspections:create_etablissement_api'), {
            'entreprise_id': self.entreprise.pk,
            'nom_site': 'Agence Gombe',
            'province': 'KINSHASA',
            'ville_territoire': 'Kinshasa',
            'adresse': 'Avenue de la Paix',
        })
        search_response = self.client.get(reverse('inspections:search_etablissements_api'), {
            'entreprise_id': self.entreprise.pk,
            'q': 'gomb',
        })

        self.assertEqual(create_response.status_code, 201)
        self.assertEqual(search_response.status_code, 200)
        self.assertEqual(search_response.json()['results'][0]['nom_site'], 'Agence Gombe')

    def test_creation_etablissement_existante_ne_cree_pas_de_doublon(self):
        self.client.force_login(self.user)
        payload = {
            'entreprise_id': self.entreprise.pk,
            'nom_site': 'Agence A',
            'province': 'KINSHASA',
            'ville_territoire': 'Kinshasa',
        }

        response = self.client.post(reverse('inspections:create_etablissement_api'), payload)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['created'])
        self.assertEqual(Etablissement.objects.filter(entreprise=self.entreprise, nom_site='Agence A').count(), 1)

    def test_api_recherche_refuse_un_travailleur(self):
        travailleur = User.objects.create_user(
            username='travailleur-recherche',
            email='travailleur-recherche@example.com',
            password='mot-de-passe-test',
            role='travailleur',
        )
        self.client.force_login(travailleur)

        response = self.client.get(reverse('inspections:search_entreprises_api'), {'q': 'so'})

        self.assertEqual(response.status_code, 403)

    def test_agent_peut_consulter_et_filtrer_les_ordres_de_mission(self):
        mission = self.mission(entite_emetteure='IGT')
        mission.save()
        self.client.force_login(self.user)

        response = self.client.get(reverse('inspections:liste_ordres_mission'), {'statut': 'PROGRAMME'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, mission.numero_om)
        self.assertContains(response, reverse('inspections:ordre_mission_pdf', args=[mission.pk]))

    def test_travailleur_ne_peut_pas_consulter_les_ordres_de_mission(self):
        travailleur = User.objects.create_user(
            username='travailleur-consultation',
            email='travailleur-consultation@example.com',
            password='mot-de-passe-test',
            role='travailleur',
        )
        self.client.force_login(travailleur)

        response = self.client.get(reverse('inspections:liste_ordres_mission'))

        self.assertRedirects(response, reverse('core:dashboard'), fetch_redirect_response=False)


class ImportEntreprisesArspCommandTests(TestCase):
    def test_importe_uniquement_les_champs_entreprise_et_est_idempotente(self):
        workbook = Workbook()
        worksheet = workbook.active
        worksheet.append(['Dénomination', 'RCCM', 'Num Impôt', 'Adresse'])
        worksheet.append([' Societe  Exemple ', 'CD/KNG/RCCM/24-A-001', 'A240001X', 'Non importe'])
        with NamedTemporaryFile(suffix='.xlsx', delete=False) as source:
            source_path = source.name
        try:
            workbook.save(source_path)
            output = StringIO()
            call_command('import_entreprises_arsp', file=source_path, stdout=output)
            call_command('import_entreprises_arsp', file=source_path, stdout=output)
        finally:
            os.unlink(source_path)

        entreprise = Entreprise.objects.get()
        self.assertEqual(entreprise.nom, 'Societe Exemple')
        self.assertEqual(entreprise.rccm, 'CD/KNG/RCCM/24-A-001')
        self.assertEqual(entreprise.nif, 'A240001X')
        self.assertEqual(Entreprise.objects.count(), 1)


class OrdreDeMissionFormTests(TestCase):
    def test_listes_deroulantes_affichent_un_libelle_de_selection(self):
        form = OrdreDeMissionForm()

        self.assertEqual(form.fields['entite_emetteure'].choices[0][1], 'Veuillez sélectionner')
        self.assertEqual(form.fields['scope'].choices[0][1], 'Veuillez sélectionner')
