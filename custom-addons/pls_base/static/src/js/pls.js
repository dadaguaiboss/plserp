/** @odoo-module **/

import { session } from "@web/session";

/**
 * 普洛狮ERP 品牌定制脚本
 * 将系统中的 "Odoo" 引用替换为 "普洛狮ERP"
 */

const ORIGINAL_NAME = "Odoo";
const BRAND_NAME = "普洛狮ERP";

// 覆盖文档标题
const originalTitle = document.title;
if (originalTitle && originalTitle.includes(ORIGINAL_NAME)) {
    document.title = originalTitle.replace(ORIGINAL_NAME, BRAND_NAME);
}

// 监听标题变化，持续替换
const titleObserver = new MutationObserver(() => {
    if (document.title.includes(ORIGINAL_NAME)) {
        document.title = document.title.replace(ORIGINAL_NAME, BRAND_NAME);
    }
});

const titleElement = document.querySelector("title");
if (titleElement) {
    titleObserver.observe(titleElement, { childList: true });
}
