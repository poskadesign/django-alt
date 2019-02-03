from rest_framework import serializers

from django_alt.managers import ValidatedManager


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
    def __init__(self, *args, model_class=None, validator_class=None, context=None, **kwargs):
        self.no_validation = kwargs.pop('no_validation', False)
        if self.no_validation:
            super().__init__(*args, **kwargs)
        else:
            if self.Meta:
                if model_class is None:
                    assert hasattr(self.Meta, 'model'), (
                        'Missing `model` field in serializer Meta class. '
                        'Offending serializer: {}').format(self.__class__.__qualname__)
                    model_class = self.Meta.model
                if validator_class is None:
                    assert hasattr(self.Meta, 'validator'), (
                        'Missing `validator` field in serializer Meta class. '
                        'Offending serializer: {}').format(self.__class__.__qualname__)
                    validator_class = self.Meta.validator

            super().__init__(*args, **kwargs)
            ValidatedManager.__init__(self, model_class=model_class, validator_class=validator_class, context=context, **kwargs)

    @classmethod
    def many_init(cls, *args, **kwargs):
        list_serializer = getattr(cls.Meta, 'list_serializer_class', None)
        if list_serializer is None:
            setattr(cls.Meta, 'list_serializer_class', ValidatedSerializer.Meta.list_serializer_class)
        # if not popped, overrides Django Rest Framework's context variable
        kwargs.pop('context')
        return super().many_init(*args, **kwargs)

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

    def validate(self, attrs):
        self.make_validator(attrs, is_create=self.instance is None)
        return self.validate_only()

    def create(self, validated_data):
        return self.do_create(**validated_data)

    def update(self, instance, validated_data):
        return self.do_update(instance, **validated_data)

    def delete(self):
        return self.do_delete(self.instance, **self.initial_data)

    def to_representation(self, instance):
        if self.no_validation:
            return super().to_representation(instance)
        attrs = super().to_representation(instance)
        if self.validator is None:
            self.make_validator(attrs)
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
