// Reusable UI Components

const Icons = {
    dashboard: `<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M4 5a1 1 0 011-1h4a1 1 0 011 1v5a1 1 0 01-1 1H5a1 1 0 01-1-1V5zm10 0a1 1 0 011-1h4a1 1 0 011 1v2a1 1 0 01-1 1h-4a1 1 0 01-1-1V5zm0 7a1 1 0 011-1h4a1 1 0 011 1v5a1 1 0 01-1 1h-4a1 1 0 01-1-1v-5zM4 14a1 1 0 011-1h4a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1v-2z"/></svg>`,
    upload: `<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/></svg>`,
    history: `<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>`,
    vendors: `<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/></svg>`,
    settings: `<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/></svg>`,
    check: `<svg class="w-4 h-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7"/></svg>`,
    x: `<svg class="w-4 h-4 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12"/></svg>`,
    warn: `<svg class="w-4 h-4 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4.5c-.77-.833-2.694-.833-3.464 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z"/></svg>`,
    spinner: `<svg class="w-4 h-4 animate-spin text-brand-500" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path></svg>`,
    doc: `<svg class="w-12 h-12 text-brand-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>`,
    clock: `<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3"/><circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="2" fill="none"/></svg>`,
};

function statusBadge(status) {
    const map = {
        'APPROVED': 'badge-approved',
        'REVIEW_REQUIRED': 'badge-review',
        'REJECTED': 'badge-rejected',
        'pending': 'badge-pending',
        'completed': 'badge-approved',
        'failed': 'badge-rejected',
        'running': 'badge-running',
    };
    const label = status === 'REVIEW_REQUIRED' ? 'REVIEW' : status;
    return `<span class="badge ${map[status] || 'badge-pending'}">${label}</span>`;
}

function statCard(title, value, color, icon) {
    return `
    <div class="card p-5 animate-fade-in">
        <div class="flex items-center justify-between mb-3">
            <span class="text-sm font-medium text-gray-500">${title}</span>
            <div class="w-10 h-10 rounded-lg bg-${color}-50 flex items-center justify-center">
                <span class="text-${color}-500 text-lg font-bold">${icon}</span>
            </div>
        </div>
        <div class="text-2xl font-bold text-gray-900">${value}</div>
    </div>`;
}

function stageTimeline(stages) {
    if (!stages || !stages.length) return '<p class="text-gray-400 text-sm">No stages recorded</p>';
    return `<div class="space-y-0">${stages.map((s, i) => {
        let icon, lineColor;
        if (s.status === 'completed') { icon = Icons.check; lineColor = 'bg-green-300'; }
        else if (s.status === 'running') { icon = Icons.spinner; lineColor = 'bg-brand-300'; }
        else if (s.status === 'failed') { icon = Icons.x; lineColor = 'bg-red-300'; }
        else { icon = `<div class="w-4 h-4 rounded-full border-2 border-gray-300"></div>`; lineColor = 'bg-gray-200'; }
        
        const duration = s.started_at && s.completed_at 
            ? `${((new Date(s.completed_at) - new Date(s.started_at)) / 1000).toFixed(1)}s` 
            : '';
        
        return `
        <div class="stage-item relative pl-10 pb-4">
            ${i < stages.length - 1 ? `<div class="stage-line ${lineColor}"></div>` : ''}
            <div class="absolute left-0 top-0.5 w-8 h-8 rounded-full bg-white border-2 ${s.status === 'completed' ? 'border-green-400' : s.status === 'running' ? 'border-brand-400' : s.status === 'failed' ? 'border-red-400' : 'border-gray-200'} flex items-center justify-center">
                ${icon}
            </div>
            <div>
                <div class="flex items-center gap-2">
                    <span class="font-medium text-sm text-gray-900">${s.name}</span>
                    ${duration ? `<span class="text-xs text-gray-400">${duration}</span>` : ''}
                </div>
                ${s.details ? `<p class="text-xs text-gray-500 mt-0.5">${s.details}</p>` : ''}
            </div>
        </div>`;
    }).join('')}</div>`;
}

