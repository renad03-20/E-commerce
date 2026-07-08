document.getElementById('import-btn').addEventListener('click', async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  
  chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: scrapeAliExpressPage
  }, (results) => {
    if (!results || !results[0]) return;
    
    // Send the scraped data to your Django Backend
    fetch('http://127.0.0.1:8000/api/admin/import-product/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(results[0].result)
    })
    .then(res => res.json())
    .then(data => alert('Product imported successfully!'))
    .catch(err => alert('Error importing product. Check console.'));
  });
});

// This function runs directly inside the AliExpress webpage context
function scrapeAliExpressPage() {
  const title = document.querySelector('.slider--title--v21W16A')?.innerText || "Unknown Product";
  const priceText = document.querySelector('.price--currentPriceText--S6eV71g')?.innerText || "0.00";
  const firstImage = document.querySelector('.magnifier--image--G6g6EAG')?.src || "";

  return {
    title: title,
    price: priceText.replace(/[^0-9.]/g, ''), // Strip currency symbols
    image_url: firstImage,
    source_url: window.location.href
  };
}