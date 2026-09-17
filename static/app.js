const app = document.getElementById('app');

const state = {
  token: localStorage.getItem('token') || '',
  user: JSON.parse(localStorage.getItem('user') || 'null'),
  page: 'dashboard',
  repricerData: null,
  detailAutoFixSource: [],
  detailAutoFixAI: [],
  detailAutoFixRemaining: []
};

const sectionLabels = {
  'dashboard': 'Dashboard',
  'sourcing': 'Add New Product',
  'listings': 'All Listings',
  'detail': 'Listing Detail',
  'analytics': 'Catalog Analytics',
  'categories': 'Category Explorer',
  'variations': 'Variations',
  'imageStudio': 'AI Image Studio',
  'imageLibrary': 'Image Library',
  'imageReferences': 'Image References',
  'repricer': 'Repricer',
  'amazonIntegration': 'Amazon Integration',
  'orders': 'Orders'
};

function normalizeBaseUrl() {
  return window.location.origin;
}

function showError(element, message) {
  if (!element) return;
  element.textContent = message || '';
  element.classList.add('visible');
}

function clearError(element) {
  if (!element) return;
  element.textContent = '';
  element.classList.remove('visible');
}

function renderLoginPage() {
  return `<div class="auth-page">
    <div class="auth-card">
      <section class="auth-brand">
        <div class="brand-logo">
          <span class="logo-svg logo-svg--lg logo-svg--white" aria-hidden="true">
            <svg viewBox="0 0 160 40" fill="none" xmlns="http://www.w3.org/2000/svg">
              <defs>
                <linearGradient id="logoGradient" x1="0" y1="0" x2="1" y2="1" gradientUnits="objectBoundingBox">
                  <stop offset="0%" stop-color="#14b8a6"/>
                  <stop offset="100%" stop-color="#0d9488"/>
                </linearGradient>
              </defs>
              <g class="logo-mark">
                <path d="M8 30C8 24.477 12.477 20 18 20H42C47.523 20 52 24.477 52 30V32H8V30Z" fill="url(#logoGradient)"/>
                <path d="M18 20L24 14L30 20" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
                <path d="M24 14V30" stroke="white" stroke-width="2" stroke-linecap="round" opacity="0.9"/>
                <circle cx="48" cy="10" r="8" stroke="white" stroke-width="2.5"/>
                <path d="M48 2V18M40 10H56" stroke="white" stroke-width="2" stroke-linecap="round"/>
                <path d="M60 30C60 24.477 64.477 20 70 20H94C99.523 20 104 24.477 104 30V32H60V30Z" fill="url(#logoGradient)"/>
                <path d="M70 20L76 14L82 20" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
                <path d="M76 14V30" stroke="white" stroke-width="2" stroke-linecap="round" opacity="0.9"/>
                <path d="M110 30C110 24.477 114.477 20 120 20H144C149.523 20 154 24.477 154 30V32H110V30Z" fill="url(#logoGradient)"/>
                <path d="M120 20L126 14L132 20" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
                <path d="M126 14V30" stroke="white" stroke-width="2" stroke-linecap="round" opacity="0.9"/>
              </g>
              <text x="130" y="28" class="logo-text-svg" font-family="Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" font-size="28" font-weight="800" letter-spacing="-0.02em" fill="currentColor">Sellrix</text>
            </svg>
          </span>
          <div class="logo-text">Sellrix</div>
        </div>
        <div class="brand-copy">
          <h1>Run your Amazon catalog from one place</h1>
          <p>Find products, create listings, fix pricing, and track performance — all without switching tools.</p>
          <div class="brand-stats">
            <div class="stat">
              <small>Active listings</small>
              <b>128</b>
            </div>
            <div class="stat">
              <small>Monthly profit</small>
              <b>$8.7k</b>
            </div>
          </div>
          <div class="brand-credit">by Chaudhary Commerce Suite</div>
        </div>
      </section>
      <section class="auth-form-panel">
        <div class="top">
          <span class="small-label">Sellrix</span>
          <span class="pill">v2.0</span>
        </div>
        <h2 id="authTitle">Welcome back</h2>
        <div class="sub">Sign in to your workspace</div>
        <div class="form-error" id="authError"></div>
        <div class="auth-form">
          <div class="form-grid">
            <div class="form-field" id="nameField" style="display:none">
              <label for="name">Your name</label>
              <input type="text" id="name" autocomplete="name" placeholder="Jane Seller" />
              <span class="field-hint">This is how you'll appear in the app</span>
            </div>
            <div class="form-field">
              <label for="email">Email address</label>
              <input type="email" id="email" autocomplete="email" placeholder="seller@example.com" />
              <span class="field-hint">We'll send a login link to this address</span>
            </div>
            <div class="form-field">
              <label for="password">Password</label>
              <input type="password" id="password" autocomplete="current-password" placeholder="••••••••" />
              <span class="field-hint">At least 6 characters</span>
            </div>
          </div>
          <div class="form-actions">
            <button class="btn" id="submitAuth">Sign in</button>
            <button class="btn btn-secondary" id="switchMode">Create account</button>
          </div>
          <div class="auth-toggle">
            <span id="modeText">Need an account?</span>
            <a class="muted-link" id="modeLink">Create one</a>
          </div>
        </div>
      </section>
    </div>
  </div>`;
}

function renderDashboardPage() {
  return `<section class="page-wrap">
    <section class="page-heading">
      <div>
        <span class="eyebrow">Overview</span>
        <h1>Dashboard</h1>
      </div>
      <p class="page-description">Your Amazon business at a glance — sales, listings, profit, and what needs attention.</p>
    </section>
    <section class="dashboard-grid">
      <div class="kpi-card">
        <div class="label">Monthly revenue</div>
        <div class="value">$12,420</div>
        <div class="trend positive">+12.8% vs last month</div>
        <div class="kpi-hint">Total sales before Amazon fees</div>
      </div>
      <div class="kpi-card">
        <div class="label">Active listings</div>
        <div class="value">128</div>
        <div class="trend positive">+9 this week</div>
        <div class="kpi-hint">Products currently live and selling on Amazon</div>
      </div>
      <div class="kpi-card">
        <div class="label">Profit margin</div>
        <div class="value">22.3%</div>
        <div class="trend positive">+1.5% trend</div>
        <div class="kpi-hint">What you keep after all costs and fees</div>
      </div>
      <div class="kpi-card">
        <div class="label">Items needing attention</div>
        <div class="value">3</div>
        <div class="trend warning">2 are high priority</div>
        <div class="kpi-hint">Listings with issues that could affect sales</div>
      </div>
    </section>
    <section class="panel-grid two">
      <section class="panel main-panel">
        <div class="panel-title">Products in progress</div>
        <p style="font-size:12px; color:var(--muted); margin-bottom:12px;">These listings are being worked on but aren't live on Amazon yet.</p>
        <table class="table">
          <thead><tr><th>Product</th><th>Status</th><th>Your cost</th><th>Sell price</th><th>Est. profit</th></tr></thead>
          <tbody>
            <tr><td>Eco Cleaning Set</td><td><span class="status draft">Draft — not submitted</span></td><td>$12.50</td><td>$29.99</td><td>$6.10</td></tr>
            <tr><td>Portable LED Lamp</td><td><span class="status review">Needs your review</span></td><td>$18.90</td><td>$39.99</td><td>$8.40</td></tr>
            <tr><td>Smart Organizer Basket</td><td><span class="status live">Ready to submit</span></td><td>$11.00</td><td>$26.90</td><td>$5.80</td></tr>
          </tbody>
        </table>
      </section>
      <section class="panel">
        <div class="panel-title">Account health</div>
        <p style="font-size:12px; color:var(--muted); margin-bottom:16px;">Amazon tracks these metrics. Green = good, Orange = needs work, Red = urgent.</p>
        <div class="health-list">
          <div class="health-row"><span class="health-label">Listing quality</span><span class="health-meter"><span class="meter-fill" style="width:84%"></span></span><span class="health-number">84%</span></div>
          <div class="health-row"><span class="health-label">Amazon sync</span><span class="health-meter"><span class="meter-fill green" style="width:76%"></span></span><span class="health-number">76%</span></div>
          <div class="health-row"><span class="health-label">Content quality</span><span class="health-meter"><span class="meter-fill orange" style="width:91%"></span></span><span class="health-number">91%</span></div>
        </div>
      </section>
    </section>
  </section>`;
}

function renderSourcingPage() {
  return `<section class="page-wrap">
    <section class="page-heading">
      <div>
        <span class="eyebrow">Catalog / Listings</span>
        <h1>Add New Product</h1>
      </div>
      <p class="page-description">Choose how you want to add products to your queue. Your product queue on the right shows all products added but not yet submitted.</p>
    </section>
    
    <section class="method-tabs" role="tablist" aria-label="Add product method" id="sourcingTabs">
      <button class="method-tab active" data-sourcing-tab="manual" role="tab" aria-selected="true">
        <span class="method-tab-icon">✎</span>
        <span class="method-tab-label">Add One Product</span>
        <span class="method-tab-desc">Add one product at a time by pasting its link — we'll fetch the title and image automatically.</span>
      </button>
      <button class="method-tab" data-sourcing-tab="import" role="tab" aria-selected="false">
        <span class="method-tab-icon">📊</span>
        <span class="method-tab-label">Import from Spreadsheet</span>
        <span class="method-tab-desc">Add many products at once from a CSV or Excel file.</span>
      </button>
      <button class="method-tab" data-sourcing-tab="ebay" role="tab" aria-selected="false">
        <span class="method-tab-icon">🛒</span>
        <span class="method-tab-label">Fetch from eBay Seller</span>
        <span class="method-tab-desc">Pull every product from one eBay seller's store.</span>
      </button>
    </section>

    <section class="panel-grid two">
      <section class="panel" id="sourcingFormPanel">
        <div class="panel-title" id="sourcingTabTitle">Add One Product</div>
        <p class="tab-description" id="sourcingTabDesc">Add one product at a time by pasting its link — we'll fetch the title and image automatically.</p>
        
        <div id="sourcingTabContent">
          ${renderAddOneProductForm()}
        </div>
      </section>
      
      <section class="panel queue-panel" style="height: 100%;">
        <div class="panel-title">Your Product Queue</div>
        <p style="font-size:12px; color:var(--muted); margin-bottom:12px;">Products you've added but haven't submitted to Amazon yet. Click one to review details.</p>
        <div class="queue-list" id="queueList">
          <div class="queue-row">
            <div>
              <div class="queue-title">Portable Kitchen Storage Set</div>
              <div class="queue-meta">Source: Supplier A • Price: $29.99 • SKU: KH-204</div>
            </div>
            <span class="status review">Needs review</span>
          </div>
          <div class="queue-row">
            <div>
              <div class="queue-title">Smart Organizer Basket</div>
              <div class="queue-meta">Source: Supplier B • Price: $26.90 • SKU: OG-210</div>
            </div>
            <span class="status live">Ready to submit</span>
          </div>
          <div class="queue-row">
            <div>
              <div class="queue-title">LED Mobility Lamp</div>
              <div class="queue-meta">Source: Supplier C • Price: $39.99 • SKU: AP-900</div>
            </div>
            <span class="status error">Amazon rejected — click to see why</span>
          </div>
        </div>
      </section>
    </section>
  </section>`;
}

function renderAddOneProductForm() {
  return `<div class="source-form">
    <div class="form-grid">
      <div class="form-row">
        <div class="form-field">
          <label>Product page link <span class="required-mark">*</span></label>
          <input type="text" id="sourceLink" value="http://127.0.0.1:8000/static/source-pages/kh-204.html" placeholder="https://supplier-site.com/product/123" />
          <span class="field-hint">Paste the product page URL from your supplier, eBay, AliExpress, or competitor site. We'll fetch the title and main image.</span>
        </div>
        <div class="form-field">
          <label>Competitor ASIN or link (optional)</label>
          <input type="text" id="competitorLink" value="B09XYZ1234" placeholder="B0XXXXXXXX or Amazon URL" />
          <span class="field-hint">Amazon ASIN or competitor product URL to compare prices and stock</span>
        </div>
      </div>
      <div class="form-row">
        <div class="form-field">
          <label>Product name</label>
          <input type="text" id="productName" value="Portable Kitchen Storage Set" />
          <span class="field-hint">We'll auto-fill this from the source link if found</span>
        </div>
        <div class="form-field">
          <label>Brand</label>
          <input type="text" id="brand" value="Nexa Home" />
          <span class="field-hint">We'll auto-fill this from the source link if found</span>
        </div>
      </div>
      <div class="form-row">
        <div class="form-field">
          <label>Your cost per unit</label>
          <input type="number" id="cost" value="11.50" step="0.01" min="0" />
          <span class="field-hint">What you pay the supplier for each unit</span>
        </div>
        <div class="form-field">
          <label>Your selling price on Amazon</label>
          <input type="number" id="sellPrice" value="29.99" step="0.01" min="0" />
          <span class="field-hint">The price customers will see on Amazon</span>
        </div>
        <div class="form-field">
          <label>Handling time</label>
          <select id="handlingDays"><option>2-3 days</option><option>4-5 days</option></select>
          <span class="field-hint">How many business days before you ship after an order</span>
        </div>
      </div>
      <div class="form-row">
        <div class="form-field">
          <label>Barcode (EAN / UPC)</label>
          <input type="text" id="barcode" value="654123987321" />
          <span class="field-hint">Product barcode for Amazon listing (EAN, UPC, or ISBN)</span>
        </div>
        <div class="form-field">
          <label>Pricing method</label>
          <select id="autoPrice"><option>Auto-price (use my profit rules)</option><option>Manual (I set the price)</option></select>
          <span class="field-hint">Auto-price calculates a price based on your cost and profit margin</span>
        </div>
      </div>
      <div class="form-actions">
        <button class="btn" id="addSourceProduct" disabled title="Fetch details & add to queue">Add to Queue</button>
        <button class="btn btn-secondary" id="saveDraft">Save as draft</button>
      </div>
      <div id="sourceFetchResult" class="fetch-result"></div>
    </div>`;
}

function renderImportForm() {
  return `<div class="bulk-import-zone">
    <div class="form-grid">
      <div class="form-field" style="grid-column: 1/-1;">
        <p style="font-size:12px; color:var(--muted); margin-bottom:12px;">Upload a CSV or Excel file with exact columns: <strong>Source link</strong>, <strong>Competitor ASIN/link</strong>, <strong>Product name</strong>, <strong>Brand</strong>, <strong>Cost</strong>, <strong>Sell price</strong>, <strong>Handling days</strong>, <strong>Barcode</strong>. Required: Source link, Cost.</p>
      </div>
      <div class="form-field" style="grid-column: 1/-1;">
        <div style="display:flex; gap:8px; align-items:center; flex-wrap:wrap; margin-bottom:12px;">
          <input type="file" id="bulkImportFile" accept=".csv,.xlsx,.xls" />
          <button class="btn small-padded" id="runBulkImport" disabled>Import rows</button>
          <a class="btn btn-secondary small-padded" id="downloadTemplate" href="/api/sourcing/import/template" download>Download template</a>
        </div>
      </div>
      <div class="form-field" style="grid-column: 1/-1;">
        <div id="bulkImportProgress" class="fetch-result"></div>
        <div id="bulkImportSummary" class="fetch-result"></div>
      </div>
    </div>`;
}

function renderEbayForm() {
  return `<div class="ebay-fetch-zone">
    <div class="form-grid">
      <div class="form-field" style="grid-column: 1/-1;">
        <p style="font-size:12px; color:var(--muted); margin-bottom:12px;">Paste an eBay seller's store link (e.g., <code>https://www.ebay.com/str/storename</code>) or just their username. We'll fetch all their listings, auto-skip compliance-risk items, and let you pick which to add to your queue.</p>
      </div>
      <div class="form-field" style="grid-column: 1/-1;">
        <label>eBay seller link or username</label>
        <input type="text" id="ebaySellerInput" placeholder="https://www.ebay.com/str/storename or just storename" />
        <span class="field-hint">Store link, profile link, or username</span>
      </div>
      <div class="form-field" style="grid-column: 1/-1;">
        <div class="form-actions">
          <button class="btn" id="runEbayFetch" disabled>Fetch all products</button>
          <button class="btn btn-secondary small-padded" id="cancelEbayFetch" style="display:none;">Cancel</button>
        </div>
      </div>
      <div class="form-field" style="grid-column: 1/-1;">
        <div id="ebayFetchProgress" class="fetch-result"></div>
        <div id="ebayFetchResults" class="fetch-result" style="display:none;"></div>
      </div>
    </div>`;
}

