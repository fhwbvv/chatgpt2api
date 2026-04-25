import { readFileSync } from "node:fs";
import { join } from "node:path";

function readUserImagesHtml() {
  try {
    return readFileSync(join(process.cwd(), "user_images.html"), "utf-8");
  } catch {
    return `<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <title>作品</title>
  </head>
  <body style="font-family: 'Microsoft YaHei', sans-serif; padding: 24px;">
    <h1>作品页面不存在</h1>
    <p>未找到 web/user_images.html，请检查文件是否存在。</p>
  </body>
</html>`;
  }
}

export default function UserImagesPage() {
  const html = readUserImagesHtml();

  return (
    <section className="mx-auto h-[calc(100vh-5rem)] w-full max-w-[1380px] px-3 pb-6">
      <iframe
        title="\u4f5c\u54c1"
        srcDoc={html}
        className="h-full w-full rounded-2xl border border-stone-200 bg-white shadow-sm"
      />
    </section>
  );
}
