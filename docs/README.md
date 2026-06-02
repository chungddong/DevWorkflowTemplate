# 문서 인덱스

이 폴더는 프로젝트 개발 중 생성되는 문서와 상태 데이터를 관리하는 공간입니다.

프로젝트를 처음 파악할 때는 아래 순서로 문서를 확인합니다.

## 읽는 순서

1. [프로젝트 대시보드](DASHBOARD.html)
2. [프로젝트 상태 데이터](data/project-status.yaml)
3. [개발 규칙](DEVELOPMENT_RULES.md)
4. [환경 세팅](setup.md)
5. [프로젝트 구조](architecture.md)
6. [개발 메모](notes/README.md)
7. [템플릿 개선 피드백](notes/template-feedback.md)

## 문서 역할

- `DASHBOARD.html`: 프로젝트 진행 상황을 브라우저에서 볼 수 있는 자동 생성 대시보드입니다.
- `data/project-status.yaml`: 목표, 마일스톤, TODO, 현재 상태를 관리하는 구조화 원본입니다.
- `DEVELOPMENT_RULES.md`: 개발과 문서 관리에 대한 공통 규칙입니다.
- `setup.md`: 개발 환경 세팅과 빌드 방법을 설명합니다.
- `architecture.md`: 코드 구조와 실행 흐름을 설명합니다.
- `notes/`: 개발 중 나온 아이디어, 결정사항, 임시 메모를 보관합니다.
- `notes/template-feedback.md`: 템플릿 저장소에 반영할 만한 범용 개선 제안을 기록합니다.

새 문서를 만들면 이 문서에 링크와 목적을 추가합니다.

프로젝트 상태를 수정할 때는 `data/project-status.yaml`을 수정한 뒤 아래 명령으로 대시보드를 갱신합니다.

```powershell
python ..\tools\generate_dashboard.py
```
