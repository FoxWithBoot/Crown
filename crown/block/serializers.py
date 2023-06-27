from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from .controller import read_road, create_block
from .models import Block


class WhereInsertBlock(serializers.Serializer):
    before_after = serializers.ChoiceField(choices=(('before', 1), ('after', 2)),
                                           help_text="Вставлять до или после указанного блока",
                                           required=True)
    block = serializers.ModelField(model_field=Block()._meta.get_field('id'), required=True)

    class Meta:
        fields = ['before_after', 'block']

    def validate_block(self, value):
        try:
            block = Block.objects.get(id=value)
            if block.road.page != self.context['road'].page:
                raise serializers.ValidationError("Блок другой страницы.")
            return block
        except ObjectDoesNotExist:
            raise serializers.ValidationError("Такого блока не существует.")


class CreateBlockSerializer(serializers.ModelSerializer):
    where = WhereInsertBlock(required=True, help_text="Куда вставить новый блока?")

    class Meta:
        model = Block
        fields = ['content', 'where']

    def validate(self, data):
        block = data['where']['block']
        line = read_road(self.context['road'])
        if block not in line:
            raise serializers.ValidationError({'where': {'block': ['Блок вне линии повествования.']}})
        data['line'] = line
        return data

    def create(self, validated_data):
        return create_block(road=self.context['road'], line=validated_data['line'],
                            content=validated_data.get('content', ''), where=validated_data['where'])


class BlockSerializer(serializers.ModelSerializer):

    class Meta:
        model = Block
        fields = ['id', 'content']
