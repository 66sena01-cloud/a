document.addEventListener('DOMContentLoaded', () => {
    if (!localStorage.getItem('adminToken')) { window.location.href = '/login.html'; return; }

    document.querySelectorAll('.sidebar-menu a[data-section]').forEach(item => {
        item.addEventListener('click', (e) => { e.preventDefault(); showSection(item.dataset.section); });
    });
    document.getElementById('logoutBtn')?.addEventListener('click', () => { adminApi.logout(); window.location.href = '/login.html'; });
    document.getElementById('refreshData')?.addEventListener('click', () => { loadDashboard(); loadPackages(); loadEvents(); loadBlogPosts(); loadApplications(); loadAppointments(); loadMedia(); loadPurchases(); loadSettings(); loadSocialLinks(); });
    document.getElementById('sidebarToggle')?.addEventListener('click', () => document.getElementById('sidebar').classList.toggle('open'));

    showSection('dashboard');
    loadDashboard();
    loadPackages();
    loadEvents();
    loadBlogPosts();
    loadApplications();
    loadAppointments();
    loadMedia();
    loadPurchases();
    loadSettings();
    loadSocialLinks();
});

function showSection(sectionId) {
    document.querySelectorAll('.section-panel').forEach(p => p.classList.remove('active'));
    const target = document.getElementById(`section-${sectionId}`);
    if (target) target.classList.add('active');
    document.querySelectorAll('.sidebar-menu a').forEach(a => a.classList.remove('active'));
    const activeLink = document.querySelector(`[data-section="${sectionId}"]`);
    if (activeLink) activeLink.classList.add('active');
}

async function loadDashboard() {
    try {
        const data = await adminApi.getDashboard();
        document.getElementById('statPackages').textContent = data.total_packages;
        document.getElementById('statActivePackages').textContent = data.active_packages;
        document.getElementById('statEvents').textContent = data.total_events;
        document.getElementById('statApplications').textContent = data.total_applications;
        document.getElementById('statPendingAppointments').textContent = data.pending_appointments;
        document.getElementById('statPurchases').textContent = data.total_purchases;
        document.getElementById('statPendingPurchases').textContent = data.pending_purchases;
    } catch (e) { showToast(e.message, 'error'); }
}

// ---------- PAKETLER ----------
async function loadPackages() {
    const container = document.getElementById('packagesTableBody');
    if (!container) return;
    try {
        const packages = await adminApi.getPackages();
        if (!packages.length) { container.innerHTML = '<tr><td colspan="7">Henüz paket yok.</td></tr>'; return; }
        container.innerHTML = packages.map(pkg => `
            <tr>
                <td><img src="${pkg.cover_image ? '/media/' + pkg.cover_image.replace(/^\/?/, '') : '/placeholder.jpg'}" style="width:50px;height:50px;object-fit:cover;border-radius:8px;"></td>
                <td>${pkg.name}</td>
                <td>${pkg.category}</td>
                <td>${pkg.duration || '-'}</td>
                <td>₺${pkg.price}</td>
                <td>${pkg.is_active ? '<span class="badge-success">Aktif</span>' : '<span class="badge-danger">Pasif</span>'}</td>
                <td><button class="btn btn-secondary" onclick="deletePackage(${pkg.id})">Sil</button></td>
            </tr>
        `).join('');
    } catch (e) { showToast(e.message, 'error'); }
}

function openPackageModal() {
    document.getElementById('packageForm').reset();
    document.getElementById('packagePreview').style.display = 'none';
    document.getElementById('packageCoverInput').value = '';
    openModal('packageModal');
}

function previewImage(input, previewId, hiddenId) {
    const file = input.files[0];
    const preview = document.getElementById(previewId);
    const hidden = document.getElementById(hiddenId);
    if (file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            preview.src = e.target.result;
            preview.style.display = 'block';
            hidden.value = e.target.result;
        };
        reader.readAsDataURL(file);
    }
}