function renderListingsPage() {
  return `<section class="page-wrap">
    <section class="page-heading">
      <div>
        <span class="eyebrow">Catalog / Listings</span>
        <h1>All Listings</h1>
      </div>
      <p class="page-description">View and manage every product listing — drafts, live on Amazon, and ones needing your attention.</p>
      <div class="page-actions">
        <button class="btn small-padded" data-section="sourcing">Add new product</button>
        <button class="btn btn-secondary small-padded">Filter listings</button>
      </div>
    </section>
    <section class="tabs" role="tablist" aria-label="Listing status">
      <button class="tab active" data-list-tab="all" role="tab" aria-selected="true">All listings</button>
      <button class="tab" data-list-tab="drafts" role="tab" aria-selected="false">Drafts (not submitted)</button>
      <button class="tab" data-list-tab="live" role="tab" aria-selected="false">Live on Amazon</button>
    </section>
    <section class="panel">
      <table class="table listing-table">
        <thead>
          <tr>
            <th>Image</th><th>Title</th><th>ASIN / SKU / Barcode</th><th>Brand</th><th>Condition</th><th>Handling time</th><th>Your cost</th><th>Amazon fees</th><th>Est. profit</th><th>Status</th>
          </tr>
        </thead>
        <tbody>
          <tr data-list-row="live">
            <td><span class="thumbnail">IMG</span></td>
            <td>Kitchen Organization Box</td>
            <td>SKU KH-204<br>ASIN B09ABC1234<br>EAN 654123987321</td>
            <td>Nexa Home</td>
            <td>New</td>
            <td>2-3 days</td>
            <td>$11.50</td>
            <td>$5.20</td>
            <td>$8.30</td>
            <td><span class="status live">Live on Amazon</span></td>
          </tr>
          <tr data-list-row="draft">
            <td><span class="thumbnail">IMG</span></td>
            <td>Eco Cleaning Set</td>
            <td>SKU EC-440<br>Not published yet<br>EAN 444001333</td>
            <td>CleanPro</td>
            <td>New</td>
            <td>4-5 days</td>
            <td>$12.40</td>
            <td>$4.90</td>
            <td>$7.10</td>
            <td><span class="status draft">Draft — not submitted</span></td>
          </tr>
          <tr data-list-row="live">
            <td><span class="thumbnail">IMG</span></td>
            <td>LED Mobility Lamp</td>
            <td>SKU AP-900<br>ASIN B09LMN7777<br>EAN 5549002812</td>
            <td>BrightNest</td>
            <td>New</td>
            <td>1-2 days</td>
            <td>$18.90</td>
            <td>$7.00</td>
            <td>$11.50</td>
            <td><span class="status review">Needs your review</span></td>
          </tr>
        </tbody>
      </table>
      <div class="empty-state" style="display: none; text-align: center; padding: 40px; color: var(--muted);">
        <div style="font-size: 48px; margin-bottom: 16px;">📦</div>
        <h3 style="margin: 0 0 8px;">No listings yet</h3>
        <p style="margin: 0 0 16px;">You haven't added any products yet. Start by adding your first product.</p>
        <button class="btn" data-section="sourcing">Go to Add New Product</button>
      </div>
    </section>
  </section>`;
}

function renderDetailPage() {
  return `<section class="page-wrap">
    <section class="page-heading">
      <div>
        <span class="eyebrow">Catalog / Listings</span>
        <h1>Listing Detail</h1>
      </div>
      <p class="page-description">Review and complete all product details before submitting to Amazon. Use the tabs below to check each section.</p>
      <div class="page-actions">
        <button class="btn small-padded" id="previewListing" title="Preview full listing">Preview</button>
        <button class="btn btn-secondary small-padded" id="autoFix" title="Auto-fill missing fields">Auto-fill</button>
        <button class="btn small-padded" id="generateAiText" title="Generate AI content">Generate AI</button>
      </div>
    </section>
    <section class="detail-layout">
      <aside class="detail-sidebar panel">
        <div class="listing-image big-image">Product<br>Image</div>
        <div class="detail-meta">
          <div class="detail-title">Portable Kitchen Storage Set</div>
          <div class="detail-id">ASIN: B09ABC1234 • SKU: KH-204 • EAN: 654123987321</div>
          <div class="compact-status">
            <span class="status live">Ready to submit</span>
            <span class="status review">Claim Risk: Low</span>
          </div>
        </div>
        <div class="detail-actions">
          <button class="btn small-padded" id="openImageStudio" title="Open Image Studio">Image Studio</button>
          <button class="btn btn-secondary small-padded" id="viewRawData" title="View raw data">Raw Data</button>
        </div>
      </aside>
      <section class="panel detail-main">
        <p style="font-size:12px; color:var(--muted); margin-bottom:12px;">Step through each tab to make sure everything is complete. Green checks = good, Orange = needs review, Red = must fix.</p>
        <div class="tabs small-tabs" role="tablist" aria-label="Listing sections">
          <button class="tab active" data-detail-tab="details" role="tab" aria-selected="true">Product Details</button>
          <button class="tab" data-detail-tab="images" role="tab" aria-selected="false">Images</button>
          <button class="tab" data-detail-tab="offer" role="tab" aria-selected="false">Offer & Pricing</button>
          <button class="tab" data-detail-tab="compliance" role="tab" aria-selected="false">Safety & Compliance</button>
        </div>
        <div class="detail-content">
          <div class="detail-section">
            <div class="detail-row"><span class="detail-label">Title</span><span class="detail-value" id="detailTitleText">Portable Kitchen Storage Set</span></div>
            <div class="detail-row"><span class="detail-label">Brand</span><span class="detail-value">Nexa Home</span></div>
            <div class="detail-row"><span class="detail-label">Condition</span><span class="detail-value">New</span></div>
            <div class="detail-row"><span class="detail-label">Bullet points</span><span class="detail-value" id="detailBulletPoints">Organize kitchen spaces • Durable • Compact</span></div>
            <div class="detail-row"><span class="detail-label">Description</span><span class="detail-value" id="detailDescription">Designed for one clean, organized kitchen experience.</span></div>
            <div class="detail-row"><span class="detail-label">Backend search keywords</span><span class="detail-value" id="detailKeywords">portable kitchen storage set, nexa home, home kitchen</span></div>
          </div>
          <div class="compliance-panel">
            <h4>Compliance checks</h4>
            <div class="check-list">
              <div class="check-row"><span class="check-status ok">✓</span><span>Restricted category check: passed</span></div>
              <div class="check-row"><span class="check-status warn">!</span><span>Claim risk: no medical or safety claims detected</span></div>
              <div class="check-row"><span class="check-status warn">!</span><span>Required documents: manufacturer invoices needed</span></div>
            </div>
            <p style="font-size:12px; color:var(--muted); margin-top:12px;">Orange items need your review before submitting. Red items would block submission.</p>
          </div>
          <div class="ai-panel">
            <div class="ai-panel-title">AI Content Generation</div>
            <p style="font-size:12px; color:var(--muted); margin-bottom:12px;">Click "Generate AI content" above to create a title, bullets, description, and keywords based on your product info.</p>
            <div class="ai-preview-grid">
              <div class="form-field">
                <label>Generated title</label>
                <textarea id="aiTitle" class="ai-textarea title-area">Nexa Home Portable Kitchen Storage Set</textarea>
                <span class="field-hint">Max 200 characters for Amazon</span>
              </div>
              <div class="form-field">
                <label>Bullet points</label>
                <textarea id="aiBullets" class="ai-textarea">Made for organized home and kitchen spaces\nCompact, durable and easy to store\nDesigned to keep everyday items neat and accessible</textarea>
                <span class="field-hint">One per line, max 5 bullets</span>
              </div>
              <div class="form-field">
                <label>Full description</label>
                <textarea id="aiDescription" class="ai-textarea desc-area">The Portable Kitchen Storage Set from Nexa Home is built for organized shopping and storage routines in the Home & Kitchen category.</textarea>
                <span class="field-hint">HTML allowed, max 2000 characters</span>
              </div>
              <div class="form-field">
                <label>Backend keywords</label>
                <textarea id="aiKeywords" class="ai-textarea">portable kitchen storage set, nexa home, home kitchen, kitchen storage, home organization</textarea>
                <span class="field-hint">Comma-separated, max 250 bytes total</span>
              </div>
            </div>
            <div class="form-actions">
              <button class="btn small-padded" id="saveAiText" title="Save AI content to this listing">Save AI Content</button>
            </div>
          </div>

          <section class="detail-preview-panel" id="detailPreviewPanel" style="display: none;">
            <div class="panel-title">Review before submitting</div>
            <p style="font-size:12px; color:var(--muted); margin-bottom:12px;">Auto-fill pulled data from your source link and AI. Review each column — you'll need to confirm the items in the right column yourself.</p>
            <div class="preview-progress-wrap">
              <div class="preview-progress" id="autoFixProgress">Ready to fill</div>
              <div class="preview-summary" id="autoFixSummary">Click "Auto-fill missing fields" to populate from source link and AI.</div>
            </div>
            <div class="preview-grid preview-grid-three">
              <div class="preview-column">
                <div class="preview-column-title">✓ Filled from source link</div>
                <ul class="preview-list" id="sourceList">
                  <li>Title: copied from source link</li>
                  <li>Bullet point 1: copied from source link</li>
                </ul>
              </div>
              <div class="preview-column">
                <div class="preview-column-title">🤖 Filled by AI (review carefully)</div>
                <ul class="preview-list" id="aiList">
                  <li>Bullet point 3: generated by AI — no source data available</li>
                </ul>
              </div>
              <div class="preview-column">
                <div class="preview-column-title danger-title">⚠ Still needs your attention</div>
                <ul class="preview-list" id="manualList">
                  <li>Confirm the supplier image meets Amazon's image requirements.</li>
                </ul>
              </div>
            </div>
            <div class="preview-action-row">
              <button class="btn small-padded" id="continueSubmit">Submit to Amazon</button>
              <button class="btn btn-secondary small-padded" id="closePreview">Close preview</button>
            </div>
          </section>
        </div>
      </section>
    </section>
  </section>`;
}

function renderAnalyticsPage() {
  return `<section class="page-wrap">
    <section class="page-heading">
      <div>
        <span class="eyebrow">Catalog / Listings</span>
        <h1>Catalog Analytics</h1>
      </div>
      <p class="page-description">See which products drive revenue, which are losing money, and what needs attention.</p>
      <div class="page-actions">
        <select class="mini-select"><option>All time</option><option>Last month</option><option>Last 3 months</option><option>Last year</option></select>
      </div>
    </section>
    <section class="dashboard-grid analytics-grid">
      <div class="kpi-card">
        <div class="label">Revenue from top 5 products</div>
        <div class="value">31%</div>
        <div class="trend positive">High concentration</div>
        <div class="kpi-hint">A small number of products make most of your revenue — consider diversifying</div>
      </div>
      <div class="kpi-card">
        <div class="label">Best performer</div>
        <div class="value">Kitchen Set</div>
        <div class="trend positive">$4,860 revenue</div>
        <div class="kpi-hint">Highest revenue product this period</div>
      </div>
      <div class="kpi-card">
        <div class="label">Products with zero sales (90+ days)</div>
        <div class="value">8</div>
        <div class="trend warning">Dead stock</div>
        <div class="kpi-hint">These listings are live but haven't sold in 3+ months — consider repricing or removing</div>
      </div>
    </section>
    <section class="panel mt-20">
      <div class="panel-title">Product performance (ranked by revenue)</div>
      <p style="font-size:12px; color:var(--muted); margin-bottom:12px;">ROI = Return on Investment (profit ÷ cost). Higher is better.</p>
      <table class="table">
        <thead>
          <tr><th>Product</th><th>Revenue</th><th>Units sold</th><th>Profit</th><th>ROI</th><th>Status</th></tr>
        </thead>
        <tbody>
          <tr><td>Kitchen Organization Box</td><td>$4,860</td><td>314</td><td>$1,940</td><td>39%</td><td><span class="status live">Live on Amazon</span></td></tr>
          <tr><td>LED Mobility Lamp</td><td>$3,416</td><td>205</td><td>$1,211</td><td>34%</td><td><span class="status review">Needs your review</span></td></tr>
          <tr><td>Eco Cleaning Set</td><td>$1,842</td><td>120</td><td>$745</td><td>26%</td><td><span class="status draft">Draft — not submitted</span></td></tr>
        </tbody>
      </table>
    </section>
  </section>`;
}

function renderCategoryPage() {
  return `<section class="page-wrap">
    <section class="page-heading">
      <div>
        <span class="eyebrow">Catalog / Listings</span>
        <h1>Category Explorer</h1>
      </div>
      <p class="page-description">Find the right Amazon category for your product. The correct category affects fees, visibility, and what info Amazon requires.</p>
      <button class="btn btn-secondary small-padded">Browse full category tree</button>
    </section>
    <section class="panel-grid two">
      <section class="panel">
        <div class="panel-title">Amazon Category Tree</div>
        <p style="font-size:12px; color:var(--muted); margin-bottom:12px;">Click a category to see its selling requirements, fees, and required product attributes.</p>
        <div class="tree">
          <div class="tree-item"><span class="tree-icon">▾</span> Home & Kitchen</div>
          <div class="tree-indent">
            <div class="tree-item"><span class="tree-icon">▾</span> Kitchen Storage</div>
            <div class="tree-indent">
              <div class="tree-item"><span class="tree-icon">•</span> Organization Bins</div>
              <div class="tree-item"><span class="tree-icon">•</span> Food Storage</div>
            </div>
          </div>
          <div class="tree-item"><span class="tree-icon">▾</span> Cleaning Supplies</div>
        </div>
      </section>
      <section class="panel">
        <div class="panel-title">Your listings by category</div>
        <p style="font-size:12px; color:var(--muted); margin-bottom:12px;">How many active listings you have in each top-level category.</p>
        <div class="category-list">
          <div class="category-row"><span>Home & Kitchen</span><b>32 listings</b></div>
          <div class="category-row"><span>Cleaning Supplies</span><b>17 listings</b></div>
          <div class="category-row"><span>Lighting</span><b>9 listings</b></div>
          <div class="category-row"><span>Storage Solutions</span><b>12 listings</b></div>
        </div>
      </section>
    </section>
  </section>`;
}

function renderImageStudioPage() {
  return `<section class="page-wrap">
    <section class="page-heading">
      <div>
        <span class="eyebrow">AI Content Generation</span>
        <h1>AI Image Studio</h1>
      </div>
      <p class="page-description">Create product images with AI. Choose a mode, set your preferences, and generate images that meet Amazon's requirements.</p>
      <div class="page-actions">
        <button class="btn small-padded" id="generateImageCreative">Generate</button>
        <button class="btn btn-secondary small-padded" id="downloadImage">Download</button>
      </div>
    </section>
    <section class="image-studio-grid">
      <section class="panel image-preview-panel">
        <div class="panel-title">Preview</div>
        <div class="image-preview big-image-studio">Product<br>Image</div>
        <div class="fidelity-row">
          <label class="label-line">Fidelity</label>
          <input type="range" min="1" max="100" value="82" class="slider" id="fidelitySlider" />
          <span class="slider-value" id="fidelityValue">82%</span>
        </div>
        <p style="font-size:11px; color:var(--muted); margin-top:4px;">Higher = closer to your actual product. Lower = more creative freedom.</p>
        <div class="form-field standing">
          <label>Standing instructions</label>
          <textarea id="standingInstructions">always white background</textarea>
          <span class="field-hint">Rules the AI always follows (e.g., "always white background", "no text overlays")</span>
        </div>
      </section>
      <section class="panel">
        <div class="panel-title">Generate image</div>
        <div class="tabs small-tabs">
          <button class="tab active" data-image-tab="creative" role="tab" aria-selected="true">Creative concepts</button>
          <button class="tab" data-image-tab="main" role="tab" aria-selected="false">Main image (white background)</button>
          <button class="tab" data-image-tab="secondary" role="tab" aria-selected="false">Secondary images (lifestyle, infographics)</button>
          <button class="tab" data-image-tab="aplus" role="tab" aria-selected="false">A+ Content modules</button>
        </div>
        <div class="studio-form">
          <div class="form-grid">
            <div class="form-row">
              <div class="form-field">
                <label>How close to real product</label>
                <select id="imageFidelity">
                  <option>Preserve product exactly</option>
                  <option>Balanced</option>
                  <option>Creative interpretation</option>
                </select>
                <span class="field-hint">"Preserve" keeps your product exactly as-is. "Creative" lets AI redesign.</span>
              </div>
              <div class="form-field">
                <label>Which image slot</label>
                <select id="imageSlot">
                  <option>Main (white background)</option>
                  <option>Image 1 (lifestyle)</option>
                  <option>Image 2 (detail shot)</option>
                  <option>Image 3 (in use)</option>
                  <option>Image 4 (comparison)</option>
                  <option>A+ Image 1 (module)</option>
                </select>
                <span class="field-hint">Main image must be on pure white background per Amazon rules</span>
              </div>
            </div>
            <div class="form-row">
              <div class="form-field">
                <label>Secondary image approach</label>
                <div class="segmented">
                  <button class="btn small-padded active" data-sec-method="suggest">Let AI suggest concepts</button>
                  <button class="btn btn-secondary small-padded" data-sec-method="manual">Pick exact modules</button>
                </div>
                <span class="field-hint">"Suggest" = AI proposes ideas. "Manual" = you choose specific templates.</span>
              </div>
            </div>
            <div class="form-row">
              <div class="form-field">
                <label>Template for secondary/A+ images</label>
                <select id="imageModule">
                  <option>Feature highlight</option>
                  <option>Infographic</option>
                  <option>Usage comparison</option>
                  <option>Dimensions/scale</option>
                </select>
                <span class="field-hint">Choose a layout template for lifestyle or A+ images</span>
              </div>
            </div>
            <div class="form-actions">
              <button class="btn small-padded" id="generateImage">Generate image</button>
              <button class="btn btn-secondary small-padded" id="assignImage">Assign to listing slot</button>
            </div>
          </div>
        </div>
      </section>
    </section>
    <section class="panel mt-20">
      <div class="panel-title">Your generated images</div>
      <p style="font-size:12px; color:var(--muted); margin-bottom:12px;">Images you've created in this session. Click "Assign" to add one to a listing slot.</p>
      <table class="table">
        <thead><tr><th>Image</th><th>Slot</th><th>Mode</th><th>Fidelity</th><th>Source</th><th>Action</th></tr></thead>
        <tbody>
          <tr><td><span class="thumbnail">IMG</span></td><td>Main</td><td>Creative</td><td>82%</td><td>AI generated</td><td><button class="btn btn-secondary small-padded">Assign</button></td></tr>
          <tr><td><span class="thumbnail">IMG</span></td><td>Image 1</td><td>Secondary</td><td>78%</td><td>AI generated</td><td><button class="btn btn-secondary small-padded">Assign</button></td></tr>
        </tbody>
      </table>
    </section>
  </section>`;
}

