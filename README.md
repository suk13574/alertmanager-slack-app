## Slack Bot - AlertaGra

이 프로젝트는 **Slack을 통해 Alertmanager와 Grafana를 제어**하기 위해 시작했습니다. </br>
멀티 Alertmanager 및 Grafana 연동을 지원하며, 하나의 Slack 채팅방에서 여러 Alertmanager, Grafana를 제어할 수 있습니다. </br>

해당 Slack 봇을 통해 다음 기능을 수행할 수 있습니다:

- Alertmanager의 Alerts 조회 및 Silence 설정
- Alertmanager의 Silences 조회 및 Silence 업데이트
- Grafana 패널(그래프) 이미지 캡처

</br>
해당 Slack bot은 Socket mode로 만들여졌습니다.
slack bot이 배포된 서버는 outbound가 열려있고, outbound로 인터넷 통신이 되는 환경이면 slack과 통신이 됩니다.

</br>

## 🖼️ How to use

1. [Slack 채널 및 Bot 생성](https://api.slack.com/apps)
2. [Install Slack bot - AlertaGra](#-install)
3. Slack Bot 관리 페이지에서 `/overview` command 생성
4. Slack 채널에 `/overview` 입력하여 사용

</br>

| Function | Image | Description |
|--------|--------|--------|
|command - `/overview`|![image](https://github.com/user-attachments/assets/7b66f5c0-a75f-44e5-9c2d-b6937c577dfd)|config.json으로 연동한 endpoint 목록과 각 기능 버튼 반환|

</br>

| Function | Image | Description |
|--------|--------|--------|
|button - `Get Alerts`|![image](https://github.com/user-attachments/assets/e70eff12-dc02-484d-b658-29a781a476b1)|울리고 있는 알람 목록 조회|
|modal - Silence|![image](https://github.com/user-attachments/assets/1ee9e354-5a8b-4146-8f99-0eef855aa2a9)|Silence 생성|
|button - `Get Silences`|![image](https://github.com/user-attachments/assets/e115479e-0f0b-440f-b7c6-d428d29d1143)|현재 설정된 Silences 목록 조회|
|modal - Update|![image](https://github.com/user-attachments/assets/616f7f57-afee-4b74-b015-9fd7055dd86f)|Update silences|
|modal - Submit|![image](https://github.com/user-attachments/assets/43a108f4-78ac-437f-b83b-ddf933c87e40)|사일런스 반영 여부|

</br>

| Function | Image | Description |
|--------|--------|--------|
|button - `Get Panel`|![image](https://github.com/user-attachments/assets/6d4a4397-7486-43b3-b613-e5af5000eca1)|캡처할 Grafana Panel 정보 입력|
|modal - Submit|![image](https://github.com/user-attachments/assets/e56cc606-23e3-403a-ab96-289710151d80)|Grafana 캡처 이미지 요청 여부|
|cahnnel|![image](https://github.com/user-attachments/assets/7fae1069-ec33-4eac-b64c-fa6d04e2e734)|성공 시 채널에 요청한 그라파나 패널 이미지 확인 가능|


</br>

## 🔶 Requirement

해당 Slack Bot은 Grafana 버전 9.0 이상을 요구합니다. </br>
또한 Grafana는 [Grafana Renderer Plugin](https://grafana.com/grafana/plugins/grafana-image-renderer/)이 설치되어 있어야 합니다.

해당 프로젝트는 Slack Bot을 생성하여 연동 작업이 필요하며, Slack Bot은 [Slack 사이트](https://api.slack.com/apps)에서 생성 가능합니다.
Slack Bot에서 설정해야 하는 기능 및 권한은 다음과 같습니다.

**기능** 
- Sokcet Mode
- Command

**필요로 하는 OAuth Scope 권한**
- channels:read
- chat:write
- commands
- files:write
- groups:read
- incoming-webhook



</br>

## 🚀 Install

간단하게 docker image를 생성하여 실행시킬 수 있습니다.

1. docker 이미지 생성
``` bash
git clone https://github.com/suk13574/slack-bot-alertmanager-grafana.git

cd slack-bot-alertmanager-grafana

docker build -t slack-app-am-grafana:latest .
```

2. docker 이미지 실행
``` bash
docker run -d \
  --name slack-app-am-grafana \
  --env-file <.env 파일 경로> \
  -v <config.json 파일 경로>:/slack_app/config/config.json \
  -p 3000:3000 \
  slack-app-am-grafana:latest
  ```

  </br>


## ⚙️ Configuration

서버 실행을 위해 두 개의 설정 파일이 필요합니다.


1. `.env`
   
Slack Bot과 관련된 값을 환경변수로 설정합니다.
```
SLACK_BOT_TOKEN=<Your Slack Bot Token>
SLACK_CHANNEL_ID=<Your Slack Channel ID>
SLACK_BOT_SOCKET_MODE_TOKEN=<Your Slack Socket Mode Token>
```

- SLACK_BOT_TOKEN: Slack Bot의 `OAuth Tokens`를 발급받아 해당 Token 값을 기입
  - 해당 토큰은 OAuth & Permissions에서 발급 가능
- SLACK_CHANNEL_ID: Slack Bot이 초대된 Slack 채널 ID 기입
- SLACK_BOT_SOCKET_MODE_TOKEN: Slack Bot의 `Socket Mode` 활성화하여 발급받은 Token 값을 기입
  - 해당 토큰은 Socket Mode에서 발급 가능
 
</br>


1. `config.json`

Alertmanager와 Grafana의 URL 설정 정보를 담고 있습니다.
``` json
{
  "ALERTMANAGER_URLS": {
    "<key>": {
      "url": "<Your Alertmanager URL>",
      "default": true 
    }
  },
  "GRAFANA_URLS": {
    "<key1>": {
      "url": "<Your Grafana URL>",
      "token": "<your Grafana Token>",
      "default": true
    }, 
    "<key2>": {
      "url": "<Your Grafana URL>",
      "token": "<your Grafana Token>",
    }, 
  }
}
```

**(Option) ALERTMANAGER_URLS** </br>
연동할 Alertmanager url의 정보를 기입합니다.
만약 여러 Alertmanager 연동을 희망하는 경우, 서로 다른 key 값으로 작성.
- key: slack bot에서 구분할 Alertmanager 이름.
- url: Alertmanager url 정보.
- (option) default: 초기값 지정, 기본 값은 false이며 true값이 없을 경우 맨 위의 값이 자동으로 기본 초기 값으로 설정됨.

</br>

**(Option) Grafana_URLS** </br>
연동할 Grafana url 정보를 기입합니다.
만약 여러 Grafana 연동을 희망하는 경우, 이 역시 서로 다른 key 값으로 작성.
- key: slack bot에서 구분할 Grafana 이름.
- url: Grafana url 정보.
- token: Grafana의 service account Token. API 호출을 위한 값이며, viewr 권한 이상 필요.
- (option) default: 초기값 지정, 기본 값은 false이며 true값이 없을 경우 맨 위의 값이 자동으로 기본 초기 값으로 설정됨.

</br>

위의 예시는 아래와 같이 config를 설정한 것이다.
``` json
{
  "ALERTMANAGER_URLS": {
    "dev": {
      "url": "<Your Alertmanager URL>",
      "default": true 
    },
    "alert1": {
      "url": "<Your Alertmanager URL>",
    },
    "alert2": {
      "url": "<Your Alertmanager URL>",
    }        
  },
  "GRAFANA_URLS": {
    "dev": {
      "url": "<Your Grafana URL>",
      "token": "<your Grafana Token>",
      "default": true
    }, 
    "grafana1": {
      "url": "<Your Grafana URL>",
      "token": "<your Grafana Token>",
    }, 
    "grafana2": {
      "url": "<Your Grafana URL>",
      "token": "<your Grafana Token>",
    }    
  }
}
```

</br>

## 🗂️ Project Architecture

``` bash
.
|-- Dockerfile
|-- app
|   |-- errors        # 커스텀 에러 정의
|   |-- events        # slack 이벤트 정의
|   |-- middleware    # slack bot 미들웨어 정의
|   |-- services      # 싱글톤 패턴
|   `-- utils         # 공통 유틸 (로깅, 설정 등)
|-- config
|   `-- config.json   # 설정 파일
|-- main.py           # 실행 메인 파일
|-- requirements.txt
`-- src
    `-- manager       # Alertmanager, Grafana, Slack 로직 모듈

```

