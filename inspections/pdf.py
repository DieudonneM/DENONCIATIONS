from io import BytesIO

from django.conf import settings
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def build_ordre_de_mission_pdf(mission):
    """Construit le PDF administratif exportable d'un ordre de mission."""
    output = BytesIO()
    document = SimpleDocTemplate(
        output,
        pagesize=A4,
        rightMargin=2.1 * cm,
        leftMargin=2.1 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        title=f'Ordre de mission {mission.numero_om}',
        author="Ministere de l'Emploi et Travail",
    )
    styles = getSampleStyleSheet()
    centered = ParagraphStyle('Centered', parent=styles['Normal'], alignment=TA_CENTER, leading=14)
    heading = ParagraphStyle(
        'MissionHeading', parent=centered, fontName='Helvetica-Bold', fontSize=13, leading=18,
        spaceBefore=22, spaceAfter=20,
    )
    body = ParagraphStyle('MissionBody', parent=styles['Normal'], fontName='Times-Roman', fontSize=11, leading=15)
    signature = ParagraphStyle('Signature', parent=centered, fontName='Times-Bold', fontSize=11, leading=16)
    story = []

    logo_path = settings.BASE_DIR / 'staticfiles' / 'img' / 'favicon.png'
    if logo_path.exists():
        story.append(Image(str(logo_path), width=3.15 * cm, height=3.15 * cm, hAlign='CENTER'))
    story.extend([
        Paragraph("MINISTERE D'EMPLOI ET TRAVAIL", ParagraphStyle(
            'Ministry', parent=centered, fontName='Helvetica-Bold', fontSize=9, leading=12,
        )),
        Paragraph('Le Ministre', ParagraphStyle(
            'Minister', parent=centered, fontName='Times-Italic', fontSize=16, leading=20,
        )),
        Paragraph(f'<u>ORDRE DE MISSION N° {mission.numero_om}</u>', heading),
        Paragraph(
            "Les personnes mandatees sont designees pour effectuer une mission officielle "
            f"pour le compte de {mission.get_entite_emetteure_display()}.",
            body,
        ),
        Spacer(1, .45 * cm),
        Paragraph('<b>OBJET DE LA MISSION :</b> ' + mission.objet_mission, body),
        Spacer(1, .65 * cm),
    ])

    location = mission.entreprise.nom
    if mission.etablissement:
        location = f'{mission.etablissement.nom_site}, {mission.etablissement.ville_territoire}'
    duration = (mission.date_fin - mission.date_debut).days + 1
    details = [
        ['Entite emettrice', mission.get_entite_emetteure_display()],
        ['Entreprise concernee', mission.entreprise.nom],
        ['Lieu', location],
        ['Portee', mission.get_scope_display()],
        ['Duree', f'{duration} jour(s)'],
        ['Du', mission.date_debut.strftime('%d/%m/%Y')],
        ['Au', mission.date_fin.strftime('%d/%m/%Y')],
    ]
    table = Table(details, colWidths=[4.4 * cm, 11.2 * cm])
    table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Times-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Times-Roman'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('LEADING', (0, 0), (-1, -1), 15),
        ('LINEBELOW', (0, 0), (-1, -1), .3, colors.HexColor('#d0d5dd')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.extend([
        table,
        Spacer(1, .9 * cm),
        Paragraph(
            "Les autorites civiles, judiciaires, militaires et policieres sont priees "
            "d'apporter leur assistance aux porteurs du present ordre de mission en cas de necessite.",
            body,
        ),
        Spacer(1, 1.4 * cm),
        Paragraph('Fait a Kinshasa, le ' + mission.created_at.strftime('%d/%m/%Y'), centered),
        Spacer(1, .8 * cm),
        Paragraph('Pour le Ministre de l\'Emploi et Travail', signature),
        Spacer(1, .35 * cm),
        Paragraph(mission.created_by.get_full_name() or mission.created_by.email, signature),
    ])
    document.build(story)
    return output.getvalue()