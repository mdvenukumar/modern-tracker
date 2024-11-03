import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import sqlite3
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import IsolationForest
import json
import base64
import io

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS expenses
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
         date TEXT NOT NULL,
         category TEXT NOT NULL,
         amount REAL NOT NULL,
         description TEXT,
         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
    ''')
    conn.commit()
    return conn

# Initialize session state
if 'db_initialized' not in st.session_state:
    st.session_state.db_initialized = False
    init_db()
    st.session_state.db_initialized = True

# Page Configuration
st.set_page_config(page_title="Expense Tracker", layout="wide")
st.title("💰 Expense Tracker")

# Sidebar Navigation
page = st.sidebar.selectbox(
    "Navigation",
    ["Dashboard", "Add Expense", "Manage Expenses", "Analytics", "Settings"]
)

# Common database functions
def add_expense(date, category, amount, description):
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO expenses (date, category, amount, description)
        VALUES (?, ?, ?, ?)
    ''', (date, category, amount, description))
    conn.commit()
    conn.close()

def get_expenses(start_date=None, end_date=None):
    conn = sqlite3.connect('expenses.db')
    query = "SELECT * FROM expenses"
    if start_date and end_date:
        query += f" WHERE date BETWEEN '{start_date}' AND '{end_date}'"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def delete_expense(expense_id):
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    conn.commit()
    conn.close()

# Category suggestions based on description
CATEGORY_SUGGESTIONS = {
    'grocery': 'Food & Groceries',
    'restaurant': 'Dining Out',
    'uber': 'Transportation',
    'fuel': 'Transportation',
    'netflix': 'Entertainment',
    'movie': 'Entertainment',
    'rent': 'Housing',
    'utility': 'Utilities'
}

def suggest_category(description):
    description = description.lower()
    for key, category in CATEGORY_SUGGESTIONS.items():
        if key in description:
            return category
    return 'Other'

# Dashboard Page
if page == "Dashboard":
    col1, col2 = st.columns(2)
    
    # Get recent expenses
    df = get_expenses()
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
        
        with col1:
            st.subheader("Monthly Spending")
            monthly_spending = df.groupby(df['date'].dt.strftime('%Y-%m'))[['amount']].sum()
            fig = px.line(monthly_spending, x=monthly_spending.index, y='amount')
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            st.subheader("Category Distribution")
            category_spending = df.groupby('category')[['amount']].sum()
            fig = px.pie(category_spending, values='amount', names=category_spending.index)
            st.plotly_chart(fig, use_container_width=True)
        
        # Recent Transactions
        st.subheader("Recent Transactions")
        recent_df = df.sort_values('date', ascending=False).head(5)
        st.dataframe(recent_df[['date', 'category', 'amount', 'description']])
    else:
        st.info("No expenses recorded yet. Start by adding some expenses!")

# Add Expense Page
elif page == "Add Expense":
    st.subheader("Add New Expense")
    
    with st.form("add_expense_form"):
        date = st.date_input("Date", datetime.now())
        amount = st.number_input("Amount", min_value=0.01, step=0.01)
        description = st.text_input("Description")
        
        # Suggest category based on description
        suggested_category = suggest_category(description) if description else "Other"
        categories = ["Food & Groceries", "Dining Out", "Transportation", "Entertainment",
                     "Housing", "Utilities", "Shopping", "Healthcare", "Other"]
        category = st.selectbox("Category", categories, 
                              index=categories.index(suggested_category) if suggested_category in categories else -1)
        
        submitted = st.form_submit_button("Add Expense")
        if submitted:
            add_expense(date.strftime('%Y-%m-%d'), category, amount, description)
            st.success("Expense added successfully!")

# Manage Expenses Page
elif page == "Manage Expenses":
    st.subheader("Manage Expenses")
    
    # Date range filter
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", datetime.now() - timedelta(days=30))
    with col2:
        end_date = st.date_input("End Date", datetime.now())
    
    df = get_expenses(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
    
    if not df.empty:
        # Add sorting functionality
        sort_col = st.selectbox("Sort by", df.columns)
        sort_order = st.radio("Sort order", ["Ascending", "Descending"])
        df = df.sort_values(sort_col, ascending=sort_order=="Ascending")
        
        # Display expenses with delete button
        st.dataframe(df)
        
        # Export to Excel
        if st.button("Export to Excel"):
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df.to_excel(writer, index=False)
            buffer.seek(0)
            b64 = base64.b64encode(buffer.read()).decode()
            href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="expenses.xlsx">Download Excel file</a>'
            st.markdown(href, unsafe_allow_html=True)
    else:
        st.info("No expenses found for the selected date range.")

# Analytics Page
elif page == "Analytics":
    st.subheader("Expense Analytics")
    
    df = get_expenses()
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
        
        # Spending Trends
        st.subheader("Spending Trends")
        monthly_spending = df.groupby(df['date'].dt.strftime('%Y-%m'))[['amount']].sum()
        
        # Forecast future spending
        X = np.arange(len(monthly_spending)).reshape(-1, 1)
        y = monthly_spending['amount'].values
        model = LinearRegression()
        model.fit(X, y)
        
        # Predict next 3 months
        future_months = np.arange(len(monthly_spending), len(monthly_spending) + 3).reshape(-1, 1)
        future_spending = model.predict(future_months)
        
        # Plot actual and predicted spending
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=monthly_spending.index, y=monthly_spending['amount'],
                                name='Actual Spending'))
        fig.add_trace(go.Scatter(x=[f'Forecast {i+1}' for i in range(3)],
                                y=future_spending, name='Forecast'))
        st.plotly_chart(fig, use_container_width=True)
        
        # Anomaly Detection
        st.subheader("Unusual Spending Detection")
        isolation_forest = IsolationForest(contamination=0.1, random_state=42)
        anomalies = isolation_forest.fit_predict(df[['amount']])
        unusual_expenses = df[anomalies == -1]
        if not unusual_expenses.empty:
            st.warning("Unusual spending patterns detected:")
            st.dataframe(unusual_expenses[['date', 'category', 'amount', 'description']])
        else:
            st.success("No unusual spending patterns detected.")
        
        # Category-wise Heatmap
        st.subheader("Category-wise Monthly Spending Heatmap")
        monthly_category = df.pivot_table(
            values='amount',
            index=df['date'].dt.strftime('%Y-%m'),
            columns='category',
            aggfunc='sum',
            fill_value=0
        )
        fig = px.imshow(monthly_category.T,
                       labels=dict(x="Month", y="Category", color="Amount"),
                       aspect="auto")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No expenses recorded yet. Add some expenses to see analytics!")

# Settings Page
elif page == "Settings":
    st.subheader("Settings")
    
    # Backup functionality
    if st.button("Backup Data"):
        df = get_expenses()
        json_str = df.to_json()
        b64 = base64.b64encode(json_str.encode()).decode()
        href = f'<a href="data:application/json;base64,{b64}" download="expenses_backup.json">Download Backup File</a>'
        st.markdown(href, unsafe_allow_html=True)
    
    # Restore functionality
    uploaded_file = st.file_uploader("Restore from backup", type=['json'])
    if uploaded_file is not None:
        try:
            backup_df = pd.read_json(uploaded_file)
            conn = sqlite3.connect('expenses.db')
            backup_df.to_sql('expenses', conn, if_exists='replace', index=False)
            conn.close()
            st.success("Data restored successfully!")
        except Exception as e:
            st.error(f"Error restoring data: {str(e)}")