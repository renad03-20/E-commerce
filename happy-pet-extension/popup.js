document.getElementById('import-btn').addEventListener('click', async () => {
  const statusText = document.getElementById('status');
  statusText.textContent = "Scraping product and variants...";

  try {
    let [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    chrome.scripting.executeScript({
      target: { tabId: tab.id },
      function: scrapeAndSendProduct,
    });
    
    statusText.textContent = "Action triggered. Check page alerts.";
  } catch (error) {
    statusText.textContent = "Error: Cannot access tab.";
  }
});

// This function runs IN THE CONTEXT OF THE SUPPLIER'S WEBPAGE
async function scrapeAndSendProduct() {
  try {
    const title = document.querySelector('h1')?.innerText || 'Unknown Product';
    const sourceUrl = window.location.href;
    
    // Grab the base price shown on the page
    const priceText = document.querySelector('.price, [class*="price"]')?.innerText || '0.00';
    const basePrice = parseFloat(priceText.replace(/[^0-9.]/g, '')) || 0.00;

    let variants = [];

    // CSS Selectors for variant options. 
    // 'sku-property-item' is common on AliExpress. We also look for generic 'variant' classes.
    const variantElements = document.querySelectorAll('.sku-property-item, [class*="sku-item"], [class*="variant-option"]');

    if (variantElements.length > 0) {
      // Loop through the found variant buttons and extract their details
      variantElements.forEach((el, index) => {
        // Try to get text first, if it's an image-only variant, grab the image alt tag
        let variantName = el.innerText.trim();
        if (!variantName) {
           const img = el.querySelector('img');
           variantName = img ? img.alt : `Option ${index + 1}`;
        }

        // Clean up the name in case of weird formatting
        variantName = variantName.replace(/\n/g, ' ').trim();

        variants.push({
          name: variantName,
          price: basePrice, // Assigning base price. You can adjust retail margins in Django admin later.
          supplier_sku: `AUTO-${Math.random().toString(36).substr(2, 9)}`, // Temp SKU
          stock_quantity: 100
        });
      });
    } else {
      // Fallback: If no variants are found on the page, create a default one
      variants.push({
        name: "Default",
        price: basePrice,
        supplier_sku: `AUTO-DEFAULT-${Math.random().toString(36).substr(2, 5)}`,
        stock_quantity: 100
      });
    }

    // Build the payload
    const productData = {
      title: title,
      source_url: sourceUrl,
      variants: variants // We are now sending the array of extracted variants
    };

    // Send to your Django backend
    const response = await fetch('http://localhost:8000/api/inventory/import-product/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(productData)
    });
    
    const result = await response.json();

    if (response.ok) {
      alert(`Success! Imported product with ${variants.length} variant(s).`);
    } else {
      alert(`Failed to import: ${result.error || 'Unknown error'}`);
    }
  } catch (error) {
    alert('Network error: Could not reach the Happy Pet backend. Is the Django server running?');
  }
}