#!/usr/bin/env node

import * as fs from "node:fs";
import { resolve } from "node:path";

/**
 * 统计 SARIF 文件中的 result 数量
 * @param {string} sarifFilePath - SARIF 文件路径
 * @returns {number} result 数量
 */
function countSarifResults(sarifFilePath) {
   try {
      // 读取并解析 SARIF 文件
      const content = fs.readFileSync(sarifFilePath, "utf8");
      const sarif = JSON.parse(content);

      // 检查 SARIF 文件格式
      if (!sarif.runs || !Array.isArray(sarif.runs) || sarif.runs.length === 0) {
         console.error("错误: SARIF 文件格式不正确，缺少 runs 数组");
         return 0;
      }

      // 统计所有 runs 中的 results 数量
      let totalResults = 0;
      for (const run of sarif.runs) {
         if (run.results && Array.isArray(run.results)) {
            totalResults += run.results.length;
         }
      }

      return totalResults;
   } catch (error) {
      if (error.code === "ENOENT") {
         console.error(`错误: 文件不存在: ${sarifFilePath}`);
      } else if (error instanceof SyntaxError) {
         console.error(`错误: 无法解析 JSON 文件: ${error.message}`);
      } else {
         console.error(`错误: ${error.message}`);
      }
      process.exit(1);
   }
}

// 主函数
function main() {
   const args = process.argv.slice(2);

   if (args.length === 0) {
      console.log("用法: node count_sarif_results.js <sarif文件路径> [更多文件...]");
      console.log("示例: node count_sarif_results.js results.sarif");
      console.log("示例: node count_sarif_results.js results1.sarif results2.sarif");
      process.exit(1);
   }

   let totalCount = 0;
   const fileCounts = [];

   for (const fileArg of args) {
      const sarifFilePath = resolve(fileArg);
      const count = countSarifResults(sarifFilePath);
      fileCounts.push({ path: sarifFilePath, count });
      totalCount += count;
   }

   // 输出结果
   console.log("\n=== SARIF Result 统计 ===\n");
   for (const { path, count } of fileCounts) {
      console.log(`${path}: ${count} 个 results`);
   }

   if (fileCounts.length > 1) {
      console.log(`\n总计: ${totalCount} 个 results`);
   }
}

main();

