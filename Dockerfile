FROM python:3.8.5-alpine

WORKDIR /opt/App_BullsAndCows

RUN apk --update add --no-cache py3-requests py3-six py3-urllib3 py3-chardet py3-certifi py3-idna

COPY src/requirements.txt .
    
RUN pip install -r requirements.txt

COPY src/ .

CMD [ "python", "app.py" ]
