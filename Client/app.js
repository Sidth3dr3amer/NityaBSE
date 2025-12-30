// Use environment variable or fallback to localhost for development
const API_URL = window.ENV?.VITE_API_URL || 'http://localhost:5000/api';
const container = document.getElementById('announcementsContainer');
const searchInput = document.getElementById('searchCompany');
const categoryFilter = document.getElementById('categoryFilter');
const sortFilter = document.getElementById('sortFilter');
const refreshBtn = document.getElementById('refreshBtn');

let debounceTimer;
let cachedAnnouncements = [];
let currentPage = 1;
const ITEMS_PER_PAGE = 10;

async function fetchAnnouncements() {
    try {
        container.innerHTML = '<div class="loading-state">Loading announcements...</div>';
        
        const params = new URLSearchParams();
        const company = searchInput.value.trim();
        const category = categoryFilter.value;
        
        if (company) params.append('company', company);
        if (category) params.append('category', category);
        
        const response = await fetch(`${VITE_API_URL}/announcements?${params}`);
        const data = await response.json();
        
        if (!data.success) {
            throw new Error('Failed to fetch announcements');
        }
        
        cachedAnnouncements = data.data;
        currentPage = 1;
        applySortAndDisplay();
        updateLastUpdated();
    } catch (error) {
        console.error('Error:', error);
        container.innerHTML = '<div class="no-results">Failed to load announcements. Please try again.</div>';
    }
}

function updateLastUpdated() {
    const lastUpdated = document.getElementById('lastUpdated');
    const now = new Date();
    lastUpdated.textContent = `Last sync: ${now.toLocaleString('en-IN', { 
        hour: '2-digit', 
        minute: '2-digit',
        day: 'numeric',
        month: 'short'
    })}`;
}

function applySortAndDisplay() {
    let sorted = [...cachedAnnouncements];
    const sortOrder = sortFilter.value;
    
    sorted.sort((a, b) => {
        const dateA = new Date(a.filed_at);
        const dateB = new Date(b.filed_at);
        return sortOrder === 'newest' ? dateB - dateA : dateA - dateB;
    });
    
    displayAnnouncements(sorted);
}

function displayAnnouncements(announcements) {
    if (!announcements || announcements.length === 0) {
        container.innerHTML = '<div class="no-results">No announcements found</div>';
        return;
    }
    
    // Update stats
    updateStats(announcements);
    
    // Pagination calculations
    const totalItems = announcements.length;
    const totalPages = Math.ceil(totalItems / ITEMS_PER_PAGE);
    const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
    const endIndex = startIndex + ITEMS_PER_PAGE;
    const paginatedAnnouncements = announcements.slice(startIndex, endIndex);
    
    const cardsHtml = paginatedAnnouncements.map((announcement, index) => {
        const isRecent = isRecentAnnouncement(announcement.filed_at);
        const timeAgo = getTimeAgo(announcement.filed_at);
        
        return `
        <div class="announcement-card ${isRecent ? 'recent' : ''}">
            <div class="card-header">
                <div class="company-section">
                    <h2 class="company-name">${escapeHtml(announcement.company_name)}</h2>
                    ${announcement.company_code ? `<span class="company-code">BSE: ${escapeHtml(announcement.company_code)}</span>` : ''}
                </div>
                <div class="meta-section">
                    ${isRecent ? '<span class="new-indicator">NEW</span>' : ''}
                    <span class="category-badge ${announcement.category || 'other'}">
                        ${formatCategory(announcement.category)}
                    </span>
                </div>
            </div>
            
            <div class="filing-info">
                <div class="time-info">
                    <span class="label">Filed:</span>
                    <span class="time-main">${formatDate(announcement.filed_at)}</span>
                    ${timeAgo ? `<span class="time-ago">${timeAgo}</span>` : ''}
                </div>
            </div>
            
            <div class="announcement-content">
                <div class="subject-label">Subject:</div>
                <div class="subject-text">
                    ${escapeHtml(announcement.subject)}
                </div>
                ${announcement.summary && announcement.summary !== announcement.subject ? `
                    <div class="summary-section">
                        <div class="summary-label">AI Summary:</div>
                        <div class="summary-text">
                            ${escapeHtml(announcement.summary)}
                        </div>
                    </div>
                ` : ''}
            </div>
            
            <div class="action-bar">
                <div class="action-buttons">
                    ${announcement.pdf_url ? `
                        <button class="action-btn primary" onclick="openPreview('${escapeHtml(announcement.pdf_url)}', 'pdf', '${escapeHtml(announcement.company_name)}')">
                            <span class="btn-icon">&#128196;</span>
                            View Disclosure
                        </button>
                        <a href="${escapeHtml(announcement.pdf_url)}" target="_blank" class="action-btn secondary">
                            <span class="btn-icon">&#8595;</span>
                            Download PDF
                        </a>
                    ` : ''}
                    
                </div>
            </div>
        </div>
    `}).join('');
    
    // Pagination controls
    const paginationHtml = `
        <div class="pagination">
            <div class="pagination-info">
                Showing ${startIndex + 1}-${Math.min(endIndex, totalItems)} of ${totalItems} announcements
            </div>
            <div class="pagination-controls">
                <button class="page-btn" onclick="goToPage(1)" ${currentPage === 1 ? 'disabled' : ''}>
                    First
                </button>
                <button class="page-btn" onclick="goToPage(${currentPage - 1})" ${currentPage === 1 ? 'disabled' : ''}>
                    Previous
                </button>
                <span class="page-indicator">Page ${currentPage} of ${totalPages}</span>
                <button class="page-btn" onclick="goToPage(${currentPage + 1})" ${currentPage === totalPages ? 'disabled' : ''}>
                    Next
                </button>
                <button class="page-btn" onclick="goToPage(${totalPages})" ${currentPage === totalPages ? 'disabled' : ''}>
                    Last
                </button>
            </div>
        </div>
    `;
    
    container.innerHTML = cardsHtml + paginationHtml;
}

