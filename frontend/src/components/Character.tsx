import type { CSSProperties } from "react";

type CharacterConfig = {
  personality: "cute" | "funny" | "romantic" | "confident" | "mysterious" | "chaotic";
  head_shape: "round" | "soft" | "sharp";
  skin_tone: "porcelain" | "peach" | "honey" | "almond" | "cocoa";
  hair_style: "short" | "bob" | "long" | "curly" | "bun";
  hair_color: "midnight" | "chestnut" | "honey" | "rose" | "lavender";
  eyes: "round" | "soft" | "sparkle" | "mischief";
  brows: "soft" | "arched" | "straight" | "bold";
  outfit: "hoodie" | "sweater" | "shirt" | "dress" | "jacket";
  accessory: "none" | "heart" | "star" | "flower" | "sparkle";
  glasses: "none" | "round" | "cat_eye";
  hat: "none" | "beanie" | "beret" | "halo";
  palette: "rose" | "violet" | "mint" | "sunset" | "night";
};

type CharacterProps = { config: CharacterConfig; emotion?: string; pose?: string; compact?: boolean };

const skin: Record<CharacterConfig["skin_tone"], string> = { porcelain: "#fff0e9", peach: "#f8c4a8", honey: "#e6a36e", almond: "#b9704f", cocoa: "#754634" };
const hair: Record<CharacterConfig["hair_color"], string> = { midnight: "#292642", chestnut: "#68423d", honey: "#d4934d", rose: "#c7597f", lavender: "#8270b2" };
const palette: Record<CharacterConfig["palette"], [string, string]> = { rose: ["#f47ba8", "#d95e9d"], violet: ["#9b87e8", "#7658c4"], mint: ["#69d6bd", "#3aaf9d"], sunset: ["#ffae75", "#e66d66"], night: ["#7074c9", "#414077"] };

