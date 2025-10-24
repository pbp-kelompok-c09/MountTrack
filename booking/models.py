from django.db import models
from django.conf import settings
from userprofile.models import UserProfile
# from list_gunung.models import Gunung

class Booking(models.Model): 
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    # gunung = models.ForeignKey(Gunung, on_delete=models.CASCADE)
    pax = models.IntegerField()  
    levels = models.JSONField()  
    porter_required = models.BooleanField(default=False)
    
    def check_porter(self):
        user_profile = UserProfile.objects.get(user=self.user)  
        if user_profile.category_experience == 'beginner' and all(level == 'beginner' for level in self.levels):
            return True
        return False

    def __str__(self):
        return f"Booking untuk {self.user.username} di {self.gunung.nama}"
