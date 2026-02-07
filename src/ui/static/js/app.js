/* WohnungsScraper - JavaScript v5.07 */

let currentPage = 'search';
let searchInterval = null;

// Navigation
function navigate(page) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    document.getElementById('page-' + page).classList.add('active');
    document.querySelector('[data-page="' + page + '"]').classList.add('active');
    currentPage = page;
    
    if (page === 'addresses') loadAddresses();
    if (page === 'archive') loadReports();
}

// Adressen
async function loadAddresses() {
    const addresses = await pywebview.api.get_addresses();
    const tbody = document.getElementById('addresses-table');
    const empty = document.getElementById('addresses-empty');
    
    if (addresses.length === 0) {
        tbody.innerHTML = '';
        empty.style.display = 'block';
    } else {
        empty.style.display = 'none';
        tbody.innerHTML = addresses.map(a => `
            <tr>
                <td>${a.street}</td>
                <td style="text-align:center;">${a.house_number}</td>
                <td style="text-align:center;">${a.postal_code || '-'}</td>
                <td>${a.city}</td>
                <td>${a.notes || '-'}</td>
                <td>
                    <div class="address-actions">
                        <button class="btn-edit" onclick="editAddress('${a.id}')">Bearbeiten</button>
                        <button class="btn-delete" onclick="deleteAddress('${a.id}')">X</button>
                    </div>
                </td>
            </tr>
        `).join('');
    }
    loadStats();
}

async function addAddress() {
    const street = document.getElementById('new-street').value.trim();
    const house = document.getElementById('new-house').value.trim();
    const plz = document.getElementById('new-plz').value.trim();
    const city = document.getElementById('new-city').value.trim();
    const notes = document.getElementById('new-notes').value.trim();
    
    if (!street || !house || !city) {
        alert('Bitte Strasse, Hausnummer und Stadt angeben!');
        return;
    }
    
    await pywebview.api.add_address(street, house, plz, city, notes);
    
    document.getElementById('new-street').value = '';
    document.getElementById('new-house').value = '';
    document.getElementById('new-plz').value = '';
    document.getElementById('new-city').value = '';
    document.getElementById('new-notes').value = '';
    
    loadAddresses();
}

async function editAddress(id) {
    const addr = await pywebview.api.get_address(id);
    if (!addr) {
        alert('Adresse nicht gefunden!');
        return;
    }
    
    document.getElementById('edit-address-id').value = addr.id;
    document.getElementById('edit-street').value = addr.street;
    document.getElementById('edit-house').value = addr.house_number;
    document.getElementById('edit-plz').value = addr.postal_code || '';
    document.getElementById('edit-city').value = addr.city;
    document.getElementById('edit-notes').value = addr.notes || '';
    
    document.getElementById('edit-modal').style.display = 'block';
}

async function saveEditAddress() {
    const id = document.getElementById('edit-address-id').value;
    const street = document.getElementById('edit-street').value.trim();
    const house = document.getElementById('edit-house').value.trim();
    const plz = document.getElementById('edit-plz').value.trim();
    const city = document.getElementById('edit-city').value.trim();
    const notes = document.getElementById('edit-notes').value.trim();
    
    if (!street || !house || !city) {
        alert('Bitte Strasse, Hausnummer und Stadt angeben!');
        return;
    }
    
    await pywebview.api.update_address(id, street, house, plz, city, notes);
    closeEditModal();
    loadAddresses();
}

function closeEditModal() {
    document.getElementById('edit-modal').style.display = 'none';
}

async function deleteAddress(id) {
    if (confirm('Adresse wirklich loeschen?')) {
        await pywebview.api.delete_address(id);
        loadAddresses();
    }
}

// Suche
async function startSearch() {
    const mode = document.getElementById('search-mode').value;
    const matchMode = document.getElementById('match-mode').value;
    
    const websites = {
        wgGesucht: document.getElementById('cb-wggesucht').checked,
        immoscout: document.getElementById('cb-immoscout').checked,
        immowelt: document.getElementById('cb-immowelt').checked,
        kleinanzeigen: document.getElementById('cb-kleinanzeigen').checked
    };
    
    const anySelected = Object.values(websites).some(v => v);
    if (!anySelected) {
        alert('Bitte mindestens eine Website auswaehlen!');
        return;
    }
    
    await pywebview.api.start_search(mode, matchMode, websites);
    
    document.getElementById('btn-start').style.display = 'none';
    document.getElementById('btn-stop').style.display = 'inline-flex';
    document.getElementById('progress-container').style.display = 'block';
    
    searchInterval = setInterval(updateSearchStatus, 400);
}

async function stopSearch() {
    await pywebview.api.stop_search();
}

