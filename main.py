import sys
import argparse
import json
from pathlib import Path
from lark import Lark, Transformer, Token
from lark.exceptions import LarkError
grammar = r"""
    start: top_level_items
    
    top_level_items: (const_decl | dict | array)*
    
    const_decl: "var" NAME value
    
    dict: "[" dict_items "]"
    dict_items: (dict_item ("," dict_item)*)?
    dict_item: NAME ":" value
    
    array: "{" array_items "}"
    array_items: (value ("." value)*)?
    
    value: simple_value | array | dict | const_ref
    
    simple_value: NUMBER | STRING
    
    const_ref: "$" NAME "$"
    
    NAME: /[a-zA-Z][_a-zA-Z0-9]*/
    NUMBER: /[+-]?\d+\.\d+/
    STRING: /q\([^)]*\)/
    
    COMMENT: "/*" /(.|\n)+?/ "*/"
    
    %import common.WS
    %ignore WS
    %ignore COMMENT
"""

class MyTransformer(Transformer):
    def __init__(self):
        super().__init__()
        self.consts = {}
        self.top_level_items_list = []
    
    def start(self, items):
        if len(self.top_level_items_list) == 1:
            item = self.top_level_items_list[0]
            if isinstance(item, dict):
                return item
            elif isinstance(item, list):
                return item  
        elif self.top_level_items_list:
            result = {}
            arrays = []
            for item in self.top_level_items_list:
                if isinstance(item, dict) and item:
                    result.update(item)
                elif isinstance(item, list):
                    arrays.append(item)
            if arrays:
                result["arrays"] = arrays
            return result
        
        return {}
    
    def top_level_items(self, items):
        self.top_level_items_list = list(items)
        return items
    
    def dict(self, items):
        if items and items[0] is not None:
            return items[0]
        return {}
    
    def dict_items(self, items):
        result = {}
        for item in items:
            if item and isinstance(item, tuple) and len(item) == 2:
                key, value = item
                result[key] = value
        return result
    
    def dict_item(self, items):
        if len(items) >= 2:
            return (str(items[0]), items[1])
        return None
    
    def array(self, items):
        if items and items[0] is not None:
            return items[0]
        return []
    
    def array_items(self, items):
        return list(items)
    
    def const_decl(self, items):
        if len(items) >= 2:
            name = str(items[0])
            value = items[1]
            self.consts[name] = value
        return {}
    
    def const_ref(self, items):
        if items:
            name = str(items[0])
            if name in self.consts:
                return self.consts[name]
            raise ValueError(f"Константа '{name}' не определена")
        return None
    
    def value(self, items):
        if not items:
            return None
        return items[0]
    
    def simple_value(self, items):
        return items[0] if items else None
    
    def NAME(self, token):
        return Token('NAME', str(token))
    
    def NUMBER(self, token):
        return float(token)
    
    def STRING(self, token):
        content = str(token)
        return content[2:-1]

class Converter:
    def __init__(self):
        self.transformer = MyTransformer()
        self.parser = Lark(grammar, parser='lalr', transformer=self.transformer)
    
    def parse_file(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return self.parse_content(content)
        except FileNotFoundError:
            raise ValueError(f"Файл не найден: {file_path}")
        except IOError as e:
            raise ValueError(f"Ошибка чтения файла: {e}")
    
    def parse_content(self, text):
        try:
            result = self.parser.parse(text)
            return result if result is not None else {}
        except LarkError as e:
            raise ValueError(f"Синтаксическая ошибка: {e}")
        except ValueError as e:
            raise ValueError(f"Ошибка вычисления: {e}")
    
    def to_json(self, config):
        return json.dumps(config, ensure_ascii=False, indent=2)

def main():
    parser = argparse.ArgumentParser(
        description='Конвертер учебного конфигурационного языка в JSON (вариант 29)'
    )
    parser.add_argument(
        '-i', '--input',
        type=str,
        required=True,
        help='Путь к входному файлу конфигурации'
    )
    
    args = parser.parse_args()
    
    try:
        converter = Converter()
        config = converter.parse_file(Path(args.input))
        json_output = converter.to_json(config)
        print(json_output)
        return 0
    except Exception as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
