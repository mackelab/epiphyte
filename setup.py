from setuptools import setup, find_packages

setup(
    name='epiphyte',
    version='0.1.0', 
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    include_package_data=True,
    install_requires=[
        'datajoint>=0.14.1 ',
        'numpy>=1.26.3',
        'pandas>=2.2.0'
    ],
    python_requires='>=3.7, <3.10',
    author='Alana Darcher, Tamara Mueller, Rachel Rapp, Franziska Gerken',
    author_email='alana.darcher@gmail.com',
    description='',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/mackelab/epiphyte',
    license='MIT', 
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
)
