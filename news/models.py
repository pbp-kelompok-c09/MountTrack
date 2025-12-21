from django.db import models
from uuid import uuid4
from django.conf import settings

# Create your models here.
class News(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    title = models.CharField(max_length=200)
    content = models.TextField()
    published_date = models.DateTimeField(auto_now_add=True)
    news_views = models.PositiveIntegerField(default=0)
    pinned_thumbnail = models.URLField(blank=True, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True) #untuk nama penulis
    likes = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='news_likes', blank=True) #fitur baru, likes
    

    def __str__(self):
        return self.title
    
    def increment_views(self):
        self.news_views += 1
        self.save()
        
    def set_pinned_thumbnail(self, url):
        self.pinned_thumbnail = url
        self.save()
    def total_likes(self):
        return self.likes.count()
    
class ImageNews(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    news = models.ForeignKey(News, related_name='images', on_delete=models.CASCADE)
    image_url = models.URLField()

    def __str__(self):
        return f"Image for {self.news.title}"
#pebepe

