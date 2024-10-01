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

