import asyncio
from dataclasses import dataclass
from datetime import date
from enum import Enum

import pymysql
import sshtunnel
import paramiko

import streamlit as st
import pandas as pd
from agents.sql_agent import SQLAgent
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool
from contextlib import contextmanager
import logging
from typing import Any, Callable, Dict, List, Optional, Generator
from tenacity import retry, stop_after_attempt, wait_exponential

from config import Config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/main.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class FieldType(Enum):
    """Типы полей формы"""
    TEXT = "text"
    NUMBER = "number"
    DATE = "date"
    DATE_RANGE = "date_range"
    SELECT = "select"
    MULTISELECT = "multiselect"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    SLIDER = "slider"
    TEXT_AREA = "text_area"

@dataclass
class FormField:
    """Описание поля формы"""
    name: str
    label: str
    field_type: FieldType
    default: Any = None
    options: List[Any] = None  # для select, multiselect, radio
    min_value: Any = None       # для number, slider, date
    max_value: Any = None       # для number, slider, date
    step: Any = None            # для number, slider
    help_text: str = None
    required: bool = False
    width: int = 12  # 1-12 для колонок (12 = полная ширина)

@dataclass
class ReportConfig:
    """Конфигурация отчета"""
    name: str
    title: str
    description: str
    form_fields: List[FormField]
    generate_func: Callable = None
    icon: str = "📊"
    category: str = "Общие"