async function createPackage(event) {
    event.preventDefault();
    const form = document.getElementById('packageForm');
    const data = {
        name: form.name.value,
        category: form.category.value,
        price: parseFloat(form.price.value),
        duration: form.duration.value,
        description: form.description.value,
        features: form.features.value ? form.features.value.split('\n') : [],
        cover_image: form.cover_image.value || null,
        is_active: form.is_active.checked,
        is_featured: form.is_featured.checked,
        sort_order: parseInt(form.sort_order.value || 0)
    };
    try {
        await adminApi.createPackage(data);
        showToast('Paket oluşturuldu.', 'success');
        closeModal('packageModal');
        loadPackages();
    } catch (e) { showToast(e.message, 'error'); }
}

async function deletePackage(id) {
    if (!confirm('Emin misiniz?')) return;
    try { await adminApi.deletePackage(id); showToast('Paket silindi.', 'success'); loadPackages(); }
    catch (e) { showToast(e.message, 'error'); }
}

// ---------- ETKİNLİKLER ----------
async function loadEvents() {
    const container = document.getElementById('eventsTableBody');
    if (!container) return;
    try {
        const events = await adminApi.getEvents();
        if (!events.length) { container.innerHTML = '<tr><td colspan="7">Henüz etkinlik yok.</td></tr>'; return; }
        container.innerHTML = events.map(ev => `
            <tr>
                <td><img src="${ev.cover_image ? '/media/' + ev.cover_image.replace(/^\/?/, '') : '/placeholder.jpg'}" style="width:50px;height:50px;object-fit:cover;border-radius:8px;"></td>
                <td>${ev.title}</td>
                <td>${ev.event_date}</td>
                <td>${ev.event_time || '-'}</td>
                <td>${ev.location || '-'}</td>
                <td>${ev.is_active ? '<span class="badge-success">Aktif</span>' : '<span class="badge-danger">Pasif</span>'}</td>
                <td><button class="btn btn-secondary" onclick="deleteEvent(${ev.id})">Sil</button></td>
            </tr>
        `).join('');
    } catch (e) { showToast(e.message, 'error'); }
}

function openEventModal() {
    document.getElementById('eventForm').reset();
    document.getElementById('eventPreview').style.display = 'none';
    document.getElementById('eventCoverInput').value = '';
    openModal('eventModal');
}

async function createEvent(event) {
    event.preventDefault();
    const form = document.getElementById('eventForm');
    const data = {
        title: form.title.value,
        description: form.description.value,
        event_date: form.event_date.value,
        event_time: form.event_time.value,
        location: form.location.value,
        is_online: form.is_online.value === 'true',
        capacity: form.capacity.value ? parseInt(form.capacity.value) : null,
        registration_link: form.registration_link.value,
        cover_image: form.cover_image.value || null,
        is_active: form.is_active.checked
    };
    try {
        await adminApi.createEvent(data);
        showToast('Etkinlik oluşturuldu.', 'success');
        closeModal('eventModal');
        loadEvents();
    } catch (e) { showToast(e.message, 'error'); }
}

async function deleteEvent(id) {
    if (!confirm('Emin misiniz?')) return;
    try { await adminApi.deleteEvent(id); showToast('Etkinlik silindi.', 'success'); loadEvents(); }
    catch (e) { showToast(e.message, 'error'); }
}

// ---------- BLOG ----------
async function loadBlogPosts() {
    const container = document.getElementById('blogTableBody');
    if (!container) return;
    try {
        const posts = await adminApi.getBlogPosts();
        if (!posts.length) { container.innerHTML = '<tr><td colspan="6">Henüz blog yazısı yok.</td></tr>'; return; }
        container.innerHTML = posts.map(post => `
            <tr>
                <td><img src="${post.cover_image ? '/media/' + post.cover_image.replace(/^\/?/, '') : '/placeholder.jpg'}" style="width:50px;height:50px;object-fit:cover;border-radius:8px;"></td>
                <td>${post.title}</td>
                <td>${post.category || '-'}</td>
                <td>${post.author || '-'}</td>
                <td>${post.is_active ? '<span class="badge-success">Aktif</span>' : '<span class="badge-danger">Pasif</span>'}</td>
                <td><button class="btn btn-secondary" onclick="deleteBlogPost(${post.id})">Sil</button></td>
            </tr>
        `).join('');
    } catch (e) { showToast(e.message, 'error'); }
}

