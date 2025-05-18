document.getElementById('generate-btn').addEventListener('click', async () => {
  const prompt = tinymce.get('editor').getContent({ format: 'text' });
  const res = await fetch('/generate_post', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt })
  });
  const data = await res.json();
  tinymce.get('editor').setContent(data.post);
});

// The serp_search.js file is already linked in the HTML template
