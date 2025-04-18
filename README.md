# Secondhand Platform

## 프로젝트 소개
이 프로젝트는 중고거래 플랫폼을 모사한 웹 애플리케이션입니다. 회원 가입, 로그인, 상품 등록 및 조회, 상품 검색, 1대1 채팅, 실시간 전체 채팅, 송금 기능, 불량 유저 및 상품 신고, 관리자 기능 등을 지원합니다.

## 환경 설정 방법

Python 3.10 이상이 설치되어 있어야 합니다.  
다음 과정을 통해 프로젝트를 설정합니다.

1. 가상환경을 생성하고 활성화합니다.
```
python -m venv venv
source venv/bin/activate (Linux, Mac)
venv\Scripts\activate (Windows)
```

2. 필요 패키지를 설치합니다.
```
pip install -r requirements.txt
```

3. 데이터베이스를 초기화합니다.
```
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

4. 서버를 실행합니다.
```
python app.py
```

5. 기본 서버 주소는 다음과 같습니다.
```
http://localhost:5000
```

## 실행 방법

1. 서버를 실행한 후 브라우저에서 `global_chat_test.html` 파일을 직접 열어 접속합니다.
2. 회원가입을 진행하고 로그인하여 액세스 토큰을 발급받습니다.
3. 로그인 후 채팅 기능 및 상품 등록, 송금, 신고 등의 기능을 사용할 수 있습니다.

## 주의사항

업로드 폴더 uploads는 비어 있을 수 있지만 프로젝트 내에 반드시 존재해야 합니다.  
instance 폴더 내부의 secondhand.db 파일은 배포시 포함되지 않습니다.  
로컬에서 테스트할 경우 migrations 폴더를 기반으로 직접 데이터베이스를 생성해야 합니다.  

## 폴더 구조

app.py : 메인 서버 파일  
models.py : 데이터베이스 모델 정의  
global_chat_test.html : 실시간 채팅 테스트용 클라이언트  
migrations/ : 데이터베이스 마이그레이션 이력  
uploads/ : 상품 이미지 업로드 폴더  
requirements.txt : 필요 패키지 목록  
README.md : 프로젝트 설명 파일
