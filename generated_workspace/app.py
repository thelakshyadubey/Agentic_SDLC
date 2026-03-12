import streamlit as st
import sqlite3
import hashlib
import datetime
from dateutil import parser
import os

def create_tables(conn):
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS Users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, role_id INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS Roles
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, role_name TEXT UNIQUE)''')
    c.execute('''CREATE TABLE IF NOT EXISTS Tasks
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, description TEXT, due_date DATE, user_id INTEGER)''')
    conn.commit()

def register_user(conn, username, password):
    c = conn.cursor()
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    c.execute("INSERT INTO Users (username, password, role_id) VALUES (?, ?, 1)", (username, hashed_password))
    conn.commit()

def login_user(conn, username, password):
    c = conn.cursor()
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    c.execute("SELECT * FROM Users WHERE username = ? AND password = ?", (username, hashed_password))
    return c.fetchone()

def create_task(conn, title, description, due_date, user_id):
    c = conn.cursor()
    c.execute("INSERT INTO Tasks (title, description, due_date, user_id) VALUES (?, ?, ?, ?)", (title, description, due_date, user_id))
    conn.commit()

def update_task(conn, task_id, title, description, due_date):
    c = conn.cursor()
    c.execute("UPDATE Tasks SET title = ?, description = ?, due_date = ? WHERE id = ?", (title, description, due_date, task_id))
    conn.commit()

def delete_task(conn, task_id):
    c = conn.cursor()
    c.execute("DELETE FROM Tasks WHERE id = ?", (task_id,))
    conn.commit()

def get_tasks(conn, user_id):
    c = conn.cursor()
    c.execute("SELECT * FROM Tasks WHERE user_id = ?", (user_id,))
    return c.fetchall()

def get_task(conn, task_id):
    c = conn.cursor()
    c.execute("SELECT * FROM Tasks WHERE id = ?", (task_id,))
    return c.fetchone()

def main():
    if 'page' not in st.session_state:
        st.session_state.page = 'login'
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None

    conn = sqlite3.connect('tasks.db')
    create_tables(conn)

    if st.session_state.page == 'login':
        st.title('Login')
        username = st.text_input('Username')
        password = st.text_input('Password', type="password")
        if st.button('Login'):
            user = login_user(conn, username, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.user_id = user[0]
                st.session_state.page = 'view_tasks'
                st.rerun()
            else:
                st.error('Invalid username or password')
        if st.button('Register'):
            st.session_state.page = 'register'
            st.rerun()

    elif st.session_state.page == 'register':
        st.title('Register')
        username = st.text_input('Username')
        password = st.text_input('Password', type="password")
        if st.button('Register'):
            register_user(conn, username, password)
            st.session_state.page = 'login'
            st.rerun()

    elif st.session_state.logged_in:
        page = st.sidebar.selectbox('Menu', ['View Tasks', 'Create Task', 'Update Task', 'Delete Task', 'Reports', 'Logout'])
        if page == 'View Tasks':
            st.session_state.page = 'view_tasks'
        elif page == 'Create Task':
            st.session_state.page = 'create_task'
        elif page == 'Update Task':
            st.session_state.page = 'update_task'
        elif page == 'Delete Task':
            st.session_state.page = 'delete_task'
        elif page == 'Reports':
            st.session_state.page = 'reports'
        elif page == 'Logout':
            st.session_state.logged_in = False
            st.session_state.user_id = None
            st.session_state.page = 'login'
            st.rerun()

        if st.session_state.page == 'view_tasks':
            st.title('View Tasks')
            tasks = get_tasks(conn, st.session_state.user_id)
            for task in tasks:
                st.write(f'Task {task[0]}: {task[1]} - Due: {task[3]}')

        elif st.session_state.page == 'create_task':
            st.title('Create Task')
            title = st.text_input('Title')
            description = st.text_area('Description')
            due_date = st.text_input('Due Date (YYYY-MM-DD)')
            if st.button('Create Task'):
                try:
                    due_date = parser.parse(due_date).date()
                    create_task(conn, title, description, due_date, st.session_state.user_id)
                    st.success('Task created successfully')
                    st.session_state.page = 'view_tasks'
                    st.rerun()
                except ValueError:
                    st.error('Invalid due date')

        elif st.session_state.page == 'update_task':
            st.title('Update Task')
            task_id = st.text_input('Task ID')
            if st.button('Get Task'):
                task = get_task(conn, int(task_id))
                if task:
                    st.write(f'Task {task[0]}: {task[1]} - Due: {task[3]}')
                    title = st.text_input('Title', value=task[1])
                    description = st.text_area('Description', value=task[2])
                    due_date = st.text_input('Due Date (YYYY-MM-DD)', value=task[3])
                    if st.button('Update Task'):
                        try:
                            due_date = parser.parse(due_date).date()
                            update_task(conn, int(task_id), title, description, due_date)
                            st.success('Task updated successfully')
                            st.session_state.page = 'view_tasks'
                            st.rerun()
                        except ValueError:
                            st.error('Invalid due date')
                else:
                    st.error('Task not found')

        elif st.session_state.page == 'delete_task':
            st.title('Delete Task')
            task_id = st.text_input('Task ID')
            if st.button('Get Task'):
                task = get_task(conn, int(task_id))
                if task:
                    st.write(f'Task {task[0]}: {task[1]} - Due: {task[3]}')
                    if st.button('Delete Task'):
                        if st.button('Confirm Delete'):
                            delete_task(conn, int(task_id))
                            st.success('Task deleted successfully')
                            st.session_state.page = 'view_tasks'
                            st.rerun()
                else:
                    st.error('Task not found')

        elif st.session_state.page == 'reports':
            st.title('Reports')
            st.write('Reports will be displayed here')

if __name__ == '__main__':
    try:
        main()
    except sqlite3.Error as e:
        st.error(f'Database error: {e}')