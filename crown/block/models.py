from django.db import models
from django.db.models import Q

from road.models import Road


class Block(models.Model):
    """Блок контента на дороге"""
    roads = models.ManyToManyField(Road,
                                   verbose_name="Дороги",
                                   through='BlocksOnRoad')
    #index = models.PositiveIntegerField(verbose_name="Индекс блока в дороге")
    content = models.TextField(verbose_name="Текст блока", blank=True, null=True)

    class Meta:
        verbose_name = "Блок"
        verbose_name_plural = "Блоки"

    def __str__(self):
        return "{}".format(self.id)

    def insert_block(self, road, index):
        blocks = BlocksOnRoad.objects.filter(Q(road=road) & Q(index__gte=index) & ~Q(block=self))
        for b in blocks:
            b.index += 1
            b.save()

    def cut_block(self, road):
        index = BlocksOnRoad.objects.get(road=road, block=self).index
        blocks = BlocksOnRoad.objects.filter(Q(road=road) & Q(index__gte=index) & ~Q(block=self))
        for b in blocks:
            b.index -= 1
            b.save()

class BlocksOnRoad(models.Model):
    block = models.ForeignKey(Block, on_delete=models.CASCADE)
    road = models.ForeignKey(Road, on_delete=models.CASCADE)
    index = models.PositiveIntegerField(verbose_name="Индекс блока в дороге")
    original_road = models.BooleanField(default=False, verbose_name="Оригинальный блок дороги")
