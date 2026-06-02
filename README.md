# Dev Workflow Template

AI와 함께 개발할 때 프로젝트 문서, 상태 데이터, 마일스톤, TODO, 대시보드를 일관되게 관리하기 위한 템플릿입니다.

이 템플릿은 특정 언어나 프레임워크에 종속되지 않습니다. 새 프로젝트를 시작할 때 문서 관리 구조를 먼저 갖추고, 이후 프로젝트 성격에 맞게 내용을 채워 넣는 것을 목표로 합니다.

## 포함된 구조

```text
.
├── README.md
├── .gitignore
├── docs
│   ├── README.md
│   ├── DEVELOPMENT_RULES.md
│   ├── DASHBOARD.html
│   ├── data
│   │   └── project-status.yaml
│   ├── setup.md
│   ├── architecture.md
│   └── notes
│       ├── README.md
│       └── template-feedback.md
└── tools
    └── generate_dashboard.py
```

## 사용 방법

1. GitHub에서 이 저장소를 템플릿 저장소로 설정합니다.
2. 새 프로젝트를 만들 때 **Use this template**를 사용합니다.
3. `docs/data/project-status.yaml`에서 프로젝트 이름, 목표, 마일스톤, TODO를 수정합니다.
4. 대시보드를 다시 생성합니다.

```powershell
python tools\generate_dashboard.py
```

5. `README.md`, `docs/setup.md`, `docs/architecture.md`를 실제 프로젝트에 맞게 수정합니다.

## 문서 관리 원칙

- Markdown 문서는 사람이 읽는 설명과 기록으로 사용합니다.
- YAML 데이터는 목표, 마일스톤, TODO, 현재 상태의 구조화 원본으로 사용합니다.
- HTML 대시보드는 YAML을 기반으로 자동 생성되는 결과물입니다.
- `docs/DASHBOARD.html`은 직접 수정하지 않습니다.

## 템플릿 개선

이 템플릿을 기반으로 만든 프로젝트에서 범용적으로 유용한 개선이 생기면 `docs/notes/template-feedback.md`에 기록합니다.

템플릿 저장소에서는 해당 피드백을 검토해 여러 프로젝트에서 반복적으로 유용한 항목만 반영합니다.
