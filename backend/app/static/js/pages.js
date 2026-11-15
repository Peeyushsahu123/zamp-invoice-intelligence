// Pages - Each page is a render function returning HTML + optional init function

const Pages = {
    // ==================== DASHBOARD ====================
    async dashboard() {
        const content = document.getElementById('page-content');
        content.innerHTML = `
            <div class="mb-6">
                <h1 class="text-2xl font-bold text-gray-900">Dashboard</h1>
                <p class="text-gray-500 text-sm mt-1">Real-time invoice processing overview</p>
            </div>
            <div id="stats-grid" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                ${[1,2,3,4].map(() => `<div class="card p-5 animate-pulse"><div class="h-16 bg-gray-100 rounded"></div></div>`).join('')}
            </div>
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div class="card p-5">
                    <h2 class="font-semibold text-gray-800 mb-4">Quick Process</h2>
                    <div id="quick-upload" class="upload-area rounded-xl p-8 text-center cursor-pointer">
                        <div class="flex flex-col items-center gap-3">
                            ${Icons.doc}
                            <div>
                                <p class="font-medium text-gray-700">Drop an invoice PDF here</p>
                                <p class="text-sm text-gray-400 mt-1">or click to browse files</p>
                            </div>
                        </div>
                        <input type="file" accept=".pdf" class="hidden" id="dash-file-input">
                    </div>
                    <div id="quick-samples" class="mt-4"></div>
                </div>
                <div class="card p-5">
                    <h2 class="font-semibold text-gray-800 mb-4">Recent Processing Runs</h2>
                    <div id="recent-runs" class="space-y-2">
                        <p class="text-gray-400 text-sm">Loading...</p>
                    </div>
                </div>
            </div>`;

        // Load stats
        try {
            const stats = await api.getStats();
            document.getElementById('stats-grid').innerHTML =
                statCard('Total Processed', stats.total_processed, 'brand', '#') +
                statCard('Approved', stats.approved_count, 'green', '✓') +
                statCard('Review Required', stats.review_count, 'amber', '!') +
                statCard('Rejected', stats.rejected_count, 'red', '✗');
        } catch (e) {
            document.getElementById('stats-grid').innerHTML = `<div class="col-span-4 text-red-500 text-sm">Failed to load stats: ${e.message}</div>`;
        }

        // Load recent runs
        try {
            const runs = await api.getRuns({ limit: 8 });
            const list = runs.runs || runs;
            const container = document.getElementById('recent-runs');
            if (!list.length) {
                container.innerHTML = '<p class="text-gray-400 text-sm py-4 text-center">No invoices processed yet. Upload one to get started!</p>';
            } else {
                container.innerHTML = list.map(r => `
                    <div class="flex items-center justify-between py-2.5 px-3 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors" onclick="app.navigate('history', '${r.id}')">
                        <div class="flex items-center gap-3 min-w-0">
                            <div class="w-8 h-8 rounded-lg bg-gray-100 flex items-center justify-center shrink-0">
                                ${Icons.clock}
                            </div>
                            <div class="min-w-0">
                                <div class="text-sm font-medium text-gray-800 truncate">${r.extracted_data?.invoice_number || r.invoice?.invoice_number || (r.status === 'completed' ? `Document #${r.id}` : 'Processing...')}</div>
                                <div class="text-xs text-gray-400">${formatDate(r.created_at)}</div>
                            </div>
                        </div>
                        ${r.decision ? statusBadge(r.decision.status) : statusBadge(r.status)}
                    </div>
                `).join('');
            }
        } catch (e) {
            document.getElementById('recent-runs').innerHTML = `<p class="text-red-500 text-sm">${e.message}</p>`;
        }

        // Load sample invoices
        try {
            const samples = await api.getSampleInvoices();
            if (samples && samples.length) {
                document.getElementById('quick-samples').innerHTML = `
                    <div class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Sample Invoices</div>
                    <div class="flex flex-wrap gap-2">
                        ${samples.map(s => `
                            <button class="text-xs px-3 py-1.5 bg-brand-50 text-brand-600 rounded-full hover:bg-brand-100 transition-colors font-medium"
                                onclick="Pages.processSampleInvoice('${s.filename}')">
                                ${s.label || s.filename}
                            </button>
                        `).join('')}
                    </div>`;
            }
        } catch(e) { /* ignore */ }

        // File upload handlers
        const uploadArea = document.getElementById('quick-upload');
        const fileInput = document.getElementById('dash-file-input');
        uploadArea.addEventListener('click', () => fileInput.click());
        uploadArea.addEventListener('dragover', e => { e.preventDefault(); uploadArea.classList.add('drag-over'); });
        uploadArea.addEventListener('dragleave', () => uploadArea.classList.remove('drag-over'));
        uploadArea.addEventListener('drop', e => {
            e.preventDefault(); uploadArea.classList.remove('drag-over');
            if (e.dataTransfer.files[0]) Pages.processFile(e.dataTransfer.files[0]);
        });
        fileInput.addEventListener('change', e => { if (e.target.files[0]) Pages.processFile(e.target.files[0]); });
    },

    // ==================== PROCESS INVOICE ====================
    async processInvoice() {
        const content = document.getElementById('page-content');
        content.innerHTML = `
            <div class="mb-6">
                <h1 class="text-2xl font-bold text-gray-900">Process Invoice</h1>
                <p class="text-gray-500 text-sm mt-1">Upload a vendor invoice PDF for AI-powered extraction and validation</p>
            </div>
            <div class="grid grid-cols-1 xl:grid-cols-3 gap-6">
                <!-- Upload Column -->
                <div class="xl:col-span-1 space-y-4">
                    <div class="card p-5">
                        <h3 class="font-semibold text-gray-800 mb-3">Upload Invoice</h3>
                        <div id="upload-area" class="upload-area rounded-xl p-10 text-center cursor-pointer">
                            <div class="flex flex-col items-center gap-3">
                                ${Icons.doc}
                                <div>
                                    <p class="font-medium text-gray-700">Drop PDF here</p>
                                    <p class="text-sm text-gray-400 mt-1">or click to browse</p>
                                </div>
                            </div>
                            <input type="file" accept=".pdf" class="hidden" id="file-input">
                        </div>
                    </div>
                    <div class="card p-5">
                        <h3 class="font-semibold text-gray-800 mb-3">Sample Invoices</h3>
                        <div id="sample-list" class="space-y-2"><p class="text-gray-400 text-sm">Loading...</p></div>
                    </div>
                    <div id="stage-panel" class="card p-5 hidden">
                        <h3 class="font-semibold text-gray-800 mb-3">Processing Stages</h3>
                        <div id="stages-content"></div>
                    </div>
                </div>

                <!-- Results Column -->
                <div class="xl:col-span-2 space-y-4">
                    <div id="decision-container"></div>
                    <div id="extracted-panel" class="card p-5 hidden">
                        <div class="flex items-center justify-between mb-3">
                            <h3 class="font-semibold text-gray-800">Extracted Invoice Data</h3>
                            <span id="extraction-method" class="text-xs px-2 py-1 rounded-full bg-gray-100 text-gray-500"></span>
                        </div>
                        <div id="extracted-content"></div>
                    </div>
                    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
                        <div id="validation-panel" class="card p-5 hidden">
                            <h3 class="font-semibold text-gray-800 mb-3">Validation Checklist</h3>
                            <div id="validation-content"></div>
                        </div>
                        <div id="po-panel" class="card p-5 hidden">
                            <h3 class="font-semibold text-gray-800 mb-3">Matched Purchase Order</h3>
                            <div id="po-content"></div>
                        </div>
                    </div>
                </div>
            </div>`;

        // Setup upload
        const uploadArea = document.getElementById('upload-area');
        const fileInput = document.getElementById('file-input');
        uploadArea.addEventListener('click', () => fileInput.click());
        uploadArea.addEventListener('dragover', e => { e.preventDefault(); uploadArea.classList.add('drag-over'); });
        uploadArea.addEventListener('dragleave', () => uploadArea.classList.remove('drag-over'));
        uploadArea.addEventListener('drop', e => {
            e.preventDefault(); uploadArea.classList.remove('drag-over');
            if (e.dataTransfer.files[0]) Pages.processFile(e.dataTransfer.files[0]);
        });
        fileInput.addEventListener('change', e => { if (e.target.files[0]) Pages.processFile(e.target.files[0]); });

        // Load samples
        try {
            const samples = await api.getSampleInvoices();
            document.getElementById('sample-list').innerHTML = samples.map(s => `
                <button class="w-full text-left px-3 py-2.5 rounded-lg border border-gray-100 hover:border-brand-200 hover:bg-brand-50 transition-all group"
                    onclick="Pages.processSampleInvoice('${s.filename}')">
                    <div class="flex items-center gap-2">
                        <span class="text-sm font-medium text-gray-700 group-hover:text-brand-600">${s.label}</span>
                    </div>
                    <div class="text-xs text-gray-400 mt-0.5">${s.description || s.filename}</div>
                </button>
            `).join('');
        } catch(e) {
            document.getElementById('sample-list').innerHTML = `<p class="text-red-500 text-sm">${e.message}</p>`;
        }
    },

    // Process a file upload
    async processFile(file) {
        if (!file.name.toLowerCase().endsWith('.pdf')) {
            toast('Please upload a PDF file', 'error');
            return;
        }
        toast('Uploading invoice...', 'info');

        try {
            const result = await api.uploadInvoice(file);
            const runId = result.run_id || result.id;
            toast('Processing started!', 'success');
            Pages.pollRunStatus(runId);
        } catch (e) {
            toast(`Upload failed: ${e.message}`, 'error');
        }
    },

    // Process a sample invoice
    async processSampleInvoice(filename) {
        toast('Processing sample invoice...', 'info');
        try {
            const result = await api.request('POST', `/invoices/process-sample/${filename}`);
            const runId = result.run_id || result.id;
            toast('Processing started!', 'success');
            Pages.pollRunStatus(runId);
        } catch (e) {
            toast(`Processing failed: ${e.message}`, 'error');
        }
    },

    // Poll for run completion and display results
    async pollRunStatus(runId) {
        const stagePanel = document.getElementById('stage-panel');
        if (stagePanel) stagePanel.classList.remove('hidden');

        const poll = async () => {
            try {
                const run = await api.getRun(runId);
                Pages.displayRunResults(run);

                if (run.status === 'completed' || run.status === 'failed') {
                    return; // done
                }
                setTimeout(poll, 800);
            } catch (e) {
                console.error('Poll error:', e);
            }
        };
        poll();
    },

    // Display full run results
    displayRunResults(run) {
        // Stages
        const stagesEl = document.getElementById('stages-content');
        const stagePanel = document.getElementById('stage-panel');
        if (stagesEl && run.stages) {
            stagePanel.classList.remove('hidden');
            stagesEl.innerHTML = stageTimeline(run.stages);
        }

        // Extracted data
        const extractedPanel = document.getElementById('extracted-panel');
        const extractedContent = document.getElementById('extracted-content');
        const methodEl = document.getElementById('extraction-method');
        if (extractedPanel && run.extracted_data) {
            extractedPanel.classList.remove('hidden');
            extractedContent.innerHTML = extractedDataTable(run.extracted_data);
            if (methodEl) {
                const method = run.extraction_method || 'unknown';
                const methodLabel = method === 'llm' ? '🤖 AI Extracted' : method === 'fallback_parser' ? '📋 Pattern Parser' : method;
                methodEl.textContent = methodLabel;
                methodEl.className = `text-xs px-2 py-1 rounded-full ${method === 'llm' ? 'bg-purple-100 text-purple-600' : 'bg-blue-100 text-blue-600'}`;
            }
        }

        // Validation
        const validPanel = document.getElementById('validation-panel');
        const validContent = document.getElementById('validation-content');
        if (validPanel && run.validation_results && run.validation_results.length) {
            validPanel.classList.remove('hidden');
            validContent.innerHTML = validationChecklist(run.validation_results);
        }

        // PO Match
        const poPanel = document.getElementById('po-panel');
        const poContent = document.getElementById('po-content');
        if (poPanel && run.matched_po) {
            poPanel.classList.remove('hidden');
            const po = run.matched_po;
            poContent.innerHTML = `
                <table class="w-full text-sm">
                    <tr class="border-b border-gray-50"><td class="py-2 text-gray-500 font-medium w-32">PO Number</td><td class="py-2 text-gray-900 font-medium">${po.po_number}</td></tr>
                    <tr class="border-b border-gray-50"><td class="py-2 text-gray-500 font-medium">Vendor</td><td class="py-2 text-gray-900">${po.vendor_name || ''}</td></tr>
                    <tr class="border-b border-gray-50"><td class="py-2 text-gray-500 font-medium">PO Amount</td><td class="py-2 text-gray-900">${formatCurrency(po.total_amount)}</td></tr>
                    <tr class="border-b border-gray-50"><td class="py-2 text-gray-500 font-medium">Committed</td><td class="py-2 text-gray-900">${formatCurrency(po.committed_amount || 0)}</td></tr>
                    <tr class="border-b border-gray-50"><td class="py-2 text-gray-500 font-medium">Remaining</td><td class="py-2 text-gray-900 font-medium">${formatCurrency(po.remaining_amount != null ? po.remaining_amount : po.total_amount)}</td></tr>
                    <tr><td class="py-2 text-gray-500 font-medium">Status</td><td class="py-2">${statusBadge(po.status || 'open')}</td></tr>
                </table>`;
        }

        // Decision
        const decisionContainer = document.getElementById('decision-container');
        if (decisionContainer && run.decision) {
            decisionContainer.innerHTML = decisionPanel(run.decision, run.id);
        }
    },

    // ==================== RUN HISTORY ====================
    async history(selectedRunId) {
        const content = document.getElementById('page-content');
        content.innerHTML = `
            <div class="flex items-center justify-between mb-6">
                <div>
                    <h1 class="text-2xl font-bold text-gray-900">Processing History</h1>
                    <p class="text-gray-500 text-sm mt-1">All invoice processing runs and their outcomes</p>
                </div>
                <div class="flex gap-2">
                    <input id="search-input" type="text" placeholder="Search by invoice #, vendor..." 
                        class="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-200 w-64">
                    <select id="status-filter" class="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-200">
                        <option value="">All Statuses</option>
                        <option value="APPROVED">Approved</option>
                        <option value="REVIEW_REQUIRED">Review Required</option>
                        <option value="REJECTED">Rejected</option>
                    </select>
                </div>
            </div>
            <div class="grid grid-cols-1 xl:grid-cols-3 gap-6">
                <div class="xl:col-span-1">
                    <div class="card">
                        <div id="runs-list" class="divide-y divide-gray-50 max-h-[70vh] overflow-y-auto">
                            <p class="text-gray-400 text-sm p-4">Loading...</p>
                        </div>
                    </div>
                </div>
                <div class="xl:col-span-2">
                    <div id="run-detail" class="space-y-4">
                        <div class="card p-8 text-center text-gray-400">
                            <p>Select a run to view details</p>
                        </div>
                    </div>
                </div>
            </div>`;

        const loadRuns = async (search = '', statusFilter = '') => {
            try {
                const params = { limit: 50 };
                if (search) params.search = search;
                if (statusFilter) params.status = statusFilter;
                const data = await api.getRuns(params);
                const runs = data.runs || data;
                const list = document.getElementById('runs-list');
                if (!runs.length) {
                    list.innerHTML = '<p class="text-gray-400 text-sm p-4 text-center">No runs found</p>';
                    return;
                }
                list.innerHTML = runs.map(r => `
                    <div class="p-3 hover:bg-gray-50 cursor-pointer transition-colors ${selectedRunId == r.id ? 'bg-brand-50 border-l-3 border-brand-500' : ''}"
                         onclick="Pages.loadRunDetail(${r.id})">
                        <div class="flex items-center justify-between">
                            <div class="min-w-0">
                                <div class="text-sm font-medium text-gray-800 truncate">${r.extracted_data?.invoice_number || r.invoice?.invoice_number || `Run #${r.id}`}</div>
                                <div class="text-xs text-gray-400 mt-0.5">${r.extracted_data?.vendor_name || r.invoice?.vendor_name || ''} · ${formatDate(r.created_at)}</div>
                            </div>
                            ${r.decision ? statusBadge(r.decision.status) : statusBadge(r.status)}
                        </div>
                    </div>
                `).join('');

                if (selectedRunId) Pages.loadRunDetail(selectedRunId);
            } catch (e) {
                document.getElementById('runs-list').innerHTML = `<p class="text-red-500 text-sm p-4">${e.message}</p>`;
            }
        };

        Pages.historyLoadRuns = loadRuns;
        loadRuns();

        // Search & filter
        let debounce;
        document.getElementById('search-input').addEventListener('input', e => {
            clearTimeout(debounce);
            debounce = setTimeout(() => loadRuns(e.target.value, document.getElementById('status-filter').value), 300);
        });
        document.getElementById('status-filter').addEventListener('change', e => {
            loadRuns(document.getElementById('search-input').value, e.target.value);
        });
    },

    async loadRunDetail(runId) {
        const detail = document.getElementById('run-detail');
        try {
            const run = await api.getRun(runId);
            detail.innerHTML = `
                <div id="decision-container">${run.decision ? decisionPanel(run.decision, run.id) : ''}</div>
                <div id="stage-panel" class="card p-5">
                    <h3 class="font-semibold text-gray-800 mb-3">Processing Stages</h3>
                    <div id="stages-content">${stageTimeline(run.stages)}</div>
                </div>
                <div id="extracted-panel" class="card p-5">
                    <div class="flex items-center justify-between mb-3">
                        <h3 class="font-semibold text-gray-800">Extracted Data</h3>
                        <span id="extraction-method" class="text-xs px-2 py-1 rounded-full ${run.extraction_method === 'llm' ? 'bg-purple-100 text-purple-600' : 'bg-blue-100 text-blue-600'}">
                            ${run.extraction_method === 'llm' ? '🤖 AI Extracted' : '📋 Pattern Parser'}
                        </span>
                    </div>
                    <div id="extracted-content">${extractedDataTable(run.extracted_data)}</div>
                </div>
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
                    <div id="validation-panel" class="card p-5">
                        <h3 class="font-semibold text-gray-800 mb-3">Validation Results</h3>
                        <div id="validation-content">${validationChecklist(run.validation_results)}</div>
                    </div>
                    ${run.matched_po ? `
                    <div id="po-panel" class="card p-5">
                        <h3 class="font-semibold text-gray-800 mb-3">Matched PO</h3>
                        <div id="po-content">
                            <table class="w-full text-sm">
                                <tr class="border-b border-gray-50"><td class="py-2 text-gray-500 font-medium w-32">PO Number</td><td class="py-2 text-gray-900 font-medium">${run.matched_po.po_number}</td></tr>
                                <tr class="border-b border-gray-50"><td class="py-2 text-gray-500 font-medium">PO Amount</td><td class="py-2 text-gray-900">${formatCurrency(run.matched_po.total_amount)}</td></tr>
                                <tr class="border-b border-gray-50"><td class="py-2 text-gray-500 font-medium">Committed</td><td class="py-2 text-gray-900">${formatCurrency(run.matched_po.committed_amount || 0)}</td></tr>
                                <tr><td class="py-2 text-gray-500 font-medium">Remaining</td><td class="py-2 text-gray-900 font-medium">${formatCurrency(run.matched_po.remaining_amount != null ? run.matched_po.remaining_amount : run.matched_po.total_amount)}</td></tr>
                            </table>
                        </div>
                    </div>` : ''}
                </div>`;
        } catch (e) {
            detail.innerHTML = `<div class="card p-5 text-red-500">${e.message}</div>`;
        }
    },

    // ==================== VENDORS & POs ====================
    async vendors() {
        const content = document.getElementById('page-content');
        content.innerHTML = `
            <div class="mb-6">
                <h1 class="text-2xl font-bold text-gray-900">Vendors & Purchase Orders</h1>
                <p class="text-gray-500 text-sm mt-1">Manage approved vendors and their purchase orders</p>
            </div>
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div>
                    <h2 class="font-semibold text-gray-800 mb-3">Vendors</h2>
                    <div id="vendors-list" class="space-y-3"><p class="text-gray-400 text-sm">Loading...</p></div>
                </div>
                <div>
                    <h2 class="font-semibold text-gray-800 mb-3">Purchase Orders</h2>
                    <div id="po-list" class="space-y-3"><p class="text-gray-400 text-sm">Loading...</p></div>
                </div>
            </div>`;

        try {
            const [vendors, pos] = await Promise.all([api.getVendors(), api.getPurchaseOrders()]);

            document.getElementById('vendors-list').innerHTML = (vendors || []).map(v => `
                <div class="card p-4 animate-fade-in">
                    <div class="flex items-center justify-between mb-2">
                        <div class="font-medium text-gray-800">${v.name}</div>
                        ${statusBadge(v.status.toUpperCase ? v.status.toUpperCase() : v.status)}
                    </div>
                    <div class="text-xs text-gray-500 space-y-0.5">
                        <div>Tax ID: ${v.tax_id || '—'}</div>
                        <div>Email: ${v.email || '—'}</div>
                    </div>
                </div>
            `).join('');

            document.getElementById('po-list').innerHTML = (pos || []).map(po => `
                <div class="card p-4 animate-fade-in">
                    <div class="flex items-center justify-between mb-2">
                        <div class="font-medium text-gray-800">${po.po_number}</div>
                        <span class="text-sm font-semibold text-gray-900">${formatCurrency(po.total_amount)}</span>
                    </div>
                    <div class="text-xs text-gray-500 space-y-0.5">
                        <div>Vendor: ${po.vendor_name || po.vendor?.name || '—'}</div>
                        <div>Description: ${po.description || '—'}</div>
                        <div class="flex items-center gap-3 mt-1">
                            <span>Committed: ${formatCurrency(po.committed_amount || 0)}</span>
                            <span>Remaining: ${formatCurrency(po.remaining_amount != null ? po.remaining_amount : po.total_amount)}</span>
                        </div>
                    </div>
                </div>
            `).join('');
        } catch (e) {
            toast(`Failed to load data: ${e.message}`, 'error');
        }
    },

    // ==================== SETTINGS ====================
    async settings() {
        const content = document.getElementById('page-content');
        content.innerHTML = `
            <div class="mb-6">
                <h1 class="text-2xl font-bold text-gray-900">Rules & Settings</h1>
                <p class="text-gray-500 text-sm mt-1">Configure validation rules and tolerance thresholds</p>
            </div>
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div class="card p-5">
                    <h2 class="font-semibold text-gray-800 mb-4">Validation Settings</h2>
                    <div id="settings-form" class="space-y-4"><p class="text-gray-400 text-sm">Loading...</p></div>
                </div>
                <div class="card p-5">
                    <h2 class="font-semibold text-gray-800 mb-4">Validation Rules</h2>
                    <div class="space-y-3">
                        ${[
                            { name: 'Required Fields', desc: 'Invoice must have: number, date, vendor name, total amount', severity: 'Warning' },
                            { name: 'Duplicate Detection', desc: 'Rejects invoices with the same number from the same vendor', severity: 'Critical' },
                            { name: 'Vendor Verification', desc: 'Checks vendor exists and is in APPROVED status', severity: 'Critical (suspended) / Warning (unknown)' },
                            { name: 'PO Matching', desc: 'Matches invoice PO reference to purchase orders in the system', severity: 'Warning' },
                            { name: 'Arithmetic Check', desc: 'Validates subtotal + tax = total within tolerance', severity: 'Warning' },
                            { name: 'Amount Tolerance', desc: 'Invoice total must be within tolerance % of PO amount', severity: 'Critical (>2x tolerance) / Warning' },
                            { name: 'Cumulative Balance', desc: 'Total approved invoices against a PO cannot exceed PO amount + tolerance', severity: 'Critical' },
                        ].map(r => `
                            <div class="p-3 rounded-lg bg-gray-50">
                                <div class="flex items-center justify-between">
                                    <span class="text-sm font-medium text-gray-800">${r.name}</span>
                                    <span class="text-xs text-gray-400">${r.severity}</span>
                                </div>
                                <p class="text-xs text-gray-500 mt-1">${r.desc}</p>
                            </div>
                        `).join('')}
                    </div>
                    <div class="mt-6 p-4 rounded-lg bg-brand-50 border border-brand-100">
                        <h3 class="text-sm font-semibold text-brand-800 mb-2">Decision Precedence</h3>
                        <ol class="text-xs text-brand-700 space-y-1 list-decimal list-inside">
                            <li><strong>REJECTED</strong> — Any critical validation failure</li>
                            <li><strong>REVIEW_REQUIRED</strong> — Any warning-level issue</li>
                            <li><strong>APPROVED</strong> — All validations pass</li>
                        </ol>
                    </div>
                </div>
            </div>`;

        try {
            const settings = await api.getSettings();
            const form = document.getElementById('settings-form');
            const settingsArr = Array.isArray(settings) ? settings : Object.entries(settings).map(([k,v]) => ({key:k, value:v, description: k.replace(/_/g, ' ')}));
            form.innerHTML = settingsArr.map(s => `
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">${(s.description || s.key).replace(/\b\w/g, l => l.toUpperCase())}</label>
                    <input type="text" value="${s.value}" data-key="${s.key}"
                        class="setting-input w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-200">
                </div>
            `).join('') + `
                <button id="save-settings" class="mt-2 px-5 py-2 bg-brand-500 text-white rounded-lg text-sm font-medium hover:bg-brand-600 transition-colors">
                    Save Settings
                </button>`;

            document.getElementById('save-settings').addEventListener('click', async () => {
                const data = {};
                document.querySelectorAll('.setting-input').forEach(inp => {
                    data[inp.dataset.key] = inp.value;
                });
                try {
                    await api.updateSettings(data);
                    toast('Settings saved!', 'success');
                } catch (e) {
                    toast(`Save failed: ${e.message}`, 'error');
                }
            });
        } catch (e) {
            document.getElementById('settings-form').innerHTML = `<p class="text-red-500 text-sm">${e.message}</p>`;
        }
    },

    async approveManually(runId) {
        const notes = prompt("Enter verification notes:", "Approved by AP Reviewer after manual check");
        if (notes === null) return;
        try {
            await api.manualDecision(runId, 'APPROVED', notes);
            toast("Invoice manually verified & approved!", "success");
            await Pages.loadRunDetail(runId);
            if (Pages.historyLoadRuns) Pages.historyLoadRuns();
        } catch (e) {
            toast(`Failed to update: ${e.message}`, "error");
        }
    },

    async rejectManually(runId) {
        const notes = prompt("Enter rejection reason:", "Rejected by AP Reviewer after manual check");
        if (notes === null) return;
        try {
            await api.manualDecision(runId, 'REJECTED', notes);
            toast("Invoice manually rejected", "info");
            await Pages.loadRunDetail(runId);
            if (Pages.historyLoadRuns) Pages.historyLoadRuns();
        } catch (e) {
            toast(`Failed to update: ${e.message}`, "error");
        }
    },
};
