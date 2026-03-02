/**
 * 输入文本文件（一行一个具体ID）和一个数据集目录，数据集目录是这样的，根目录是datasets/，底下有5个类别，暂记A,B,C,D,E，
 * 每个类别下有不同ID的子文件夹（可以和文本文件的ID对应）。 
 * 我需要你遍历文本文件中的每个ID，然后判断其是哪个类别下的，并最终对每个类别统计该类下的ID在文本文件里出现的有哪些，
 * 没出现的有些，并分别统计数量，最终生成一个json文件
 * id统一转小写
 */
const fs = require("fs");
const path = require("path");

// ====== 配置区 ======
const idsFile = process.argv[2];       // ids.txt
const datasetsDir = process.argv[3];   // datasets
const outputJson = process.argv[4] || "result.json";

const CATEGORIES = ["path-traversal", "code-injection", "command-injection", "prototype-pollution", "redos"];
// ====================

if (!idsFile || !datasetsDir) {
  console.error("Usage: node analyze.js <ids.txt> <datasets_dir> [output.json]");
  process.exit(1);
}

// 1. 读取 ID 文件，统一转小写
const idSet = new Set(
  fs.readFileSync(idsFile, "utf-8")
    .split(/\r?\n/)
    .map(line => line.trim())
    .filter(Boolean)
    .map(id => id.toLowerCase())
);

// 2. 初始化结果
const result = {};

for (const category of CATEGORIES) {
  const categoryPath = path.join(datasetsDir, category);
  if (!fs.existsSync(categoryPath) || !fs.statSync(categoryPath).isDirectory()) {
    continue;
  }

  const dirs = fs.readdirSync(categoryPath, { withFileTypes: true })
    .filter(d => d.isDirectory());

  const present = [];
  const absent = [];

  for (const dir of dirs) {
    const originalId = dir.name;
    const normalizedId = originalId.toLowerCase();

    if (idSet.has(normalizedId)) {
      present.push(originalId);
    } else {
      absent.push(originalId);
    }
  }

  result[category] = {
    present_ids: present,
    absent_ids: absent,
    present_count: present.length,
    absent_count: absent.length
  };
}

// 3. 写出 JSON
fs.writeFileSync(outputJson, JSON.stringify(result, null, 2));
console.log(`Result written to ${outputJson}`);
