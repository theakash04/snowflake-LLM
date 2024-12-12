FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt ./

RUN pip3 install --no-cache-dir --default-timeout=100 -r ./requirements.txt

COPY . ./

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

CMD ["sh", "-c", "cd streamlit && streamlit run app.py --server.port=8501 --server.address=0.0.0.0"]