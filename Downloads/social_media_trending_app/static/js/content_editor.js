// Social Media Content Creator JavaScript

document.addEventListener('DOMContentLoaded', () => {
  // When the form is submitted
  document.getElementById('contentForm').addEventListener('submit', function(event) {
    event.preventDefault();
    
    const action = document.activeElement.value;
    if (action === 'generate') {
      generateContent();
    } else if (action === 'save') {
      saveContent();
    }
  });
  
  // Clear button
  document.getElementById('clearBtn').addEventListener('click', function() {
    tinymce.get('editor').setContent('');
    document.getElementById('topic').value = '';
    document.getElementById('cta').value = '';
    currentBlogSnippet = '';
    document.getElementById('toggleBlogBtn').disabled = true;
  });
  
  // Toggle blog snippet button
  document.getElementById('toggleBlogBtn').addEventListener('click', function() {
    toggleBlogSnippet();
  });
  
  // Initialize the toggle button as disabled until we have content
  document.getElementById('toggleBlogBtn').disabled = true;
    // Store the blog snippet separately
  let currentBlogSnippet = '';
  let isBlogSnippetVisible = true;
  
  // Generate content function
  function generateContent() {
    const platform = document.getElementById('platform').value;
    const tone = document.getElementById('tone').value;
    const topic = document.getElementById('topic').value;
    const cta = document.getElementById('cta').value;
    const length = document.getElementById('length').value;
    const emojiLevel = document.getElementById('emoji_level').value;
    
    if (!topic) {
      alert('Please enter a topic for your content.');
      return;
    }
    
    // Show loading state
    const generateBtn = document.querySelector('button[value="generate"]');
    const originalText = generateBtn.textContent;
    generateBtn.disabled = true;
    generateBtn.textContent = 'Generating...';
    
    fetch('/generate_social_content', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        platform: platform,
        tone: tone,
        topic: topic,
        cta: cta,
        length_hint: length,
        emoji_level: emojiLevel
      })
    })
    .then(response => response.json())
    .then(data => {
      if (data.platform_post) {
        tinymce.get('editor').setContent(data.platform_post);
        
        // Store the blog snippet but only show if visible
        if (data.blog_snippet) {
          currentBlogSnippet = data.blog_snippet;
          
          if (isBlogSnippetVisible) {
            tinymce.get('editor').setContent(
              tinymce.get('editor').getContent() + 
              '<div id="blog-snippet-container" class="blog-snippet">' +
              '<hr><h3>Blog Snippet:</h3>' + 
              data.blog_snippet +
              '</div>'
            );
          }
          
          // Enable the toggle button if we have a blog snippet
          const toggleBtn = document.getElementById('toggleBlogBtn');
          toggleBtn.disabled = false;
          if (isBlogSnippetVisible) {
            toggleBtn.classList.add('toggle-active');
          } else {
            toggleBtn.classList.remove('toggle-active');
          }
        }
      } else if (data.error) {
        alert('Error: ' + data.error);
      }
      
      generateBtn.disabled = false;
      generateBtn.textContent = originalText;
    })
    .catch(error => {
      console.error('Error:', error);
      alert('An error occurred while generating content. Please try again.');
      generateBtn.disabled = false;
      generateBtn.textContent = originalText;
    });
  }
  
  // Save content function
  function saveContent() {
    const content = tinymce.get('editor').getContent();
    
    if (!content) {
      alert('Please generate or write some content before saving.');
      return;
    }
    
    const platform = document.getElementById('platform').value;
    const tone = document.getElementById('tone').value;
    const topic = document.getElementById('topic').value;
    const cta = document.getElementById('cta').value;
    const length = document.getElementById('length').value;
    const emojiLevel = document.getElementById('emoji_level').value;
    
    // Use topic as the title if available
    const title = topic ? `${platform} post about ${topic}` : `${platform} post`;
    
    // Show loading state
    const saveBtn = document.querySelector('button[value="save"]');
    const originalText = saveBtn.textContent;
    saveBtn.disabled = true;
    saveBtn.textContent = 'Saving...';
    
    fetch('/save_content', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        title: title,
        content: content,
        platform: platform,
        tone: tone,
        topic: topic,
        cta: cta,
        length: length,
        emoji_level: emojiLevel
      })
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        alert('Content saved successfully!');
        // Reload the page to show the updated list of saved posts
        window.location.reload();
      } else {
        alert('Error: ' + data.error);
      }
      saveBtn.disabled = false;
      saveBtn.textContent = originalText;
    })
    .catch(error => {
      console.error('Error:', error);
      alert('An error occurred while saving. Please try again.');
      saveBtn.disabled = false;
      saveBtn.textContent = originalText;
    });
  }
    // Function to toggle blog snippet visibility
  function toggleBlogSnippet() {
    const editor = tinymce.get('editor');
    const editorContent = editor.getContent();
    const toggleBtn = document.getElementById('toggleBlogBtn');
    
    // Check if we have a blog snippet
    if (!currentBlogSnippet) {
      alert('No blog snippet available to toggle.');
      return;
    }
    
    isBlogSnippetVisible = !isBlogSnippetVisible;
    
    // Update button state
    if (isBlogSnippetVisible) {
      toggleBtn.classList.add('toggle-active');
    } else {
      toggleBtn.classList.remove('toggle-active');
    }
    
    // Find the existing blog snippet container
    const blogSnippetRegex = /<div id="blog-snippet-container"[^>]*>[\s\S]*?<\/div>/i;
    const hasBlogSnippet = blogSnippetRegex.test(editorContent);
    
    if (isBlogSnippetVisible && !hasBlogSnippet) {
      // Show the blog snippet
      editor.setContent(
        editorContent + 
        '<div id="blog-snippet-container" class="blog-snippet">' +
        '<hr><h3>Blog Snippet:</h3>' + 
        currentBlogSnippet +
        '</div>'
      );
    } else if (!isBlogSnippetVisible && hasBlogSnippet) {
      // Hide the blog snippet
      const newContent = editorContent.replace(blogSnippetRegex, '');
      editor.setContent(newContent);
    }
  }
  
  // Make the functions available globally
  window.generateContent = generateContent;
  window.saveContent = saveContent;
  window.toggleBlogSnippet = toggleBlogSnippet;
    // Function to view a post
  window.viewPost = function(postId) {
    window.location.href = '/view_post/' + postId;
  };
  
  // Function to edit a post
  window.editPost = function(postId) {
    window.location.href = '/edit_post/' + postId;
  };
  
  // Function to delete a post
  window.deletePost = function(postId) {
    if (confirm('Are you sure you want to delete this post?')) {
      fetch('/delete_post/' + postId, { method: 'POST' })
        .then(response => response.json())
        .then(data => {
          if (data.success) {
            alert('Post deleted successfully.');
            window.location.reload();
          } else {
            alert('Error deleting post: ' + data.error);
          }
        })
        .catch(error => {
          console.error('Error deleting post:', error);
          alert('An error occurred while deleting. Please try again.');
        });
    }
  };
  
  // Toggle expanded content in post cards
  const postContents = document.querySelectorAll('.post-content');
  postContents.forEach(content => {
    content.addEventListener('click', function() {
      this.classList.toggle('expanded');
      const fade = this.querySelector('.post-fade');
      if (fade) {
        fade.style.display = this.classList.contains('expanded') ? 'none' : 'block';
      }
    });
  });
});