function validationChecklist(results) {
    if (!results || !results.length) return '<p class="text-gray-400 text-sm">No validation results</p>';
    return `<div class="divide-y divide-gray-100">${results.map(r => `
        <div class="check-item py-2.5">
            <div class="mt-0.5 shrink-0">${r.passed ? Icons.check : Icons.x}</div>
            <div class="min-w-0">
                <div class="text-sm font-medium text-gray-800">${r.rule_name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</div>
                <div class="text-xs text-gray-500 mt-0.5">${r.message}</div>
            </div>
        </div>
    `).join('')}</div>`;
}

function decisionPanel(decision, runId = null) {
    if (!decision) return '';
    const colorMap = { APPROVED: 'green', REVIEW_REQUIRED: 'amber', REJECTED: 'red' };
    const c = colorMap[decision.status] || 'gray';
    return `
    <div class="border-2 border-${c}-200 bg-${c}-50 rounded-xl p-5 animate-fade-in">
        <div class="flex items-center justify-between mb-3">
            <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-full bg-${c}-100 flex items-center justify-center">
                    ${decision.status === 'APPROVED' ? Icons.check : decision.status === 'REJECTED' ? Icons.x : Icons.warn}
                </div>
                <div>
                    <div class="font-bold text-lg text-${c}-800">${decision.status.replace('_', ' ')}</div>
                    ${decision.manual_override ? `<span class="text-xs font-semibold px-2 py-0.5 rounded bg-blue-100 text-blue-800">Manually Verified</span>` : ''}
                </div>
            </div>
        </div>
        <p class="text-sm text-${c}-700 mb-3">${decision.explanation}</p>
        ${decision.reasons && decision.reasons.length ? `
            <div class="mt-3 space-y-1">
                <div class="text-xs font-semibold text-${c}-600 uppercase tracking-wide">Reasons</div>
                ${decision.reasons.map(r => `<div class="text-sm text-${c}-700 flex items-start gap-1.5">
                    <span class="mt-1 shrink-0">•</span><span>${r}</span>
                </div>`).join('')}
            </div>
        ` : ''}
        ${decision.recommended_action ? `
            <div class="mt-3 pt-3 border-t border-${c}-200">
                <div class="text-xs font-semibold text-${c}-600 uppercase tracking-wide mb-1">Recommended Action</div>
                <div class="text-sm text-${c}-800">${decision.recommended_action}</div>
            </div>
        ` : ''}
        ${decision.status === 'REVIEW_REQUIRED' && runId ? `
            <div class="mt-4 pt-3 border-t border-amber-200 flex flex-wrap items-center gap-3">
                <button onclick="Pages.approveManually(${runId})" class="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold rounded-lg shadow-sm transition-colors flex items-center gap-1.5 cursor-pointer">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7"/></svg>
                    Mark as Manually Verified & Approve
                </button>
                <button onclick="Pages.rejectManually(${runId})" class="px-3 py-2 bg-rose-100 hover:bg-rose-200 text-rose-700 text-xs font-semibold rounded-lg transition-colors cursor-pointer">
                    Reject Manually
                </button>
            </div>
        ` : ''}
    </div>`;
}

function extractedDataTable(data) {
    if (!data) return '';
    const fields = [
        ['Invoice Number', data.invoice_number],
        ['Invoice Date', data.invoice_date],
        ['Vendor Name', data.vendor_name],
        ['Vendor Tax ID', data.vendor_tax_id],
        ['PO Reference', data.po_reference],
        ['Currency', data.currency],
        ['Subtotal', data.subtotal != null ? formatCurrency(data.subtotal, data.currency) : null],
        ['Tax', data.tax_amount != null ? formatCurrency(data.tax_amount, data.currency) : null],
        ['Total', data.total_amount != null ? formatCurrency(data.total_amount, data.currency) : null],
    ];
    return `
    <table class="w-full text-sm">
        <tbody>
            ${fields.map(([k, v]) => `
                <tr class="border-b border-gray-50">
                    <td class="py-2 pr-4 text-gray-500 font-medium w-36">${k}</td>
                    <td class="py-2 text-gray-900">${v ?? '<span class="text-gray-300 italic">not found</span>'}</td>
                </tr>
            `).join('')}
        </tbody>
    </table>
    ${data.line_items && data.line_items.length ? `
        <div class="mt-4">
            <div class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Line Items</div>
            <table class="w-full text-xs">
                <thead><tr class="bg-gray-50">
                    <th class="text-left py-2 px-3 font-medium text-gray-600">Description</th>
                    <th class="text-right py-2 px-3 font-medium text-gray-600">Qty</th>
                    <th class="text-right py-2 px-3 font-medium text-gray-600">Unit Price</th>
                    <th class="text-right py-2 px-3 font-medium text-gray-600">Amount</th>
                </tr></thead>
                <tbody>${data.line_items.map(li => `
                    <tr class="border-b border-gray-50">
                        <td class="py-1.5 px-3 text-gray-700">${li.description || ''}</td>
                        <td class="py-1.5 px-3 text-right text-gray-700">${li.quantity ?? ''}</td>
                        <td class="py-1.5 px-3 text-right text-gray-700">${li.unit_price != null ? formatCurrency(li.unit_price) : ''}</td>
                        <td class="py-1.5 px-3 text-right text-gray-700">${li.amount != null ? formatCurrency(li.amount) : ''}</td>
                    </tr>
                `).join('')}</tbody>
            </table>
        </div>
    ` : ''}`;
}

function formatCurrency(amount, currency = 'USD') {
    if (amount == null) return '—';
    const sym = currency === 'EUR' ? '€' : currency === 'GBP' ? '£' : '$';
    return `${sym}${Number(amount).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function formatDate(dateStr) {
    if (!dateStr) return '—';
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) + ' ' +
           d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
}

function toast(message, type = 'info') {
    const colors = { info: 'bg-brand-500', success: 'bg-green-500', error: 'bg-red-500' };
    const el = document.createElement('div');
    el.className = `fixed top-4 right-4 z-50 ${colors[type]} text-white px-5 py-3 rounded-lg shadow-lg text-sm font-medium animate-fade-in`;
    el.textContent = message;
    document.body.appendChild(el);
    setTimeout(() => { el.style.opacity = '0'; el.style.transition = 'opacity 0.3s'; setTimeout(() => el.remove(), 300); }, 3500);
}
