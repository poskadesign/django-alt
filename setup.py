from setuptools import setup, find_packages

setup(name='django-alt',
      version='0.24',
      description='Alternative approach to data validation and REST endpoints in Django and DRF',
      url='https://github.com/poskadesign/django-alt',
      author='Vilius Poška',
      author_email='vilius@poska.lt',
      license='MIT',
      install_requires=['django', 'djangorestframework'],
      packages=find_packages() + ['django_alt_tests', 'django_alt_tests.conf', 'django_alt_tests.conf.migrations'])
