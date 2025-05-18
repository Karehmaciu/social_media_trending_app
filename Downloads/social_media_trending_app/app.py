from flask import Flask, render_template, request, jsonify, send_from_directory, url_for, redirect
import os
from dotenv import load_dotenv
import openai # Keep this for openai.OpenAI()
from werkzeug.utils import secure_filename
import uuid
from datetime import datetime
import json
from models import PostsDatabase
# from serpapi import GoogleSearch # This line is correct if google-search-results is installed

load_dotenv()

# Make sure instance directory exists
if not os.path.exists('instance'):
    os.makedirs('instance')

# Initialize database
db = PostsDatabase(db_path="instance/posts.db")

# Initialize OpenAI client
# Make sure your OPENAI_API_KEY is set in your .env file
try:
    client = openai.OpenAI()
except openai.OpenAIError as e:
    print(f"Error initializing OpenAI client: {e}")
    client = None

app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create upload folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

openai.api_key = os.getenv('OPENAI_API_KEY') # Still needed for older versions or specific configurations
SERP_API_KEY = os.getenv('SERP_API_KEY')
TINYMCE_API_KEY = os.getenv('TINYMCE_API_KEY')

@app.route('/')
def editor():
    return render_template('editor.html', tinymce_api_key=TINYMCE_API_KEY)

@app.route('/generate_post', methods=['POST'])
def generate_post():
    if not client:
        return jsonify({"error": "OpenAI client not initialized. Check API key."}), 500
    data = request.json
    prompt = data.get('prompt', '')
    if not prompt:
        return jsonify({"error": "Prompt cannot be empty."}), 400
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        post_content = resp.choices[0].message.content
        return jsonify({"post": post_content})
    except openai.APIError as e:
        print(f"OpenAI API Error: {e}")
        return jsonify({"error": f"Failed to generate post: {str(e)}"}), 500
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return jsonify({"error": "An unexpected error occurred while generating the post."}), 500


@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q')
    if not query:
        return jsonify({"error": "Search query cannot be empty."}), 400
    if not SERP_API_KEY:
        return jsonify({"error": "SERP API key not configured."}), 500
        
    from serpapi import GoogleSearch # Import here to ensure it's only used when needed and avoid startup error if not installed during dev
    params = {
        "engine": "google",
        "q": query,
        "api_key": SERP_API_KEY
    }
    try:
        search_results = GoogleSearch(params)
        results = search_results.get_dict().get('organic_results', [])
        return jsonify(results[:5])
    except Exception as e:
        print(f"SerpAPI Error: {e}")
        return jsonify({"error": "Failed to fetch search results."}), 500

@app.route('/upload_media', methods=['POST'])
def upload_media():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if file:
        # Consider adding filename sanitization and security checks here
        filename = file.filename # In a real app, use werkzeug.utils.secure_filename
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        try:
            file.save(save_path)
            return jsonify({"url": f"/{UPLOAD_FOLDER}/{filename}"})
        except Exception as e:
            print(f"File upload error: {e}")
            return jsonify({"error": "Failed to save uploaded file."}), 500
    return jsonify({"error": "File upload failed."}), 400

@app.route('/tinymce/upload', methods=['POST'])
def tinymce_upload():
    """Handle file uploads from TinyMCE"""
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file:
        # Secure the filename and add a UUID to avoid conflicts
        filename = secure_filename(file.filename)
        # Add a unique prefix to avoid filename conflicts
        filename = f"{uuid.uuid4().hex[:8]}_{filename}"
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        try:
            file.save(save_path)
            # Return the location in the format TinyMCE expects
            file_url = url_for('static', filename=f'uploads/{filename}', _external=True)
            print(f"Image uploaded: {file_url}")
            return jsonify({
                "location": file_url
            })
        except Exception as e:
            print(f"TinyMCE file upload error: {e}")
            return jsonify({"error": {"message": "Failed to save uploaded file."}}), 500
    
    return jsonify({"error": {"message": "File upload failed."}}), 400

# Serve uploaded files
@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/tinymce/ai', methods=['POST'])
def tinymce_ai_assistant():
    """Handle AI requests from TinyMCE"""
    if not client:
        return jsonify({"error": "OpenAI client not initialized. Check API key."}), 500
    
    data = request.json
    prompt = data.get('prompt', '')
    
    if not prompt:
        return jsonify({"error": "Prompt cannot be empty."}), 400
    
    try:
        # Use GPT-4o mini for AI assistant requests
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant integrated with a text editor. Keep responses concise and focused on helping with content creation."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500  # Limit response size to be concise
        )
        
        response_text = response.choices[0].message.content
        return jsonify({"text": response_text})
    except Exception as e:
        print(f"AI Assistant Error: {e}")
        return jsonify({"error": f"Failed to process AI request: {str(e)}"}), 500

