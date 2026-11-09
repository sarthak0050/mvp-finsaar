// Golden-set "must include" matching. Some required keywords are single words or English phrases
// that a plain-words or Hinglish answer can express differently; those accept equivalents.
import { norm } from "./gate.js";

const ALTERNATIVES = {
  yearly: ["yearly", "per year", "a year", "annual", "saal bhar", "har saal", "saal ka"],
  "units are still yours": ["units are still yours", "still own all", "still yours", "units abhi bhi aapke", "units aapke hi"],
  "decision is yours": ["decision is yours", "your decision", "faisla aapka", "aapka faisla"],
  "faisla aapka": ["faisla aapka", "aapka faisla", "decision is yours"],
  "can't recommend": ["can't recommend", "recommend nahi kar", "not able to recommend"],
  "can't predict": ["can't predict", "predict nahi kar", "nobody can predict", "no one can predict", "not able to predict"],
  "don't see": ["don't see", "do not see", "isn't in your", "not in your sips", "nahi dikh"],
  "nahi dikh": ["nahi dikh", "don't see", "do not see"],
  stop: ["stop", "band kar", "band karna"],
  pause: ["pause", "rok"],
  skip: ["skip", "chhod"],
  "5%": ["5%", "5 percent", "5 per cent"],
};

// A ₹ amount also matches when written without the symbol (e.g. "496 rupees").
const variantsOf = (item) => {
  const list = ALTERNATIVES[item] || [item];
  return item.startsWith("₹") ? [...list, item.slice(1)] : list;
};

export const findKeyword = (answer, item) => {
  const a = norm(answer);
  return variantsOf(item).find((v) => a.includes(norm(v))) || null;
};
