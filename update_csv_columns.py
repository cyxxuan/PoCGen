#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSV列更新脚本
用于更新PoCGen_GLM, PoCGen_CodeQL_Result_Num, CodeQL_vanilla, Dynamic Source Export, Lines of code这5列

用法:
    python3 update_csv_columns.py <csv_file> <base_dir_name>
    
示例:
    python3 update_csv_columns.py path-traversal.csv path_traversal
    python3 update_csv_columns.py code-injection.csv code_injection
    python3 update_csv_columns.py command-injection.csv command_injection
    python3 update_csv_columns.py prototype-pollution.csv prototype_pollution
    python3 update_csv_columns.py redos.csv redos
"""

import csv
import json
import sys
import subprocess
import re
import os
from pathlib import Path


def load_id_lists():
    """加载success_generate_ids.txt和api_error_ids.txt"""
    success_ids = set()
    api_error_ids = set()
    
    try:
        with open('success_generate_ids.txt', 'r', encoding='utf-8') as f:
            for line in f:
                id_val = line.strip()
                if id_val:
                    success_ids.add(id_val)
    except FileNotFoundError:
        print("警告: success_generate_ids.txt 文件不存在")
    
    try:
        with open('api_error_ids.txt', 'r', encoding='utf-8') as f:
            for line in f:
                id_val = line.strip()
                if id_val:
                    api_error_ids.add(id_val)
    except FileNotFoundError:
        print("警告: api_error_ids.txt 文件不存在")
    
    return success_ids, api_error_ids


def count_sarif_results(sarif_file_path):
    """统计单个SARIF文件中的result数量"""
    try:
        with open(sarif_file_path, 'r', encoding='utf-8') as f:
            sarif = json.load(f)
        
        if not sarif.get('runs') or not isinstance(sarif['runs'], list) or len(sarif['runs']) == 0:
            return 0
        
        total_results = 0
        for run in sarif['runs']:
            if run.get('results') and isinstance(run['results'], list):
                total_results += len(run['results'])
        
        return total_results
    except Exception:
        return 0


def find_sarif_files(base_dir, id_value):
    """在指定目录下查找ID对应的目录，并递归查找所有sarif文件"""
    base_path = Path(base_dir)
    if not base_path.exists():
        return []
    
    # 尝试精确匹配
    id_dir = base_path / id_value
    if id_dir.exists() and id_dir.is_dir():
        sarif_files = list(id_dir.rglob('*.sarif'))
        return sarif_files
    
    # 如果精确匹配失败，尝试大小写不敏感匹配
    id_upper = id_value.upper()
    for item in base_path.iterdir():
        if item.is_dir() and item.name.upper() == id_upper:
            sarif_files = list(item.rglob('*.sarif'))
            return sarif_files
    
    return []


def count_all_sarif_results(base_dir, id_value):
    """统计某个ID下所有sarif文件中的result总数"""
    sarif_files = find_sarif_files(base_dir, id_value)
    
    if not sarif_files:
        return 'no sarif'
    
    total_results = 0
    for sarif_file in sarif_files:
        total_results += count_sarif_results(sarif_file)
    
    return str(total_results)


def count_codeql_vanilla(base_dir, id_value):
    """统计CodeQL_vanilla的result数量"""
    sarif_files = find_sarif_files(base_dir, id_value)
    
    if not sarif_files:
        return 'no sarif'
    
    total_results = 0
    for sarif_file in sarif_files:
        total_results += count_sarif_results(sarif_file)
    
    if total_results == 0:
        return '0'
    
    return str(total_results)


def count_export_api(base_dir, id_value):
    """统计某个ID的target/export-api.json文件中的export-api数组长度"""
    base_path = Path(base_dir)
    if not base_path.exists():
        return 'no export api'
    
    # 尝试精确匹配目录
    id_dir = base_path / id_value
    if not id_dir.exists() or not id_dir.is_dir():
        # 尝试大小写不敏感匹配
        id_upper = id_value.upper()
        for item in base_path.iterdir():
            if item.is_dir() and item.name.upper() == id_upper:
                id_dir = item
                break
        else:
            return 'no export api'
    
    # 查找target/export-api.json文件
    export_api_file = id_dir / 'target' / 'export-api.json'
    
    if not export_api_file.exists():
        return 'no export api'
    
    try:
        with open(export_api_file, 'r', encoding='utf-8') as f:
            export_api_data = json.load(f)
        
        if isinstance(export_api_data, list):
            return str(len(export_api_data))
        else:
            if isinstance(export_api_data, dict) and 'export-api' in export_api_data:
                export_api = export_api_data['export-api']
                if isinstance(export_api, list):
                    return str(len(export_api))
            
            return 'no export api'
    except Exception:
        return 'no export api'


def count_lines_of_code(base_dir, id_value):
    """统计某个ID的target目录下dbs的lines of code"""
    base_path = Path(base_dir)
    if not base_path.exists():
        return 'no loc'
    
    # 尝试精确匹配目录
    id_dir = base_path / id_value
    if not id_dir.exists() or not id_dir.is_dir():
        # 尝试大小写不敏感匹配
        id_upper = id_value.upper()
        for item in base_path.iterdir():
            if item.is_dir() and item.name.upper() == id_upper:
                id_dir = item
                break
        else:
            return 'no loc'
    
    # 查找target/dbs目录
    target_dir = id_dir / 'target'
    dbs_dir = target_dir / 'dbs'
    
    if not target_dir.exists() or not dbs_dir.exists():
        return 'no loc'
    
    try:
        # 设置PATH环境变量
        env = os.environ.copy()
        codeql_path = os.path.expanduser('~/.cursor-server/data/User/globalStorage/github.vscode-codeql/distribution3/codeql')
        if os.path.exists(codeql_path):
            env['PATH'] = env.get('PATH', '') + ':' + codeql_path
        
        # 执行codeql database print-baseline命令
        result = subprocess.run(
            ['codeql', 'database', 'print-baseline', str(dbs_dir)],
            cwd=str(target_dir),
            capture_output=True,
            text=True,
            env=env,
            timeout=30
        )
        
        if result.returncode != 0:
            return 'no loc'
        
        # 从输出中提取lines of code数字
        # 格式: "Counted a baseline of 25782 lines of code for javascript."
        output = result.stdout + result.stderr
        match = re.search(r'Counted a baseline of (\d+) lines of code', output)
        if match:
            return match.group(1)
        else:
            return 'no loc'
    except subprocess.TimeoutExpired:
        return 'no loc'
    except Exception:
        return 'no loc'


def process_csv(csv_file, base_dir_name, verbose=True):
    """处理单个CSV文件"""
    output_dir = '/home/linxw/cyx/PoCGen/output'
    base_dir = f'/home/linxw/project/AePPollo_Plus/AePPollo_plus/final/workspace/cwebench/{base_dir_name}'
    
    # 加载ID列表
    success_ids, api_error_ids = load_id_lists()
    
    rows = []
    updated_count = 0
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        
        # 检查header是否需要添加Lines of code列
        if len(header) < 14 or (len(header) >= 13 and header[-1] != 'Lines of code'):
            if len(header) == 13:
                header.append('Lines of code')
            elif len(header) < 13:
                while len(header) < 13:
                    header.append('')
                header.append('Lines of code')
        
        rows.append(header)
        
        for row in reader:
            if len(row) > 0:
                row_id = row[0].strip()
                if row_id:
                    # 确保行有足够的列（包括新增的Lines of code列）
                    while len(row) < 14:
                        row.append('')
                    
                    # 1. 更新PoCGen_GLM列（索引5）
                    if row_id in success_ids:
                        current_value = row[5].strip() if len(row) > 5 and row[5] else ''
                        if current_value == '':
                            row[5] = 'y'
                        elif 'y' not in current_value:
                            row[5] = current_value + 'y'
                    
                    if row_id in api_error_ids:
                        current_value = row[5].strip() if len(row) > 5 and row[5] else ''
                        if current_value == '':
                            row[5] = '(api-error)'
                        elif '(api-error)' not in current_value:
                            row[5] = current_value + '(api-error)'
                    
                    # 2. 更新PoCGen_CodeQL_Result_Num列（索引6）
                    result_count = count_all_sarif_results(output_dir, row_id)
                    row[6] = result_count
                    
                    # 3. 更新CodeQL_vanilla列（索引7）
                    codeql_count = count_codeql_vanilla(base_dir, row_id)
                    row[7] = codeql_count
                    
                    # 4. 更新Dynamic Source Export列（索引8）
                    export_api_count = count_export_api(base_dir, row_id)
                    row[8] = export_api_count
                    
                    # 5. 更新Lines of code列（索引13，最后一列）
                    loc_count = count_lines_of_code(base_dir, row_id)
                    row[13] = loc_count
                    
                    updated_count += 1
                    if verbose and updated_count % 10 == 0:
                        print(f'  已处理 {updated_count} 行...', end='\r')
            
            rows.append(row)
    
    # 写回CSV文件
    with open(csv_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(rows)
    
    if verbose:
        print(f'  已处理 {updated_count} 行...完成！')
    
    return updated_count


def main():
    if len(sys.argv) < 3:
        print("用法: python3 update_csv_columns.py <csv_file> <base_dir_name>")
        print("\n示例:")
        print("  python3 update_csv_columns.py path-traversal.csv path_traversal")
        print("  python3 update_csv_columns.py code-injection.csv code_injection")
        print("  python3 update_csv_columns.py command-injection.csv command_injection")
        print("  python3 update_csv_columns.py prototype-pollution.csv prototype_pollution")
        print("  python3 update_csv_columns.py redos.csv redos")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    base_dir_name = sys.argv[2]
    
    if not Path(csv_file).exists():
        print(f"错误: CSV文件不存在: {csv_file}")
        sys.exit(1)
    
    print(f"处理 {csv_file}...")
    print(f"使用目录: /home/linxw/project/AePPollo_Plus/AePPollo_plus/final/workspace/cwebench/{base_dir_name}")
    
    try:
        count = process_csv(csv_file, base_dir_name)
        print(f"\n完成！已更新 {count} 行")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()







