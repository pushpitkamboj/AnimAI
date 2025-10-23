import ast
from typing import List, Dict, Any

def get_source_segment(source_code: str, node_start: int, node_end: int) -> str:
    """Extracts the source code lines between node_start (inclusive) and node_end (exclusive)."""
    lines = source_code.splitlines(keepends=True)
    return "".join(lines[node_start - 1: node_end - 1]).strip()

def create_hierarchy_chunks(source_code: str, file_path: str) -> List[Dict[str, Any]]:
    nodes = ast.parse(source_code).body
    parent_all_chunks = []
    child_all_chunks = []
    for node in nodes:
        if isinstance(node, ast.ClassDef):
            class_name = node.name
            
            method_names = [
                item.name for item in node.body 
                if isinstance(item, ast.FunctionDef) and item.name != '__init__'
            ]

            init_node = next((item for item in node.body if isinstance(item, ast.FunctionDef) and item.name == '__init__'), None)
            
            context_end_line = node.body[0].lineno if node.body else node.end_lineno
            if init_node:
                context_end_line = init_node.end_lineno + 1
            elif node.body:
                context_end_line = node.body[0].lineno

            class_content = get_source_segment(source_code, node.lineno, context_end_line)

            parent_chunk = {
                "id": class_name,
                "content": class_content,
                "type": "Class",
                "file_path": file_path,
                "children_ids": [f"{class_name}.{m}" for m in method_names] 
            }
            parent_all_chunks.append(parent_chunk)

            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    method_name = item.name
                    if method_name == "__init__":
                        continue
                    method_id = f"{class_name}.{method_name}"
                    
                    # 2a. Extract the source segment for the Child Chunk
                    method_content = get_source_segment(source_code, item.lineno, item.end_lineno + 1)
                    
                    # 2b. Create the Child Chunk Document
                    child_chunk = {
                        "id": method_id,
                        "content": method_content,
                        "type": "Method",
                        "file_path": file_path,
                        # "class_name": class_name,
                        "method_name": method_name,
                        "parent_id": class_name 
                    }
                    child_all_chunks.append(child_chunk)
    return [parent_all_chunks, child_all_chunks]


def chunking(file_path: str, file_url):
    try:

        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()

        return create_hierarchy_chunks(source_code, file_url)

    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        return []
    except Exception as e:
        print(f"An error occurred during file processing: {e}")
        return []
