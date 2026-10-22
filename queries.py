
CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    telegram_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT
);
"""

CREATE_TASKS_TABLE = """
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    title TEXT,
    is_done INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users (telegram_id)
);
"""


REGISTER_USER = "INSERT OR IGNORE INTO users (telegram_id, username, first_name) VALUES (?, ?, ?);"
ADD_TASK = "INSERT INTO tasks (user_id, title) VALUES (?, ?);"


GET_USER_TASKS = """
SELECT t.id, t.title, t.is_done 
FROM tasks t
INNER JOIN users u ON t.user_id = u.telegram_id
WHERE u.telegram_id = ?;
"""

GET_TASK_BY_ID = "SELECT user_id, is_done FROM tasks WHERE id = ?;"
MARK_TASK_DONE = "UPDATE tasks SET is_done = 1 WHERE id = ?;"


GET_STATS = """
SELECT 
    COUNT(t.id) as total,
    SUM(CASE WHEN t.is_done = 1 THEN 1 ELSE 0 END) as done,
    SUM(CASE WHEN t.is_done = 0 THEN 1 ELSE 0 END) as not_done
FROM tasks t
INNER JOIN users u ON t.user_id = u.telegram_id
WHERE u.telegram_id = ?
GROUP BY u.telegram_id;
"""