class ReportManager:
    
    
    def __init__(self, agent:SQLAgent):
        self.agent=agent
        self.reports: Dict[str, ReportConfig] = {}
        self._register_default_reports()
    
    def _register_default_reports(self):
        """Регистрация стандартных отчетов"""
        
        # Отчет по ключам
        self.register_report(ReportConfig(
            name="report_keya_on_date",
            title="Ключи клиента на дату",
            description="Ключи клиента, установленные на дату среза + ключи отвязанные за 30 дней до даты среза",
            icon="🔑",
            category="Ключи",
            form_fields=[
                FormField(
                    name="report_date",
                    label="Дата среза",
                    field_type=FieldType.DATE,
                    default=(date.today()),
                    required=True
                ),
                FormField(
                    name="contract_id",
                    label="ID договора клиента (Сервер лицензий)",
                    field_type=FieldType.TEXT,                    
                    default="",
                    width=6,
                    required=True
                )
            ],
            generate_func=self._generate_keys_report
        ))

        # Отчет по ключам
        self.register_report(ReportConfig(
            name="get_auto_issued_keys",
            title="Автоматически выданные ключи",
            description="Ключи, выданные Сервером лицензий в автоматическом режиме",
            icon="🔑",
            category="Ключи",
            form_fields=[],
            generate_func=self._generate_auto_keys_report
        ))


    def register_report(self, config: ReportConfig):
        """Регистрация нового отчета"""
        self.reports[config.name] = config
    
    def getReportList(self) -> List[str]:
        """Получить список названий отчетов"""
        return [f"{config.icon} {config.title}" for config in self.reports.values()]

    def getReportCategories(self) -> Dict[str, List[ReportConfig]]:
        """Получить отчеты по категориям"""
        categories = {}
        for report in self.reports.values():
            if report.category not in categories:
                categories[report.category] = []
            categories[report.category].append(report)
        return categories
    
    def getReportConfig(self, report_name: str) -> Optional[ReportConfig]:
        """Получить конфигурацию отчета по имени"""
        # Убираем иконку из имени если есть
        clean_name = report_name.split(' ', 1)[-1] if ' ' in report_name else report_name
        for report in self.reports.values():
            if report.title == clean_name or report.name == clean_name:
                return report
        return None
    
    def render_form(self, report_config: ReportConfig) -> Dict[str, Any]:
        """Отрисовка формы для отчета"""
        st.subheader(f"{report_config.icon} {report_config.title}")
        st.caption(report_config.description)
        
        form_values = {}
        
        # Группировка полей по рядам (по 12 колонок)
        current_row = []
        row_width = 0
        
        for field in report_config.form_fields:
            # Начинаем новый ряд если текущий заполнен
            if row_width + field.width > 12:
                # Отрисовываем текущий ряд
                if current_row:
                    cols = st.columns([f.width for f in current_row])
                    for i, f in enumerate(current_row):
                        with cols[i]:
                            form_values[f.name] = self._render_field(f)
                current_row = []
                row_width = 0
            
            current_row.append(field)
            row_width += field.width
        
        # Отрисовываем последний ряд
        if current_row:
            cols = st.columns([f.width for f in current_row])
            for i, f in enumerate(current_row):
                with cols[i]:
                    form_values[f.name] = self._render_field(f)
        
        return form_values
    
    def _render_field(self, field: FormField) -> Any:
        """Отрисовка одного поля формы"""
        field_key = f"{field.name}_{id(field)}"
        
        if field.field_type == FieldType.TEXT:
            return st.text_input(
                field.label,
                value=field.default or "",
                help=field.help_text,
                key=field_key
            )
            
        elif field.field_type == FieldType.TEXT_AREA:
            return st.text_area(
                field.label,
                value=field.default or "",
                help=field.help_text,
                key=field_key
            )
            
        elif field.field_type == FieldType.NUMBER:
            return st.number_input(
                field.label,
                value=field.default or 0,
                min_value=field.min_value,
                max_value=field.max_value,
                step=field.step or 1,
                help=field.help_text,
                key=field_key
            )
            
        elif field.field_type == FieldType.DATE:
            return st.date_input(
                field.label,
                value=field.default or date.today(),
                min_value=field.min_value,
                max_value=field.max_value,
                help=field.help_text,
                key=field_key,
                format="DD-MM-YYYY"
            )
            
        elif field.field_type == FieldType.DATE_RANGE:
            default_start, default_end = field.default or (date.today(), date.today())
            col1, col2 = st.columns(2)
            with col1:
                start = st.date_input(
                    f"{field.label} (с)",
                    value=default_start,
                    min_value=field.min_value,
                    max_value=field.max_value,
                    key=f"{field_key}_start"
                )
            with col2:
                end = st.date_input(
                    f"{field.label} (по)",
                    value=default_end,
                    min_value=field.min_value,
                    max_value=field.max_value,
                    key=f"{field_key}_end"
                )
            return (start, end)
            
        elif field.field_type == FieldType.SELECT:
            return st.selectbox(
                field.label,
                options=field.options or [],
                index=field.options.index(field.default) if field.default in field.options else 0,
                help=field.help_text,
                key=field_key
            )
            
        elif field.field_type == FieldType.MULTISELECT:
            return st.multiselect(
                field.label,
                options=field.options or [],
                default=field.default or [],
                help=field.help_text,
                key=field_key
            )
            
        elif field.field_type == FieldType.CHECKBOX:
            return st.checkbox(
                field.label,
                value=field.default or False,
                help=field.help_text,
                key=field_key
            )
            
        elif field.field_type == FieldType.RADIO:
            return st.radio(
                field.label,
                options=field.options or [],
                index=field.options.index(field.default) if field.default in field.options else 0,
                help=field.help_text,
                key=field_key,
                horizontal=True
            )
            
        elif field.field_type == FieldType.SLIDER:
            return st.slider(
                field.label,
                min_value=field.min_value or 0,
                max_value=field.max_value or 100,
                value=field.default or 50,
                step=field.step or 1,
                help=field.help_text,
                key=field_key
            )
        
        return None
    
    def generate_report(self, report_name: str, form_data: Dict[str, Any]) -> pd.DataFrame:
        """Генерация отчета по данным формы"""
        report_config = self.getReportConfig(report_name)
        if not report_config or not report_config.generate_func:
            return pd.DataFrame({"error": ["Отчет не найден"]})
        
        return report_config.generate_func(form_data)
    
    # Методы генерации отчетов
    def _generate_keys_report(self, params: Dict) -> pd.DataFrame:
        """Генерация отчета по ключам"""
        contract_id = params.get('contract_id')
        report_date = params.get('report_date').strftime("%Y-%m-%d") + " 00:00:00"
        logging.info(f"""Генерация отчета по ключам. Параметры: contract_id={contract_id},report_date={report_date}""")
        #reportDate
        #SET @TargetDate = '2026-03-03 00:00:00';

        sql=f"""

    SELECT 
        p.name AS 'Партнер',
        c.name AS 'Клиент',
        cc.name AS 'Юр.лицо',
        con.name AS 'Договор',
        IFNULL(f.name, 'Без объекта') AS 'Объект',
        lk.sernum AS 'Серийный номер ключа',
        CONCAT(a.name, " ", av.name) AS 'ПО',
        lk.key_type AS 'Тип Ключа',
        CASE 
            WHEN ka.status = -1 AND ka.dt_status BETWEEN DATE_SUB("{report_date}", INTERVAL 1 MONTH) AND "{report_date}" THEN 'Отвязан за период'
            ELSE 'Установлен на дату'
        END AS 'Статус',
        ka.dt_assign AS 'Дата установки',
        CASE 
            WHEN ka.status = -1 AND ka.dt_status BETWEEN DATE_SUB("{report_date}", INTERVAL 1 MONTH) AND "{report_date}" THEN ''
            ELSE ic.its_name
        END AS 'Договор ИТС',
        CASE 
            WHEN ka.status = -1 AND ka.dt_status BETWEEN DATE_SUB("{report_date}", INTERVAL 1 MONTH) AND "{report_date}" THEN ''
            ELSE ic.dt_end
        END AS 'Обновление до',    
        CASE 
            WHEN ka.status = -1 AND ka.dt_status BETWEEN DATE_SUB("{report_date}", INTERVAL 1 MONTH) AND "{report_date}" THEN ka.dt_status    	
            ELSE ""
        END AS 'Дата отвязки',
        CASE 
            WHEN ka.status = -1 AND ka.dt_status BETWEEN DATE_SUB("{report_date}", INTERVAL 1 MONTH) AND "{report_date}" THEN ka.reason_text
            ELSE ""
        END AS 'Причина отвязки'    	
    FROM key_assignment ka    
        INNER JOIN lic_key lk ON ka.key_id = lk.id    
        LEFT JOIN its_contract ic ON ic.id=ka.its_contract_id 
        INNER JOIN client_contract con ON ka.contract_id = con.id    
        INNER JOIN client_contragent cc ON con.contragent_id = cc.id
        INNER JOIN client c ON cc.client_id = c.id
        INNER JOIN partner p ON c.partner_id = p.id    
        LEFT JOIN filial f ON ka.filial_id = f.id
        INNER JOIN app_version av ON av.id=ka.app_version_id 
        INNER JOIN app a ON a.id=av.app_id 

    WHERE con.dt_archive IS NULL AND con.id={contract_id}    
        AND (
                ((ka.dt_assign <= "{report_date}" AND ka.status = 0) OR (ka.status = -1 AND ka.dt_status > "{report_date}"))
                OR  
                (ka.status = -1 AND ka.dt_status BETWEEN DATE_SUB("{report_date}", INTERVAL 1 MONTH) AND "{report_date}")
            )
        
    ORDER BY 
        p.name, c.name, cc.name, con.name, ka.dt_assign;
    """
        result = asyncio.run(self.agent.process_report_query(sql))
        
        return pd.DataFrame(result["data"])
    
     
    def _generate_auto_keys_report(self, params: Dict) -> pd.DataFrame:
        """Генерация отчета по автоматически выданным ключам"""
        
        logging.info(f"""Генерация отчета по автоматически выданным ключам""")        

        sql=f"""
            SELECT 
                p.name AS "Партнер",
                c.name AS "Клиент",
                cc.name AS "Контрагент",
                li.serial_num AS "Серийный номер",	 
                CONCAT(li.app_type ," ",li.app_version) AS "Продукт",
                li.dt_assign AS "Дата выдачи",
                li.expiration_date AS "Дата окончания лицензии",
                li.build_date AS "Дата доступного релиза",
                CASE WHEN li.expiration_date<NOW() THEN "Просрочена" ELSE "Действующая" END AS "Статус"	
            FROM licencecenter.licence_info li
            INNER JOIN licencecenter.client_contragent cc  ON cc.uuid=li.contragentid 
            INNER JOIN licencecenter.client c ON c.id=cc.client_id 
            INNER JOIN licencecenter.partner p ON p.id=c.partner_id   
            ORDER BY p.name, c.name, cc.name;
    """
        result = asyncio.run(self.agent.process_report_query(sql))
        
        return pd.DataFrame(result["data"])