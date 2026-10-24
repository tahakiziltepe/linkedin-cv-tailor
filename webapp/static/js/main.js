/**
 * Job Tracker Dashboard Logic
 */

document.addEventListener('DOMContentLoaded', () => {
    Dashboard.init();
});

const Dashboard = {
    // State
    jobs: [],
    filteredJobs: [],
    currentPage: 1,
    itemsPerPage: 15,

    // Elements
    elements: {
        searchInput: document.getElementById('searchInput'),
        statusFilterWrapper: document.getElementById('statusFilterWrapper'),
        statusFilterToggle: document.getElementById('statusFilterToggle'),
        statusFilterDropdown: document.getElementById('statusFilterDropdown'),
        statusFilterClear: document.getElementById('statusFilterClear'),
        jobsTableBody: document.getElementById('jobsTableBody'),
        pagination: document.getElementById('pagination'),
        resultCount: document.getElementById('resultCount'),
        totalCount: document.getElementById('totalCount'),
        notesModal: document.getElementById('notesModal'),
        notesTextarea: document.getElementById('notesTextarea'),
        saveNotesBtn: document.getElementById('saveNotesBtn'),
        modalOverlay: document.querySelector('.modal-overlay'),
        modalCloseBtn: document.querySelector('.modal-close'),
        modalCancelBtn: document.querySelector('.btn-cancel'),
        // Add Job Modal elements
        addJobBtn: document.getElementById('addJobBtn'),
        addJobModalOverlay: document.getElementById('addJobModalOverlay'),
        addJobModal: document.getElementById('addJobModal'),
        addJobModalClose: document.getElementById('addJobModalClose'),
        addJobCancelBtn: document.getElementById('addJobCancelBtn'),
        addJobSaveBtn: document.getElementById('addJobSaveBtn'),
        jobCompany: document.getElementById('jobCompany'),
        jobTitle: document.getElementById('jobTitle'),
        jobUrl: document.getElementById('jobUrl'),
        // Blocked Companies Modal elements
        blockedCompaniesCard: document.getElementById('blockedCompaniesCard'),
        blockedCompaniesModalOverlay: document.getElementById('blockedCompaniesModalOverlay'),
        blockedCompaniesModalClose: document.getElementById('blockedCompaniesModalClose'),
        blockedCompaniesCancelBtn: document.getElementById('blockedCompaniesCancelBtn'),
        blockedCompaniesSaveBtn: document.getElementById('blockedCompaniesSaveBtn'),
        blockedCompaniesTextarea: document.getElementById('blockedCompaniesTextarea'),
        blockedCompaniesExistingList: document.getElementById('blockedCompaniesExistingList'),
        blockedSearchInput: document.getElementById('blockedSearchInput'),
        blockedCountBadge: document.getElementById('blockedCountBadge'),
        blockedRemoveAllBtn: document.getElementById('blockedRemoveAllBtn'),
        blockedListContainer: document.getElementById('blockedListContainer'),
        blockedEmptyState: document.getElementById('blockedEmptyState'),
        blockedNoResults: document.getElementById('blockedNoResults'),
        // Mobile elements
        toggleStatsBtn: document.getElementById('toggleStatsBtn'),
        statsGrid: document.getElementById('statsGrid')
    },

    // Current editing job
    currentEditingJob: null,

    init() {
        this.loadJobs();
        this.setupEventListeners();
        this.applyFilters(); // Initial render
    },

    loadJobs() {
        // Load data from server-injected JSON
        this.jobs = window.INITIAL_JOBS_DATA || [];

        // Ensure properties exist
        this.jobs = this.jobs.map(job => ({
            timestamp: job.timestamp,
            query: job.query,
            company: job.company,
            title: job.title,
            url: job.url,
            status: job.status,
            notes: job.notes || '',
            pdfPath: job.pdf_path || null
        }));
    },

    getSelectedStatuses() {
        const checkboxes = this.elements.statusFilterDropdown.querySelectorAll('input[type="checkbox"]:checked');
        return Array.from(checkboxes).map(cb => cb.value);
    },

    updateStatusFilterLabel() {
        const selected = this.getSelectedStatuses();
        const label = this.elements.statusFilterToggle.querySelector('.multi-select-label');
        if (selected.length === 0) {
            label.textContent = 'All Statuses';
            this.elements.statusFilterToggle.classList.remove('has-selection');
        } else if (selected.length === 1) {
            label.textContent = selected[0];
            this.elements.statusFilterToggle.classList.add('has-selection');
        } else {
            label.textContent = `${selected.length} statuses selected`;
            this.elements.statusFilterToggle.classList.add('has-selection');
        }
    },

    setupEventListeners() {
        this.elements.searchInput.addEventListener('input', () => this.handleSearch());

        // Multi-select status filter toggle
        this.elements.statusFilterToggle.addEventListener('click', (e) => {
            e.stopPropagation();
            this.elements.statusFilterWrapper.classList.toggle('open');
        });

        // Checkbox changes in dropdown
        this.elements.statusFilterDropdown.addEventListener('change', (e) => {
            if (e.target.type === 'checkbox') {
                this.updateStatusFilterLabel();
                this.handleSearch();
            }
        });

        // Clear all button
        this.elements.statusFilterClear.addEventListener('click', (e) => {
            e.stopPropagation();
            this.elements.statusFilterDropdown.querySelectorAll('input[type="checkbox"]').forEach(cb => cb.checked = false);
            this.updateStatusFilterLabel();
            this.handleSearch();
        });

        // Mobile Stats Toggle
        if (this.elements.toggleStatsBtn) {
            this.elements.toggleStatsBtn.addEventListener('click', () => {
                this.elements.statsGrid.classList.toggle('show-mobile');
            });
        }

        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!this.elements.statusFilterWrapper.contains(e.target)) {
                this.elements.statusFilterWrapper.classList.remove('open');
            }
        });

        // Prevent dropdown from closing when clicking inside it
        this.elements.statusFilterDropdown.addEventListener('click', (e) => {
            e.stopPropagation();
        });

        // Delegation for table actions
        this.elements.jobsTableBody.addEventListener('click', (e) => {
            const target = e.target;

            // Delete button
            if (target.closest('.btn-delete')) {
                e.stopPropagation();
                const url = target.closest('.btn-delete').dataset.url;
                this.deleteJob(url);
                return;
            }

            // Edit notes button
            if (target.closest('.btn-edit-notes')) {
                e.stopPropagation();
                const url = target.closest('.btn-edit-notes').dataset.url;
                const notes = target.closest('.btn-edit-notes').dataset.notes;
                this.openNotesModal(url, notes);
                return;
            }
            
            // Prevent row expansion if clicking the link or select
            if (target.closest('a.link') || target.closest('a.download-link') || target.closest('.status-select:not(td)')) {
                return;
            }

            // Row expand/collapse for mobile
            const row = target.closest('tr');
            if (row && window.innerWidth <= 768) {
                row.classList.toggle('expanded');
            }
        });

        // Delegation for status updates
        this.elements.jobsTableBody.addEventListener('change', (e) => {
            if (e.target.classList.contains('status-select')) {
                const url = e.target.dataset.url;
                const newStatus = e.target.value;
                this.updateStatus(url, newStatus);
            }
        });

        // Modal actions
        this.elements.saveNotesBtn.addEventListener('click', () => this.saveNotes());
        this.elements.modalCloseBtn.addEventListener('click', () => this.closeNotesModal());
        this.elements.modalCancelBtn.addEventListener('click', () => this.closeNotesModal());
        this.elements.modalOverlay.addEventListener('click', (e) => {
            if (e.target === this.elements.modalOverlay) this.closeNotesModal();
        });

        // Add Job Modal actions
        this.elements.addJobBtn.addEventListener('click', () => this.openAddJobModal());
        this.elements.addJobModalClose.addEventListener('click', () => this.closeAddJobModal());
        this.elements.addJobCancelBtn.addEventListener('click', () => this.closeAddJobModal());
        this.elements.addJobSaveBtn.addEventListener('click', () => this.saveNewJob());
        this.elements.addJobModalOverlay.addEventListener('click', (e) => {
            if (e.target === this.elements.addJobModalOverlay) this.closeAddJobModal();
        });

        // Blocked Companies Modal actions
        if (this.elements.blockedCompaniesCard) {
            this.elements.blockedCompaniesCard.addEventListener('click', () => this.openBlockedCompaniesModal());
        }
        this.elements.blockedCompaniesModalClose.addEventListener('click', () => this.closeBlockedCompaniesModal());
        this.elements.blockedCompaniesCancelBtn.addEventListener('click', () => this.closeBlockedCompaniesModal());
        this.elements.blockedCompaniesSaveBtn.addEventListener('click', () => this.saveBlockedCompanies());
        this.elements.blockedCompaniesModalOverlay.addEventListener('click', (e) => {
            if (e.target === this.elements.blockedCompaniesModalOverlay) this.closeBlockedCompaniesModal();
        });

        // Blocked Companies search filter
        if (this.elements.blockedSearchInput) {
            this.elements.blockedSearchInput.addEventListener('input', () => this.filterBlockedCompaniesList());
        }

        // Remove All button
        if (this.elements.blockedRemoveAllBtn) {
            this.elements.blockedRemoveAllBtn.addEventListener('click', () => {
                if (confirm('Remove all blocked companies from the list?')) {
                    window.INITIAL_BLOCKED_COMPANIES = [];
                    this.renderBlockedCompaniesList();
                }
            });
        }
    },

    handleSearch(resetPage = true) {
        const query = this.elements.searchInput.value.toLowerCase();
        const selectedStatuses = this.getSelectedStatuses();

        this.filteredJobs = this.jobs.filter(job => {
            const matchesSearch =
                !query ||
                job.company.toLowerCase().includes(query) ||
                job.title.toLowerCase().includes(query) ||
                (job.query && job.query.toLowerCase().includes(query));

            const matchesStatus = selectedStatuses.length === 0 || selectedStatuses.includes(job.status);

            return matchesSearch && matchesStatus;
        });

        if (resetPage) {
            this.currentPage = 1;
        } else {
            // Clamp page if items were removed from filtered results
            const totalPages = Math.max(1, Math.ceil(this.filteredJobs.length / this.itemsPerPage));
            if (this.currentPage > totalPages) this.currentPage = totalPages;
        }
        this.render();
    },

    applyFilters() {
        this.handleSearch();
    },

    render() {
        // Update counts
        this.elements.resultCount.textContent = this.filteredJobs.length;
        this.elements.totalCount.textContent = this.jobs.length;

        // Pagination calculations
        const totalPages = Math.ceil(this.filteredJobs.length / this.itemsPerPage);
        const startIndex = (this.currentPage - 1) * this.itemsPerPage;
        const endIndex = startIndex + this.itemsPerPage;
        const jobsToShow = this.filteredJobs.slice(startIndex, endIndex);

        // Render Table Rows
        this.elements.jobsTableBody.innerHTML = jobsToShow.map(job => this.createJobRowHTML(job)).join('');

        // Render Pagination
        this.renderPagination(totalPages);
    },

    createJobRowHTML(job) {
        const statusClass = `status-${job.status.replace(/ /g, '-')}`;
        // Check if URL is a manually generated ID
        const isManualJob = job.url && job.url.startsWith('manual-job-');
        const titleDisplay = isManualJob
            ? `<span class="font-medium">${job.title}</span>`
            : `<a href="${job.url}" target="_blank" class="link">${job.title}</a>`;

        return `
            <tr>
                <td class="mobile-hidden" data-label="Date & Query">
                    <div class="text-sm text-muted">${job.timestamp}</div>
                    <div class="text-sm font-medium" style="margin-top:2px;">${job.query}</div>
                </td>
                <td class="mobile-only" data-label="Query">
                    <div class="text-sm font-medium">${job.query}</div>
                </td>
                <td class="col-company" data-label="Company">
                    <div class="text-sm text-muted mobile-only" style="margin-bottom: 4px; font-size: 0.75rem;">${job.timestamp}</div>
                    <div class="font-medium">${job.company}</div>
                </td>
                <td class="col-role" data-label="Role">
                    ${titleDisplay}
                    <div class="mobile-only" style="margin-top: 6px;">
                        <span class="badge ${statusClass}">
                            <span class="badge-dot"></span>
                            ${job.status}
                        </span>
                    </div>
                </td>
                <td class="mobile-hidden" data-label="Status">
                    <span class="badge ${statusClass}">
                        <span class="badge-dot"></span>
                        ${job.status}
                    </span>
                </td>
                <td data-label="Notes">
                    <div class="text-sm text-muted mb-1 notes-preview">${this.truncate(job.notes, 50)}</div>
                    <button class="btn btn-outline btn-icon btn-edit-notes" style="padding: 2px 8px; font-size: 11px;" 
                            data-url="${job.url}" data-notes="${this.escapeHtml(job.notes)}">
                        Edit
                    </button>
                </td>
                <td data-label="Other Postings">
                    ${this.renderOtherPostings(job)}
                </td>
                <td data-label="Files">
                    ${job.pdfPath ? `
                        <div class="flex gap-2" style="flex-direction: column;">
                            <a href="/download/${job.pdfPath}" target="_blank" class="download-link">
                                <span>📄</span> Original
                            </a>
                            <a href="/download/${job.pdfPath}?name=M.TahaKiziltepe-CV.pdf" target="_blank" class="download-link">
                                <span>📥</span> App PDF
                            </a>
                        </div>
                    ` : '<span class="text-muted text-sm">-</span>'}
                </td>
                <td data-label="Actions">
                    <div class="flex gap-2 items-center">
                        <div class="select-wrapper">
                            <select class="custom-select status-select" data-url="${job.url}" style="width: 130px;">
                                <option value="" disabled>Status</option>
                                ${this.getStatusOptions(job.status)}
                            </select>
                        </div>
                        <button class="btn btn-danger btn-icon btn-delete" data-url="${job.url}" title="Delete">
                            🗑️
                        </button>
                    </div>
                </td>
            </tr>
        `;
    },

    getOtherPostings(job) {
        if (!job.pdfPath) return null;

        const company = job.company.toLowerCase().trim();
        const counts = {};

        this.jobs.forEach(j => {
            if (j.url !== job.url && j.company.toLowerCase().trim() === company) {
                const status = j.status || 'Unknown';
                counts[status] = (counts[status] || 0) + 1;
            }
        });

        return Object.entries(counts).filter(([, count]) => count > 0);
    },

    renderOtherPostings(job) {
        const postings = this.getOtherPostings(job);
        if (!postings || postings.length === 0) {
            return '<span class="text-muted text-sm">-</span>';
        }
        return postings.map(([status, count]) =>
            `<div class="text-sm"><span class="text-muted">${status}:</span> <strong>${count}</strong></div>`
        ).join('');
    },

    getStatusOptions(currentStatus) {
        const statuses = ['Pending', 'Applied', 'First Touch', 'Interview', 'Offer', 'Rejected', 'Ghosted', 'Not Interested', 'Blocked Company'];
        return statuses.map(s =>
            `<option value="${s}" ${s === currentStatus ? 'selected' : ''}>${s}</option>`
        ).join('');
    },

    renderPagination(totalPages) {
        if (totalPages <= 1) {
            this.elements.pagination.classList.add('hidden');
            return;
        }

        this.elements.pagination.classList.remove('hidden');
        const container = this.elements.pagination.querySelector('.page-numbers');

        let html = '';

        // Previous Button
        const prevDisabled = this.currentPage === 1 ? 'disabled' : '';
        document.getElementById('prevPage').disabled = this.currentPage === 1;
        document.getElementById('nextPage').disabled = this.currentPage === totalPages;

        document.getElementById('prevPage').onclick = () => {
            if (this.currentPage > 1) {
                this.currentPage--;
                this.render();
            }
        };

        document.getElementById('nextPage').onclick = () => {
            if (this.currentPage < totalPages) {
                this.currentPage++;
                this.render();
            }
        };

        // Simple pagination logic: show surrounding pages
        let startPage = Math.max(1, this.currentPage - 2);
        let endPage = Math.min(totalPages, this.currentPage + 2);

        if (totalPages > 5) {
            if (this.currentPage <= 3) endPage = 5;
            if (this.currentPage >= totalPages - 2) startPage = totalPages - 4;
        }

        for (let i = startPage; i <= endPage; i++) {
            html += `<button class="${i === this.currentPage ? 'active' : ''}" onclick="Dashboard.goToPage(${i})">${i}</button>`;
        }

        container.innerHTML = html;

        // Update info text
        document.getElementById('pageInfo').textContent = `Page ${this.currentPage} of ${totalPages}`;
    },

    goToPage(page) {
        this.currentPage = page;
        this.render();
    },

    // actions
    async updateStatus(jobUrl, newStatus) {
        try {
            const response = await fetch('/api/update_status', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url: jobUrl, status: newStatus })
            });

            if (response.ok) {
                // Update local state
                const job = this.jobs.find(j => j.url === jobUrl);
                if (job) {
                    job.status = newStatus;
                    this.handleSearch(false); // Re-render without resetting page
                    this.showToast('Status updated successfully', 'success');
                }
                // Sync blocked companies list so modal shows the new entry
                if (newStatus === 'Blocked Company' && job) {
                    const company = job.company ? job.company.trim() : '';
                    const current = window.INITIAL_BLOCKED_COMPANIES || [];
                    if (company && !current.includes(company)) {
                        window.INITIAL_BLOCKED_COMPANIES = [...current, company];
                    }
                }
            } else {
                throw new Error('Failed to update status');
            }
        } catch (error) {
            console.error(error);
            this.showToast('Error updating status', 'error');
        }
    },

    async deleteJob(jobUrl) {
        if (!confirm('Are you sure you want to delete this job?')) return;

        try {
            const response = await fetch('/api/delete_job', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url: jobUrl })
            });

            if (response.ok) {
                this.jobs = this.jobs.filter(j => j.url !== jobUrl);
                this.handleSearch();
                this.showToast('Job deleted successfully', 'success');
            } else {
                throw new Error('Failed to delete job');
            }
        } catch (error) {
            console.error(error);
            this.showToast('Error deleting job', 'error');
        }
    },

    // Helper functions
    truncate(str, length) {
        if (!str) return '';
        if (str.length <= length) return str;
        return str.substring(0, length) + '...';
    },

    escapeHtml(unsafe) {
        if (!unsafe) return '';
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    },

    // Notes Modal
    openNotesModal(url, currentNotes) {
        this.currentEditingJob = url;
        this.elements.notesTextarea.value = currentNotes;
        this.elements.modalOverlay.classList.add('open');
    },

    closeNotesModal() {
        this.elements.modalOverlay.classList.remove('open');
        this.currentEditingJob = null;
    },

    async saveNotes() {
        if (!this.currentEditingJob) return;

        const newNotes = this.elements.notesTextarea.value;

        try {
            const response = await fetch('/api/update_notes', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url: this.currentEditingJob, notes: newNotes })
            });

            if (response.ok) {
                const job = this.jobs.find(j => j.url === this.currentEditingJob);
                if (job) {
                    job.notes = newNotes;
                    this.handleSearch(false);
                }
                this.closeNotesModal();
                this.showToast('Notes saved successfully', 'success');
            } else {
                throw new Error('Failed to save notes');
            }
        } catch (error) {
            console.error(error);
            this.showToast('Error saving notes', 'error');
        }
    },

    showToast(message, type = 'success') {
        // Simple toast implementation could go here
        // For now just alert or log
        console.log(`[${type}] ${message}`);
    },

    // Add Job Modal
    openAddJobModal() {
        // Reset form
        this.elements.jobCompany.value = '';
        this.elements.jobTitle.value = '';
        this.elements.jobUrl.value = '';
        this.elements.addJobModalOverlay.classList.add('open');
    },

    closeAddJobModal() {
        this.elements.addJobModalOverlay.classList.remove('open');
    },

    async saveNewJob() {
        const company = this.elements.jobCompany.value.trim();
        const title = this.elements.jobTitle.value.trim();
        const url = this.elements.jobUrl.value.trim();

        // Validate required fields
        if (!company) {
            alert('Company is required');
            this.elements.jobCompany.focus();
            return;
        }

        if (!title) {
            alert('Title is required');
            this.elements.jobTitle.focus();
            return;
        }

        try {
            const response = await fetch('/api/add_job', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ company, title, url })
            });

            if (response.ok) {
                const data = await response.json();
                // Add the new job to the beginning of the list
                const newJob = {
                    timestamp: data.job.timestamp,
                    query: data.job.query,
                    company: data.job.company,
                    title: data.job.title,
                    url: data.job.url,
                    status: data.job.status,
                    notes: data.job.notes,
                    pdfPath: data.job.pdf_path
                };
                this.jobs.unshift(newJob);
                this.handleSearch();
                this.closeAddJobModal();
                this.showToast('Job added successfully', 'success');
            } else {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to add job');
            }
        } catch (error) {
            console.error(error);
            alert('Error adding job: ' + error.message);
        }
    },

    // Blocked Companies Modal
    openBlockedCompaniesModal() {
        if (this.elements.blockedSearchInput) this.elements.blockedSearchInput.value = '';
        this.renderBlockedCompaniesList();
        this.elements.blockedCompaniesTextarea.value = '';
        this.elements.blockedCompaniesModalOverlay.classList.add('open');
    },

    renderBlockedCompaniesList() {
        const companies = window.INITIAL_BLOCKED_COMPANIES || [];
        const list = this.elements.blockedCompaniesExistingList;
        const searchQuery = (this.elements.blockedSearchInput ? this.elements.blockedSearchInput.value : '').toLowerCase();

        // Update counter badge
        if (this.elements.blockedCountBadge) {
            this.elements.blockedCountBadge.textContent = companies.length;
        }

        // Toggle Remove All button visibility
        if (this.elements.blockedRemoveAllBtn) {
            this.elements.blockedRemoveAllBtn.style.display = companies.length > 0 ? '' : 'none';
        }

        if (companies.length === 0) {
            list.innerHTML = '';
            if (this.elements.blockedEmptyState) this.elements.blockedEmptyState.style.display = 'flex';
            if (this.elements.blockedNoResults) this.elements.blockedNoResults.style.display = 'none';
            return;
        }

        if (this.elements.blockedEmptyState) this.elements.blockedEmptyState.style.display = 'none';

        // Filter by search
        const filtered = searchQuery
            ? companies.filter(c => c.toLowerCase().includes(searchQuery))
            : companies;

        if (filtered.length === 0) {
            list.innerHTML = '';
            if (this.elements.blockedNoResults) this.elements.blockedNoResults.style.display = 'flex';
            return;
        }

        if (this.elements.blockedNoResults) this.elements.blockedNoResults.style.display = 'none';

        list.innerHTML = filtered.map(c =>
            `<li class="blocked-chip" data-company="${this.escapeHtml(c)}">
                <span class="blocked-chip-dot"></span>
                <span class="blocked-chip-name" title="${this.escapeHtml(c)}">${this.escapeHtml(c)}</span>
                <button class="blocked-chip-remove" title="Remove">&times;</button>
            </li>`
        ).join('');

        // Attach remove listeners
        list.querySelectorAll('.blocked-chip-remove').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const chip = e.target.closest('.blocked-chip');
                const company = chip.dataset.company;
                window.INITIAL_BLOCKED_COMPANIES = (window.INITIAL_BLOCKED_COMPANIES || []).filter(c => c !== company);
                this.renderBlockedCompaniesList();
            });
        });
    },

    filterBlockedCompaniesList() {
        this.renderBlockedCompaniesList();
    },

    closeBlockedCompaniesModal() {
        this.elements.blockedCompaniesModalOverlay.classList.remove('open');
    },

    async saveBlockedCompanies() {
        // Existing (possibly with removals applied) + new entries from textarea
        const existing = window.INITIAL_BLOCKED_COMPANIES || [];
        const newEntries = this.elements.blockedCompaniesTextarea.value
            .split('\n').map(c => c.trim()).filter(c => c.length > 0);

        // Merge and deduplicate using a Set for O(1) lookups
        const seen = new Set(existing);
        const combined = [...existing];
        for (const c of newEntries) {
            if (!seen.has(c)) {
                seen.add(c);
                combined.push(c);
            }
        }

        try {
            const response = await fetch('/api/blocked_companies', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ companies: combined })
            });

            if (response.ok) {
                const data = await response.json();
                window.INITIAL_BLOCKED_COMPANIES = data.companies;
                this.closeBlockedCompaniesModal();
                this.showToast('Blocked companies saved successfully', 'success');
            } else {
                throw new Error('Failed to save blocked companies');
            }
        } catch (error) {
            console.error(error);
            this.showToast('Error saving blocked companies', 'error');
        }
    }
};

window.Dashboard = Dashboard;
