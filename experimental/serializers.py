from rest_framework import serializers

from experimental.managers import ValidatedManager


class ValidatedListSerializer(serializers.ListSerializer):
    """
    Overridden default `ListSerializer` class to support multiple delete.
    """
    def delete(self):
        assert self.instance is not None, (
            'Instances were not passed to `{}` constructor\n'
            'but `delete` was called.'
            'Did you forget to pass the queryset when constructing the serializer?'
        ).format(self.__class__.__qualname__)

        result = list(self.instance)
        for instance in result:
            self.child._do_delete_pre(instance)

        self.instance.delete()
        self.instance = None

        def remove_pk(i):
            i.pk = None
            return i

        self._validated_data = [
            self.child._do_delete_post(remove_pk(instance)) for instance in result
        ]
        return self.validated_data


class ValidatedSerializer(serializers.Serializer, ValidatedManager):
    def __init__(self, *args, model_class, validator_class, context=None, **kwargs):
        super().__init__(*args, **kwargs)
        ValidatedManager.__init__(self, model_class=model_class, validator_class=validator_class, context=context, **kwargs)

    @staticmethod
    def validate_and_save(serializer: serializers.Serializer, **kwargs):
        """
        a DRY Shorthand for executing `Serializer` subclass:
        - validation procedures
        - saving the model
        - returning serialized data
        :param serializer: rest_framework.serializers.Serializer subclass
        :param kwargs: extra kwargs to pass to serializer's `save` function
        :return: serializer.data
        """
        serializer.is_valid(raise_exception=True)
        serializer.save(**kwargs)
        return serializer.data

    @classmethod
    def many_init(cls, *args, **kwargs):
        list_serializer = getattr(cls.Meta, 'list_serializer_class', None)
        if list_serializer is None:
            setattr(cls.Meta, 'list_serializer_class', ValidatedSerializer.Meta.list_serializer_class)
        return super().many_init(*args, **kwargs)

    def validate(self, attrs):
        return self.validate_only(**attrs)

    def create(self, validated_data):
        return self.do_create(**validated_data)

    def update(self, instance, validated_data):
        return self.do_update(instance, **validated_data)

    def delete(self):
        assert self.instance is not None, (
            'An instance was not passed to `{}` constructor\n'
            'but `delete` was called.'
            'Did you forget to pass an instance when constructing the serializer?'
        ).format(self.__class__.__qualname__)
        return self.do_delete(self.instance)

    def to_representation(self, instance):
        attrs = super().to_representation(instance)
        if self.validator is None:
            self.make_validator(**attrs)
        else:
            self.validator.attrs = attrs
        self.validator.prepare_read_fields(instance)
        self.validator.will_read(instance)
        return self.validator.attrs

    class Meta:
        list_serializer_class = ValidatedListSerializer


class ValidatedModelSerializer(ValidatedSerializer, serializers.ModelSerializer):
    """
    Combines `ValidatedManager` and `rest_framework.serializers.ModelSerializer`.
    This construction allows overriding `create` and `update` functions without
    having to manually include the validator statements (`base`, `will_create`, etc.).
    Sequential validator calls are now handled by the `ValidatedManager`.
    Override `create` and `update` methods like this:
    
    >>> def create(self, validated_data):
    >>>     # for example you want to create a new record only under a certain condition
    >>>     if should_create_new():
    >>>         # actual creation is done by `do_create`
    >>>         return self.do_create()
    >>>     else:
    >>>         # skip creation and return an existing object
    >>>         return MyModel.objects.first()
    """

    def __init__(self, *args, **kwargs):
        assert hasattr(self.Meta, 'model'), (
            'Missing `model` field in serializer Meta class. '
            'Offending serializer: {}').format(self.__class__.__qualname__)
        assert hasattr(self.Meta, 'validator'), (
            'Missing `validator` field in serializer Meta class. '
            'Offending serializer: {}').format(self.__class__.__qualname__)
        super().__init__(*args, model_class=self.Meta.model, validator_class=self.Meta.validator, **kwargs)
