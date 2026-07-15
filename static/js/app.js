let currentFile = null;
let currentTable = null;
let currentPage = 1;
let pageSize = 50;

// Toast notifications
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toast-container');
    const bgColor = type === 'error' ? 'bg-danger' : type === 'success' ? 'bg-success' : 'bg-primary';
    const toastId = 'toast-' + Date.now();

    toastContainer.innerHTML += `
        <div id="${toastId}" class="toast ${bgColor}" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-body text-white">
                ${message}
            </div>
        </div>
    `;

    const toastEl = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastEl, { delay: 3000 });
    toast.show();

    toastEl.addEventListener('hidden.bs.toast', () => {
        toastEl.remove();
    });
}

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    await loadFiles();

    document.getElementById('btn-refresh').addEventListener('click', async () => {
        await loadFiles();
        showToast('Refreshed successfully!', 'success');
    });

    document.getElementById('btn-upload').addEventListener('click', async () => {
        await uploadFile();
    });
});

async function loadFiles() {
    try {
        const response = await fetch('/api/files');
        const files = await response.json();

        const fileList = document.getElementById('file-list');
        fileList.innerHTML = '';

        if (files.length === 0) {
            fileList.innerHTML = '<div class="text-secondary small">No SQL files found</div>';
        } else {
            files.forEach(file => {
                const itemDiv = document.createElement('div');
                itemDiv.className = 'd-flex align-items-center gap-2';

                const itemBtn = document.createElement('button');
                itemBtn.className = 'list-group-item list-group-item-action flex-grow-1 text-start';
                itemBtn.textContent = file.name;
                itemBtn.addEventListener('click', () => selectFile(file.name));

                const deleteBtn = document.createElement('button');
                deleteBtn.className = 'btn btn-outline-danger btn-sm';
                deleteBtn.innerHTML = '<i class="bi bi-trash"></i>';
                deleteBtn.title = 'Delete file';
                deleteBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    deleteFile(file.name);
                });

                itemDiv.appendChild(itemBtn);
                itemDiv.appendChild(deleteBtn);
                fileList.appendChild(itemDiv);
            });
        }
    } catch (error) {
        showToast('Failed to load files: ' + error, 'error');
    }
}

async function uploadFile() {
    const fileInput = document.getElementById('file-upload');
    if (!fileInput.files || fileInput.files.length === 0) {
        showToast('Please select a file to upload', 'error');
        return;
    }

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    try {
        const response = await fetch('/api/files/upload', {
            method: 'POST',
            body: formData
        });
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Upload failed');
        }
        const result = await response.json();
        showToast('File uploaded successfully!', 'success');
        await loadFiles();
        // Reset file input
        fileInput.value = '';
    } catch (error) {
        showToast('Failed to upload file: ' + error.message, 'error');
    }
}

async function deleteFile(filename) {
    if (!confirm(`Are you sure you want to delete "${filename}"?`)) {
        return;
    }

    try {
        const response = await fetch(`/api/files/${filename}`, {
            method: 'DELETE'
        });
        if (!response.ok) {
            throw new Error('Delete failed');
        }
        showToast('File deleted successfully!', 'success');
        // Reset selection if deleted file was current
        if (currentFile === filename) {
            currentFile = null;
            currentTable = null;
            document.getElementById('table-section').style.display = 'none';
            document.getElementById('database-info').style.display = 'none';
            document.getElementById('table-view').style.display = 'none';
            document.getElementById('welcome-message').style.display = 'block';
        }
        await loadFiles();
    } catch (error) {
        showToast('Failed to delete file: ' + error.message, 'error');
    }
}

async function selectFile(filename) {
    currentFile = filename;
    currentTable = null;

    // Update file list UI
    const fileItems = document.querySelectorAll('#file-list .list-group-item');
    fileItems.forEach(item => {
        if (item.textContent === filename) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });

    // Load tables
    await loadTables(filename);

    // Load database info
    await loadDatabaseInfo(filename);
}

