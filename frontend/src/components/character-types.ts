export type CharacterConfig = {
  gender: "feminine" | "masculine";
  personality: "cute" | "funny" | "romantic" | "confident" | "mysterious" | "chaotic";
  head_shape: "round" | "soft" | "sharp";
  skin_tone: "porcelain" | "peach" | "honey" | "almond" | "cocoa";
  hair_style: "short" | "bob" | "long" | "curly" | "bun" | "pixie" | "space_buns" | "side_swept";
  hair_color: "midnight" | "chestnut" | "honey" | "rose" | "lavender";
  eyes: "round" | "soft" | "sparkle" | "mischief";
  brows: "soft" | "arched" | "straight" | "bold";
  outfit: "hoodie" | "sweater" | "shirt" | "dress" | "jacket";
  accessory: "none" | "heart" | "star" | "flower" | "sparkle" | "headphones" | "bow" | "crown" | "scarf" | "earrings";
  glasses: "none" | "round" | "cat_eye";
  hat: "none" | "beanie" | "beret" | "halo";
  palette: "rose" | "violet" | "mint" | "sunset" | "night";
};

export type CharacterPair = {
  feminine: CharacterConfig;
  masculine: CharacterConfig;
};
