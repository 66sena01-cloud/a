document.addEventListener('DOMContentLoaded', () => {
    createNavbar();
    createFooter();
    initScrollReveal();
    initThemeToggle();

    const hamburger = document.getElementById('hamburger');
    if (hamburger) hamburger.addEventListener('click', () => document.getElementById('navLinks').classList.toggle('active'));

    window.addEventListener('scroll', () => {
        const navbar = document.querySelector('.navbar');
        if (navbar) navbar.classList.toggle('scrolled', window.scrollY > 50);
    });

    const page = document.body.dataset.page;
    if (page === 'index') initIndex();
});

function createNavbar() {
    const navbar = document.createElement('nav');
    navbar.className = 'navbar';
    navbar.innerHTML = `
        <div class="container">
            <a href="/" class="logo">SenaFit <span>Nutrition</span></a>
            <ul class="nav-links" id="navLinks">
                <li><a href="/">Ana Sayfa</a></li>
                <li><a href="/packages.html">Programlar</a></li>
                <li><a href="/events.html">Etkinlikler</a></li>
                <li><a href="/blog.html">Blog</a></li>
                <li><a href="/about.html">Hakkımda</a></li>
                <li><a href="/contact.html">İletişim</a></li>
            </ul>
            <div class="nav-actions">
                <button class="theme-toggle" id="themeToggle" aria-label="Tema değiştir">🌙</button>
                <a href="/packages.html" class="btn">Programını Oluştur</a>
                <button class="hamburger" id="hamburger" aria-label="Menü"><span></span><span></span><span></span></button>
            </div>
        </div>
    `;
    document.body.prepend(navbar);
}

function initThemeToggle() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    const toggle = document.getElementById('themeToggle');
    if (toggle) {
        toggle.textContent = savedTheme === 'dark' ? '☀️' : '🌙';
        toggle.addEventListener('click', () => {
            const current = document.documentElement.getAttribute('data-theme');
            const next = current === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', next);
            localStorage.setItem('theme', next);
            toggle.textContent = next === 'dark' ? '☀️' : '🌙';
        });
    }
}

function createFooter() {
    const footer = document.createElement('footer');
    footer.className = 'footer';
    footer.innerHTML = `
        <div class="container">
            <div class="footer-grid">
                <div><h4>SenaFit Nutrition</h4><p>Beslenme ve egzersizde bilimsel, sürdürülebilir ve kişiye özel yaklaşım.</p></div>
                <div><h4>Menü</h4><ul><li><a href="/">Ana Sayfa</a></li><li><a href="/packages.html">Programlar</a></li><li><a href="/events.html">Etkinlikler</a></li><li><a href="/blog.html">Blog</a></li><li><a href="/about.html">Hakkımda</a></li><li><a href="/contact.html">İletişim</a></li></ul></div>
                <div><h4>Hizmetler</h4><ul><li><a href="/packages.html?category=beslenme">Beslenme Programları</a></li><li><a href="/packages.html?category=egzersiz">Egzersiz Programları</a></li><li><a href="/packages.html?category=kombine">Kombine Programlar</a></li></ul></div>
                <div><h4>Sosyal Medya</h4><ul id="footerSocialLinks"></ul></div>
            </div>
            <div class="footer-bottom" id="footerText">© 2026 SenaFit Nutrition. Tüm hakları saklıdır.</div>
        </div>
    `;
    document.body.appendChild(footer);
    loadSiteSettings();
}

async function loadSiteSettings() {
    try {
        const settings = await api.getSiteSettings();
        const social = settings.social || {};
        const container = document.getElementById('footerSocialLinks');
        if (container) {
            container.innerHTML = '';
            if (social.instagram) container.innerHTML += `<li><a href="${social.instagram}" target="_blank">Instagram</a></li>`;
            if (social.tiktok) container.innerHTML += `<li><a href="${social.tiktok}" target="_blank">TikTok</a></li>`;
            if (social.youtube) container.innerHTML += `<li><a href="${social.youtube}" target="_blank">YouTube</a></li>`;
        }
        const footerText = document.getElementById('footerText');
        if (footerText && settings.footer_text) footerText.textContent = settings.footer_text;
    } catch (e) {}
}

