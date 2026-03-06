# database/schema.py
"""Полная схема базы данных сервера лицензий для агента"""
import json

SCHEMA_INFO = {
    "tables": {        
        "app": {
            "description": "Приложения/программное обеспечение/ПО",
            "columns": {
                "id": "bigint - идентификатор приложения",
                "parent_id": "bigint - родительское приложение",
                "id_1c": "varchar(128) - идентификатор в 1С",
                "name": "varchar(512) - название приложения",                                
                "is_counting_in_remains": "tinyint - учитывать при расчете остатков",
                "app_type": "varchar(50) - тип приложения"
            }
        },
        "app_feature": {
            "description": "Связь приложений с функциями/модулями",
            "columns": {
                "feature_id": "bigint - идентификатор функции",
                "app_type": "varchar(50) - тип приложения"
            }
        },
        "app_key_type": {
            "description": "Типы ключей для приложений",
            "columns": {
                "id": "bigint - идентификатор",
                "app_id": "bigint - идентификатор приложения",
                "key_type": "varchar(30) - тип ключа"
            }
        },
        "app_version": {
            "description": "Версии приложений",
            "columns": {
                "id": "bigint - идентификатор версии",
                "app_id": "bigint - идентификатор приложения",
                "id_1c": "varchar(128) - идентификатор в 1С",
                "name": "varchar(512) - название версии",
                "combined_index": "bigint - составной индекс",
                "dt_create": "datetime - дата создания",
                "dt_begin": "datetime - дата начала действия",
                "dt_complete": "datetime - дата завершения"
            }
        },
        "ci_type": {
            "description": "Типы конфигурационных единиц (Configuration Items)",
            "columns": {
                "id": "bigint - идентификатор типа CI",
                "parent_id": "bigint - родительский тип",
                "sd_id": "bigint - идентификатор в Service Desk",
                "name": "varchar(512) - название типа",
                "id_1c": "varchar(32) - идентификатор в 1С",
                "lic_code": "bigint - код лицензии",
                "key_type": "varchar(30) - тип ключа"
            }
        },
        "client": {
            "description": "Клиенты (организации-пользователи ПО)",
            "columns": {
                "id": "bigint - идентификатор клиента",
                "client_type_id": "bigint - тип клиента",
                "partner_id": "bigint - идентификатор партнера",
                "filial_id": "bigint - идентификатор филиала",
                "id_1c": "varchar(16) - идентификатор в 1С",
                "name": "varchar(1024) - название клиента",
                "contact": "varchar(4000) - контактная информация",
                "comments": "varchar(4000) - комментарии",
                "dt_archive": "datetime - дата архивации",
                "contract_type_id": "bigint - тип договора по умолчанию",
                "id_1c_ri": "varchar(128) - идентификатор в 1С Ритейл-интеграции"
            }
        },
        "client_contragent": {
            "description": "Контрагенты клиентов",
            "columns": {
                "id": "bigint - идентификатор контрагента",
                "client_id": "bigint - идентификатор клиента",
                "id_1c": "varchar(32) - идентификатор в 1С",
                "name": "varchar(1024) - название контрагента",
                "inn": "varchar(16) - ИНН",
                "contact": "varchar(4000) - контактная информация",
                "comments": "varchar(4000) - комментарии",
                "dt_archive": "datetime - дата архивации",
                "uuid": "varchar(36) - UUID",
                "id_1c_ri": "varchar(128) - идентификатор в 1С Ритейл-интеграции"
            }
        },
        "client_contract": {
            "description": "Договоры с клиентами",
            "columns": {
                "id": "bigint - идентификатор договора",
                "contract_type_id": "bigint - тип договора",                
                "contragent_id": "bigint - идентификатор контрагента",
                "id_1c": "varchar(32) - идентификатор в 1С",
                "name": "varchar(1024) - название договора",
                "prolongation_step": "int - период продления лицензии в месяцах",
                "overtime": "int - дополнительное время в днях",
                "dt_begin": "datetime - дата начала действия",
                "dt_check": "datetime - лицензировано до",
                "solution_id": "bigint - решение менеджера о продлении",
                "dt_solution": "datetime - дата принятия решения",
                "dt_archive": "datetime - дата архивации",
                "dt_overtime_check": "datetime - дата окончания лицензии",
                "dt_update_end": "datetime - дата окончания обновления ПО",
                "is_tempory": "tinyint - признак временного контракта",
                "comments": "varchar(255) - комментарии",
                "is_forbidden_keys_installing": "tinyint - запрет установки ключей"
            }
        },       
        "client_document_application": {
            "description": "Документы продажи приложений клиентам",
            "columns": {
                "id": "bigint - идентификатор документа",
                "contract_id": "bigint - идентификатор договора",
                "app_version_id": "bigint - версия приложения",
                "dt_accept": "datetime - дата продажи",
                "lic_count": "int - количество лицензий",
                "dt_archive": "datetime - дата архивации",
                "comments": "varchar(4000) - комментарии",
                "user_id": "bigint - пользователь",
                "reason_archive": "varchar(4000) - причина архивации"
            }
        },
        "client_document_feature": {
            "description": "Документы продажи модулей клиентам",
            "columns": {
                "id": "bigint - идентификатор документа",
                "contract_id": "bigint - идентификатор договора",
                "feature_id": "bigint - идентификатор модуля",
                "dt_accept": "datetime - дата продажи",
                "lic_count": "int - количество лицензий",
                "dt_archive": "datetime - дата архивации",
                "comments": "varchar(4000) - комментарии",
                "user_id": "bigint - пользователь",
                "reason_archive": "varchar(4000) - причина архивации",
                "is_tempory": "tinyint - признак временного модуля",
                "tempory_date_complete": "datetime - дата окончания временного модуля",
                "auto_install_app_version_id": "bigint - версия для автоустановки",
                "is_not_considered_during_migration": "tinyint - не учитывать при миграции"
            }
        },
        "client_type": {
            "description": "Типы клиентов",
            "columns": {
                "id": "bigint - идентификатор типа",
                "parent_id": "bigint - родительский тип",
                "name": "varchar(64) - название типа"
            }
        },
        "contract_type": {
            "description": "Типы договоров",
            "columns": {
                "id": "bigint - идентификатор типа",
                "name": "varchar(128) - название типа",
                "is_prolongated": "tinyint - пролонгируется",
                "enable_extend": "tinyint - разрешено продление",
                "do_export": "tinyint - экспортировать",
                "is_service": "tinyint - сервисный",
                "is_sale": "tinyint - продажа"
            }
        },
        "country": {
            "description": "Страны",
            "columns": {
                "id": "bigint - идентификатор страны",
                "name": "varchar(15) - название страны",
                "is_default": "tinyint - по умолчанию"
            }
        },
        "feature": {
            "description": "Модули/функции программного обеспечения",
            "columns": {
                "id": "bigint - идентификатор модуля",
                "name": "varchar(128) - название модуля",
                "licence_name": "varchar(128) - название в лицензии",
                "is_default": "tinyint - поставляется в комплекте (1) или оплачивается (0)"
            }
        },
        "filial": {
            "description": "Филиалы / объекты",
            "columns": {
                "id": "bigint - идентификатор филиала",
                "parent_id": "bigint - родительский филиал",
                "filial_type_id": "bigint - тип филиала",
                "town_id": "bigint - город",
                "name": "varchar(1024) - название филиала",
                "id_1c": "varchar(32) - идентификатор в 1С",
                "short_name": "varchar(128) - краткое название",
                "signature": "varchar(512) - подпись",
                "address": "varchar(4000) - адрес",
                "comments": "varchar(4000) - комментарии",
                "contact": "varchar(4000) - контакты",
                "dt_archive": "datetime - дата архивации"
            }
        },
        "filial_type": {
            "description": "Типы филиалов / объектов",
            "columns": {
                "id": "bigint - идентификатор типа",
                "parent_id": "bigint - родительский тип",
                "name": "varchar(64) - название типа",
                "is_default": "tinyint - по умолчанию"
            }
        },       
        "its_contract": {
            "description": "Договоры ИТС (Информационно-технологическое сопровождение)",
            "columns": {
                "id": "bigint - идентификатор договора ИТС",
                "client_contract_id": "bigint - идентификатор клиентского договора",
                "its_name": "varchar(1024) - название ИТС",
                "dt_end": "datetime - дата окончания",
                "total_key_count": "bigint - общее количество ключей",
                "is_contract_default": "tinyint - договор по умолчанию",
                "comments": "varchar(255) - комментарии",
                "its_monitoring": "varchar(30) - мониторинг ИТС",
                "id_1c_ri": "varchar(128) - идентификатор в 1С Ритейл-интеграции"
            }
        },
        "key_assignment": {
            "description": "Привязка/установка ключей к объектам (филиалам, договорам)",
            "columns": {
                "id": "bigint - идентификатор привязки",
                "key_id": "bigint - идентификатор ключа",
                "contract_id": "bigint - идентификатор договора",
                "filial_id": "bigint - идентификатор филиала",
                "app_version_id": "bigint - версия приложения",
                "hw_signature": "varchar(512) - аппаратная подпись",
                "dt_assign": "datetime - дата привязки",
                "dt_expiry": "datetime - дата истечения",
                "dt_status": "datetime - дата смены статуса",
                "is_fixed": "tinyint - фиксированная привязка",
                "reason_text": "varchar(4000) - причина",
                "status": "tinyint - статус (0 - активна, -1 - отвязана)",
                "its_contract_id": "bigint - внешний ключ ИТС"                
            }
        },
        "key_assignment_feature": {
            "description": "Привязка/установка модулей к ключам",
            "columns": {
                "id": "bigint - идентификатор привязки",
                "feature_id": "bigint - идентификатор модуля",
                "key_assignment_id": "bigint - идентификатор привязки ключа",
                "feature_count": "smallint - количество модулей",
                "dt_assign": "timestamp - дата установки модуля",
                "status": "tinyint - статус (0 - активно, -1 - отвязано)",
                "dt_status": "datetime - дата смены статуса",
                "end_date": "datetime - дата окончания",
                "feature_spec_id": "bigint - идентификатор спецификации модуля"
            }
        },
        "lic_key": {
            "description": "Лицензионные ключи",
            "columns": {
                "id": "bigint - идентификатор ключа",
                "key_type": "varchar(30) - тип ключа",
                "client_id": "bigint - идентификатор клиента",                                
                "sernum": "varchar(64) - серийный номер",                
                "dt_archive": "datetime - дата архивации",
                "reason_text": "varchar(4000) - комментарии"
            }
        },       
        "partner": {
            "description": "Партнеры",
            "columns": {
                "id": "bigint - идентификатор партнера",
                "parent_id": "bigint - родительский партнер",
                "partner_type_id": "bigint - тип партнера",
                "town_id": "bigint - город",
                "name": "varchar(200) - название партнера",
                "comments": "varchar(500) - комментарии",
                "dt_archive": "datetime - дата архивации"
            }
        },       
        "region": {
            "description": "Регионы",
            "columns": {
                "id": "bigint - идентификатор региона",
                "name": "varchar(100) - название региона",
                "region_code": "varchar(8) - код региона",
                "country_id": "bigint - идентификатор страны"
            }
        },
        
        "town": {
            "description": "Города/населенные пункты",
            "columns": {
                "id": "bigint - идентификатор города",
                "address_code": "varchar(32) - почтовый индекс",
                "name": "longtext - название города",
                "phone_code": "varchar(64) - телефонный код",
                "region_id": "bigint - идентификатор региона"
            }
        },       
    },
    "common_queries": {
        "total_keys": "SELECT COUNT(*) as total FROM lic_key WHERE dt_archive IS NULL",
        "active_keys": """
            SELECT COUNT(DISTINCT k.id) as active 
            FROM lic_key k 
            JOIN key_assignment ka ON k.id = ka.key_id 
            WHERE k.dt_archive IS NULL AND ka.status = 0
        """,
        "keys_by_type": "SELECT key_type, COUNT(*) as count FROM lic_key WHERE dt_archive IS NULL GROUP BY key_type",
        "top_clients": """
            SELECT c.name, COUNT(ka.id) as key_count
            FROM client c
            JOIN lic_key k ON c.id = k.client_id
            JOIN key_assignment ka ON k.id = ka.key_id
            WHERE c.dt_archive IS NULL AND ka.status = 0
            GROUP BY c.id, c.name
            ORDER BY key_count DESC
            LIMIT :limit
        """,
        "expiring_soon": """
            SELECT c.name as client_name, f.name as filial_name, 
                   ka.dt_expiry, k.sernum
            FROM key_assignment ka
            JOIN lic_key k ON ka.key_id = k.id
            JOIN client c ON k.client_id = c.id
            LEFT JOIN filial f ON ka.filial_id = f.id
            WHERE ka.status = 0 
              AND ka.dt_expiry BETWEEN NOW() AND DATE_ADD(NOW(), INTERVAL :days DAY)
            ORDER BY ka.dt_expiry
        """,
        "popular_features": """
            SELECT f.name, COUNT(cdf.id) as sales_count, SUM(cdf.lic_count) as total_licenses
            FROM feature f
            JOIN client_document_feature cdf ON f.id = cdf.feature_id
            WHERE cdf.dt_archive IS NULL
            GROUP BY f.id, f.name
            ORDER BY total_licenses DESC
            LIMIT :limit
        """,
        "clients_by_type": """
            SELECT ct.name as client_type, COUNT(c.id) as client_count
            FROM client c
            JOIN client_type ct ON c.client_type_id = ct.id
            WHERE c.dt_archive IS NULL
            GROUP BY ct.id, ct.name
            ORDER BY client_count DESC
        """,
        "contracts_expiring": """
            SELECT cc.name, cc.dt_check, c.name as client_name
            FROM client_contract cc
            JOIN client c ON cc.partner_id = c.partner_id
            WHERE cc.dt_archive IS NULL 
              AND cc.dt_check BETWEEN NOW() AND DATE_ADD(NOW(), INTERVAL 60 DAY)
            ORDER BY cc.dt_check
        """,
        "partners_summary": """
            SELECT pt.name as partner_type, COUNT(p.id) as partner_count
            FROM partner p
            JOIN partner_type pt ON p.partner_type_id = pt.id
            WHERE p.dt_archive IS NULL
            GROUP BY pt.id, pt.name
        """
    }
}

