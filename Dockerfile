FROM python:3.12-slim
RUN mkdir /src
WORKDIR /src
ADD . /src
RUN pip install -r requirements.txt

CMD ["python", "app.py"]
EXPOSE 8000