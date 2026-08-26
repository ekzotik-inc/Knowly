import type { CharacterConfig } from "./character-types";

type CharacterEditorProps = { config: CharacterConfig; onChange: (config: CharacterConfig) => void; onSave: () => void; saving?: boolean };

const choices = {
  personality: [["cute", "Cute 🥰"], ["funny", "Funny 😂"], ["romantic", "Romantic 💗"], ["confident", "Confident 😎"], ["mysterious", "Mysterious 👀"], ["chaotic", "Chaotic 😈"]],
  hair_style: [["short", "Short"], ["bob", "Bob"], ["long", "Long"], ["curly", "Curly"], ["bun", "Bun"]],
  hair_color: [["midnight", "Midnight"], ["chestnut", "Chestnut"], ["honey", "Honey"], ["rose", "Rose"], ["lavender", "Lavender"]],
  outfit: [["hoodie", "Hoodie"], ["sweater", "Sweater"], ["shirt", "Shirt"], ["dress", "Dress"], ["jacket", "Jacket"]],
  accessory: [["none", "None"], ["heart", "Heart"], ["star", "Star"], ["flower", "Flower"], ["sparkle", "Sparkle"]],
  palette: [["rose", "Rose"], ["violet", "Violet"], ["mint", "Mint"], ["sunset", "Sunset"], ["night", "Night"]],
} as const;

export function CharacterEditor({ config, onChange, onSave, saving = false }: CharacterEditorProps) {
  const update = (key: keyof CharacterConfig, value: string) => onChange({ ...config, [key]: value } as CharacterConfig);
  return <section className="character-editor"><div className="editor-heading"><strong>Настрой свой companion</strong><span>Your Character</span></div><div className="editor-grid">{Object.entries(choices).map(([key, items]) => <label key={key}>{key.replace("_", " ")}<select value={config[key as keyof typeof config] as string} onChange={(event) => update(key as keyof CharacterConfig, event.target.value)}>{items.map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select></label>)}</div><button type="button" className="secondary wide" disabled={saving} onClick={onSave}>{saving ? "Сохраняем…" : "Сохранить персонажа"}</button></section>;
}
