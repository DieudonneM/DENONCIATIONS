from django import forms

from .models import OrdreDeMission


class OrdreDeMissionForm(forms.ModelForm):
    class Meta:
        model = OrdreDeMission
        fields = [
            'entite_emetteure',
            'scope',
            'entreprise',
            'etablissement',
            'objet_mission',
            'date_debut',
            'date_fin',
            'derogation_justification',
        ]
        widgets = {
            'entite_emetteure': forms.Select(attrs={'class': 'form-control'}),
            'scope': forms.Select(attrs={'class': 'form-control'}),
            'entreprise': forms.HiddenInput(),
            'etablissement': forms.HiddenInput(),
            'objet_mission': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'date_debut': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_fin': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'derogation_justification': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['entreprise'].queryset = self.fields['entreprise'].queryset.order_by('nom')
        for field_name in ('entite_emetteure', 'scope'):
            field = self.fields[field_name]
            field.choices = [
                (value, 'Veuillez sélectionner' if value == '' else label)
                for value, label in field.choices
            ]

    def clean(self):
        cleaned_data = super().clean()
        scope = cleaned_data.get('scope')
        etablissement = cleaned_data.get('etablissement')

        if scope == 'LOCAL' and not etablissement:
            self.add_error('etablissement', 'Un etablissement est obligatoire pour une mission locale.')
        return cleaned_data