async function loadTables(filename) {
    try {
        const response = await fetch(`/api/files/${filename}/tables`);
        const tables = await response.json();

        const tableSection = document.getElementById('table-section');
        const tableList = document.getElementById('table-list');

        tableSection.style.display = 'block';
        tableList.innerHTML = '';

        if (tables.length === 0) {
            tableList.innerHTML = '<div class="text-secondary small">No tables found</div>';
        } else {
            tables.forEach(table => {
                const item = document.createElement('button');
                item.className = 'list-group-item list-group-item-action d-flex justify-content-between align-items-center';
                item.innerHTML = `
                    <span><i class="bi bi-table me-2"></i>${table.name}</span>
                    <span class="badge bg-secondary rounded-pill">${table.rows.toLocaleString()}</span>
                `;
                item.addEventListener('click', () => selectTable(table.name));
                tableList.appendChild(item);
            });
        }
    } catch (error) {
        showToast('Failed to load tables: ' + error, 'error');
    }
}

async function loadDatabaseInfo(filename) {
    try {
        const response = await fetch(`/api/files/${filename}/metadata`);
        const metadata = await response.json();

        const infoDiv = document.getElementById('database-info');
        const welcomeDiv = document.getElementById('welcome-message');
        const tableView = document.getElementById('table-view');

        welcomeDiv.style.display = 'none';
        tableView.style.display = 'none';
        infoDiv.style.display = 'block';

        infoDiv.innerHTML = `
            <div class="card bg-dark border-secondary mb-4">
                <div class="card-body">
                    <h5 class="card-title"><i class="bi bi-database me-2"></i>${filename}</h5>
                    <div class="row">
                        <div class="col-md-3">
                            <div class="text-secondary small">File Size</div>
                            <div class="h5">${formatBytes(metadata.file_size)}</div>
                        </div>
                        <div class="col-md-3">
                            <div class="text-secondary small">Tables</div>
                            <div class="h5">${metadata.num_tables}</div>
                        </div>
                        <div class="col-md-3">
                            <div class="text-secondary small">Total Rows</div>
                            <div class="h5">${metadata.total_rows.toLocaleString()}</div>
                        </div>
                        <div class="col-md-3">
                            <div class="text-secondary small">Created</div>
                            <div class="h5">${new Date(metadata.created_at).toLocaleString()}</div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    } catch (error) {
        showToast('Failed to load metadata: ' + error, 'error');
    }
}

async function selectTable(tableName) {
    currentTable = tableName;
    currentPage = 1;

    // Update table list UI
    const tableItems = document.querySelectorAll('#table-list .list-group-item');
    tableItems.forEach(item => {
        if (item.querySelector('span')?.textContent.includes(tableName)) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });

    await loadTableData();
}

async function loadTableData(search = null, sort = null, order = 'asc') {
    if (!currentFile || !currentTable) return;

    try {
        let url = `/api/files/${currentFile}/table/${currentTable}?page=${currentPage}&page_size=${pageSize}`;
        if (search) {
            url += `&search=${encodeURIComponent(search)}`;
        }
        if (sort) {
            url += `&sort=${encodeURIComponent(sort)}&order=${order}`;
        }

        const response = await fetch(url);
        const data = await response.json();

        const infoDiv = document.getElementById('database-info');
        const tableView = document.getElementById('table-view');

        infoDiv.style.display = 'none';
        tableView.style.display = 'block';

        // Build table
        tableView.innerHTML = `
            <div class="mb-3 d-flex justify-content-between align-items-center">
                <h5><i class="bi bi-table me-2"></i>${currentTable}</h5>
                <div class="d-flex gap-2">
                    <button class="btn btn-outline-secondary btn-sm" onclick="exportCSV()">
                        <i class="bi bi-filetype-csv"></i> Export CSV
                    </button>
                </div>
            </div>
            <div class="mb-3">
                <input type="text" id="search-input" class="form-control bg-dark text-light border-secondary" placeholder="Search rows...">
            </div>
            <div class="table-responsive" style="max-height: calc(100vh - 250px);">
                <table class="table table-dark table-striped table-hover">
                    <thead>
                        <tr>
                            ${data.columns.map(col => `
                                <th style="cursor: pointer;" class="sortable" data-column="${col}">
                                    ${col}
                                    <i class="bi bi-chevron-expand ms-1"></i>
                                </th>
                            `).join('')}
                        </tr>
                    </thead>
                    <tbody>
                        ${data.rows.map(row => `
                            <tr>
                                ${data.columns.map(col => `<td>${escapeHtml(row[col] ?? '')}</td>`).join('')}
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
            <div class="mt-3 d-flex justify-content-between align-items-center">
                <div class="text-secondary">
                    Showing ${((currentPage - 1) * pageSize) + 1} to ${Math.min(currentPage * pageSize, data.row_count)} of ${data.row_count.toLocaleString()} rows
                </div>
                <div class="btn-group">
                    <button class="btn btn-outline-secondary" ${currentPage <= 1 ? 'disabled' : ''} onclick="changePage(-1)">
                        <i class="bi bi-chevron-left"></i> Previous
                    </button>
                    <button class="btn btn-outline-secondary" ${currentPage * pageSize >= data.row_count ? 'disabled' : ''} onclick="changePage(1)">
                        Next <i class="bi bi-chevron-right"></i>
                    </button>
                </div>
            </div>
        `;

        // Add sort handlers
        document.querySelectorAll('.sortable').forEach(th => {
            th.addEventListener('click', () => {
                const col = th.dataset.column;
                const currentSort = th.dataset.currentSort || 'asc';
                const newOrder = currentSort === 'asc' ? 'desc' : 'asc';
                th.dataset.currentSort = newOrder;
                loadTableData(search, col, newOrder);
            });
        });

        // Add search handler
        const searchInput = document.getElementById('search-input');
        let searchTimeout;
        searchInput.addEventListener('input', () => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                currentPage = 1;
                loadTableData(searchInput.value);
            }, 300);
        });

    } catch (error) {
        showToast('Failed to load table: ' + error, 'error');
    }
}

