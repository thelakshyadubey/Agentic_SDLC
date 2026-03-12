import streamlit as st
import sqlite3
import bcrypt
from datetime import datetime, date, timedelta

# --- Configuration ---
DATABASE_PATH = 'task_manager.db'

# --- Database Functions ---
def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # This enables fetching rows as dict-like objects
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            email TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            due_date DATE,
            status TEXT NOT NULL DEFAULT 'to-do',
            created_by_user_id INTEGER NOT NULL,
            assigned_to_user_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by_user_id) REFERENCES users(id),
            FOREIGN KEY (assigned_to_user_id) REFERENCES users(id)
        );
    """)
    conn.commit()
    conn.close()

# --- Utility Functions ---
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password, hashed_password):
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

# --- Authentication Functions ---
def register_user(username, password, email=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        hashed_pwd = hash_password(password)
        cursor.execute("INSERT INTO users (username, password_hash, email) VALUES (?, ?, ?)",
                       (username, hashed_pwd, email))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # Username or email already exists
    finally:
        conn.close()

def login_user(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, password_hash FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    if user and verify_password(password, user['password_hash']):
        return {'id': user['id'], 'username': user['username']}
    return None

def is_logged_in():
    return st.session_state.get('logged_in', False)

def get_current_user():
    if is_logged_in():
        return {'id': st.session_state.user_id, 'username': st.session_state.username}
    return None

def logout_user():
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.user_id = None
    st.session_state.page = 'Login' # Redirect to login page after logout
    st.rerun()

# --- Task Management Functions ---
def create_task(title, description, due_date, created_by_user_id, assigned_to_user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tasks (title, description, due_date, status, created_by_user_id, assigned_to_user_id) VALUES (?, ?, ?, ?, ?, ?)",
        (title, description, due_date, 'to-do', created_by_user_id, assigned_to_user_id)
    )
    conn.commit()
    conn.close()
    return True

def get_tasks(created_by_user_id_filter=None, assigned_to_user_id_filter=None, status=None, search_term=None, sort_by=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        SELECT t.id, t.title, t.description, t.due_date, t.status,
               cu.username AS created_by_username,
               au.username AS assigned_to_username,
               t.created_at, t.updated_at,
               t.created_by_user_id, t.assigned_to_user_id
        FROM tasks t
        JOIN users cu ON t.created_by_user_id = cu.id
        LEFT JOIN users au ON t.assigned_to_user_id = au.id
        WHERE 1=1
    """
    params = []

    if created_by_user_id_filter is not None:
        query += " AND t.created_by_user_id = ?"
        params.append(created_by_user_id_filter)
    
    if assigned_to_user_id_filter is not None:
        if assigned_to_user_id_filter == 'NULL': # Special string for unassigned
            query += " AND t.assigned_to_user_id IS NULL"
        else:
            query += " AND t.assigned_to_user_id = ?"
            params.append(assigned_to_user_id_filter)

    if status and status != "All":
        query += " AND t.status = ?"
        params.append(status)
    if search_term:
        query += " AND (t.title LIKE ? OR t.description LIKE ?)"
        params.extend([f"%{search_term}%", f"%{search_term}%"])

    if sort_by == 'Due Date':
        query += " ORDER BY t.due_date ASC"
    elif sort_by == 'Status':
        query += " ORDER BY t.status ASC"
    elif sort_by == 'Created At':
        query += " ORDER BY t.created_at DESC"
    else:
        query += " ORDER BY t.id DESC" # Default sort

    cursor.execute(query, params)
    tasks = cursor.fetchall()
    conn.close()
    return tasks

