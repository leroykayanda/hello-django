FROM python:3.12-alpine

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN python manage.py collectstatic --noinput
# For serving static files
RUN pip install whitenoise==6.7.0
COPY . .
EXPOSE 8000