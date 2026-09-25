# XBTI Data Format Reference

This documents the exact data structure used by XBTI projects. When generating a custom BTI, output files MUST follow these formats exactly.

## Architecture Overview

```
my-bti/
├── index.html
├── package.json
├── vite.config.js
├── public/
├── image/              # Avatar images (one per personality type)
│   ├── CODE1.png
│   └── CODE2.png
└── src/
    ├── main.jsx
    ├── App.jsx
    ├── index.css
    ├── data/
    │   ├── dimensions.js
    │   ├── questions.js
    │   └── types.js
    ├── logic/
    │   └── scoring.js
    └── components/
        ├── IntroScreen.jsx
        ├── TestScreen.jsx
        └── ResultScreen.jsx
```

## dimensions.js

```javascript
export const dimensionMeta = {
  D1: { name: 'D1 维度名称', model: '模型名称' },
  D2: { name: 'D2 维度名称', model: '模型名称' },
  // ... 15 dimensions total, 5 models x 3 sub-dimensions each
};

export const dimensionOrder = ['D1','D2','D3','D4','D5','D6','D7','D8','D9','D10','D11','D12','D13','D14','D15'];

export const DIM_EXPLANATIONS = {
  D1: {
    L: "低分解释文案",
    M: "中分解释文案",
    H: "高分解释文案"
  },
  // ... one for each dimension
};
```

## questions.js

```javascript
export const questions = [
  {
    id: 'q1', dim: 'D1',
    text: '题目文本',
    options: [
      { label: '选项A', value: 1 },
      { label: '选项B', value: 2 },
      { label: '选项C', value: 3 }
    ]
  },
  // ... 30 questions total (2 per dimension)
  // Each question has 3 options with values 1, 2, 3
];

// Optional: special trigger question for hidden type
export const SPECIAL_TRIGGER_QUESTION_ID = 'special_q1';
```

## types.js

```javascript
export const TYPE_LIBRARY = {
  "CODE": {
    code: "CODE",
    cn: "中文名",
    intro: "一句话介绍",
    desc: `详细的人格描述文案（200-400字，幽默讽刺风格）`
  },
  // ... one for each personality type (16-25 types recommended)
};

export const TYPE_IMAGES = {
  "CODE": "/image/CODE.png",
  // ... one for each type
};

export const NORMAL_TYPES = [
  { code: "CODE", pattern: "HHH-HMH-MHH-HHH-MHM" },
  // Pattern format: 15 letters (L/M/H), grouped by model with dashes
  // Groups: Model1(3) - Model2(3) - Model3(3) - Model4(3) - Model5(3)
];
```

## scoring.js

The scoring algorithm is IDENTICAL across all BTI variants:
1. Sum raw scores per dimension (each dimension has 2 questions, score range 2-6)
2. Convert to level: sum ≤ 3 → L, sum = 4 → M, sum ≥ 5 → H
3. Build 15-element user vector
4. Calculate Manhattan distance to each type's pattern
5. Best match = lowest distance; fallback if similarity < 60%

**This file should be copied as-is from XBTI, only changing import paths.**

## Component Customization Points

- `IntroScreen.jsx`: Title, subtitle, theme color, attribution
- `TestScreen.jsx`: Progress bar style, question card style
- `ResultScreen.jsx`: Avatar display, description style, sharing features
- `index.css`: Theme colors, fonts, layout

## Nano Banana Pro Avatar Prompt Template

For each personality type, generate a prompt like:

```
[Character type name], [key personality trait visual], chibi style character,
cute cartoon illustration, simple flat design, vibrant colors,
white background, centered composition, high quality, masterpiece
```

The prompt should capture the essence of the personality type visually.
