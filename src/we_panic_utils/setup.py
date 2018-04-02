from setuptools import setup
from setuptools import find_packages

setup(name='we_panic_utils',
      version='0.12',
      description='Utility functions from boiler plate functions, to video preprocessing'+ 
                  ' and training deep neural nets',
      url='https://github.com/danielberenberg/DeepLearning-BloodData',
      author='Adam Barson and Daniel Berenberg',
      author_email='abarson@uvm.edu',
      license='UVM',
      packages=find_packages(),
      install_requires=[
          'Pillow',
          'opencv-python'
        ],
      zip_safe=False)
