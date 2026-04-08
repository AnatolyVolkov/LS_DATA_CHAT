# agents/sql_agent.py (исправленная версия)
import json
import logging
from typing import Dict, List, Any, Optional, TypedDict
import pandas as pd
from datetime import datetime

from database.connection import db_connection
from database.schema import get_schema_text
from llm.deepseek import DeepSeekLLM

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/main.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class AgentState(TypedDict):
    """State for the SQL agent"""
    messages: List[Dict[str, str]]
    user_query: str
    sql_query: Optional[str]
    query_result: Optional[List[Dict]]
    error: Optional[str]
    analysis: Optional[Dict]
    visualization_data: Optional[Dict]
    context: Dict[str, Any]

class SQLAgent:
    """Agent for handling database queries and analysis"""
    
    def __init__(self):
        self.llm = DeepSeekLLM()
        self.schema = get_schema_text()
    
    async def process_query(self, user_query: str, readySQL: str="", readySQLQuery:str="") -> Dict:
        """Process user query through the agent workflow"""
        state = {
            "messages": [{"role": "user", "content": user_query}],
            "user_query": user_query,
            "sql_query": None,
            "query_result": None,
            "error": None,
            "analysis": None,
            "visualization_data": None,
            "context": {}
        }
        
        try:
            
            if readySQL=="" and readySQL=="":
                # Step 1: Understand query
                state = await self._understand_query(state)
                logging.info(state)
                if state.get("error"):
                    return self._format_response(state)
            
                # Step 2: Generate SQL
                state = await self._generate_sql(state)
                logging.info(state)
                if state.get("error"):
                    return self._format_response(state)
            else:
                state["sql_query"]=readySQL
                state["user_query"]=readySQLQuery
            
            # Step 3: Validate SQL
            state = self._validate_sql(state)
            logging.info(state)
            if state.get("error"):
                return self._format_response(state)
            
            # Step 4: Execute query
            state = await self._execute_query(state)
            logging.info(state)
            if state.get("error"):
                return self._format_response(state)
            
            # Step 5: Analyze results
            state = self._analyze_results(state)
            logging.info(state)
            
            # Step 6: Generate response
            state = await self._generate_response(state)
            logging.info(state)
            
        except Exception as e:
            logging.error(f"Error processing query: {e}")
            state["error"] = str(e)
        
        return self._format_response(state)
    

    async def process_report_query(self, reportSQL:str) -> Dict:
        """Process user query through the agent workflow"""
        state = {
            "messages": "",
            "user_query": "",
            "sql_query": reportSQL,
            "query_result": None,
            "error": None,
            "analysis": None,
            "visualization_data": None,
            "context": {}
        }
        
        try:
            
            # Step 3: Validate SQL
            state = self._validate_sql(state)
            logging.info(state)
            if state.get("error"):
                return self._format_response(state)
            
            # Step 4: Execute query
            state = await self._execute_query(state)
            logging.info(state)
            if state.get("error"):
                return self._format_response(state)            
            
        except Exception as e:
            logging.error(f"Error processing query: {e}")
            state["error"] = str(e)
        
        return self._format_response(state)
    
    async def _understand_query(self, state: AgentState) -> AgentState:
        """Understand the user's query and extract intent"""
        prompt = f"""
        Ты - аналитик данных сервера лицензий. Проанализируй запрос пользователя и определи:
        1. Какую информацию нужно получить из БД
        2. Какие таблицы потребуются
        3. Нужна ли агрегация данных
        4. Требуется ли визуализация
        
        Запрос пользователя: {state['user_query']}
        
        Ответь в формате JSON:
        {{
            "intent": "краткое описание цели",
            "required_tables": ["таблица1", "таблица2"],
            "needs_aggregation": true/false,
            "needs_visualization": true/false
        }}
        """
        
        try:
            response = await self.llm.ainvoke(prompt)
            # Clean response to ensure valid JSON
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.endswith("```"):
                response = response[:-3]
            
            context = json.loads(response)
            state['context'] = context
        except Exception as e:
            logging.error(f"Error understanding query: {e}")
            state['error'] = "Не удалось понять запрос"
        
        return state
    
    async def _generate_sql(self, state: AgentState) -> AgentState:
        """Generate SQL query based on user request"""
        prompt = f"""
        Схема базы данных:
        {self.schema}
        
        Запрос пользователя: {state['user_query']}
        
        Сгенерируй SQL запрос (только SELECT) для получения данных.
        Важно: 
        - Используй ONLY FULL GROUP BY если нужна агрегация
        - Добавляй LIMIT где уместно (обычно 100-1000 записей)
        - Не учитывай архивированные записи в тех таблица, которые имеют поле dt_archive (dt_archive IS NULL для активных)
        - Используй понятные алиасы
        - НЕ используй INSERT, UPDATE, DELETE, DROP, ALTER        
        - Используй JOIN client_contract с client_contragent
        - Используй JOIN client_contragent с client
        - Используй JOIN client с partner
        - Используй JOIN lic_key с key_assignment
        - Недопустимо использовать JOIN client_document_application с key_assignment, вместо него используй подзапросы
        - Если не сказано иное - сравнивай переданное значение ключа с полем sernum, а не id таблицы lic_key
        
        Ответь ТОЛЬКО SQL запросом, без пояснений.
        """
        
        try:
            sql_query = await self.llm.ainvoke(prompt)
            sql_query = sql_query.strip().replace('```sql', '').replace('```', '').strip()
            
            # Basic validation
            if not sql_query.upper().startswith('SELECT'):
                raise ValueError("Generated query is not SELECT")
            
            state['sql_query'] = sql_query
            logging.info(f"Generated SQL: {sql_query}")
        except Exception as e:
            logging.error(f"Error generating SQL: {e}")
            state['error'] = "Не удалось сгенерировать SQL запрос"
        
        return state
    
    def _validate_sql(self, state: AgentState) -> AgentState:
        """Validate SQL query for safety"""
        sql = state.get('sql_query', '')
        
        # Check for dangerous keywords
        dangerous = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'TRUNCATE', 
                     'ALTER', 'CREATE', 'REPLACE', 'GRANT']
        
        sql_upper = sql.upper()
        for word in dangerous:
            if word in sql_upper:
                state['error'] = f"Запрос содержит запрещенную операцию: {word}"
                return state
        
        return state
    
    async def _execute_query(self, state: AgentState) -> AgentState:
        """Execute the SQL query"""
        try:
            sql = state['sql_query']
            logging.info(f"Begin query execution. SQL: {sql}")
            result = db_connection.execute_query(sql)
            
            # Convert to list of dicts
            query_result = []
            if result:
                # Get column names from the first row
                if hasattr(result[0], '_fields'):
                    columns = result[0]._fields
                    for row in result:
                        query_result.append(dict(zip(columns, row)))
                else:
                    # Fallback for different result formats
                    for row in result:
                        if hasattr(row, '_asdict'):
                            query_result.append(row._asdict())
                        else:
                            query_result.append(dict(row))
            
            state['query_result'] = query_result
            logging.info(f"Query executed, returned {len(query_result)} rows")
            
        except Exception as e:
            logging.error(f"Error executing query: {e}")
            state['error'] = f"Ошибка выполнения запроса: {str(e)}"
        
        return state
    
    def _analyze_results(self, state: AgentState) -> AgentState:
        """Analyze query results"""
        results = state.get('query_result', [])
        if not results:
            state['analysis'] = {"row_count": 0}
            return state
        
        try:
            df = pd.DataFrame(results)
            
            # Basic statistics
            stats = {
                "row_count": len(results),
                "columns": list(df.columns)
            }
            
            # Convert date columns
            for col in df.columns:
                if df[col].dtype == 'object':
                    # Try to convert to datetime
                    try:
                        df[col] = pd.to_datetime(df[col])
                    except:
                        pass
            
            # Numeric statistics
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                stats['numeric_stats'] = {}
                for col in numeric_cols:
                    stats['numeric_stats'][col] = {
                        "min": float(df[col].min()) if not pd.isna(df[col].min()) else None,
                        "max": float(df[col].max()) if not pd.isna(df[col].max()) else None,
                        "mean": float(df[col].mean()) if not pd.isna(df[col].mean()) else None,
                        "sum": float(df[col].sum()) if not pd.isna(df[col].sum()) else None
                    }
            
            state['analysis'] = stats
            
            # Prepare visualization if needed
            if state.get('context', {}).get('needs_visualization', False):
                state['visualization_data'] = self._prepare_visualization(df)
                
        except Exception as e:
            logging.error(f"Error analyzing results: {e}")
            state['analysis'] = {"row_count": len(results), "error": str(e)}
        
        return state
    
    def _prepare_visualization(self, df: pd.DataFrame) -> Dict:
        """Prepare data for visualization"""
        viz_data = {
            "type": "table",
            "data": df.to_dict('records'),
            "columns": list(df.columns)
        }
        
        # Determine chart type based on data
        if len(df) > 0 and len(df) < 1000:  # Don't try to visualize too many rows
            numeric_cols = list(df.select_dtypes(include=['number']).columns)
            categorical_cols = list(df.select_dtypes(include=['object']).columns)
            date_cols = list(df.select_dtypes(include=['datetime64']).columns)
            
            if len(numeric_cols) >= 1:
                if len(categorical_cols) >= 1 and len(df) < 50:
                    viz_data["type"] = "bar"
                    viz_data["x_column"] = categorical_cols[0]
                    viz_data["y_column"] = numeric_cols[0]
                elif len(date_cols) >= 1:
                    viz_data["type"] = "line"
                    viz_data["x_column"] = date_cols[0]
                    viz_data["y_column"] = numeric_cols[0]
                elif len(numeric_cols) >= 2:
                    viz_data["type"] = "scatter"
                    viz_data["x_column"] = numeric_cols[0]
                    viz_data["y_column"] = numeric_cols[1]
        
        return viz_data
    
    async def _generate_response(self, state: AgentState) -> AgentState:
        """Generate natural language response"""
        prompt = f"""
        Запрос пользователя: {state['user_query']}
        
        Результаты запроса: {json.dumps(state.get('query_result', [])[:10], ensure_ascii=False, default=str)}
        
        Анализ данных: {json.dumps(state.get('analysis', {}), ensure_ascii=False, default=str)}
        
        Сгенерируй понятный ответ на русском языке, объясняющий результаты.
        Если есть визуализация, укажи на это.
        Используй цифры и факты из результатов.
        Будь краток и информативен.
        """
        
        try:
            response = await self.llm.ainvoke(prompt)
        except Exception as e:
            logging.error(f"Error generating response: {e}")
            response = "Извините, не удалось сформировать ответ"
        
        state['messages'].append({
            "role": "assistant",
            "content": response
        })
        
        return state
    
    def _format_response(self, state: AgentState) -> Dict:
        """Format the final response"""
        if state.get('error'):
            response = f"Извините, произошла ошибка: {state['error']}"
        else:
            response = state['messages'][-1]['content'] if state['messages'] else "Готово"
        
        return {
            "response": response,
            "data": state.get('query_result'),
            "analysis": state.get('analysis'),
            "visualization": state.get('visualization_data'),
            "error": state.get('error'),
            "sql": state.get('sql_query')
        }