const API_BASE = '/api';

async function fetchAPI(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: { 'Content-Type': 'application/json', ...options.headers },
            ...options
        });
        const data = await response.json();
        if (!response.ok || !data.success) {
            throw new Error(data.message || 'Bir hata oluştu.');
        }
        return data.data;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

const api = {
    getPackages: (filters = {}) => {
        const params = new URLSearchParams(filters).toString();
        return fetchAPI(`${API_BASE}/packages${params ? '?' + params : ''}`);
    },
    getPackage: (id) => fetchAPI(`${API_BASE}/packages/${id}`),
    getEvents: () => fetchAPI(`${API_BASE}/events`),
    getEvent: (id) => fetchAPI(`${API_BASE}/events/${id}`),
    getBlogPosts: () => fetchAPI(`${API_BASE}/blog`),
    getBlogPost: (slug) => fetchAPI(`${API_BASE}/blog/${slug}`),
    getSiteSettings: () => fetchAPI(`${API_BASE}/site-settings`),
    getSocialLinks: () => fetchAPI(`${API_BASE}/social-links`),
    createApplication: (data) => fetchAPI(`${API_BASE}/applications`, {
        method: 'POST', body: JSON.stringify(data)
    }),
    createAppointment: (data) => fetchAPI(`${API_BASE}/appointments`, {
        method: 'POST', body: JSON.stringify(data)
    }),
    createPurchase: (data) => fetchAPI(`${API_BASE}/purchase`, {
        method: 'POST', body: JSON.stringify(data)
    })
};

function showToast(message, type = 'success') {
    const container = document.querySelector('.toast-container') || (() => {
        const div = document.createElement('div');
        div.className = 'toast-container';
        document.body.appendChild(div);
        return div;
    })();
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 3500);
}

function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.add('active');
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.remove('active');
}