function openBlogModal() {
    document.getElementById('blogForm').reset();
    document.getElementById('blogPreview').style.display = 'none';
    document.getElementById('blogCoverInput').value = '';
    openModal('blogModal');
}

async function createBlogPost(event) {
    event.preventDefault();
    const form = document.getElementById('blogForm');
    const data = {
        title: form.title.value,
        category: form.category.value,
        author: form.author.value,
        summary: form.summary.value,
        content: form.content.value,
        cover_image: form.cover_image.value || null,
        is_active: form.is_active.checked
    };
    try {
        await adminApi.createBlogPost(data);
        showToast('Blog yazısı oluşturuldu.', 'success');
        closeModal('blogModal');
        loadBlogPosts();
    } catch (e) { showToast(e.message, 'error'); }
}

async function deleteBlogPost(id) {
    if (!confirm('Emin misiniz?')) return;
    try { await adminApi.deleteBlogPost(id); showToast('Blog silindi.', 'success'); loadBlogPosts(); }
    catch (e) { showToast(e.message, 'error'); }
}

// ---------- BAŞVURULAR ----------
async function loadApplications() {
    const container = document.getElementById('applicationsTableBody');
    if (!container) return;
    try {
        const apps = await adminApi.getApplications();
        if (!apps.length) { container.innerHTML = '<tr><td colspan="7">Henüz başvuru yok.</td></tr>'; return; }
        container.innerHTML = apps.map(a => `
            <tr>
                <td>${a.name} ${a.surname}</td>
                <td>${a.email || '-'}</td>
                <td>${a.phone || '-'}</td>
                <td>${a.goal || '-'}</td>
                <td>${a.status}</td>
                <td>${new Date(a.created_at).toLocaleDateString('tr-TR')}</td>
                <td><button class="btn btn-secondary" onclick="updateApplicationStatus(${a.id}, 'Onaylandı')">Onayla</button> <button class="btn btn-secondary" onclick="deleteApplication(${a.id})">Sil</button></td>
            </tr>
        `).join('');
    } catch (e) { showToast(e.message, 'error'); }
}

async function updateApplicationStatus(id, status) {
    try { await adminApi.updateApplication(id, { status }); showToast('Başvuru güncellendi.', 'success'); loadApplications(); }
    catch (e) { showToast(e.message, 'error'); }
}

async function deleteApplication(id) {
    if (!confirm('Emin misiniz?')) return;
    try { await adminApi.deleteApplication(id); showToast('Başvuru silindi.', 'success'); loadApplications(); }
    catch (e) { showToast(e.message, 'error'); }
}

// ---------- RANDEVULAR ----------
async function loadAppointments() {
    const container = document.getElementById('appointmentsTableBody');
    if (!container) return;
    try {
        const apts = await adminApi.getAppointments();
        if (!apts.length) { container.innerHTML = '<tr><td colspan="7">Henüz randevu yok.</td></tr>'; return; }
        container.innerHTML = apts.map(a => `
            <tr>
                <td>${a.name}</td>
                <td>${a.date}</td>
                <td>${a.time}</td>
                <td>${a.service || '-'}</td>
                <td>${a.status}</td>
                <td>${a.email || '-'}</td>
                <td><button class="btn btn-secondary" onclick="updateAppointmentStatus(${a.id}, 'Onaylandı')">Onayla</button> <button class="btn btn-secondary" onclick="deleteAppointment(${a.id})">Sil</button></td>
            </tr>
        `).join('');
    } catch (e) { showToast(e.message, 'error'); }
}

async function updateAppointmentStatus(id, status) {
    try { await adminApi.updateAppointment(id, { status }); showToast('Randevu güncellendi.', 'success'); loadAppointments(); }
    catch (e) { showToast(e.message, 'error'); }
}

async function deleteAppointment(id) {
    if (!confirm('Emin misiniz?')) return;
    try { await adminApi.deleteAppointment(id); showToast('Randevu silindi.', 'success'); loadAppointments(); }
    catch (e) { showToast(e.message, 'error'); }
}