function renderImageLibraryPage() {
  return `<section class="page-wrap">
    <section class="page-heading">
      <div>
        <span class="eyebrow">AI Content Generation</span>
        <h1>Image Library</h1>
      </div>
      <p class="page-description">All your generated and uploaded product images in one place. Filter by listing, slot, or status to find what you need.</p>
      <div class="page-actions">
        <button class="btn small-padded" data-section="imageStudio">Create new images</button>
        <button class="btn btn-secondary small-padded">Upload image set</button>
      </div>
    </section>
    <section class="image-library-grid">
      <section class="panel image-library-list">
        <div class="panel-title">Your image assets</div>
        <p style="font-size:12px; color:var(--muted); margin-bottom:12px;">Active = assigned to a live listing. Draft = saved but not assigned. Queued = waiting to be processed.</p>
        <div class="library-list">
          <div class="library-row">
            <span class="thumbnail library-thumb">IMG</span>
            <div class="library-copy">
              <strong>KH-204-main-creative.png</strong>
              <span class="muted">Main image • Creative • 2000x2000</span>
            </div>
            <span class="status live">Active</span>
          </div>
          <div class="library-row">
            <span class="thumbnail library-thumb">IMG</span>
            <div class="library-copy">
              <strong>KH-204-image1-secondary.png</strong>
              <span class="muted">Image 1 • Secondary • 1200x1200</span>
            </div>
            <span class="status review">Draft</span>
          </div>
          <div class="library-row">
            <span class="thumbnail library-thumb">IMG</span>
            <div class="library-copy">
              <strong>KH-204-aplus-feature.png</strong>
              <span class="muted">A+ • Feature module • 1200x1200</span>
            </div>
            <span class="status draft">Queued</span>
          </div>
        </div>
      </section>
      <section class="panel">
        <div class="panel-title">Filter & actions</div>
        <div class="library-controls">
          <div class="form-field">
            <label>Which listing</label>
            <select>
              <option>Current listing set</option>
              <option>All generated images</option>
              <option>Marketplace-ready</option>
            </select>
          </div>
          <div class="form-field">
            <label>Image slot</label>
            <select>
              <option>All slots</option>
              <option>Main (white background)</option>
              <option>Image 1 (lifestyle)</option>
              <option>Image 2 (detail)</option>
              <option>A+ module</option>
            </select>
          </div>
          <div class="form-field">
            <label>Status</label>
            <select>
              <option>All statuses</option>
              <option>Active (on live listing)</option>
              <option>Draft (saved, not assigned)</option>
              <option>Queued (processing)</option>
            </select>
          </div>
          <div class="form-actions">
            <button class="btn">Apply filters</button>
            <button class="btn btn-secondary">Download as ZIP</button>
          </div>
        </div>
      </section>
    </section>
  </section>`;
}

function renderImageReferencesPage() {
  return `<section class="page-wrap">
    <section class="page-heading">
      <div>
        <span class="eyebrow">AI Content Generation</span>
        <h1>Image References</h1>
      </div>
      <p class="page-description">Save reference images (from suppliers, competitors, or brand guidelines) to guide AI image generation. These tell the AI what style, angle, and composition you want.</p>
      <div class="page-actions">
        <button class="btn small-padded">Add reference image</button>
        <button class="btn btn-secondary small-padded">Sync from brand package</button>
      </div>
    </section>
    <section class="panel-grid two">
      <section class="panel">
        <div class="panel-title">Saved reference images</div>
        <p style="font-size:12px; color:var(--muted); margin-bottom:12px;">Matched = linked to a product. Review = needs your check. Queued = waiting to be processed.</p>
        <div class="reference-list">
          <div class="reference-row">
            <span class="reference-thumb">IMG</span>
            <div>
              <div class="queue-title">Kitchen organizer concept</div>
              <div class="queue-meta">Source: supplier product photo • White background</div>
            </div>
            <span class="status live">Matched to product</span>
          </div>
          <div class="reference-row">
            <span class="reference-thumb">IMG</span>
            <div>
              <div class="queue-title">Storage bin modular layout</div>
              <div class="queue-meta">Source: A+ module reference • Front angle</div>
            </div>
            <span class="status review">Needs review</span>
          </div>
          <div class="reference-row">
            <span class="reference-thumb">IMG</span>
            <div>
              <div class="queue-title">Food organization lifestyle</div>
              <div class="queue-meta">Source: brand packshot • Pastel kitchen</div>
            </div>
            <span class="status draft">Queued</span>
          </div>
        </div>
      </section>
      <section class="panel">
        <div class="panel-title">Reference style guide</div>
        <p style="font-size:12px; color:var(--muted); margin-bottom:12px;">Set the visual style for AI-generated images. The AI will try to match this look.</p>
        <div class="studio-form">
          <div class="form-grid">
            <div class="form-field">
              <label>Visual style</label>
              <select>
                <option>Clean white background</option>
                <option>Bright lifestyle kitchen</option>
                <option>Infographic feature callout</option>
              </select>
              <span class="field-hint">The overall look for generated images</span>
            </div>
            <div class="form-field">
              <label>Brand color palette</label>
              <select>
                <option>Minimal white / sage</option>
                <option>Warm neutral</option>
                <option>Pure product (no styling)</option>
              </select>
              <span class="field-hint">Colors the AI should use in backgrounds and accents</span>
            </div>
            <div class="form-field">
              <label>Notes for AI</label>
              <textarea>Use clean front-angle composition with visible storage depth and no complex background texture.</textarea>
              <span class="field-hint">Specific instructions for the AI (angles, lighting, composition, what to avoid)</span>
            </div>
            <div class="form-actions">
              <button class="btn">Save style guide</button>
              <button class="btn btn-secondary">Generate test image</button>
            </div>
          </div>
        </div>
      </section>
    </section>
  </section>`;
}

function renderRepricerPage() {
  const products = state.repricerData?.products || [
    {
      id: 'KH-204', name: 'Portable Kitchen Storage Set', brand: 'Nexa Home', current_sell_price: 29.99,
      sources: [
        {id: 'source-kh-1', label: 'Supplier A', link: 'https://supplier-a.example/source/kh-204', current_price: 11.50, stock_status: 'In Stock', last_checked: '2026-09-13T08:30:00Z'},
        {id: 'source-kh-2', label: 'Supplier B', link: 'https://supplier-b.example/source/kh-204', current_price: 10.50, stock_status: 'In Stock', last_checked: '2026-09-13T08:35:00Z'},
        {id: 'source-kh-3', label: 'Competitor X', link: 'https://competitor-x.example/product/kh-204', current_price: 12.20, stock_status: 'Out of Stock', last_checked: '2026-09-13T08:38:00Z'},
      ],
      active_source_id: 'source-kh-2', active_source_price: 10.50, status: 'Auto-priced', edge_message: 'Cheapest in-stock source is active.'
    }
  ];

  const defaultRule = state.repricerData?.default_rule || {type: 'percentage', minimum_profit_percent: 20, minimum_profit_fixed: 5, fixed_currency: 'USD', active: 'percentage'};

  const productRows = products.map(product => {
    const sources = product.sources.map(source => {
      const isActive = product.active_source_id === source.id;
      const outClass = source.stock_status === 'Out of Stock' ? 'out' : '';
      const stockClass = source.stock_status === 'In Stock' ? 'live' : 'error';
      const stockText = source.stock_status;
      return `<div class="source-card ${isActive ? 'active-source' : ''} ${outClass}">
        <div class="source-card-top">
          <span class="source-label">${source.label}</span>
          <span class="status ${stockClass}">${stockText}</span>
        </div>
        <div class="source-price">$${source.current_price}</div>
        <div class="source-link"><a href="${source.link}" target="_blank">${source.link}</a></div>
        <div class="source-meta">Last checked ${source.last_checked}</div>
      </div>`;
    }).join('');

    const productStatus = product.status || 'Auto-priced';
    const statusType = product.status === 'No source available' ? 'error' : 'live';
    const activeSource = product.active_source_id ? product.sources.find(s => s.id === product.active_source_id) : null;

    return `<section class="panel repricer-product">
      <div class="panel-title">${product.name}</div>
      <p style="font-size:12px; color:var(--muted); margin-bottom:12px;">This product's price is auto-adjusted based on your cheapest in-stock supplier. Current rule: ${defaultRule.type === 'percentage' ? 'minimum ' + defaultRule.minimum_profit_percent + '% profit' : '$' + defaultRule.minimum_profit_fixed + ' fixed profit'}.</p>
      <div class="repricer-product-head">
        <div><span class="detail-label">Status</span><span class="status ${statusType}">${productStatus}</span></div>
        <div><span class="detail-label">Cheapest in-stock supplier</span><span class="source-active-label">${activeSource ? `${activeSource.label} — $${activeSource.current_price}` : 'None available'}</span></div>
        <div><span class="detail-label">Current Amazon price</span><span class="detail-value">$${product.current_sell_price}</span></div>
      </div>
      <div class="repricer-sources">${sources}</div>
      <div class="repricer-edge">${product.edge_message || product.status}</div>
      <div class="form-actions repricer-actions">
        <button class="btn small-padded source-add">Add supplier source</button>
        <button class="btn btn-secondary small-padded source-edit">Edit sources</button>
        <button class="btn btn-secondary small-padded source-remove">Remove selected</button>
      </div>
    </section>`;
  }).join('');

  return `<section class="page-wrap">
    <section class="page-heading">
      <div>
        <span class="eyebrow">Catalog / Pricing</span>
        <h1>Repricer</h1>
      </div>
      <p class="page-description">Automatically adjust your Amazon prices when supplier costs change. The system watches your supplier links and keeps your profit margin intact.</p>
      <div class="page-actions">
        <button class="btn small-padded" id="repricerRefresh" title="Check supplier prices now">Check Prices</button>
        <button class="btn btn-secondary small-padded" id="repricerSaveRule" title="Save profit rule">Save Rule</button>
      </div>
    </section>
    <section class="panel rule-panel">
      <div class="panel-title">Your profit rule (applies to all products)</div>
      <p style="font-size:12px; color:var(--muted); margin-bottom:16px;">This rule sets the minimum profit you want on every sale. The repricer finds your cheapest in-stock supplier and sets your Amazon price to maintain this margin.</p>
      <div class="repricer-rule-grid">
        <div class="form-field">
          <label>Profit rule type</label>
          <select id="repricerRuleType">
            <option value="percentage" ${defaultRule.type === 'percentage' ? 'selected' : ''}>Percentage (e.g., "keep 20% profit margin")</option>
            <option value="fixed" ${defaultRule.type === 'fixed' ? 'selected' : ''}>Fixed amount (e.g., "keep $5 profit per unit")</option>
          </select>
          <span class="field-hint">Percentage scales with price. Fixed stays the same regardless of price.</span>
        </div>
        <div class="form-field">
          <label>Minimum profit %</label>
          <input type="number" id="repricerPercent" value="${defaultRule.minimum_profit_percent}" min="0" step="0.1" />
          <span class="field-hint">Used when rule type is "Percentage". Example: 20% on a $10 cost = $12 minimum price.</span>
        </div>
        <div class="form-field">
          <label>Fixed profit amount</label>
          <input type="number" id="repricerFixed" value="${defaultRule.minimum_profit_fixed}" min="0" step="0.01" />
          <span class="field-hint">Used when rule type is "Fixed amount". Example: $5 on a $10 cost = $15 minimum price.</span>
        </div>
        <div class="form-field">
          <label>Currency</label>
          <select id="repricerCurrency">
            <option value="USD" ${defaultRule.fixed_currency === 'USD' ? 'selected' : ''}>USD ($)</option>
            <option value="EUR" ${defaultRule.fixed_currency === 'EUR' ? 'selected' : ''}>EUR (€)</option>
            <option value="GBP" ${defaultRule.fixed_currency === 'GBP' ? 'selected' : ''}>GBP (£)</option>
            <option value="CAD" ${defaultRule.fixed_currency === 'CAD' ? 'selected' : ''}>CAD ($)</option>
          </select>
        </div>
      </div>
    </section>
    <section class="repricer-products">${productRows}</section>
  </section>`;
}

function renderAmazonIntegrationPage() {
  return `<section class="page-wrap">
    <section class="page-heading">
      <div>
        <span class="eyebrow">Amazon / Integration</span>
        <h1>Amazon SP-API Integration</h1>
      </div>
      <p class="page-description">Connect your Amazon Seller Central account via SP-API to publish listings, sync orders, and compare live data. You need a Professional Seller account and a registered Developer App.</p>
      <div class="page-actions">
        <button class="btn btn-secondary small-padded" id="checkCredentialsStatus">Check Connection Status</button>
      </div>
    </section>

    <section class="panel-grid two">
      <section class="panel">
        <div class="panel-title">SP-API Credentials</div>
        <div id="credentialsStatus" style="margin-bottom:16px;"></div>
        <div class="setup-guide" id="setupGuide" style="display:none;">
          <h4>How to get SP-API credentials:</h4>
          <ol style="font-size:13px; line-height:1.8; color:var(--muted); padding-left:20px;">
            <li>Go to <strong>Amazon Seller Central > Apps & Services > Develop Apps</strong></li>
            <li>Click <strong>"Register a new application"</strong></li>
            <li>Fill in: App name (e.g., "Sellrix"), description, redirect URI (your app URL + <code>/auth/callback</code>)</li>
            <li>Add <strong>Selling Partner API roles</strong>: Orders, Listings Items, Catalog Items, Reports, Product Fees</li>
            <li>Save to get your <strong>Client ID</strong> and <strong>Client Secret</strong></li>
            <li>Click <strong>"Authorize"</strong> next to your app to get the <strong>Refresh Token</strong></li>
            <li>Enter all three values below and click "Save Credentials"</li>
          </ol>
          <div class="form-actions" style="margin-top:16px;">
            <button class="btn small-padded" id="showCredentialsForm" title="I have my credentials — enter them now">Enter Credentials</button>
          </div>
        </div>
        <form id="credentialsForm" class="credentials-form" style="display:none;">
          <div class="form-grid">
            <div class="form-field">
              <label>Marketplace</label>
              <select id="credMarketplace">
                <option value="ATVPDKIKX0DER">Amazon.com (US)</option>
                <option value="A2EUQ1WTGCTBG2">Amazon.ca (Canada)</option>
                <option value="A1AM78C64UM0Y8">Amazon.com.mx (Mexico)</option>
                <option value="A1PA6795UKMFR9">Amazon.de (Germany)</option>
                <option value="A1RKKUPIHCS9HS">Amazon.es (Spain)</option>
                <option value="A13V1IB3VIYZZH">Amazon.fr (France)</option>
                <option value="APJ6JRA9NG5V4">Amazon.it (Italy)</option>
                <option value="A1F83G8C2ARO7P">Amazon.co.uk (UK)</option>
              </select>
            </div>
            <div class="form-field">
              <label>Region</label>
              <select id="credRegion">
                <option value="na">North America</option>
                <option value="eu">Europe</option>
                <option value="fe">Far East</option>
              </select>
            </div>
            <div class="form-field" style="grid-column: 1/-1;">
              <label>Client ID <span class="required-mark">*</span></label>
              <input type="text" id="credClientId" placeholder="amzn1.application-oa2-client.xxxxx" />
            </div>
            <div class="form-field" style="grid-column: 1/-1;">
              <label>Client Secret <span class="required-mark">*</span></label>
              <input type="password" id="credClientSecret" placeholder="••••••••••••••••••••••••••••••••" />
            </div>
            <div class="form-field" style="grid-column: 1/-1;">
              <label>Refresh Token <span class="required-mark">*</span></label>
              <input type="password" id="credRefreshToken" placeholder="Atzr|xxxxxxxxxxxxxxxxxxxxxxxxxxxx" />
              <span class="field-hint">This is the LWA refresh token from the authorization step</span>
            </div>
            <div class="form-field" style="grid-column: 1/-1;">
              <label>Marketplace Name</label>
              <input type="text" id="credMarketplaceName" value="Amazon.com" />
            </div>
          </div>
          <div class="form-actions">
            <button class="btn" id="saveCredentials">Save Credentials</button>
            <button class="btn btn-secondary" id="cancelCredentials">Cancel</button>
          </div>
        </form>
        <div id="credentialsResult" class="fetch-result"></div>
      </section>

      <section class="panel">
        <div class="panel-title">Publish Listing to Amazon</div>
        <p style="font-size:12px; color:var(--muted); margin-bottom:16px;">Select a completed listing from your queue and publish it live to Amazon.</p>
        <div class="form-grid">
          <div class="form-field">
            <label>Listing to publish</label>
            <select id="publishListingSelect">
              <option value="">Select a listing...</option>
              <option value="1">KH-204 - Portable Kitchen Storage Set</option>
              <option value="2">AP-900 - LED Mobility Lamp</option>
              <option value="3">EC-440 - Eco Cleaning Set</option>
            </select>
          </div>
          <div class="form-field">
            <label>ASIN (if updating existing)</label>
            <input type="text" id="publishAsin" placeholder="B0XXXXXXXX (leave blank for new)" />
          </div>
          <div class="form-field">
            <label>Condition</label>
            <select id="publishCondition">
              <option value="New">New</option>
              <option value="UsedLikeNew">Used - Like New</option>
              <option value="UsedVeryGood">Used - Very Good</option>
              <option value="UsedGood">Used - Good</option>
              <option value="UsedAcceptable">Used - Acceptable</option>
            </select>
          </div>
          <div class="form-field">
            <label>Fulfillment Latency</label>
            <select id="publishFulfillment">
              <option value="2-3 days">2-3 days</option>
              <option value="4-5 days">4-5 days</option>
              <option value="1-2 days">1-2 days</option>
            </select>
          </div>
        </div>
        <div class="form-actions">
          <button class="btn" id="publishListing">Publish to Amazon</button>
        </div>
        <div id="publishResult" class="fetch-result"></div>
      </section>
    </section>

    <section class="panel mt-20">
      <div class="panel-title">Compare with Amazon (Live Data Sync)</div>
      <p style="font-size:12px; color:var(--muted); margin-bottom:16px;">Pull Amazon's live version of a listing and compare field-by-field with your local data. Choose which side wins per field — never auto-overwrites.</p>
      <div class="form-grid">
        <div class="form-field">
          <label>Listing to compare</label>
          <select id="compareListingSelect">
            <option value="">Select a listing...</option>
            <option value="1">KH-204 - Portable Kitchen Storage Set</option>
            <option value="2">AP-900 - LED Mobility Lamp</option>
            <option value="3">EC-440 - Eco Cleaning Set</option>
          </select>
        </div>
      </div>
      <div class="form-actions">
        <button class="btn" id="compareListing">Compare with Amazon</button>
      </div>
      <div id="compareResult" class="fetch-result" style="display:none;"></div>
    </section>

    <section class="panel mt-20" id="compareDetailPanel" style="display:none;">
      <div class="panel-title">Field Comparison: <span id="compareListingTitle"></span></div>
      <div class="comparison-table-wrap">
        <table class="table comparison-table">
          <thead>
            <tr><th>Field</th><th>Local Value (Sellrix)</th><th>Amazon Value (Live)</th><th>Match?</th><th>Action</th></tr>
          </thead>
          <tbody id="compareTableBody"></tbody>
        </table>
      </div>
      <div class="form-actions">
        <button class="btn btn-secondary" id="closeCompare">Close Comparison</button>
      </div>
    </section>
  </section>`;
}