@app.route('/create_content')
def create_content():
    """Render the content editor page"""
    platforms = ["LinkedIn", "Facebook", "Instagram", "X (Twitter)", "TikTok", "YouTube", "Bluesky", "Blog"]
    tones = ["Professional", "Conversational", "Inspiring", "Humorous"]
    lengths = ["short", "medium", "long"]
    emoji_levels = ["none", "light", "rich"]
    
    # Get recent posts
    try:
        saved_posts = db.get_all_posts(limit=5)
        # Format datetime for display
        for post in saved_posts:
            if isinstance(post.get('created_at'), str):
                try:
                    dt = datetime.fromisoformat(post['created_at'])
                    post['created_at'] = dt.strftime('%b %d, %Y %I:%M %p')
                except:
                    pass
    except Exception as e:
        print(f"Error getting saved posts: {e}")
        saved_posts = []
        
    # Default values
    default_values = {
        'selected_platform': request.args.get('platform', 'LinkedIn'),
        'selected_tone': request.args.get('tone', 'Professional'),
        'selected_length': request.args.get('length', 'medium'),
        'selected_emoji_level': request.args.get('emoji_level', 'light'),
        'topic': request.args.get('topic', ''),
        'cta': request.args.get('cta', ''),
        'content': ''
    }
    
    return render_template(
        'content_editor.html',
        platforms=platforms,
        tones=tones,
        lengths=lengths,
        emoji_levels=emoji_levels,
        saved_posts=saved_posts,
        current_year=datetime.now().year,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        **default_values
    )

@app.route('/generate_social_content', methods=['POST'])
def generate_social_content():
    """Generate social media content based on parameters"""
    if not client:
        return jsonify({"error": "OpenAI client not initialized. Check API key."}), 500
    
    data = request.json
    platform = data.get('platform', 'LinkedIn')
    tone = data.get('tone', 'Professional')
    topic = data.get('topic', '')
    cta = data.get('cta', '')
    length_hint = data.get('length_hint', 'medium')
    emoji_level = data.get('emoji_level', 'light')
    
    if not topic:
        return jsonify({"error": "Topic cannot be empty."}), 400
    
    # Build the prompt
    prompt = f"""Create a {platform} post about {topic}. 
    Tone: {tone}
    Length: {length_hint}
    Emoji usage: {emoji_level}
    """
    
    if cta:
        prompt += f"Call to action: {cta}\n"
    
    # Add platform-specific instructions
    if platform == "LinkedIn":
        prompt += "Format as a professional LinkedIn post with appropriate hashtags."
    elif platform == "X (Twitter)":
        prompt += "Format as a concise tweet under 280 characters with relevant hashtags."
    elif platform == "Instagram":
        prompt += "Format as an engaging Instagram caption with appropriate hashtags."
    elif platform == "Facebook":
        prompt += "Format as an engaging Facebook post with a conversational tone."
    elif platform == "TikTok":
        prompt += "Format as a short, catchy TikTok script with relevant hashtags."
    elif platform == "YouTube":
        prompt += "Format as a YouTube video description with timestamps and key points."
    elif platform == "Bluesky":
        prompt += "Format as a Bluesky post with concise, engaging text and relevant hashtags. Keep it conversational but thoughtful."
    elif platform == "Blog":
        prompt += "Format as a blog post with headers, bullet points, and proper structure."
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert social media content creator. Create engaging, platform-specific content that follows best practices."},
                {"role": "user", "content": prompt}
            ]
        )
        
        platform_post = response.choices[0].message.content
        
        # Generate a complementary blog snippet for non-Blog platforms
        blog_snippet = None
        if platform != "Blog":
            blog_prompt = f"Based on the {platform} post about '{topic}', write a short blog snippet (1-2 paragraphs) that complements the post and could be used for a blog version."
            
            try:
                blog_response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are an expert content writer creating complementary blog content."},
                        {"role": "user", "content": platform_post},
                        {"role": "user", "content": blog_prompt}
                    ],
                    max_tokens=300
                )
                
                blog_snippet = blog_response.choices[0].message.content
            except Exception as e:
                print(f"Blog snippet generation error: {e}")
                # Non-critical error, continue without blog snippet
                pass
        
        return jsonify({
            "platform_post": platform_post,
            "blog_snippet": blog_snippet
        })
    except Exception as e:
        print(f"Content generation error: {e}")
        return jsonify({"error": f"Failed to generate content: {str(e)}"}), 500