def get_task_by_id(task_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT t.id, t.title, t.description, t.due_date, t.status,
               t.created_by_user_id, t.assigned_to_user_id,
               cu.username AS created_by_username,
               au.username AS assigned_to_username,
               t.created_at, t.updated_at
        FROM tasks t
        JOIN users cu ON t.created_by_user_id = cu.id
        LEFT JOIN users au ON t.assigned_to_user_id = au.id
        WHERE t.id = ?
    """, (task_id,))
    task = cursor.fetchone()
    conn.close()
    return task

def update_task(task_id, title, description, due_date, status, assigned_to_user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE tasks SET title = ?, description = ?, due_date = ?, status = ?, assigned_to_user_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (title, description, due_date, status, assigned_to_user_id, task_id)
    )
    conn.commit()
    conn.close()
    return True

def delete_task(task_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    return True

def get_dashboard_summary(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    summary = {}

    # Total tasks created by user
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE created_by_user_id = ?", (user_id,))
    summary['total_created'] = cursor.fetchone()[0]

    # Total tasks assigned to user
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE assigned_to_user_id = ?", (user_id,))
    summary['total_assigned'] = cursor.fetchone()[0]

    # Tasks by status for tasks created by user
    cursor.execute("SELECT status, COUNT(*) FROM tasks WHERE created_by_user_id = ? GROUP BY status", (user_id,))
    summary['created_by_status'] = {row['status']: row['COUNT(*)'] for row in cursor.fetchall()}

    # Tasks by status for tasks assigned to user
    cursor.execute("SELECT status, COUNT(*) FROM tasks WHERE assigned_to_user_id = ? GROUP BY status", (user_id,))
    summary['assigned_by_status'] = {row['status']: row['COUNT(*)'] for row in cursor.fetchall()}

    # Overdue tasks assigned to user
    today = date.today().isoformat()
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE assigned_to_user_id = ? AND due_date < ? AND status != 'completed'", (user_id, today))
    summary['overdue_assigned'] = cursor.fetchone()[0]

    # Upcoming tasks assigned to user (due in next 7 days, not completed)
    seven_days_later = (date.today() + timedelta(days=7)).isoformat()
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE assigned_to_user_id = ? AND due_date BETWEEN ? AND ? AND status != 'completed'", (user_id, today, seven_days_later))
    summary['upcoming_assigned'] = cursor.fetchone()[0]

    conn.close()
    return summary

def get_all_users():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username FROM users")
    users = cursor.fetchall()
    conn.close()
    return users

# --- Streamlit UI Functions ---

def show_register_page():
    st.subheader("Register New User")
    with st.form("register_form"):
        new_username = st.text_input("Username")
        new_password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        new_email = st.text_input("Email (Optional)")
        register_button = st.form_submit_button("Register")

        if register_button:
            if new_username and new_password and confirm_password:
                if new_password == confirm_password:
                    if register_user(new_username, new_password, new_email if new_email else None):
                        st.success("Registration successful! Please login.")
                        st.session_state.page = 'Login'
                        st.rerun()
                    else:
                        st.error("Username or email already exists. Please choose a different one.")
                else:
                    st.error("Passwords do not match.")
            else:
                st.error("Username and Password are required.")

def show_login_page():
    st.subheader("Login")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        login_button = st.form_submit_button("Login")

        if login_button:
            user = login_user(username, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.username = user['username']
                st.session_state.user_id = user['id']
                st.success(f"Welcome, {user['username']}!")
                st.session_state.page = 'View Tasks' # Redirect to dashboard or view tasks
                st.rerun()
            else:
                st.error("Invalid username or password.")

def show_dashboard_page():
    st.subheader(f"Dashboard for {st.session_state.username}")
    user_id = st.session_state.user_id
    summary = get_dashboard_summary(user_id)

    st.markdown("---")
    st.markdown("#### Tasks Created By You")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Created", summary.get('total_created', 0))
    with col2:
        st.metric("To-Do", summary['created_by_status'].get('to-do', 0))
    with col3:
        st.metric("In-Progress", summary['created_by_status'].get('in-progress', 0))
    with col4:
        st.metric("Completed", summary['created_by_status'].get('completed', 0))

    st.markdown("---")
    st.markdown("#### Tasks Assigned To You")
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        st.metric("Total Assigned", summary.get('total_assigned', 0))
    with col2:
        st.metric("To-Do", summary['assigned_by_status'].get('to-do', 0))
    with col3:
        st.metric("In-Progress", summary['assigned_by_status'].get('in-progress', 0))
    with col4:
        st.metric("Completed", summary['assigned_by_status'].get('completed', 0))
    with col5:
        st.metric("Overdue", summary.get('overdue_assigned', 0))
    with col6:
        st.metric("Upcoming (7 days)", summary.get('upcoming_assigned', 0))

    st.markdown("---")
    st.write("Detailed task lists can be found in 'View Tasks'.")


def show_view_tasks_page():
    st.subheader("View Tasks")
    current_user_id = st.session_state.user_id

    # Filters and Sorting
    col1, col2, col3 = st.columns(3)
    with col1:
        filter_status = st.selectbox("Filter by Status", ["All", "to-do", "in-progress", "completed"], key="view_task_status_filter")
    with col2:
        search_term = st.text_input("Search (Title/Description)", key="view_task_search_term")
    with col3:
        sort_by = st.selectbox("Sort By", ["ID", "Due Date", "Status", "Created At"], key="view_task_sort_by")

    st.markdown("---")
    st.markdown("#### Tasks Created by You")
    created_tasks = get_tasks(created_by_user_id_filter=current_user_id, status=filter_status,
                              search_term=search_term, sort_by=sort_by)
    if created_tasks:
        st.dataframe(created_tasks, use_container_width=True)
    else:
        st.info("No tasks created by you found matching the criteria.")

    st.markdown("---")
    st.markdown("#### Tasks Assigned to You")
    assigned_tasks = get_tasks(assigned_to_user_id_filter=current_user_id, status=filter_status,
                               search_term=search_term, sort_by=sort_by)
    if assigned_tasks:
        st.dataframe(assigned_tasks, use_container_width=True)
    else:
        st.info("No tasks assigned to you found matching the criteria.")

def show_create_task_page():
    st.subheader("Create New Task")
    current_user_id = st.session_state.user_id
    all_users = get_all_users()
    user_options = {user['username']: user['id'] for user in all_users}
    user_options['Unassigned'] = None # Option for unassigned task

    with st.form("create_task_form"):
        title = st.text_input("Task Title", max_chars=100)
        description = st.text_area("Description")
        due_date_str = st.date_input("Due Date (Optional)", value=None, min_value=date.today())
        
        # Set default assigned user to current user
        initial_assigned_username = st.session_state.username
        assigned_username = st.selectbox("Assign To", options=list(user_options.keys()), 
                                         index=list(user_options.keys()).index(initial_assigned_username))
        assigned_to_user_id = user_options[assigned_username]

        create_button = st.form_submit_button("Create Task")

        if create_button:
            if title:
                due_date_iso = due_date_str.isoformat() if due_date_str else None
                if create_task(title, description, due_date_iso, current_user_id, assigned_to_user_id):
                    st.success("Task created successfully!")
                    st.session_state.page = 'View Tasks'
                    st.rerun()
                else:
                    st.error("Failed to create task.")
            else:
                st.error("Task Title is required.")

def show_update_task_page():
    st.subheader("Update Task")
    current_user_id = st.session_state.user_id
    
    # Get all tasks created by or assigned to the current user
    created_tasks = get_tasks(created_by_user_id_filter=current_user_id)
    assigned_tasks = get_tasks(assigned_to_user_id_filter=current_user_id)
    
    # Combine and deduplicate tasks
    all_relevant_tasks_dict = {task['id']: task for task in created_tasks + assigned_tasks}
    all_relevant_tasks = list(all_relevant_tasks_dict.values())

    if not all_relevant_tasks:
        st.info("No tasks available to update.")
        return

    task_options = [f"{task['id']} - {task['title']}" for task in all_relevant_tasks]
    
    selected_task_display = st.selectbox("Select Task to Update", options=task_options, key="update_task_select")

    selected_task_id = None
    if selected_task_display:
        selected_task_id = int(selected_task_display.split(' - ')[0])
        st.session_state.selected_task_id_for_update = selected_task_id
    
    task_to_update = None
    if st.session_state.selected_task_id_for_update:
        task_to_update = get_task_by_id(st.session_state.selected_task_id_for_update)

    if task_to_update:
        all_users = get_all_users()
        user_options = {user['username']: user['id'] for user in all_users}
        user_options['Unassigned'] = None

        # Determine initial assigned user for selectbox
        initial_assigned_username = "Unassigned"
        if task_to_update['assigned_to_user_id']:
            for user in all_users:
                if user['id'] == task_to_update['assigned_to_user_id']:
                    initial_assigned_username = user['username']
                    break

        with st.form("update_task_form"):
            st.write(f"Updating Task ID: {task_to_update['id']}")
            title = st.text_input("Task Title", value=task_to_update['title'], max_chars=100)
            description = st.text_area("Description", value=task_to_update['description'])
            
            # Convert due_date string to date object for st.date_input
            current_due_date = datetime.strptime(task_to_update['due_date'], '%Y-%m-%d').date() if task_to_update['due_date'] else None
            due_date_str = st.date_input("Due Date (Optional)", value=current_due_date, min_value=date.today())
            
            status = st.selectbox("Status", options=["to-do", "in-progress", "completed"], index=["to-do", "in-progress", "completed"].index(task_to_update['status']))
            
            assigned_username = st.selectbox("Assign To", options=list(user_options.keys()), index=list(user_options.keys()).index(initial_assigned_username))
            assigned_to_user_id = user_options[assigned_username]

            update_button = st.form_submit_button("Update Task")

            if update_button:
                if title:
                    due_date_iso = due_date_str.isoformat() if due_date_str else None
                    if update_task(task_to_update['id'], title, description, due_date_iso, status, assigned_to_user_id):
                        st.success(f"Task '{title}' updated successfully!")
                        st.session_state.page = 'View Tasks'
                        st.rerun()
                    else:
                        st.error("Failed to update task.")
                else:
                    st.error("Task Title is required.")
    elif selected_task_display:
        st.warning("Please select a task to update.")


def show_delete_task_page():
    st.subheader("Delete Task")
    current_user_id = st.session_state.user_id
    
    # Get all tasks created by the current user
    user_created_tasks = get_tasks(created_by_user_id_filter=current_user_id)

    if not user_created_tasks:
        st.info("No tasks created by you are available to delete.")
        return

    task_options = [f"{task['id']} - {task['title']}" for task in user_created_tasks]
    
    selected_task_display = st.selectbox("Select Task to Delete", options=task_options, key="delete_task_select")

    selected_task_id = None
    if selected_task_display:
        selected_task_id = int(selected_task_display.split(' - ')[0])
        st.session_state.selected_task_id_for_delete = selected_task_id

    if st.session_state.selected_task_id_for_delete:
        task_to_delete = get_task_by_id(st.session_state.selected_task_id_for_delete)
        if task_to_delete:
            st.warning(f"Are you sure you want to delete task: **{task_to_delete['title']}** (ID: {task_to_delete['id']})?")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Confirm Delete", key="confirm_delete_button"):
                    if delete_task(task_to_delete['id']):
                        st.success(f"Task '{task_to_delete['title']}' deleted successfully.")
                        st.session_state.page = 'View Tasks'
                        st.session_state.selected_task_id_for_delete = None # Clear selection
                        st.rerun()
                    else:
                        st.error("Failed to delete task.")
            with col2:
                if st.button("Cancel", key="cancel_delete_button"):
                    st.info("Deletion cancelled.")
                    st.session_state.selected_task_id_for_delete = None # Clear selection
                    st.rerun()
        else:
            st.error("Selected task not found.")
    elif selected_task_display:
        st.warning("Please select a task to delete.")


# --- Main Application Logic ---
def main():
    st.set_page_config(page_title="Task Manager App", layout="wide")
    st.title("Task Manager App")

    # Initialize session state variables
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'page' not in st.session_state:
        st.session_state.page = 'Login' # Default page
    if 'selected_task_id_for_update' not in st.session_state:
        st.session_state.selected_task_id_for_update = None
    if 'selected_task_id_for_delete' not in st.session_state:
        st.session_state.selected_task_id_for_delete = None

    # Initialize database
    init_db()

    with st.sidebar:
        st.header("Navigation")
        if is_logged_in():
            st.write(f"Logged in as: **{st.session_state.username}**")
            menu_options = ["View Tasks", "Create Task", "Update Task", "Delete Task", "Reports", "Logout"]
            selected_page = st.selectbox("Go to", menu_options, key="logged_in_nav")
            if selected_page == "Logout":
                logout_user()
            else:
                st.session_state.page = selected_page
        else:
            menu_options = ["Login", "Register"]
            selected_page = st.selectbox("Go to", menu_options, key="logged_out_nav")
            st.session_state.page = selected_page

    # Render pages based on session state
    if st.session_state.page == 'Register':
        show_register_page()
    elif st.session_state.page == 'Login':
        show_login_page()
    elif st.session_state.page == 'View Tasks':
        if is_logged_in():
            show_view_tasks_page()
        else:
            st.warning("Please log in to view tasks.")
            st.session_state.page = 'Login'
            st.rerun()
    elif st.session_state.page == 'Create Task':
        if is_logged_in():
            show_create_task_page()
        else:
            st.warning("Please log in to create tasks.")
            st.session_state.page = 'Login'
            st.rerun()
    elif st.session_state.page == 'Update Task':
        if is_logged_in():
            show_update_task_page()
        else:
            st.warning("Please log in to update tasks.")
            st.session_state.page = 'Login'
            st.rerun()
    elif st.session_state.page == 'Delete Task':
        if is_logged_in():
            show_delete_task_page()
        else:
            st.warning("Please log in to delete tasks.")
            st.session_state.page = 'Login'
            st.rerun()
    elif st.session_state.page == 'Reports':
        if is_logged_in():
            show_dashboard_page()
        else:
            st.warning("Please log in to view reports.")
            st.session_state.page = 'Login'
            st.rerun()

if __name__ == "__main__":
    main()