#!/usr/bin/env node

/**
 * 测试脚本：检查 metacalc 包的导出 API
 * 使用 PocGen 的 ApiExplorer 模块
 */

import { getExportsFromPackage } from "./src/analysis/api-explorer/getExports.js";
import { join, resolve } from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = resolve(__filename, "..");

// 目标目录路径
const targetDir = join(__dirname, "output", "GHSA-5gc4-cx9x-9c43");
const nmPath = join(targetDir, "node_modules");
const moduleName = "metacalc";

console.log("=".repeat(80));
console.log("Metacalc API Explorer Test");
console.log("=".repeat(80));
console.log(`Target directory: ${targetDir}`);
console.log(`Node modules path: ${nmPath}`);
console.log(`Module name: ${moduleName}`);
console.log("=".repeat(80));
console.log();

async function testApiExplorer() {
   try {
      console.log("Exploring metacalc package exports...");
      console.log("-".repeat(80));
      
      const results = await getExportsFromPackage(nmPath, moduleName, {
         onlyEntryPoint: false
      });
      
      console.log(`\nFound ${results.list.length} module(s)`);
      console.log(`Total sources: ${results.sources.length}`);
      console.log(`Sources in scope: ${results.sourcesInScope.length}`);
      console.log(`Sources out of scope: ${results.sourcesOutOfScope.length}`);
      
      if (results.errors.length > 0) {
         console.log(`\nErrors: ${results.errors.length}`);
         results.errors.forEach((err, i) => {
            console.log(`  ${i + 1}. ${err}`);
         });
      }
      
      console.log("\n" + "=".repeat(80));
      console.log("Exported Functions/Methods:");
      console.log("=".repeat(80));
      
      if (results.sources.length === 0) {
         console.log("No sources found!");
      } else {
         results.sources.forEach((source, index) => {
            console.log(`\n${index + 1}. ${source.callable.name || "anonymous"}`);
            console.log(`   Type: ${source.callable.type || "N/A"}`);
            console.log(`   Kind: ${source.callable.kind || "N/A"}`);
            console.log(`   Export name: ${source.callable.exportName || "N/A"}`);
            console.log(`   Location: ${source.callable.location?.filePath || "N/A"}:${source.callable.location?.startLine || "N/A"}`);
            console.log(`   Signature: ${source.callable.signature || "N/A"}`);
            console.log(`   Is exported: ${source.isExported}`);
            console.log(`   Is global: ${source.isGlobal}`);
            
            if (source.parentChain && source.parentChain.length > 0) {
               console.log(`   Parent chain: ${source.parentChain.map(p => p.exportName || p.name).join(" -> ")}`);
            }
            
            if (source.callable.protoFunctions && source.callable.protoFunctions.length > 0) {
               console.log(`   Prototype methods: ${source.callable.protoFunctions.length}`);
               source.callable.protoFunctions.forEach((proto, i) => {
                  console.log(`     ${i + 1}. ${proto.name || "anonymous"} (${proto.kind || "method"})`);
               });
            }
            
            if (source.callable.children && source.callable.children.length > 0) {
               console.log(`   Static properties: ${source.callable.children.length}`);
               source.callable.children.forEach((child, i) => {
                  console.log(`     ${i + 1}. ${child.exportName || "anonymous"}`);
               });
            }
         });
      }
      
      console.log("\n" + "=".repeat(80));
      console.log("Test completed successfully!");
      console.log("=".repeat(80));
      
   } catch (error) {
      console.error("\n" + "=".repeat(80));
      console.error("Error occurred:");
      console.error("=".repeat(80));
      console.error(error);
      console.error("\nStack trace:");
      console.error(error.stack);
      process.exit(1);
   }
}

// 运行测试
testApiExplorer().catch((error) => {
   console.error("Unhandled error:", error);
   process.exit(1);
});