@app.route('/save_content', methods=['POST'])
def save_content():
    """Save or update content to the database"""
    data = request.json
    required_fields = ['content', 'platform']
    
    # Check for required fields
    for field in required_fields:
        if not data.get(field):
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    try:
        post_id = db.save_post(data)
        return jsonify({"success": True, "post_id": post_id})
    except Exception as e:
        print(f"Error saving content: {e}")
        return jsonify({"error": f"Failed to save content: {str(e)}"}), 500

@app.route('/get_saved_posts')
def get_saved_posts():
    """Get saved posts as JSON"""
    limit = request.args.get('limit', 10, type=int)
    offset = request.args.get('offset', 0, type=int)
    platform = request.args.get('platform')
    
    try:
        posts = db.get_all_posts(limit=limit, offset=offset, platform=platform)
        
        # Format datetime for display
        for post in posts:
            if isinstance(post.get('created_at'), str):
                try:
                    dt = datetime.fromisoformat(post['created_at'])
                    post['timestamp'] = dt.strftime('%b %d, %Y')
                except:
                    post['timestamp'] = post['created_at']
            else:
                post['timestamp'] = str(post.get('created_at', ''))
        
        return jsonify(posts)
    except Exception as e:
        print(f"Error getting saved posts: {e}")
        return jsonify({"error": f"Failed to get saved posts: {str(e)}"}), 500

@app.route('/get_post/<post_id>')
def get_post(post_id):
    """Get a single post by ID"""
    try:
        post = db.get_post(post_id)
        if not post:
            return jsonify({"error": "Post not found"}), 404
        return jsonify(post)
    except Exception as e:
        print(f"Error getting post {post_id}: {e}")
        return jsonify({"error": f"Failed to get post: {str(e)}"}), 500

@app.route('/edit_post/<post_id>')
def edit_post(post_id):
    """Render the content editor page with a post loaded for editing"""
    try:
        post = db.get_post(post_id)
        if not post:
            return redirect('/create_content')
        
        # Pass post data as URL parameters
        return redirect(url_for(
            'create_content',
            post_id=post_id,
            platform=post.get('platform', 'LinkedIn'),
            tone=post.get('tone', 'Professional'),
            length=post.get('length', 'medium'),
            emoji_level=post.get('emoji_level', 'light'),
            topic=post.get('topic', ''),
            cta=post.get('cta', '')
        ))
    except Exception as e:
        print(f"Error editing post {post_id}: {e}")
        return redirect('/create_content')

@app.route('/delete_post/<post_id>', methods=['POST'])
def delete_post(post_id):
    """Delete a post by ID"""
    try:
        deleted = db.delete_post(post_id)
        if deleted:
            return jsonify({"success": True})
        else:
            return jsonify({"error": "Post not found"}), 404
    except Exception as e:
        print(f"Error deleting post {post_id}: {e}")
        return jsonify({"error": f"Failed to delete post: {str(e)}"}), 500

