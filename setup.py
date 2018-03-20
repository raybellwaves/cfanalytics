from setuptools import setup, find_packages

setup(name='cfanalytics',
      version='0.1.10',
      license='BSD 3-Clause License',
      author='Ray Bell',      
      author_email='rbell1987@gmail.com',
      description='Downloading, analyzing and visualizing CrossFit data',
      url='https://github.com/raybellwaves/cfanalytics',
      packages=find_packages(),
      install_requires=['requests', 'aiohttp', 'pandas', 'numpy', 'xarray'],
      python_requires='>=3.6')
