import os

LINUX = 'linux'
DARWIN = 'darwin'


def setup(requires, name, platform, description, version, maintainer, maintainer_email, url, author,
          keywords, base_dir, entry_points, package_data, dependency_links, data_files):
    import ez_setup
    ez_setup.use_setuptools()
    from setuptools import setup, find_packages

    if platform == DARWIN:
        os.environ['CFLAGS'] = '-I/usr/local/opt/openssl/include'

    setup(name=name,
          description=description,
          version=version,
          maintainer=maintainer,
          maintainer_email=maintainer_email,
          url=url,
          author=author,
          keywords=keywords,
          packages=find_packages(base_dir),
          install_requires=requires,
          entry_points=entry_points,
          package_data=package_data,
          dependency_links=dependency_links,
          # If this is True, setuptools tries to build an egg
          # and py2app / modulegraph / imp.find_module
          # doesn't like that.
          zip_safe=False if platform == DARWIN else True)
