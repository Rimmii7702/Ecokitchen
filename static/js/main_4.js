document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const dropArea = document.getElementById('dropArea');
    const fileInput = document.getElementById('fileInput');
    const previewImage = document.getElementById('previewImage');
    const uploadForm = document.getElementById('uploadForm');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const resultsContainer = document.getElementById('resultsContainer');
    const newAnalysisBtn = document.getElementById('newAnalysisBtn');
    const uploadBtn = document.getElementById('uploadBtn');
    const statusDot = document.getElementById('statusDot');
    const wasteLevel = document.getElementById('wasteLevel');
    
    // Click on upload area to trigger file input
    if (dropArea) {
        dropArea.addEventListener('click', function() {
            fileInput.click();
        });
        
        // Handle drag and drop
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropArea.addEventListener(eventName, preventDefaults, false);
        });
        
        ['dragenter', 'dragover'].forEach(eventName => {
            dropArea.addEventListener(eventName, highlight, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            dropArea.addEventListener(eventName, unhighlight, false);
        });
        
        // Handle dropped files
        dropArea.addEventListener('drop', function(e) {
            const dt = e.dataTransfer;
            const files = dt.files;
            
            if (files.length) {
                fileInput.files = files;
                updatePreview(files[0]);
            }
        });
    }
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    function highlight() {
        dropArea.classList.add('highlight');
    }
    
    function unhighlight() {
        dropArea.classList.remove('highlight');
    }
    
    // Handle file selection
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            if (fileInput.files.length) {
                updatePreview(fileInput.files[0]);
            }
        });
    }
    
    // Update image preview
    function updatePreview(file) {
        if (file) {
            const reader = new FileReader();
            
            reader.onload = function(e) {
                previewImage.src = e.target.result;
                previewImage.style.display = 'block';
            };
            
            reader.readAsDataURL(file);
        }
    }
    
    // Form submission
    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            if (!fileInput.files.length) {
                e.preventDefault();
                alert('Please select an image first.');
                return;
            }
            
            loadingSpinner.style.display = 'block';
        });
    }
    
    // New analysis button
    if (newAnalysisBtn) {
        newAnalysisBtn.addEventListener('click', function() {
            resultsContainer.style.display = 'none';
            previewImage.style.display = 'none';
            fileInput.value = '';
            uploadForm.reset();
        });
    }
    
    // Check if results should be displayed (if we have results from backend)
    if (resultsContainer && document.getElementById('wasteCategory').textContent !== 'N/A') {
        resultsContainer.style.display = 'block';
        if (loadingSpinner) {
            loadingSpinner.style.display = 'none';
        }

        // Set status dot color based on waste level
        if (statusDot && wasteLevel) {
            const level = wasteLevel.textContent.trim().toLowerCase().split(' ')[0];
            statusDot.className = "status-dot status-" + level;
        }
    }
});



// dashboard static data

