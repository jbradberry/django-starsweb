from django.db import models


class Game(models.Model):
    STATE_CHOICES = (
        ('S', 'Setup'),
        ('A', 'Active'),
        ('P', 'Paused'),
        ('F', 'Finished')
    )
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    hosts = models.ManyToManyField("auth.User")
    created = models.DateTimeField(auto_now_add=True)
    state = models.CharField(max_length=1, choices=STATE_CHOICES, default='S')
    published = models.BooleanField()

    def __unicode__(self):
        return self.name


class Turn(models.Model):
    class Meta:
        get_latest_by = 'generated'
        ordering = ['-generated']

    game = models.ForeignKey(Game)
    year = models.IntegerField()
    generated = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return unicode(self.year)


class Ambassador(models.Model):
    game = models.ForeignKey(Game)
    user = models.ForeignKey("auth.User")
    player_number = models.PositiveSmallIntegerField()
    name = models.CharField(max_length=128)
    race_name = models.CharField(max_length=15)
    plural_race_name = models.CharField(max_length=15)
    active = models.BooleanField(default=True)

    def __unicode__(self):
        return self.name
