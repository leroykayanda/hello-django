## Django + Celery Setup

Set up a python virtual environment.

    python3 -m venv django  
    source django/bin/activate

Install django.

    pip install django

Create a project.

    django-admin startproject blog

Copy the contents of blog into the root folder and delete the blog folder.
Start the development server.

    python manage.py runserver
    
Create an app.

    python manage.py startapp post

This is the directory structure.

    ll
    total 304
    drwxr-xr-x   9 leroy  staff     288 Oct  1 10:31 blog
    drwxr-xr-x   6 leroy  staff     192 Sep 27 18:01 django
    -rwxr-xr-x   1 leroy  staff     660 Sep 27 18:40 manage.py
    drwxr-xr-x  11 leroy  staff     352 Oct  1 10:56 post

Add the app in settings.py

    INSTALLED_APPS = [
    	'django.contrib.admin',
    	'django.contrib.auth',
    	'django.contrib.contenttypes',
    	'django.contrib.sessions',
    	'django.contrib.messages',
    	'django.contrib.staticfiles',
    	'post.apps.PostConfig', # our app name
    ]

## Models

A model maps to a database table. Django comes packaged with a sqlite database. Add this in models.py.

    from django.db import models
    from django.utils import timezone
    from django.contrib.auth.models import User
    
    class Post(models.Model):
    
    	title = models.CharField(max_length=255)
    	author = models.ForeignKey(User, on_delete=models.CASCADE)
    	body = models.TextField()
    	created_on = models.DateTimeField(default=timezone.now)
    	last_modified = models.DateTimeField(auto_now=True)
    
    	def __str__(self) -> str:
    		return self.title

Whenever we add, update or delete a model, we need to run 2 cmds.

    python manage.py makemigrations

This generates the SQL cmds.

    python manage.py migrate

This executes the sql cmds in the db.

## Superuser

    python manage.py createsuperuser

Log in to the admin portal at *http://127.0.0.1:8000/admin*
To render the Post model in admin, add the following in post/admin.py.

    from django.contrib import admin
    from .models import Post
    
    # Register your models here.
    admin.site.register(Post)

Add some test posts.

## Views
Set this in post/views.py

    from django.http import HttpResponse
    
    # create a function
    def home(request):
    	
    	return HttpResponse("<h1>Welcome</h1>")

## Urls
post/urls.py

    from django.urls import path
    from . import views
    
    urlpatterns = [
    	path('', views.home, name='home'),
    ]

blog/urls.py

    from django.contrib import admin
    from django.urls import path, include
    
    urlpatterns = [
    	path('admin/', admin.site.urls),
    	path('', include('post.urls'))
    ]

## Templates
Create a templates directory at the root level.
Add this to settings.py.

    TEMPLATES = [
    	{
    		'BACKEND': 'django.template.backends.django.DjangoTemplates',
    	
    		# adding template folder that we just created
    		'DIRS': [BASE_DIR/'templates'],
    		'APP_DIRS': True,
    		'OPTIONS': {
    			'context_processors': [
    				'django.template.context_processors.debug',
    				'django.template.context_processors.request',
    				'django.contrib.auth.context_processors.auth',
    				'django.contrib.messages.context_processors.messages',
    			],
    		},
    	},
    ]
Create home.html.

    <h1>Welcome to GeeksforGeeks</h1>

Modify views.py to fetch data from the model.

    from django.http import HttpResponse
    from django.shortcuts import render
    from .models import Post
    
    def home(request):
    	posts = Post.objects.all()
    	context = {
    		'Posts': posts
    	}
    
    	return render(request, 'home.html', context)

And home.html

    {% for post in object_list %}
    	<h1>{{post.title}}</h1>
    	<small>By: {{post.author.first_name}} {{post.author.last_name}}</small>
    	
    
    <p>{{post.body}}</p>
    
    
    {% endfor %}

Dockerize the app using this Dockerfile

    FROM python:3.12-alpine
    
    WORKDIR /app
    COPY requirements.txt .
    RUN pip install -r requirements.txt
    COPY . .
    EXPOSE 8000

And requirements.txt

    gunicorn==23.0.0
    Django==5.1.1
    celery==5.4.0
    redis==5.1.0
    amqp==5.2.0

docker-compose.yaml

version: '3'

    services:
      web:
        build: .
        command: gunicorn --bind 0.0.0.0:8000 --log-level info --workers 4 blog.wsgi:application
        ports:
          - "8000:8000"
     

## Celery
Add blog/celery.py

    import os
    from celery import Celery
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
    app = Celery('blog') 
    app.config_from_object('django.conf:settings', namespace='CELERY')
    # Load task modules from all registered Django app configs.
    app.autodiscover_tasks()
    
In settings.py, add these.

If using redis as a broker.

    CELERY_BROKER_URL = 'redis://redis:6379/0'
    CELERY_RESULT_BACKEND = 'redis://redis:6379/0'

Rabbitmq

    CELERY_BROKER_URL =  'amqp://guest:guest@rabbitmq:5672//'
    CELERY_RESULT_BACKEND =  'rpc://'

In

    blog/__init__.py

Set this

    from .celery import app as celery_app
    
    __all__ = ['celery_app']

Define a celery task in post/tasks.py

    from celery import shared_task
    
    @shared_task
    def add(x, y):
        return x + y

Modify views.py to make a call to the celery task

    from django.http import HttpResponse
    from django.shortcuts import render
    from .models import Post
    import logging
    from post.tasks import add
    from celery.result import AsyncResult
    
    logger = logging.getLogger(__name__)
    
    def home(request):
    	posts = Post.objects.all()
    	context = {
    		'Posts': posts
    	}
    
    	res = add.delay(2, 3)
    	task_result = AsyncResult(res.id)
    
    	try:
    		result = task_result.get(timeout=5)  # Wait for up to 1 second
    		logger.info(f"Result: {result}")
    	except TimeoutError:
    		logger.info("Task is still running")
    
    	return render(request, 'home.html', context)

We add this in settings for logging.

    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
            },
        },
        'root': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'loggers': {
            'django': {
                'handlers': ['console'],
                'level': 'INFO',
                'propagate': True,
            }
        }
    }

We start celery using this cmd

    celery -A blog worker --loglevel=info

Complete docker-compose

    version: '3'
    
    services:
      web:
        build: .
        command: gunicorn --bind 0.0.0.0:8000 --log-level info --workers 4 blog.wsgi:application
        ports:
          - "8000:8000"
          
      redis:
        image: redis:latest
        ports:
          - "6379:6379"
    
      rabbitmq:
        image: rabbitmq:3-management
        ports:
          - "5672:5672"  # AMQP protocol port
          - "15672:15672"  # Management UI
    
      celery:
        build: .
        command: celery -A blog worker --loglevel=info

**Refs**
- https://www.geeksforgeeks.org/getting-started-with-django/
- https://www.geeksforgeeks.org/celery-integration-with-django/
- https://medium.com/django-unleashed/how-to-use-celery-with-django-c4c341997704