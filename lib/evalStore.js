// The latest completed golden-set run, kept in a private Vercel Blob so every visitor sees it.
import { get, put } from "@vercel/blob";

const LATEST = "evals/latest.json";
const enabled = () => Boolean(process.env.BLOB_READ_WRITE_TOKEN);

export const loadLatestRun = async () => {
  if (!enabled()) return null;
  try {
    const res = await get(LATEST, { access: "private", useCache: false });
    if (!res || res.statusCode !== 200) return null;
    return JSON.parse(await new Response(res.stream).text());
  } catch (err) {
    if (err?.name !== "BlobNotFoundError") console.error("load latest run failed", err?.message || err);
    return null;
  }
};

export const saveLatestRun = async (run) => {
  if (!enabled()) return false;
  await put(LATEST, JSON.stringify(run), { access: "private", addRandomSuffix: false, allowOverwrite: true, contentType: "application/json" });
  return true;
};