export function Character({ config, emotion = "default", pose = "idle", compact = false }: CharacterProps) {
  const [primary, secondary] = palette[config.palette];
  const faceRadius = config.head_shape === "round" ? 75 : config.head_shape === "sharp" ? 57 : 67;
  const bodyTransform = pose === "bounce" ? "translateY(-7)" : pose === "tilt" ? "rotate(-4 120 225)" : pose === "victory" ? "translateY(-3)" : "none";
  const eyeY = emotion === "shocked" || emotion === "surprise" ? 148 : 151;
  const eyeScale = emotion === "shocked" ? 1.32 : emotion === "shy" ? .72 : 1;
  const style = { "--character-primary": primary, "--character-secondary": secondary } as CSSProperties;
  const isHappy = ["happy", "love", "proud", "excited"].includes(emotion);
  const isSad = ["sad", "shy"].includes(emotion);

  return <div className={`character character-${pose} ${compact ? "character-compact" : ""}`} style={style} aria-label={`Персонаж Knowly: ${emotion}`}>
    <svg viewBox="0 0 240 300" role="img" aria-hidden="true">
      <defs>
        <linearGradient id="characterBody" x1="0" x2="1" y1="0" y2="1"><stop stopColor="var(--character-primary)" /><stop offset="1" stopColor="var(--character-secondary)" /></linearGradient>
        <linearGradient id="characterSkin" x1="0" x2="1" y1="0" y2="1"><stop stopColor={skin[config.skin_tone]} /><stop offset="1" stopColor="#e99c83" /></linearGradient>
        <filter id="softShadow"><feDropShadow dx="0" dy="8" stdDeviation="7" floodColor="#592b6940" /></filter>
      </defs>
      <g transform={bodyTransform} filter="url(#softShadow)">
        <ellipse cx="120" cy="278" rx="62" ry="10" fill="#6c3d7620" />
        <path d={config.outfit === "dress" ? "M59 276 Q62 210 120 205 Q178 210 181 276Z" : "M72 276 Q72 210 120 205 Q168 210 168 276Z"} fill="url(#characterBody)" />
        {config.outfit === "hoodie" && <path d="M87 217 Q120 243 153 217" fill="none" stroke="#ffffff70" strokeWidth="7" />}
        {config.outfit === "jacket" && <path d="M120 216V276 M93 220L110 236 M147 220L130 236" fill="none" stroke="#ffffff70" strokeWidth="4" />}
        <path d="M78 232 Q58 238 50 263" fill="none" stroke={skin[config.skin_tone]} strokeWidth="16" strokeLinecap="round" />
        <path d="M162 232 Q182 238 190 263" fill="none" stroke={skin[config.skin_tone]} strokeWidth="16" strokeLinecap="round" />
        {pose === "victory" && <><path d="M52 255 Q30 236 40 216" fill="none" stroke={skin[config.skin_tone]} strokeWidth="12" strokeLinecap="round" /><path d="M188 255 Q210 236 200 216" fill="none" stroke={skin[config.skin_tone]} strokeWidth="12" strokeLinecap="round" /></>}
        <path d={`M120 ${62 + (config.hair_style === "bun" ? 7 : 0)} C${120 - faceRadius} 78 ${120 - faceRadius - 4} 142 ${120 - faceRadius / 1.1} 184 C${120 - 35} 218 ${120 + 35} 218 ${120 + faceRadius / 1.1} 184 C${120 + faceRadius + 4} 142 ${120 + faceRadius} 78 120 ${62 + (config.hair_style === "bun" ? 7 : 0)}Z`} fill="url(#characterSkin)" />
        <path d={config.hair_style === "long" || config.hair_style === "bob" ? "M52 138 Q41 80 80 54 Q120 23 160 54 Q199 80 188 138 Q173 110 162 93 Q120 112 78 93 Q67 110 52 138Z" : config.hair_style === "curly" ? "M53 129 Q32 86 69 52 Q120 19 171 52 Q208 86 187 129 Q169 100 156 91 Q120 106 84 91 Q71 100 53 129Z" : "M54 119 Q48 73 82 53 Q120 31 158 53 Q192 73 186 119 Q166 91 153 86 Q120 100 87 86 Q74 91 54 119Z"} fill={hair[config.hair_color]} />
        {config.hair_style === "bun" && <circle cx="163" cy="55" r="22" fill={hair[config.hair_color]} />}
        {config.hat === "beanie" && <><path d="M64 74 Q65 24 120 22 Q175 24 176 74Z" fill={secondary} /><path d="M65 69H175" stroke="#ffffff66" strokeWidth="8" /></>}
        {config.hat === "beret" && <ellipse cx="128" cy="54" rx="63" ry="25" fill={secondary} transform="rotate(-8 128 54)" />}
        {config.hat === "halo" && <ellipse cx="120" cy="24" rx="48" ry="12" fill="none" stroke="#ffd76d" strokeWidth="7" />}
        <path d={config.brows === "arched" ? "M78 133 Q91 122 102 133 M138 133 Q149 122 162 133" : config.brows === "straight" ? "M78 130H102 M138 130H162" : "M78 132 Q90 126 102 132 M138 132 Q150 126 162 132"} fill="none" stroke="#583b48" strokeWidth={config.brows === "bold" ? 6 : 4} strokeLinecap="round" />
        <g transform={`translate(0 ${eyeY - 151}) scale(1 ${eyeScale})`}>
          {config.eyes === "sparkle" ? <><circle cx="91" cy="151" r="10" fill="#49334e" /><circle cx="149" cy="151" r="10" fill="#49334e" /><circle cx="88" cy="147" r="3" fill="white" /><circle cx="146" cy="147" r="3" fill="white" /></> : config.eyes === "mischief" ? <><path d="M79 151 Q91 140 103 151" fill="none" stroke="#49334e" strokeWidth="5" /><path d="M137 151 Q149 140 161 151" fill="none" stroke="#49334e" strokeWidth="5" /></> : <><ellipse cx="91" cy="151" rx={config.eyes === "round" ? 10 : 8} ry="11" fill="#49334e" /><ellipse cx="149" cy="151" rx={config.eyes === "round" ? 10 : 8} ry="11" fill="#49334e" /><circle cx="88" cy="147" r="3" fill="white" /><circle cx="146" cy="147" r="3" fill="white" /></>}
        </g>
        {config.glasses !== "none" && <><circle cx="90" cy="151" r="20" fill="none" stroke="#47384f" strokeWidth="4" /><circle cx="150" cy="151" r="20" fill="none" stroke="#47384f" strokeWidth="4" /><path d="M110 151H130" stroke="#47384f" strokeWidth="4" /></>}
        {isHappy ? <path d="M105 174 Q120 188 135 174" fill="none" stroke="#ac4865" strokeWidth="5" strokeLinecap="round" /> : isSad ? <path d="M106 184 Q120 171 134 184" fill="none" stroke="#ac4865" strokeWidth="5" strokeLinecap="round" /> : <path d="M109 177 Q120 181 131 177" fill="none" stroke="#ac4865" strokeWidth="4" strokeLinecap="round" />}
        {emotion === "shy" && <path d="M70 172 Q80 166 90 172 M150 172 Q160 166 170 172" stroke="#e88991" strokeWidth="7" strokeLinecap="round" opacity=".7" />}
        {config.accessory === "heart" && <text x="177" y="113" fill="#f36b9e" fontSize="25">♥</text>}
        {config.accessory === "star" && <text x="177" y="113" fill="#ffd15c" fontSize="26">✦</text>}
        {config.accessory === "flower" && <text x="176" y="113" fill="#ff96b7" fontSize="23">✿</text>}
        {config.accessory === "sparkle" && <text x="177" y="113" fill="#b69bff" fontSize="25">✧</text>}
        {emotion === "excited" && <g fill="#f3a2c4"><circle cx="40" cy="102" r="4" /><circle cx="197" cy="174" r="4" /><circle cx="45" cy="190" r="3" /></g>}
      </g>
    </svg>
  </div>;
}

export const defaultCharacter: CharacterConfig = {
  personality: "romantic", head_shape: "soft", skin_tone: "peach", hair_style: "bob", hair_color: "chestnut", eyes: "soft", brows: "soft", outfit: "sweater", accessory: "heart", glasses: "none", hat: "none", palette: "rose",
};
