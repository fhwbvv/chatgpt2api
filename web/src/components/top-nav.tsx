"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Github } from "lucide-react";
import { usePathname, useRouter } from "next/navigation";

import webConfig from "@/constants/common-env";
import { clearStoredAuthSession, getStoredAuthSession, type StoredAuthSession } from "@/store/auth";
import { cn } from "@/lib/utils";

const adminNavItems = [
  { href: "/image", label: "\u753b\u56fe" },
  { href: "/accounts", label: "\u53f7\u6c60\u7ba1\u7406" },
  { href: "/settings", label: "\u8bbe\u7f6e" },
  { href: "/user-images", label: "\u4f5c\u54c1" },
];

const userNavItems = [{ href: "/image", label: "\u753b\u56fe" }];

export function TopNav() {
  const pathname = usePathname();
  const router = useRouter();
  const [session, setSession] = useState<StoredAuthSession | null | undefined>(undefined);

  useEffect(() => {
    let active = true;

    const load = async () => {
      if (pathname === "/login") {
        if (!active) {
          return;
        }
        setSession(null);
        return;
      }

      const storedSession = await getStoredAuthSession();
      if (!active) {
        return;
      }
      setSession(storedSession);
    };

    void load();
    return () => {
      active = false;
    };
  }, [pathname]);

  const handleLogout = async () => {
    await clearStoredAuthSession();
    router.replace("/login");
  };

  if (pathname === "/login" || session === undefined || !session) {
    return null;
  }

  const navItems = session.role === "admin" ? adminNavItems : userNavItems;
  const roleLabel = session.role === "admin" ? "\u7ba1\u7406\u5458" : "\u666e\u901a\u7528\u6237";

  return (
    <header className="border-b border-stone-100/50">
      <div className="flex h-12 items-center justify-between px-3 sm:px-6">
        <div className="flex items-center gap-2 sm:gap-3">
          <Link
            href="/image"
            className="py-1 text-[14px] font-bold tracking-tight text-stone-950 transition hover:text-stone-700 sm:text-[15px]"
          >
            chatgpt2api
          </Link>
          <a
            href="https://github.com/basketikun/chatgpt2api"
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1.5 py-1 text-sm text-stone-400 transition hover:text-stone-700"
            aria-label="GitHub repository"
          >
            <Github className="size-4" />
            <span className="hidden md:inline">GitHub</span>
          </a>
        </div>
        <div className="flex flex-1 justify-center gap-3 sm:gap-8">
          {navItems.map((item) => {
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "relative py-1 text-[13px] font-medium transition sm:text-[15px]",
                  active ? "font-semibold text-stone-950" : "text-stone-500 hover:text-stone-900",
                )}
              >
                {item.label}
                {active ? <span className="absolute inset-x-0 -bottom-[1px] h-0.5 bg-stone-950" /> : null}
              </Link>
            );
          })}
        </div>
        <div className="flex items-center justify-end gap-2 sm:gap-3">
          <span className="hidden rounded-md bg-stone-100 px-2 py-1 text-[10px] font-medium text-stone-500 sm:inline-block sm:text-[11px]">
            {roleLabel}
          </span>
          <span className="hidden rounded-md bg-stone-100 px-2 py-1 text-[10px] font-medium text-stone-500 sm:inline-block sm:text-[11px]">
            v{webConfig.appVersion}
          </span>
          <button
            type="button"
            className="py-1 text-xs text-stone-400 transition hover:text-stone-700 sm:text-sm"
            onClick={() => void handleLogout()}
          >
            {"\u9000\u51fa"}
          </button>
        </div>
      </div>
    </header>
  );
}
