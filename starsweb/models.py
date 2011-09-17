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


class Race(models.Model):
    game = models.ForeignKey(Game)
    name = models.CharField(max_length=15)
    plural_name = models.CharField(max_length=15)
    player_number = models.PositiveSmallIntegerField()

    def __unicode__(self):
        return self.name


class Ambassador(models.Model):
    race = models.ForeignKey(Race)
    user = models.ForeignKey("auth.User")
    name = models.CharField(max_length=128)
    active = models.BooleanField(default=True)

    def __unicode__(self):
        return self.name


class Turn(models.Model):
    game = models.ForeignKey(Game)
    year = models.IntegerField()
    generated = models.DateTimeField(auto_now_add=True)

    class Meta:
        get_latest_by = 'generated'
        ordering = ('-generated',)

    def __unicode__(self):
        return unicode(self.year)


class Score(models.Model):
    turn = models.ForeignKey(Turn)
    race = models.ForeignKey(Race)
    section = models.IntegerField()
    value = models.IntegerField()

    class Meta:
        ordering = ('-turn', 'race')
        unique_together = ('turn', 'race', 'section')

    def __unicode__(self):
        return u"{0}: {1}".format(self.section, self.value)
