from distutils.core import setup, Extension
 
module1 = Extension('braid', sources = ['braidmodule.c'])
 
setup (name = 'BraidData',
        version = '1.0',
        description = 'This is a package for implementing a method for combining lists',
        ext_modules = [module1])

setup(name = 'Redeem', 
      version = '0.8', 
      description = 'The Replicape daemon', 
      author='Elias Bakken',
      url='http://http://wiki.thing-printer.com/index.php?title=Redeem')

