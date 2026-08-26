import type { CharacterConfig } from "./character-types";

type CharacterEditorProps = { config: CharacterConfig; onChange: (config: CharacterConfig) => void; onSave: () => void; saving?: boolean };

type ChoiceKey = "personality" | "hair_style" | "hair_color" | "outfit" | "accessory" | "palette";
const choices: { key: ChoiceKey; label: string; items: [string, string][] }[] = [
  { key: "personality", label: "Характер", items: [["cute", "Милая"], ["funny", "Смешная"], ["romantic", "Романтичная"], ["confident", "Уверенная"], ["mysterious", "Загадочная"], ["chaotic", "Хаотичная"]] },
  { key: "hair_style", label: "Причёска", items: [["short", "Короткая"], ["bob", "Каре"], ["long", "Длинная"], ["curly", "Кудри"], ["bun", "Пучок"]] },
  { key: "hair_color", label: "Цвет волос", items: [["midnight", "Ночной"], ["chestnut", "Каштан"], ["honey", "Мёд"], ["rose", "Розовый"], ["lavender", "Лаванда"]] },
  { key: "outfit", label: "Наряд", items: [["hoodie", "Худи"], ["sweater", "Свитер"], ["shirt", "Рубашка"], ["dress", "Платье"], ["jacket", "Куртка"]] },
  { key: "accessory", label: "Аксессуар", items: [["none", "Ничего"], ["heart", "Сердце"], ["star", "Звезда"], ["flower", "Цветок"], ["sparkle", "Искра"]] },
  { key: "palette", label: "Палитра", items: [["rose", "Розовая"], ["violet", "Фиолетовая"], ["mint", "Мятная"], ["sunset", "Закат"], ["night", "Ночная"]] },
];

export function CharacterEditor({ config, onChange, onSave, saving = false }: CharacterEditorProps) {
  const update = (key: keyof CharacterConfig, value: string) => onChange({ ...config, [key]: value } as CharacterConfig);
  return <section className="character-editor"><div className="editor-heading"><strong>Собери своего companion</strong><span>персонализация</span></div><div className="editor-grid">{choices.map(({ key, label, items }) => <label key={key}>{label}<select value={config[key] as string} onChange={(event) => update(key, event.target.value)}>{items.map(([value, text]) => <option value={value} key={value}>{text}</option>)}</select></label>)}</div><button type="button" className="secondary wide" disabled={saving} onClick={onSave}>{saving ? "Сохраняем…" : "Сохранить персонажа"}</button></section>;
}