function renderOrdersPage() {
  return `<section class="page-wrap">
    <section class="page-heading">
      <div>
        <span class="eyebrow">Amazon / Orders</span>
        <h1>Orders</h1>
      </div>
      <p class="page-description">View and manage all Amazon orders. Sync from SP-API to get the latest data.</p>
      <div class="page-actions">
        <button class="btn" id="syncOrders">Sync from Amazon</button>
        <button class="btn btn-secondary small-padded" id="refreshOrders">Refresh View</button>
      </div>
    </section>

    <section class="panel stats-panel" id="ordersStats">
      <div class="dashboard-grid" style="grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));">
        <div class="kpi-card"><div class="label">Total Orders</div><div class="value" id="statTotalOrders">—</div></div>
        <div class="kpi-card"><div class="label">Shipped</div><div class="value" id="statShipped">—</div></div>
        <div class="kpi-card"><div class="label">Unshipped</div><div class="value" id="statUnshipped">—</div></div>
        <div class="kpi-card"><div class="label">Cancelled</div><div class="value" id="statCancelled">—</div></div>
        <div class="kpi-card"><div class="label">Total Revenue</div><div class="value" id="statRevenue">—</div></div>
        <div class="kpi-card"><div class="label">Amazon Fees</div><div class="value" id="statFees">—</div></div>
        <div class="kpi-card"><div class="label">Profit</div><div class="value" id="statProfit">—</div></div>
        <div class="kpi-card"><div class="label">Avg ROI%</div><div class="value" id="statRoi">—</div></div>
      </div>
    </section>

    <section class="panel mt-20">
      <div class="panel-title">Orders Table</div>
      <div class="table-toolbar">
        <div class="toolbar-left">
          <input type="text" id="ordersSearch" class="searchbox" placeholder="Search order ID, city, state..." />
          <select id="ordersStatusFilter" class="mini-select">
            <option value="">All statuses</option>
            <option value="Shipped">Shipped</option>
            <option value="Unshipped">Unshipped</option>
            <option value="Cancelled">Cancelled</option>
            <option value="Pending">Pending</option>
          </select>
          <select id="ordersSortBy" class="mini-select">
            <option value="purchase_date">Date (newest)</option>
            <option value="purchase_date_asc">Date (oldest)</option>
            <option value="order_total">Revenue (high)</option>
            <option value="profit">Profit (high)</option>
            <option value="roi_percent">ROI% (high)</option>
          </select>
        </div>
        <div class="toolbar-right">
          <span class="pagination-info" id="paginationInfo">Page 1 of 1</span>
          <button class="btn btn-secondary small-padded" id="prevPage" disabled>Previous</button>
          <button class="btn btn-secondary small-padded" id="nextPage" disabled>Next</button>
        </div>
      </div>
      <div class="table-wrap">
        <table class="table orders-table">
          <thead>
            <tr>
              <th>Order ID</th>
              <th>Date</th>
              <th>Status</th>
              <th>Customer</th>
              <th>Destination</th>
              <th>Items</th>
              <th>Revenue</th>
              <th>Fees</th>
              <th>Profit</th>
              <th>ROI%</th>
            </tr>
          </thead>
          <tbody id="ordersTableBody"></tbody>
        </table>
      </div>
      <div class="empty-state" id="ordersEmpty" style="display: none; text-align: center; padding: 40px; color: var(--muted);">
        <div style="font-size: 48px; margin-bottom: 16px;">📦</div>
        <h3 style="margin: 0 0 8px;">No orders yet</h3>
        <p style="margin: 0 0 16px;">Click "Sync from Amazon" to fetch your orders via SP-API.</p>
        <button class="btn" id="syncOrdersEmpty">Sync from Amazon</button>
      </div>
    </section>
  </section>`;
}

function renderVariationsPage() {
  return `<section class="page-wrap">
    <section class="page-heading">
      <div>
        <span class="eyebrow">Catalog / Listings</span>
        <h1>Variations</h1>
      </div>
      <p class="page-description">Group related products (sizes, colors, styles) under one Amazon listing. Customers see all options on a single page.</p>
      <button class="btn small-padded" id="createVariationBtn">Create variation set</button>
    </section>
    <section class="panel">
      <div class="panel-title">Your variation groups</div>
      <p style="font-size:12px; color:var(--muted); margin-bottom:12px;">Each group = one Amazon listing with multiple child options (size, color, etc.).</p>
      <table class="table">
        <thead>
          <tr><th>Parent listing (main product)</th><th>Child variations</th><th>Variation type</th><th>Status</th></tr>
        </thead>
        <tbody>
          <tr><td>Kitchen Storage Set</td><td>Small, Medium, Large</td><td>Size</td><td><span class="status live">Synced on Amazon</span></td></tr>
          <tr><td>LED Lamp</td><td>Warm White, Cool White</td><td>Color</td><td><span class="status review">Needs your review</span></td></tr>
        </tbody>
      </table>
      <div class="empty-state" style="display: none; text-align: center; padding: 40px; color: var(--muted);">
        <div style="font-size: 48px; margin-bottom: 16px;">🔗</div>
        <h3 style="margin: 0 0 8px;">No variation sets yet</h3>
        <p style="margin: 0 0 16px;">Variations let you sell sizes, colors, or styles under one Amazon listing. Customers pick their option on a single page.</p>
        <button class="btn" id="createVariationBtn2">Create your first variation set</button>
      </div>
    </section>
  </section>`;
}

function renderShell() {
  const page = state.page;
  const title = sectionLabels[page] || 'Dashboard';
  return `<div class="app-shell">
    <aside class="sidebar">
      <div class="logo">
        <span class="logo-svg logo-svg--md" aria-hidden="true">
          <svg viewBox="0 0 160 40" fill="none" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <linearGradient id="logoGradient" x1="0" y1="0" x2="1" y2="1" gradientUnits="objectBoundingBox">
                <stop offset="0%" stop-color="#14b8a6"/>
                <stop offset="100%" stop-color="#0d9488"/>
              </linearGradient>
            </defs>
            <g class="logo-mark">
              <path d="M8 30C8 24.477 12.477 20 18 20H42C47.523 20 52 24.477 52 30V32H8V30Z" fill="url(#logoGradient)"/>
              <path d="M18 20L24 14L30 20" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
              <path d="M24 14V30" stroke="white" stroke-width="2" stroke-linecap="round" opacity="0.9"/>
              <circle cx="48" cy="10" r="8" stroke="white" stroke-width="2.5"/>
              <path d="M48 2V18M40 10H56" stroke="white" stroke-width="2" stroke-linecap="round"/>
              <path d="M60 30C60 24.477 64.477 20 70 20H94C99.523 20 104 24.477 104 30V32H60V30Z" fill="url(#logoGradient)"/>
              <path d="M70 20L76 14L82 20" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
              <path d="M76 14V30" stroke="white" stroke-width="2" stroke-linecap="round" opacity="0.9"/>
              <path d="M110 30C110 24.477 114.477 20 120 20H144C149.523 20 154 24.477 154 30V32H110V30Z" fill="url(#logoGradient)"/>
              <path d="M120 20L126 14L132 20" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
              <path d="M126 14V30" stroke="white" stroke-width="2" stroke-linecap="round" opacity="0.9"/>
            </g>
            <text x="130" y="28" class="logo-text-svg" font-family="Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" font-size="28" font-weight="800" letter-spacing="-0.02em" fill="currentColor">Sellrix</text>
          </svg>
        </span>
      </div>
      <div class="nav-group-title">Operations</div>
      <div class="nav-item ${page === 'dashboard' ? 'active' : ''}" data-section="dashboard"><span class="icon">◫</span>Dashboard</div>
      <div class="nav-item ${page === 'sourcing' ? 'active' : ''}" data-section="sourcing"><span class="icon">+</span>Add New Product</div>
      <div class="nav-item ${page === 'listings' ? 'active' : ''}" data-section="listings"><span class="icon">✦</span>All Listings</div>
      <div class="nav-item ${page === 'detail' ? 'active' : ''}" data-section="detail"><span class="icon">⌁</span>Listing Detail</div>
      <div class="nav-item ${page === 'analytics' ? 'active' : ''}" data-section="analytics"><span class="icon">⌕</span>Catalog Analytics</div>
      <div class="nav-item ${page === 'categories' ? 'active' : ''}" data-section="categories"><span class="icon">☰</span>Category Explorer</div>
      <div class="nav-item ${page === 'variations' ? 'active' : ''}" data-section="variations"><span class="icon">⎋</span>Variations</div>
      <div class="nav-group-title">AI Assets</div>
      <div class="nav-item ${page === 'imageStudio' ? 'active' : ''}" data-section="imageStudio"><span class="icon">✎</span>AI Image Studio</div>
      <div class="nav-item ${page === 'imageLibrary' ? 'active' : ''}" data-section="imageLibrary"><span class="icon">▣</span>Image Library</div>
      <div class="nav-item ${page === 'imageReferences' ? 'active' : ''}" data-section="imageReferences"><span class="icon">⌁</span>Image References</div>
      <div class="nav-item ${page === 'repricer' ? 'active' : ''}" data-section="repricer"><span class="icon">⇄</span>Repricer</div>
      <div class="nav-group-title">Amazon</div>
      <div class="nav-item ${page === 'amazonIntegration' ? 'active' : ''}" data-section="amazonIntegration"><span class="icon">☁</span>Amazon Integration</div>
      <div class="nav-item ${page === 'orders' ? 'active' : ''}" data-section="orders"><span class="icon">📦</span>Orders</div>
      <div class="nav-group-title">Account</div>
      <div class="nav-item" id="logoutNav"><span class="icon">↩</span>Logout</div>
      <div class="sidebar-credit">Sellrix — by Chaudhary Commerce Suite</div>
    </aside>
    <main class="main">
      <section class="topbar">
        <div class="topbar-left">
          <div class="page-title">${title}</div>
        </div>
        <div class="topbar-right">
          <div class="workspace-switcher">Workspace: Main Marketplace ▾</div>
          <input class="searchbox" placeholder="Search listings, ASIN, SKU, barcode" />
          <button class="help-btn" id="helpBtn" title="Help for this page">?</button>
          <div class="user-menu">
            <span class="avatar-icon">${state.user ? state.user.name[0].toUpperCase() : 'S'}</span>
            <span>${state.user ? state.user.name : 'Seller'}</span>
          </div>
        </div>
      </section>
      <section class="content">
        ${getPageContent(page)}
      </section>
    </main>
    <div class="chat-widget">
      <button class="chat-toggle" id="chatToggle" title="Ask AI Assistant">
        <span class="chat-icon">💬</span>
      </button>
      <div class="chat-modal" id="chatModal" style="display:none">
        <div class="chat-header">
          <span>AI Assistant</span>
          <button class="chat-close" id="chatClose">×</button>
        </div>
        <div class="chat-messages" id="chatMessages"></div>
        <div class="chat-input-area">
          <input type="text" class="chat-input" id="chatInput" placeholder="Ask me anything — Amazon policies, how to use this app, your listings..." />
          <button class="chat-send" id="chatSend">Send</button>
        </div>
      </div>
    </div>
    <div class="help-modal" id="helpModal" style="display:none">
      <div class="help-modal-overlay"></div>
      <div class="help-modal-content">
        <div class="help-modal-header">
          <span class="help-modal-title">Help</span>
          <button class="help-modal-close" id="helpModalClose">×</button>
        </div>
        <div class="help-modal-body" id="helpModalBody"></div>
      </div>
    </div>
  </div>`;
}

function getPageContent(page) {
  switch(page) {
    case 'sourcing': return renderSourcingPage();
    case 'listings': return renderListingsPage();
    case 'detail': return renderDetailPage();
    case 'analytics': return renderAnalyticsPage();
    case 'categories': return renderCategoryPage();
    case 'variations': return renderVariationsPage();
    case 'imageStudio': return renderImageStudioPage();
    case 'imageLibrary': return renderImageLibraryPage();
    case 'imageReferences': return renderImageReferencesPage();
    case 'repricer': return renderRepricerPage();
    case 'amazonIntegration': return renderAmazonIntegrationPage();
    case 'orders': return renderOrdersPage();
    case 'dashboard':
    default: return renderDashboardPage();
  }
}