async function updateSearchStatus() {
    const status = await pywebview.api.get_search_status();
    const p = status.progress;
    
    document.getElementById('progress-website').textContent = p.website || 'Initialisiere...';
    document.getElementById('progress-percent').textContent = p.percent + '%';
    document.getElementById('progress-bar').style.width = p.percent + '%';
    document.getElementById('progress-action').textContent = p.action || '';
    document.getElementById('progress-time').textContent = status.elapsed || '00:00';
    document.getElementById('progress-listings').textContent = p.listings || 0;
    document.getElementById('progress-matches').textContent = p.matches || status.matches || 0;
    
    const logContainer = document.getElementById('log-container');
    logContainer.innerHTML = status.logs.map(l => '<div>' + l + '</div>').join('');
    
    if (!status.running) {
        clearInterval(searchInterval);
        document.getElementById('btn-start').style.display = 'inline-flex';
        document.getElementById('btn-stop').style.display = 'none';
        
        // Automatisch Treffer anzeigen wenn welche gefunden wurden
        const matchCount = p.matches || status.matches || 0;
        if (matchCount > 0) {
            // Kurz warten damit der Bericht gespeichert wird
            setTimeout(async () => {
                navigate('archive');
                await loadReports();
                // Neuesten Bericht (Index 0) anzeigen
                if (window.savedReports && window.savedReports.length > 0) {
                    showMatches(0);
                }
            }, 500);
        }
    }
}

// Archiv
async function loadReports() {
    const reports = await pywebview.api.get_reports();
    window.savedReports = reports;
    
    const table = document.getElementById('reports-table');
    const empty = document.getElementById('reports-empty');
    
    if (reports.length === 0) {
        table.innerHTML = '';
        empty.style.display = 'block';
    } else {
        empty.style.display = 'none';
        table.innerHTML = reports.map((r, i) => `
            <tr>
                <td style="font-family:monospace;white-space:nowrap;">${new Date(r.started_at).toLocaleString('de-DE')}</td>
                <td style="text-align:center;">${r.addresses_checked}</td>
                <td><span class="badge ${r.matches_found > 0 ? 'badge-red' : 'badge-green'}">${r.matches_found} Treffer</span></td>
                <td><span class="badge badge-blue">${r.search_mode === 'quick' ? 'Schnell' : 'Voll'}</span></td>
                <td><span class="badge ${r.status === 'completed' ? 'badge-green' : 'badge-yellow'}">${r.status === 'completed' ? 'Fertig' : r.status === 'stopped' ? 'Gestoppt' : 'Laeuft'}</span></td>
                <td style="white-space:nowrap;">
                    ${r.matches_found > 0 ? `<button class="btn btn-primary btn-sm" onclick="showMatches(${i})">Anzeigen</button>` : ''}
                    ${r.matches_found > 0 ? `<button class="btn btn-success btn-sm" style="margin-left:5px;" onclick="exportReport(${i})">Export</button>` : ''}
                    <button class="btn btn-secondary btn-sm" style="color:#ef5350;margin-left:5px;" onclick="deleteReport('${r.id}')">X</button>
                </td>
            </tr>
        `).join('');
    }
}

function showMatches(idx) {
    const report = window.savedReports[idx];
    const matches = report.matches || [];
    
    document.getElementById('matches-modal-title').textContent = matches.length + ' Treffer gefunden';
    
    if (matches.length === 0) {
        document.getElementById('matches-list').innerHTML = '<div class="empty"><p>Keine Treffer-Details verfuegbar.</p></div>';
    } else {
        document.getElementById('matches-list').innerHTML = matches.map(m => `
            <div class="match-item ${m.match_type === 'exact' ? 'exact' : ''}">
                <div class="match-address">${m.address_display || 'Adresse'}</div>
                <div class="match-title">${m.listing_title || 'Kein Titel'}</div>
                <div class="match-footer">
                    <div>
                        <span class="badge badge-blue">${m.website_name || m.website}</span>
                        <span class="badge ${m.match_type === 'exact' ? 'badge-green' : 'badge-yellow'}" style="margin-left:8px;">${m.match_type === 'exact' ? 'Exakt' : 'Erweitert'}</span>
                    </div>
                    <button class="btn btn-success btn-sm" onclick="window.open('${m.listing_url}', '_blank')">Inserat oeffnen</button>
                </div>
            </div>
        `).join('');
    }
    
    document.getElementById('matches-modal').style.display = 'block';
}

function closeMatchesModal() {
    document.getElementById('matches-modal').style.display = 'none';
}

async function exportReport(idx) {
    const report = window.savedReports[idx];
    const result = await pywebview.api.export_report(report.id);
    
    if (result.success) {
        alert('Bericht erfolgreich gespeichert:\n' + result.filename);
    } else if (result.error !== 'Abgebrochen') {
        alert('Fehler beim Speichern: ' + result.error);
    }
}

async function deleteReport(id) {
    if (confirm('Bericht wirklich loeschen?')) {
        await pywebview.api.delete_report(id);
        loadReports();
    }
}

// Title Bar Funktionen
async function minimizeWindow() {
    await pywebview.api.minimize_window();
}

async function closeWindow() {
    await pywebview.api.close_window();
}

function toggleHelpMenu() {
    const menu = document.getElementById('help-menu');
    menu.classList.toggle('show');
}

function openUrl(url) {
    pywebview.api.open_url(url);
    document.getElementById('help-menu').classList.remove('show');
}

// Click outside to close help menu
document.addEventListener('click', function(e) {
    const helpMenu = document.getElementById('help-menu');
    const helpBtn = document.querySelector('.title-bar-btn[onclick="toggleHelpMenu()"]');
    if (helpMenu && !helpMenu.contains(e.target) && e.target !== helpBtn) {
        helpMenu.classList.remove('show');
    }
});

// Init - App bereit
console.log('WohnungsScraper v5.07 geladen');