@app.route('/saved_posts')
def saved_posts():
    """Display a list of saved posts in a compact view"""
    platforms = ["LinkedIn", "Facebook", "Instagram", "X (Twitter)", "TikTok", "YouTube", "Bluesky", "Blog"]
    
    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = 12  # Number of posts per page
    offset = (page - 1) * per_page
    
    # Get filter parameters
    platform_filter = request.args.get('platform', '')
    date_filter = request.args.get('date', '')
    search_query = request.args.get('q', '')
    
    try:
        # Get total count for pagination
        all_posts = db.get_all_posts(platform=platform_filter if platform_filter else None)
        
        # Apply date filtering if needed
        if date_filter:
            current_date = datetime.now()
            filtered_posts = []
            
            for post in all_posts:
                try:
                    if isinstance(post.get('created_at'), str):
                        post_date = datetime.fromisoformat(post['created_at'])
                    else:
                        continue
                        
                    if date_filter == 'today' and post_date.date() == current_date.date():
                        filtered_posts.append(post)
                    elif date_filter == 'week' and (current_date - post_date).days <= 7:
                        filtered_posts.append(post)
                    elif date_filter == 'month' and post_date.month == current_date.month and post_date.year == current_date.year:
                        filtered_posts.append(post)
                except:
                    continue
            
            all_posts = filtered_posts
            
        # Apply search filtering if needed
        if search_query:
            search_query = search_query.lower()
            filtered_posts = []
            
            for post in all_posts:
                if (search_query in str(post.get('title', '')).lower() or 
                    search_query in str(post.get('content', '')).lower() or
                    search_query in str(post.get('topic', '')).lower()):
                    filtered_posts.append(post)
            
            all_posts = filtered_posts
        
        total_posts = len(all_posts)
        total_pages = (total_posts + per_page - 1) // per_page
        
        # Get the current page of posts
        posts = db.get_all_posts(
            limit=per_page, 
            offset=offset, 
            platform=platform_filter if platform_filter else None
        )
        
        # Apply the same filters to the paginated results
        if date_filter or search_query:
            posts = [post for post in posts if post in all_posts]
        
        # Format dates for display
        for post in posts:
            if isinstance(post.get('created_at'), str):
                try:
                    dt = datetime.fromisoformat(post['created_at'])
                    post['timestamp'] = dt.strftime('%b %d, %Y %I:%M %p')
                except:
                    post['timestamp'] = post.get('created_at', '')
            else:
                post['timestamp'] = str(post.get('created_at', ''))
        
        return render_template(
            'saved_posts.html',
            posts=posts,
            platforms=platforms,
            page=page,
            total_pages=total_pages,
            current_year=datetime.now().year,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
    except Exception as e:
        print(f"Error loading saved posts: {e}")
        return render_template(
            'saved_posts.html',
            posts=[],
            platforms=platforms,
            page=1,
            total_pages=1,
            current_year=datetime.now().year,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            error=str(e)
        )

@app.route('/view_post/<post_id>')
def view_post(post_id):
    """View a single post in detail"""
    try:
        post = db.get_post(post_id)
        
        if not post:
            return redirect('/saved_posts')
        
        # Format date for display
        if isinstance(post.get('created_at'), str):
            try:
                dt = datetime.fromisoformat(post['created_at'])
                post['timestamp'] = dt.strftime('%b %d, %Y %I:%M %p')
            except:
                post['timestamp'] = post.get('created_at', '')
        else:
            post['timestamp'] = str(post.get('created_at', ''))
        
        return render_template(
            'view_post.html',
            post=post,
            current_year=datetime.now().year,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
    except Exception as e:
        print(f"Error viewing post {post_id}: {e}")
        return redirect('/saved_posts')

@app.route('/share_post/<post_id>/<platform>', methods=['GET'])
def share_post(post_id, platform):
    """Prepare post for sharing to specific platform"""
    try:
        post = db.get_post(post_id)
        if not post:
            return jsonify({"error": "Post not found"}), 404
        
        # Get the raw content
        content = post.get('content', '')
        title = post.get('title', 'Untitled Post')
        
        # Format content for different platforms if needed
        platform_specific_content = content
        share_url = url_for('view_post', post_id=post_id, _external=True)
        
        return jsonify({
            "title": title,
            "content": platform_specific_content,
            "platform": platform,
            "share_url": share_url
        })
    except Exception as e:
        print(f"Error sharing post {post_id}: {e}")
        return jsonify({"error": f"Failed to prepare post for sharing: {str(e)}"}), 500

if __name__ == '__main__':
    # Ensure the serpapi import is valid before running
    try:
        from serpapi import GoogleSearch
    except ImportError:
        print("Error: The 'google-search-results' package (for serpapi) is not installed or not found.")
        print("Please install it by running: pip install google-search-results")
        exit(1) # Exit if essential dependency is missing

    if not openai.api_key:
        print("Warning: OPENAI_API_KEY is not set in .env file. OpenAI features will not work.")
    if not SERP_API_KEY:
        print("Warning: SERP_API_KEY is not set in .env file. Search features will not work.")
    if not TINYMCE_API_KEY or TINYMCE_API_KEY == 'your_tinymce_api_key_here':
        print("Warning: TINYMCE_API_KEY is not set or is a placeholder in .env file. TinyMCE editor might not function correctly.")
    
    # Use PORT environment variable if available (for Render deployment)
    port = int(os.environ.get("PORT", 8008))
    
    # Set debug based on environment
    debug = os.environ.get("FLASK_ENV", "production") == "development"
        
    app.run(host='0.0.0.0', port=port, debug=debug)