function initScrollReveal() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('revealed');
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });
    document.querySelectorAll('.reveal').forEach(el => observer.observe(el));
}

async function initIndex() {
    const featuredContainer = document.getElementById('featuredPackages');
    if (featuredContainer) {
        try {
            const packages = await api.getPackages();
            const featured = packages.filter(p => p.is_featured).slice(0, 3);
            featuredContainer.innerHTML = featured.length ? featured.map(pkg => `
                <div class="package-card ${pkg.is_featured ? 'featured' : ''}">
                    ${pkg.is_featured ? '<div class="badge">EN POPÜLER</div>' : ''}
                    <div class="package-image"><img src="${pkg.cover_image ? '/media/' + pkg.cover_image.replace(/^\/?/, '') : '/placeholder.jpg'}" alt="${pkg.name}" onerror="this.style.display='none'"></div>
                    <div class="package-body">
                        <span class="package-category">${pkg.category}</span>
                        <h3>${pkg.name}</h3>
                        <div class="package-price">₺${pkg.price}</div>
                        <a href="/package-detail.html?slug=${pkg.slug}" class="btn">Detayları Gör</a>
                    </div>
                </div>
            `).join('') : '<p>Yakında yeni programlar burada.</p>';
        } catch (e) {
            featuredContainer.innerHTML = '<p>Paketler yüklenemedi.</p>';
        }
    }

    const eventsContainer = document.getElementById('upcomingEvents');
    if (eventsContainer) {
        try {
            const events = await api.getEvents();
            eventsContainer.innerHTML = events.length ? events.slice(0,3).map(ev => {
                const date = new Date(ev.event_date);
                return `
                    <div class="event-card">
                        <div class="event-date"><span class="day">${date.getDate()}</span><span class="month">${date.toLocaleString('tr-TR', { month: 'short' })}</span></div>
                        <div class="event-info"><h3>${ev.title}</h3><p>${ev.description || ''}</p><p><strong>${ev.event_time || ''}</strong> ${ev.location || ''} ${ev.is_online ? '(Online)' : ''}</p></div>
                    </div>
                `;
            }).join('') : '<p>Şu anda planlanmış bir etkinlik bulunmuyor.</p>';
        } catch (e) {
            eventsContainer.innerHTML = '<p>Etkinlikler yüklenemedi.</p>';
        }
    }

    const blogContainer = document.getElementById('recentBlog');
    if (blogContainer) {
        try {
            const posts = await api.getBlogPosts();
            blogContainer.innerHTML = posts.length ? posts.slice(0,3).map(post => `
                <div class="blog-card">
                    <div class="blog-image"><img src="${post.cover_image ? '/media/' + post.cover_image.replace(/^\/?/, '') : '/placeholder.jpg'}" alt="${post.title}" onerror="this.style.display='none'"></div>
                    <div class="blog-body"><span class="blog-category">${post.category || ''}</span><h3>${post.title}</h3><p>${post.summary || ''}</p><a href="/blog-detail.html?slug=${post.slug}" class="btn btn-secondary">Devamını Oku</a></div>
                </div>
            `).join('') : '<p>Henüz blog yazısı yok.</p>';
        } catch (e) {
            blogContainer.innerHTML = '<p>Blog yazıları yüklenemedi.</p>';
        }
    }

    try {
        const settings = await api.getSiteSettings();
        const heroTitle = document.getElementById('heroTitle');
        const heroDesc = document.getElementById('heroDesc');
        if (heroTitle && settings.hero_title) heroTitle.textContent = settings.hero_title;
        if (heroDesc && settings.hero_description) heroDesc.textContent = settings.hero_description;
    } catch (e) {}
}