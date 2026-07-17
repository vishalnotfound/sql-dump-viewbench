let currentFile = null;
let currentTable = null;
let currentPage = 1;
let pageSize = 50;
let currentSearch = null;
let currentSort = null;
let currentOrder = 'asc';

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

    const fileItems = document.querySelectorAll('#file-list .list-group-item');
    fileItems.forEach(item => {
        if (item.textContent === filename) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });

    await loadTables(filename);
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
        const sourceView = document.getElementById('source-view');

        welcomeDiv.style.display = 'none';
        tableView.style.display = 'none';
        sourceView.style.display = 'none';
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
                    <div class="mt-3">
                        <button class="btn btn-outline-primary btn-sm" onclick="viewSource('${filename}')">
                            <i class="bi bi-file-code me-2"></i>View SQL Source
                        </button>
                    </div>
                </div>
            </div>
        `;
    } catch (error) {
        showToast('Failed to load metadata: ' + error, 'error');
    }
}

async function viewSource(filename) {
    currentFile = filename;
    currentTable = null;

    const infoDiv = document.getElementById('database-info');
    const sourceView = document.getElementById('source-view');
    const tableView = document.getElementById('table-view');

    infoDiv.style.display = 'none';
    tableView.style.display = 'none';
    sourceView.style.display = 'block';

    try {
        const response = await fetch(`/api/files/${filename}/source`);
        if (!response.ok) {
            throw new Error('Failed to load source');
        }
        const sql = await response.text();
        const lines = sql.split('\n');

        sourceView.innerHTML = `
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h5><i class="bi bi-file-code me-2"></i>${filename} - SQL Source</h5>
                <button class="btn btn-outline-secondary btn-sm" onclick="backToInfo()">
                    <i class="bi bi-arrow-left me-2"></i>Back to Info
                </button>
            </div>
            <div class="table-responsive" style="max-height: calc(100vh - 200px); overflow: auto;">
                <table class="table table-dark table-striped table-hover" style="font-family: monospace;">
                    <thead>
                        <tr>
                            <th style="width: 60px;">#</th>
                            <th>SQL Statement</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${renderSQLStatements(lines)}
                    </tbody>
                </table>
            </div>
        `;
    } catch (error) {
        showToast('Failed to load SQL source: ' + error, 'error');
    }
}

function renderSQLStatements(lines) {
    let html = '';
    let lineNum = 1;
    let statementStart = null;
    let statementLines = [];

    function flushStatement() {
        if (statementLines.length === 0) return;
        const content = statementLines.join('\n').trim();
        if (!content) return;
        const type = getStatementType(content);
        html += `
            <tr>
                <td class="text-secondary">${statementStart}</td>
                <td>
                    <span class="badge bg-primary me-2">${type}</span>
                    <code>${escapeHtml(content.substring(0, 200))}${content.length > 200 ? '...' : ''}</code>
                </td>
            </tr>
        `;
        statementLines = [];
    }

    for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        const trimmed = line.trim();

        if (!trimmed || trimmed.startsWith('--') || trimmed.startsWith('#')) {
            statementLines.push(escapeHtml(line));
            continue;
        }

        if (trimmed.toUpperCase().startsWith('CREATE TABLE') || trimmed.toUpperCase().startsWith('INSERT INTO')) {
            flushStatement();
            statementStart = lineNum + i + 1;
            statementLines = [escapeHtml(line)];
        } else if (statementLines.length > 0) {
            statementLines.push(escapeHtml(line));
        }
    }
    flushStatement();

    return html || '<tr><td colspan="2" class="text-center text-secondary">No SQL statements found</td></tr>';
}

function getStatementType(sql) {
    const upper = sql.toUpperCase();
    if (upper.startsWith('CREATE TABLE')) return 'CREATE TABLE';
    if (upper.startsWith('INSERT INTO')) return 'INSERT';
    if (upper.startsWith('DROP')) return 'DROP';
    if (upper.startsWith('ALTER')) return 'ALTER';
    if (upper.startsWith('SELECT')) return 'SELECT';
    return 'OTHER';
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function backToInfo() {
    document.getElementById('source-view').style.display = 'none';
    document.getElementById('table-view').style.display = 'none';
    document.getElementById('database-info').style.display = 'block';
}

async function selectTable(tableName) {
    currentTable = tableName;
    currentPage = 1;
    currentSearch = null;
    currentSort = null;
    currentOrder = 'asc';

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

    if (search !== null) {
        currentSearch = search;
    }
    if (sort !== null) {
        currentSort = sort;
        currentOrder = order;
    }

    try {
        let url = `/api/files/${currentFile}/table/${currentTable}?page=${currentPage}&page_size=${pageSize}`;
        if (currentSearch) {
            url += `&search=${encodeURIComponent(currentSearch)}`;
        }
        if (currentSort) {
            url += `&sort=${encodeURIComponent(currentSort)}&order=${currentOrder}`;
        }

        const response = await fetch(url);
        const data = await response.json();

        const infoDiv = document.getElementById('database-info');
        const tableView = document.getElementById('table-view');

        infoDiv.style.display = 'none';
        tableView.style.display = 'block';

        renderTable(data, tableView);

    } catch (error) {
        showToast('Failed to load table: ' + error, 'error');
    }
}

function renderTable(data, container) {
    if (!data || !data.columns || data.columns.length === 0) {
        container.innerHTML = `
            <div class="text-center py-5">
                <i class="bi bi-table display-1 text-secondary"></i>
                <h5 class="mt-3">No data found</h5>
                <p class="text-secondary">This table is empty</p>
            </div>
        `;
        return;
    }

    const start = ((data.page - 1) * data.page_size) + 1;
    const end = ((data.page - 1) * data.page_size) + (data.rows ? data.rows.length : 0);

    let html = `
        <div class="mb-3 d-flex justify-content-between align-items-center">
            <h5><i class="bi bi-table me-2"></i>${currentTable}</h5>
            <div class="d-flex gap-2">
                <button class="btn btn-outline-secondary btn-sm" onclick="exportCSV()">
                    <i class="bi bi-filetype-csv"></i> Export CSV
                </button>
            </div>
        </div>
        <div class="mb-3">
            <input type="text" id="search-input" class="form-control bg-dark text-light border-secondary" placeholder="Search rows..." value="${currentSearch || ''}">
        </div>
        <div class="table-responsive" style="max-height: calc(100vh - 250px);">
            <table class="table table-dark table-striped table-hover">
                <thead>
                    <tr>
                        ${data.columns.map(col => {
                            const sortIcon = currentSort === col
                                ? (currentOrder === 'asc' ? 'bi-chevron-up' : 'bi-chevron-down')
                                : 'bi-chevron-expand';
                            return `<th style="cursor: pointer;" class="sortable" data-column="${col}" data-current-sort="${currentSort === col ? currentOrder : 'asc'}">
                                ${col} <i class="bi ${sortIcon} ms-1"></i>
                            </th>`;
                        }).join('')}
                    </tr>
                </thead>
                <tbody>
                    ${(data.rows || []).map(row => `
                        <tr>
                            ${data.columns.map(col => `<td>${row[col] !== null && row[col] !== undefined ? row[col] : ''}</td>`).join('')}
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
        <div class="mt-3 d-flex justify-content-between align-items-center">
            <div class="text-secondary">
                Showing ${start} to ${end} of ${data.row_count} rows
            </div>
            <div class="btn-group">
                <button class="btn btn-outline-secondary" ${data.page <= 1 ? 'disabled' : ''} onclick="changePage(-1)">
                    <i class="bi bi-chevron-left"></i> Previous
                </button>
                <button class="btn btn-outline-secondary" ${data.page >= data.total_pages ? 'disabled' : ''} onclick="changePage(1)">
                    Next <i class="bi bi-chevron-right"></i>
                </button>
            </div>
        </div>
    `;

    container.innerHTML = html;

    document.querySelectorAll('.sortable').forEach(th => {
        th.addEventListener('click', () => {
            const col = th.dataset.column;
            const currentSortState = th.dataset.currentSort || 'asc';
            const newOrder = currentSortState === 'asc' ? 'desc' : 'asc';
            loadTableData(currentSearch, col, newOrder);
        });
    });

    const searchInput = document.getElementById('search-input');
    let searchTimeout;
    if (searchInput) {
        searchInput.addEventListener('input', () => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                currentPage = 1;
                currentSearch = searchInput.value;
                loadTableData(searchInput.value, currentSort, currentOrder);
            }, 300);
        });
    }
}

function changePage(delta) {
    currentPage += delta;
    loadTableData(currentSearch, currentSort, currentOrder);
}

function formatBytes(bytes) {
    const sizes = ['B', 'KB', 'MB', 'GB'];
    if (bytes === 0) return '0 B';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return parseFloat((bytes / Math.pow(1024, i)).toFixed(2)) + ' ' + sizes[i];
}

async function exportCSV() {
    if (!currentFile || !currentTable) return;

    try {
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

        let csv = columns.join(',') + '\n';
        allRows.forEach(row => {
            csv += columns.map(col => {
                const val = row[col] ?? '';
                if (typeof val === 'string' && (val.includes(',') || val.includes('"'))) {
                    return '"' + val.replace(/"/g, '""') + '"';
                }
                return val;
            }).join(',') + '\n';
        });

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
