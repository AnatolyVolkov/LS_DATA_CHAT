# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import logging
import asyncio
from contextlib import contextmanager

from database.connection import db_connection
from agents.sql_agent import SQLAgent
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize session state
if 'agent' not in st.session_state:
    st.session_state.agent = SQLAgent()
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'connected' not in st.session_state:
    st.session_state.connected = False
if 'query_history' not in st.session_state:
    st.session_state.query_history = []

def init_connection():
    """Initialize database connection"""
    with st.spinner("Подключение к базе данных..."):
        if db_connection.connect():
            st.session_state.connected = True
            st.success("✅ Подключено к базе данных")
            logger.info("Database connection established")
        else:
            st.error("❌ Не удалось подключиться к базе данных")
            st.session_state.connected = False

def display_results(data, analysis, visualization):
    """Display query results with visualizations"""
    if data:
        df = pd.DataFrame(data)
        
        # Show statistics
        if analysis:
            with st.expander("📊 Статистика", expanded=False):
                col1, col2, col3 = st.columns(3)
                col1.metric("Всего строк", analysis.get('row_count', 0))
                
                if analysis.get('numeric_stats'):
                    st.subheader("Числовые показатели")
                    for col, stats in analysis['numeric_stats'].items():
                        st.write(f"**{col}**")
                        cols = st.columns(4)
                        if stats.get('min') is not None:
                            cols[0].metric("Мин", f"{stats['min']:.2f}")
                        if stats.get('max') is not None:
                            cols[1].metric("Макс", f"{stats['max']:.2f}")
                        if stats.get('mean') is not None:
                            cols[2].metric("Среднее", f"{stats['mean']:.2f}")
                        if stats.get('sum') is not None:
                            cols[3].metric("Сумма", f"{stats['sum']:.2f}")
        
        # Show visualization
        if visualization:
            st.subheader("📈 Визуализация")
            
            if visualization['type'] == 'bar':
                fig = px.bar(
                    df, 
                    x=visualization['x_column'], 
                    y=visualization['y_column'],
                    title=f"{visualization['y_column']} по {visualization['x_column']}"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            elif visualization['type'] == 'pie':
                fig = px.pie(
                    df,
                    values=visualization['value_column'],
                    names=visualization.get('label_column'),
                    title=f"Распределение {visualization['value_column']}"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            elif visualization['type'] == 'scatter':
                fig = px.scatter(
                    df,
                    x=visualization['x_column'],
                    y=visualization['y_column'],
                    title=f"{visualization['y_column']} от {visualization['x_column']}"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            elif visualization['type'] == 'line' and 'date' in df.columns:
                fig = px.line(
                    df,
                    x='date',
                    y=visualization.get('y_column', df.select_dtypes(include=['number']).columns[0]),
                    title="Динамика по датам"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Show data table
        st.subheader("📋 Данные")
        st.dataframe(df, use_container_width=True)
        
        # Export options
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Скачать CSV",
            data=csv,
            file_name=f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

def main():
    st.set_page_config(
        page_title="Сервер лицензий - Чат-бот аналитик (v0.1.3)",
        page_icon="🔐",
        layout="wide"
    )
    
    # Custom CSS
    st.markdown("""
    <style>
    .stApp {
        background-color: #f5f7f9;
    }
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    .assistant-message {
        background-color: #f3e5f5;
        border-left: 4px solid #9c27b0;
    }
    .sql-box {
        background-color: #2d2d2d;
        color: #f8f8f2;
        padding: 1rem;
        border-radius: 5px;
        font-family: monospace;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🔐 Сервер лицензий - Аналитический чат-бот</h1>
        <p>Задавайте вопросы о лицензиях, ключах, клиентах и получайте аналитику в реальном времени</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("🔌 Подключение")
        
        if not st.session_state.connected:
            if st.button("🔄 Подключиться к БД", type="primary", use_container_width=True):
                init_connection()
                if st.session_state.connected:
                    st.rerun()
        else:
            st.success("✅ Подключено к БД")
            if st.button("❌ Отключиться", use_container_width=True):
                db_connection.disconnect()
                st.session_state.connected = False
                st.rerun()
        
        st.divider()
        
        # st.header("📊 Быстрые запросы")
        # quick_queries = {
        #     "Всего ключей": "SELECT COUNT(*) as total_keys FROM lic_key WHERE dt_archive IS NULL",
        #     "Активные ключи": """
        #         SELECT COUNT(DISTINCT k.id) as active_keys 
        #         FROM lic_key k 
        #         JOIN key_assignment ka ON k.id = ka.key_id 
        #         WHERE k.dt_archive IS NULL AND ka.status = 0
        #     """,
        #     "Топ-10 клиентов": """
        #         SELECT c.name, COUNT(ka.id) as key_count
        #         FROM client c
        #         JOIN lic_key k ON c.id = k.client_id
        #         JOIN key_assignment ka ON k.id = ka.key_id
        #         WHERE c.dt_archive IS NULL AND ka.status = 0
        #         GROUP BY c.id, c.name
        #         ORDER BY key_count DESC
        #         LIMIT 10
        #     """,
        #     "Ключи по типам": """
        #         SELECT key_type, COUNT(*) as count 
        #         FROM lic_key 
        #         WHERE dt_archive IS NULL 
        #         GROUP BY key_type
        #     """
        # }
        
        # for query_name, query in quick_queries.items():
        #     if st.button(query_name, use_container_width=True):
        #         st.session_state.user_input = query_name
        #         st.session_state.run_quick_query = True
        
        st.divider()
        
        st.header("📁 История запросов")
        for i, q in enumerate(st.session_state.query_history[-5:]):
            if st.button(f"🔄 {q[:30]}...", key=f"hist_{i}", use_container_width=True):
                st.session_state.user_input = q
                st.session_state.run_quick_query = True
    
    # Main chat area
    chat_container = st.container()
    
    with chat_container:
        # Display chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                
                # Show SQL if available
                if "sql" in message and message["sql"]:
                    with st.expander("Показать SQL запрос"):
                        st.code(message["sql"], language="sql")
                
                # Show data if available
                if "data" in message and message["data"]:
                    display_results(
                        message["data"], 
                        message.get("analysis"), 
                        message.get("visualization")
                    )
    
    # Chat input
    if prompt := st.chat_input("Задайте вопрос о лицензиях..."):
        if not st.session_state.connected:
            st.error("❌ Сначала подключитесь к базе данных")
            st.stop()
        
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Process query
        with st.chat_message("assistant"):
            with st.spinner("🔍 Анализирую запрос..."):
                # Run agent
                result = asyncio.run(st.session_state.agent.process_query(prompt))
                
                # Display response
                st.markdown(result['response'])
                
                # Show SQL
                if result.get('sql'):
                    with st.expander("Показать SQL запрос"):
                        st.code(result['sql'], language="sql")
                
                # Display results
                if result.get('data'):
                    display_results(
                        result['data'],
                        result.get('analysis'),
                        result.get('visualization')
                    )
                
                # Save to history
                st.session_state.query_history.append(prompt)
                
                # Save message
                message = {
                    "role": "assistant", 
                    "content": result['response'],
                    "sql": result.get('sql'),
                    "data": result.get('data'),
                    "analysis": result.get('analysis'),
                    "visualization": result.get('visualization')
                }
                st.session_state.messages.append(message)

if __name__ == "__main__":
    main()