function attachAuthEvents() {
  const authTitle = document.getElementById('authTitle');
  const submitAuth = document.getElementById('submitAuth');
  const switchMode = document.getElementById('switchMode');
  const modeText = document.getElementById('modeText');
  const modeLink = document.getElementById('modeLink');
  const nameField = document.getElementById('nameField');
  const authError = document.getElementById('authError');

  let registerMode = false;

  function updateMode() {
    if (registerMode) {
      authTitle.textContent = 'Create account';
      submitAuth.textContent = 'Create account';
      modeText.textContent = 'Already have an account?';
      modeLink.textContent = 'Login';
      nameField.style.display = 'block';
    } else {
      authTitle.textContent = 'Welcome back';
      submitAuth.textContent = 'Login';
      modeText.textContent = 'Need an account?';
      modeLink.textContent = 'Create one';
      nameField.style.display = 'none';
    }
    clearError(authError);
  }

  switchMode.addEventListener('click', () => {
    registerMode = !registerMode;
    updateMode();
  });

  modeLink.addEventListener('click', () => {
    registerMode = !registerMode;
    updateMode();
  });

  submitAuth.addEventListener('click', async () => {
    const name = document.getElementById('name').value.trim();
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;

    if (!email || !password || (registerMode && !name)) {
      showError(authError, 'Please complete all required fields.');
      return;
    }

    const endpoint = registerMode ? '/api/register' : '/api/login';
    const payload = registerMode ? { name, email, password } : { email, password };

    try {
      const response = await fetch(`${normalizeBaseUrl()}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await response.json();

      if (!response.ok) {
        showError(authError, data.detail || 'Authentication failed.');
        return;
      }

      if (registerMode) {
        registerMode = false;
        updateMode();
        showError(authError, 'Account created. Please sign in.');
        authError.style.color = 'var(--success)';
        authError.style.background = 'var(--success-soft)';
        return;
      }

      if (data.token) {
        localStorage.setItem('token', data.token);
        localStorage.setItem('user', JSON.stringify(data.user));
        state.token = data.token;
        state.user = data.user;
        state.page = 'dashboard';
        render();
      }
    } catch (err) {
      showError(authError, 'Network error. Please try again.');
    }
  });
}

async function loadRepricerData() {
  try {
    const response = await fetch(`${normalizeBaseUrl()}/api/repricer/products`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    });
    if (!response.ok) {
      console.warn('Repricer route returned an error.');
      state.repricerData = null;
      return;
    }
    state.repricerData = await response.json();
  } catch (err) {
    console.warn('Repricer products could not be loaded locally.');
    state.repricerData = null;
  }
}

function attachDashboardEvents() {
  document.querySelectorAll('[data-section]').forEach(item => {
    item.addEventListener('click', async () => {
      const section = item.getAttribute('data-section');
      if (section) {
        state.page = section;
        if (section === 'repricer') {
          await loadRepricerData();
        }
        render();
      }
    });
  });

  document.querySelectorAll('[data-list-tab]').forEach(item => {
    item.addEventListener('click', () => {
      document.querySelectorAll('[data-list-tab]').forEach(tab => tab.classList.toggle('active', tab === item));
      const tab = item.getAttribute('data-list-tab');
      const rows = document.querySelectorAll('[data-list-row]');
      rows.forEach(row => {
        if (tab === 'all' || row.getAttribute('data-list-row') === tab || (tab === 'drafts' && row.getAttribute('data-list-row') === 'draft') || (tab === 'live' && row.getAttribute('data-list-row') === 'live')) {
          row.style.display = 'table-row';
        } else {
          row.style.display = 'none';
        }
      });
    });
  });

  // Sourcing tabs - preserve form state when switching
  state.sourcingTab = state.sourcingTab || 'manual';
  state.sourcingFormData = state.sourcingFormData || { manual: {}, import: {}, ebay: {} };

  document.querySelectorAll('[data-sourcing-tab]').forEach(item => {
    item.addEventListener('click', () => {
      const newTab = item.getAttribute('data-sourcing-tab');
      if (newTab === state.sourcingTab) return;

      // Save current form data before switching
      saveSourcingFormData(state.sourcingTab);

      // Update active tab
      document.querySelectorAll('[data-sourcing-tab]').forEach(tab => tab.classList.toggle('active', tab === item));
      item.classList.add('active');
      item.setAttribute('aria-selected', 'true');
      document.querySelectorAll('[data-sourcing-tab]').forEach(tab => {
        if (tab !== item) tab.setAttribute('aria-selected', 'false');
      });

      state.sourcingTab = newTab;
      switchSourcingTab(newTab);
    });
  });

  function saveSourcingFormData(tab) {
    if (tab === 'manual') {
      state.sourcingFormData.manual = {
        sourceLink: document.getElementById('sourceLink')?.value || '',
        competitorLink: document.getElementById('competitorLink')?.value || '',
        productName: document.getElementById('productName')?.value || '',
        brand: document.getElementById('brand')?.value || '',
        cost: document.getElementById('cost')?.value || '',
        sellPrice: document.getElementById('sellPrice')?.value || '',
        handlingDays: document.getElementById('handlingDays')?.value || '',
        barcode: document.getElementById('barcode')?.value || '',
        autoPrice: document.getElementById('autoPrice')?.value || ''
      };
    } else if (tab === 'import') {
      state.sourcingFormData.import = {
        fileName: document.getElementById('bulkImportFile')?.value || ''
      };
    } else if (tab === 'ebay') {
      state.sourcingFormData.ebay = {
        sellerInput: document.getElementById('ebaySellerInput')?.value || ''
      };
    }
  }

  function restoreSourcingFormData(tab) {
    if (tab === 'manual') {
      const data = state.sourcingFormData.manual || {};
      if (data.sourceLink) document.getElementById('sourceLink').value = data.sourceLink;
      if (data.competitorLink) document.getElementById('competitorLink').value = data.competitorLink;
      if (data.productName) document.getElementById('productName').value = data.productName;
      if (data.brand) document.getElementById('brand').value = data.brand;
      if (data.cost) document.getElementById('cost').value = data.cost;
      if (data.sellPrice) document.getElementById('sellPrice').value = data.sellPrice;
      if (data.handlingDays) document.getElementById('handlingDays').value = data.handlingDays;
      if (data.barcode) document.getElementById('barcode').value = data.barcode;
      if (data.autoPrice) document.getElementById('autoPrice').value = data.autoPrice;
      updateAddButtonState();
    } else if (tab === 'import') {
      const data = state.sourcingFormData.import || {};
      // File inputs can't be programmatically set for security, but we can show the filename
      if (data.fileName) {
        const fileInput = document.getElementById('bulkImportFile');
        if (fileInput) fileInput.title = data.fileName;
      }
    } else if (tab === 'ebay') {
      const data = state.sourcingFormData.ebay || {};
      if (data.sellerInput) document.getElementById('ebaySellerInput').value = data.sellerInput;
      const runBtn = document.getElementById('runEbayFetch');
      if (runBtn) runBtn.disabled = !data.sellerInput;
    }
  }

  function switchSourcingTab(tab) {
    const contentEl = document.getElementById('sourcingTabContent');
    const titleEl = document.getElementById('sourcingTabTitle');
    const descEl = document.getElementById('sourcingTabDesc');
    
    if (!contentEl) return;

    if (tab === 'manual') {
      titleEl.textContent = 'Add One Product';
      descEl.textContent = 'Add one product at a time by pasting its link — we\'ll fetch the title and image automatically.';
      contentEl.innerHTML = renderAddOneProductForm();
      attachAddOneProductEvents();
      restoreSourcingFormData('manual');
    } else if (tab === 'import') {
      titleEl.textContent = 'Import from Spreadsheet';
      descEl.textContent = 'Add many products at once from a CSV or Excel file.';
      contentEl.innerHTML = renderImportForm();
      attachImportEvents();
    } else if (tab === 'ebay') {
      titleEl.textContent = 'Fetch from eBay Seller';
      descEl.textContent = 'Pull every product from one eBay seller\'s store.';
      contentEl.innerHTML = renderEbayForm();
      attachEbayEvents();
    }
  }

  // Initialize the first tab's events
  attachAddOneProductEvents();

  const addSourceProduct = document.getElementById('addSourceProduct');
  const sourceLinkInput = document.getElementById('sourceLink');
  if (addSourceProduct && sourceLinkInput) {
    // Enable/disable button based on required field
    function updateAddButtonState() {
      const hasSourceLink = sourceLinkInput.value.trim().length > 0;
      addSourceProduct.disabled = !hasSourceLink;
    }
    sourceLinkInput.addEventListener('input', updateAddButtonState);
    updateAddButtonState();

    addSourceProduct.addEventListener('click', async () => {
      const sourceLink = sourceLinkInput.value.trim();
      const productName = document.getElementById('productName')?.value || '';
      const brand = document.getElementById('brand')?.value || '';
      const competitorLink = document.getElementById('competitorLink')?.value || '';
      const sku = document.getElementById('barcode')?.value || 'manual-sku';
      const resultBox = document.getElementById('sourceFetchResult');

      if (!sourceLink) {
        if (resultBox) resultBox.textContent = 'Please paste a source link first.';
        return;
      }

      addSourceProduct.disabled = true;
      addSourceProduct.textContent = 'Fetching...';

      try {
        const response = await fetch(`${normalizeBaseUrl()}/api/sourcing/products/fetch`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ source_link: sourceLink, competitor_link: competitorLink, product_name: productName, brand, sku })
        });
        const data = await response.json();
        if (resultBox) {
          if (data.success) {
            resultBox.innerHTML = `<div style="color: var(--success);"><strong>Success!</strong> Title and image fetched from source link.<br><strong>Title:</strong> ${data.title}<br><strong>Image:</strong> ${data.image_url ? 'Found' : 'Not found'}</div>`;
          } else {
            resultBox.innerHTML = `<div style="color: var(--error);"><strong>Couldn't fetch automatically:</strong> ${data.reason || 'Unknown reason'}<br>You can still add the product manually and fill in details.</div>`;
          }
          }
            } catch (err) {
        if (resultBox) resultBox.innerHTML = `<div style="color: var(--error);"><strong>Error:</strong> Couldn't reach the source link. Please check the URL and try again.</div>`;
      } finally {
        addSourceProduct.disabled = false;
        addSourceProduct.textContent = 'Add to Queue';
      }
    });
  }

  const runBulkImport = document.getElementById('runBulkImport');
  const bulkImportFile = document.getElementById('bulkImportFile');
  if (runBulkImport && bulkImportFile) {
    bulkImportFile.addEventListener('change', () => {
      runBulkImport.disabled = !bulkImportFile.files?.length;
    });
    runBulkImport.disabled = !bulkImportFile.files?.length;

    runBulkImport.addEventListener('click', async () => {
      const file = bulkImportFile.files?.[0];
      const progressBox = document.getElementById('bulkImportProgress');
      const summaryBox = document.getElementById('bulkImportSummary');

      if (!file) {
        if (progressBox) progressBox.textContent = 'Choose a CSV or spreadsheet file first.';
        return;
      }

      runBulkImport.disabled = true;
      runBulkImport.textContent = 'Importing...';

      try {
        const form = new FormData();
        form.append('file', file);
        if (progressBox) progressBox.textContent = 'Starting spreadsheet import...';

        const response = await fetch(`${normalizeBaseUrl()}/api/sourcing/import`, {
          method: 'POST',
          body: form
        });
        const data = await response.json();

        if (!response.ok) {
          const errorMessage = data.detail || 'Import failed. Please check your file.';
          if (progressBox) progressBox.innerHTML = `<div style="color: var(--error);"><strong>Error:</strong> ${errorMessage}</div>`;
          if (summaryBox) summaryBox.innerHTML = '';
          runBulkImport.disabled = false;
          runBulkImport.textContent = 'Import rows';
          return;
        }

        if (progressBox) progressBox.textContent = 'Bulk import job started.';

        const start = Date.now();
        let pollCount = 0;
        const timer = setInterval(async () => {
          pollCount += 1;
          try {
            const progressResponse = await fetch(`${normalizeBaseUrl()}/api/sourcing/import/progress`);
            const progress = await progressResponse.json();
            const total = progress.total || data.total || 0;
            const done = progress.done || 0;
            if (progress.running) {
              if (progressBox) progressBox.innerHTML = `Fetched ${done} of ${total}`;
            } else {
              clearInterval(timer);
              if (progressBox) progressBox.innerHTML = `Fetched ${progress.done || 0} of ${progress.total || 0}`;
              if (summaryBox) {
                const items = Array.isArray(progress.items) ? progress.items : [];
                const titleSuccess = items.filter(i => i.title_success).length;
                const imageSuccess = items.filter(i => i.image_success).length;
                const fullySuccess = items.filter(i => i.success).length;
                const rows = items.map(item => {
                  const titleStatus = item.title_success ? '✓ Title' : '✗ Title: ' + (item.title_reason || 'failed');
                  const imageStatus = item.image_success ? '✓ Image' : '✗ Image: ' + (item.image_reason || 'failed');
                  return `Row ${item.row} (${item.sku}): ${titleStatus} | ${imageStatus}`;
                }).join('<br>');
summaryBox.innerHTML = `<strong>Import summary:</strong> ${fullySuccess} fully successful, ${titleSuccess} titles, ${imageSuccess} images, ${progress.failed || 0} failed.<br>${rows}`;
              }
            }
            }
            catch (err) {
              if (progressBox) progressBox.textContent = 'Bulk import progress is unavailable.';
            }
            if (pollCount > 100 || (Date.now() - start) > 12000) {
              clearInterval(timer);
            }
}, 550);
    }
    catch (err) {
      if (progressBox) progressBox.innerHTML = `<div style="color: var(--error);"><strong>Error:</strong> Bulk import failed. Check the file and source links.</div>`;
    } finally {
      runBulkImport.disabled = false;
      runBulkImport.textContent = 'Import rows';
    }
});
}

  // Sourcing tab event attachment functions
  function attachAddOneProductEvents() {
    const addSourceProduct = document.getElementById('addSourceProduct');
    const sourceLinkInput = document.getElementById('sourceLink');
    if (addSourceProduct && sourceLinkInput) {
      function updateAddButtonState() {
        const hasSourceLink = sourceLinkInput.value.trim().length > 0;
        addSourceProduct.disabled = !hasSourceLink;
      }
      sourceLinkInput.addEventListener('input', updateAddButtonState);
      updateAddButtonState();

      addSourceProduct.addEventListener('click', async () => {
        const sourceLink = sourceLinkInput.value.trim();
        const productName = document.getElementById('productName')?.value || '';
        const brand = document.getElementById('brand')?.value || '';
        const competitorLink = document.getElementById('competitorLink')?.value || '';
        const sku = document.getElementById('barcode')?.value || 'manual-sku';
        const resultBox = document.getElementById('sourceFetchResult');

        if (!sourceLink) {
          if (resultBox) resultBox.textContent = 'Please paste a source link first.';
          return;
        }

        addSourceProduct.disabled = true;
        addSourceProduct.textContent = 'Fetching...';

        try {
          const response = await fetch(`${normalizeBaseUrl()}/api/sourcing/products/fetch`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ source_link: sourceLink, competitor_link: competitorLink, product_name: productName, brand, sku })
          });
          const data = await response.json();
          if (resultBox) {
            if (data.success) {
              resultBox.innerHTML = `<div style="color: var(--success);"><strong>Success!</strong> Title and image fetched from source link.<br><strong>Title:</strong> ${data.title}<br><strong>Image:</strong> ${data.image_url ? 'Found' : 'Not found'}</div>`;
            } else {
            }
            }
            }
            catch (err) {
          if (resultBox) resultBox.innerHTML = `<div style="color: var(--error);"><strong>Error:</strong> Couldn't reach the source link. Please check the URL and try again.</div>`;
        } finally {
          addSourceProduct.disabled = false;
          addSourceProduct.textContent = 'Add to Queue';
        }
      });
    }
  }

  function attachImportEvents() {
    const runBulkImport = document.getElementById('runBulkImport');
    const bulkImportFile = document.getElementById('bulkImportFile');
    if (runBulkImport && bulkImportFile) {
      bulkImportFile.addEventListener('change', () => {
        runBulkImport.disabled = !bulkImportFile.files?.length;
      });
      runBulkImport.disabled = !bulkImportFile.files?.length;

      runBulkImport.addEventListener('click', async () => {
        const file = bulkImportFile.files?.[0];
        const progressBox = document.getElementById('bulkImportProgress');
        const summaryBox = document.getElementById('bulkImportSummary');

        if (!file) {
          if (progressBox) progressBox.textContent = 'Choose a CSV or spreadsheet file first.';
          return;
        }

        runBulkImport.disabled = true;
        runBulkImport.textContent = 'Importing...';

        try {
          const form = new FormData();
          form.append('file', file);
          if (progressBox) progressBox.textContent = 'Starting spreadsheet import...';

          const response = await fetch(`${normalizeBaseUrl()}/api/sourcing/import`, {
            method: 'POST',
            body: form
          });
          const data = await response.json();

          if (!response.ok) {
            const errorMessage = data.detail || 'Import failed. Please check your file.';
            if (progressBox) progressBox.innerHTML = `<div style="color: var(--error);"><strong>Error:</strong> ${errorMessage}</div>`;
            if (summaryBox) summaryBox.innerHTML = '';
            runBulkImport.disabled = false;
            runBulkImport.textContent = 'Import rows';
            return;
          }

          if (progressBox) progressBox.textContent = 'Bulk import job started.';

          const start = Date.now();
          let pollCount = 0;
          const timer = setInterval(async () => {
            pollCount += 1;
            try {
              const progressResponse = await fetch(`${normalizeBaseUrl()}/api/sourcing/import/progress`);
              const progress = await progressResponse.json();
              const total = progress.total || data.total || 0;
              const done = progress.done || 0;
              if (progress.running) {
                if (progressBox) progressBox.innerHTML = `Fetched ${done} of ${total}`;
              } else {
                clearInterval(timer);
                if (progressBox) progressBox.innerHTML = `Fetched ${progress.done || 0} of ${progress.total || 0}`;
                if (summaryBox) {
                  const items = Array.isArray(progress.items) ? progress.items : [];
                  const titleSuccess = items.filter(i => i.title_success).length;
                  const imageSuccess = items.filter(i => i.image_success).length;
                  const fullySuccess = items.filter(i => i.success).length;
                  const rows = items.map(item => {
                    const titleStatus = item.title_success ? '✓ Title' : '✗ Title: ' + (item.title_reason || 'failed');
                    const imageStatus = item.image_success ? '✓ Image' : '✗ Image: ' + (item.image_reason || 'failed');
                    return `Row ${item.row} (${item.sku}): ${titleStatus} | ${imageStatus}`;
                  }).join('<br>');
                  summaryBox.innerHTML = `<strong>Import summary:</strong> ${fullySuccess} fully successful, ${titleSuccess} titles, ${imageSuccess} images, ${progress.failed || 0} failed.<br>${rows}`;
                }
              }
            } catch (err) {
              if (progressBox) progressBox.textContent = 'Bulk import progress is unavailable.';
            }
            if (pollCount > 100 || (Date.now() - start) > 12000) {
              clearInterval(timer);
            }
          }, 550);
        } catch (err) {
          if (progressBox) progressBox.innerHTML = `<div style="color: var(--error);"><strong>Error:</strong> Bulk import failed. Check the file and source links.</div>`;
        } finally {
          runBulkImport.disabled = false;
          runBulkImport.textContent = 'Import rows';
        }
      });
    }
  }

  function attachEbayEvents() {
    const ebaySellerInput = document.getElementById('ebaySellerInput');
    const runEbayFetch = document.getElementById('runEbayFetch');
    const cancelEbayFetch = document.getElementById('cancelEbayFetch');
    const ebayFetchProgress = document.getElementById('ebayFetchProgress');
    const ebayFetchResults = document.getElementById('ebayFetchResults');

    if (ebaySellerInput && runEbayFetch) {
      ebaySellerInput.addEventListener('input', () => {
        runEbayFetch.disabled = !ebaySellerInput.value.trim();
      });
      runEbayFetch.disabled = !ebaySellerInput.value.trim();

      runEbayFetch.addEventListener('click', async () => {
        const sellerInput = ebaySellerInput.value.trim();
        if (!sellerInput) return;

        runEbayFetch.disabled = true;
        runEbayFetch.textContent = 'Fetching...';
        if (cancelEbayFetch) cancelEbayFetch.style.display = 'inline-flex';
        if (ebayFetchProgress) {
          ebayFetchProgress.innerHTML = 'Starting eBay seller fetch...';
          ebayFetchProgress.style.display = 'block';
        }
        if (ebayFetchResults) {
          ebayFetchResults.style.display = 'none';
          ebayFetchResults.innerHTML = '';
        }

        try {
          const response = await fetch(`${normalizeBaseUrl()}/api/sourcing/ebay/fetch-seller`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ seller_link: sellerInput })
          });
          const data = await response.json();

          if (!response.ok) {
            if (ebayFetchProgress) ebayFetchProgress.innerHTML = `<div style="color: var(--error);"><strong>Error:</strong> ${data.detail || 'Failed to start fetch'}</div>`;
            runEbayFetch.disabled = false;
            runEbayFetch.textContent = 'Fetch all products';
            if (cancelEbayFetch) cancelEbayFetch.style.display = 'none';
            return;
          }

          const start = Date.now();
          let pollCount = 0;
          const timer = setInterval(async () => {
            pollCount += 1;
            try {
              const progressResponse = await fetch(`${normalizeBaseUrl()}/api/sourcing/ebay/fetch-progress`);
              const progress = await progressResponse.json();

              if (progress.error) {
                clearInterval(timer);
                if (ebayFetchProgress) ebayFetchProgress.innerHTML = `<div style="color: var(--error);"><strong>Error:</strong> ${progress.error}</div>`;
                runEbayFetch.disabled = false;
                runEbayFetch.textContent = 'Fetch all products';
                if (cancelEbayFetch) cancelEbayFetch.style.display = 'none';
                return;
              }

              const total = progress.total || 0;
              const done = progress.done || 0;
              const products = progress.products || [];
              const skipped = progress.skipped || [];

              if (progress.running) {
                if (ebayFetchProgress) ebayFetchProgress.innerHTML = `Fetched ${done} of ${total} — ${products.length} ready, ${skipped.length} skipped for compliance`;
              } else {
                clearInterval(timer);
                runEbayFetch.disabled = false;
                runEbayFetch.textContent = 'Fetch all products';
                if (cancelEbayFetch) cancelEbayFetch.style.display = 'none';
                
                if (ebayFetchResults) {
                  ebayFetchResults.style.display = 'block';
                  let html = '<div style="margin-bottom:12px;"><strong>Results:</strong> ';
                  html += `${products.length} products ready to add, ${skipped.length} skipped for compliance reasons.</div>`;
                  
                  if (products.length > 0) {
                    html += '<div style="margin-top:12px;"><strong>✅ Ready to add (pre-selected):</strong></div>';
                    html += '<div style="max-height:300px; overflow-y:auto; border:1px solid var(--line); border-radius:8px;">';
                    products.forEach((p, i) => {
                      const img = p.image_url ? `<img src="${p.image_url}" style="width:40px;height:40px;object-fit:cover;border-radius:4px;margin-right:8px;">` : '<div style="width:40px;height:40px;background:var(--primary-soft);border-radius:4px;margin-right:8px;"></div>';
                      html += `<label style="display:flex;align-items:center;padding:8px;border-bottom:1px solid var(--line);gap:8px;">`;
                      html += `<input type="checkbox" data-ebay-product="${i}" checked style="width:18px;height:18px;">`;
                      html += `${img}<div><strong>${escapeHtml(p.title)}</strong><br><small style="color:var(--muted);">${escapeHtml(p.source_link)}</small></div>`;
                      html += `</label>`;
                    });
                    html += '</div>';
                  }
                  
                  if (skipped.length > 0) {
                    html += '<div style="margin-top:16px;"><strong>⚠️ Skipped — compliance risk (not selected):</strong></div>';
                    html += '<div style="max-height:200px; overflow-y:auto; border:1px solid var(--error-soft); border-radius:8px; background:var(--error-soft);">';
                    skipped.forEach((p, i) => {
                      const img = p.image_url ? `<img src="${p.image_url}" style="width:40px;height:40px;object-fit:cover;border-radius:4px;margin-right:8px;">` : '<div style="width:40px;height:40px;background:var(--error-soft);border-radius:4px;margin-right:8px;"></div>';
                      html += `<label style="display:flex;align-items:center;padding:8px;border-bottom:1px solid var(--error-soft);gap:8px;">`;
                      html += `<input type="checkbox" data-ebay-skipped="${i}" style="width:18px;height:18px;">`;
                      html += `${img}<div><strong>${escapeHtml(p.title)}</strong><br><small style="color:var(--error);">${escapeHtml(p.compliance_reason)}</small><br><small style="color:var(--muted);">${escapeHtml(p.source_link)}</small></div>`;
                      html += `</label>`;
                    });
                    html += '</div>';
                  }
                  
                  html += '<div class="form-actions" style="margin-top:16px;">';
                  html += '<button class="btn" id="addSelectedEbay">Add selected to queue</button>';
                  html += '<button class="btn btn-secondary small-padded" id="clearEbayResults">Clear results</button>';
                  html += '</div>';
                  ebayFetchResults.innerHTML = html;

                  const addSelectedBtn = document.getElementById('addSelectedEbay');
                  if (addSelectedBtn) {
                    addSelectedBtn.addEventListener('click', async () => {
                      const checkboxes = ebayFetchResults.querySelectorAll('input[type="checkbox"]:checked');
                      const selectedProducts = [];
                      checkboxes.forEach(cb => {
                        const idx = parseInt(cb.dataset.ebayProduct) || parseInt(cb.dataset.ebaySkipped);
                        const isSkipped = cb.dataset.ebaySkipped !== undefined;
                        const sourceArray = isSkipped ? progress.skipped : progress.products;
                        const product = sourceArray[idx];
                        if (product) {
                          selectedProducts.push({ ...product, selected: true });
                        }
                      });
                      
                      if (selectedProducts.length === 0) {
                        alert('No products selected');
                        return;
                      }
                      
                      addSelectedBtn.disabled = true;
                      addSelectedBtn.textContent = 'Adding...';
                      
                      try {
                        const response = await fetch(`${normalizeBaseUrl()}/api/sourcing/ebay/add-selected`, {
                          method: 'POST',
                          headers: { 'Content-Type': 'application/json' },
                          body: JSON.stringify({ products: selectedProducts })
                        });
                        const data = await response.json();
                        
                        if (!response.ok) {
                          alert(data.detail || 'Failed to add products');
                        } else {
                          alert(data.message);
                          render();
                        }
                      } catch (err) {
                        alert('Error adding products: ' + err.message);
                      } finally {
                        addSelectedBtn.disabled = false;
                        addSelectedBtn.textContent = 'Add selected to queue';
                      }
                    });
                  }

                  const clearBtn = document.getElementById('clearEbayResults');
                  if (clearBtn) {
                    clearBtn.addEventListener('click', () => {
                      if (ebayFetchResults) {
                        ebayFetchResults.style.display = 'none';
                        ebayFetchResults.innerHTML = '';
                      }
                      if (ebayFetchProgress) {
                        ebayFetchProgress.innerHTML = '';
                        ebayFetchProgress.style.display = 'none';
                      }
                    });
                  }
                }
              }
            } catch (err) {
              if (ebayFetchProgress) ebayFetchProgress.innerHTML = `<div style="color: var(--error);"><strong>Error:</strong> ${err.message}</div>`;
            }
            if (pollCount > 200 || (Date.now() - start) > 300000) {
              clearInterval(timer);
            }
          }, 1000);

          if (cancelEbayFetch) {
            cancelEbayFetch.onclick = () => {
              clearInterval(timer);
              runEbayFetch.disabled = false;
              runEbayFetch.textContent = 'Fetch all products';
              cancelEbayFetch.style.display = 'none';
              if (ebayFetchProgress) ebayFetchProgress.innerHTML = 'Fetch cancelled.';
            };
          }

        } catch (err) {
          if (ebayFetchProgress) ebayFetchProgress.innerHTML = `<div style="color: var(--error);"><strong>Error:</strong> ${err.message}</div>`;
          runEbayFetch.disabled = false;
          runEbayFetch.textContent = 'Fetch all products';
          if (cancelEbayFetch) cancelEbayFetch.style.display = 'none';
        }
      });
}
  }

  const generateAiText = document.getElementById('generateAiText');
  if (generateAiText) {
    generateAiText.addEventListener('click', async () => {
      try {
        const response = await fetch(`${normalizeBaseUrl()}/api/ai/text/generate`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            listing_id: 'KH-204',
            product_name: 'Portable Kitchen Storage Set',
            brand: 'Nexa Home',
            category: 'Home & Kitchen'
          })
        });

        if (!response.ok) {
          console.warn('Text generation route returned an error.');
          return;
        }

        const data = await response.json();
        const title = document.getElementById('aiTitle');
        const bullets = document.getElementById('aiBullets');
        const description = document.getElementById('aiDescription');
        const keywords = document.getElementById('aiKeywords');

        if (title) title.value = data.title;
        if (bullets) bullets.value = data.bullet_points.join('\n');
        if (description) description.value = data.description;
        if (keywords) keywords.value = data.backend_keywords.join(', ');

        const detailTitleText = document.getElementById('detailTitleText');
        if (detailTitleText) detailTitleText.textContent = data.title;

        const detailBulletPoints = document.getElementById('detailBulletPoints');
        if (detailBulletPoints) detailBulletPoints.textContent = data.bullet_points.join(' • ');

        const detailDescription = document.getElementById('detailDescription');
        if (detailDescription) detailDescription.textContent = data.description;

        const detailKeywords = document.getElementById('detailKeywords');
        if (detailKeywords) detailKeywords.textContent = data.backend_keywords.join(', ');
      } catch (err) {
        console.warn('AI text generation request failed locally.');
      }
    });
  }

  const openImageStudio = document.getElementById('openImageStudio');
  if (openImageStudio) {
    openImageStudio.addEventListener('click', () => {
      state.page = 'imageStudio';
      render();
    });
  }

  const generateImageCreative = document.getElementById('generateImageCreative');
  if (generateImageCreative) {
    generateImageCreative.addEventListener('click', async () => {
      try {
        const response = await fetch(`${normalizeBaseUrl()}/api/ai/image/generate`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            product_id: 'KH-204',
            product_name: 'Portable Kitchen Storage Set',
            mode: 'creative',
            fidelity: 80,
            standing_instructions: 'always white background',
            concept_mode: 'suggest',
            image_slot: 'Main'
          })
        });
        if (!response.ok) { console.warn('Image generation error'); return; }
        const data = await response.json();
        const image = data.images?.[0];
        if (image) {
          const preview = document.querySelector('.image-preview');
          if (preview) preview.innerHTML = image.title || 'Generated Image';
        }
      } catch (err) { console.warn('Image generation failed'); }
    });
  }

  const downloadImage = document.getElementById('downloadImage');
  if (downloadImage) {
    downloadImage.addEventListener('click', () => {
      alert('Download image - in the full app this would download the generated image file.');
    });
  }

  const assignImage = document.getElementById('assignImage');
  if (assignImage) {
    assignImage.addEventListener('click', () => {
      alert('Assign to listing slot - in the full app this would add the generated image to your product listing.');
    });
  }

  const imageStudioGenerate = document.getElementById('generateImage');
  if (imageStudioGenerate) {
    imageStudioGenerate.addEventListener('click', async () => {
      try {
        const body = {
          product_id: 'KH-204',
          product_name: 'Portable Kitchen Storage Set',
          mode: document.querySelector('[data-image-tab].active')?.getAttribute('data-image-tab') || 'creative',
          fidelity: parseInt(document.getElementById('fidelitySlider')?.value || '82'),
          standing_instructions: document.getElementById('standingInstructions')?.value || 'always white background',
          concept_mode: document.querySelector('[data-sec-method].active')?.getAttribute('data-sec-method') || 'suggest',
          image_slot: document.getElementById('imageSlot')?.value || 'Main'
        };

        const response = await fetch(`${normalizeBaseUrl()}/api/ai/image/generate`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body)
        });

        if (!response.ok) {
          console.warn('Image generation route returned an error.');
          return;
        }

        const data = await response.json();
        const image = data.images?.[0];
        if (image) {
          const preview = document.querySelector('.image-preview');
          if (preview) preview.innerHTML = image.title || 'Generated Image';
        }
      } catch (err) {
        console.warn('AI image generation request failed locally.');
      }
    });
  }

  const previewListing = document.getElementById('previewListing');
  if (previewListing) {
    previewListing.addEventListener('click', () => {
      const previewPanel = document.getElementById('detailPreviewPanel');
      const autoFixProgress = document.getElementById('autoFixProgress');
      const autoFixSummary = document.getElementById('autoFixSummary');
      if (!previewPanel) {
        if (autoFixSummary) autoFixSummary.textContent = 'Preview could not open. Please open the Listing Detail page again.';
        return;
      }
      previewPanel.style.display = 'block';
      if (autoFixProgress) autoFixProgress.textContent = 'Preview ready';
      if (autoFixSummary) autoFixSummary.textContent = 'Preview: source link values, AI gaps, and manual attention separated.';
    });
  }

  const closePreview = document.getElementById('closePreview');
  if (closePreview) {
    closePreview.addEventListener('click', () => {
      const previewPanel = document.getElementById('detailPreviewPanel');
      if (previewPanel) {
        previewPanel.style.display = 'none';
      }
    });
  }

  const autoFix = document.getElementById('autoFix');
  if (autoFix) {
    autoFix.addEventListener('click', async () => {
      const autoFixProgress = document.getElementById('autoFixProgress');
      const autoFixSummary = document.getElementById('autoFixSummary');
      const previewPanel = document.getElementById('detailPreviewPanel');
      const sourceList = document.getElementById('sourceList');
      const aiList = document.getElementById('aiList');
      const manualList = document.getElementById('manualList');

      try {
        if (!previewPanel) {
          throw new Error('Preview panel is unavailable.');
        }

        if (autoFixProgress) autoFixProgress.textContent = 'Fixing 1 of 1 listing...';
        if (autoFixSummary) autoFixSummary.textContent = 'Running Auto-fix...';
        previewPanel.style.display = 'block';

        await new Promise(resolve => setTimeout(resolve, 550));

        state.detailAutoFixSource = [
          'Item name: copied from source link',
          'Brand: copied from source link',
          'Category: copied from source link',
          'Description: copied from source link',
          'Bullet point 1: copied from source link',
          'Bullet point 2: copied from source link'
        ];
        state.detailAutoFixAI = [
          'Bullet point 3: generated by AI — no source data available',
          'Image: generated by AI — source data missing'
        ];
        state.detailAutoFixRemaining = [
          'Dimensions need a human supplier confirmation',
          'Compliance image brief needs seller review'
        ];

        if (autoFixSummary) autoFixSummary.textContent = 'Auto-fix complete. Review the three categories in the preview before Submit.';
        if (sourceList) {
          sourceList.innerHTML = state.detailAutoFixSource.map(item => `<li>${item}</li>`).join('');
        }
        if (aiList) {
          aiList.innerHTML = state.detailAutoFixAI.map(item => `<li>${item}</li>`).join('');
        }
        if (manualList) {
          manualList.innerHTML = state.detailAutoFixRemaining.map(item => `<li>${item}</li>`).join('');
        }

        previewPanel.style.display = 'block';

        const detailTitleText = document.getElementById('detailTitleText');
        if (detailTitleText) detailTitleText.textContent = 'Nexa Home Portable Kitchen Storage Set';
        const detailBulletPoints = document.getElementById('detailBulletPoints');
        if (detailBulletPoints) detailBulletPoints.textContent = 'Organize kitchen spaces • Durable • Compact • Easy to store';
        const detailDescription = document.getElementById('detailDescription');
        if (detailDescription) detailDescription.textContent = 'Designed for one clean, organized kitchen experience.';
        const detailKeywords = document.getElementById('detailKeywords');
        if (detailKeywords) detailKeywords.textContent = 'portable kitchen storage set, nexa home, home kitchen, kitchen storage, home organization';
        const detailBrandText = document.querySelector('.detail-row .detail-value');
        if (detailBrandText) detailBrandText.textContent = 'Nexa Home';
      } catch (err) {
        if (autoFixProgress) autoFixProgress.textContent = 'Auto-fix failed';
        if (autoFixSummary) autoFixSummary.textContent = 'Auto-fix failed. Please retry the listing, then check the competitor/source link and AI generation fields.';
        if (previewPanel) previewPanel.style.display = 'block';
        if (sourceList) sourceList.innerHTML = '<li>No source data was available.</li>';
        if (aiList) aiList.innerHTML = '<li>No AI fields were generated.</li>';
        if (manualList) manualList.innerHTML = '<li>Manual review required.</li>';
      }
    });
  }

  const continueSubmit = document.getElementById('continueSubmit');
  if (continueSubmit) {
    continueSubmit.addEventListener('click', () => {
      const previewPanel = document.getElementById('detailPreviewPanel');
      if (previewPanel) previewPanel.style.display = 'none';
      
      // Confirm before submitting to Amazon
      if (!confirm('This will submit your listing to Amazon for review. Once submitted, you cannot undo this action. Continue?')) {
        return;
      }
      
      const submitMessage = 'Submitted to Amazon! Your listing is now under review.';
      const summary = document.getElementById('autoFixSummary');
      if (summary) summary.textContent = submitMessage;
      
      // In a real app, this would call the API to submit
      alert('In the full app, this would call the Amazon API to publish your listing.');
    });
  }

  const viewRawData = document.getElementById('viewRawData');
  if (viewRawData) {
    viewRawData.addEventListener('click', () => {
      alert('View raw data - in the full app this would show the complete listing JSON.');
    });
  }

  document.querySelectorAll('[data-image-tab]').forEach(item => {
    item.addEventListener('click', () => {
      document.querySelectorAll('[data-image-tab]').forEach(tab => tab.classList.toggle('active', tab === item));
    });
  });

  document.querySelectorAll('[data-sec-method]').forEach(item => {
    item.addEventListener('click', () => {
      document.querySelectorAll('[data-sec-method]').forEach(method => method.classList.toggle('active', method === item));
    });
  });

  const imageFidelity = document.getElementById('fidelitySlider');
  if (imageFidelity) {
    imageFidelity.addEventListener('input', () => {
      const value = document.getElementById('fidelitySlider').value;
      const valueLabel = document.getElementById('fidelityValue');
      if (valueLabel) valueLabel.textContent = `${value}%`;
    });
  }

  const saveAiText = document.getElementById('saveAiText');
  if (saveAiText) {
    saveAiText.addEventListener('click', () => {
      // Get the AI content from the textareas
      const title = document.getElementById('aiTitle')?.value || '';
      const bullets = document.getElementById('aiBullets')?.value || '';
      const description = document.getElementById('aiDescription')?.value || '';
      const keywords = document.getElementById('aiKeywords')?.value || '';
      
      if (!title && !bullets && !description && !keywords) {
        alert('No AI content to save. Click "Generate AI content" first.');
        return;
      }
      
      // Update the detail page fields
      const detailTitleText = document.getElementById('detailTitleText');
      if (detailTitleText && title) detailTitleText.textContent = title;
      
      const detailBulletPoints = document.getElementById('detailBulletPoints');
      if (detailBulletPoints && bullets) detailBulletPoints.textContent = bullets.split('\n').join(' • ');
      
      const detailDescription = document.getElementById('detailDescription');
      if (detailDescription && description) detailDescription.textContent = description;
      
      const detailKeywords = document.getElementById('detailKeywords');
      if (detailKeywords && keywords) detailKeywords.textContent = keywords;
      
      alert('AI content saved to this listing!');
    });
  }

  const logout = document.getElementById('logoutNav');
  if (logout) {
    logout.addEventListener('click', async () => {
      try {
        await fetch(`${normalizeBaseUrl()}/api/logout`, {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${state.token}` }
        });
      } catch (err) {
        console.warn('Logout request failed locally.');
      }
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      state.token = '';
      state.user = null;
      state.page = 'login';
      render();
});
  }

  // ===== Amazon Integration Events =====
  attachAmazonIntegrationEvents();

  // ===== Orders Events =====
  attachOrdersEvents();

  attachChatEvents();
}

function attachAmazonIntegrationEvents() {
  // Check credentials status
  const checkStatusBtn = document.getElementById('checkCredentialsStatus');
  if (checkStatusBtn) {
    checkStatusBtn.addEventListener('click', async () => {
      const statusBox = document.getElementById('credentialsStatus');
      if (statusBox) {
        statusBox.innerHTML = '<div style="color:var(--muted);">Checking connection...</div>';
      }
      try {
        const response = await fetch(`${normalizeBaseUrl()}/api/amazon/credentials/status`);
        const data = await response.json();
        if (statusBox) {
          if (data.configured) {
            statusBox.innerHTML = `<div style="color: ${data.is_mock ? 'var(--warning)' : 'var(--success)'};">
              <strong>${data.is_mock ? '⚠ Mock Mode' : '✓ Connected'}</strong><br>
              Marketplace: ${data.marketplace}<br>
              Region: ${data.region}<br>
              ${data.message}
            </div>`;
            document.getElementById('setupGuide').style.display = 'none';
            document.getElementById('credentialsForm').style.display = 'none';
          } else {
            statusBox.innerHTML = `<div style="color: var(--error);"><strong>✗ Not Connected</strong><br>${data.message}</div>`;
            document.getElementById('setupGuide').style.display = 'block';
            document.getElementById('credentialsForm').style.display = 'none';
          }
        }
      } catch (err) {
        if (statusBox) statusBox.innerHTML = `<div style="color: var(--error);"><strong>Error:</strong> ${err.message}</div>`;
      }
    });
  }

  // Show credentials form
  const showFormBtn = document.getElementById('showCredentialsForm');
  if (showFormBtn) {
    showFormBtn.addEventListener('click', () => {
      document.getElementById('setupGuide').style.display = 'none';
      document.getElementById('credentialsForm').style.display = 'block';
    });
  }

  // Cancel credentials form
  const cancelCredBtn = document.getElementById('cancelCredentials');
  if (cancelCredBtn) {
    cancelCredBtn.addEventListener('click', () => {
      document.getElementById('credentialsForm').style.display = 'none';
      document.getElementById('setupGuide').style.display = 'block';
    });
  }

  // Save credentials
  const saveCredBtn = document.getElementById('saveCredentials');
  if (saveCredBtn) {
    saveCredBtn.addEventListener('click', async () => {
      const clientId = document.getElementById('credClientId')?.value?.trim();
      const clientSecret = document.getElementById('credClientSecret')?.value?.trim();
      const refreshToken = document.getElementById('credRefreshToken')?.value?.trim();
      const resultBox = document.getElementById('credentialsResult');

      if (!clientId || !clientSecret || !refreshToken) {
        if (resultBox) resultBox.innerHTML = '<div style="color:var(--error);">Please fill in all required fields.</div>';
        return;
      }

      saveCredBtn.disabled = true;
      saveCredBtn.textContent = 'Saving...';

      try {
        const response = await fetch(`${normalizeBaseUrl()}/api/amazon/credentials`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            marketplace_id: document.getElementById('credMarketplace')?.value || 'ATVPDKIKX0DER',
            marketplace_name: document.getElementById('credMarketplaceName')?.value || 'Amazon.com',
            client_id: clientId,
            client_secret: clientSecret,
            refresh_token: refreshToken,
            region: document.getElementById('credRegion')?.value || 'na'
          })
        });
        const data = await response.json();
        if (resultBox) {
          if (response.ok) {
            resultBox.innerHTML = `<div style="color:var(--success);"><strong>Saved!</strong> Credentials stored. Click "Check Connection Status" to verify.</div>`;
            document.getElementById('credentialsForm').style.display = 'none';
            document.getElementById('setupGuide').style.display = 'none';
            // Trigger status check
            checkStatusBtn?.click();
          } else {
            resultBox.innerHTML = `<div style="color:var(--error);"><strong>Error:</strong> ${data.detail || 'Failed to save'}</div>`;
          }
        }
      } catch (err) {
        if (resultBox) resultBox.innerHTML = `<div style="color:var(--error);"><strong>Error:</strong> ${err.message}</div>`;
      } finally {
        saveCredBtn.disabled = false;
        saveCredBtn.textContent = 'Save Credentials';
      }
    });
  }

  // Publish listing
  const publishBtn = document.getElementById('publishListing');
  if (publishBtn) {
    publishBtn.addEventListener('click', async () => {
      const listingId = document.getElementById('publishListingSelect')?.value;
      const asin = document.getElementById('publishAsin')?.value?.trim();
      const condition = document.getElementById('publishCondition')?.value;
      const fulfillment = document.getElementById('publishFulfillment')?.value;
      const resultBox = document.getElementById('publishResult');

      if (!listingId) {
        if (resultBox) resultBox.innerHTML = '<div style="color:var(--error);">Please select a listing to publish.</div>';
        return;
      }

      publishBtn.disabled = true;
      publishBtn.textContent = 'Publishing...';

      try {
        // Get listing details from local storage (in real app, from API)
        const listings = {
          '1': { sku: 'KH-204', title: 'Portable Kitchen Storage Set', brand: 'Nexa Home', price: 29.99,
            description: 'Designed for one clean, organized kitchen experience.',
            bullet_points: ['Organize kitchen spaces', 'Durable', 'Compact', 'Easy to store'],
            backend_keywords: ['portable kitchen storage', 'nexa home', 'home kitchen'],
            images: ['/static/images/library/KH-204-main.jpg']
          },
          '2': { sku: 'AP-900', title: 'LED Mobility Lamp', brand: 'BrightNest', price: 39.99,
            description: 'Bright LED lamp for mobility assistance.',
            bullet_points: ['Bright LED', 'Adjustable neck', 'Long battery life'],
            backend_keywords: ['led lamp', 'mobility', 'brightnest'],
            images: ['/static/images/library/AP-900-main.jpg']
          },
          '3': { sku: 'EC-440', title: 'Eco Cleaning Set', brand: 'CleanPro', price: 26.90,
            description: 'Eco-friendly cleaning products set.',
            bullet_points: ['Eco-friendly', 'Non-toxic', 'Multi-surface'],
            backend_keywords: ['cleaning set', 'eco', 'cleanpro'],
            images: ['/static/images/library/EC-440-main.jpg']
          }
        };
        const listing = listings[listingId];
        if (!listing) throw new Error('Listing not found');

        const response = await fetch(`${normalizeBaseUrl()}/api/amazon/listings/publish`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            listing_id: parseInt(listingId),
            sku: listing.sku,
            asin: asin || undefined,
            title: listing.title,
            brand: listing.brand,
            description: listing.description,
            bullet_points: listing.bullet_points,
            backend_keywords: listing.backend_keywords,
            price: listing.price,
            images: listing.images,
            condition_type: condition,
            fulfillment_latency: fulfillment
          })
        });
        const data = await response.json();
        if (resultBox) {
          if (response.ok && data.success) {
            resultBox.innerHTML = `<div style="color:var(--success);"><strong>Published!</strong><br>
              SKU: ${data.sku}<br>
              ASIN: ${data.asin || 'Pending'}<br>
              Status: ${data.status}<br>
              ${data.message}
            </div>`;
          } else {
            resultBox.innerHTML = `<div style="color:var(--error);"><strong>Error:</strong> ${data.detail || data.message || 'Failed to publish'}</div>`;
          }
        }
      } catch (err) {
        if (resultBox) resultBox.innerHTML = `<div style="color:var(--error);"><strong>Error:</strong> ${err.message}</div>`;
      } finally {
        publishBtn.disabled = false;
        publishBtn.textContent = 'Publish to Amazon';
      }
    });
  }

  // Compare listing
  const compareBtn = document.getElementById('compareListing');
  if (compareBtn) {
    compareBtn.addEventListener('click', async () => {
      const listingId = document.getElementById('compareListingSelect')?.value;
      const resultBox = document.getElementById('compareResult');
      const detailPanel = document.getElementById('compareDetailPanel');
      const tableBody = document.getElementById('compareTableBody');
      const listingTitle = document.getElementById('compareListingTitle');

      if (!listingId) {
        if (resultBox) resultBox.innerHTML = '<div style="color:var(--error);">Please select a listing to compare.</div>';
        return;
      }

      compareBtn.disabled = true;
      compareBtn.textContent = 'Comparing...';
      if (resultBox) resultBox.style.display = 'block';

      try {
        const response = await fetch(`${normalizeBaseUrl()}/api/amazon/listings/compare`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ listing_id: parseInt(listingId) })
        });
        const data = await response.json();

        if (response.ok) {
          if (resultBox) resultBox.innerHTML = `<div style="color:var(--success);"><strong>Comparison complete.</strong> ${data.fields.filter(f => f.is_different).length} field(s) differ.</div>`;
          if (detailPanel) detailPanel.style.display = 'block';
          if (listingTitle) listingTitle.textContent = data.sku + (data.asin ? ' (ASIN: ' + data.asin + ')' : '');

          if (tableBody) {
            tableBody.innerHTML = data.fields.map(field => `
              <tr class="${field.is_different ? 'diff' : ''}">
                <td><strong>${field.field}</strong></td>
                <td><pre style="margin:0;white-space:pre-wrap;">${JSON.stringify(field.local_value, null, 2)}</pre></td>
                <td><pre style="margin:0;white-space:pre-wrap;">${JSON.stringify(field.amazon_value, null, 2)}</pre></td>
                <td><span class="status ${field.is_different ? 'error' : 'live'}">${field.is_different ? 'Different' : 'Match'}</span></td>
                <td>
                  ${field.is_different ? `
                    <button class="btn btn-secondary small-padded" onclick="syncFieldFromAmazon(${data.listing_id}, '${field.field}')">
                      Use Amazon Value
                    </button>
                  ` : '<span style="color:var(--muted);">—</span>'}
                </td>
              </tr>
            `).join('');
          }
        } else {
          if (resultBox) resultBox.innerHTML = `<div style="color:var(--error);"><strong>Error:</strong> ${data.detail || 'Comparison failed'}</div>`;
        }
      } catch (err) {
        if (resultBox) resultBox.innerHTML = `<div style="color:var(--error);"><strong>Error:</strong> ${err.message}</div>`;
      } finally {
        compareBtn.disabled = false;
        compareBtn.textContent = 'Compare with Amazon';
      }
    });
  }

  // Close compare panel
  const closeCompareBtn = document.getElementById('closeCompare');
  if (closeCompareBtn) {
    closeCompareBtn.addEventListener('click', () => {
      document.getElementById('compareDetailPanel').style.display = 'none';
      document.getElementById('compareResult').style.display = 'none';
    });
  }

  // Make syncFieldFromAmazon globally accessible
  window.syncFieldFromAmazon = async function(listingId, field) {
    try {
      const response = await fetch(`${normalizeBaseUrl()}/api/amazon/listings/sync-from-amazon/${listingId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ field, use_amazon_value: true })
      });
      const data = await response.json();
      if (response.ok && data.success) {
        alert(`Updated ${field} from Amazon: ${JSON.stringify(data.new_value)}`);
        // Re-run comparison to refresh
        document.getElementById('compareListing')?.click();
      } else {
        alert('Error: ' + (data.detail || 'Failed to sync'));
      }
    } catch (err) {
      alert('Error: ' + err.message);
    }
  };
}

