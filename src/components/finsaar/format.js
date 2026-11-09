export const inr = (v) => `₹${Math.abs(Math.round(v)).toLocaleString("en-IN")}`;
export const signedInr = (v) => `${v < 0 ? "−" : "+"}${inr(v)}`;
export const signedPct = (v) => `${v < 0 ? "−" : "+"}${Math.abs(v).toFixed(2)}%`;
export const signedInr2 = (v) => `${v < 0 ? "−" : "+"}₹${Math.abs(v).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
export const xirrText = (x) => (x == null ? "Not available" : `${x < 0 ? "−" : ""}${Math.abs(x)}%`);
