from setuptools import setup, find_packages

from setuptools import setup, find_packages
from setuptools.command.install import install
import os
import subprocess

class CustomInstall(install):
    def run(self):
        install.run(self)
        service_path = os.path.join(self.install_lib, 'my_package/systemd/my_service.service')
        subprocess.call(['sudo', 'cp', service_path, '/etc/systemd/system/'])
        subprocess.call(['sudo', 'systemctl', 'daemon-reload'])
        subprocess.call(['sudo', 'systemctl', 'enable', 'my_service'])
        subprocess.call(['sudo', 'systemctl', 'start', 'my_service'])

setup(
    name='my_package',
    version='0.1',
    packages=find_packages(),
    package_data={'my_package': ['systemd/my_service.service']},
    install_requires=[],
    cmdclass={'install': CustomInstall},
)
