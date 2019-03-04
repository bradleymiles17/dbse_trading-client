from django.db import models


# Create your models here.
class Order(models.Model):
    BID = 0
    ASK = 1

    OrderType = (
        (BID, 'BID'),
        (ASK, 'ASK')
    )

    time = models.DateTimeField()
    otype = models.IntegerField(choices=OrderType)
    price = models.FloatField()
    qty = models.IntegerField()

    def __str__(self):
        return '[QID:%d T=%5.2f %s P=%03d Q=%s]' % \
               (self.pk, self.time.timestamp(), self.otype, self.price, self.qty)