// ---------- MEDYA ----------
async function loadMedia() {
    const container = document.getElementById('mediaGrid');
    if (!container) return;
    try {
        const media = await adminApi.getMedia();
        if (!media.length) { container.innerHTML = '<p>Henüz medya yok.</p>'; return; }
        container.innerHTML = media.map(m => `
            <div style="position:relative;display:inline-block;margin:10px;">
                <img src="${m.url}" style="width:100px;height:100px;object-fit:cover;border-radius:8px;">
                <button class="btn btn-secondary" style="position:absolute;top:5px;right:5px;padding:2px 8px;" onclick="deleteMedia(${m.id})">×</button>
            </div>
        `).join('');
    } catch (e) { showToast(e.message, 'error'); }
}

async function deleteMedia(id) {
    if (!confirm('Emin misiniz?')) return;
    try { await adminApi.deleteMedia(id); showToast('Medya silindi.', 'success'); loadMedia(); }
    catch (e) { showToast(e.message, 'error'); }
}

// ---------- SATIN ALMA ----------
async function loadPurchases() {
    const container = document.getElementById('purchasesTableBody');
    if (!container) return;
    try {
        const purchases = await adminApi.getPurchases();
        if (!purchases.length) { container.innerHTML = '<tr><td colspan="6">Henüz satın alma yok.</td></tr>'; return; }
        container.innerHTML = purchases.map(p => `
            <tr>
                <td>${p.name} ${p.surname}</td>
                <td>${p.email}</td>
                <td>${p.package_name}</td>
                <td>₺${p.price}</td>
                <td>${p.status}</td>
                <td>${new Date(p.created_at).toLocaleDateString('tr-TR')}</td>
            </tr>
        `).join('');
    } catch (e) { showToast(e.message, 'error'); }
}

// ---------- SİTE AYARLARI ----------
async function loadSettings() {
    try {
        const settings = await adminApi.getSiteSettings();
        const form = document.getElementById('settingsForm');
        if (form) {
            form.site_name.value = settings.site_name || '';
            form.hero_title.value = settings.hero_title || '';
            form.hero_description.value = settings.hero_description || '';
            form.footer_text.value = settings.footer_text || '';
            form.phone.value = settings.phone || '';
            form.email.value = settings.email || '';
            form.about_text.value = settings.about_text || '';
        }
    } catch (e) { showToast(e.message, 'error'); }
}

async function saveSettings(event) {
    event.preventDefault();
    const form = document.getElementById('settingsForm');
    const data = {
        site_name: form.site_name.value,
        hero_title: form.hero_title.value,
        hero_description: form.hero_description.value,
        footer_text: form.footer_text.value,
        phone: form.phone.value,
        email: form.email.value,
        about_text: form.about_text.value
    };
    try { await adminApi.updateSiteSettings(data); showToast('Ayarlar kaydedildi.', 'success'); }
    catch (e) { showToast(e.message, 'error'); }
}

// ---------- SOSYAL MEDYA ----------
async function loadSocialLinks() {
    try {
        const settings = await adminApi.getSiteSettings();
        const social = settings.social || {};
        const form = document.getElementById('socialForm');
        if (form) {
            form.instagram.value = social.instagram || '';
            form.tiktok.value = social.tiktok || '';
            form.youtube.value = social.youtube || '';
            form.whatsapp.value = social.whatsapp || '';
            form.email.value = social.email || '';
        }
    } catch (e) { showToast(e.message, 'error'); }
}

async function saveSocialLinks(event) {
    event.preventDefault();
    const form = document.getElementById('socialForm');
    const data = {
        instagram: form.instagram.value,
        tiktok: form.tiktok.value,
        youtube: form.youtube.value,
        whatsapp: form.whatsapp.value,
        email: form.email.value
    };
    try { await adminApi.updateSocialLinks(data); showToast('Sosyal linkler kaydedildi.', 'success'); }
    catch (e) { showToast(e.message, 'error'); }
}