def get_schema_text() -> str:
    """Format schema for LLM context"""
    lines = ["ПОЛНАЯ СХЕМА БАЗЫ ДАННЫХ СЕРВЕРА ЛИЦЕНЗИЙ:", ""]
    lines.append(f"Всего таблиц: {len(SCHEMA_INFO['tables'])}")
    lines.append("=" * 80)
    
    for table_name, table_info in SCHEMA_INFO["tables"].items():
        lines.append(f"\n📊 ТАБЛИЦА: {table_name}")
        lines.append(f"   Описание: {table_info['description']}")
        lines.append("   Колонки:")
        for col_name, col_desc in table_info["columns"].items():
            lines.append(f"     • {col_name}: {col_desc}")
        lines.append("-" * 60)
    
    lines.append("\n" + "=" * 80)
    lines.append("ПРИМЕРЫ ПОЛЕЗНЫХ ЗАПРОСОВ:")
    
    for query_name, query in SCHEMA_INFO["common_queries"].items():
        lines.append(f"\n📌 {query_name}:")
        # Format query for display
        formatted_query = query.strip().replace('\n', ' ').replace('            ', ' ')
        lines.append(f"   {formatted_query}")
    
    return "\n".join(lines)

def get_table_names() -> list:
    """Get list of all table names"""
    return list(SCHEMA_INFO["tables"].keys())

def get_table_description(table_name: str) -> str:
    """Get description of specific table"""
    table_info = SCHEMA_INFO["tables"].get(table_name)
    if table_info:
        return f"Таблица {table_name}: {table_info['description']}"
    return f"Таблица {table_name} не найдена в схеме"

def get_common_queries() -> dict:
    """Get dictionary of common queries"""
    return SCHEMA_INFO["common_queries"]