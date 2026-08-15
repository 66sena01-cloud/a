const ADMIN_API_BASE = '/api';
let authToken = localStorage.getItem('adminToken');

function setAuthToken(token) {
    authToken = token;
    if (token) localStorage.setItem('adminToken', token);
    else localStorage.removeItem('adminToken');
}

async function adminFetch(url, options = {}) {
    if (!authToken) {
        window.location.href = '/login.html';
        throw new Error('Yetkilendirme gerekli.');
    }
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`,
                ...options.headers
            },
            ...options
        });
        if (response.status === 401) {
            setAuthToken(null);
            window.location.href = '/login.html';
            throw new Error('Oturum süresi doldu.');
        }
        const data = await response.json();
        if (!response.ok || !data.success) {
            throw new Error(data.message || 'Bir hata oluştu.');
        }
        return data.data;
    } catch (error) {
        console.error('Admin API Error:', error);
        throw error;
    }
}

const adminApi = {
    login: async (email, password) => {
        const response = await fetch(`${ADMIN_API_BASE}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        const data = await response.json();
        if (!response.ok || !data.success) {
            throw new Error(data.message || 'Giriş başarısız.');
        }
        return data.data;
    },
    logout: () => setAuthToken(null),
    getDashboard: () => adminFetch(`${ADMIN_API_BASE}/dashboard`),

    // Paketler
    getPackages: () => adminFetch(`${ADMIN_API_BASE}/packages`),
    getPackage: (id) => adminFetch(`${ADMIN_API_BASE}/packages/${id}`),
    createPackage: (data) => adminFetch(`${ADMIN_API_BASE}/packages`, {
        method: 'POST',
        body: JSON.stringify(data)
    }),
    updatePackage: (id, data) => adminFetch(`${ADMIN_API_BASE}/packages/${id}`, {
        method: 'PUT',
        body: JSON.stringify(data)
    }),
    deletePackage: (id) => adminFetch(`${ADMIN_API_BASE}/packages/${id}`, {
        method: 'DELETE'
    }),

    // Etkinlikler
    getEvents: () => adminFetch(`${ADMIN_API_BASE}/events`),
    getEvent: (id) => adminFetch(`${ADMIN_API_BASE}/events/${id}`),
    createEvent: (data) => adminFetch(`${ADMIN_API_BASE}/events`, {
        method: 'POST',
        body: JSON.stringify(data)
    }),
    updateEvent: (id, data) => adminFetch(`${ADMIN_API_BASE}/events/${id}`, {
        method: 'PUT',
        body: JSON.stringify(data)
    }),
    deleteEvent: (id) => adminFetch(`${ADMIN_API_BASE}/events/${id}`, {
        method: 'DELETE'
    }),

    // Blog
    getBlogPosts: () => adminFetch(`${ADMIN_API_BASE}/blog`),
    getBlogPost: (id) => adminFetch(`${ADMIN_API_BASE}/blog/${id}`),
    createBlogPost: (data) => adminFetch(`${ADMIN_API_BASE}/blog`, {
        method: 'POST',
        body: JSON.stringify(data)
    }),
    updateBlogPost: (id, data) => adminFetch(`${ADMIN_API_BASE}/blog/${id}`, {
        method: 'PUT',
        body: JSON.stringify(data)
    }),
    deleteBlogPost: (id) => adminFetch(`${ADMIN_API_BASE}/blog/${id}`, {
        method: 'DELETE'
    }),

    // Başvurular
    getApplications: () => adminFetch(`${ADMIN_API_BASE}/applications`),
    updateApplication: (id, data) => adminFetch(`${ADMIN_API_BASE}/applications/${id}`, {
        method: 'PUT',
        body: JSON.stringify(data)
    }),
    deleteApplication: (id) => adminFetch(`${ADMIN_API_BASE}/applications/${id}`, {
        method: 'DELETE'
    }),

    // Randevular
    getAppointments: () => adminFetch(`${ADMIN_API_BASE}/appointments`),
    updateAppointment: (id, data) => adminFetch(`${ADMIN_API_BASE}/appointments/${id}`, {
        method: 'PUT',
        body: JSON.stringify(data)
    }),
    deleteAppointment: (id) => adminFetch(`${ADMIN_API_BASE}/appointments/${id}`, {
        method: 'DELETE'
    }),

    // Medya
    getMedia: () => adminFetch(`${ADMIN_API_BASE}/media`),
    uploadMedia: (formData) => adminFetch(`${ADMIN_API_BASE}/media/upload`, {
        method: 'POST',
        headers: {},
        body: formData
    }),
    deleteMedia: (id) => adminFetch(`${ADMIN_API_BASE}/media/${id}`, {
        method: 'DELETE'
    }),

    // Satın Almalar
    getPurchases: () => adminFetch(`${ADMIN_API_BASE}/purchases`),

    // Site Ayarları & Sosyal
    getSiteSettings: () => adminFetch(`${ADMIN_API_BASE}/site-settings`),
    updateSiteSettings: (data) => adminFetch(`${ADMIN_API_BASE}/site-settings`, {
        method: 'PUT',
        body: JSON.stringify(data)
    }),
    updateSocialLinks: (data) => adminFetch(`${ADMIN_API_BASE}/social-links`, {
        method: 'PUT',
        body: JSON.stringify(data)
    })
};