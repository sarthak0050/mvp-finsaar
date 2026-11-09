import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";

// Local dev only: serve /api/* from the same handler files Vercel deploys as functions.
const vercelApi = () => ({
  name: "vercel-api-dev",
  configureServer(server) {
    server.middlewares.use(async (req, res, next) => {
      const url = new URL(req.url, "http://localhost");
      if (!url.pathname.startsWith("/api/")) return next();
      try {
        const mod = await server.ssrLoadModule(path.resolve(__dirname, `.${url.pathname}.js`));
        let raw = "";
        for await (const chunk of req) raw += chunk;
        req.body = raw ? JSON.parse(raw) : {};
        req.query = Object.fromEntries(url.searchParams);
        res.status = (code) => ((res.statusCode = code), res);
        res.json = (obj) => (res.setHeader("Content-Type", "application/json"), res.end(JSON.stringify(obj)));
        await mod.default(req, res);
      } catch (err) {
        console.error(err);
        res.statusCode = 404;
        res.end("Not found");
      }
    });
  },
});

export default defineConfig({
  plugins: [react(), vercelApi()],
  resolve: { alias: { "@": path.resolve(__dirname, "src") } },
  // Original CRA code reads REACT_APP_BACKEND_URL; empty means same origin (/api on Vercel).
  define: { "process.env.REACT_APP_BACKEND_URL": JSON.stringify(process.env.REACT_APP_BACKEND_URL || "") },
});
