// App - Router and initialization

const app = {
    currentPage: 'dashboard',
    
    pages: [
        { id: 'dashboard', label: 'Dashboard', icon: Icons.dashboard, render: Pages.dashboard },
        { id: 'process', label: 'Process Invoice', icon: Icons.upload, render: Pages.processInvoice },
        { id: 'history', label: 'Run History', icon: Icons.history, render: Pages.history },
        { id: 'vendors', label: 'Vendors & POs', icon: Icons.vendors, render: Pages.vendors },
        { id: 'settings', label: 'Rules & Settings', icon: Icons.settings, render: Pages.settings },
    ],

    init() {
        this.renderNav();
        
        // Check URL hash for initial page
        const hash = window.location.hash.slice(1) || 'dashboard';
        this.navigate(hash);

        window.addEventListener('hashchange', () => {
            const h = window.location.hash.slice(1) || 'dashboard';
            if (h !== this.currentPage) this.navigate(h);
        });
    },

    renderNav() {
        const nav = document.getElementById('nav-links');
        nav.innerHTML = this.pages.map(p => `
            <div class="nav-link" data-page="${p.id}" onclick="app.navigate('${p.id}')">
                ${p.icon}
                <span>${p.label}</span>
            </div>
        `).join('');
    },

    navigate(pageId, param) {
        const page = this.pages.find(p => p.id === pageId);
        if (!page) return;

        this.currentPage = pageId;
        window.location.hash = pageId;

        // Update nav active state
        document.querySelectorAll('.nav-link').forEach(el => {
            el.classList.toggle('active', el.dataset.page === pageId);
        });

        // Render page
        page.render(param);
    }
};

// Boot
document.addEventListener('DOMContentLoaded', () => app.init());