function attachOrdersEvents() {
  // Load orders on page load
  loadOrders();
  loadOrderStats();

  // Sync orders button
  const syncBtn = document.getElementById('syncOrders');
  const syncBtnEmpty = document.getElementById('syncOrdersEmpty');
  const syncHandler = async () => {
    const btn = document.getElementById('syncOrders') || document.getElementById('syncOrdersEmpty');
    if (btn) {
      btn.disabled = true;
      btn.textContent = 'Syncing...';
    }
    try {
      const response = await fetch(`${normalizeBaseUrl()}/api/amazon/orders/sync`, { method: 'POST' });
      const data = await response.json();
      if (response.ok) {
        alert(`Sync complete: ${data.synced} new orders, ${data.updated} updated.`);
        loadOrders();
        loadOrderStats();
      } else {
        alert('Error: ' + (data.detail || 'Sync failed'));
      }
    } catch (err) {
      alert('Error: ' + err.message);
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.textContent = 'Sync from Amazon';
      }
    }
  };
  if (syncBtn) syncBtn.addEventListener('click', syncHandler);
  if (syncBtnEmpty) syncBtnEmpty.addEventListener('click', syncHandler);

  // Refresh orders
  const refreshBtn = document.getElementById('refreshOrders');
  if (refreshBtn) {
    refreshBtn.addEventListener('click', () => {
      loadOrders();
      loadOrderStats();
    });
  }

  // Search and filter
  const searchInput = document.getElementById('ordersSearch');
  const statusFilter = document.getElementById('ordersStatusFilter');
  const sortBy = document.getElementById('ordersSortBy');
  let currentPage = 1;

  async function loadOrders(page = 1) {
    currentPage = page;
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: '25'
    });
    if (searchInput?.value) params.append('search', searchInput.value);
    if (statusFilter?.value) params.append('status_filter', statusFilter.value);
    
    const sortValue = sortBy?.value || 'purchase_date';
    if (sortValue === 'purchase_date') { params.append('sort_by', 'purchase_date'); params.append('sort_order', 'desc'); }
    else if (sortValue === 'purchase_date_asc') { params.append('sort_by', 'purchase_date'); params.append('sort_order', 'asc'); }
    else if (sortValue === 'order_total') { params.append('sort_by', 'order_total'); params.append('sort_order', 'desc'); }
    else if (sortValue === 'profit') { params.append('sort_by', 'profit'); params.append('sort_order', 'desc'); }
    else if (sortValue === 'roi_percent') { params.append('sort_by', 'roi_percent'); params.append('sort_order', 'desc'); }

    const tableBody = document.getElementById('ordersTableBody');
    const emptyState = document.getElementById('ordersEmpty');
    const paginationInfo = document.getElementById('paginationInfo');
    const prevPageBtn = document.getElementById('prevPage');
    const nextPageBtn = document.getElementById('nextPage');

    if (tableBody) tableBody.innerHTML = '<tr><td colspan="10" style="text-align:center;color:var(--muted);">Loading...</td></tr>';

    try {
      const response = await fetch(`${normalizeBaseUrl()}/api/amazon/orders?${params.toString()}`);
      const data = await response.json();

      if (tableBody) {
        if (data.orders && data.orders.length > 0) {
          tableBody.innerHTML = data.orders.map(order => `
            <tr>
              <td><strong>${escapeHtml(order.amazon_order_id)}</strong></td>
              <td>${formatDate(order.purchase_date)}</td>
              <td><span class="status ${getStatusClass(order.order_status)}">${escapeHtml(order.order_status)}</span></td>
              <td>${escapeHtml(order.shipping_address_city || '—')}, ${escapeHtml(order.shipping_address_state || '—')}</td>
              <td>${escapeHtml(order.shipping_address_city || '')}, ${escapeHtml(order.shipping_address_state || '')}, ${escapeHtml(order.shipping_address_country || '')}</td>
              <td>${order.number_of_items}</td>
              <td>$${order.order_total.toFixed(2)}</td>
              <td>$${order.amazon_fees.toFixed(2)}</td>
              <td style="color:${order.profit >= 0 ? 'var(--success)' : 'var(--error)'};">$${order.profit.toFixed(2)}</td>
              <td>${order.roi_percent.toFixed(1)}%</td>
            </tr>
          `).join('');
          if (emptyState) emptyState.style.display = 'none';
        } else {
          tableBody.innerHTML = '';
          if (emptyState) emptyState.style.display = 'block';
        }
      }

      if (paginationInfo) {
        paginationInfo.textContent = `Page ${data.page} of ${data.total_pages} (${data.total} total)`;
      }
      if (prevPageBtn) prevPageBtn.disabled = data.page <= 1;
      if (nextPageBtn) nextPageBtn.disabled = data.page >= data.total_pages;

      // Pagination handlers
      if (prevPageBtn) {
        prevPageBtn.onclick = () => loadOrders(currentPage - 1);
      }
      if (nextPageBtn) {
        nextPageBtn.onclick = () => loadOrders(currentPage + 1);
      }
    } catch (err) {
      if (tableBody) tableBody.innerHTML = `<tr><td colspan="10" style="text-align:center;color:var(--error);">Error loading orders: ${err.message}</td></tr>`;
    }
  }

  function loadOrderStats() {
    fetch(`${normalizeBaseUrl()}/api/amazon/orders/stats`)
      .then(r => r.json())
      .then(data => {
        const setText = (id, value) => { const el = document.getElementById(id); if (el) el.textContent = value; };
        setText('statTotalOrders', data.total_orders || 0);
        setText('statShipped', data.shipped || 0);
        setText('statUnshipped', data.unshipped || 0);
        setText('statCancelled', data.cancelled || 0);
        setText('statRevenue', '$' + (data.total_revenue || 0).toFixed(2));
        setText('statFees', '$' + (data.total_fees || 0).toFixed(2));
        setText('statProfit', '$' + (data.total_profit || 0).toFixed(2));
        setText('statRoi', (data.avg_roi || 0).toFixed(1) + '%');
      })
      .catch(() => {});
  }

  // Debounced search
  let searchTimeout;
  if (searchInput) {
    searchInput.addEventListener('input', () => {
      clearTimeout(searchTimeout);
      searchTimeout = setTimeout(() => loadOrders(1), 300);
    });
  }
  if (statusFilter) {
    statusFilter.addEventListener('change', () => loadOrders(1));
  }
  if (sortBy) {
    sortBy.addEventListener('change', () => loadOrders(1));
  }
}

