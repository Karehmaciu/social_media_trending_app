import sqlite3
import os
import json
from datetime import datetime
import uuid

class PostsDatabase:
    def __init__(self, db_path="database.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialize the database and create tables if they don't exist"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            # Create directory if it doesn't exist and path has a directory
            os.makedirs(db_dir, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create posts table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id TEXT PRIMARY KEY,
                title TEXT,
                content TEXT,
                platform TEXT,
                tone TEXT,
                topic TEXT,
                cta TEXT,
                emoji_level TEXT,
                length TEXT,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_post(self, post_data):
        """Save a new post or update an existing one"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        post_id = post_data.get('id')
        if not post_id:
            # New post
            post_id = str(uuid.uuid4())
            created_at = datetime.now().isoformat()
            updated_at = created_at
        else:
            # Update existing post
            cursor.execute(
                "SELECT created_at FROM posts WHERE id = ?",
                (post_id,)
            )
            result = cursor.fetchone()
            if result:
                created_at = result[0]
            else:
                created_at = datetime.now().isoformat()
            updated_at = datetime.now().isoformat()
        
        # Extract metadata (additional attributes not in main columns)
        main_fields = ['id', 'title', 'content', 'platform', 'tone', 'topic', 'cta', 'emoji_level', 'length', 'created_at', 'updated_at']
        metadata = {k: v for k, v in post_data.items() if k not in main_fields}
        
        cursor.execute(
            """
            INSERT OR REPLACE INTO posts 
            (id, title, content, platform, tone, topic, cta, emoji_level, length, metadata, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                post_id,
                post_data.get('title', ''),
                post_data.get('content', ''),
                post_data.get('platform', ''),
                post_data.get('tone', ''),
                post_data.get('topic', ''),
                post_data.get('cta', ''),
                post_data.get('emoji_level', ''),
                post_data.get('length', ''),
                json.dumps(metadata),
                created_at,
                updated_at
            )
        )
        
        conn.commit()
        conn.close()
        
        return post_id
    
    def get_post(self, post_id):
        """Get a post by ID"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM posts WHERE id = ?",
            (post_id,)
        )
        
        post = cursor.fetchone()
        conn.close()
        
        if post:
            post_dict = dict(post)
            # Parse metadata
            if post_dict.get('metadata'):
                try:
                    metadata = json.loads(post_dict['metadata'])
                    post_dict.update(metadata)
                except:
                    pass
            return post_dict
        
        return None
    
    def get_all_posts(self, limit=None, offset=0, platform=None):
        """Get all posts with optional filtering"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = "SELECT * FROM posts"
        params = []
        
        if platform:
            query += " WHERE platform = ?"
            params.append(platform)
        
        query += " ORDER BY created_at DESC"
        
        if limit:
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])
        
        cursor.execute(query, params)
        posts = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        # Parse metadata for each post
        for post in posts:
            if post.get('metadata'):
                try:
                    metadata = json.loads(post['metadata'])
                    post.update(metadata)
                except:
                    pass
        
        return posts
    
    def delete_post(self, post_id):
        """Delete a post by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "DELETE FROM posts WHERE id = ?",
            (post_id,)
        )
        
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return deleted