function goToPage(page) {
    currentPage = page;
    applySortAndDisplay();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function formatCategory(category) {
    const categories = {
        'agm_egm': 'AGM/EGM',
        'board_meeting': 'Board Meeting',
        'company_update': 'Company Update',
        'corp_action': 'Corporate Action',
        'insider_trading': 'Insider Trading / SAST',
        'new_listing': 'New Listing',
        'results': 'Results',
        'integrated_filing': 'Integrated Filing',
        'other': 'Other'
    };
    return categories[category] || 'Other';
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('en-IN', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function getTimeAgo(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} min ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
    return '';
}

function isRecentAnnouncement(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffHours = (now - date) / 3600000;
    return diffHours < 24; // Less than 24 hours old
}

function updateStats(announcements) {
    const statsBar = document.getElementById('statsBar');
    const total = announcements.length;
    const recent = announcements.filter(a => isRecentAnnouncement(a.filed_at)).length;
    const categories = {};
    announcements.forEach(a => {
        categories[a.category] = (categories[a.category] || 0) + 1;
    });
    
    statsBar.innerHTML = `
        <div class="stat-item">
            <span class="stat-value">${total}</span>
            <span class="stat-label">Total</span>
        </div>
        <div class="stat-item highlight">
            <span class="stat-value">${recent}</span>
            <span class="stat-label">Last 24hrs</span>
        </div>
        ${Object.entries(categories).map(([cat, count]) => `
            <div class="stat-item">
                <span class="stat-value">${count}</span>
                <span class="stat-label">${formatCategory(cat)}</span>
            </div>
        `).join('')}
    `;
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function debounceSearch() {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
        fetchAnnouncements();
    }, 500);
}

searchInput.addEventListener('input', debounceSearch);
categoryFilter.addEventListener('change', fetchAnnouncements);
sortFilter.addEventListener('change', applySortAndDisplay);
refreshBtn.addEventListener('click', fetchAnnouncements);

// Preview Modal Functions
function openPreview(url, type, companyName) {
    const modal = document.getElementById('previewModal');
    const modalTitle = document.getElementById('previewTitle');
    const previewContent = document.getElementById('previewContent');
    
    modalTitle.textContent = `${companyName} - ${type === 'pdf' ? 'PDF Document' : 'Screenshot'}`;
    
    if (type === 'pdf') {
        // Use Google Docs Viewer or embed tag as fallback for PDFs with CORS issues
        previewContent.innerHTML = `
            <div class="pdf-preview-container">
                <iframe src="https://docs.google.com/viewer?url=${encodeURIComponent(url)}&embedded=true" 
                        width="100%" 
                        height="100%" 
                        frameborder="0"
                        style="border: none;">
                </iframe>
                <div class="pdf-fallback">
                    <p>Unable to load preview?</p>
                    <a href="${url}" target="_blank" class="link-btn">Open PDF in New Tab</a>
                </div>
            </div>
        `;
    } else {
        previewContent.innerHTML = `
            <img src="${url}" alt="Screenshot" style="max-width: 100%; height: auto;">
        `;
    }
    
    modal.style.display = 'block';
}

function closePreview() {
    const modal = document.getElementById('previewModal');
    const previewContent = document.getElementById('previewContent');
    modal.style.display = 'none';
    previewContent.innerHTML = '';
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('previewModal');
    if (event.target === modal) {
        closePreview();
    }
}

fetchAnnouncements();