function getStatusClass(status) {
  switch (status) {
    case 'Shipped': return 'live';
    case 'Unshipped': return 'review';
    case 'Pending': return 'review';
    case 'Cancelled': return 'error';
    default: return '';
  }
}

function formatDate(dateStr) {
  try {
    return new Date(dateStr).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  } catch { return dateStr; }
}

function attachChatEvents() {
  const chatToggle = document.getElementById('chatToggle');
  const chatClose = document.getElementById('chatClose');
  const chatSend = document.getElementById('chatSend');
  const chatInput = document.getElementById('chatInput');
  const chatModal = document.getElementById('chatModal');
  const chatMessages = document.getElementById('chatMessages');

  if (!chatToggle || !chatClose || !chatSend || !chatInput || !chatModal || !chatMessages) {
    return;
  }

  let chatHistory = [];

  function openChat() {
    chatModal.style.display = 'flex';
    chatInput.focus();
  }

  function closeChat() {
    chatModal.style.display = 'none';
  }

  function addMessage(role, content) {
    const div = document.createElement('div');
    div.className = `chat-message ${role}`;
    div.innerHTML = `<div class="chat-bubble">${escapeHtml(content)}</div>`;
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function showLoading() {
    const div = document.createElement('div');
    div.className = 'chat-message assistant';
    div.id = 'chatLoading';
    div.innerHTML = `<div class="chat-bubble chat-loading"><span></span><span></span><span></span></div>`;
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function hideLoading() {
    const loading = document.getElementById('chatLoading');
    if (loading) loading.remove();
  }

  function getPageContext() {
    const page = state.page;
    const contexts = {
      dashboard: 'Dashboard — overview of your Amazon business: sales, listings, profit, and items needing attention.',
      sourcing: 'Add New Product — choose how to add products: (1) Add One Product by pasting a link, (2) Import from Spreadsheet (CSV/Excel), (3) Fetch from eBay Seller (pull all products from a seller\'s store). The product queue on the right shows items added but not yet submitted.',
      listings: 'All Listings — view and manage every product listing (drafts, live on Amazon, needing review). Filter by status: All, Drafts, or Live.',
      detail: 'Listing Detail — review and complete all product details before submitting to Amazon. Tabs: Product Details, Images, Offer & Pricing, Safety & Compliance. Use Auto-fill, AI Content, and Image Studio buttons.',
      analytics: 'Catalog Analytics — see which products drive revenue, which are losing money, and what needs attention. View revenue concentration, best performers, and dead stock.',
      categories: 'Category Explorer — find the right Amazon category for your product. Browse the category tree and see your listings by category.',
      variations: 'Variations — group related products (sizes, colors, styles) under one Amazon listing. Create and manage variation sets.',
      imageStudio: 'AI Image Studio — create product images with AI. Choose mode (creative, main, secondary, A+), set fidelity and standing instructions, generate and assign images to listing slots.',
      imageLibrary: 'Image Library — all your generated and uploaded product images in one place. Filter by listing, slot, or status (Active, Draft, Queued).',
      imageReferences: 'Image References — save reference images (from suppliers, competitors, brand guidelines) to guide AI image generation. Set visual style, brand colors, and notes for AI.',
      repricer: 'Repricer — automatically adjust Amazon prices when supplier costs change. Set profit rule (percentage or fixed), system watches supplier links and maintains your margin.',
      amazonIntegration: 'Amazon Integration — connect your Amazon Seller Central via SP-API. Add credentials (Client ID, Client Secret, Refresh Token), publish listings, and compare local data with Amazon live data.',
      orders: 'Orders — view and manage all Amazon orders. Sync from SP-API, filter by status, search by order ID or destination, sort by date/revenue/profit/ROI. View order details including items, fees, and profit.'
    };
    return contexts[page] || 'Sellrix page';
  }

  // Help content for each page
  const helpContent = {
    dashboard: {
      title: 'Dashboard',
      body: `<p><strong>What this page is for:</strong> Your Amazon business at a glance.</p>
        <p><strong>Main sections:</strong></p>
        <ul>
          <li><strong>KPIs</strong> — Monthly revenue, active listings, profit margin, items needing attention</li>
          <li><strong>Products in progress</strong> — Draft listings being worked on (not live yet)</li>
          <li><strong>Account health</strong> — Listing quality, Amazon sync, content quality scores</li>
        </ul>
        <p><strong>Important:</strong> Green = good, Orange = needs work, Red = urgent. Use the sidebar to navigate to Sourcing (add products), Listings (manage all), or other tools.</p>`
    },
    sourcing: {
      title: 'Add New Product',
      body: `<p><strong>What this page is for:</strong> Add products to your queue using one of three methods.</p>
        <p><strong>Three ways to add products:</strong></p>
        <ul>
          <li><strong>Add One Product</strong> — Paste a product link (from supplier, eBay, AliExpress, etc.) and we'll fetch the title and image automatically. Fill in your cost and sell price, then click "Add to Queue".</li>
          <li><strong>Import from Spreadsheet</strong> — Download the template, fill in your product data (source link, cost, etc.), upload the CSV/Excel file, and we'll process all rows at once. Required: Source link and Cost.</li>
          <li><strong>Fetch from eBay Seller</strong> — Enter an eBay store link or username. We'll pull all their listings, auto-skip compliance-risk items, and let you choose which to add to your queue.</li>
        </ul>
        <p><strong>Important:</strong> The source link is required — we use it to get the product's title and photo automatically. Your product queue on the right shows everything you've added but not yet submitted to Amazon.</p>`
    },
    listings: {
      title: 'All Listings',
      body: `<p><strong>What this page is for:</strong> View and manage every product listing.</p>
        <p><strong>Main actions:</strong></p>
        <ul>
          <li><strong>Tabs</strong> — Switch between All listings / Drafts (not submitted) / Live on Amazon</li>
          <li><strong>Filter listings</strong> — Narrow down by status, category, etc.</li>
          <li><strong>Add new product</strong> — Go to the Sourcing page to add more products</li>
        </ul>
        <p><strong>Status badges:</strong> Draft (not submitted), Live on Amazon, Needs your review, Amazon rejected. Click any listing to review details.</p>`
    },
    detail: {
      title: 'Listing Detail',
      body: `<p><strong>What this page is for:</strong> Review and complete all product details before submitting to Amazon.</p>
        <p><strong>Four tabs:</strong></p>
        <ul>
          <li><strong>Product Details</strong> — Title, brand, condition, bullets, description, backend keywords</li>
          <li><strong>Images</strong> — Manage product images (Main, lifestyle, A+ modules)</li>
          <li><strong>Offer & Pricing</strong> — Your cost, sell price, handling time, barcode, pricing method</li>
          <li><strong>Safety & Compliance</strong> — Compliance checks (restricted categories, claim risk, required documents)</li>
        </ul>
        <p><strong>Key buttons:</strong> Auto-fix (auto-populate from source link and AI), Generate AI content (create listing text), Open Image Studio (create images). When ready, click Submit to Amazon.</p>`
    },
    analytics: {
      title: 'Catalog Analytics',
      body: `<p><strong>What this page is for:</strong> See what drives your business — revenue, profit, and problem products.</p>
        <p><strong>Key metrics:</strong></p>
        <ul>
          <li><strong>Revenue concentration</strong> — % of revenue from top 5 products (high = consider diversifying)</li>
          <li><strong>Best performer</strong> — Your highest-revenue product</li>
          <li><strong>Dead stock</strong> — Products with zero sales for 90+ days (consider repricing or removing)</li>
          <li><strong>Product performance table</strong> — Ranked by revenue with units sold, profit, ROI, and status</li>
        </ul>
        <p><strong>Important:</strong> ROI = profit ÷ cost. Higher is better. Filter by time period using the dropdown.</p>`
    },
    categories: {
      title: 'Category Explorer',
      body: `<p><strong>What this page is for:</strong> Find the right Amazon category for your product.</p>
        <p><strong>Main actions:</strong></p>
        <ul>
          <li>Browse the Amazon category tree (click to expand)</li>
          <li>Each category shows selling requirements, fees, and required product attributes</li>
          <li>See your active listings count by top-level category</li>
        </ul>
        <p><strong>Important:</strong> The correct category affects fees, visibility, and what info Amazon requires. Click "Browse full category tree" for more.</p>`
    },
    variations: {
      title: 'Variations',
      body: `<p><strong>What this page is for:</strong> Group related products (sizes, colors, styles) under one Amazon listing.</p>
        <p><strong>How it works:</strong></p>
        <ul>
          <li>Each group = one parent listing with multiple child options (size, color, style)</li>
          <li>Customers see all options on a single product page</li>
          <li>Click "Create variation set" to start a new group</li>
          <li>Status shows if synced on Amazon or needs review</li>
        </ul>
        <p><strong>Why use variations:</strong> Customers pick their option without leaving the page.</p>`
    },
    imageStudio: {
      title: 'AI Image Studio',
      body: `<p><strong>What this page is for:</strong> Create product images with AI.</p>
        <p><strong>Tabs:</strong> Creative concepts / Main image (white background) / Secondary images / A+ Content modules</p>
        <p><strong>Settings:</strong> Fidelity (higher = closer to real product), image slot, secondary approach (AI suggest vs manual), template</p>
        <p><strong>Workflow:</strong> Generate image → Assign to listing slot → Add to your product</p>
        <p><strong>Important:</strong> Main images MUST be on pure white background per Amazon rules.</p>`
    },
    imageLibrary: {
      title: 'Image Library',
      body: `<p><strong>What this page is for:</strong> All your generated and uploaded product images in one place.</p>
        <p><strong>Filter by:</strong> Listing, image slot (Main, Image 1-4, A+), or status (Active, Draft, Queued)</p>
        <p><strong>Status meanings:</strong> Active = assigned to live listing, Draft = saved but not assigned, Queued = processing</p>
        <p><strong>Actions:</strong> Create new images (go to Image Studio), Upload image set, Download as ZIP</p>`
    },
    imageReferences: {
      title: 'Image References',
      body: `<p><strong>What this page is for:</strong> Save reference images to guide AI image generation.</p>
        <p><strong>What to add:</strong> Images from suppliers, competitors, or brand guidelines</p>
        <p><strong>Settings:</strong> Visual style (clean white, lifestyle, infographic), brand colors, notes for AI</p>
        <p><strong>Why use references:</strong> They tell the AI what style, angle, and composition you want. Click "Generate test image" to preview the style.</p>`
    },
    repricer: {
      title: 'Repricer',
      body: `<p><strong>What this page is for:</strong> Automatically adjust Amazon prices when supplier costs change.</p>
        <p><strong>Profit rule (applies to all products):</strong> Percentage (e.g., "keep 20% margin") or Fixed amount (e.g., "$5 profit")</p>
        <p><strong>How it works:</strong> System watches your supplier links, finds the cheapest <strong>in-stock</strong> source, sets your Amazon price to maintain your margin.</p>
        <p><strong>Each product shows:</strong> Current Amazon price, cheapest in-stock supplier, status (Auto-priced / No source available)</p>
        <p><strong>Important:</strong> Only in-stock sources are considered — out-of-stock competitors are ignored. Click "Check supplier prices now" to refresh.</p>`
    },
    amazonIntegration: {
      title: 'Amazon Integration',
      body: `<p><strong>What this page is for:</strong> Connect your Amazon Seller Central account via SP-API to publish listings and sync live data.</p>
        <p><strong>Setup required:</strong></p>
        <ol>
          <li>Have a <strong>Professional Seller account</strong> on Amazon</li>
          <li>Go to <strong>Seller Central > Apps & Services > Develop Apps</strong></li>
          <li>Register a new app, add SP-API roles (Orders, Listings, Catalog, Reports)</li>
          <li>Get <strong>Client ID</strong>, <strong>Client Secret</strong>, and authorize to get <strong>Refresh Token</strong></li>
          <li>Enter all three in the Credentials section below</li>
        </ol>
        <p><strong>Features:</strong></p>
        <ul>
          <li><strong>Publish Listing</strong> — Send a completed, validated listing live to Amazon</li>
          <li><strong>Compare with Amazon</strong> — Pull Amazon's live version, see field-by-field differences, choose which side wins per field</li>
        </ul>
        <p><strong>Note:</strong> Without real credentials, the app runs in mock/demo mode showing sample data.</p>`
    },
    orders: {
      title: 'Orders',
      body: `<p><strong>What this page is for:</strong> View and manage all Amazon orders synced from SP-API.</p>
        <p><strong>Main features:</strong></p>
        <ul>
          <li><strong>Sync from Amazon</strong> — Fetch latest orders via SP-API (orders, items, fees, profit)</li>
          <li><strong>Filter & Search</strong> — By status (Shipped/Unshipped/Cancelled), order ID, city, state</li>
          <li><strong>Sort</strong> — By date, revenue, profit, ROI%</li>
          <li><strong>Stats cards</strong> — Total orders, shipped/unshipped/cancelled counts, revenue, fees, profit, avg ROI%</li>
        </ul>
        <p><strong>Columns:</strong> Order ID, Date, Status, Customer, Destination, Items, Revenue, Fees, Profit, ROI%</p>
        <p><strong>Note:</strong> Profit and fees are estimated (15% referral + FBA fees). For exact numbers, connect real SP-API credentials.</p>`
    },
  };

  function openHelp() {
    const page = state.page;
    const content = helpContent[page] || { title: 'Help', body: '<p>No help available for this page.</p>' };
    const modal = document.getElementById('helpModal');
    const body = document.getElementById('helpModalBody');
    if (modal && body) {
      body.innerHTML = `<h3>${content.title}</h3>${content.body}`;
      modal.style.display = 'flex';
    }
  }

  function closeHelp() {
    const modal = document.getElementById('helpModal');
    if (modal) modal.style.display = 'none';
  }

  async function sendMessage() {
    const message = chatInput.value.trim();
    if (!message) return;

    addMessage('user', message);
    chatHistory.push({ role: 'user', content: message });
    chatInput.value = '';
    chatSend.disabled = true;
    showLoading();

    try {
      const response = await fetch(`${normalizeBaseUrl()}/api/assistant/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${state.token}` },
        body: JSON.stringify({
          messages: chatHistory.slice(0, -1),
          user_message: message,
          page_context: getPageContext()
        })
      });
      const data = await response.json();
      hideLoading();
      if (data.response) {
        addMessage('assistant', data.response);
        chatHistory.push({ role: 'assistant', content: data.response });
      } else {
        addMessage('assistant', 'Sorry, I couldn\'t generate a response. Please try again.');
      }
    } catch (err) {
      hideLoading();
      addMessage('assistant', 'Network error. Please try again.');
    } finally {
      chatSend.disabled = false;
      chatInput.focus();
    }
  }

  chatToggle.addEventListener('click', openChat);
  chatClose.addEventListener('click', closeChat);
  chatSend.addEventListener('click', sendMessage);
  chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') sendMessage();
  });

  chatModal.addEventListener('click', (e) => {
    if (e.target === chatModal) closeChat();
  });

  // Help button events
  const helpBtn = document.getElementById('helpBtn');
  const helpModalClose = document.getElementById('helpModalClose');
  const helpModal = document.getElementById('helpModal');

  if (helpBtn) {
    helpBtn.addEventListener('click', openHelp);
  }
  if (helpModalClose) {
    helpModalClose.addEventListener('click', closeHelp);
  }
  if (helpModal) {
    helpModal.addEventListener('click', (e) => {
      if (e.target === helpModal || e.target.classList.contains('help-modal-overlay')) {
        closeHelp();
      }
    });
  }
}

function escapeHtml(text) {
  const map = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;'
  };
  return text.replace(/[&<>"']/g, m => map[m]);
}

function render() {
  if (state.page === 'login' || !state.user) {
    app.innerHTML = renderLoginPage();
    attachAuthEvents();
  } else {
    app.innerHTML = renderShell();
    attachDashboardEvents();
  }
}

if (state.user) {
  state.page = 'dashboard';
  render();
} else {
  state.page = 'login';
  render();
}


