// API Client - All backend communication
const API_BASE = '/api';

const api = {
    async request(method, path, body = null, isFormData = false) {
        const opts = { method, headers: {} };
        if (body && !isFormData) {
            opts.headers['Content-Type'] = 'application/json';
            opts.body = JSON.stringify(body);
        } else if (body && isFormData) {
            opts.body = body;
        }
        const res = await fetch(`${API_BASE}${path}`, opts);
        if (!res.ok) {
            const err = await res.json().catch(() => ({ detail: res.statusText }));
            throw new Error(err.detail || `HTTP ${res.status}`);
        }
        return res.json();
    },

    // Dashboard
    getStats() { return this.request('GET', '/dashboard/stats'); },

    // Invoice Upload
    uploadInvoice(file) {
        const fd = new FormData();
        fd.append('file', file);
        return this.request('POST', '/invoices/upload', fd, true);
    },

    // Runs
    getRun(id) { return this.request('GET', `/runs/${id}`); },
    getRuns(params = {}) {
        const q = new URLSearchParams(params).toString();
        return this.request('GET', `/runs${q ? '?' + q : ''}`);
    },
    manualDecision(runId, status, notes) {
        return this.request('POST', `/runs/${runId}/manual-decision`, { status, notes });
    },

    // Vendors & POs
    getVendors() { return this.request('GET', '/vendors'); },
    getPurchaseOrders() { return this.request('GET', '/purchase-orders'); },

    // Settings
    getSettings() { return this.request('GET', '/settings'); },
    updateSettings(data) { return this.request('PUT', '/settings', data); },

    // Sample invoices
    getSampleInvoices() { return this.request('GET', '/invoices/samples'); },
};
