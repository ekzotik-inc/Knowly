import type { CharacterConfig } from "./character-types";

type CharacterEditorProps = {
  config: CharacterConfig;
  onChange: (config: CharacterConfig) => void;
  onSave: () => void;
  saving?: boolean;
  onboarding?: boolean;
};
type ChoiceKey = keyof Pick<CharacterConfig, "gender" | "personality" | "skin_tone" | "hair_style" | "hair_color" | "eyes" | "brows" | "outfit" | "accessory" | "glasses" | "hat" | "palette">;

type Choice = { key: ChoiceKey; label: string; items: [string, string][] };

const choices: Choice[] = [
  { key: "gender", label: "Образ", items: [["feminine", "Она"], ["masculine", "Он"]] },
  { key: "personality", label: "Характер", items: [["cute", "Милая"], ["funny", "Смешная"], ["romantic", "Романтичная"], ["confident", "Уверенная"], ["mysterious", "Загадочная"], ["chaotic", "Хаотичная"]] },
  { key: "skin_tone", label: "Тон кожи", items: [["porcelain", "Фарфор"], ["peach", "Персиковый"], ["honey", "Мёд"], ["almond", "Миндальный"], ["cocoa", "Какао"]] },
  { key: "hair_style", label: "Причёска", items: [["short", "Короткая"], ["bob", "Каре"], ["long", "Длинная"], ["curly", "Кудри"], ["bun", "Пучок"], ["pixie", "Пикси"], ["space_buns", "Два пучка"], ["side_swept", "На бок"]] },
  { key: "hair_color", label: "Цвет волос", items: [["midnight", "Ночной"], ["chestnut", "Каштан"], ["honey", "Мёд"], ["rose", "Розовый"], ["lavender", "Лаванда"]] },
  { key: "eyes", label: "Глаза", items: [["round", "Круглые"], ["soft", "Мягкие"], ["sparkle", "Сияющие"], ["mischief", "Озорные"]] },
  { key: "brows", label: "Брови", items: [["soft", "Мягкие"], ["arched", "Дугою"], ["straight", "Прямые"], ["bold", "Выразительные"]] },
  { key: "outfit", label: "Наряд", items: [["hoodie", "Худи"], ["sweater", "Свитер"], ["shirt", "Рубашка"], ["dress", "Платье"], ["jacket", "Куртка"]] },
  { key: "accessory", label: "Аксессуар", items: [["none", "Ничего"], ["heart", "Сердце"], ["star", "Звезда"], ["flower", "Цветок"], ["sparkle", "Искра"], ["headphones", "Наушники"], ["bow", "Бант"], ["crown", "Корона"], ["scarf", "Шарф"], ["earrings", "Серьги"]] },
  { key: "glasses", label: "Очки", items: [["none", "Без очков"], ["round", "Круглые"], ["cat_eye", "Кошачьи"]] },
  { key: "hat", label: "Головной убор", items: [["none", "Без него"], ["beanie", "Шапка"], ["beret", "Берет"], ["halo", "Ореол"]] },
  { key: "palette", label: "Палитра", items: [["rose", "Розовая"], ["violet", "Фиолетовая"], ["mint", "Мятная"], ["sunset", "Закат"], ["night", "Ночная"]] },
];

export function CharacterEditor({ config, onChange, onSave, saving = false, onboarding = false }: CharacterEditorProps) {
  const update = (key: ChoiceKey, value: string) => onChange({ ...config, [key]: value } as CharacterConfig);
  return <section className={`character-editor ${onboarding ? "onboarding-editor" : ""}`}>
    <div className="editor-heading"><div><strong>{onboarding ? "Создай своего персонажа" : "Измени своего персонажа"}</strong><small>{onboarding ? "Это твой companion — настрой его под себя" : "Ты можешь изменить его в любой момент"}</small></div><span>{onboarding ? "первый шаг" : "персонализация"}</span></div>
    <div className="editor-identity"><span className="identity-dot" />{config.gender === "masculine" ? "Твой персонаж — он" : "Твой персонаж — она"}</div>
    <div className="editor-grid">{choices.map(({ key, label, items }) => <label key={key}>{label}<select value={config[key] as string} onChange={(event) => update(key, event.target.value)}>{items.map(([value, text]) => <option value={value} key={value}>{text}</option>)}</select></label>)}</div>
    <button type="button" className="secondary wide" disabled={saving} onClick={onSave}>{saving ? "Сохраняем…" : onboarding ? "Создать моего персонажа" : "Сохранить персонажа"}</button>
  </section>;
}
