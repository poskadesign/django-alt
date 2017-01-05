from setuptools import setup

setup(name='django-alt',
      version='0.1',
      description='Alternative approach to data validation and REST endpoints in Django and DRF',
      url='https://github.com/poskadesign/django-alt',
      author='Vilius Poška',
      author_email='vilius@poska.lt',
      license='MIT',
      install_requires=['django', 'djangorestframework'],
      packages=['django_alt'])
