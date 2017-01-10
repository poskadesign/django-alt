from setuptools import setup, find_packages

setup(name='django-alt',
      version='0.2',
      description='Alternative approach to data validation and REST endpoints in Django and DRF',
      url='https://github.com/poskadesign/django-alt',
      author='Vilius Poška',
      author_email='vilius@poska.lt',
      license='MIT',
      install_requires=['django', 'djangorestframework'],
      packages=find_packages() + ['tests.conf', 'tests.conf.migrations'])
