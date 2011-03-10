# Copyright 2010  Red Hat, Inc.
# Stanislav Ochotnicky <sochotnicky@redhat.com>
#
# This file is part of pywebcal.
#
# pywebcal is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pywebcal is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pywebcal.  If not, see <http://www.gnu.org/licenses/>.

from distutils.core import setup

setup(name='pywebcal',
      version='0.1',
      description='Module to simplify access to iCalendar (RFC2445) over WebDAV',
      author='Stanislav Ochotnicky',
      author_email='sochotnicky@redhat.com',
      url='none yet',
      packages=['pywebcal'],
      requires=["python-dateutil", "vobject", "python-webdav-library"],
      install_requires=["python-dateutil >= 1.5", "vobject >= 0.8.1c", "python-webdav-library >= 2.0"],
      classifiers=['Development Status :: 4 - Beta',
                   'License :: OSI Approved :: GNU General Public License (GPL)',
                   'Programming Language :: Python :: 2.6',
                   'Topic :: Software Development :: Libraries'],
      keywords="WebDAV iCal iCalendar calendar library",
      license="GPLv3",
      platforms=["any"],
     )
