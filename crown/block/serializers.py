from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from .models import Block


class WhereInsertBlock(serializers.Serializer):
    before_after = serializers.ChoiceField(choices=(('before', 1), ('after', 2)),
                                           help_text="Вставлять до или после указанного блока",
                                           required=True)
    block = serializers.ModelField(model_field=Block()._meta.get_field('id'), required=True)

    class Meta:
        fields = ['before_after', 'block']

    # def validate_block(self, value):
    #     try:
    #         block = Block.objects.get(id=value)
    #         if block.road.page != self.context['road'].page:
    #             raise serializers.ValidationError("Блок другой страницы.")
    #     except ObjectDoesNotExist:
    #         raise serializers.ValidationError("Такого блока не существует.")


class CreateBlockSerializer(serializers.ModelSerializer):
    where = WhereInsertBlock(required=True)

    class Meta:
        model = Block
        fields = ['content', 'road', 'where']


class BlockSerializer(serializers.ModelSerializer):

    class Meta:
        model = Block
        fields = ['id', 'content']
