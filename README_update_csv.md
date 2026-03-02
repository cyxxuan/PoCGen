# CSV列更新脚本使用说明

## 脚本功能

`update_csv_columns.py` 脚本用于自动更新CSV文件中的以下5列：

1. **PoCGen_GLM** - 根据 `success_generate_ids.txt` 和 `api_error_ids.txt` 更新
2. **PoCGen_CodeQL_Result_Num** - 从 `/home/linxw/cyx/PoCGen/output` 目录统计sarif文件的result数量
3. **CodeQL_vanilla** - 从对应的cwebench目录统计sarif文件的result数量
4. **Dynamic Source Export** - 从对应目录的 `target/export-api.json` 文件统计数组长度
5. **Lines of code** - 从对应目录的 `target/dbs` 执行 `codeql database print-baseline` 统计代码行数

## 使用方法

```bash
python3 update_csv_columns.py <csv_file> <base_dir_name>
```

### 参数说明

- `csv_file`: 要更新的CSV文件名（如 `path-traversal.csv`）
- `base_dir_name`: cwebench目录下的子目录名（如 `path_traversal`）

### 示例

```bash
# 更新 path-traversal.csv
python3 update_csv_columns.py path-traversal.csv path_traversal

# 更新 code-injection.csv
python3 update_csv_columns.py code-injection.csv code_injection

# 更新 command-injection.csv
python3 update_csv_columns.py command-injection.csv command_injection

# 更新 prototype-pollution.csv
python3 update_csv_columns.py prototype-pollution.csv prototype_pollution

# 更新 redos.csv
python3 update_csv_columns.py redos.csv redos
```

## 更新逻辑

### PoCGen_GLM列
- 如果ID在 `success_generate_ids.txt` 中，填入 `y`
- 如果ID在 `api_error_ids.txt` 中，追加 `(api-error)`
- 如果两者都有，会同时添加

### PoCGen_CodeQL_Result_Num列
- 从 `/home/linxw/cyx/PoCGen/output/<ID>/` 目录递归查找所有 `.sarif` 文件
- 统计所有sarif文件中的result总数
- 如果找不到sarif文件，写入 `no sarif`

### CodeQL_vanilla列
- 从 `/home/linxw/project/AePPollo_Plus/AePPollo_plus/final/workspace/cwebench/<base_dir_name>/<ID>/` 目录递归查找所有 `.sarif` 文件
- 统计所有sarif文件中的result总数
- 如果找不到sarif文件，写入 `no sarif`
- 如果result数量为0，写入 `0`

### Dynamic Source Export列
- 从 `/home/linxw/project/AePPollo_Plus/AePPollo_plus/final/workspace/cwebench/<base_dir_name>/<ID>/target/export-api.json` 读取JSON文件
- 如果文件是数组，返回数组长度
- 如果文件是对象且包含 `export-api` 字段，返回该字段的数组长度
- 如果找不到文件或解析错误，写入 `no export api`
- 如果数组长度为0，写入 `0`

### Lines of code列
- 从 `/home/linxw/project/AePPollo_Plus/AePPollo_plus/final/workspace/cwebench/<base_dir_name>/<ID>/target/dbs` 执行 `codeql database print-baseline` 命令
- 从输出中提取 "Counted a baseline of X lines of code for javascript." 中的数字
- 如果找不到dbs目录或命令执行失败，写入 `no loc`
- 脚本会自动设置PATH环境变量以使用codeql命令

## 注意事项

1. 脚本会自动处理ID的大小写不匹配问题（目录名可能是大写）
2. 脚本会保留CSV文件中的其他列不变
3. 确保以下文件存在：
   - `success_generate_ids.txt`（可选，如果不存在会显示警告）
   - `api_error_ids.txt`（可选，如果不存在会显示警告）
4. 确保目录路径正确：
   - `/home/linxw/cyx/PoCGen/output/` - 用于PoCGen_CodeQL_Result_Num
   - `/home/linxw/project/AePPollo_Plus/AePPollo_plus/final/workspace/cwebench/<base_dir_name>/` - 用于CodeQL_vanilla和Dynamic Source Export

## 输出

脚本会显示处理进度，每处理10行会显示一次进度。完成后会显示总更新行数。

