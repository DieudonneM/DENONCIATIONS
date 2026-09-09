document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('mission-form');
    if (!form) return;

    const fields = {
        entreprise: document.getElementById('id_entreprise'),
        etablissement: document.getElementById('id_etablissement'),
        scope: document.getElementById('id_scope'),
        dateDebut: document.getElementById('id_date_debut'),
        dateFin: document.getElementById('id_date_fin'),
        derogation: document.getElementById('id_derogation_justification'),
    };
    const alertBanner = document.getElementById('collision-alert-banner');
    const alertDetails = document.getElementById('collision-alert-details');
    const derogationGroup = fields.derogation.closest('.derogation-field');
    const submitButton = document.getElementById('mission-submit-button');
    const companySearch = document.getElementById('entreprise-search');
    const companySuggestions = document.getElementById('entreprise-suggestions');
    const establishmentSearch = document.getElementById('etablissement-search');
    const establishmentSuggestions = document.getElementById('etablissement-suggestions');
    const addEstablishmentButton = document.getElementById('add-establishment-button');
    const newEstablishmentFields = document.getElementById('new-establishment-fields');
    const newEstablishmentProvince = document.getElementById('new-establishment-province');
    const newEstablishmentCity = document.getElementById('new-establishment-city');
    const newEstablishmentAddress = document.getElementById('new-establishment-address');
    const saveEstablishmentButton = document.getElementById('save-establishment-button');
    const establishmentError = document.getElementById('establishment-error');
    let requestId = 0;
    let searchTimeout;
    let searchRequestId = 0;
    let establishmentSearchTimeout;
    let establishmentSearchRequestId = 0;

    function setCollisionState(hasCollision, details = '') {
        alertBanner.hidden = !hasCollision;
        alertDetails.textContent = details;
        derogationGroup.hidden = !hasCollision;
        fields.derogation.required = hasCollision;
        submitButton.textContent = hasCollision
            ? 'Soumettre avec derogation'
            : 'Valider et emettre la mission';
        submitButton.classList.toggle('requires-derogation', hasCollision);
    }

    async function checkCollision() {
        const { entreprise, etablissement, scope, dateDebut, dateFin } = fields;
        const isLocalWithoutSite = scope.value === 'LOCAL' && !etablissement.value;
        if (!entreprise.value || !scope.value || !dateDebut.value || !dateFin.value || isLocalWithoutSite) {
            setCollisionState(false);
            return;
        }

        const currentRequestId = ++requestId;
        const params = new URLSearchParams({
            entreprise_id: entreprise.value,
            etablissement_id: etablissement.value,
            scope: scope.value,
            date_debut: dateDebut.value,
            date_fin: dateFin.value,
        });

        try {
            const response = await fetch(`${form.dataset.collisionUrl}?${params.toString()}`, {
                headers: { Accept: 'application/json' },
                credentials: 'same-origin',
            });
            if (!response.ok) throw new Error('Verification indisponible');
            const result = await response.json();
            if (currentRequestId !== requestId) return;
            setCollisionState(result.has_collision, result.conflict_details);
        } catch (error) {
            if (currentRequestId === requestId) setCollisionState(false);
        }
    }

    [fields.entreprise, fields.etablissement, fields.scope, fields.dateDebut, fields.dateFin]
        .forEach((field) => {
            field.addEventListener('change', checkCollision);
            field.addEventListener('input', checkCollision);
        });

    function hideCompanySuggestions() {
        companySuggestions.hidden = true;
        companySearch.setAttribute('aria-expanded', 'false');
    }

    function selectCompany(company) {
        fields.entreprise.value = company.id;
        companySearch.value = company.nom;
        fields.etablissement.value = '';
        establishmentSearch.value = '';
        establishmentSearch.disabled = false;
        newEstablishmentFields.hidden = true;
        addEstablishmentButton.hidden = true;
        hideCompanySuggestions();
        fields.entreprise.dispatchEvent(new Event('change'));
    }

    function renderCompanySuggestions(companies) {
        companySuggestions.replaceChildren();
        companies.forEach((company) => {
            const option = document.createElement('button');
            option.type = 'button';
            option.className = 'company-suggestion';
            option.setAttribute('role', 'option');
            option.textContent = company.nom;
            const details = [company.rccm && `RCCM: ${company.rccm}`, company.nif && `NIF: ${company.nif}`]
                .filter(Boolean)
                .join(' | ');
            if (details) {
                const metadata = document.createElement('small');
                metadata.textContent = details;
                option.appendChild(metadata);
            }
            option.addEventListener('click', () => selectCompany(company));
            companySuggestions.appendChild(option);
        });
        companySuggestions.hidden = companies.length === 0;
        companySearch.setAttribute('aria-expanded', String(companies.length > 0));
    }

    async function searchCompanies() {
        const query = companySearch.value.trim();
        fields.entreprise.value = '';
        if (query.length < 2) {
            hideCompanySuggestions();
            return;
        }

        const currentSearchRequestId = ++searchRequestId;
        try {
            const response = await fetch(
                `${form.dataset.companySearchUrl}?${new URLSearchParams({ q: query })}`,
                { headers: { Accept: 'application/json' }, credentials: 'same-origin' },
            );
            if (!response.ok) throw new Error('Recherche indisponible');
            const result = await response.json();
            if (currentSearchRequestId === searchRequestId) renderCompanySuggestions(result.results);
        } catch (error) {
            if (currentSearchRequestId === searchRequestId) hideCompanySuggestions();
        }
    }

    companySearch.addEventListener('input', () => {
        window.clearTimeout(searchTimeout);
        searchTimeout = window.setTimeout(searchCompanies, 220);
    });
    companySearch.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') hideCompanySuggestions();
    });
    document.addEventListener('click', (event) => {
        if (!event.target.closest('.company-search-group')) hideCompanySuggestions();
    });

    function hideEstablishmentSuggestions() {
        establishmentSuggestions.hidden = true;
        establishmentSearch.setAttribute('aria-expanded', 'false');
    }

    function selectEstablishment(establishment) {
        fields.etablissement.value = establishment.id;
        establishmentSearch.value = establishment.nom_site;
        hideEstablishmentSuggestions();
        newEstablishmentFields.hidden = true;
        addEstablishmentButton.hidden = true;
        fields.etablissement.dispatchEvent(new Event('change'));
    }

    function renderEstablishmentSuggestions(establishments) {
        establishmentSuggestions.replaceChildren();
        establishments.forEach((establishment) => {
            const option = document.createElement('button');
            option.type = 'button';
            option.className = 'company-suggestion';
            option.setAttribute('role', 'option');
            option.textContent = establishment.nom_site;
            const metadata = document.createElement('small');
            metadata.textContent = `${establishment.ville_territoire}, ${establishment.province}`;
            option.appendChild(metadata);
            option.addEventListener('click', () => selectEstablishment(establishment));
            establishmentSuggestions.appendChild(option);
        });
        establishmentSuggestions.hidden = establishments.length === 0;
        establishmentSearch.setAttribute('aria-expanded', String(establishments.length > 0));
        addEstablishmentButton.hidden = establishments.length > 0 || establishmentSearch.value.trim().length < 2;
    }

    async function searchEstablishments() {
        const query = establishmentSearch.value.trim();
        fields.etablissement.value = '';
        newEstablishmentFields.hidden = true;
        if (!fields.entreprise.value || query.length < 2) {
            hideEstablishmentSuggestions();
            addEstablishmentButton.hidden = true;
            return;
        }

        const currentSearchRequestId = ++establishmentSearchRequestId;
        try {
            const params = new URLSearchParams({ entreprise_id: fields.entreprise.value, q: query });
            const response = await fetch(`${form.dataset.establishmentSearchUrl}?${params}`, {
                headers: { Accept: 'application/json' }, credentials: 'same-origin',
            });
            if (!response.ok) throw new Error('Recherche indisponible');
            const result = await response.json();
            if (currentSearchRequestId === establishmentSearchRequestId) {
                renderEstablishmentSuggestions(result.results);
            }
        } catch (error) {
            if (currentSearchRequestId === establishmentSearchRequestId) hideEstablishmentSuggestions();
        }
    }

    function csrfToken() {
        return form.querySelector('[name=csrfmiddlewaretoken]').value;
    }

    addEstablishmentButton.addEventListener('click', () => {
        newEstablishmentFields.hidden = false;
        newEstablishmentProvince.focus();
    });
    saveEstablishmentButton.addEventListener('click', async () => {
        const formData = new URLSearchParams({
            entreprise_id: fields.entreprise.value,
            nom_site: establishmentSearch.value.trim(),
            province: newEstablishmentProvince.value,
            ville_territoire: newEstablishmentCity.value.trim(),
            adresse: newEstablishmentAddress.value.trim(),
        });
        establishmentError.hidden = true;
        try {
            const response = await fetch(form.dataset.establishmentCreateUrl, {
                method: 'POST',
                headers: {
                    Accept: 'application/json',
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': csrfToken(),
                },
                body: formData,
                credentials: 'same-origin',
            });
            const result = await response.json();
            if (!response.ok) throw new Error(result.detail || 'Enregistrement indisponible');
            selectEstablishment(result);
        } catch (error) {
            establishmentError.textContent = error.message;
            establishmentError.hidden = false;
        }
    });
    establishmentSearch.addEventListener('input', () => {
        window.clearTimeout(establishmentSearchTimeout);
        establishmentSearchTimeout = window.setTimeout(searchEstablishments, 220);
    });
    establishmentSearch.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') hideEstablishmentSuggestions();
    });
    document.addEventListener('click', (event) => {
        if (!event.target.closest('.establishment-search-group')) hideEstablishmentSuggestions();
    });
});