document.getElementById('search-btn').addEventListener('click', async () => {
  const q = document.getElementById('search-bar').value;
  if (!q) {
    alert('Please enter a search query');
    return;
  }

  const searchBtn = document.getElementById('search-btn');
  const container = document.getElementById('search-results');
  
  // Show loading state
  searchBtn.disabled = true;
  searchBtn.textContent = 'Searching...';
  container.innerHTML = '<p>Loading results...</p>';
  
  try {
    const res = await fetch(`/search?q=${encodeURIComponent(q)}`);
    const data = await res.json();
    
    // Handle error response from server
    if (data.error) {
      container.innerHTML = `<p class="error">Error: ${data.error}</p>`;
      return;
    }
    
    // Handle empty results
    if (!Array.isArray(data) || data.length === 0) {
      container.innerHTML = '<p>No results found</p>';
      return;
    }
    
    // Display results
    container.innerHTML = data.map(r => `
      <div class="search-result">
        <h3><a href="${r.link}" target="_blank">${r.title || 'No title'}</a></h3>
        <p>${r.snippet || r.description || ''}</p>
        <small>${r.link || ''}</small>
      </div>
    `).join('');
  } catch (error) {
    console.error('Search error:', error);
    container.innerHTML = '<p class="error">Error performing search. Please try again later.</p>';
  } finally {
    // Reset button state
    searchBtn.disabled = false;
    searchBtn.textContent = 'Search';
  }
});

// Add clear button functionality
document.getElementById('clear-btn').addEventListener('click', () => {
  // Clear the search results
  document.getElementById('search-results').innerHTML = '';
  
  // Clear the search input
  document.getElementById('search-bar').value = '';
  
  // Focus on the search input for better UX
  document.getElementById('search-bar').focus();
});
