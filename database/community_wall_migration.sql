-- ============================================================================
-- Community Support Wall - Database Migration
-- ============================================================================

-- Update anonymous_messages table for community support wall
ALTER TABLE anonymous_messages
  ADD COLUMN IF NOT EXISTS title VARCHAR(255) DEFAULT NULL AFTER id,
  ADD COLUMN IF NOT EXISTS user_id INT DEFAULT NULL AFTER title,
  ADD COLUMN IF NOT EXISTS likes_count INT DEFAULT 0 AFTER is_hidden,
  ADD COLUMN IF NOT EXISTS supports_count INT DEFAULT 0 AFTER likes_count,
  ADD COLUMN IF NOT EXISTS comments_count INT DEFAULT 0 AFTER supports_count,
  ADD COLUMN IF NOT EXISTS is_pinned BOOLEAN DEFAULT FALSE AFTER comments_count,
  ADD COLUMN IF NOT EXISTS is_hidden BOOLEAN DEFAULT FALSE AFTER is_pinned,
  ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP AFTER is_hidden;

-- Create community_reactions table
CREATE TABLE IF NOT EXISTS community_reactions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    post_id INT NOT NULL,
    user_id INT NOT NULL,
    reaction_type ENUM('like', 'support') NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (post_id) REFERENCES anonymous_messages(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_reaction (post_id, user_id, reaction_type),
    INDEX idx_post_id (post_id),
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create community_comments table
CREATE TABLE IF NOT EXISTS community_comments (
    id INT PRIMARY KEY AUTO_INCREMENT,
    post_id INT NOT NULL,
    user_id INT DEFAULT NULL,
    comment_text TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (post_id) REFERENCES anonymous_messages(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_post_id (post_id),
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
