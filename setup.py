from distutils.core import setup

setup(name='pyvim',
      version='1.0',
      description= 'Python package for programming function in vim internal enviroment.',
      author='winterTTr',
      author_email='winterTTr@gmail.com',
      url='http://code.google.com/p/pyvim',
      license = 'LGPL' ,
      py_modules = ['sockpdb'],
      packages=['pyvim'],
      package_dir = { 'pyvim' : 'src' } ,
      package_data= { 'pyvim' : ['pvLogging.ini'] },
      )