function changePage(delta) {
    currentPage += delta;
    loadTableData();
}

function formatBytes(bytes) {
    const sizes = ['B', 'KB', 'MB', 'GB'];
    if (bytes === 0) return '0 B';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return parseFloat((bytes / Math.pow(1024, i)).toFixed(2)) + ' ' + sizes[i];
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

async function exportCSV() {
    if (!currentFile || !currentTable) return;

    try {
        // Fetch all rows for export
        let offset = 0;
        let allRows = [];
        let columns = [];

        while (true) {
            const url = `/api/files/${currentFile}/table/${currentTable}?page=${Math.floor(offset / pageSize) + 1}&page_size=1000`;
            const response = await fetch(url);
            const data = await response.json();

            if (columns.length === 0) {
                columns = data.columns;
            }

            if (data.rows.length === 0) break;
            allRows.push(...data.rows);

            if (allRows.length >= data.row_count) break;
            offset += 1000;
        }

        // Create CSV
        let csv = columns.join(',') + '\n';
        allRows.forEach(row => {
            csv += columns.map(col => {
                const val = row[col] ?? '';
                // Escape commas and quotes
                if (typeof val === 'string' && (val.includes(',') || val.includes('"'))) {
                    return '"' + val.replace(/"/g, '""') + '"';
                }
                return val;
            }).join(',') + '\n';
        });

        // Download
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${currentTable}.csv`;
        a.click();
        window.URL.revokeObjectURL(url);

        showToast('CSV exported successfully!', 'success');
    } catch (error) {
        showToast('Failed to export CSV: ' + error, 'error');
    }
}