// Static Data
const data = {
    inventory: [
      { product: "Item A", category: "Food", stock: 50, lowStockThreshold: 20, unitPrice: 10 },
      { product: "Item B", category: "Beverage", stock: 10, lowStockThreshold: 15, unitPrice: 15 },
      { product: "Item C", category: "Medicine", stock: 30, lowStockThreshold: 10, unitPrice: 20 }
    ],
    sales: [
      { date: "2025-04-01", product: "Item A", amount: 200 },
      { date: "2025-04-02", product: "Item B", amount: 150 },
      { date: "2025-04-03", product: "Item A", amount: 300 },
      { date: "2025-04-04", product: "Item C", amount: 250 }
    ],
    expiry: [
      { product: "Item A", expiryDate: "2025-04-20", daysToExpiry: 8 },
      { product: "Item B", expiryDate: "2025-04-15", daysToExpiry: 3 },
      { product: "Item C", expiryDate: "2025-05-01", daysToExpiry: 19 }
    ]
  };
  
  // Populate KPIs
  const totalInventoryValue = data.inventory.reduce((sum, item) => sum + item.stock * item.unitPrice, 0);
  document.getElementById("totalInventory").textContent = `$${totalInventoryValue.toLocaleString()}`;
  const totalSales = data.sales.reduce((sum, item) => sum + item.amount, 0);
  document.getElementById("totalSales").textContent = `$${totalSales.toLocaleString()}`;
  const nearExpiryCount = data.expiry.filter(item => item.daysToExpiry <= 7).length;
  document.getElementById("nearExpiry").textContent = nearExpiryCount;
  
  // Populate Inventory Table
  const inventoryTableBody = document.querySelector("#inventoryTable tbody");
  data.inventory.forEach(item => {
    const row = inventoryTableBody.insertRow();
    row.insertCell(0).textContent = item.product;
    row.insertCell(1).textContent = item.category;
    row.insertCell(2).textContent = item.stock;
    const statusCell = row.insertCell(3);
    statusCell.textContent = item.stock <= item.lowStockThreshold ? "Low Stock" : "Sufficient";
    statusCell.className = item.stock <= item.lowStockThreshold ? "status-low" : "status-safe";
  });
  
  // Populate Sales Table
  const salesTableBody = document.querySelector("#salesTable tbody");
  data.sales.forEach(item => {
    const row = salesTableBody.insertRow();
    row.insertCell(0).textContent = item.date;
    row.insertCell(1).textContent = item.product;
    row.insertCell(2).textContent = item.amount.toLocaleString();
  });
  
  // Populate Expiry Table
  const expiryTableBody = document.querySelector("#expiryTable tbody");
  data.expiry.forEach(item => {
    const row = expiryTableBody.insertRow();
    row.insertCell(0).textContent = item.product;
    row.insertCell(1).textContent = item.expiryDate;
    row.insertCell(2).textContent = item.daysToExpiry;
    const statusCell = row.insertCell(3);
    statusCell.textContent = item.daysToExpiry <= 0 ? "Expired" : item.daysToExpiry <= 7 ? "Near Expiry" : "Safe";
    statusCell.className = item.daysToExpiry <= 0 ? "status-expired" : item.daysToExpiry <= 7 ? "status-warning" : "status-safe";
  });
  
  // Inventory Chart (Interactive Bar)
  new Chart(document.getElementById("inventoryChart"), {
    type: "bar",
    data: {
      labels: data.inventory.map(item => item.product),
      datasets: [
        {
          label: "Stock Levels",
          data: data.inventory.map(item => item.stock),
          backgroundColor: ["#3B82F6", "#DC2626", "#16A34A"],
          borderRadius: 5,
          hoverBackgroundColor: ["#2563EB", "#B91C1C", "#15803D"]
        },
        {
          label: "Low Stock Threshold",
          data: data.inventory.map(item => item.lowStockThreshold),
          backgroundColor: "rgba(255, 99, 132, 0.3)",
          borderRadius: 5,
          hoverBackgroundColor: "rgba(255, 99, 132, 0.5)"
        }
      ]
    },
    options: {
      plugins: {
        title: { display: true, text: "Inventory Levels", font: { size: 16 } },
        tooltip: {
          enabled: true,
          mode: 'index',
          intersect: false,
          callbacks: {
            label: context => `${context.dataset.label}: ${context.raw}`
          }
        },
        legend: { display: true, position: 'top', labels: { font: { size: 12 } } }
      },
      scales: {
        y: { beginAtZero: true, title: { display: true, text: "Units" } },
        x: { title: { display: true, text: "Products" } }
      },
      animation: { duration: 1000 },
      responsive: true,
      maintainAspectRatio: false
    }
  });
  
  // Sales Chart (Interactive Line)
  const salesByProduct = {};
  data.sales.forEach(item => {
    if (!salesByProduct[item.product]) salesByProduct[item.product] = [];
    salesByProduct[item.product].push({ date: item.date, amount: item.amount });
  });
  
  const salesDatasets = Object.keys(salesByProduct).map((product, index) => ({
    label: product,
    data: data.sales.filter(sale => sale.product === product).map(sale => sale.amount),
    borderColor: ["#3B82F6", "#DC2626", "#16A34A"][index % 3],
    backgroundColor: ["rgba(59, 130, 246, 0.2)", "rgba(220, 38, 38, 0.2)", "rgba(22, 163, 74, 0.2)"][index % 3],
    fill: true,
    tension: 0.4,
    pointHoverRadius: 8
  }));
  
  new Chart(document.getElementById("salesChart"), {
    type: "line",
    data: {
      labels: [...new Set(data.sales.map(item => item.date))].sort(),
      datasets: salesDatasets
    },
    options: {
      plugins: {
        title: { display: true, text: "Sales Trend by Product", font: { size: 16 } },
        tooltip: {
          enabled: true,
          mode: 'index',
          intersect: false,
          callbacks: {
            label: context => `${context.dataset.label}: $${context.raw}`
          }
        },
        legend: { display: true, position: 'top', labels: { font: { size: 12 } } }
      },
      scales: {
        y: { beginAtZero: true, title: { display: true, text: "Amount ($)" } },
        x: { title: { display: true, text: "Date" } }
      },
      animation: { duration: 1000 },
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'nearest', axis: 'x', intersect: false }
    }
  });
  
  // Expiry Chart (Interactive Pie)
  const expiryStatus = data.expiry.reduce((acc, item) => {
    if (item.daysToExpiry <= 0) acc.expired++;
    else if (item.daysToExpiry <= 7) acc.nearExpiry++;
    else acc.safe++;
    return acc;
  }, { expired: 0, nearExpiry: 0, safe: 0 });
  
  new Chart(document.getElementById("expiryChart"), {
    type: "pie",
    data: {
      labels: ["Expired", "Near Expiry (≤7 days)", "Safe (>7 days)"],
      datasets: [{
        data: [expiryStatus.expired, expiryStatus.nearExpiry, expiryStatus.safe],
        backgroundColor: ["#DC2626", "#F59E0B", "#16A34A"],
        hoverBackgroundColor: ["#B91C1C", "#D97706", "#15803D"],
        borderWidth: 1
      }]
    },
    options: {
      plugins: {
        title: { display: true, text: "Expiry Status", font: { size: 16 } },
        tooltip: {
          enabled: true,
          callbacks: {
            label: context => `${context.label}: ${context.raw} item(s)`
          }
        },
        legend: { display: true, position: 'top', labels: { font: { size: 12 } } }
      },
      animation: { duration: 1000 },
      responsive: true,
      maintainAspectRatio: false
    }
  });